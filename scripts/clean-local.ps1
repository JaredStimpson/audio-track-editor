param(
    [switch]$RemoveEnv,
    [switch]$RemoveMedia,
    [switch]$RemoveModels,
    [switch]$RemoveExports,
    [switch]$RemoveLogs
)

$ErrorActionPreference = "Stop"
$RepoRoot = (Resolve-Path (Split-Path -Parent $PSScriptRoot)).Path
Set-Location $RepoRoot

function Remove-RepoPath {
    param([string]$PathValue)

    $resolved = Resolve-Path $PathValue -ErrorAction SilentlyContinue
    if (-not $resolved) {
        return
    }

    $target = $resolved.Path
    if (-not $target.StartsWith($RepoRoot)) {
        throw "Refusing to remove path outside repo: $target"
    }

    Remove-Item -LiteralPath $target -Recurse -Force
    Write-Host "Removed $target"
}

Remove-RepoPath ".venv"
Remove-RepoPath ".pytest_cache"
Remove-RepoPath ".ruff_cache"
Remove-RepoPath "analysis-cache"
Remove-RepoPath ".ate-cache"

Get-ChildItem -Path $RepoRoot -Recurse -Directory -Filter "__pycache__" |
    ForEach-Object { Remove-RepoPath $_.FullName }

if ($RemoveEnv) {
    Remove-RepoPath ".env"
    Remove-RepoPath ".ate.local.toml"
}

if ($RemoveMedia) {
    Remove-RepoPath "sample-media"
    Remove-RepoPath "local-media"
}

if ($RemoveModels) {
    Remove-RepoPath "models"
}

if ($RemoveExports) {
    Remove-RepoPath "exports"
}

if ($RemoveLogs) {
    Remove-RepoPath "logs"
}

Write-Host "Local cleanup complete."
