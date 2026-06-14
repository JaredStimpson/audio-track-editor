from __future__ import annotations

import subprocess
from pathlib import Path

from audio_track_editor.config import Settings
from audio_track_editor.media import MediaToolError, build_extract_segment_command
from audio_track_editor.schemas import Project, Segment, save_project


def ensure_segment_preview(
    project: Project,
    segment: Segment,
    project_path: Path,
    settings: Settings,
) -> Path:
    if segment.audio_preview_path and Path(segment.audio_preview_path).exists():
        return Path(segment.audio_preview_path)

    if segment.source_audio_stream is None:
        raise MediaToolError("Segment has no source audio stream for preview.")

    preview_dir = settings.root_dir / ".ate-cache" / "previews" / project_path.stem
    preview_dir.mkdir(parents=True, exist_ok=True)
    preview_path = preview_dir / f"{segment.segment_id}.wav"
    command = build_extract_segment_command(
        Path(project.media_path),
        segment.source_audio_stream,
        segment.start,
        segment.duration,
        preview_path,
        settings.ffmpeg_bin,
    )
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        raise MediaToolError(completed.stderr.strip() or "FFmpeg preview extraction failed")

    segment.audio_preview_path = str(preview_path)
    save_project(project, project_path)
    return preview_path
