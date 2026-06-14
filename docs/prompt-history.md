# Prompt History

This records the important turns and implementation decisions so future sessions
do not need to infer them from scattered chat context.

## 2026-06-14: Initial Product Request

User wanted a GitHub-compatible program for multi-language dubbed shows. The
core idea: detect voices in MKV/MP4 audio tracks, label speakers, choose which
language each speaker should use, and use subtitles on uncertain sections.

Decisions made:

- Windows desktop first.
- Python/PySide6 app.
- Local/offline-first processing.
- NVIDIA GPU preferred, CPU fallback supported.
- MKV remux/export first.
- Reusable speaker/character profiles planned.

## 2026-06-14: Initial Scaffold

Implemented initial repo scaffold:

- `src/`, `tests/`, `docs/`, scripts, CI, README, MIT license.
- CLI commands: `ate doctor`, `ate analyze`, `ate export`.
- GUI shell.
- Project schemas, FFmpeg helpers, subtitle fallback generation.
- Ignored `.env`, local media, models, exports, and cache folders.

Verification: tests and lint passed.

## 2026-06-14: Offline-First Clarification

User clarified that ML/AI should run locally and potentially without internet.
They also asked why a token was needed and wanted setup to create local folders.

Changes:

- Added `ATE_OFFLINE_MODE=true`.
- Reframed `HF_TOKEN` as optional, one-time gated model download only.
- Setup creates input, output, and model cache folders.
- Added cleanup script and update/cleanup docs.

## 2026-06-14: GPU PC Doctor Output

User shared doctor output from the GPU PC showing base app dependencies OK but
ML adapters and Torch/CUDA missing.

Changes:

- Added `scripts/install-ml.ps1`.
- Added `scripts/run-first-test.ps1`.
- Doctor prints actionable `Next:` lines.
- GUI Analyze/Export buttons were wired to real CLI-equivalent behavior.
- Added first-test docs.

## 2026-06-14: ML Install Error

User shared an ML install error log. Root cause: `asteroid` pulled `pesq`, which
requires Microsoft C++ Build Tools on Windows.

Changes:

- Removed Asteroid from default `.[ml]`.
- Added separate `.[overlap]` and `.[asteroid]` extras.
- `scripts/install-ml.ps1 -ExperimentalSeparation` installs SpeechBrain only.
- `scripts/install-ml.ps1 -Asteroid` is explicit and warns about native builds.
- Added docs for fixing the `pesq` error.

## 2026-06-14: Test Branch And All-In-One Setup

User requested a new branch called `test`, all-in-one setup, a more functional
first version, handoff docs, error logs, and ongoing prompt history.

Changes:

- Created local branch `test`.
- `scripts/setup.ps1` now installs core ML by default and runs doctor.
- Added logging transcripts under ignored `logs/`.
- Added `docs/AI_HANDOFF.md`.
- Added this prompt history file.
