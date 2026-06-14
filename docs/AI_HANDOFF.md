# AI Handoff

Use this file to brief another AI or future debugging session. Also include the
latest relevant files from the ignored `logs/` folder, especially `setup-*.log`,
`install-ml-*.log`, `doctor-*.log`, or `first-test-*.log`.

## Repository State

- Repo: `JaredStimpson/audio-track-editor`
- Current implementation branch for this phase: `test`
- App type: Windows-first Python/PySide6 desktop app
- Goal: local/offline-first per-speaker language track editor for multi-audio
  MKV/MP4 files
- Current version: functional scaffold with GUI analyze/export, FFmpeg
  metadata/remux path, pyannote diarization adapter, generated fallback
  subtitles, setup scripts, and tests

## Product Intent

The app should let a user load a multi-language video, identify speakers, label
characters, choose which language track each character should use, and export a
new MKV with copied video, mixed audio, and soft subtitles for uncertain
segments.

The design is local-first. Internet should not be needed for normal processing
after dependencies/models are installed or cached.

## Important Decisions

- Default setup now installs the core local ML stack.
- Selected diarization model: `pyannote/speaker-diarization-community-1`.
- Diarization passes an FFmpeg-extracted mono 16 kHz waveform into pyannote
  instead of passing a file path, to avoid Windows `AudioDecoder`/torchcodec
  loader failures.
- Asteroid is not in the default ML path because it pulls `pesq`, which failed
  on Windows without Microsoft C++ Build Tools.
- `HF_TOKEN` is optional and only for one-time downloads of gated model files.
- `models/` is a local cache, not a folder users normally populate by hand.
- Real media, exports, models, logs, caches, `.env`, and `.ateproj.json` files
  are ignored by git.

## Key Commands

GPU PC setup:

```powershell
git switch test
git pull origin test
scripts/setup.ps1 -Device cuda
scripts/run-first-test.ps1
scripts/launch.ps1
```

Dev/CPU setup:

```powershell
scripts/setup.ps1 -Device cpu
```

Repair only ML:

```powershell
scripts/install-ml.ps1 -Device cuda
scripts/doctor.ps1
```

Remove failed Asteroid partial installs:

```powershell
.venv\Scripts\python.exe -m pip uninstall -y asteroid pb-bss-eval pesq torch-stoi torch-optimizer pytorch-ranger
```

## Current Functional Surface

- `ate doctor`: checks Python, FFmpeg, PySide6, ML packages, offline mode,
  configured local folders, and Torch/CUDA.
- `ate analyze <media> --project <file>`: probes streams and writes a project
  with pyannote speaker segments when the model is available, otherwise a clear
  fallback segment explaining what blocked detection.
- `ate export <project> --output <file.mkv>`: writes fallback SRT and remuxes
  video/base audio/subtitles.
- GUI: browse media, analyze, inspect streams/timeline, play detected sections,
  name speakers, assign preferred tracks, export MKV.
- `scripts/run-first-test.ps1`: generates synthetic multi-audio MKV and runs
  analyze/export.
- `scripts/cache-model.ps1 -AllowDownload`: one-time diarization model cache
  step after accepting model terms and setting `HF_TOKEN`.

## Known Gaps

- Speech separation is not wired yet.
- Export does not yet synthesize a true mixed dialogue stem; it remuxes the
  selected base audio plus generated subtitles.
- GUI is functional but still a scaffold, not a full timeline editor.

## Logs

Ignored logs are created in `logs/`:

- `setup-*.log`
- `install-ml-*.log`
- `doctor-*.log`
- `first-test-*.log`
- `launch-*.log`

When handing off, include the latest logs and `scripts/doctor.ps1` output.
