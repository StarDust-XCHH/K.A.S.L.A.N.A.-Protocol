![alt text](assets/preview.jpg)

# K.A.S.L.A.N.A. Protocol


K.A.S.L.A.N.A. Protocol (Kinetic Audio Stream & Local Automated Network Assistant) is a Python architecture for a physical-device WeChat voice wake-up assistant.

The safety boundary is strict: the system must not use WeChat reverse engineering, hooks, memory modification, or unofficial protocol APIs. All WeChat interaction must be modeled as human-like UI automation on a real Android device.

## Current Stage

This repository currently contains the modular architecture and engineering handbook only. It defines interfaces, configuration loading, the call state machine, an async orchestrator skeleton, adapter placeholders, docs, and unit tests.

Real ADB/UI automation, audio hardware, ASR, LLM, VAD, and TTS implementations are intentionally left for later module-by-module development.

## Start Here

For future AI assistants and long-running development, read these first:

- [AI_HANDOFF.md](AI_HANDOFF.md)
- [AI_TASK_TEMPLATE.md](AI_TASK_TEMPLATE.md)
- [docs/README.md](docs/README.md)
- [docs/00_PROJECT_STATUS.md](docs/00_PROJECT_STATUS.md)
- [docs/01_ARCHITECTURE.md](docs/01_ARCHITECTURE.md)
- [docs/09_ROADMAP.md](docs/09_ROADMAP.md)
- [docs/10_DEVELOPMENT_LOG.md](docs/10_DEVELOPMENT_LOG.md)
- [FEATURES_TESTING.md](FEATURES_TESTING.md)

## Project Shape

```text
src/kaslana/
  config/      typed YAML and .env loading
  core/        call states, events, orchestrator, scheduler
  ports/       abstract interfaces for all external capabilities
  adapters/    concrete implementation placeholders
  domain/      call session and conversation objects
  utils/       logging and audio path helpers
docs/          Chinese engineering handbook and module plans
tests/         unit tests first, integration tests reserved
```

## Local Setup

Recommended conda setup with RTX 4060 Laptop GPU / CUDA PyTorch support:

```powershell
.\scripts\setup_kaslana_conda_env.ps1
conda run -n kaslana-protocol python scripts\check_gpu.py
conda run -n kaslana-protocol python -m pytest
conda run -n kaslana-protocol python scripts\try_gpt_sovits_tts.py --list-emotions
```

The setup script creates or updates the `kaslana-protocol` conda environment, installs the CUDA 12.8 PyTorch wheels, installs this package in editable mode, and creates local-only `.env` / `config/config.yaml` files when missing.

Reusable local GSVI TTS server check:

```powershell
.\scripts\start_gsvi_tts_server.ps1 -Port 5100
conda run -n kaslana-protocol python scripts\check_tts_server.py
conda run -n kaslana-protocol python scripts\try_gpt_sovits_tts.py --api-style gsvi --character "琪亚娜E7" --text "早安，该起床啦。"
```

The GSVI server lives under ignored `local_assets/`; generated WAV files are written under ignored `diagnostics/`.

Local browser TTS control panel:

```powershell
.\scripts\start_tts_control_panel.ps1
```

The panel opens at `http://127.0.0.1:8765` and can start/stop the local GSVI service, select emotions, synthesize short text, and play the generated WAV in the browser.

Lightweight venv setup for architecture-only development:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
python -m pytest
```

## Configuration

Copy the examples before running real hardware modules:

```powershell
Copy-Item .env.example .env
Copy-Item config/config.example.yaml config/config.yaml
```

All device IDs, coordinates, contact aliases, model endpoints, and API keys must come from `.env` or YAML. Do not commit real secrets, real contacts, private device identifiers, model weights, reference audio, or generated call recordings.

## Verification

```powershell
python -m pytest
python -m ruff check .
git diff --check
python -m kaslana.main --config config/config.example.yaml --check-config
```

## Development Discipline

1. Keep the orchestrator dependent only on `ports/` abstract classes.
2. Implement one adapter at a time under `adapters/`.
3. Add fake or contract tests before connecting real hardware.
4. Add integration checks only after pure architecture tests pass.
5. Commit small, named steps so Git history mirrors the module-by-module build.
