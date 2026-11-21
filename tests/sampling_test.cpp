#include "sampling.h"
#include <cassert>
#include <cmath>

int main() {
  SamplingWindow windows;
  Window completed;
  for (uint64_t t = 0; t < 1000000; t += 1000)
    assert(!windows.add(t, Mode::Normal, 1, true, 0, completed));
  assert(windows.add(1000000, Mode::Normal, 9, false, 3, completed));
  assert(completed.sampleCount == 1000 && completed.durationUs == 1000000);
  assert(completed.actualHz == 1000 && completed.features.rms == 1 && completed.sensorOk);
  assert(completed.uptimeMs == 1000 && completed.missedSamples == 3);
  assert(!completed.modelReady && completed.prediction == DIAGNOSIS_UNAVAILABLE);
  const Window snapshot = completed;
  for (uint64_t t = 1001000; t <= 2000000; t += 1000)
    windows.add(t, Mode::Normal, 9, true, 3, completed);
  assert(completed.sampleCount == 1000 && completed.features.rms == 9 && !completed.sensorOk);
  assert(snapshot.features.rms == 1 && snapshot.uptimeMs == 1000);

  windows.reset();
  for (uint64_t t = 3000000; t < 3500000; t += 1000)
    assert(!windows.add(t, Mode::Normal, 1, true, 3, completed));
  for (uint64_t t = 3500000; t < 4500000; t += 1000)
    assert(!windows.add(t, Mode::Loose, 2, true, 3, completed));
  assert(windows.add(4500000, Mode::Loose, 2, true, 3, completed));
  assert(completed.sampleCount == 1000 && completed.features.rms == 2 && completed.mode == Mode::Loose);

  windows.reset();
  for (uint64_t t = 5000000; t < 6000000; t += 1000)
    assert(!windows.add(t, Mode::Normal, 1, true, 3, completed));
  assert(windows.add(7000000, Mode::Normal, 1, true, 1003, completed));
  assert(completed.sampleCount == 1000 && completed.durationUs == 2000000 && completed.actualHz == 500);
  assert(!windows.add(7001000, Mode::Normal, NAN, false, 1003, completed));
}
