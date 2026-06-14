from __future__ import annotations

from dataclasses import replace

from audio_track_editor.schemas import Segment


def apply_fallback_policy(segments: list[Segment], confidence_threshold: float) -> list[Segment]:
    updated: list[Segment] = []
    for segment in segments:
        needs_subtitles = (
            segment.subtitle_required
            or segment.overlap
            or segment.confidence < confidence_threshold
        )
        updated.append(replace(segment, subtitle_required=needs_subtitles))
    return updated


def merge_adjacent_segments(segments: list[Segment], gap_tolerance: float = 0.15) -> list[Segment]:
    if not segments:
        return []

    ordered = sorted(segments, key=lambda item: (item.start, item.end))
    merged: list[Segment] = [ordered[0]]
    for segment in ordered[1:]:
        previous = merged[-1]
        same_route = (
            previous.speaker_id == segment.speaker_id
            and previous.target_audio_stream == segment.target_audio_stream
            and previous.subtitle_required == segment.subtitle_required
            and previous.overlap == segment.overlap
        )
        if same_route and segment.start - previous.end <= gap_tolerance:
            merged[-1] = replace(
                previous,
                end=max(previous.end, segment.end),
                confidence=min(previous.confidence, segment.confidence),
                text=" ".join(part for part in [previous.text, segment.text] if part).strip(),
            )
        else:
            merged.append(segment)
    return merged


def plan_crossfades(
    segments: list[Segment],
    fade_seconds: float = 0.035,
) -> list[dict[str, float | str]]:
    plans: list[dict[str, float | str]] = []
    for segment in segments:
        usable_fade = min(fade_seconds, segment.duration / 2)
        plans.append(
            {
                "segment_id": segment.segment_id,
                "fade_in_start": segment.start,
                "fade_in_end": segment.start + usable_fade,
                "fade_out_start": segment.end - usable_fade,
                "fade_out_end": segment.end,
            }
        )
    return plans
