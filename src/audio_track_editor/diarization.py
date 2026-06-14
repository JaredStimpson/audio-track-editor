from __future__ import annotations

import os
import subprocess
import sys
import wave
from array import array
from dataclasses import dataclass
from pathlib import Path

from audio_track_editor.config import Settings
from audio_track_editor.media import MediaToolError, build_extract_audio_command
from audio_track_editor.schemas import Segment, SpeakerProfile


class DiarizationUnavailable(RuntimeError):
    """Raised when model-backed diarization cannot run in this environment."""


@dataclass(frozen=True)
class DiarizationResult:
    segments: list[Segment]
    speakers: list[SpeakerProfile]
    model: str
    device: str
    audio_path: Path


def resolve_torch_device(requested: str) -> str:
    if requested == "cpu":
        return "cpu"

    try:
        import torch
    except ImportError as exc:
        if requested == "cuda":
            raise DiarizationUnavailable(
                "Torch is not installed, so CUDA diarization cannot run."
            ) from exc
        return "cpu"

    if requested == "cuda":
        if not torch.cuda.is_available():
            raise DiarizationUnavailable("ATE_DEVICE=cuda was requested but torch cannot see CUDA.")
        return "cuda"

    return "cuda" if torch.cuda.is_available() else "cpu"


def _prepare_model_environment(settings: Settings) -> None:
    settings.model_cache_dir.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("HF_HOME", str(settings.model_cache_dir))
    os.environ.setdefault("HUGGINGFACE_HUB_CACHE", str(settings.model_cache_dir / "hub"))
    os.environ.setdefault("PYANNOTE_METRICS_ENABLED", "0")

    if settings.offline_mode:
        os.environ.setdefault("HF_HUB_OFFLINE", "1")
        os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")


def _load_pipeline(settings: Settings, device: str):
    try:
        import torch
        from pyannote.audio import Pipeline
    except ImportError as exc:
        raise DiarizationUnavailable(
            "pyannote.audio and torch are required for voice detection. "
            "Run scripts/setup.ps1 -Device cuda on the GPU PC."
        ) from exc

    _prepare_model_environment(settings)

    model_origin = str(settings.diarization_model_path or settings.diarization_model)
    token = settings.hf_token if not settings.diarization_model_path else None
    try:
        pipeline = Pipeline.from_pretrained(model_origin, token=token)
    except Exception as exc:
        raise DiarizationUnavailable(
            "Could not load the diarization model. For the recommended model, accept "
            "the pyannote/speaker-diarization-community-1 conditions, set HF_TOKEN "
            "only for the first download, or set ATE_DIARIZATION_MODEL_PATH to a "
            f"local cached pipeline. Original error: {exc}"
        ) from exc

    pipeline.to(torch.device(device))
    return pipeline, model_origin


def _load_wav_for_pipeline(path: Path):
    try:
        import torch
    except ImportError as exc:
        raise DiarizationUnavailable("Torch is required to load audio for diarization.") from exc

    with wave.open(str(path), "rb") as wav:
        channels = wav.getnchannels()
        sample_width = wav.getsampwidth()
        sample_rate = wav.getframerate()
        frames = wav.readframes(wav.getnframes())

    if sample_width == 2:
        samples = array("h")
        scale = 32768.0
    elif sample_width == 4:
        samples = array("i")
        scale = 2147483648.0
    else:
        raise DiarizationUnavailable(
            f"Unsupported WAV sample width: {sample_width}. "
            "FFmpeg should create 16-bit or 32-bit PCM WAV."
        )

    samples.frombytes(frames)
    if sys.byteorder == "big":
        samples.byteswap()

    waveform = torch.tensor(samples, dtype=torch.float32) / scale
    if channels > 1:
        waveform = waveform.reshape(-1, channels).transpose(0, 1).contiguous()
    else:
        waveform = waveform.unsqueeze(0)

    return {"waveform": waveform, "sample_rate": sample_rate}


def _extract_turns(output) -> list[tuple[float, float, str]]:
    diarization = getattr(output, "speaker_diarization", output)

    turns: list[tuple[float, float, str]] = []
    if hasattr(diarization, "itertracks"):
        for turn, _, speaker in diarization.itertracks(yield_label=True):
            turns.append((float(turn.start), float(turn.end), str(speaker)))
        return turns

    for turn, speaker in diarization:
        turns.append((float(turn.start), float(turn.end), str(speaker)))
    return turns


def _mark_overlaps(segments: list[Segment]) -> list[Segment]:
    ordered = sorted(segments, key=lambda item: (item.start, item.end, item.speaker_id))
    for index, segment in enumerate(ordered):
        for other in ordered[max(0, index - 3) : index] + ordered[index + 1 : index + 4]:
            if other.speaker_id == segment.speaker_id:
                continue
            if segment.start < other.end and other.start < segment.end:
                segment.overlap = True
                break
    return ordered


def run_diarization(
    media_path: Path,
    audio_stream_index: int,
    settings: Settings,
    work_dir: Path,
) -> DiarizationResult:
    device = resolve_torch_device(settings.device)
    work_dir.mkdir(parents=True, exist_ok=True)
    analysis_wav = work_dir / f"stream-{audio_stream_index}.analysis.wav"

    command = build_extract_audio_command(
        media_path,
        audio_stream_index,
        analysis_wav,
        settings.ffmpeg_bin,
    )
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    if completed.returncode != 0:
        raise MediaToolError(completed.stderr.strip() or "FFmpeg audio extraction failed")

    pipeline, model_origin = _load_pipeline(settings, device)
    waveform = _load_wav_for_pipeline(analysis_wav)
    try:
        output = pipeline(waveform)
    except NameError as exc:
        if "AudioDecoder" in str(exc):
            raise DiarizationUnavailable(
                "pyannote tried to use its torchcodec AudioDecoder but it is unavailable. "
                "The app attempted waveform mode; rerun setup so torch/pyannote versions are "
                "consistent, then try Analyze again."
            ) from exc
        raise

    turns = _extract_turns(output)
    speaker_ids = sorted({speaker for _, _, speaker in turns})
    speaker_map = {speaker: f"speaker-{index:02d}" for index, speaker in enumerate(speaker_ids)}
    speakers = [
        SpeakerProfile(speaker_id=speaker_map[speaker], label=speaker_map[speaker])
        for speaker in speaker_ids
    ]

    segments = [
        Segment(
            segment_id=f"segment-{index:04d}",
            start=start,
            end=end,
            speaker_id=speaker_map[speaker],
            source_audio_stream=audio_stream_index,
            target_audio_stream=audio_stream_index,
            confidence=0.86,
            notes=f"Detected by {model_origin}",
        )
        for index, (start, end, speaker) in enumerate(turns, start=1)
    ]

    return DiarizationResult(
        segments=_mark_overlaps(segments),
        speakers=speakers,
        model=model_origin,
        device=device,
        audio_path=analysis_wav,
    )
