$NoTranscript = $false
foreach ($arg in $args) {
    if ($arg -eq "-NoTranscript") {
        $NoTranscript = $true
    }
}

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot
$LogFile = $null

if (-not $NoTranscript) {
    $LogDir = Join-Path $RepoRoot "logs"
    New-Item -ItemType Directory -Force $LogDir | Out-Null
    $LogFile = Join-Path $LogDir ("doctor-{0}.log" -f (Get-Date -Format "yyyyMMdd-HHmmss"))
    Start-Transcript -Path $LogFile -Append | Out-Null
}

try {
    if (Test-Path ".venv\Scripts\ate.exe") {
        & ".venv\Scripts\ate.exe" doctor
    } else {
        python -m audio_track_editor doctor
    }
} finally {
    if (-not $NoTranscript) {
        Stop-Transcript | Out-Null
        Write-Host "Doctor log: $LogFile"
    }
}
