# Model Setup

The app is designed to run locally after setup. Some model files may still need
to be downloaded once, and some pyannote models require accepting terms on
Hugging Face.

## Optional ML Install

The base repo can run tests and metadata commands without ML dependencies. To
prepare for model-backed analysis:

```powershell
.venv\Scripts\python.exe -m pip install -e ".[ml]"
```

This installs large packages such as torch, pyannote.audio, WhisperX, Demucs,
SpeechBrain, and Asteroid. Expect this to take time.

## Hugging Face Token

If a model requires a token:

1. Create a Hugging Face account.
2. Accept the model terms required by pyannote.
3. Create a read token.
4. Set it in `.env`:

```dotenv
HF_TOKEN=hf_your_token_here
```

`.env` is ignored by git.

## GPU And CPU

Set the preferred device:

```dotenv
ATE_DEVICE=auto
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
