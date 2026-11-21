# Edge vibration monitor

[GitHub repository](https://github.com/DanhLent/edge-vibration-monitor) · CE339 N06 / E2 · Danh, Nhat, Dat

ESP32 fan/motor vibration monitoring with MPU6050, MQTT, a FastAPI/SQLite dashboard, and a planned
shallow decision-tree diagnosis. Target: evaluated FFT extension, Wokwi first, physical kit later.

The reviewed scaffold computes one-second RMS, absolute peak, and crest factor, publishes v1 JSON,
stores unique measurement windows, and provides acknowledged simulation-mode control.
**The trained model is unavailable: predictions are null and diagnosis LEDs remain off.**
Synthetic modes are provisional inputs, not validated predictions. Wokwi runtime, official TH5
calibration/training, traffic experiments, evaluated FFT, and physical validation remain pending.

## Start the backend

Use Python 3.12 for the tested development environment:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.lock
.venv/bin/python -m backend.api
```

Open [dashboard](http://127.0.0.1:8000) or [API documentation](http://127.0.0.1:8000/docs).
Runtime dependencies alone are listed in `backend/requirements.txt`. Environment overrides:
MQTT_HOST, MQTT_PORT, DB_PATH, API_PORT, COMMAND_TTL (default 15 seconds).
The default public broker is test.mosquitto.org:1883; SQLite output is ignored `artifacts/iot.db`.
Pre-v1 local databases require archival and a fresh DB_PATH.

## Wokwi and hardware

Copy `firmware/` into an ESP32 Arduino Wokwi project, keeping sketch.ino as the main sketch and using
the supplied diagram.json and libraries.txt. Wokwi Public Gateway requires an Internet broker;
backend and ESP32 both connect outward to it. There is no ESP32 web server.

Pins: MPU6050 SDA/SCL 21/22, AD0 to GND; button 18 to GND with pull-up; green/yellow/red LEDs
25/26/27 through individual 220 Ω resistors. OLED is deferred.
Default acquisition is nominal 1 kHz with raw X-axis acceleration in provisional g. Synthetic
normal/imbalance/loose inputs are selected by button or dashboard; amplitudes await TH5 calibration.
Failed physical reads never fall back to generated data. For a physical kit, copy
config.local.h.example to ignored config.local.h and set credentials/source there.
Read [hardware verification gates](docs/hardware.md) before claiming runtime behavior.

## Interfaces

Topic base: `ce339/N06/e2/esp32-01`. `/telemetry` is non-retained QoS 0; `/status` is retained
(QoS 0 online, QoS 1 Last Will); `/cmd` is non-retained QoS 1; `/ack` is non-retained QoS 0.
Commands use IDs, expiry, duplicate-result caching, and one-second application retries. Dashboard
controls require a connected/subscribed backend and a fresh online synthetic device with ready clock
and sampling. Current mode comes from live status; historical window mode remains attached to its features.
The unavailable C stub and all JSON/REST definitions are in [interface contract](docs/interfaces.md).

## Verification and team work

Local verification: 25 Python tests, including actual host-compiled firmware serialization/command
logic and real local MQTT transport with a software peer. C/C++ checks cover feature math, window
boundaries, and the unavailable stub. ESP32 compilation and dashboard syntax/control checks also pass.
These checks do not establish Wokwi execution, hardware accuracy, or trained-model parity.

See [workflow](docs/workflow.md) for the pinned toolchain, reproduction commands, branch ownership,
Conventional Commits, PR reviews, and onboarding TODOs. Root AGENTS.md stays under 60 lines;
[specification index](docs/README.md) routes detailed work. [STATE.md](STATE.md) tracks verified progress.
Private TH5 data and the original course workbook are excluded from this public repository; scoped
[course requirements](docs/requirements.md) preserve relevant requirements and source hash.
Submission evidence belongs under [deliverables](deliverables/README.md).

## TH4 provenance and AI use

MQTT callbacks, SQLite synchronization, REST/command lifecycle, dashboard foundations, and Arduino
network reconnect/Last-Will foundations were adapted from Danh's TH4_23520241_LeNguyenThanhDanh
submission. Obsolete pump/relay/potentiometer features and old lab results were removed.
AI assisted the E2 scaffold and its contract hardening, sampling/features, C stub, revised JSON/API/
storage/dashboard, tests, requirement extraction, CI, and documentation. No trained ML artifact exists.
The initial Git author records Danh's actual account; starter branches and onboarding placeholders
claim no Nhat/Dat contributions. Members must commit their real work through their own accounts,
record assistance, and explain/modify their own code during oral assessment.
See [AI log](docs/ai-log.md) and member records for provenance and verification limits.

## Capture integration measurements

The official Wokwi CLI capture runner builds unchanged firmware, observes MQTT, runs acknowledged
mode commands, and exports cadence, command latency and received-payload CSVs from a fresh backend.
See [capture and review instructions](docs/reporting.md#wokwi-cli-capture) for private token setup,
bounded runs, public web-source verification and separate dashboard evidence. Outputs begin under
ignored `artifacts/`; only reviewed synthetic evidence belongs in `deliverables/measurements/`.
The tooling and its tests used AI assistance, adapting TH3 CLI/measurement patterns and TH4
backend correlation. Firmware/model behavior is unchanged; runtime findings remain Dat follow-ups.
