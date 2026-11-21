#pragma once
#include <stdint.h>

struct SignalFeatures {
  float rms;
  float peak;
  float crestFactor;
};

class FeatureAccumulator {
 public:
  void reset();
  void add(float sample);
  SignalFeatures result() const;
  uint32_t count() const { return count_; }

 private:
  double sumSquares_ = 0;
  float peak_ = 0;
  uint32_t count_ = 0;
};
