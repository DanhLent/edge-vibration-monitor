#include "protocol.h"
#include "config.h"
#include <ArduinoJson.h>
#include <cassert>
#include <cstring>
#include <fstream>
#include <iostream>
#include <string>

int main(int argc, char** argv) {
  assert(argc == 2);
  std::ifstream input(argv[1]);
  JsonDocument fixtures;
  assert(!deserializeJson(fixtures, input));
  char payload[768];
  serializeJson(fixtures["command"], payload, sizeof payload);
  CommandCache cache;
  CommandResult result;
  auto handle = [&](bool synthetic, bool ready, uint32_t now) {
    return cache.handle(reinterpret_cast<const uint8_t*>(payload), strlen(payload), synthetic, ready, now, result);
  };
  assert(handle(true, true, 1795299999) && result.apply && result.result == CommandOutcome::Done);
  assert(handle(true, true, 1795300000) && !result.apply && result.result == CommandOutcome::Done);
  const CommandResult done = result;
  auto command = [&](const char* id, bool synthetic, bool ready, uint32_t now) {
    fixtures["command"]["id"] = id;
    serializeJson(fixtures["command"], payload, sizeof payload);
    return handle(synthetic, ready, now);
  };
  assert(command("cboundary", true, true, 1795300000) && result.result == CommandOutcome::Expired);
  assert(command("cclock", true, false, 0) && result.result == CommandOutcome::Clock);
  assert(command("cphysical", false, true, 1795299999) && result.result == CommandOutcome::Unsupported);
  fixtures["command"]["schema_version"] = 2;
  assert(command("cbad", true, true, 1795299999) && result.result == CommandOutcome::Bad);
  assert(!command("id!", true, true, 1795299999));
  assert(!command("0123456789012345", true, true, 1795299999));
  assert(!cache.handle(reinterpret_cast<const uint8_t*>("{"), 1, true, true, 0, result));
  const std::string embeddedNull = R"({"schema_version":1,"id":"cnull\u0000x","action":"set_mode","mode":"loose","exp":1795300000})";
  assert(!cache.handle(reinterpret_cast<const uint8_t*>(embeddedNull.data()), embeddedNull.size(), true, true, 0, result));
  fixtures["command"]["schema_version"] = 1;
  fixtures["command"]["exp"] = true;
  assert(command("cboolexp", true, true, 0) && result.result == CommandOutcome::Bad);

  Window value;
  value.features = {0.2f, 0.4f, 2};
  value.id = 1;
  value.sampleCount = 1000;
  value.durationUs = 1000000;
  value.actualHz = 1000;
  value.uptimeMs = 1000;
  value.ts = 1795300000;
  value.sensorOk = true;
  assert(telemetryJson(value, "1234abcd", payload, sizeof payload));
  std::cout << payload << '\n';
  assert(statusJson("1234abcd", Mode::Normal, true, true, true, false, payload, sizeof payload));
  std::cout << payload << '\n';
  assert(ackJson(done, "1234abcd", payload, sizeof payload));
  std::cout << payload << '\n';
  assert(statusJson("1234abcd", Mode::Normal, false, false, false, true, payload, sizeof payload));
  std::cout << payload << '\n';
  char tooSmall[8];
  assert(!telemetryJson(value, "1234abcd", tooSmall, sizeof tooSmall));
  assert(predictionName(DIAGNOSIS_UNAVAILABLE) == nullptr);
}
