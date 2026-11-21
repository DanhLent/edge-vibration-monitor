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

## Wokwi CLI capture

Run from the repository root with the existing development environment. Install the official
[Wokwi CLI](https://docs.wokwi.com/wokwi-ci/cli-installation) in ignored `.tools/` or supply
an executable path. Version 0.29.1 is the locally inspected reference; the manifest records the
actual version. Use the project Arduino toolchain pinned in [workflow](workflow.md).
Keep a token in a private file outside the public checkout (permission 600), or supply
`WOKWI_CLI_TOKEN` through your local environment. Never put token values in arguments or documents.

```bash
.venv/bin/python -m scripts.capture_wokwi \
  --wokwi-cli .tools/wokwi-cli \
  --token-file ~/.config/ce339/wokwi_token
```

The runner builds unchanged firmware, creates `artifacts/wokwi/<run-id>/`, starts its own fresh
backend/database and passive observer, then launches CLI with a merged BIN, ELF, and diagram.
It refuses local/private configuration and uncommitted firmware inputs. Backend broker overrides
are refused because the unchanged baseline targets test.mosquitto.org:1883. Only run one E2
simulator on these fixed public topics; unexpected live boots abort acceptance as possible collisions.

Defaults: 60 device-uptime seconds per mode, ten serialized REST commands, 120-second startup/readiness
waits, and a 900-second overall wall budget including compilation. `--mode-seconds`, `--startup-timeout`,
and `--wall-timeout` allow bounded diagnostic runs; shortened captures do not satisfy the 60-second gate.
CLI itself has a 600-second simulation-time ceiling. These clocks can advance at different rates.
Each command must reach a successful persisted terminal state and a new matching-mode window.
Current live status must also match the applied mode. Command failures stop the exercise and preserve
partial data. Exit 0 means `CAPTURED_PENDING_REVIEW`; exit 2 means `BLOCKED` or `INCOMPLETE`.
Neither establishes visual review, diagnosis accuracy, or completed course acceptance.

The 2026-11-22 reference run hit the token tier's five-minute API connection limit after only
about 38 device-uptime seconds. Increasing `--wall-timeout` does not extend that service limit.
The partial capture is evidence of transport/one ACK, not the complete three-mode/ten-command gate.
Dat must investigate runtime throughput before selecting a later acquisition/runtime adjustment;
Danh's tooling does not change firmware or upgrade a paid plan to bypass this constraint.

The runner prints its localhost dashboard URL. Add `--dashboard-seconds 120` to keep capture open
after the REST exercise for one separate dashboard command. Apply a different mode, wait for its
ACK and new window, and capture live/control-complete screenshots. Inspect health, feature values,
chart feature selection, synthetic warnings, and Model unavailable. Empty/disconnected views and
button/reconnect tests are separate conditions. Browser checks remain NOT RUN until independently
documented; the capture script does not simulate clicks or manufacture screenshots.

Save a new E2 web project with all public `.ino`, `.h`, `.c`, and `.cpp` firmware files plus
`diagram.json` and `libraries.txt`. Exclude `config.local.h` and its example from uploads. Reload
the saved URL and compare every file against `source_sha256`. A clean-context readback should
also match. `--wokwi-url https://wokwi.com/projects/<id>` records a link without asserting this check
passed. Web compilation uses Wokwi's toolchain; CLI runtime uses the recorded local build.
CLI component screenshots do not replace full browser evidence. PCAP is not required for this
payload-byte phase and stays private if captured for diagnosis.

## Export and review

After capture, `measurements/` within the ignored run directory contains sampling, commands,
traffic CSVs and a safe manifest. Re-export only that run's dedicated database:

```bash
.venv/bin/python -m scripts.export_measurements artifacts/wokwi/<run-id>
```

Sampling rows are complete validated, unique stored synthetic windows, joined by boot/window IDs
to the first corresponding observer message. Payload bytes come from the original received bytes,
not SQLite's reserialized JSON. Cadence is blank across boot/mode transitions; window-ID deltas
make skipped windows visible. Stored/observer discrepancies are findings. Actual rate comes from
the device's count/duration contract, independently of publishing cadence.

Command latency uses `(updated-created)*1000` only for done/done resources; failures, expiry and
pending commands leave it blank. Observer ACK time is a separate timestamp. Traffic retains all
observed messages, including malformed payload lengths, retries, duplicate windows and retained
replay, grouped by topic kind/retained/valid flags. MQTT DUP flags do not identify every application
retry. Observer disconnect boundaries are recorded; totals are subscriber-received payload bytes,
not authoritative device-sent or wire totals.

Review CSVs, hashes, conditions, source identity and findings before copying selected small outputs
to `deliverables/measurements/<run-id>/` using `--output`. Keep raw observer/Serial/browser logs,
SQLite, token files, profiles, build binaries and PCAP under ignored locations. Never export an
old lab database. Preserve failed runs; never replace Wokwi results with software-peer fixtures.
