from audio_track_editor.schemas import Segment
from audio_track_editor.timeline import (
    apply_fallback_policy,
    merge_adjacent_segments,
    plan_crossfades,
)


def test_apply_fallback_policy_marks_low_confidence_and_overlap() -> None:
    segments = [
        Segment("s1", 0.0, 1.0, "a", confidence=0.9),
        Segment("s2", 1.0, 2.0, "a", confidence=0.3),
        Segment("s3", 2.0, 3.0, "b", confidence=0.9, overlap=True),
    ]

    updated = apply_fallback_policy(segments, confidence_threshold=0.68)

    assert updated[0].subtitle_required is False
    assert updated[1].subtitle_required is True
    assert updated[2].subtitle_required is True


def test_merge_adjacent_segments_combines_same_route() -> None:
    merged = merge_adjacent_segments(
        [
            Segment("s1", 0.0, 1.0, "a", target_audio_stream=1, confidence=0.8, text="hello"),
            Segment("s2", 1.05, 2.0, "a", target_audio_stream=1, confidence=0.7, text="there"),
        ],
        gap_tolerance=0.1,
    )

    assert len(merged) == 1
    assert merged[0].end == 2.0
    assert merged[0].confidence == 0.7
    assert merged[0].text == "hello there"


def test_plan_crossfades_clamps_short_segments() -> None:
    plans = plan_crossfades([Segment("s1", 0.0, 0.04, "a")], fade_seconds=0.05)

    assert plans[0]["fade_in_end"] == 0.02
    assert plans[0]["fade_out_start"] == 0.02
