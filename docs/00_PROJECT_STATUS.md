# 00. 当前项目状态

## 状态摘要

K.A.S.L.A.N.A. Protocol 当前已经完成第一阶段工程骨架。这个阶段的目标是把项目切成可维护的模块，而不是打通真实硬件闭环。

当前代码可以被测试和 lint，但真实功能仍然是占位：

- 可以加载示例配置。
- 可以运行状态机和 fake 调度测试。
- 可以确认抽象 port 和占位 adapter 的继承关系。
- 可以通过 `AI_TASK_TEMPLATE.md` 给后续 AI 助手交接任务。
- 可以通过 `docs/10_DEVELOPMENT_LOG.md` 记录每轮开发流水账。
- 可以用 fake 测试验证离线预瞄缓存命中和未命中路径。
- 可以启动 ignored 的本地 GSVI TTS 服务，并通过 HTTP 健康检查和短句合成生成 WAV。
- 可以打开本地浏览器调试面板，启动/关闭 GSVI、选择 emotion、输入测试语句并网页试听 WAV。
- 可以在同一面板通过通义 `qwen-flash`（默认）生成《崩坏三》琪亚娜风格文本（`short` 档位约 80–150 字），非流式返回 LLM 耗时后自动填入 TTS 文本框；合成后显示 TTS `elapsed_ms`、音频时长与 RTF。
- 长文压测可设 `KASLANA_TONGYI_MODEL=qwen-long`。
- 可以用 `kaslana-protocol` 专属 conda 环境模板安装项目核心依赖和 RTX 4060 Laptop GPU 的 CUDA PyTorch。
- 不能真实打开微信。
- 不能真实拨打语音通话。
- 不能真实录音或播放到外置声卡。
- 不能把 GPT-SoVITS 接入完整通话链路；orchestrator 仍未接 LLM；Silero、Faster-Whisper 仍未实现。
- 通义长文生成仅用于本地控制面板调试，不是完整通话链路的一部分。
- 不能真实执行完整夜间批处理；当前只有安全骨架。

## 当前完成内容

### 工程元信息

位置：

- `pyproject.toml`
- `.gitignore`
- `.gitattributes`
- `README.md`

已完成：

- Python 包名：`kaslana-protocol`
- Python 版本要求：`>=3.11`
- 构建后端：`setuptools`
- 测试依赖：`pytest`、`pytest-asyncio`
- Lint 工具：`ruff`
- 配置依赖：`PyYAML`
- 命令入口：`kaslana = kaslana.main:main`
- 专属 conda 环境模板：`environment.yml`
- 环境创建脚本：`scripts/setup_kaslana_conda_env.ps1`
- GPU 检查脚本：`scripts/check_gpu.py`
- GSVI 启动脚本：`scripts/start_gsvi_tts_server.ps1`
- GSVI 关闭脚本：`scripts/stop_gsvi_tts_server.ps1`
- GSVI 健康检查脚本：`scripts/check_tts_server.py`
- TTS 试音控制台：`scripts/tts_control_panel.py`
- TTS 控制台启动脚本：`scripts/start_tts_control_panel.ps1`

开发建议：

- 后续新增运行依赖时，不要把所有可选硬件依赖都塞进默认依赖。
- 建议后续拆分 extras，例如 `audio`、`automation`、`ai`、`dev`。
- 外设依赖如 `sounddevice`、`uiautomator2`、`torch`、`faster-whisper` 应该按模块引入。

测试标准：

- `python -m pytest` 必须通过。
- `python -m ruff check .` 必须通过。
- `python -m kaslana.main --config config/config.example.yaml --check-config` 必须能加载示例配置。

### 配置系统

位置：

- `config/config.example.yaml`
- `config/prompts/kiana.yaml`
- `src/kaslana/config/schema.py`
- `src/kaslana/config/loader.py`

已完成：

- YAML 配置加载。
- `.env` 简单加载。
- dataclass 类型化配置。
- 必填字段基础校验。
- 示例配置覆盖 project、scheduler、automation、audio、vad、asr、llm、tts、prompts。
- 示例配置新增 offline_cache、ingestion、intent_matching、batch_preprocess，默认关闭。

尚未完成：

- 更细的数值范围校验。
- provider 枚举校验。
- 真实密钥存在性检查。
- 设备名和配置值的实际匹配检查。
- 多环境配置，例如 `dev`、`hardware_test`、`production`。

开发建议：

- 短期继续保留轻依赖方案：标准库 + `PyYAML` + dataclass。
- 当配置变复杂时再评估是否迁移到 `pydantic-settings`。
- 所有真实设备 ID、联系人 alias、API Key、模型路径都只能出现在未提交的 `config/config.yaml` 或 `.env`。

测试标准：

- 示例配置必须能加载。
- 缺少一级配置块必须抛出 `ConfigError`。
- 坐标必须解析成 `Point`。
- 音频路径必须解析成 `Path`。

### 抽象接口

位置：

- `src/kaslana/ports/automation.py`
- `src/kaslana/ports/audio.py`
- `src/kaslana/ports/vad.py`
- `src/kaslana/ports/asr.py`
- `src/kaslana/ports/llm.py`
- `src/kaslana/ports/tts.py`

已完成：

- `AutomationPort`
- `AudioInputPort`
- `AudioOutputPort`
- `VadPort`
- `AsrPort`
- `LlmPort`
- `TtsPort`

设计意图：

- 核心调度层只依赖 port。
- 真实 SDK 只能出现在 adapter。
- port 描述能力，不描述具体实现方式。

尚未完成：

- 硬件健康检查 port。
- 校准 port。
- UI 诊断结构。
- 统一健康检查结果结构。
- adapter factory。

### 核心调度

位置：

- `src/kaslana/core/states.py`
- `src/kaslana/core/events.py`
- `src/kaslana/core/orchestrator.py`
- `src/kaslana/core/scheduler.py`
- `src/kaslana/domain/call_session.py`
- `src/kaslana/domain/conversation.py`

已完成：

- `CallState`
- `CallEvent`
- 合法状态流转校验。
- `CallSession` 记录状态变化。
- `ConversationContext` 保存对话上下文。
- `Orchestrator` fake 可测骨架。

当前状态流：

```text
IDLE -> DIALING -> WAITING -> GREETING -> LISTENING -> INTENT_MATCHING -> THINKING -> SPEAKING -> HUNG_UP
```

当前保守失败路径：

- 任意 active 状态收到 `TIMEOUT` 进入 `HUNG_UP`。
- 任意 active 状态收到 `FAILURE` 进入 `HUNG_UP`。
- `finally` 中尝试挂断和关闭音频流。

尚未完成：

- 多轮会话策略。
- 真实 preflight。
- 运行日志。
- 人工确认模式。
- 定时任务实装。

### 离线预瞄与缓存

位置：

- `src/kaslana/domain/offline_cache.py`
- `src/kaslana/ports/ingestion.py`
- `src/kaslana/ports/weather.py`
- `src/kaslana/ports/dialogue_cache.py`
- `src/kaslana/ports/intent_router.py`
- `src/kaslana/adapters/dialogue_cache/json_file_cache.py`
- `src/kaslana/adapters/intent_router/regex_router.py`
- `src/kaslana/core/offline_preprocessor.py`
- `scripts/run_nightly_preprocess.py`
- `docs/11_OFFLINE_RAG_PRECACHE.md`

已完成：

- 定义本地日程接入、天气 provider、对话缓存、意图路由 ports。
- 定义 `CachedDialogueMapping`、`DialogueBranch`、`IntentMatch` 等领域对象。
- 实现 JSON 文件缓存 adapter。
- 实现 Regex 意图路由 adapter。
- Orchestrator 支持缓存问候语和缓存分支优先播放。
- 缓存未命中时回落实时 LLM/TTS。
- `cache/`、`.idea/`、`*.iml` 已加入 `.gitignore`。

尚未完成：

- adapter factory 真实接线。
- 真实天气 API。
- 真实 LLM 结构化对话树生成。
- 真实 GPT-SoVITS 批量 WAV 渲染。
- 夜间定时任务实战运行。
- 缓存健康检查、过期策略和运行报告。

### 适配器占位

位置：

- `src/kaslana/adapters/automation/uiautomator2_wechat.py`
- `src/kaslana/adapters/audio/sounddevice_loopback.py`
- `src/kaslana/adapters/vad/silero_vad.py`
- `src/kaslana/adapters/asr/faster_whisper.py`
- `src/kaslana/adapters/llm/openai_compatible.py`
- `src/kaslana/adapters/tts/gpt_sovits.py`

已完成：

- 每个 adapter 类继承对应 port。
- 除 GPT-SoVITS TTS 外，每个方法明确 `NotImplementedError`。
- GPT-SoVITS TTS 已有最小 HTTP 合成实现，可读取 `infer_config.json` 并请求 official API 或 GSVI 风格本地 `/tts` 生成 WAV。
- 新增 `scripts/try_gpt_sovits_tts.py`，用于本地试音和列出可用 emotion/reference。
- 新增 `scripts/start_gsvi_tts_server.ps1`，用 ignored 的 GSVI 预打包 runtime 启动本机 loopback 服务。
- 新增 `scripts/check_tts_server.py`，检查 `/character_list` 并可选合成短句到 ignored 的 `diagnostics/tts/`。
- 新增 `scripts/tts_control_panel.py`，提供本地浏览器试音控制台，可启动/关闭 GSVI、选择 emotion、设置语言和高级参数、网页播放生成 WAV。

尚未完成：

- 微信、音频、VAD、ASR、LLM 的真实实现。
- GPT-SoVITS 的播放链路、缓存策略和 orchestrator/factory 接线。

开发建议：

- 每个 adapter 单独实现、单独测试、单独提交。
- 不要在实现一个 adapter 时顺手修改无关模块。

### 测试

位置：

- `tests/unit/test_config_loader.py`
- `tests/unit/test_states.py`
- `tests/unit/test_ports_contract.py`
- `tests/unit/test_orchestrator.py`

已完成：

- 配置加载测试。
- 状态流转测试。
- 占位 adapter 接口继承测试。
- fake port 驱动的 orchestrator 异步测试。
- 离线缓存 JSON adapter 和 Regex router 测试。
- Orchestrator 缓存命中和缓存 miss 测试。
- GPT-SoVITS infer_config 解析、HTTP payload、权重切换和文本清理测试。

尚未完成：

- 硬件集成测试。
- ADB 设备检测测试。
- 音频设备枚举测试。
- 微信 UI XML fixture 测试。
- TTS fake server 测试。
- LLM fake server 测试。
- OfflinePreprocessor fake LLM/TTS 批处理测试。

### AI 接力文档

位置：

- `AI_HANDOFF.md`
- `AI_TASK_TEMPLATE.md`
- `docs/10_DEVELOPMENT_LOG.md`

已完成：

- 后续 AI 助手的推荐阅读顺序。
- 可直接复制使用的通用任务提示语。
- 每轮任务完成后的落盘规则。
- 开发流水账模板和历史记录入口。

开发建议：

- 每轮实质开发后都更新 `docs/10_DEVELOPMENT_LOG.md`。
- 如果项目状态变化，更新 `AI_HANDOFF.md` 和本文件。
- 如果某模块完成或调整路线，更新 `docs/09_ROADMAP.md` 和对应模块文档。

## 当前本机环境观察

截至本手册落盘时，本机观察结果：

- ADB 已存在：`D:\platform-tools-latest-windows\platform-tools\adb.exe`
- 当前 `adb devices` 未列出已连接设备。
- Python：3.12.4
- `sounddevice` 未安装。
- `pyaudio` 未安装。
- `uiautomator2` 未安装。
- CPU：Intel Core i9-13900H
- 内存：约 32GB
- GPU：NVIDIA GeForce RTX 4060 Laptop GPU，约 8GB 显存。
- 专属 conda 环境目标：`kaslana-protocol`，Python 3.11，PyTorch CUDA 12.8 wheel。

这些事实用于规划，不应该硬编码进代码。

## 当前 Git 状态

已完成首次提交：

```text
a72451b Initialize Kaslana architecture skeleton
```

后续文档落盘应单独提交：

```text
Document engineering handbook and AI handoff
```

AI 接力模板落盘应单独提交：

```text
Add AI task template and development log
```

## 下一个推荐开发主题

默认仍推荐先开发“硬件诊断与音频校准”，因为它最能暴露真实环境风险：

1. ADB 设备是否稳定。
2. 旧安卓手机是否能长期保持唤醒。
3. 外置声卡是否能稳定输入输出。
4. 物理环回是否有底噪、啸叫、削波。
5. VAD 是否能在真实通话音频中可靠判断语音。

如果下一轮继续离线缓存方向，推荐先做 adapter factory 和 OfflinePreprocessor fake LLM/TTS 测试，不要直接接真实天气或真实 TTS。
