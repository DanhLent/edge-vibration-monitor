#pragma once
#include <stdint.h>

#if __has_include("config.local.h")
#include "config.local.h"
#endif
#ifndef EVM_WIFI_SSID
#define EVM_WIFI_SSID "Wokwi-GUEST"
#endif
#ifndef EVM_WIFI_PASSWORD
#define EVM_WIFI_PASSWORD ""
#endif
#ifndef EVM_MQTT_HOST
#define EVM_MQTT_HOST "test.mosquitto.org"
#endif
#ifndef EVM_USE_SYNTHETIC
#define EVM_USE_SYNTHETIC true
#endif

namespace Config {
constexpr char GROUP_ID[] = "N06";
constexpr char DEVICE_ID[] = "esp32-01";
constexpr char MQTT_HOST[] = EVM_MQTT_HOST;
constexpr uint16_t MQTT_PORT = 1883;
constexpr char WIFI_SSID[] = EVM_WIFI_SSID;
constexpr char WIFI_PASSWORD[] = EVM_WIFI_PASSWORD;
constexpr int SDA_PIN = 21, SCL_PIN = 22, BUTTON_PIN = 18;
constexpr int GREEN_LED = 25, YELLOW_LED = 26, RED_LED = 27;
constexpr uint8_t IMU_ADDRESS = 0x68;
constexpr uint32_t SAMPLE_HZ = 1000;
constexpr uint32_t WINDOW_US = 1000000;
constexpr bool USE_SYNTHETIC = EVM_USE_SYNTHETIC;
constexpr uint32_t STATUS_HEARTBEAT_MS = 15000;

// These amplitudes are provisional until the official TH5 units and ranges are known.
constexpr float NORMAL_AMPLITUDE = 0.10f;
constexpr float IMBALANCE_AMPLITUDE = 0.40f;
constexpr float LOOSE_AMPLITUDE = 0.20f;
}
static_assert(Config::SAMPLE_HZ >= 200 && Config::SAMPLE_HZ <= 1000, "E2 sampling range");
