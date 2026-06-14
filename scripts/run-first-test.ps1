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
    $LogFile = Join-Path $LogDir ("first-test-{0}.log" -f (Get-Date -Format "yyyyMMdd-HHmmss"))
    Start-Transcript -Path $LogFile -Append | Out-Null
}

try {
    if (-not (Test-Path ".venv\Scripts\ate.exe")) {
        throw "Virtual environment is missing. Run scripts/setup.ps1 first."
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

    $Ffmpeg = Get-LocalConfigValue "ATE_FFMPEG_BIN" "ffmpeg"
    if (-not (Get-Command $Ffmpeg -ErrorAction SilentlyContinue) -and -not (Test-Path $Ffmpeg)) {
        throw "FFmpeg was not found. Install FFmpeg or set ATE_FFMPEG_BIN in .env."
    }

    $SampleDir = Join-Path $RepoRoot "sample-media"
    $ExportDir = Join-Path $RepoRoot "exports"
    New-Item -ItemType Directory -Force $SampleDir | Out-Null
    New-Item -ItemType Directory -Force $ExportDir | Out-Null

    $Media = Join-Path $SampleDir "first-test.mkv"
    $Project = Join-Path $ExportDir "first-test.ateproj.json"
    $Output = Join-Path $ExportDir "first-test-export.mkv"

    Write-Host "Creating synthetic multi-audio MKV..."
    & $Ffmpeg -y `
        -f lavfi -i "testsrc=size=640x360:rate=24:duration=4" `
        -f lavfi -i "sine=frequency=440:duration=4" `
        -f lavfi -i "sine=frequency=660:duration=4" `
        -map 0:v -map 1:a -map 2:a `
        -c:v mpeg4 -c:a aac -shortest `
        -metadata:s:a:0 language=eng `
        -metadata:s:a:0 title="English synthetic" `
        -metadata:s:a:1 language=jpn `
        -metadata:s:a:1 title="Japanese synthetic" `
        $Media

    Write-Host "Analyzing synthetic media..."
    & ".venv\Scripts\ate.exe" analyze $Media --project $Project

    Write-Host "Exporting synthetic MKV with fallback subtitles..."
    & ".venv\Scripts\ate.exe" export $Project --output $Output

    Write-Host "First test complete:"
    Write-Host "  Media:   $Media"
    Write-Host "  Project: $Project"
    Write-Host "  Output:  $Output"
} finally {
    if (-not $NoTranscript) {
        Stop-Transcript | Out-Null
        Write-Host "First-test log: $LogFile"
    }
}
