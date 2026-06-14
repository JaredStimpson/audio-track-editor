# Audio Track Editor

Audio Track Editor is a Windows-first desktop app for experimenting with
per-speaker language mixing in multi-audio video files. The target workflow is:
import an MKV/MP4, inspect the audio/subtitle streams, detect speaker segments,
label characters, choose which language each character should use, and export a
new MKV with copied video, mixed audio, and a generated soft subtitle track for
uncertain moments.

The project is early and dev-first. The current scaffold includes the GUI shell,
CLI, project schema, local config handling, FFmpeg command planning, subtitle
fallback generation, setup scripts, tests, and docs. The heavy ML adapters are
kept optional so the repo can test cleanly before large model downloads. The
intended app behavior is local/offline-first: once models are installed or
cached, analysis and export should run without internet.

## What It Is Trying To Solve

Dubbed shows often have multiple language tracks, but players usually choose one
whole track at a time. This app is designed to let a viewer keep one character in
one language and another character in another language, while preserving the
background bed and minimizing audible gaps.

The intended local pipeline uses:

- FFmpeg/ffprobe for container inspection, stream extraction, and MKV export.
- pyannote.audio for speaker diarization.
- WhisperX for speech timing and word alignment.
- Demucs for vocal/background separation.
- SpeechBrain or Asteroid adapters for experimental overlap/speaker separation.

## Current Limitations

- The first scaffold does not yet run full diarization or speech separation.
- `ate analyze` currently inspects streams and writes a placeholder review
  segment so the schema, UI, docs, and export path can be exercised.
- `ate export` currently remuxes copied video, the selected base audio stream,
  and generated fallback subtitles. Full mixed-audio rendering comes next.
- Model dependencies are optional because they are large. Some model providers
  may require a token only for the one-time download step, not for normal local
  processing once files are cached.

## Requirements

- Windows 10/11
- Python 3.11 or newer
- FFmpeg and ffprobe available on PATH, or configured in `.env`
- NVIDIA GPU recommended for the future ML pipeline
- CPU fallback supported for development and smaller experiments

## Setup

From a PowerShell prompt in the repository:

```powershell
scripts/setup.ps1
```

That creates `.venv`, installs the GUI/dev dependencies, copies `.env.example`
to `.env` if needed, and creates the ignored local folders for input media,
model cache, and exports.

If Python is not on PATH, install Python 3.11+ and rerun setup. If FFmpeg is not
on PATH, install FFmpeg or set these values in `.env`:

```dotenv
ATE_FFMPEG_BIN=C:\path\to\ffmpeg.exe
ATE_FFPROBE_BIN=C:\path\to\ffprobe.exe
```

## Local Media Configuration

Real show/anime/media files should never be committed. Use an ignored local
folder:

```dotenv
ATE_MEDIA_DIR=sample-media
ATE_OUTPUT_DIR=exports
ATE_MODEL_CACHE_DIR=models
ATE_OFFLINE_MODE=true
```

Then put personal test files under `sample-media/` or point `ATE_MEDIA_DIR` at
another folder outside the repo. See [docs/local-media.md](docs/local-media.md).

You usually do not put files in `models/` by hand. It is the local cache where
future model setup/download commands will store files. If the GPU machine is
offline, you can copy already-downloaded model folders into `models/` there.

## Launch

```powershell
scripts/doctor.ps1
scripts/launch.ps1
```

You can also use the CLI directly after setup:

```powershell
.venv\Scripts\ate.exe doctor
.venv\Scripts\ate.exe analyze sample-media\episode.mkv --project work\episode.ateproj.json
.venv\Scripts\ate.exe export work\episode.ateproj.json --output exports\episode-mixed.mkv --dry-run
```

Remove `--dry-run` to run the current remux export.

## Model Setup

Model-backed analysis is planned behind optional adapters. Install those only
when you are ready for the heavier local processing path:

```powershell
.venv\Scripts\python.exe -m pip install -e ".[ml]"
```

The app is designed to run locally. `HF_TOKEN` is optional and is only for
specific one-time model downloads if a provider requires accepted terms. See
[docs/model-setup.md](docs/model-setup.md).

## Development

Run tests:

```powershell
.venv\Scripts\python.exe -m pytest
```

Run lint:

```powershell
.venv\Scripts\python.exe -m ruff check .
```

Remove ignored local dev artifacts:

```powershell
scripts/clean-local.ps1
```

That removes `.venv`, test/lint caches, and `__pycache__` folders. It keeps
`.env`, media, models, and exports unless you pass explicit switches.

For GPU-PC update and cleanup commands, see
[docs/update-cleanup.md](docs/update-cleanup.md).

## Project Files

- `.ateproj.json`: per-media project state with streams, speakers, segments,
  confidence values, overlap flags, and export settings.
- `.env`: ignored local machine settings.
- `.ate.local.toml`: optional ignored local settings for developers who prefer
  TOML over env files.

## Commit And Push

After reviewing changes locally:

```powershell
git status
git add .
git commit -m "Initial audio track editor scaffold"
git push origin main
```
