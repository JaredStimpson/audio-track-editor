from __future__ import annotations

from audio_track_editor.schemas import Segment


def format_srt_timestamp(seconds: float) -> str:
    milliseconds = int(round(max(0.0, seconds) * 1000))
    hours, remainder = divmod(milliseconds, 3_600_000)
    minutes, remainder = divmod(remainder, 60_000)
    secs, millis = divmod(remainder, 1000)
    return f"{hours:02}:{minutes:02}:{secs:02},{millis:03}"


def build_srt(segments: list[Segment], default_text: str = "[subtitle fallback]") -> str:
    cues: list[str] = []
    cue_index = 1
    for segment in segments:
        if not segment.subtitle_required:
            continue
        text = segment.text.strip() or default_text
        timestamp = (
            f"{format_srt_timestamp(segment.start)} --> "
            f"{format_srt_timestamp(segment.end)}"
        )
        cues.append(
            "\n".join(
                [
                    str(cue_index),
                    timestamp,
                    text,
                ]
            )
        )
        cue_index += 1
    return "\n\n".join(cues) + ("\n" if cues else "")
