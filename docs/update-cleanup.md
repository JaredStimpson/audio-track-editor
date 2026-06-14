# Update And Cleanup

Use these commands on the GPU PC after changes have been pushed to GitHub.

## Update To Latest

```powershell
cd C:\path\to\audio-track-editor
git pull origin main
scripts/setup.ps1
scripts/doctor.ps1
```

`git pull` updates committed source files. `scripts/setup.ps1` refreshes the
Python environment and creates the ignored local folders from `.env`.

If the update adds or changes ML dependencies on the GPU PC, run:

```powershell
scripts/install-ml.ps1 -Device cuda
scripts/doctor.ps1
```

## Local Cleanup

Normal updates do not remove ignored folders like `.venv`, caches, exports,
models, or media. To remove dev artifacts that setup/tests created:

```powershell
scripts/clean-local.ps1
```

That removes:

- `.venv`
- `.pytest_cache`
- `.ruff_cache`
- `.ate-cache`
- `analysis-cache`
- `__pycache__` folders

It does not remove `.env`, media, models, or exports by default.

Use explicit switches for those:

```powershell
scripts/clean-local.ps1 -RemoveEnv
scripts/clean-local.ps1 -RemoveExports
scripts/clean-local.ps1 -RemoveModels
scripts/clean-local.ps1 -RemoveMedia
```

Be careful with `-RemoveMedia` and `-RemoveModels` if those folders contain files
you want to keep.
