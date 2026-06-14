# Update And Cleanup

Use these commands on the GPU PC after changes have been pushed to GitHub.

## Update To Latest

```powershell
cd C:\path\to\audio-track-editor
git fetch origin
git switch test
git pull origin test
scripts/setup.ps1 -Device cuda
scripts/doctor.ps1
```

`git pull origin test` updates committed source files from the current test
branch. `scripts/setup.ps1 -Device cuda` refreshes the Python environment,
installs the core local ML stack, creates the ignored local folders from `.env`,
and writes a setup log under `logs/`.

If the update adds or changes ML dependencies on the GPU PC, run:

```powershell
scripts/install-ml.ps1 -Device cuda
scripts/doctor.ps1
```

If the selected diarization model is not cached yet:

```powershell
scripts/cache-model.ps1 -AllowDownload
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

It does not remove `.env`, media, models, exports, or logs by default.

Use explicit switches for those:

```powershell
scripts/clean-local.ps1 -RemoveEnv
scripts/clean-local.ps1 -RemoveExports
scripts/clean-local.ps1 -RemoveModels
scripts/clean-local.ps1 -RemoveMedia
scripts/clean-local.ps1 -RemoveLogs
```

Be careful with `-RemoveMedia` and `-RemoveModels` if those folders contain files
you want to keep.
