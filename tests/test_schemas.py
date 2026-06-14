from pathlib import Path

from audio_track_editor.schemas import (
    Project,
    Segment,
    SpeakerProfile,
    StreamInfo,
    load_project,
    save_project,
)


def test_project_round_trip(tmp_path: Path) -> None:
    project = Project(
        media_path="sample-media/episode.mkv",
        base_audio_stream=1,
        streams=[StreamInfo(index=1, type="audio", language="jpn")],
        speakers=[SpeakerProfile(speaker_id="speaker-00", label="Hero")],
        segments=[
            Segment(
                segment_id="segment-1",
                start=0.0,
                end=1.5,
                speaker_id="speaker-00",
                confidence=0.9,
            )
        ],
    )
    path = tmp_path / "project.ateproj.json"

    save_project(project, path)
    loaded = load_project(path)

    assert loaded.media_path == project.media_path
    assert loaded.streams[0].language == "jpn"
    assert loaded.speakers[0].label == "Hero"
    assert loaded.segments[0].duration == 1.5
