#include "protocol.h"
#include "config.h"
#include <ArduinoJson.h>
#include <ctype.h>
#include <string.h>

const char* modeName(Mode mode) {
  switch (mode) {
    case Mode::Normal: return "normal";
    case Mode::Imbalance: return "imbalance";
    default: return "loose";
  }
}

const char* predictionName(int8_t prediction) {
  return prediction >= 0 && prediction <= 2 ? modeName(static_cast<Mode>(prediction)) : nullptr;
}

static bool parseMode(const char* name, Mode& mode) {
  if (strcmp(name, "normal") == 0) mode = Mode::Normal;
  else if (strcmp(name, "imbalance") == 0) mode = Mode::Imbalance;
  else if (strcmp(name, "loose") == 0) mode = Mode::Loose;
  else return false;
  return true;
}

const char* resultName(CommandOutcome result) {
  switch (result) {
    case CommandOutcome::Done: return "done";
    case CommandOutcome::Expired: return "expired";
    case CommandOutcome::Clock: return "clock";
    case CommandOutcome::Unsupported: return "unsupported";
    default: return "bad";
  }
}

bool CommandCache::handle(const uint8_t* payload, size_t length, bool synthetic,
                          bool clockReady, uint32_t now, CommandResult& result) {
  if (length > 512) return false;
  JsonDocument doc;
  if (deserializeJson(doc, payload, length) || !doc["id"].is<const char*>()) return false;
  const char* id = doc["id"];
  const size_t idLength = doc["id"].as<JsonString>().size();
  if (!idLength || idLength >= sizeof result.id || strlen(id) != idLength) return false;
  for (size_t i = 0; i < idLength; ++i) {
    const unsigned char c = id[i];
    if (c > 127 || (!isalnum(c) && c != '_' && c != '-')) return false;
  }
  for (const auto& seen : seen_) {
    if (strcmp(id, seen.id) == 0) { result = seen; result.apply = false; return true; }
  }
  result = CommandResult{};
  memcpy(result.id, id, idLength + 1);
  if (doc.size() == 5 && doc["schema_version"].is<int>() && doc["schema_version"] == 1 &&
      doc["action"].is<const char*>() && strcmp(doc["action"], "set_mode") == 0 &&
      doc["action"].as<JsonString>().size() == 8 &&
      doc["mode"].is<const char*>() && parseMode(doc["mode"], result.mode) &&
      doc["mode"].as<JsonString>().size() == strlen(modeName(result.mode)) &&
      doc["exp"].is<uint32_t>()) {
    if (!synthetic) result.result = CommandOutcome::Unsupported;
    else if (!clockReady) result.result = CommandOutcome::Clock;
    else if (now >= doc["exp"].as<uint32_t>()) result.result = CommandOutcome::Expired;
    else { result.result = CommandOutcome::Done; result.apply = true; }
  }
  seen_[position_] = result;
  position_ = (position_ + 1) % 8;
  return true;
}

static size_t writeJson(const JsonDocument& doc, char* buffer, size_t capacity) {
  if (measureJson(doc) >= capacity) return 0;
  return serializeJson(doc, buffer, capacity);
}

size_t telemetryJson(const Window& value, const char* bootId, char* buffer, size_t capacity) {
  JsonDocument doc;
  doc["schema_version"] = 1;
  doc["boot_id"] = bootId;
  if (value.ts) doc["ts"] = value.ts; else doc["ts"] = nullptr;
  doc["uptime_ms"] = value.uptimeMs;
  doc["window_id"] = value.id;
  doc["window_duration_us"] = value.durationUs;
  doc["rms"] = value.features.rms;
  doc["peak"] = value.features.peak;
  doc["crest_factor"] = value.features.crestFactor;
  doc["fs_hz"] = Config::SAMPLE_HZ;
  doc["sample_count"] = value.sampleCount;
  doc["actual_hz"] = value.actualHz;
  doc["missed_samples"] = value.missedSamples;
  doc["source"] = Config::USE_SYNTHETIC ? "synthetic" : "mpu6050";
  doc["mode"] = Config::USE_SYNTHETIC ? modeName(value.mode) : nullptr;
  doc["sensor_ok"] = value.sensorOk;
  doc["model_ready"] = value.modelReady;
  doc["prediction"] = value.modelReady ? predictionName(value.prediction) : nullptr;
  return writeJson(doc, buffer, capacity);
}

size_t statusJson(const char* bootId, Mode mode, bool sensorOk, bool clockReady,
                  bool samplingOk, bool offline, char* buffer, size_t capacity) {
  JsonDocument doc;
  doc["schema_version"] = 1;
  doc["boot_id"] = bootId;
  doc["connection"] = offline ? "offline" : "online";
  if (!offline) {
    doc["source"] = Config::USE_SYNTHETIC ? "synthetic" : "mpu6050";
    doc["mode"] = Config::USE_SYNTHETIC ? modeName(mode) : nullptr;
    doc["sensor_ok"] = sensorOk;
    doc["clock_ready"] = clockReady;
    doc["sampling_ok"] = samplingOk;
    doc["model_ready"] = model_is_ready();
  }
  return writeJson(doc, buffer, capacity);
}

size_t ackJson(const CommandResult& result, const char* bootId, char* buffer, size_t capacity) {
  JsonDocument doc;
  doc["schema_version"] = 1;
  doc["boot_id"] = bootId;
  doc["id"] = result.id;
  doc["result"] = resultName(result.result);
  doc["mode"] = result.result == CommandOutcome::Done ? modeName(result.mode) : nullptr;
  return writeJson(doc, buffer, capacity);
}
