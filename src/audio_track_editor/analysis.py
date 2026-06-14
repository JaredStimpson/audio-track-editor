from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from audio_track_editor.config import Settings
from audio_track_editor.media import first_audio_stream, probe_media
from audio_track_editor.schemas import Project, Segment, SpeakerProfile, save_project
from audio_track_editor.timeline import apply_fallback_policy


@dataclass(frozen=True)
class AnalyzeOptions:
    media_path: Path
    project_path: Path
    base_audio_stream: int | None = None


class Analyzer:
    """Coordinates media inspection now and model-backed analysis as adapters land."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def analyze(self, options: AnalyzeOptions) -> Project:
        streams = probe_media(options.media_path, self.settings.ffprobe_bin)
        base_stream = options.base_audio_stream
        if base_stream is None:
            base_stream = first_audio_stream(streams)

        segments = [
            Segment(
                segment_id="segment-0001",
                start=0.0,
                end=3.0,
                speaker_id="speaker-00",
                source_audio_stream=base_stream,
                target_audio_stream=base_stream,
                confidence=0.0,
                overlap=False,
                text="Review this placeholder segment after model analysis is enabled.",
                notes="Initial scaffold segment created from stream metadata only.",
            )
        ]

        project = Project(
            media_path=str(options.media_path),
            base_audio_stream=base_stream,
            streams=streams,
            speakers=[SpeakerProfile(speaker_id="speaker-00", label="Unlabeled Speaker")],
            segments=apply_fallback_policy(segments, self.settings.confidence_threshold),
        )
        save_project(project, options.project_path)
        return project
