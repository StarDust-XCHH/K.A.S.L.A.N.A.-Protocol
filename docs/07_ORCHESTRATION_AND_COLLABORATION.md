# 07. 总调度与协同开发

## 模块目标

协同模块负责把硬件、微信自动化、音频、VAD、ASR、LLM、TTS 组合成一个可控、可测试、可诊断的生命周期。

核心目标：

- 保持核心调度层干净。
- 通过依赖注入连接 adapter。
- 通过配置选择运行模式。
- 通过日志和 preflight 降低真实运行风险。
- 失败时保守退出。

## 当前代码位置

- 调度器：`src/kaslana/core/orchestrator.py`
- 状态机：`src/kaslana/core/states.py`
- 事件：`src/kaslana/core/events.py`
- 会话对象：`src/kaslana/domain/call_session.py`
- 对话对象：`src/kaslana/domain/conversation.py`
- 配置：`src/kaslana/config/`
- CLI 入口：`src/kaslana/main.py`

## 状态生命周期

当前主路径：

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

调度阶段职责：

- `DIALING`：调用自动化模块拨号。
- `WAITING`：等待接通。
- `GREETING`：播放预设问候。
- `LISTENING`：采集用户语音。
- `THINKING`：ASR + LLM。
- `SPEAKING`：TTS + 播放。
- `HUNG_UP`：挂断和释放资源。

## 依赖注入

当前 `OrchestratorDependencies`：

- `automation`
- `audio_input`
- `audio_output`
- `vad`
- `asr`
- `llm`
- `tts`

开发建议：

- 后续新增 `adapter_factory`，从配置创建这些依赖。
- factory 可以 import 具体 adapter。
- orchestrator 仍然不 import 具体 adapter。
- fake dependencies 继续用于单元测试。

测试标准：

- factory 可以在 dry-run 模式创建 fake adapter。
- 缺少 provider 时失败清晰。
- provider 不支持时失败清晰。
- orchestrator 单元测试不需要真实配置。

## 运行模式

建议后续增加配置项：

```yaml
runtime:
  profile: "dry_run"
  allow_real_call: false
  save_diagnostics: true
```

推荐模式：

- `dry_run`：只走 fake 或不危险步骤。
- `hardware_test`：允许 ADB、声卡、截图，不允许拨号。
- `wechat_test`：允许搜索联系人，拨号前停止。
- `real_call_test`：允许短拨号，人工在场。
- `production`：定时任务运行，必须通过 preflight。

测试标准：

- 默认配置必须是安全模式。
- 真实拨号必须显式开启。
- 模式切换有测试。

## Preflight

preflight 是真实运行前的安全检查。

建议检查：

- 配置文件存在。
- `.env` 中存在 LLM API Key。
- ADB 可用。
- 目标设备在线。
- 声卡输入输出存在。
- GPT-SoVITS 服务可用。
- LLM endpoint 可用。
- 问候音频存在。
- 真实拨号开关状态明确。

输出建议：

```text
K.A.S.L.A.N.A. Preflight
ADB: OK
Audio input: OK
Audio output: OK
TTS: OK
LLM: OK
Real call allowed: false
```

测试标准：

- 每个检查项可单独 fake。
- 任一必要项失败时不进入真实拨号。
- 输出不包含 API Key。

## 日志策略

建议目录：

```text
logs/
  runtime/
  diagnostics/
  ui_snapshots/
  audio_samples/
```

这些目录应被 `.gitignore` 忽略。

日志级别：

- INFO：状态变化、模块开始结束。
- WARNING：可恢复异常、超时、降级。
- ERROR：运行失败。
- DEBUG：仅人工调试时保存详细 XML、音频诊断。

不要记录：

- API Key。
- 微信账号敏感信息。
- 完整私人对话。
- 私密语音样本。

## 失败策略

默认选择：保守退出。

规则：

- 拨号失败：挂断，结束。
- 等待接通超时：挂断，结束。
- VAD 无语音：挂断，结束。
- ASR 空文本：挂断，结束。
- LLM 失败：挂断，结束。
- TTS 失败：挂断，结束。
- 任何未捕获异常：尝试挂断和释放资源。

不做：

- 不自动反复拨号。
- 不在联系人不确定时继续。
- 不在设备状态不明时点击危险按钮。

## 协同开发规范

每次开发一个模块：

1. 先读对应 docs。
2. 先写或更新测试。
3. 实现最小功能。
4. 运行验证。
5. 小步提交。

推荐提交粒度：

- `Add ADB hardware probe`
- `Add sounddevice audio enumeration`
- `Implement WeChat UI snapshot capture`
- `Add GPT-SoVITS health check`
- `Add OpenAI-compatible LLM adapter`

## 常见协同失败模式

- 在 core 中直接 import SDK。
- 为了赶进度跳过 fake 测试。
- 真实拨号开关默认打开。
- 配置写死在 adapter 中。
- 日志泄露 API Key。
- adapter 异常没有转换，导致资源未释放。
- 一次提交改太多模块。

## 人工验收步骤

1. 跑 `python -m pytest`。
2. 跑 `python -m ruff check .`。
3. 跑配置检查。
4. 跑 preflight。
5. 检查真实拨号开关。
6. 人工确认设备连接。
7. 只运行当前阶段允许的功能。
8. 保存诊断报告。
9. 提交 Git。

## 验收门槛

完整协同前必须满足：

- adapter factory 存在。
- preflight 存在。
- 所有核心 fake 测试通过。
- 所有真实模块有单独手工验收记录。
- 失败路径可以挂断和释放资源。
