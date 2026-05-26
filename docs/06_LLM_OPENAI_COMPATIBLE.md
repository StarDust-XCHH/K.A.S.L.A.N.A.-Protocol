# 06. OpenAI-Compatible LLM 模块

## 模块目标

LLM 模块负责把用户语音识别文本、对话上下文和琪亚娜 persona prompt 转换为适合电话语音播放的短回复。

默认路线：

- 云端 OpenAI-compatible API。
- 核心层只依赖 `LlmPort`。
- Prompt 从 YAML 加载。
- 回复要短、口语化、适合 TTS。

## 当前代码位置

- LLM port：`src/kaslana/ports/llm.py`
- OpenAI-compatible adapter 占位：`src/kaslana/adapters/llm/openai_compatible.py`
- DashScope / 通义 urllib 客户端：`src/kaslana/adapters/llm/tongyi_chat.py`
- Prompt 管理：`src/kaslana/core/prompt_manager.py`
- 控制面板长文服务：`src/kaslana/services/llm_generate.py`
- prompt 示例：`config/prompts/kiana.yaml`
- LLM 配置：`config/config.example.yaml`
- 本地调试面板：`scripts/tts_control_panel.py`

当前配置：

```yaml
llm:
  provider: "dashscope"
  base_url: "https://dashscope.aliyuncs.com/compatible-mode/v1"
  model: "qwen-flash"
  api_key_env: "TONGYI_API_KEY"
  timeout_s: 60.0
```

## 控制面板文本生成场景（已实现）

用途：

- 在本地浏览器面板中生成《崩坏三》琪亚娜·卡斯兰娜口吻文本（默认短句档位，用于实时链路测试）。
- 为后续 GPT-SoVITS 测时和流式联调准备素材。
- 浏览器只访问本机 `127.0.0.1` API，不直接调用 DashScope。

实现要点：

- 环境变量：`TONGYI_API_KEY`（优先）或 `DASHSCOPE_API_KEY`；`KASLANA_TONGYI_MODEL`；`KASLANA_TONGYI_BASE_URL`
- 默认模型：`qwen-flash`（短句实时测试）；长文压测可设 `KASLANA_TONGYI_MODEL=qwen-long`
- HTTP：`GET /api/tongyi/status`、`POST /api/generate-long-text`（非流式，返回 `elapsed_ms`、`char_count`、`usage`）
- 长度档位：`short`（默认，约 80–150 字）/ `medium` / `long` / `stress`
- Persona：`config/prompts/kiana.yaml`；外国专名（如 Kaslana）可提示直接用英文拼写以利 TTS

与电话短回复的区别：

- 电话 orchestrator 仍计划使用短回复约束。
- 控制面板 `short` 档位用于模拟早晨电话短句；长档位仍可用于 TTS 压测。

## 输入与输出

输入：

- system prompt。
- 对话 turns。
- model。
- base URL。
- API Key 环境变量名。
- timeout。

输出：

- `LlmResponse.text`
- `LlmResponse.model`
- `LlmResponse.usage`

LLM adapter 不负责：

- 录音。
- ASR。
- TTS。
- 微信控制。

## Prompt 设计原则

电话语音场景的回复必须：

- 简短。
- 自然。
- 不输出 Markdown。
- 不输出长列表。
- 不输出复杂代码。
- 不要求用户看屏幕。
- 不声称自己是真实人物。
- 不引导危险行为。

建议 persona 包含：

- 角色语气。
- 早晨叫醒场景。
- 回复长度。
- 安全边界。
- 失败兜底句。

## 待实现小功能

### 1. PromptManager

开发建议：

- 从 `config/prompts/kiana.yaml` 加载 persona。
- 生成 system prompt。
- 将运行场景注入，例如“早晨叫醒电话”。
- 不把 API Key 或设备信息注入 prompt。

测试标准：

- prompt YAML 能加载。
- 缺少 persona 字段失败清晰。
- system prompt 非空。
- 不包含敏感环境变量值。

### 2. OpenAI-compatible 客户端

开发建议：

- 从 `base_url`、`model`、`api_key_env` 初始化。
- API Key 只从环境变量读取。
- adapter 内处理 HTTP 或 SDK 细节。
- 返回统一 `LlmResponse`。

测试标准：

- 环境变量缺失时报错清晰。
- fake server 覆盖成功响应。
- 401、429、500、超时有测试。
- 空 choices 或空 text 失败。

### 3. 回复约束

开发建议：

- 在 prompt 中约束回复长度。
- adapter 或后处理层检查超长回复。
- 超长回复可截断，也可要求模型重试；第一版建议保守截断或失败。

测试标准：

- 回复为空时失败。
- 回复过长时被处理。
- Markdown 符号被过滤或避免生成。
- 输出适合 TTS。

### 4. 对话上下文管理

开发建议：

- `ConversationContext` 保存最近 turns。
- 电话叫醒不需要很长上下文。
- 第一版可限制 3 到 6 轮。

测试标准：

- 用户文本会加入上下文。
- 助手回复会加入上下文。
- 超过上限时旧消息被裁剪或不再传入。

### 5. 失败兜底

开发建议：

- 默认失败策略是保守退出。
- 不在通话中自动多次重试。
- 可以预留一个本地固定兜底句，但是否播放要由 orchestrator 策略控制。

测试标准：

- 网络超时进入失败路径。
- 429 不无限重试。
- LLM 失败不会调用 TTS 播放空文本。

## 常见失败模式

- API Key 未配置。
- base URL 错误。
- model 名不可用。
- 网络超时。
- 额度不足。
- 返回格式不兼容。
- 回复太长导致 TTS 慢。
- 回复包含 Markdown 或不适合语音的内容。

## 人工验收步骤

1. 配置 `.env` 中的 API Key。
2. 配置 `base_url` 和 `model`。
3. 加载 prompt。
4. 发送固定用户文本：“我醒了，但还想再睡五分钟。”
5. 检查回复是否短、自然、适合电话朗读。
6. 检查日志中没有 API Key。
7. 模拟超时和错误码。
8. 确认失败时调度器保守退出。

## 验收门槛

接入完整调度前必须满足：

- PromptManager 测试通过。
- fake server 测试覆盖主要错误。
- 真实 API 健康检查可选通过。
- 回复长度可控。
- 敏感信息不进入日志。
