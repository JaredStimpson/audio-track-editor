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

function Get-LocalConfigValue {
    param(
        [string]$Key,
        [string]$DefaultValue
    )

    if (-not (Test-Path ".env")) {
        return $DefaultValue
    }

    $line = Get-Content ".env" | Where-Object { $_ -match "^\s*$Key\s*=" } | Select-Object -First 1
    if (-not $line) {
        return $DefaultValue
    }

    return ($line -replace "^\s*$Key\s*=", "").Trim().Trim('"').Trim("'")
}

function Resolve-LocalPath {
    param([string]$Value)

    $expanded = [Environment]::ExpandEnvironmentVariables($Value)
    if ([System.IO.Path]::IsPathRooted($expanded)) {
        return $expanded
    }
    return (Join-Path $RepoRoot $expanded)
}

$MediaDir = Resolve-LocalPath (Get-LocalConfigValue "ATE_MEDIA_DIR" "sample-media")
$ModelDir = Resolve-LocalPath (Get-LocalConfigValue "ATE_MODEL_CACHE_DIR" "models")
$OutputDir = Resolve-LocalPath (Get-LocalConfigValue "ATE_OUTPUT_DIR" "exports")

New-Item -ItemType Directory -Force $MediaDir | Out-Null
New-Item -ItemType Directory -Force $ModelDir | Out-Null
New-Item -ItemType Directory -Force $OutputDir | Out-Null
Write-Host "Ensured local folders:"
Write-Host "  Input media: $MediaDir"
Write-Host "  Model cache: $ModelDir"
Write-Host "  Exports:     $OutputDir"

if (-not (Get-Command ffmpeg -ErrorAction SilentlyContinue)) {
    Write-Warning "ffmpeg was not found on PATH. Install FFmpeg or set ATE_FFMPEG_BIN/ATE_FFPROBE_BIN in .env."
}

Write-Host "Setup complete. Run scripts/doctor.ps1, then scripts/launch.ps1."
