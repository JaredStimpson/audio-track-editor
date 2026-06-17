from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from audio_track_editor.config import Settings
from audio_track_editor.media import MediaToolError, build_remux_with_modified_audio_command
from audio_track_editor.muting import MuteRegion, collect_mute_regions, render_muted_audio
from audio_track_editor.schemas import Project, load_project
from audio_track_editor.subtitles import build_srt


@dataclass(frozen=True)
class ExportResult:
    command: list[str]
    subtitle_file: Path
    muted_audio_file: Path
    output_file: Path
    muted_regions: list[MuteRegion]


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
    muted_audio_file = (
        output_file
        if output_file.suffix.lower() == ".wav"
        else output_file.with_suffix(".muted.wav")
    )
    work_dir = settings.root_dir / ".ate-cache" / "render" / project_path.stem
    muted_regions = collect_mute_regions(project)

    if dry_run:
        command = []
        if output_file.suffix.lower() != ".wav":
            command = build_remux_with_modified_audio_command(
                media_path=Path(project.media_path),
                modified_audio=muted_audio_file,
                output_mkv=output_file,
                ffmpeg_bin=settings.ffmpeg_bin,
            )
        return ExportResult(
            command=command,
            subtitle_file=subtitle_file,
            muted_audio_file=muted_audio_file,
            output_file=output_file,
            muted_regions=muted_regions,
        )

    muted = render_muted_audio(project, muted_audio_file, settings, work_dir)
    if output_file.suffix.lower() == ".wav":
        return ExportResult(
            command=[],
            subtitle_file=subtitle_file,
            muted_audio_file=muted.output_wav,
            output_file=output_file,
            muted_regions=muted.muted_regions,
        )

    command = build_remux_with_modified_audio_command(
        media_path=Path(project.media_path),
        modified_audio=muted.output_wav,
        output_mkv=output_file,
        ffmpeg_bin=settings.ffmpeg_bin,
    )
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        raise MediaToolError(completed.stderr.strip() or "ffmpeg export failed")
    return ExportResult(
        command=command,
        subtitle_file=subtitle_file,
        muted_audio_file=muted.output_wav,
        output_file=output_file,
        muted_regions=muted.muted_regions,
    )
