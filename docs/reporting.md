# Reports and measurement evidence

Danh coordinates delivery; Dat owns acquisition/hardware evidence; Nhat owns ML/FFT evaluation.
Course source: [requirements](requirements.md). Calendar deadlines remain unconfirmed.

| Milestone | Weight | Evidence |
| --- | --- | --- |
| Week 7 | 30% | 4–6-page report, block/wiring/topic diagrams, monitoring/control flows, target metrics, initial Wokwi link; 5-minute presentation |
| Week 11 | 30% | End-to-end Wokwi/MQTT/dashboard evidence, source, timing/command CSV, available AI dataset, short demo |
| Weeks 14–15 | 40% | Trained baseline and actual ESP32 parity, F1/baselines/split confusion matrices, traffic reduction, evaluated FFT, final PDF/slides, 3–5-minute video, AI log |

Use clear numbered sections, figures, and tables. Every chart/table states units, source, run/date,
measurement method, and whether data is synthetic or physical. Caption screenshots with the exact
condition shown. Link evidence files from README; put small CSVs, final PDFs, and slides under
`deliverables/measurements`, `deliverables/reports`, and `deliverables/slides`. Large videos use release assets.
Use g only while acceleration units remain provisional; confirm TH5 conventions before final claims.

## Measurement conventions

- Sampling CSV: run ID, source/mode, boot/window IDs, nominal rate, count, actual duration/rate, missed timer notifications, sensor health, completion timestamp, backend receipt timestamp.
- Command CSV: run/device/command ID, requested mode, creation/expiry/ACK receipt times, result, successful backend round-trip latency. Record failed/expired commands separately from successful latency statistics.
- Parity CSV: vector ID, RMS/peak, expected Python class, actual ESP32 class, agreement, model hash. Include threshold-boundary vectors.
- ML results: dataset/model/split provenance, class support/order, temporal and random confusion matrices, macro F1, always-normal results, and limitations.

Stats currently count received telemetry payload bytes/messages for the backend session and unique
stored windows. They exclude protocol overhead and are not proof of traffic reduction.
Before the event-publishing experiment, define equal-duration raw and event/heartbeat runs with the
same sample rate, source/mode schedule, encoding, and control schedule. Count serialized MQTT payload
bytes and messages, including status/ACK traffic in the optimized total; distinguish payload from wire
overhead. Record reconnects/retries and session-counter resets. Claim ≥10× reduction only after
measured evidence supports raw_bytes/optimized_bytes ≥10; reduction percentage is
100 × (1 − optimized_bytes/raw_bytes).

Keep one-second publishing for bootstrap. Event publishing and a sparse feature heartbeat are later
milestone implementation, based on predicted-class changes after validated inference. Do not use
simulation input labels as validated diagnoses. Explain physical-kit evidence and remaining limitations.
All three members rehearse explanation and live modification of their own contributions.
