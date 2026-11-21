#include <WiFi.h>
#include <Wire.h>
#include <PubSubClient.h>
#include <esp_timer.h>
#include <esp_system.h>
#include <initializer_list>
#include <math.h>
#include <time.h>
#include "config.h"
#include "protocol.h"

WiFiClient network;
PubSubClient mqtt(network);
portMUX_TYPE dataMux = portMUX_INITIALIZER_UNLOCKED;
Window latestWindow;
Mode requestedMode = Mode::Normal;
bool sensorOk = false, imuInitialized = false, samplingOk = false;
TaskHandle_t samplingTask = nullptr;
esp_timer_handle_t sampleTimer = nullptr;
char telemetryTopic[96], statusTopic[96], commandTopic[96], ackTopic[96], clientId[64], bootId[9];
uint32_t lastRetry = 0, lastPublishedWindow = 0, lastStatus = 0;
bool statusPending = true, ackPending = false;
char pendingAck[256];
CommandCache commands;

// Configure 1 kHz IMU output, +/-2 g, and a provisional 184 Hz accelerometer bandwidth.
bool writeRegister(uint8_t reg, uint8_t value) {
  Wire.beginTransmission(Config::IMU_ADDRESS);
  Wire.write(reg);
  Wire.write(value);
  return Wire.endTransmission() == 0;
}
bool initializeImu() {
  Wire.begin(Config::SDA_PIN, Config::SCL_PIN);
  Wire.setClock(400000);
  Wire.setTimeOut(5);
  return writeRegister(0x6B, 0x01) && writeRegister(0x1A, 0x01) &&
         writeRegister(0x19, 0x00) && writeRegister(0x1C, 0x00);
}
bool readAcceleration(float& acceleration) {
  if (!imuInitialized) return false;
  Wire.beginTransmission(Config::IMU_ADDRESS);
  Wire.write(0x3B);
  if (Wire.endTransmission(false) != 0) return false;
  if (Wire.requestFrom(Config::IMU_ADDRESS, static_cast<uint8_t>(6), true) != 6) return false;
  const uint8_t high = Wire.read(), low = Wire.read();
  const int16_t rawX = static_cast<int16_t>((static_cast<uint16_t>(high) << 8) | low);
  while (Wire.available()) Wire.read();
  acceleration = rawX / 16384.0f;
  return true;
}

// Provisional waveforms until TH5 units, preprocessing, and amplitudes are confirmed.
float syntheticSample(uint64_t timeUs, Mode mode) {
  const float t = static_cast<float>(timeUs % 1000000) / 1000000.0f;
  const float phase = 2 * PI * 25 * t;
  if (mode == Mode::Normal) return Config::NORMAL_AMPLITUDE * sinf(phase);
  if (mode == Mode::Imbalance) return Config::IMBALANCE_AMPLITUDE * sinf(phase);
  const float impulse = (timeUs % 100000) < 3000 ? 0.8f : 0;
  return Config::LOOSE_AMPLITUDE * sinf(phase) + 0.1f * sinf(2 * phase) + impulse;
}
void samplingTick(void*) { xTaskNotifyGive(samplingTask); }
bool clockReady() { return time(nullptr) >= 1700000000; }

void acquireSamples(void*) {
  SamplingWindow windows;
  uint32_t missed = 0;
  for (;;) {
    const uint32_t ticks = ulTaskNotifyTake(pdTRUE, portMAX_DELAY);
    if (ticks > 1) missed += ticks - 1;
    const uint64_t now = esp_timer_get_time();
    portENTER_CRITICAL(&dataMux);
    const Mode mode = requestedMode;
    portEXIT_CRITICAL(&dataMux);
    float acceleration = 0;
    const bool ok = readAcceleration(acceleration);
    portENTER_CRITICAL(&dataMux);
    sensorOk = ok;
    portEXIT_CRITICAL(&dataMux);
    if (!ok && !Config::USE_SYNTHETIC) { windows.reset(); continue; }
    Window completed;
    if (windows.add(now, mode, Config::USE_SYNTHETIC ? syntheticSample(now, mode) : acceleration,
                    ok, missed, completed)) {
      completed.ts = clockReady() ? static_cast<uint32_t>(time(nullptr)) : 0;
      portENTER_CRITICAL(&dataMux);
      latestWindow = completed;
      portEXIT_CRITICAL(&dataMux);
    }
  }
}
Window windowSnapshot() {
  portENTER_CRITICAL(&dataMux);
  const Window value = latestWindow;
  portEXIT_CRITICAL(&dataMux);
  return value;
}
void setMode(Mode mode) {
  portENTER_CRITICAL(&dataMux);
  requestedMode = mode;
  portEXIT_CRITICAL(&dataMux);
  statusPending = true;
}
void reportStatus() {
  portENTER_CRITICAL(&dataMux);
  const Mode mode = requestedMode;
  const bool imuOk = sensorOk;
  portEXIT_CRITICAL(&dataMux);
  char payload[384];
  if (statusJson(bootId, mode, imuOk, clockReady(), samplingOk, false, payload, sizeof payload) &&
      mqtt.publish(statusTopic, payload, true)) {
    statusPending = false;
    lastStatus = millis();
  }
}
void receiveCommand(char* topic, byte* payload, unsigned int length) {
  if (strcmp(topic, commandTopic) != 0) return;
  CommandResult result;
  if (!commands.handle(payload, length, Config::USE_SYNTHETIC, clockReady(),
                       static_cast<uint32_t>(time(nullptr)), result)) return;
  if (result.apply) setMode(result.mode);
  // Status events cannot overwrite this buffer. Backend retries recover a lost QoS 0 ACK.
  ackPending = ackJson(result, bootId, pendingAck, sizeof pendingAck) != 0;
}
bool connectMqtt() {
  char will[128];
  if (!statusJson(bootId, Mode::Normal, false, false, false, true, will, sizeof will)) return false;
  if (!mqtt.connect(clientId, statusTopic, 1, true, will)) return false;
  if (!mqtt.subscribe(commandTopic, 1)) { mqtt.disconnect(); return false; }
  statusPending = true;
  lastPublishedWindow = 0;
  return true;
}
void publishWindow(const Window& value) {
  char payload[768];
  if (telemetryJson(value, bootId, payload, sizeof payload) && mqtt.publish(telemetryTopic, payload, false)) {
    lastPublishedWindow = value.id;
    Serial.printf("window=%lu samples=%lu actual_hz=%.1f missed=%lu rms=%.4f peak=%.4f mode=%s\n",
                  (unsigned long)value.id, (unsigned long)value.sampleCount, value.actualHz,
                  (unsigned long)value.missedSamples, value.features.rms, value.features.peak, modeName(value.mode));
  }
}
void serviceButton() {
  static int previous = HIGH, stable = HIGH;
  static uint32_t changedAt = 0;
  const int current = digitalRead(Config::BUTTON_PIN);
  if (current != previous) { previous = current; changedAt = millis(); }
  if (current != stable && millis() - changedAt >= 30) {
    stable = current;
    if (stable == LOW && Config::USE_SYNTHETIC) {
      portENTER_CRITICAL(&dataMux);
      const Mode next = static_cast<Mode>((static_cast<uint8_t>(requestedMode) + 1) % 3);
      portEXIT_CRITICAL(&dataMux);
      setMode(next);
    }
  }
}
void updateLeds(const Window& value) {
  const bool ready = samplingOk && value.modelReady;
  digitalWrite(Config::GREEN_LED, ready && value.prediction == DIAGNOSIS_NORMAL);
  digitalWrite(Config::YELLOW_LED, ready && value.prediction == DIAGNOSIS_IMBALANCE);
  digitalWrite(Config::RED_LED, ready && value.prediction == DIAGNOSIS_LOOSE);
}
void setup() {
  Serial.begin(115200);
  pinMode(Config::BUTTON_PIN, INPUT_PULLUP);
  for (const int led : {Config::GREEN_LED, Config::YELLOW_LED, Config::RED_LED}) {
    pinMode(led, OUTPUT);
    digitalWrite(led, LOW);
  }
  imuInitialized = initializeImu();
  sensorOk = imuInitialized;
  snprintf(bootId, sizeof bootId, "%08lx", (unsigned long)esp_random());
  snprintf(telemetryTopic, sizeof telemetryTopic, "ce339/%s/e2/%s/telemetry", Config::GROUP_ID, Config::DEVICE_ID);
  snprintf(statusTopic, sizeof statusTopic, "ce339/%s/e2/%s/status", Config::GROUP_ID, Config::DEVICE_ID);
  snprintf(commandTopic, sizeof commandTopic, "ce339/%s/e2/%s/cmd", Config::GROUP_ID, Config::DEVICE_ID);
  snprintf(ackTopic, sizeof ackTopic, "ce339/%s/e2/%s/ack", Config::GROUP_ID, Config::DEVICE_ID);
  snprintf(clientId, sizeof clientId, "ce339-%s-%s-%06lx", Config::GROUP_ID, Config::DEVICE_ID,
           (unsigned long)(ESP.getEfuseMac() & 0xFFFFFF));
  const BaseType_t taskCreated = xTaskCreatePinnedToCore(acquireSamples, "sampling", 4096, nullptr, 2, &samplingTask, 1);
  esp_timer_create_args_t timerArgs{};
  timerArgs.callback = samplingTick;
  timerArgs.name = "e2-sampling";
  samplingOk = taskCreated == pdPASS && esp_timer_create(&timerArgs, &sampleTimer) == ESP_OK &&
               esp_timer_start_periodic(sampleTimer, 1000000 / Config::SAMPLE_HZ) == ESP_OK;
  if (!samplingOk) Serial.println("Sampling initialization failed");
  WiFi.setAutoReconnect(true);
  WiFi.begin(Config::WIFI_SSID, Config::WIFI_PASSWORD);
  configTime(0, 0, "pool.ntp.org");
  mqtt.setServer(Config::MQTT_HOST, Config::MQTT_PORT);
  mqtt.setCallback(receiveCommand);
  mqtt.setKeepAlive(15);
  mqtt.setSocketTimeout(2);
  mqtt.setBufferSize(1024);
}
void loop() {
  serviceButton();
  const Window value = windowSnapshot();
  updateLeds(value);
  const uint32_t now = millis();
  if (WiFi.status() != WL_CONNECTED) {
    if (now - lastRetry >= 5000) { lastRetry = now; WiFi.reconnect(); }
    delay(1);
    return;
  }
  if (!mqtt.connected() && now - lastRetry >= 2000) { lastRetry = now; connectMqtt(); }
  mqtt.loop();
  portENTER_CRITICAL(&dataMux);
  const bool currentSensorOk = sensorOk;
  portEXIT_CRITICAL(&dataMux);
  static bool previousSensorOk = false, previousClockReady = false;
  const bool currentClockReady = clockReady();
  if (currentSensorOk != previousSensorOk || currentClockReady != previousClockReady ||
      now - lastStatus >= Config::STATUS_HEARTBEAT_MS) statusPending = true;
  previousSensorOk = currentSensorOk;
  previousClockReady = currentClockReady;
  if (mqtt.connected()) {
    if (ackPending) ackPending = !mqtt.publish(ackTopic, pendingAck, false);
    if (statusPending) reportStatus();
    if (value.id && value.id != lastPublishedWindow) publishWindow(value);
  }
  delay(1);
}
