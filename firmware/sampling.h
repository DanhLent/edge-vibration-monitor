#pragma once
#include "features.h"
#include "model.h"

enum class Mode : uint8_t { Normal, Imbalance, Loose };

struct Window {
  SignalFeatures features{};
  Mode mode = Mode::Normal;
  uint32_t id = 0, sampleCount = 0, missedSamples = 0, uptimeMs = 0, ts = 0;
  uint64_t durationUs = 0;
  float actualHz = 0;
  bool sensorOk = false, modelReady = false;
  int8_t prediction = DIAGNOSIS_UNAVAILABLE;
};

class SamplingWindow {
 public:
  void reset();
  bool add(uint64_t nowUs, Mode mode, float sample, bool sensorOk,
           uint32_t missedSamples, Window& completed);

 private:
  FeatureAccumulator values_;
  Mode mode_ = Mode::Normal;
  uint64_t started_ = 0;
  uint32_t nextId_ = 0;
  bool sensorOk_ = true;
};
