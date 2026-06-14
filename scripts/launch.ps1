$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot
$LogDir = Join-Path $RepoRoot "logs"
New-Item -ItemType Directory -Force $LogDir | Out-Null
$LogFile = Join-Path $LogDir ("launch-{0}.log" -f (Get-Date -Format "yyyyMMdd-HHmmss"))

Start-Transcript -Path $LogFile -Append | Out-Null

try {
    if (-not (Test-Path ".venv\Scripts\audio-track-editor.exe")) {
        throw "Virtual environment is missing. Run scripts/setup.ps1 first."
    }

    & ".venv\Scripts\audio-track-editor.exe"
} finally {
    Stop-Transcript | Out-Null
    Write-Host "Launch log: $LogFile"
}
