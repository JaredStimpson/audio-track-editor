from pathlib import Path

from audio_track_editor.config import load_settings, parse_env_file


def test_parse_env_file_ignores_comments(tmp_path: Path) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "# comment",
                "ATE_MEDIA_DIR=local-media",
                "HF_TOKEN='secret'",
                "",
            ]
        ),
        encoding="utf-8",
    )

    assert parse_env_file(env_file) == {"ATE_MEDIA_DIR": "local-media", "HF_TOKEN": "secret"}


def test_load_settings_uses_ignored_env_paths(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    (tmp_path / ".env").write_text(
        "ATE_MEDIA_DIR=sample-media\nATE_OUTPUT_DIR=exports\nATE_DEVICE=cpu\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("ATE_MEDIA_DIR", raising=False)
    monkeypatch.delenv("ATE_OUTPUT_DIR", raising=False)
    monkeypatch.delenv("ATE_DEVICE", raising=False)

    settings = load_settings(tmp_path)

    assert settings.media_dir == (tmp_path / "sample-media").resolve()
    assert settings.output_dir == (tmp_path / "exports").resolve()
    assert settings.device == "cpu"
    assert settings.offline_mode is True


def test_load_settings_can_disable_offline_mode(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n", encoding="utf-8")
    (tmp_path / ".env").write_text("ATE_OFFLINE_MODE=false\n", encoding="utf-8")
    monkeypatch.delenv("ATE_OFFLINE_MODE", raising=False)

    settings = load_settings(tmp_path)

    assert settings.offline_mode is False
