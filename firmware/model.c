#include "model.h"

// Enable readiness only after official-data training and recorded ESP32 parity.
bool model_is_ready(void) { return false; }

int8_t model_predict(float rms, float peak) {
  (void)rms;
  (void)peak;
  return DIAGNOSIS_UNAVAILABLE;
}
