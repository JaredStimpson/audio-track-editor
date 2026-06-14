# Local Media

Do not commit real media files. Shows, anime episodes, and ripped discs are
usually copyrighted and can also be huge. This repo is set up so local testing
uses ignored paths.

## Recommended Setup

Copy `.env.example` to `.env`:

```powershell
Copy-Item .env.example .env
```

Set a local media path:

```dotenv
ATE_MEDIA_DIR=sample-media
ATE_OUTPUT_DIR=exports
ATE_MODEL_CACHE_DIR=models
```

Then create the folder and put personal test files there:

```powershell
New-Item -ItemType Directory -Force sample-media
```

The following paths are ignored by git:

- `.env`
- `.ate.local.toml`
- `sample-media/`
- `local-media/`
- `models/`
- `exports/`
- `analysis-cache/`
- `.ate-cache/`
- `*.ateproj.json`

## Optional TOML Config

Developers who prefer TOML can create `.ate.local.toml`:

```toml
[paths]
media_dir = "D:/Media/Test Episodes"
model_cache_dir = "D:/AudioTrackEditor/models"
output_dir = "D:/AudioTrackEditor/exports"

[runtime]
device = "cuda"
confidence_threshold = 0.68
ffmpeg_bin = "ffmpeg"
ffprobe_bin = "ffprobe"

[auth]
hf_token = ""
```

Values from `.env` override `.ate.local.toml`, and real environment variables
override both.

## Testing Without Media

Automated tests generate synthetic metadata and subtitle fixtures. They do not
require or commit real video/audio files.
