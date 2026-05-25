# 01. 架构说明

## 架构目标

K.A.S.L.A.N.A. Protocol 的架构目标是：把微信 UI 自动化、物理音频链路、AI 模型链路和调度状态机完全解耦，让每个模块可以被单独实现、单独测试、单独替换。

核心原则：

- `core/` 只负责调度和状态，不认识具体 SDK。
- `ports/` 定义抽象能力。
- `adapters/` 连接真实第三方库和外设。
- `config/` 决定运行时使用什么设备、坐标、模型和 prompt。
- `tests/` 先保护纯 Python 逻辑，再逐步加入集成验收。

## 总体依赖方向

```text
config  ---> adapter_factory ---> adapters ---> third-party SDKs / hardware
                         |
                         v
core ---> ports <--------+
 |
 v
domain
```

允许的依赖：

- `core` 可以依赖 `ports`、`domain`。
- `adapters` 可以依赖 `ports` 和第三方 SDK。
- `config` 可以被工厂、脚本、入口读取。
- `tests` 可以依赖任意项目模块。

禁止的依赖：

- `core` 不允许 import `uiautomator2`。
- `core` 不允许 import `sounddevice`。
- `core` 不允许 import OpenAI、GPT-SoVITS、Whisper、Silero SDK。
- `ports` 不允许依赖具体实现。
- `domain` 不允许依赖外设或模型 SDK。

## 目录职责

### `src/kaslana/core/`

职责：

- 状态定义。
- 事件定义。
- 状态流转校验。
- 异步生命周期调度。
- 定时任务骨架。

当前文件：

- `states.py`：`CallState` 和合法状态流转。
- `events.py`：`CallEvent` 和事件到状态的映射。
- `orchestrator.py`：异步调度器骨架。
- `scheduler.py`：早晨定时任务骨架。

开发建议：

- 任何新状态都必须先写测试，再改状态机。
- 调度器只根据 port 的返回值做决策，不关心返回值如何产生。
- 失败时优先进入 `HUNG_UP`，避免误拨和骚扰。

测试标准：

- 每条新增状态流转有单元测试。
- 非法事件必须抛出清晰错误。
- `Orchestrator` 通过 fake port 测试，不依赖真实设备。

### `src/kaslana/ports/`

职责：

- 规定核心层需要的外部能力。
- 约束 adapter 的输入输出。
- 为 fake、mock、真实实现提供统一契约。

当前 port：

- `AutomationPort`：唤醒手机、打开微信、拨打、等待接通、挂断。
- `AudioInputPort`：启动输入流、异步产生音频块、停止。
- `AudioOutputPort`：播放文件、播放 PCM、停止。
- `VadPort`：判断语音、收集一句话。
- `AsrPort`：语音转文字。
- `LlmPort`：对话上下文生成回复。
- `TtsPort`：文本合成语音。

后续建议新增：

- `HardwareProbePort`：ADB、音频、模型服务健康检查。
- `CalibrationPort`：音频回环和 VAD 阈值校准。
- `PromptPort` 或 `PromptManager`：加载 persona 和场景 prompt。

接口设计标准：

- 方法名描述业务能力，不暴露 SDK 术语。
- 异步 I/O 用 `async def`。
- 流式能力预留 `AsyncIterator`。
- 返回结构使用 dataclass。
- 不返回第三方库对象。

### `src/kaslana/adapters/`

职责：

- 把真实世界能力接到 port 上。
- 封装所有第三方 SDK、HTTP API、硬件细节。

当前 adapter 占位：

- `Uiautomator2WechatAutomation`
- `SoundDeviceAudioInput`
- `SoundDeviceAudioOutput`
- `SileroVad`
- `FasterWhisperAsr`
- `OpenAICompatibleLlm`
- `GptSovitsTts`

开发建议：

- 每个 adapter 自己处理 SDK 初始化和资源释放。
- 每个 adapter 先实现健康检查或最小方法，再接入 orchestrator。
- adapter 报错要转换成项目内可理解的异常或失败原因。

测试标准：

- 占位 adapter 必须满足 port contract。
- 真实 adapter 必须有 fake SDK 或 fake server 测试。
- 硬件 adapter 的真机测试必须标记为 integration/manual。

### `src/kaslana/config/`

职责：

- 加载 `.env`。
- 加载 YAML。
- 解析成类型化配置。
- 拒绝明显缺失或错误的配置。

配置原则：

- 坐标不可写死。
- 设备 ID 不可写死。
- 联系人 alias 不可写死。
- API Key 不可写死。
- prompt 路径不可写死。
- 模型地址不可写死。

后续建议：

- 增加 `runtime_profile`，例如 `dry_run`、`hardware_test`、`real_call`。
- 增加 `automation.allow_real_call`。
- 增加 `preflight.required_checks`。
- 增加 `audio.calibration` 阈值。

测试标准：

- 示例配置加载成功。
- 缺失字段失败。
- 非法类型失败。
- 敏感信息不出现在示例配置中。

### `src/kaslana/domain/`

职责：

- 保存纯业务对象。
- 不依赖外设和 SDK。

当前对象：

- `CallSession`
- `StateTransition`
- `ConversationContext`
- `ConversationMessage`

后续建议：

- 增加 `RunReport`，用于保存一次运行的汇总。
- 增加 `FailureReason` 枚举，减少自由文本错误。
- 增加 `HealthReport`，用于 preflight 输出。

测试标准：

- 对象初始化稳定。
- 状态变化可追踪。
- 时间字段有 UTC 语义。
- 不泄露敏感配置。

### `scripts/`

职责：

- 提供人工执行的诊断和运行入口。
- 不承载核心业务逻辑。

当前脚本：

- `check_devices.py`
- `list_audio_devices.py`
- `run_morning_call.py`

后续建议：

- `calibrate_audio.py`
- `capture_ui_snapshot.py`
- `preflight.py`
- `dry_run_call_flow.py`

测试标准：

- 脚本可以导入项目包。
- 无硬件时给出清晰提示。
- 不在默认情况下触发真实拨号。

## 状态机设计

状态：

```text
IDLE
DIALING
WAITING
GREETING
LISTENING
THINKING
SPEAKING
HUNG_UP
```

正常路径：

```text
IDLE
  -> DIALING
  -> WAITING
  -> GREETING
  -> LISTENING
  -> THINKING
  -> SPEAKING
  -> LISTENING
  -> HUNG_UP
```

失败路径：

- 拨号失败：`DIALING -> HUNG_UP`
- 等待超时：`WAITING -> HUNG_UP`
- 无语音：`LISTENING -> HUNG_UP`
- ASR 空文本：`THINKING -> HUNG_UP`
- LLM 空回复：`THINKING -> HUNG_UP`
- TTS 失败：`SPEAKING -> HUNG_UP`
- 任意未捕获异常：进入 `HUNG_UP`

设计建议：

- 不要把状态机扩展成万能流程引擎。
- 每个状态只表达通话生命周期，不表达 adapter 内部细节。
- adapter 内部进度可以用日志或诊断对象记录。

## 配置驱动边界

运行时必须从配置读取：

- ADB 设备 ID。
- 微信联系人 alias。
- UI 坐标兜底值。
- 音频输入/输出设备。
- 采样率、通道数、chunk 时长。
- VAD 阈值。
- ASR 模型名。
- LLM base URL、model、API Key 环境变量名。
- TTS endpoint、speaker、timeout。
- persona prompt 路径。

不应写进配置：

- 真实 API Key 明文。
- 私密音色权重路径，如果它会被提交。
- 微信登录凭证。
- 任何微信内部协议字段。

## 日志和诊断建议

建议后续日志分层：

- `runtime.log`：一次运行的高层事件。
- `state.log`：状态机流转。
- `hardware.log`：ADB、声卡、音频诊断。
- `automation.log`：UI 自动化步骤。
- `ai.log`：ASR、LLM、TTS 的耗时和失败原因。

不要记录：

- API Key。
- 完整联系人实名。
- 私密对话全文，除非用户明确开启调试模式。
- 微信账号敏感信息。

## 架构验收标准

任何新模块合入前必须满足：

- 核心层不直接依赖第三方 SDK。
- 新配置有示例值和测试。
- 新 port 有 fake 或 contract test。
- 新 adapter 不影响已有 fake 调度测试。
- 所有真实外设调用都有关闭和异常处理路径。
- `pytest` 和 `ruff` 通过。
