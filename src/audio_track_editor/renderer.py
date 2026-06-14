from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from audio_track_editor.config import Settings
from audio_track_editor.media import MediaToolError, build_passthrough_export_command
from audio_track_editor.schemas import Project, load_project
from audio_track_editor.subtitles import build_srt


@dataclass(frozen=True)
class ExportResult:
    command: list[str]
    subtitle_file: Path
    output_file: Path


def render_project(
    project_path: Path,
    output_file: Path,
    settings: Settings,
    dry_run: bool = False,
) -> ExportResult:
    project: Project = load_project(project_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    subtitle_file = output_file.with_suffix(".fallback.srt")
    subtitle_file.write_text(build_srt(project.segments), encoding="utf-8")

    command = build_passthrough_export_command(
        media_path=Path(project.media_path),
        subtitle_file=subtitle_file,
        output_mkv=output_file,
        base_audio_stream=project.base_audio_stream,
        ffmpeg_bin=settings.ffmpeg_bin,
    )
    result = ExportResult(command=command, subtitle_file=subtitle_file, output_file=output_file)
    if dry_run:
        return result

    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        raise MediaToolError(completed.stderr.strip() or "ffmpeg export failed")
    return result
