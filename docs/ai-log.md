# AI assistance log

## 2026-11-21 — Workspace initialization

- Request: initialize N06/E2 from Danh's TH4 archive, preserving useful code and removing obsolete lab artifacts.
- Human decisions: advanced target via FFT; Wokwi first; physical-kit validation later; reuse the TH4 Python backend.
- AI-assisted work: adapt MQTT, REST, storage, and dashboard; add MPU6050/synthetic sampling and feature accumulation; draft context files, scoped workbook extraction, tests, and run instructions.
- Reused source: Danh's TH4 submission; provenance is recorded in README.
- Scope boundary: no official TH5 dataset, trained tree, prediction accuracy, evaluated FFT feature, or physical-kit evidence exists yet.
- Validation: 12 tests passed, including real local MQTT transport/acknowledgments with a software peer; zero/sine/impulse C++ feature checks and wiring consistency passed; dashboard JavaScript syntax passed.
- ESP32 compilation: Arduino CLI 1.6.0, esp32 core 4.0.0, PubSubClient 2.8.0, ArduinoJson 7.4.3; 1,022,387 bytes flash and 52,860 bytes static RAM.
- Verification limit: the browser permission gate declined the localhost preview. Visual dashboard review and execution on Wokwi/physical hardware remain pending; software-peer tests are not hardware evidence.
- Human review: each member must understand and be able to edit their assigned code before oral assessment.

## 2026-11-21 — Contract hardening and Git governance

The user approved contract fixes before the first commit and a public repository named
`DanhLent/edge-vibration-monitor`, with onboarding TODOs for missing Nhat/Dat GitHub handles.
AI assisted implementation, regression tests, CI, progressive-disclosure specs, and repository setup.
[Danh's bootstrap record](ai/danh.md) records this work. Future entries belong in the individual logs:
[Nhat](ai/nhat.md) and [Dat](ai/dat.md). These placeholders do not claim contributions by those members.
See STATE.md for verified results and pending Wokwi/data/model gates.

## Advanced FFT extension

AI assisted the mixed-radix FFT implementation, raw trace replay, locked
split comparison, C export, spectral telemetry v2, dashboard, and Wokwi
measurement tools. Danh authored the local reference drafts. Official
rows and benchmark images containing them remain in ignored storage.
See the [FFT evidence](../deliverables/measurements/wokwi-fft/README.md)
for simulator results and open verification gates.
