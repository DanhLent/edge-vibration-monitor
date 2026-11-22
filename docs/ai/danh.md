# Danh — AI assistance

## 2026-11-21 — Reviewed bootstrap

- Human request: audit interfaces and implement the approved Git/governance plan; public repository named edge-vibration-monitor; placeholders for missing Nhat/Dat handles.
- AI-assisted work: firmware sampling/protocol extraction and unavailable C stub; v1 validation, storage/presence/ACK retries, dashboard readiness, regression checks, CI, and documentation.
- Source provenance: original TH4 networking/backend foundations are Danh's; the E2 bootstrap and hardening used AI assistance.
- Verification: host C/C++ and local software-peer MQTT tests; compilation and dashboard checks. Exact current results are in STATE.md.
- Limits: no Wokwi execution, trained model, actual ESP32/Python parity, evaluated FFT, or physical-kit evidence.
- Human understanding: Danh must review and rehearse explanation/live changes; AI-produced code is not evidence of completed oral assessment.
- Git verification: initial commit 84e4b16, public clone exclusions, successful GitHub CI, main protection, and empty starter branches. Supported action runtimes are checked through the final bootstrap PR.

## 2026-11-22 — Backend/MQTT verification tooling

- Human request: implement the approved CLI-first capture plan on danh/backend-mqtt; preserve firmware/ML ownership, push only Danh's branch, and leave the PR for manual merge.
- AI-assisted work: capture runner, read-only sampling/command/traffic CSV exporter, six regression tests, usage/evidence instructions and local-only pre-onboarding draft guardrails.
- Provenance: adapt TH3 official CLI/measurement patterns and TH4 fresh-backend/MQTT correlation; do not copy old profiles, tokens, databases, payload records or browser security settings.
- Verified: 25 Python tests, dashboard syntax/control checks, and unchanged ESP32 compilation (1,026,419 bytes flash; 52,764 bytes static RAM).
- Scope: no firmware, model, wire/API contract or database-schema changes. Tests use an explicitly identified software peer and do not establish Wokwi or ESP32 model parity.
- Runtime/browser outcomes and safe selected evidence are recorded separately in STATE.md and deliverables; unfinished gates remain explicit.
- Runtime: unchanged local build produced 37 valid stored normal-mode windows and one done ACK (1931.258 ms backend latency). Wokwi API ended at the five-minute connection limit before the requested mode schedule completed.
- Browser: support-file upload worked; replacement confirmation stalled. No E2 public saved-source link was verified. Dashboard navigation was attempted after capture shutdown and returned connection refused; visual/control evidence remains pending.
- Evidence review: publish only validated synthetic CSVs and a sanitized manifest/summary; retain Serial, MQTT traces, database, browser draft and private token outside tracked outputs. No firmware fix or paid-plan upgrade was attempted.
- Human understanding: Danh must review the capture lifecycle, byte/clock conventions, export joins and failure handling and rehearse a live modification.

- Additional bounded diagnostic: unchanged build `da66910`, one-second mode holds, all three input modes, 15 windows and 10/10 done ACKs with matching windows; latency range 871.833–1180.456 ms. Published separately and explicitly excluded from the required 60-second duration claim.

- Git delivery: only danh/backend-mqtt pushed, authored under DanhLent's verified identity; PR https://github.com/DanhLent/edge-vibration-monitor/pull/2 targets main and remains open for manual review/merge.
- Required CI passed on 2096a44: Baseline checks and Conventional commits, https://github.com/DanhLent/edge-vibration-monitor/actions/runs/44948727036. The final status-documentation commit must also pass both checks before handoff.
- Public audit: no private token, database, archive, profile or build binary tracked; both CSV manifests match their published hashes. Firmware/ML and teammate remote branches remain unchanged; no reference drafts were created.
