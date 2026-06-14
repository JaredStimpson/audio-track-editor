from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    root_dir: Path
    media_dir: Path
    model_cache_dir: Path
    output_dir: Path
    hf_token: str | None
    offline_mode: bool
    diarization_model: str
    diarization_model_path: Path | None
    device: str
    confidence_threshold: float
    ffmpeg_bin: str
    ffprobe_bin: str


def find_project_root(start: Path | None = None) -> Path:
    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / "pyproject.toml").exists() or (candidate / ".git").exists():
            return candidate
    return current


def parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            values[key] = value
    return values


def _load_local_toml(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}

    data = tomllib.loads(path.read_text(encoding="utf-8"))
    values: dict[str, str] = {}
    paths = data.get("paths", {})
    runtime = data.get("runtime", {})
    auth = data.get("auth", {})

    mapping = {
        "ATE_MEDIA_DIR": paths.get("media_dir"),
        "ATE_MODEL_CACHE_DIR": paths.get("model_cache_dir"),
        "ATE_OUTPUT_DIR": paths.get("output_dir"),
        "ATE_OFFLINE_MODE": runtime.get("offline_mode"),
        "ATE_DIARIZATION_MODEL": runtime.get("diarization_model"),
        "ATE_DIARIZATION_MODEL_PATH": runtime.get("diarization_model_path"),
        "ATE_DEVICE": runtime.get("device"),
        "ATE_CONFIDENCE_THRESHOLD": runtime.get("confidence_threshold"),
        "ATE_FFMPEG_BIN": runtime.get("ffmpeg_bin"),
        "ATE_FFPROBE_BIN": runtime.get("ffprobe_bin"),
        "HF_TOKEN": auth.get("hf_token"),
    }
    for key, value in mapping.items():
        if value is not None:
            values[key] = str(value)
    return values


def _resolve_path(root: Path, value: str | None, default: str) -> Path:
    raw = value or default
    expanded = Path(os.path.expandvars(os.path.expanduser(raw)))
    if not expanded.is_absolute():
        expanded = root / expanded
    return expanded.resolve()


def _as_bool(value: str | None, default: bool) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def load_settings(root: Path | None = None) -> Settings:
    root_dir = find_project_root(root)
    local_toml = _load_local_toml(root_dir / ".ate.local.toml")
    env_file = parse_env_file(root_dir / ".env")

    merged: dict[str, str] = {}
    merged.update(local_toml)
    merged.update(env_file)
    merged.update({key: value for key, value in os.environ.items() if key.startswith("ATE_")})
    if "HF_TOKEN" in os.environ:
        merged["HF_TOKEN"] = os.environ["HF_TOKEN"]

    threshold_raw = merged.get("ATE_CONFIDENCE_THRESHOLD", "0.68")
    try:
        threshold = float(threshold_raw)
    except ValueError:
        threshold = 0.68

    return Settings(
        root_dir=root_dir,
        media_dir=_resolve_path(root_dir, merged.get("ATE_MEDIA_DIR"), "sample-media"),
        model_cache_dir=_resolve_path(root_dir, merged.get("ATE_MODEL_CACHE_DIR"), "models"),
        output_dir=_resolve_path(root_dir, merged.get("ATE_OUTPUT_DIR"), "exports"),
        hf_token=merged.get("HF_TOKEN") or None,
        offline_mode=_as_bool(merged.get("ATE_OFFLINE_MODE"), True),
        diarization_model=merged.get(
            "ATE_DIARIZATION_MODEL",
            "pyannote/speaker-diarization-community-1",
        ),
        diarization_model_path=(
            _resolve_path(root_dir, merged["ATE_DIARIZATION_MODEL_PATH"], "")
            if merged.get("ATE_DIARIZATION_MODEL_PATH")
            else None
        ),
        device=merged.get("ATE_DEVICE", "auto"),
        confidence_threshold=threshold,
        ffmpeg_bin=merged.get("ATE_FFMPEG_BIN", "ffmpeg"),
        ffprobe_bin=merged.get("ATE_FFPROBE_BIN", "ffprobe"),
    )
