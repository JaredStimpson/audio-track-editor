from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from audio_track_editor.config import Settings
from audio_track_editor.diarization import DiarizationUnavailable, run_diarization
from audio_track_editor.media import first_audio_stream, probe_media
from audio_track_editor.schemas import Project, Segment, SpeakerProfile, save_project
from audio_track_editor.timeline import apply_fallback_policy


@dataclass(frozen=True)
class AnalyzeOptions:
    media_path: Path
    project_path: Path
    base_audio_stream: int | None = None


class Analyzer:
    """Coordinates media inspection and local model-backed speaker diarization."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def analyze(self, options: AnalyzeOptions) -> Project:
        streams = probe_media(options.media_path, self.settings.ffprobe_bin)
        base_stream = options.base_audio_stream
        if base_stream is None:
            base_stream = first_audio_stream(streams)

        speakers = [SpeakerProfile(speaker_id="speaker-00", label="Unlabeled Speaker")]
        analysis_model = ""
        analysis_device = ""

        if base_stream is None:
            segments = [
                Segment(
                    segment_id="segment-0001",
                    start=0.0,
                    end=3.0,
                    speaker_id="speaker-00",
                    confidence=0.0,
                    subtitle_required=True,
                    text="No audio stream was found.",
                    notes="Voice detection requires at least one audio stream.",
                )
            ]
        else:
            work_dir = self.settings.root_dir / ".ate-cache" / "analysis" / options.media_path.stem
            try:
                result = run_diarization(
                    media_path=options.media_path,
                    audio_stream_index=base_stream,
                    settings=self.settings,
                    work_dir=work_dir,
                )
                segments = result.segments
                speakers = result.speakers
                analysis_model = result.model
                analysis_device = result.device
            except (DiarizationUnavailable, RuntimeError) as exc:
                segments = [
                    Segment(
                        segment_id="segment-0001",
                        start=0.0,
                        end=3.0,
                        speaker_id="speaker-00",
                        source_audio_stream=base_stream,
                        target_audio_stream=base_stream,
                        confidence=0.0,
                        subtitle_required=True,
                        text="Voice detection could not run yet.",
                        notes=str(exc),
                    )
                ]

        if not segments:
            segments = [
                Segment(
                    segment_id="segment-0001",
                    start=0.0,
                    end=3.0,
                    speaker_id="speaker-00",
                    source_audio_stream=base_stream,
                    target_audio_stream=base_stream,
                    confidence=0.0,
                    subtitle_required=True,
                    text="No speech segments were detected.",
                    notes="Try a different audio stream or check model setup.",
                )
            ]

        for segment in segments:
            if segment.source_audio_stream is None:
                segment.source_audio_stream = base_stream
            if segment.target_audio_stream is None:
                segment.target_audio_stream = base_stream

        project = Project(
            media_path=str(options.media_path),
            base_audio_stream=base_stream,
            streams=streams,
            speakers=speakers,
            segments=apply_fallback_policy(segments, self.settings.confidence_threshold),
            analysis_model=analysis_model,
            analysis_device=analysis_device,
        )
        save_project(project, options.project_path)
        return project
