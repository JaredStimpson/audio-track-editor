from audio_track_editor.schemas import Segment
from audio_track_editor.subtitles import build_srt, format_srt_timestamp


def test_format_srt_timestamp() -> None:
    assert format_srt_timestamp(3723.456) == "01:02:03,456"


def test_build_srt_only_includes_required_segments() -> None:
    srt = build_srt(
        [
            Segment("s1", 0.0, 1.0, "speaker-00", subtitle_required=False, text="skip"),
            Segment("s2", 1.0, 2.25, "speaker-01", subtitle_required=True, text="show"),
        ]
    )

    assert "skip" not in srt
    assert "show" in srt
    assert "00:00:01,000 --> 00:00:02,250" in srt
