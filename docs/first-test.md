# First Working Test

Use this before testing with real media. It creates a tiny synthetic MKV with a
video stream and two audio streams, then runs the scaffolded analyze/export path.
No copyrighted media is needed.

## Run

```powershell
scripts/setup.ps1
scripts/run-first-test.ps1
```

The script writes ignored local files:

- `sample-media/first-test.mkv`
- `exports/first-test.ateproj.json`
- `exports/first-test.fallback.srt`
- `exports/first-test-export.mkv`

## Expected Result

The command should finish with paths for media, project, and output. You should
be able to open `exports/first-test-export.mkv` in a media player.

This first test proves:

- FFmpeg is usable.
- The app can inspect a multi-audio container.
- A project file can be created.
- Subtitle fallback cues can be generated.
- MKV export can copy video/audio and attach the generated subtitle track.

It does not prove ML diarization yet. That comes after installing the local ML
stack on the GPU PC.

## GUI Test

After `scripts/setup.ps1`:

```powershell
scripts/launch.ps1
```

In the app:

1. Choose `sample-media/first-test.mkv`.
2. Click `Analyze`.
3. Confirm the streams table and timeline fill in.
4. Click `Export MKV`.
5. Open `exports/first-test-export.mkv`.
