#include "features.h"
#include <cmath>

void FeatureAccumulator::reset() {
  sumSquares_ = 0;
  peak_ = 0;
  count_ = 0;
}

void FeatureAccumulator::add(float sample) {
  sumSquares_ += static_cast<double>(sample) * sample;
  const float magnitude = std::fabs(sample);
  if (magnitude > peak_) peak_ = magnitude;
  ++count_;
}

SignalFeatures FeatureAccumulator::result() const {
  const float rms = count_ ? std::sqrt(sumSquares_ / count_) : 0;
  return {rms, peak_, rms > 0 ? peak_ / rms : 0};
}
