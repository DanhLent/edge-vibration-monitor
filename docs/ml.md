# ML and FFT gates

Lead: Nhat. No official TH5 dataset, trained tree, validated accuracy, or evaluated FFT feature exists.
The mandatory baseline remains a scikit-learn decision tree of depth ≤3 using only RMS and absolute peak.
Read [C/feature contract](interfaces.md) before training or exporting.

## Data acceptance

Store original and derived data under ignored `ml/datasets/`. Track only safe metadata: source and
SHA-256, RMS/peak columns, units, axis, gravity/DC preprocessing, class mapping, time/order information,
and original sampling rate. Inspect ranges and calibrate Dat's synthetic amplitudes and feature
calculation to match the official data before evaluating simulation predictions. Preserve raw data.
Missing reliable acquisition order blocks a temporal-split claim; document it and obtain clarification.

Keep an untouched temporal test partition and record the split boundaries, acquisition grouping,
leakage controls, and random seed in the notebook. Define the exact split after dataset inspection;
do not fabricate chronology or mix overlapping acquisition windows across train/test.
Compare temporal and random splits, confusion matrices in normal/imbalance/loose order, and F1 with
an explicit averaging convention. Macro F1 is the default reporting convention. Evaluate an
always-normal classifier on each corresponding test partition.

## Export and activation

Keep RMS/absolute-peak input order and float32 coercion consistent with sklearn inference. Export
actual learned thresholds with sufficient precision (17 significant decimal digits), preserve <=
branch routing, and map tree.classes_ explicitly to the C class IDs. Do not round thresholds for display
and then reuse the display values in C.

Replace only the generated model implementation and coordinated interface changes. Keep readiness
false for deployment until actual ESP32/Python test vectors agree 100%, including held-out vectors
and float32 values at/immediately adjacent to every threshold. Record vectors, predictions, model/data
hashes, export settings, and device evidence in the parity table. Host C comparisons supplement
this gate; untrained stub tests do not count as trained-model accuracy or ESP32 parity.

## Advanced FFT

Retain the mandatory two-feature tree and evaluate FFT separately. Frequency features require
available raw signals and trustworthy timing; an RMS/peak-only table is insufficient for FFT.
Select FFT size, sampling/window treatment, features, and evaluation after inspecting raw data.
Compare against the mandatory baseline using compatible evaluation partitions and report MCU
resource/timing cost plus limitations. Int8 MLP is optional and is not selected bootstrap work.
Commit the training notebook with outputs cleared of private records, reproducible export code,
safe evaluation summaries, and model/parity artifacts. Each member must understand their own code.
