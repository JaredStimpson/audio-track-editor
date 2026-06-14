# Model Setup

The app is designed to run locally and to support offline use after setup. Some
model files may need to be downloaded once on a machine with internet, but
normal analysis/export should use local files and caches.

## Optional ML Install

The base repo can run tests and metadata commands without ML dependencies. To
prepare for model-backed analysis:

```powershell
scripts/install-ml.ps1 -Device cuda
```

This installs large packages such as torch, pyannote.audio, WhisperX, and
Demucs. Expect this to take time. On the GPU machine, run this setup there so
the CUDA/Torch stack matches that PC.

Direct pip equivalent:

```powershell
.venv\Scripts\python.exe -m pip install -e ".[ml]"
```

For CPU-only development:

```powershell
scripts/install-ml.ps1 -Device cpu
```

For the experimental overlap separation package that usually installs cleanly on
Windows:

```powershell
scripts/install-ml.ps1 -Device cuda -ExperimentalSeparation
```

Asteroid is kept out of the normal ML install because it can pull `pesq`, which
often requires Microsoft C++ Build Tools on Windows:

```powershell
scripts/install-ml.ps1 -Device cuda -Asteroid
```

The script installs PyTorch first so CUDA wheels are chosen deliberately, then
installs the local ML/audio adapters.

## Fixing The `pesq` Build Error

If you see an error like this:

```text
error: Microsoft Visual C++ 14.0 or greater is required
Failed to build installable wheels ... pesq
```

That came from Asteroid's optional dependency chain, not from the core app. Use
the latest repo version, then run the safer install:

```powershell
git pull origin main
scripts/setup.ps1
scripts/install-ml.ps1 -Device cuda
scripts/doctor.ps1
```

If partial Asteroid packages were installed, cleanup is optional:

```powershell
.venv\Scripts\python.exe -m pip uninstall -y asteroid pb-bss-eval pesq torch-stoi torch-optimizer pytorch-ranger
```

Only install Asteroid later if you also install Microsoft C++ Build Tools or a
compatible wheel becomes available for your Python version.

## Model Cache Folder

`ATE_MODEL_CACHE_DIR=models` points to a local cache folder. You usually do not
put anything there manually during normal development. Future model setup
commands should populate it.

For an offline GPU machine, use one of these paths:

- Run model setup once while that machine has internet, then keep
  `ATE_OFFLINE_MODE=true`.
- Download/cache models on another machine and copy those model folders into the
  configured `models/` folder.
- Point `.env` at an existing model cache outside the repo.

## Optional Model Download Token

If a model requires a token:

1. Create a Hugging Face account.
2. Accept the model terms required by pyannote.
3. Create a read token.
4. Set it in `.env`:

```dotenv
HF_TOKEN=hf_your_token_here
```

`.env` is ignored by git.

The token is not for sending media to the cloud. It is only a credential for
downloading gated model files from a provider that requires accepted terms.
Leave it blank for offline/local-only runs.

Recommended order:

1. Get the app working with `scripts/run-first-test.ps1`.
2. Install CUDA ML dependencies on the GPU PC with `scripts/install-ml.ps1 -Device cuda`.
3. Run `scripts/doctor.ps1` and confirm `Torch/CUDA` says CUDA is available.
4. Only add `HF_TOKEN` if a chosen model download explicitly requires it.

## GPU And CPU

Set the preferred device:

```dotenv
ATE_DEVICE=auto
ATE_OFFLINE_MODE=true
```

Supported values:

- `auto`: prefer CUDA when available, otherwise CPU.
- `cuda`: expect NVIDIA GPU/CUDA.
- `cpu`: force CPU fallback.

CPU fallback is useful for development and small tests, but full-episode
analysis will be much slower.

## Privacy

The intended processing path is local after model setup. Do not use cloud model
services unless a future adapter explicitly documents that behavior and requires
user opt-in.

pyannote has optional telemetry in its own library. Audio Track Editor should
default to local/private behavior and document any telemetry-related settings
when the adapter is implemented.
