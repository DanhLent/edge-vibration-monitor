#include "features.h"
#include <cassert>
#include <cmath>
#include <iostream>

int main() {
  FeatureAccumulator values;
  for (int i = 0; i < 1000; ++i) values.add(0);
  auto result = values.result();
  assert(result.rms == 0 && result.peak == 0 && result.crestFactor == 0);
  values.reset();
  for (int i = 0; i < 1000; ++i) values.add(0.4f * std::sin(2 * 3.141592653589793 * 25 * i / 1000));
  result = values.result();
  assert(std::fabs(result.rms - 0.4 / std::sqrt(2.0)) < 1e-6);
  assert(std::fabs(result.peak - 0.4) < 1e-6);
  assert(std::fabs(result.crestFactor - std::sqrt(2.0)) < 1e-6);
  values.reset();
  values.add(-2);
  for (int i = 0; i < 3; ++i) values.add(0);
  result = values.result();
  assert(result.rms == 1 && result.peak == 2 && result.crestFactor == 2);
  std::cout << "Firmware features: zero, sine, and impulse passed\n";
}
