# K.A.S.L.A.N.A. Protocol

K.A.S.L.A.N.A. Protocol (Kinetic Audio Stream & Local Automated Network Assistant) is a Python architecture for a physical-device WeChat voice wake-up assistant. The safety boundary is strict: the system must not use WeChat reverse engineering, hooks, memory modification, or unofficial protocol APIs. All WeChat interaction is modeled as human-like UI automation on a real Android device.

## First-Stage Goal

This repository currently contains the modular architecture only. It defines interfaces, configuration loading, the call state machine, an async orchestrator skeleton, adapter placeholders, and unit tests. Real ADB/UI automation, audio hardware, ASR, LLM, VAD, and TTS implementations are intentionally left for later module-by-module development.

## Project Shape

```text
src/kaslana/
  config/      typed YAML and .env loading
  core/        call states, events, orchestrator, scheduler
  ports/       abstract interfaces for all external capabilities
  adapters/    concrete implementation placeholders
  domain/      call session and conversation objects
  utils/       logging and audio path helpers
tests/
  unit/        pure Python architecture tests
  integration/ reserved for hardware/model smoke tests
```

## Local Setup

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

All device IDs, coordinates, contact aliases, model endpoints, and API keys must come from `.env` or YAML. Do not commit real secrets, real contacts, or private device identifiers.

## Development Flow

1. Keep the orchestrator dependent only on `ports/` abstract classes.
2. Implement one adapter at a time under `adapters/`.
3. Add fake or contract tests before connecting real hardware.
4. Add integration checks only after the pure architecture tests pass.
5. Commit small, named steps so Git history mirrors the module-by-module build.
