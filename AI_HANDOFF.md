# AI Handoff for K.A.S.L.A.N.A. Protocol

This file is the first document a future AI assistant should read before changing the project.

## Current Goal

K.A.S.L.A.N.A. Protocol is a Python project for a physical-device WeChat voice wake-up assistant. The assistant should call the user's own phone through a real Android phone running WeChat, listen through a physical audio loopback, and answer with AI-generated speech.

The project is intentionally designed around real UI automation and physical audio. It must avoid all WeChat protocol risk.

## Absolute Rules

Do not:

- Use WeChat reverse engineering.
- Hook WeChat.
- Modify WeChat memory.
- Use unofficial WeChat APIs.
- Read or forge WeChat network packets.
- Add protocol-bot libraries.
- Hard-code contacts, API keys, device IDs, model paths, or UI coordinates.

Do:

- Use real Android UI automation only.
- Keep core orchestration dependent on abstract ports.
- Put SDK-specific code in adapters.
- Keep configuration external.
- Prefer fake tests before hardware tests.
- Fail conservatively and hang up when uncertain.

## Current Repository State

Implemented:

- Python package skeleton.
- `pyproject.toml`.
- YAML and `.env` config loading.
- Abstract ports for automation, audio, VAD, ASR, LLM, TTS.
- Core call states and events.
- Async orchestrator skeleton.
- Domain models for call sessions and conversation context.
- Adapter placeholders.
- Unit tests with fake ports.
- Engineering handbook under `docs/`.

Not implemented:

- Real `uiautomator2` adapter.
- Real `sounddevice` input/output.
- Real Silero VAD.
- Real Faster-Whisper ASR.
- Real GPT-SoVITS TTS.
- Real OpenAI-compatible LLM.
- Adapter factory.
- Preflight command.
- Hardware calibration scripts.
- Real scheduler execution.

## Important Files

- `README.md`: concise project entrypoint.
- `AI_TASK_TEMPLATE.md`: reusable prompt for future AI assistants.
- `docs/README.md`: documentation index.
- `docs/00_PROJECT_STATUS.md`: exact current status.
- `docs/01_ARCHITECTURE.md`: architecture rules.
- `docs/02_HARDWARE_PURCHASING_AND_SETUP.md`: hardware procurement and setup.
- `docs/03_WECHAT_AUTOMATION.md`: WeChat UI automation plan.
- `docs/04_AUDIO_VAD_AND_ASR.md`: audio, VAD, ASR plan.
- `docs/05_TTS_GPT_SOVITS.md`: GPT-SoVITS plan.
- `docs/06_LLM_OPENAI_COMPATIBLE.md`: LLM plan.
- `docs/07_ORCHESTRATION_AND_COLLABORATION.md`: orchestration and collaboration.
- `docs/08_TESTING_STANDARDS.md`: testing standards.
- `docs/09_ROADMAP.md`: development roadmap.
- `docs/10_DEVELOPMENT_LOG.md`: chronological development log.
- `src/kaslana/ports/`: abstract interfaces.
- `src/kaslana/core/orchestrator.py`: lifecycle coordinator.
- `config/config.example.yaml`: safe example config.

## Local Environment Observed During Planning

These are observations, not constants:

- ADB exists at `D:\platform-tools-latest-windows\platform-tools\adb.exe`.
- No Android device was connected during the latest planning pass.
- Python was 3.12.4.
- `sounddevice`, `pyaudio`, and `uiautomator2` were not installed during planning.
- PC hardware observed: Intel i9-13900H, 32GB RAM, NVIDIA RTX 4060 Laptop GPU with about 8GB VRAM.

Do not hard-code these values.

## Verification Commands

Run before committing:

```powershell
python -m pytest
python -m ruff check .
git diff --check
```

Config smoke test:

```powershell
python -m kaslana.main --config config/config.example.yaml --check-config
```

## Recommended Next Development Task

Start with hardware diagnostics, not full call automation. Use `AI_TASK_TEMPLATE.md` as the handoff prompt for future assistant sessions.

Recommended next scope:

1. Enhance `scripts/check_devices.py`.
2. Add ADB detection and device state parsing.
3. Add screen resolution, screenshot, battery, and charging checks.
4. Enhance `scripts/list_audio_devices.py` after adding `sounddevice` as an optional dependency.
5. Add tests for parsing fake ADB output.

Why:

- Hardware stability is the highest-risk part.
- It can be tested without touching WeChat.
- It gives later AI assistants concrete device facts.

## Safe Development Pattern

For each module:

1. Read the matching docs file.
2. Inspect existing code.
3. Add or update tests.
4. Implement the smallest useful feature.
5. Run verification commands.
6. Update `AI_HANDOFF.md`, `docs/00_PROJECT_STATUS.md`, relevant module docs, and `docs/10_DEVELOPMENT_LOG.md`.
7. Commit with a narrow message.

## Git Notes

The architecture skeleton was committed as:

```text
a72451b Initialize Kaslana architecture skeleton
```

This documentation pass should be committed as:

```text
Document engineering handbook and AI handoff
```

The AI handoff template pass should be committed as:

```text
Add AI task template and development log
```

## If Unsure

Choose the safer path:

- Do not dial.
- Do not click unknown UI.
- Do not retry calls.
- Do not log secrets.
- Do not touch WeChat internals.
- Ask for human confirmation before moving from diagnosis to real call behavior.
