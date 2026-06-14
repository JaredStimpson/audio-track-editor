param(
    [switch]$AllowDownload
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot
$LogDir = Join-Path $RepoRoot "logs"
New-Item -ItemType Directory -Force $LogDir | Out-Null
$LogFile = Join-Path $LogDir ("cache-model-{0}.log" -f (Get-Date -Format "yyyyMMdd-HHmmss"))

Start-Transcript -Path $LogFile -Append | Out-Null

try {
    if (-not (Test-Path ".venv\Scripts\ate.exe")) {
        throw "Virtual environment is missing. Run scripts/setup.ps1 first."
    }

    $Args = @("cache-model")
    if ($AllowDownload) {
        $Args += "--allow-download"
    }

    & ".venv\Scripts\ate.exe" @Args
} finally {
    Stop-Transcript | Out-Null
    Write-Host "Cache-model log: $LogFile"
}
