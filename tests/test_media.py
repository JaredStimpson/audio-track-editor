from pathlib import Path

from audio_track_editor.media import (
    build_extract_audio_command,
    build_extract_segment_command,
    build_passthrough_export_command,
    first_audio_stream,
    parse_ffprobe_streams,
)


def test_parse_ffprobe_streams_extracts_metadata() -> None:
    streams = parse_ffprobe_streams(
        {
            "streams": [
                {"index": 0, "codec_type": "video", "codec_name": "h264"},
                {
                    "index": 1,
                    "codec_type": "audio",
                    "codec_name": "aac",
                    "channels": 2,
                    "tags": {"language": "eng", "title": "English"},
                    "disposition": {"default": 1},
                },
            ]
        }
    )

    assert streams[1].language == "eng"
    assert streams[1].title == "English"
    assert streams[1].default is True
    assert first_audio_stream(streams) == 1


def test_build_extract_audio_command_maps_stream() -> None:
    command = build_extract_audio_command(Path("episode.mkv"), 2, Path("track.wav"))

    assert command[0] == "ffmpeg"
    assert command[command.index("-map") + 1] == "0:2"
    assert command[-1] == "track.wav"


def test_build_passthrough_export_command_maps_video_audio_and_subtitles() -> None:
    command = build_passthrough_export_command(
        Path("episode.mkv"),
        Path("fallback.srt"),
        Path("out.mkv"),
        base_audio_stream=1,
    )

    assert command.count("-map") == 3
    assert "0:v:0?" in command
    assert "0:1" in command
    assert "1:0" in command
    assert command[-1] == "out.mkv"


def test_build_extract_segment_command_clips_selected_stream() -> None:
    command = build_extract_segment_command(
        Path("episode.mkv"),
        3,
        12.345,
        2.5,
        Path("preview.wav"),
    )

    assert command[command.index("-ss") + 1] == "12.345"
    assert command[command.index("-t") + 1] == "2.500"
    assert command[command.index("-map") + 1] == "0:3"
