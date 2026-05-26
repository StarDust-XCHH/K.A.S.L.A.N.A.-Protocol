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
- Offline prefetch/cache skeleton with `INTENT_MATCHING` fallback flow.
- Domain models for call sessions and conversation context.
- Domain models and ports for offline ingestion, weather, dialogue cache, and intent routing.
- Adapter placeholders.
- JSON dialogue cache adapter, Regex intent router, local file ingestion adapter, and static weather placeholder.
- Minimal GPT-SoVITS HTTP TTS adapter that can read `infer_config.json` and synthesize one WAV through official API or GSVI-style local service.
- `scripts/try_gpt_sovits_tts.py` for safe local TTS smoke tests without WeChat or audio hardware playback.
- Reusable local GSVI server deployment under ignored `local_assets/GSVI-2.2.4-240318/GPT-SoVITS-Inference/`.
- `scripts/start_gsvi_tts_server.ps1` starts the prepackaged GSVI runtime on loopback only, and `scripts/check_tts_server.py` checks `/character_list` plus optional short synthesis.
- `scripts/tts_control_panel.py` provides a local browser TTS control panel for starting/stopping GSVI, selecting emotion, synthesizing test text, and playing generated WAVs in-browser.
- Dedicated `kaslana-protocol` conda environment template with RTX 4060 Laptop GPU / CUDA PyTorch setup script.
- Unit tests with fake ports.
- Engineering handbook under `docs/`.

Not implemented:

- Real `uiautomator2` adapter.
- Real `sounddevice` input/output.
- Real Silero VAD.
- Real Faster-Whisper ASR.
- Full GPT-SoVITS integration into adapter factory, playback, cache, and orchestrator flow.
- Real OpenAI-compatible LLM.
- Real offline weather provider.
- Real nightly adapter factory for offline preprocessing.
- Adapter factory.
- Preflight command.
- Hardware calibration scripts.
- Real scheduler execution.

## Important Files

- `README.md`: concise project entrypoint.
- `FEATURES_TESTING.md`: safe local feature test commands and script grouping.
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
- `docs/11_OFFLINE_RAG_PRECACHE.md`: offline prefetch and dialogue cache plan.
- `docs/12_OWNER_HARDWARE_PREP_MANUAL.md`: owner-facing Xiaomi 13 hardware preparation checklist.
- `docs/13_AI_TASK_HARDWARE_DIAGNOSTICS.md`: next AI task brief for the first hardware diagnostics implementation.
- `src/kaslana/ports/`: abstract interfaces.
- `src/kaslana/core/orchestrator.py`: lifecycle coordinator.
- `src/kaslana/adapters/tts/gpt_sovits.py`: minimal GPT-SoVITS HTTP adapter.
- `scripts/try_gpt_sovits_tts.py`: safe one-shot TTS smoke-test CLI.
- `scripts/start_gsvi_tts_server.ps1`: starts the ignored local GSVI server using its bundled runtime.
- `scripts/stop_gsvi_tts_server.ps1`: stops only the project-managed GSVI process.
- `scripts/check_tts_server.py`: safe local GSVI health check and optional one-shot synthesis.
- `scripts/tts_control_panel.py`: local browser control panel served on loopback only.
- `scripts/start_tts_control_panel.ps1`: starts the browser control panel.
- `environment.yml`: dedicated conda environment template.
- `scripts/setup_kaslana_conda_env.ps1`: create/update the dedicated conda environment.
- `scripts/check_gpu.py`: PyTorch CUDA smoke check.
- `config/config.example.yaml`: safe example config.

## Local Environment Observed During Planning

These are observations, not constants:

- ADB exists at `D:\platform-tools-latest-windows\platform-tools\adb.exe`.
- No Android device was connected during the latest planning pass.
- Python was 3.12.4.
- `sounddevice`, `pyaudio`, and `uiautomator2` were not installed during planning.
- PC hardware observed: Intel i9-13900H, 32GB RAM, NVIDIA RTX 4060 Laptop GPU with about 8GB VRAM.
- Latest dedicated environment target: `kaslana-protocol`, Python 3.11, PyTorch CUDA 12.8 wheels for the RTX 4060 Laptop GPU.
- The local network/proxy environment observed `verge-mihomo` binding port `5000`, so the reusable GSVI endpoint is set to `http://127.0.0.1:5100`.
- GSVI prepack and model assets are in ignored `local_assets/`; generated TTS WAV checks are in ignored `diagnostics/tts/`.
- The browser TTS control panel defaults to `http://127.0.0.1:8765` and writes generated WAV files to ignored `diagnostics/tts/control_panel/`.

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

Default recommendation is still to start with hardware diagnostics, not full call automation. The owner should first complete `docs/12_OWNER_HARDWARE_PREP_MANUAL.md` for the Xiaomi 13 A-side phone, then the next AI assistant should use `docs/13_AI_TASK_HARDWARE_DIAGNOSTICS.md` as the concrete task brief.

Recommended next scope:

1. Confirm the Xiaomi 13 appears in `adb devices` as `device`.
2. Enhance `scripts/check_devices.py`.
3. Add ADB detection and device state parsing.
4. Add screen resolution, optional screenshot, battery, and charging checks.
5. Add tests for parsing fake ADB output.

Why:

- Hardware stability is the highest-risk part.
- It can be tested without touching WeChat.
- It gives later AI assistants concrete device facts.

Alternative next scope if continuing the offline-cache track:

1. Add adapter factory wiring for `offline_cache`, `ingestion`, `intent_matching`, and `batch_preprocess`.
2. Add a PromptManager for stable dialogue-state-tree JSON.
3. Add fake LLM/TTS tests for `OfflinePreprocessor`.
4. Add cache health checks before the morning call.
5. Keep offline cache disabled by default until real adapters are tested.

Alternative next scope if continuing the TTS track:

1. Keep the local GSVI server running with `scripts/start_gsvi_tts_server.ps1 -Port 5100`.
2. Or use `scripts/start_tts_control_panel.ps1` for browser-based service start/stop and trial synthesis.
3. Run `scripts/check_tts_server.py` before scripted TTS experiments.
4. Add audio playback through a controlled output adapter only after WAV generation remains stable.
5. Wire TTS into an adapter factory and preflight path before touching real calls.

Current offline-cache decisions:

- First version is a testable skeleton, not a real production batch job.
- Regex is the default local intent routing strategy.
- Weather is a provider abstraction with a static placeholder.
- `cache/`, generated audio, private schedules, `.idea/`, and `*.iml` must stay out of Git.

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
