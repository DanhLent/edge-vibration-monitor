# STATE — CE339 N06 / E2
Updated: 2026-11-22
Members: Danh (Backend/MQTT), Nhat (ML/FFT), Dat (Firmware/Wokwi).
Target: advanced level via FFT; Wokwi first, physical-kit validation later.
Stack: Arduino ESP32 + MQTT + reused TH4 FastAPI/SQLite/HTML dashboard.
Repository: https://github.com/DanhLent/edge-vibration-monitor (public).
Current phase: Danh tooling verified; partial Wokwi CLI evidence captured, full runtime/browser gates and official TH5 data pending.

## Initialization
- [x] Inspect all seven workbook sheets; isolate N06/E2 and applicable shared rules.
- [x] Confirm advanced target, FFT direction, Wokwi-first/physical-kit path, and TH4 reuse.
- [x] Inspect the TH4 archive and identify reusable code and cleanup candidates.
- [x] Initialize the approved workspace and adapt the TH4 core for E2.
- [x] Exclude obsolete lab artifacts; delete the archive after successful verification.
- [x] Create AGENTS.md, STATE.md, scoped requirements, README, and AI log.
- [x] Assign member roles and establish a shared Git repository.

## Initialization verification
- [x] Pass 12 tests: backend validation/storage/commands, C++ features, wiring, requirements, and local MQTT round trip.
- [x] Compile ESP32 firmware: Arduino CLI 1.6.0, esp32 core 4.0.0; 78% flash, 16% static RAM.
- [x] Check dashboard JavaScript syntax and unavailable-model/disconnected API behavior.
- [ ] Visually verify the dashboard; browser access to the localhost preview was declined.
- [ ] Run the firmware in Wokwi and measure actual sensor/sampling/MQTT behavior.

## Milestone 1 — Week 7 (30%)
- [ ] Obtain official TH5 data; confirm units, axis, preprocessing, labels, and time order.
- [ ] Confirm distinct project context, calendar deadlines, and measurement conventions.
- [ ] Document block/wiring diagrams, MQTT topics, both data flows, and target metrics.
- [ ] Read MPU6050; implement simulation modes and one-second feature windows.
- [ ] Submit the 4–6-page report and initial Wokwi link; prepare a 5-minute presentation.

## Milestone 2 — Week 11 (30%)
- [ ] Verify device → MQTT → backend/dashboard and dashboard → device acknowledgments.
- [ ] Record sampling/publish timing and command latency in CSV.
- [ ] Prepare and document the AI dataset and evaluation split.
- [ ] Submit Wokwi link, source, measurement CSV, and short demo; rehearse individual questions.

## Milestone 3 — Weeks 14–15 (40%)
- [ ] Train/export the depth-3 RMS/peak tree; deploy classification and state LEDs.
- [ ] Verify 100% ESP32/Python test-vector agreement, including threshold boundaries.
- [ ] Report temporal F1 and always-normal baseline; compare splits/confusion matrices.
- [ ] Verify event/heartbeat publishing and >= 10x reduction against a defined raw baseline.
- [ ] Implement/evaluate FFT features while preserving the mandatory tree baseline.
- [ ] Validate on a physical ESP32/MPU6050 kit and capture hardware evidence.
- [ ] Finish CSV results, parity table, training notebook, and limitations analysis.
- [ ] Finish final PDF, slides, dashboard evidence, 3–5-minute video, README, and AI log.
- [ ] Audit submission links/files and rehearse each member's explanation and live edits.

## Next action
Run Wokwi and obtain official TH5 data; confirm its definitions before training.
Keep predictions unavailable until the official dataset and exported tree are validated.
Dat follow-up: investigate slow simulation/missed ticks and the five-minute CLI API connection limit;
complete 60 device seconds per mode, ten commands and browser evidence without mixing firmware into Danh's PR.

## Reviewed bootstrap — 2026-11-21
- [x] Fix window boundaries and immutable completion metadata; count missed timer notifications.
- [x] Add unavailable C inference API with one readiness implementation and LEDs off.
- [x] Separate ACK/status; add retries, exact expiry, and current-state/measurement separation.
- [x] Add v1 validation, boot/window deduplication, and fresh clock/sampling/presence command gates.
- [x] Pass 19 tests including real host firmware serialization/parser and local MQTT loss/reconnect checks.
- [x] Compile hardened ESP32 sketch: 1,026,419 bytes flash (78%), 52,764 bytes static RAM (16%).
- [x] Add progressive-disclosure specs, Conventional Commits, CI, and onboarding CODEOWNERS TODOs.
- [x] Verify clean staged public checkout: host/MQTT/dashboard/ESP32 checks; local-only workbook test skipped.
- [x] Verify dashboard syntax and control/diagnosis guards; visual review remains pending.
- [x] Verify GitHub CI: https://github.com/DanhLent/edge-vibration-monitor/actions/runs/44892723396.
- [x] Protect main: PRs, both required checks, up-to-date branches, resolved conversations, no force pushes/deletion.
- [x] Create starter branches for Danh/Nhat/Dat without member-authored changes; solo approval count is zero.
- [x] Upgrade CI actions to verified Node 24 runtimes after GitHub reported deprecated checkout runtime.

## Member progress
### Danh — Backend/MQTT and integration
- [x] Reviewed AI-assisted bootstrap is locally verified; provenance is in README and docs/ai/danh.md.
- [x] Add unchanged-firmware Wokwi CLI capture and read-only CSV export; pass 25 tests and ESP32 compilation.
- [ ] Add Nhat/Dat's verified GitHub handles and collaborators; activate reviewer pairs/required approval.
- [ ] Capture backend/dashboard and traffic evidence; rehearse explanation/live modification.
### Nhat — ML/FFT
- [ ] Supply verified GitHub handle and accept repository access.
- [ ] Obtain official TH5 data, train/evaluate/export, record actual ESP32 parity, evaluate FFT.
### Dat — Firmware/Wokwi
- [ ] Supply verified GitHub handle and accept repository access.
- [ ] Verify Wokwi timing/control and physical-kit behavior with measurements and evidence.

## Danh integration tooling — 2026-11-22
- [x] Audit TH3/TH4 automation without importing profiles, databases, credentials or old lab data.
- [x] Add fresh-run backend/MQTT capture, exact received-byte accounting, cadence and successful ACK latency CSVs.
- [x] Verify local-broker retry correlation, duplicate/retained handling, incomplete exports and separate clocks.
- [x] Compile unchanged firmware: 1,026,419 bytes flash, 52,764 bytes static RAM; diagnosis remains unavailable.
- [x] Document CLI/browser evidence separation and local-only teammate reference drafts; AGENTS.md remains under 60 lines.
- [x] Capture partial unchanged-build Wokwi CLI evidence: 37 normal windows, one successful command, 13,753 received payload bytes.
- [ ] Complete 60 device seconds in all modes and ten commands; API disconnected after its five-minute tier limit.
- [ ] Save/source-verify an E2 web link; in-app starter-file replacement stalled on a confirmation dialog.
- [ ] Verify dashboard visually/control through the browser; the attempted URL refused connection after capture shutdown.
- [ ] Open Danh's tooling PR and verify both required CI checks; leave manual merge to Danh.

Partial run: deliverables/measurements/20261121T203825Z-0af0d6 (UTC ID; local date 2026-11-22).
Measured rate 696.9847–1000.479 Hz; 36.017 s between stored completions; missed notifications rose to 331.
Successful backend command latency 1931.258 ms. These are provisional synthetic integration measurements,
not full-mode acceptance, wire traffic, reduction evidence, model validation or physical-kit results.
