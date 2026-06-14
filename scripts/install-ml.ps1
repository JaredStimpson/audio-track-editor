param(
    [ValidateSet("cuda", "cpu")]
    [string]$Device = "cuda",

    [ValidateSet("cu128", "cu126", "cu118")]
    [string]$CudaWheel = "cu128",

    [switch]$ExperimentalSeparation,

    [switch]$Asteroid
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

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
