param(
    [ValidateSet("cuda", "cpu")]
    [string]$Device = "cuda",

    [ValidateSet("cu128", "cu126", "cu118")]
    [string]$CudaWheel = "cu128",

    [switch]$ExperimentalSeparation,

    [switch]$Asteroid,

    [switch]$NoTranscript
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot
$LogFile = $null

if (-not $NoTranscript) {
    $LogDir = Join-Path $RepoRoot "logs"
    New-Item -ItemType Directory -Force $LogDir | Out-Null
    $LogFile = Join-Path $LogDir ("install-ml-{0}.log" -f (Get-Date -Format "yyyyMMdd-HHmmss"))
    Start-Transcript -Path $LogFile -Append | Out-Null
}

try {
    if (-not (Test-Path ".venv\Scripts\python.exe")) {
        throw "Virtual environment is missing. Run scripts/setup.ps1 first."
    }

    $Python = Join-Path $RepoRoot ".venv\Scripts\python.exe"

    & $Python -m pip install --upgrade pip

    if ($Device -eq "cuda") {
        Write-Host "Installing PyTorch CUDA wheels from $CudaWheel..."
        & $Python -m pip install torch torchvision torchaudio --index-url "https://download.pytorch.org/whl/$CudaWheel"
    } else {
        Write-Host "Installing PyTorch CPU wheels..."
        & $Python -m pip install torch torchvision torchaudio --index-url "https://download.pytorch.org/whl/cpu"
    }

    Write-Host "Installing local ML/audio adapters..."
    & $Python -m pip install pyannote.audio whisperx demucs

    if ($ExperimentalSeparation) {
        Write-Host "Installing experimental overlap separation adapter..."
        & $Python -m pip install speechbrain
    }

    if ($Asteroid) {
        Write-Warning "Asteroid can pull pesq, which may require Microsoft C++ Build Tools on Windows."
        Write-Warning "Install this only if you are ready for native package builds."
        & $Python -m pip install asteroid
    }

    Write-Host "ML install complete. Run scripts/doctor.ps1 and check Torch/CUDA."
} finally {
    if (-not $NoTranscript) {
        Stop-Transcript | Out-Null
        Write-Host "ML install log: $LogFile"
    }
}
