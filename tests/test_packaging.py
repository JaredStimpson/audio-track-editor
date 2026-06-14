import tomllib
from pathlib import Path


def test_default_ml_extra_avoids_asteroid_native_build_trap() -> None:
    pyproject = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))

    optional = pyproject["project"]["optional-dependencies"]

    assert "asteroid>=0.7" not in optional["ml"]
    assert "asteroid>=0.7" in optional["asteroid"]


def test_setup_is_all_in_one_and_logs() -> None:
    setup = Path("scripts/setup.ps1").read_text(encoding="utf-8")

    assert "install-ml.ps1" in setup
    assert "Start-Transcript" in setup
    assert "-SkipMl" in setup
    assert "$InstallArgs = @{" in setup
    assert '@("-Device", $Device' not in setup


def test_handoff_docs_exist() -> None:
    assert Path("docs/AI_HANDOFF.md").exists()
    assert Path("docs/prompt-history.md").exists()
