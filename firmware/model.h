#pragma once
#include <stdbool.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

enum Diagnosis {
  DIAGNOSIS_UNAVAILABLE = -1,
  DIAGNOSIS_NORMAL = 0,
  DIAGNOSIS_IMBALANCE = 1,
  DIAGNOSIS_LOOSE = 2
};

bool model_is_ready(void);
int8_t model_predict(float rms, float peak);

#ifdef __cplusplus
}
#endif
