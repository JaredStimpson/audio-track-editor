from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from audio_track_editor import __version__


@dataclass
class StreamInfo:
    index: int
    type: str
    codec_name: str | None = None
    language: str | None = None
    title: str | None = None
    channels: int | None = None
    default: bool = False


@dataclass
class SpeakerProfile:
    speaker_id: str
    label: str = ""
    muted: bool = False
    preferred_audio_stream: int | None = None
    preferred_subtitle_stream: int | None = None
    subtitles: str = "auto"


@dataclass
class Segment:
    segment_id: str
    start: float
    end: float
    speaker_id: str
    source_audio_stream: int | None = None
    target_audio_stream: int | None = None
    confidence: float = 0.0
    overlap: bool = False
    subtitle_required: bool = False
    text: str = ""
    notes: str = ""
    audio_preview_path: str = ""
    manually_corrected: bool = False

    @property
    def duration(self) -> float:
        return max(0.0, self.end - self.start)


@dataclass
class RenderSettings:
    fade_ms: int = 50
    pre_padding_ms: int = 80
    post_padding_ms: int = 120
    merge_gap_ms: int = 150
    mute_gain: float = 0.0


@dataclass
class Project:
    media_path: str
    base_audio_stream: int | None
    streams: list[StreamInfo] = field(default_factory=list)
    speakers: list[SpeakerProfile] = field(default_factory=list)
    segments: list[Segment] = field(default_factory=list)
    render_settings: RenderSettings = field(default_factory=RenderSettings)
    analysis_model: str = ""
    analysis_device: str = ""
    profile_id: str | None = None
    schema_version: str = "0.1"
    created_by_version: str = __version__

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Project:
        return cls(
            media_path=data["media_path"],
            base_audio_stream=data.get("base_audio_stream"),
            streams=[StreamInfo(**item) for item in data.get("streams", [])],
            speakers=[SpeakerProfile(**item) for item in data.get("speakers", [])],
            segments=[Segment(**item) for item in data.get("segments", [])],
            render_settings=RenderSettings(**data.get("render_settings", {})),
            analysis_model=data.get("analysis_model", ""),
            analysis_device=data.get("analysis_device", ""),
            profile_id=data.get("profile_id"),
            schema_version=data.get("schema_version", "0.1"),
            created_by_version=data.get("created_by_version", __version__),
        )


def save_project(project: Project, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(project.to_dict(), indent=2, sort_keys=True), encoding="utf-8")


def load_project(path: Path) -> Project:
    return Project.from_dict(json.loads(path.read_text(encoding="utf-8")))
