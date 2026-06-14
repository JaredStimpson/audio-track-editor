$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

if (Test-Path ".venv\Scripts\ate.exe") {
    & ".venv\Scripts\ate.exe" doctor
} else {
    python -m audio_track_editor doctor
}
