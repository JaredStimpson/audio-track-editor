from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from audio_track_editor.schemas import StreamInfo


class MediaToolError(RuntimeError):
    """Raised when FFmpeg or ffprobe cannot complete the requested operation."""


def executable_available(name: str) -> bool:
    return shutil.which(name) is not None or Path(name).exists()


def parse_ffprobe_streams(ffprobe_json: dict[str, Any]) -> list[StreamInfo]:
    streams: list[StreamInfo] = []
    for raw_stream in ffprobe_json.get("streams", []):
        tags = raw_stream.get("tags", {}) or {}
        disposition = raw_stream.get("disposition", {}) or {}
        streams.append(
            StreamInfo(
                index=int(raw_stream["index"]),
                type=raw_stream.get("codec_type", "unknown"),
                codec_name=raw_stream.get("codec_name"),
                language=tags.get("language"),
                title=tags.get("title"),
                channels=raw_stream.get("channels"),
                default=bool(disposition.get("default", 0)),
            )
        )
    return streams


def probe_media(path: Path, ffprobe_bin: str = "ffprobe") -> list[StreamInfo]:
    command = [
        ffprobe_bin,
        "-v",
        "error",
        "-print_format",
        "json",
        "-show_streams",
        str(path),
    ]
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        raise MediaToolError(completed.stderr.strip() or "ffprobe failed")
    return parse_ffprobe_streams(json.loads(completed.stdout))


def first_audio_stream(streams: list[StreamInfo]) -> int | None:
    default_audio = next((item for item in streams if item.type == "audio" and item.default), None)
    if default_audio:
        return default_audio.index
    audio = next((item for item in streams if item.type == "audio"), None)
    return audio.index if audio else None


def build_extract_audio_command(
    media_path: Path,
    stream_index: int,
    output_wav: Path,
    ffmpeg_bin: str = "ffmpeg",
) -> list[str]:
    return [
        ffmpeg_bin,
        "-y",
        "-i",
        str(media_path),
        "-map",
        f"0:{stream_index}",
        "-vn",
        "-ac",
        "1",
        "-ar",
        "16000",
        str(output_wav),
    ]


def build_extract_segment_command(
    media_path: Path,
    stream_index: int,
    start: float,
    duration: float,
    output_wav: Path,
    ffmpeg_bin: str = "ffmpeg",
) -> list[str]:
    return [
        ffmpeg_bin,
        "-y",
        "-ss",
        f"{start:.3f}",
        "-t",
        f"{duration:.3f}",
        "-i",
        str(media_path),
        "-map",
        f"0:{stream_index}",
        "-vn",
        "-ac",
        "2",
        "-ar",
        "48000",
        str(output_wav),
    ]


def build_extract_render_audio_command(
    media_path: Path,
    stream_index: int,
    output_wav: Path,
    ffmpeg_bin: str = "ffmpeg",
) -> list[str]:
    return [
        ffmpeg_bin,
        "-y",
        "-i",
        str(media_path),
        "-map",
        f"0:{stream_index}",
        "-vn",
        "-ac",
        "2",
        "-ar",
        "48000",
        "-sample_fmt",
        "s16",
        str(output_wav),
    ]


def build_remux_with_modified_audio_command(
    media_path: Path,
    modified_audio: Path,
    output_mkv: Path,
    ffmpeg_bin: str = "ffmpeg",
) -> list[str]:
    return [
        ffmpeg_bin,
        "-y",
        "-i",
        str(media_path),
        "-i",
        str(modified_audio),
        "-map",
        "0:v:0?",
        "-map",
        "1:a:0",
        "-map",
        "0:s?",
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-c:s",
        "copy",
        "-metadata:s:a:0",
        "title=Audio Track Editor Muted Mix",
        str(output_mkv),
    ]


def build_passthrough_export_command(
    media_path: Path,
    subtitle_file: Path,
    output_mkv: Path,
    base_audio_stream: int | None,
    ffmpeg_bin: str = "ffmpeg",
) -> list[str]:
    command = [
        ffmpeg_bin,
        "-y",
        "-i",
        str(media_path),
        "-i",
        str(subtitle_file),
        "-map",
        "0:v:0?",
    ]
    if base_audio_stream is not None:
        command.extend(["-map", f"0:{base_audio_stream}"])
    command.extend(
        [
            "-map",
            "1:0",
            "-c:v",
            "copy",
            "-c:a",
            "copy",
            "-c:s",
            "srt",
            "-metadata:s:a:0",
            "title=Audio Track Editor Mix",
            "-metadata:s:s:0",
            "title=Audio Track Editor Fallback Subtitles",
            str(output_mkv),
        ]
    )
    return command
