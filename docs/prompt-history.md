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

## 2026-06-14: Voice Detection Focus

User asked to focus on optimized voice detection, CPU compatibility, GUI display
of detected voice sections, playback, speaker naming, and model selection.

Changes:

- Selected `pyannote/speaker-diarization-community-1` as the default local
  diarization model.
- Added model config: `ATE_DIARIZATION_MODEL` and `ATE_DIARIZATION_MODEL_PATH`.
- Added real pyannote diarization adapter with CUDA/CPU auto-selection.
- `ate analyze` now extracts the selected audio stream and writes detected
  speaker segments when the model is available.
- GUI now shows detected voice sections, speaker names, target tracks, overlap
  flags, and supports lazy preview playback.
- Added `ate cache-model` and `scripts/cache-model.ps1` for the first model
  cache/download step.

## 2026-06-14: CPU Setup Script Fix

User shared a CPU setup log where `scripts/setup.ps1 -Device cpu` failed while
calling `install-ml.ps1`. Root cause: setup used an array splat, so PowerShell
passed `-Device` as the positional `Device` value. Fixed setup to use a
hashtable splat for named parameters.

## 2026-06-14: AudioDecoder Analyze Failure

User shared an Analyze failure screenshot: `name 'AudioDecoder' is not defined`.
Likely cause: pyannote tried to decode a file path through its torchcodec
`AudioDecoder` path, but that loader was unavailable in the runtime. Fixed
diarization to extract mono 16 kHz WAV with FFmpeg, load it in Python, and pass
`{"waveform": ..., "sample_rate": ...}` into pyannote instead of a file path.
The GUI now shows fallback notes in the detected voice sections table.

## 2026-06-14: Startup TorchCodec Warning

User shared the full launch warning from pyannote: torchcodec could not load
`libtorchcodec`, and pyannote warned that built-in decoding would fail. This
confirmed the waveform-mode fix is the right approach. Also patched doctor to
check installed package metadata instead of importing `pyannote.audio` during
GUI startup, so launch should not print that warning just from status checks.

## 2026-06-16: Handoff-Driven MVP Pivot

User provided a Word handoff document describing a better first build: process
each language/audio track independently, detect recurring speakers, let the user
preview/name speakers, globally mute selected speakers, and export a modified
audio/video file. The handoff explicitly says not to cross-reference voices
between languages and to start with timeline-based muting rather than true
voice-only suppression.

Changes:

- Added `muted` speaker state and render settings to project JSON.
- Added timeline-based mute region collection with pre/post padding, merge gap,
  fade down/up, and WAV rendering.
- Export now creates muted audio and can remux original video with that modified
  audio.
- GUI now includes audio track selection, speaker mute toggles, status/progress
  indication, and export reporting for muted regions.
- Added CLI helpers: `ate speakers` and `ate set-speaker`.
