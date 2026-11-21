# CE339 — Group N06 / Topic E2
Members: Danh, Nhat, Dat.
Project: fan/motor vibration monitoring and ESP32 decision-tree diagnosis.
Source: DeTai_BTL_CE339_2026.xlsx; full scoped requirements: docs/requirements.md.
Read this file and STATE.md before working; update STATE.md after verified progress.

## Requirements
- Use one ESP32, MPU6050, three state LEDs, and a simulation-mode button.
- Start in Wokwi; validate later on a physical kit. OLED is optional.
- Sample at 200–1000 Hz; compute RMS, absolute peak, and crest factor each second.
- Generate normal, imbalance, and loose-mount vibration signals in Wokwi.
- Match simulation amplitudes, units, and feature definitions to the official TH5 data.
- Train a scikit-learn tree of depth <= 3 using only RMS and peak.
- Export faithful C if–else inference; LEDs show the predicted class.
- Send features/predictions through MQTT and display them on the dashboard.
- Use MQTT topics under ce339/N06/; support dashboard control and acknowledgment.
- Require 100% ESP32/Python prediction agreement on the test vectors.
- Report temporal-split F1 and compare with an always-normal classifier.
- Complete event-based publishing plus a sparse heartbeat; demonstrate >= 10x traffic reduction.
- Compare random and temporal splits, with confusion matrices.
- Target the advanced level through evaluated FFT features; int8 MLP is optional.
- Reuse the TH4 FastAPI/SQLite/HTML backend and Arduino networking code pragmatically.
- Keep the mandatory RMS/peak decision-tree baseline when adding FFT.
- Never present simulation labels or an untrained model as validated predictions.
- Deliver Wokwi/Git links, training notebook, parity table, CSV measurements,
  dashboard evidence, PDF reports, demo video (3–5 min), slides, and AI log.
- Follow weeks 7/11/14–15 milestones weighted 30/30/40; dates remain unconfirmed.
- Document AI-generated code in README; keep real member contributions in Git.
- Each member must explain and modify their own work during oral assessment.

## Permanent working rules
- Write clean, straightforward, pragmatic code.
- Organize files/modules logically and concisely by functionality.
- Do not invent custom frameworks or complex, bloated abstractions.
- Use comments to explain why complex logic, edge cases, or hardware settings exist.
- Allow brief function/section headers; avoid dense comments and obvious-line comments.
- Leave no internal, junk, or conversational comments in delivered code.
- Keep responses concise; show only relevant sections for small file changes.
- When the user adds a coding/architecture rule or corrects an unreasonable habit
  not covered here, proactively suggest adding it to AGENTS.md.
- Keep AGENTS.md concise and strictly under 60 lines.
- Keep pre-onboarding teammate drafts local-only; follow docs/workflow.md.

## Progressive disclosure
- Use docs/README.md to locate and read relevant specs before editing.
- MQTT/API/C inference: docs/interfaces.md; ML/FFT: docs/ml.md.
- Hardware/Wokwi: docs/hardware.md; reports/evidence: docs/reporting.md.
- Git/ownership/reviews: docs/workflow.md; course scope: docs/requirements.md.
- Update the owning spec with behavior changes; link details instead of duplicating them.
