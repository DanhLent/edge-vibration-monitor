#pragma once
#include <stddef.h>
#include "sampling.h"

const char* modeName(Mode mode);
const char* predictionName(int8_t prediction);

enum class CommandOutcome : uint8_t { Done, Bad, Expired, Clock, Unsupported };
const char* resultName(CommandOutcome result);

struct CommandResult {
  char id[16]{};
  CommandOutcome result = CommandOutcome::Bad;
  Mode mode = Mode::Normal;
  bool apply = false;
};

class CommandCache {
 public:
  bool handle(const uint8_t* payload, size_t length, bool synthetic, bool clockReady,
              uint32_t now, CommandResult& result);
 private:
  CommandResult seen_[8];
  uint8_t position_ = 0;
};

size_t telemetryJson(const Window& window, const char* bootId, char* buffer, size_t capacity);
size_t statusJson(const char* bootId, Mode mode, bool sensorOk, bool clockReady,
                  bool samplingOk, bool offline, char* buffer, size_t capacity);
size_t ackJson(const CommandResult& result, const char* bootId, char* buffer, size_t capacity);
