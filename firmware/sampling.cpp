#include "sampling.h"
#include "config.h"
#include <cmath>

void SamplingWindow::reset() {
  values_.reset();
  sensorOk_ = true;
}

bool SamplingWindow::add(uint64_t nowUs, Mode mode, float sample, bool sensorOk,
                         uint32_t missedSamples, Window& completed) {
  if (!std::isfinite(sample)) { reset(); return false; }
  if (mode != mode_) { reset(); mode_ = mode; }
  if (!values_.count()) started_ = nowUs;
  const uint64_t elapsed = nowUs - started_;
  const bool complete = elapsed >= Config::WINDOW_US;
  // Close [start, now) before adding the boundary sample to the next window.
  if (complete) {
    completed = Window{};
    completed.features = values_.result();
    completed.mode = mode_;
    completed.id = ++nextId_;
    completed.sampleCount = values_.count();
    completed.missedSamples = missedSamples;
    completed.uptimeMs = static_cast<uint32_t>(nowUs / 1000);
    completed.durationUs = elapsed;
    completed.actualHz = values_.count() * 1000000.0f / elapsed;
    completed.sensorOk = sensorOk_;
    completed.modelReady = model_is_ready();
    if (completed.modelReady) {
      completed.prediction = model_predict(completed.features.rms, completed.features.peak);
      if (completed.prediction < 0 || completed.prediction > 2) completed.modelReady = false;
    }
    reset();
    started_ = nowUs;
  }
  values_.add(sample);
  sensorOk_ = sensorOk_ && sensorOk;
  return complete;
}
