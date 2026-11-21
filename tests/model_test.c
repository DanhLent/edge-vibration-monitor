#include "model.h"
#include <assert.h>
#include <math.h>

int main(void) {
  assert(!model_is_ready());
  assert(model_predict(0.2f, 0.4f) == DIAGNOSIS_UNAVAILABLE);
  assert(model_predict(NAN, INFINITY) == DIAGNOSIS_UNAVAILABLE);
  assert(DIAGNOSIS_NORMAL == 0 && DIAGNOSIS_IMBALANCE == 1 && DIAGNOSIS_LOOSE == 2);
  return 0;
}
