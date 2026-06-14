from __future__ import annotations

import os

from audio_track_editor.config import Settings
from audio_track_editor.diarization import DiarizationUnavailable, _prepare_model_environment


def cache_diarization_model(settings: Settings, allow_download: bool = False) -> str:
    try:
        from pyannote.audio import Pipeline
    except ImportError as exc:
        raise DiarizationUnavailable(
            "pyannote.audio is required before caching the diarization model. "
            "Run scripts/setup.ps1 -Device cuda first."
        ) from exc

    model_origin = str(settings.diarization_model_path or settings.diarization_model)
    _prepare_model_environment(settings)

    if allow_download:
        os.environ.pop("HF_HUB_OFFLINE", None)
        os.environ.pop("TRANSFORMERS_OFFLINE", None)

    if not settings.diarization_model_path and not settings.hf_token and allow_download:
        raise DiarizationUnavailable(
            "HF_TOKEN is required for the first download of "
            f"{settings.diarization_model}. Accept the model conditions, create a "
            "read token, set it in .env, then rerun this command."
        )

    try:
        Pipeline.from_pretrained(
            model_origin,
            token=settings.hf_token if not settings.diarization_model_path else None,
        )
    except Exception as exc:
        raise DiarizationUnavailable(
            f"Could not cache/load diarization model {model_origin}. Original error: {exc}"
        ) from exc

    return model_origin
