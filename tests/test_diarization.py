import sys
from types import SimpleNamespace

import pytest

from audio_track_editor.diarization import (
    DiarizationUnavailable,
    _extract_turns,
    _mark_overlaps,
    resolve_torch_device,
)
from audio_track_editor.schemas import Segment


def test_resolve_torch_device_cpu_without_torch(monkeypatch) -> None:
    monkeypatch.setitem(sys.modules, "torch", None)

    assert resolve_torch_device("cpu") == "cpu"


def test_resolve_torch_device_cuda_requires_torch(monkeypatch) -> None:
    monkeypatch.setitem(sys.modules, "torch", None)

    with pytest.raises(DiarizationUnavailable):
        resolve_torch_device("cuda")


def test_extract_turns_from_itertracks_shape() -> None:
    class FakeDiarization:
        def itertracks(self, yield_label: bool):
            assert yield_label is True
            yield SimpleNamespace(start=0.1, end=1.2), "track", "SPEAKER_00"

    turns = _extract_turns(SimpleNamespace(speaker_diarization=FakeDiarization()))

    assert turns == [(0.1, 1.2, "SPEAKER_00")]


def test_mark_overlaps_marks_different_speakers() -> None:
    segments = [
        Segment("s1", 0.0, 2.0, "speaker-00"),
        Segment("s2", 1.5, 3.0, "speaker-01"),
        Segment("s3", 3.0, 4.0, "speaker-00"),
    ]

    marked = _mark_overlaps(segments)

    assert marked[0].overlap is True
    assert marked[1].overlap is True
    assert marked[2].overlap is False
