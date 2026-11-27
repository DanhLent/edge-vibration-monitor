# STATE — CE339 N06 / E2
Updated: 2026-11-28
Members: Danh (Backend/MQTT), Nhat (ML/FFT), Dat (Firmware/Wokwi).
Verified GitHub: Danh @DanhLent; Nhat @GreenyB (API login Greenyb); Dat @nguyenngac214.
Target: advanced level via FFT; Wokwi first, physical-kit validation later.
Stack: Arduino ESP32 + MQTT + reused TH4 FastAPI/SQLite/HTML dashboard.
Repository: https://github.com/DanhLent/edge-vibration-monitor (public).
Current phase: Public integration and spectral telemetry backend merged. Official TH5 received. Teammate write invitations remain pending.
Public main keeps the reviewed baseline while the TH5 firmware and model are developed and tested on local drafts.

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
- [x] Verify official simulated TH5 data, including UTC burst ordering and centered X-axis RMS/peak in g.
- [ ] Confirm distinct project context, calendar deadlines, and measurement conventions.
- [ ] Document block/wiring diagrams, MQTT topics, both data flows, and target metrics.
- [ ] Read MPU6050; implement simulation modes and one-second feature windows.
- [ ] Submit the 4–6-page report and initial Wokwi link; prepare a 5-minute presentation.

## Milestone 2 — Week 11 (30%)
- [x] Verify local Wokwi device → MQTT → dashboard and dashboard → device acknowledgments.
- [ ] Record sampling/publish timing and command latency in CSV.
- [x] Document official TH5 provenance and evaluation splits in the local ML handoff.
- [ ] Submit Wokwi link, source, measurement CSV, and short demo; rehearse individual questions.

## Milestone 3 — Weeks 14–15 (40%)
- [x] Train/export the depth-3 RMS/peak tree and verify classification and LED behavior in the local Wokwi build.
- [x] Verify 100% ESP32/Python inference parity on Wokwi probes and private emulator holdout vectors.
- [x] Report temporal and grouped-random macro F1, confusion matrices, and always-normal results.
- [x] Verify event/heartbeat publishing and ≥10× payload reduction against a matched Wokwi raw baseline.
- [x] Implement and evaluate FFT features while preserving the mandatory tree baseline.
- [x] Verify live FFT dashboard, baseline selection, event heartbeat, and ≥10× paired Wokwi traffic reduction.
- [ ] Validate on a physical ESP32/MPU6050 kit and capture hardware evidence.
- [ ] Finish CSV results, parity table, training notebook, and limitations analysis.
- [ ] Finish final PDF, slides, dashboard evidence, 3–5-minute video, README, and AI log.
- [ ] Audit submission links/files and rehearse each member's explanation and live edits.

## Local TH5 Wokwi verification — 2026-11-27

- The three calibrated inputs each passed 61 consecutive Wokwi windows and
  at least 60 device seconds. The virtual button advanced through all modes.
- Browser Apply produced a correlated MQTT ACK in 0.993 s and a newer
  same-boot feature window with an imbalance prediction.
- The matched Wokwi traffic experiment reduced received payload by 37.79×
  (97.35%). The event stream included two class changes and a 60-second
  feature heartbeat.
- The official TH5 tree reached 0.3557 temporal macro F1 (0.2820 always-normal)
  and 0.5331 grouped-random macro F1 (0.2921 always-normal). The temporal
  loose-mount class had one true positive out of 1,080 windows.
- Parity was 12,188/12,188 on Wokwi ESP32 independent probes and
  7,797/7,797 on private held-out and boundary vectors in host C and
  Espressif QEMU. Physical-kit verification is pending.

Published evidence: [dashboard](deliverables/dashboard/wokwi-th5/README.md),
[traffic and circuit](deliverables/measurements/wokwi-th5-traffic/README.md).
The trained source and runnable simulator project are local handoffs.
The public checkout uses the bootstrap firmware until member-owned PRs land.

## Local advanced FFT verification

- Locked temporal/grouped-random macro F1 reached 0.7591/0.7986. The
  mandatory tree C export is unchanged and remains selectable.
- Private ESP32 replay matched NumPy on both bands for all 60 TH5 raw
  windows. Wokwi matched 6,018 independent C/Python inference probes.
- The diagnostic Wokwi capture exercised all three calibrated classes.
  [FFT evidence](deliverables/measurements/wokwi-fft/README.md) records the
  measured transform timing, resource delta, and acceptance status. A separate
  Wokwi 1 kHz timer test measured zero missed notifications in both phases.
- Live dashboard control reported a correlated ACK and spectral history on
  the same boot. Paired Wokwi runs measured 34.13× lower MQTT payload rate.
- The virtual button verified the mandatory model in all three modes while
  spectral telemetry stayed enabled.

## Historical pre-TH5 next action
Complete one bounded CLI liveness check before further Wokwi/browser captures; retain local drafts and export offline handoffs if boot remains blocked.
Teammates must accept write invitations. Obtain official TH5 data and confirm its definitions before training.
Keep predictions unavailable until the official dataset and exported tree are validated.
Dat follow-up: investigate slow simulation/missed ticks and the five-minute CLI API connection limit;
complete 60 device seconds per mode and browser evidence without mixing firmware into Danh's PR.

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
- [x] Verify Nhat/Dat's GitHub handles and send write collaborator invitations.
- [ ] Enable one non-author approval after both invitations are accepted and Danh's pre-TH5 PRs are merged.
- [x] Capture backend/dashboard and traffic evidence.
- [ ] rehearse explanation/live modification.
### Nhat — ML/FFT
- [x] Verify GitHub handle through the GitHub API.
- [ ] Accept the repository write invitation.
- [ ] Obtain official TH5 data, train/evaluate/export, record actual ESP32 parity, evaluate FFT.
### Dat — Firmware/Wokwi
- [x] Verify GitHub handle through the GitHub API.
- [ ] Accept the repository write invitation.
- [ ] Verify Wokwi timing/control and physical-kit behavior with measurements and evidence.

## Danh integration tooling — 2026-11-22
- [x] Audit TH3/TH4 automation without importing profiles, databases, credentials or old lab data.
- [x] Add fresh-run backend/MQTT capture, exact received-byte accounting, cadence and successful ACK latency CSVs.
- [x] Verify local-broker retry correlation, duplicate/retained handling, incomplete exports and separate clocks.
- [x] Compile unchanged firmware: 1,026,419 bytes flash, 52,764 bytes static RAM; diagnosis remains unavailable.
- [x] Document CLI/browser evidence separation and local-only teammate reference drafts; AGENTS.md remains under 60 lines.
- [x] Capture partial unchanged-build Wokwi CLI evidence: 37 normal windows, one successful command, 13,753 received payload bytes.
- [ ] Complete 60 device seconds in all modes; the longer run hit its five-minute API connection limit.
- [x] Short diagnostic: all three modes, 15 stored windows and ten successful commands with matching windows; one-second holds do not satisfy the duration gate.
- [ ] Save/source-verify an E2 web link; in-app starter-file replacement stalled on a confirmation dialog.
- [ ] Verify dashboard visually/control through the browser; the attempted URL refused connection after capture shutdown.
- [x] Merge https://github.com/DanhLent/edge-vibration-monitor/pull/2 through merge commit 4827210; remove the finished branch.
- [x] Verify Baseline checks and Conventional commits: https://github.com/DanhLent/edge-vibration-monitor/actions/runs/44948727036 (2096a44).

Partial run: deliverables/measurements/20261121T203825Z-0af0d6 (UTC ID; local date 2026-11-22).
Measured rate 696.9847–1000.479 Hz; 36.017 s between stored completions; missed notifications rose to 331.
Successful backend command latency 1931.258 ms. These are provisional synthetic integration measurements,
not full-mode acceptance, wire traffic, reduction evidence, model validation or physical-kit results.

Short diagnostic: deliverables/measurements/20261121T204925Z-606cca; 48 received messages / 9,176 payload bytes.
Ten done/done command latencies 871.833–1180.456 ms; median 1056.005 ms.

## Teammate onboarding — 2026-11-24
- [x] Verify @nguyenngac214 (Dat, API user ID 360623354) and @GreenyB (Nhat, API login Greenyb, user ID 81990354).
- [x] Send repository write invitations to both accounts; acceptance remains pending.
- [x] Assign one effective CODEOWNER per path: Danh for backend/scripts/dashboard/governance, Dat for firmware/hardware, Nhat for ML/model artifacts.
- [ ] Confirm both invitations are accepted before requiring a non-author review.

Single-owner rules replace the reviewer-pair onboarding guidance for this pre-TH5 work.
Main still requires both CI checks, up-to-date PRs, and resolved conversations; stale approvals are dismissed.
The approval count remains zero and code-owner review remains disabled until the planned later review-policy change.
Do not push local reference drafts or advance teammate starter branches; teammates review, adapt, and commit their own work.
