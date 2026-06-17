import wave
from array import array
from pathlib import Path

from audio_track_editor.muting import (
    MuteRegion,
    apply_mute_envelope,
    collect_mute_regions,
    merge_mute_regions,
)
from audio_track_editor.schemas import Project, RenderSettings, Segment, SpeakerProfile


def _write_constant_wav(path: Path, frames: int = 100, value: int = 1000) -> None:
    samples = array("h", [value] * frames)
    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(100)
        wav.writeframes(samples.tobytes())


def _read_samples(path: Path) -> list[int]:
    with wave.open(str(path), "rb") as wav:
        samples = array("h")
        samples.frombytes(wav.readframes(wav.getnframes()))
    return list(samples)


def test_collect_mute_regions_uses_muted_speakers_and_padding() -> None:
    project = Project(
        media_path="episode.mkv",
        base_audio_stream=1,
        speakers=[
            SpeakerProfile("speaker-00", muted=True),
            SpeakerProfile("speaker-01", muted=False),
        ],
        segments=[
            Segment("s1", 1.0, 2.0, "speaker-00"),
            Segment("s2", 3.0, 4.0, "speaker-01"),
        ],
        render_settings=RenderSettings(pre_padding_ms=100, post_padding_ms=200),
    )

    regions = collect_mute_regions(project)

    assert regions == [MuteRegion(0.9, 2.2)]


def test_merge_mute_regions_combines_close_ranges() -> None:
    regions = merge_mute_regions(
        [MuteRegion(0.0, 1.0), MuteRegion(1.1, 2.0), MuteRegion(3.0, 4.0)],
        merge_gap_seconds=0.15,
    )

    assert regions == [MuteRegion(0.0, 2.0), MuteRegion(3.0, 4.0)]


def test_apply_mute_envelope_mutes_region(tmp_path: Path) -> None:
    input_wav = tmp_path / "input.wav"
    output_wav = tmp_path / "output.wav"
    _write_constant_wav(input_wav)

    apply_mute_envelope(
        input_wav,
        output_wav,
        [MuteRegion(0.2, 0.4)],
        RenderSettings(fade_ms=0, mute_gain=0.0),
    )

    samples = _read_samples(output_wav)

    assert samples[0] == 1000
    assert samples[25] == 0
    assert samples[45] == 1000
