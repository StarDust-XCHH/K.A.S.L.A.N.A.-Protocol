# K.A.S.L.A.N.A. Testable Features

This file lists the small local features that are currently safe to test.
Unless noted otherwise, these commands do not open WeChat, do not place calls,
and do not play audio to an external sound card.

Run commands from the repository root:

```powershell
cd "E:\K.A.S.L.A.N.A. Protocol"
```

## Project Checks

### Config Smoke Test

Purpose: verify the example YAML config can be loaded.

```powershell
conda run -n kaslana-protocol python -m kaslana.main --config config/config.example.yaml --check-config
```

Expected result: prints the project name and configured contact alias.

Safety: no WeChat, no hardware, no audio playback.

### Unit Tests And Lint

Purpose: verify pure Python behavior and style.

```powershell
conda run -n kaslana-protocol python -m pytest
conda run -n kaslana-protocol python -m ruff check .
git diff --check
```

Expected result: tests pass, ruff passes, and Git reports no whitespace errors.

Safety: no WeChat, no calls, no audio playback.

## Environment And GPU

### Create Or Update The Conda Environment

Purpose: create the project environment with GPU PyTorch support.

```powershell
.\scripts\setup_kaslana_conda_env.ps1
```

Expected result: creates or updates `kaslana-protocol`, installs project dependencies,
and generates local-only `.env` / `config/config.yaml` files if missing.

Safety: changes only local environment and local ignored config files.

### Check NVIDIA GPU Detection

Purpose: verify PyTorch can see the RTX 4060 Laptop GPU.

```powershell
conda run -n kaslana-protocol python scripts\check_gpu.py
```

Expected result: `torch.cuda.is_available()` is `True` and the GPU name is printed.

Safety: no WeChat, no audio playback.

## Offline Cache Skeleton

### Run Nightly Preprocess Skeleton

Purpose: exercise the offline prefetch/cache command shape.

```powershell
conda run -n kaslana-protocol python scripts\run_nightly_preprocess.py --config config/config.example.yaml
```

Expected result: command loads configuration and exits conservatively because real
adapter factory wiring is not finished.

Safety: no WeChat, no calls, no hardware automation.

## TTS And GSVI

The current local GSVI endpoint is:

```text
http://127.0.0.1:5100
```

Port `5000` is not used because this machine has a local proxy process that can
bind it.

### List Kiana Model Emotions

Purpose: inspect emotion/reference keys from the local `infer_config.json`.

```powershell
conda run -n kaslana-protocol python scripts\try_gpt_sovits_tts.py --list-emotions
```

Expected result: prints `default` and other available emotion names.

Safety: reads local model metadata only; no service call and no audio playback.

### Start The Reusable GSVI Server

Purpose: start the local GSVI backend using the ignored prepack runtime.

```powershell
.\scripts\start_gsvi_tts_server.ps1
```

Expected result: `http://127.0.0.1:5100` becomes reachable.

Safety: binds only to `127.0.0.1`; no WeChat and no external audio playback.

### Check The GSVI Server

Purpose: verify `/character_list` and model availability.

```powershell
conda run -n kaslana-protocol python scripts\check_tts_server.py
```

Expected result: prints available characters and emotions, including `琪亚娜E7`.

Safety: no audio generation unless `--synthesize` is passed.

### Generate One Test WAV

Purpose: synthesize a short sentence and save a WAV under ignored diagnostics.

```powershell
conda run -n kaslana-protocol python scripts\try_gpt_sovits_tts.py --api-style gsvi --character "琪亚娜E7" --text "早安，该起床啦。"
```

Expected result: writes `diagnostics\tts\kiana_test.wav`.

Safety: saves a local WAV only; does not play through an external sound card.

### Open The Browser TTS Control Panel

Purpose: manage the GSVI service and test voices from a local browser page.

```powershell
cd "E:\K.A.S.L.A.N.A. Protocol"
.\scripts\start_tts_control_panel.ps1
```

Expected result: opens `http://127.0.0.1:8765`.

In the page, you can:

- start or stop the GSVI service;
- choose character and emotion;
- choose `auto`, `zh`, `en`, or `ja`;
- adjust `speed`, `top_k`, `top_p`, and `temperature`;
- generate and play a local WAV in the browser;
- generate Kiana-style text through Tongyi `qwen-flash` by default (server-side key only);
- auto-fill the TTS text box after generation and view LLM `elapsed_ms` / `char_count` / `usage`;
- view **TTS 链路** after synthesis: `elapsed_ms`, audio duration, RTF, bytes.

Safety: control panel binds only to `127.0.0.1`; generated audio is saved under
ignored `diagnostics\tts\control_panel\`.

### Tongyi Text Generation (Optional)

Purpose: verify DashScope text generation (default `qwen-flash`, short tier) for realtime dialogue + TTS timing tests.

```powershell
$env:TONGYI_API_KEY = "your-dashscope-key"
.\scripts\start_tts_control_panel.ps1
```

In the browser panel:

1. Confirm the `llm ready` badge and model label (e.g. `qwen-flash`).
2. Enter a topic (for example `早晨叫醒我但语气活泼一点`).
3. Keep length tier `short` for dialogue latency tests, or choose `long` with `KASLANA_TONGYI_MODEL=qwen-long` for stress tests.
4. Click **生成长文**; confirm text auto-fills the TTS box and LLM metadata shows elapsed time.
5. Click **生成音频**; confirm **TTS 链路** shows synthesis elapsed_ms and RTF.
5. Click **生成音频** manually to measure TTS synthesis separately.

API smoke test without the browser:

```powershell
conda run -n kaslana-protocol python -m pytest tests/unit/test_tongyi_chat.py -q
```

Expected result: unit tests pass with mocked HTTP; real API calls are manual only. No extra SDK install required.

Safety: the API key stays in `.env` / your shell session and is never sent to the browser.

### Stop The GSVI Server

Purpose: close the project-managed GSVI backend safely.

```powershell
.\scripts\stop_gsvi_tts_server.ps1
```

Expected result: stops only the PID recorded by this project and belonging to the
local GSVI root. If the port belongs to another process, it refuses to stop it.

Safety: avoids killing unrelated processes.

## Script Layout

Current `scripts/` entries remain at the top level because they are user-facing
commands documented across README and docs. The practical grouping is:

- Environment: `setup_kaslana_conda_env.ps1`, `check_gpu.py`
- Hardware placeholders: `check_devices.py`, `list_audio_devices.py`
- Offline cache: `run_nightly_preprocess.py`
- TTS CLI and service: `try_gpt_sovits_tts.py`, `check_tts_server.py`,
  `start_gsvi_tts_server.ps1`, `stop_gsvi_tts_server.ps1`
- TTS browser panel: `tts_control_panel.py`, `start_tts_control_panel.ps1`
- Future call entrypoint placeholder: `run_morning_call.py`

If the command count grows further, prefer extracting shared helper logic into a
new `scripts/lib/` package before moving public command entrypoints.
