from pathlib import Path

from audio_track_editor.config import Settings
from audio_track_editor.renderer import render_project
from audio_track_editor.schemas import Project, Segment, SpeakerProfile, save_project


def test_render_project_dry_run_writes_fallback_subtitles(tmp_path: Path) -> None:
    project_path = tmp_path / "episode.ateproj.json"
    output_path = tmp_path / "episode.mkv"
    project = Project(
        media_path=str(tmp_path / "source.mkv"),
        base_audio_stream=1,
        speakers=[SpeakerProfile("speaker-00", muted=True)],
        segments=[
            Segment(
                segment_id="s1",
                start=1.0,
                end=2.5,
                speaker_id="speaker-00",
                confidence=0.2,
                subtitle_required=True,
                text="hello",
            )
        ],
    )
    save_project(project, project_path)
    settings = Settings(
        root_dir=tmp_path,
        media_dir=tmp_path / "sample-media",
        model_cache_dir=tmp_path / "models",
        output_dir=tmp_path / "exports",
        hf_token=None,
        offline_mode=True,
        diarization_model="pyannote/speaker-diarization-community-1",
        diarization_model_path=None,
        device="cpu",
        confidence_threshold=0.68,
        ffmpeg_bin="ffmpeg",
        ffprobe_bin="ffprobe",
    )

    result = render_project(project_path, output_path, settings, dry_run=True)

    assert result.output_file == output_path
    assert result.muted_audio_file == output_path.with_suffix(".muted.wav")
    assert len(result.muted_regions) == 1
    assert result.subtitle_file.read_text(encoding="utf-8").strip().endswith("hello")
    assert result.command[-1] == str(output_path)
