# Git workflow and ownership

Repository: [DanhLent/edge-vibration-monitor](https://github.com/DanhLent/edge-vibration-monitor).
Maintainer: Danh (`@DanhLent`). Nhat GitHub: **TODO — verified handle**. Dat GitHub: **TODO — verified handle**.

| Lead | Owned functionality | Reviewer |
| --- | --- | --- |
| Danh | Backend, MQTT, dashboard, governance; backend/MQTT tests | Dat |
| Nhat | ML/FFT, generated model.h/model.c, parity and ML tests | Danh; Dat for C integration |
| Dat | Acquisition, simulation, wiring, Wokwi; firmware tests | Nhat |
| All affected leads | MQTT/API/C contract changes | Every affected lead |

Ownership assigns a lead, not an exclusive editing permission. Changes across a boundary require
that lead's review. The firmware directory belongs to Dat except generated model artifacts owned
by Nhat. Put model CODEOWNERS rules after the general firmware rule because the last match wins.

## Bootstrap and onboarding

1. Danh creates the public repository and commits the reviewed AI-assisted scaffold using his own verified Git identity.
2. CI runs `Baseline checks` and `Conventional commits`. Protect main after these contexts exist: require PRs, checks, resolved conversations, and prohibit force pushes/deletion. Allow merge commits; disable squash and rebase merging.
3. During solo bootstrap, require zero approvals and leave code-owner review disabled. Bootstrap ownership is Danh; commented TODOs stand in for missing member handles.
4. TODO(Danh): obtain Nhat/Dat's verified handles, invite each with write access, and have them accept invitations.
5. Replace commented placeholders with active lead/reviewer pairs, including tests and shared docs. Include a second eligible owner wherever the lead may author the PR.
6. Enable one non-author approving review, dismiss stale approvals after new commits, and require code-owner review. Authors cannot approve their own PR.

CODEOWNERS can require an eligible owner's approval, but does not enforce every affected lead's
approval. For shared contracts, collect all affected leads' agreement in the PR before merging.

## Branches and commits

Starter branches: `danh/backend-mqtt`, `nhat/ml-baseline`, `dat/firmware-wokwi`. Each initially points
to the reviewed main baseline; there are no member-authored changes implied by creating these refs.
Use your own computer/clone or a separate checkout when working concurrently.

```bash
git clone https://github.com/DanhLent/edge-vibration-monitor.git
cd edge-vibration-monitor
git switch --track origin/dat/firmware-wokwi
```

Use the corresponding starter branch for the first task, then make a new short-lived branch from
updated main for each later task, such as `dat/button-debounce`. Synchronize with `git fetch origin`
and `git merge origin/main`; preserve published history. Open a PR, pass required checks, obtain
applicable reviews, and merge with a merge commit. Delete finished topic branches after merging.
Main is the integration branch; long-running integration/develop branches are unnecessary here.

Before Nhat and Dat onboard with verified accounts, reference drafts for their tracks remain on
local-only branches. Never push those drafts or advance their remote starter branches. Use the
actual author's identity and label reference drafts clearly; members later explain, modify and
commit their real contributions themselves. Danh's first tooling PR must contain no firmware or
ML changes. Record runtime firmware findings for Dat rather than fixing them in that PR.

Conventional Commits: `type(scope): summary`. Types: feat, fix, docs, test, refactor, perf, build,
ci, chore, revert. Recommended scopes: repo, backend, mqtt, dashboard, firmware, wokwi, ml, fft,
docs, tests. Use `!` plus a BREAKING CHANGE body when needed. CI checks authored non-merge
commit subjects and PR titles. Examples: `fix(mqtt): preserve mode across old windows`,
`feat(ml): export depth-three baseline tree`, `test(firmware): cover mode-change boundaries`.

Configure your own repository-local Git name and a verified GitHub email or account noreply address.
Never impersonate another member, backdate contributions, or add co-author credit without real work.
The bootstrap records Danh's TH4 provenance and AI assistance; later contributions belong to their
actual human authors. Each member must explain and modify their submitted work during oral assessment.

## Shared documents and artifacts

Update your own section in STATE.md after verified progress. Danh updates the header and consolidates
milestone checkboxes during integration. Use member AI logs under `docs/ai/` rather than concurrently
appending detailed entries to one shared log. Put subsystem details in their owning spec; keep README
changes focused on entry points and verified claims.

Track source, cleared-output notebooks, safe dataset manifests, small CSV measurements, and final
PDF/slide evidence under `deliverables/`. Keep scratch output under ignored `artifacts/`. Publish
large demo videos as release assets. Do not commit the full course workbook, raw/derived official
TH5 records, credentials, databases, environments, or toolchain/build caches. Review staged contents
and notebook outputs before pushing. Dataset metadata must not embed private records.

## Reproduce checks

Use Python 3.12, Node 22, Arduino CLI 1.6.0, ESP32 core 4.0.0, PubSubClient 2.8.0, and ArduinoJson 7.4.3.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.lock
bash scripts/setup_arduino.sh arduino-cli
.venv/bin/python -m unittest discover -s tests -p 'test_*.py' -v
node scripts/check_dashboard.js
.venv/bin/python scripts/check_firmware.py --cli arduino-cli
.venv/bin/python scripts/check_commits.py --base origin/main
```

The setup script writes only project-local `.tools/`. Host protocol tests use its ArduinoJson headers;
set `ARDUINOJSON_INCLUDE` if you install the library elsewhere. Original-workbook verification is
optional on public clones; scoped-document/routing/AGENTS line-limit checks always run.

## Later task packages

- Dat: measure/tune acquisition with before/after CSV and Nyquist review; verify button, clock,
  reconnect and mode transitions; then coordinate event/heartbeat publishing and raw-signal timing
  capture. Preserve the 200–1000 Hz requirement and prove reduction using the reporting convention.
- Nhat: build an explicitly temporary synthetic loader/generator and cleared-output training notebook;
  evaluate grouped chronological and seeded random splits with macro F1, confusion matrices and
  always-normal results. Export faithful C into scratch output and verify host parity on held-out
  and float32 threshold-boundary vectors while the deployed model remains unavailable.
- After TH5 arrives, Nhat inspects official units/preprocessing/order and chooses the real split;
  Dat calibrates simulation inputs. Activation requires actual ESP32/Python parity. FFT evaluation
  additionally requires raw signals and trustworthy timing; an RMS/peak table alone is insufficient.

These are later-session packages, not completed contributions or permission to push teammate drafts.
