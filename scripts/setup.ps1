param(
    [string]$Python = ""
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

if (-not $Python) {
    $candidate = Get-Command py -ErrorAction SilentlyContinue
    if ($candidate) {
        $Python = "py -3.12"
    } else {
        $candidate = Get-Command python -ErrorAction SilentlyContinue
        if (-not $candidate) {
            throw "Python 3.11+ was not found. Install Python, then rerun scripts/setup.ps1."
        }
        $Python = "python"
    }
}

Write-Host "Creating virtual environment..."
Invoke-Expression "$Python -m venv .venv"

$VenvPython = Join-Path $RepoRoot ".venv\Scripts\python.exe"
& $VenvPython -m pip install --upgrade pip
& $VenvPython -m pip install -e ".[gui,dev]"

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env from .env.example. Edit ATE_MEDIA_DIR before using personal media."
}

if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
    Write-Warning "ffmpeg was not found on PATH. Install FFmpeg or set ATE_FFMPEG_BIN/ATE_FFPROBE_BIN in .env."
}

Write-Host "Setup complete. Run scripts/doctor.ps1, then scripts/launch.ps1."
