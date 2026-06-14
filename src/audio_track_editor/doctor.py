from __future__ import annotations

import importlib.util
import sys
from dataclasses import dataclass

from audio_track_editor.config import Settings
from audio_track_editor.media import executable_available


@dataclass(frozen=True)
class DoctorCheck:
    name: str
    ok: bool
    detail: str
    recommendation: str = ""


def _module_available(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except ModuleNotFoundError:
        return False


def run_doctor(settings: Settings) -> list[DoctorCheck]:
    checks = [
        DoctorCheck("Python", sys.version_info >= (3, 11), sys.version.split()[0]),
        DoctorCheck(
            "FFmpeg",
            executable_available(settings.ffmpeg_bin),
            settings.ffmpeg_bin,
            "Install FFmpeg or set ATE_FFMPEG_BIN in .env.",
        ),
        DoctorCheck(
            "ffprobe",
            executable_available(settings.ffprobe_bin),
            settings.ffprobe_bin,
            "Install FFmpeg or set ATE_FFPROBE_BIN in .env.",
        ),
        DoctorCheck(
            "PySide6",
            _module_available("PySide6"),
            "required for GUI",
            "Run scripts/setup.ps1 to install GUI dependencies.",
        ),
        DoctorCheck(
            "pyannote.audio",
            _module_available("pyannote.audio"),
            "local diarization adapter",
            "Run scripts/install-ml.ps1 on the GPU PC.",
        ),
        DoctorCheck(
            "WhisperX",
            _module_available("whisperx"),
            "local ASR/alignment adapter",
            "Run scripts/install-ml.ps1 on the GPU PC.",
        ),
        DoctorCheck(
            "Demucs",
            _module_available("demucs"),
            "local vocal/background separation adapter",
            "Run scripts/install-ml.ps1 on the GPU PC.",
        ),
        DoctorCheck(
            "Offline mode",
            True,
            "enabled" if settings.offline_mode else "disabled for model download/setup",
        ),
        DoctorCheck(
            "Diarization model",
            True,
            str(settings.diarization_model_path or settings.diarization_model),
        ),
        DoctorCheck(
            "Optional model download token",
            True,
            "present" if settings.hf_token else "not configured; local cached models only",
        ),
        DoctorCheck("Model cache", True, str(settings.model_cache_dir)),
        DoctorCheck("Media dir", True, str(settings.media_dir)),
        DoctorCheck("Output dir", True, str(settings.output_dir)),
    ]

    torch_detail = "torch unavailable"
    torch_ok = False
    torch_recommendation = "Run scripts/install-ml.ps1 -Device cuda on the GPU PC."
    if _module_available("torch"):
        import torch

        cuda_ok = torch.cuda.is_available()
        torch_ok = settings.device in {"cpu", "auto"} or cuda_ok
        cuda_status = "yes" if cuda_ok else "no"
        torch_detail = f"torch installed; cuda={cuda_status}; device={settings.device}"
        if torch_ok:
            torch_recommendation = ""
        elif settings.device == "cuda":
            torch_recommendation = "CUDA is requested but unavailable to torch."
    checks.append(DoctorCheck("Torch/CUDA", torch_ok, torch_detail, torch_recommendation))
    return checks


def format_checks(checks: list[DoctorCheck], include_recommendations: bool = True) -> str:
    lines = []
    for check in checks:
        marker = "OK" if check.ok else "WARN"
        lines.append(f"[{marker}] {check.name}: {check.detail}")
        if include_recommendations and not check.ok and check.recommendation:
            lines.append(f"  Next: {check.recommendation}")
    return "\n".join(lines)
