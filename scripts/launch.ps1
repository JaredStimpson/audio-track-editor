$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

if (-not (Test-Path ".venv\Scripts\audio-track-editor.exe")) {
    throw "Virtual environment is missing. Run scripts/setup.ps1 first."
}

& ".venv\Scripts\audio-track-editor.exe"
