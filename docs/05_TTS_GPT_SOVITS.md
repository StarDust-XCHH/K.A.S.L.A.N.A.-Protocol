# 05. GPT-SoVITS TTS 模块

## 模块目标

TTS 模块负责把 LLM 生成的文本转换成可播放的语音，并通过 PC 外置声卡输出到 A 端手机麦克风输入。

默认路线：

- 本地 GPT-SoVITS 服务。
- 先零样本或参考音频方式验证链路。
- 不把权重、参考音频、生成音频提交到仓库。
- 后续再优化音色质量和延迟。

## 当前代码位置

- TTS port：`src/kaslana/ports/tts.py`
- GPT-SoVITS adapter 占位：`src/kaslana/adapters/tts/gpt_sovits.py`
- TTS 配置：`config/config.example.yaml`

当前配置：

```yaml
tts:
  provider: "gpt_sovits"
  endpoint: "http://127.0.0.1:9880"
  speaker: "kiana"
  timeout_s: 60.0
```

## 输入与输出

输入：

- 文本。
- endpoint。
- speaker 或参考音频配置。
- 超时时间。

输出：

- `TtsAudio.audio`
- `TtsAudio.sample_rate`
- `TtsAudio.channels`
- `TtsAudio.format`

TTS adapter 不负责：

- 播放音频。
- 控制微信。
- 判断用户是否说话。

## 待实现小功能

### 1. GPT-SoVITS 服务健康检查

开发建议：

- 增加健康检查方法或独立 preflight 检查。
- 检查本地 endpoint 是否可连接。
- 检查模型是否加载。
- 检查一次极短文本合成是否成功。

测试标准：

- 服务未启动时返回清晰错误。
- endpoint 错误时失败不重试过久。
- 健康检查默认 2 秒到 5 秒内结束。
- 不在健康检查中生成大量音频。

### 2. 文本预处理

开发建议：

- 去除 Markdown。
- 去除过长空白。
- 限制文本长度。
- 替换不适合语音朗读的符号。
- 保留中文语气，但不要让模型输出复杂列表。

测试标准：

- 空文本拒绝合成。
- 超长文本会截断或失败。
- Markdown 列表不会原样读出。
- 文本预处理不改变主要语义。

### 3. 普通合成

开发建议：

- 第一版实现 `synthesize(text)`。
- 使用 HTTP client 调用本地 GPT-SoVITS。
- 将返回音频统一转成 `TtsAudio`。
- 如果返回 WAV，可在 adapter 内解析采样率和通道数。

测试标准：

- fake HTTP server 覆盖成功响应。
- 404、500、超时、空 body 都有测试。
- 返回音频非空。
- 音频采样率和通道数正确。

### 4. 音频格式统一

开发建议：

- orchestrator 只接收 `TtsAudio`。
- 播放端负责播放 PCM 或 WAV。
- 如果 TTS 返回 WAV，而 `AudioOutputPort.play_pcm()` 只接收 PCM，应在 adapter 或 audio utility 中转换。

测试标准：

- WAV header 可正确解析。
- PCM bytes 非空。
- 格式错误时不播放。
- 采样率不匹配时给出转换或失败提示。

### 5. 缓存

开发建议：

- 对固定问候语启用文件缓存。
- 缓存 key 可基于文本、speaker、模型配置 hash。
- 缓存目录应加入 `.gitignore`。

测试标准：

- 相同文本第二次命中缓存。
- 配置变化后缓存失效。
- 缓存损坏时自动重新合成或失败清晰。

### 6. 流式合成预留

开发建议：

- 保留 `stream_synthesize()`。
- 第一版可以不实现。
- 后续当 GPT-SoVITS 服务支持流式或分句生成时再接。

测试标准：

- 未实现时抛出明确 `NotImplementedError`。
- orchestrator 默认不依赖流式能力。

## 音色资源管理

原则：

- 不提交权重。
- 不提交私密参考音频。
- 不提交生成的真实通话音频。
- 文档只写路径约定和配置项，不写私人资源名称。

建议目录：

```text
local_assets/
  tts/
    refs/
    models/
    cache/
```

并加入 `.gitignore`。

## 常见失败模式

- GPT-SoVITS 服务未启动。
- endpoint 写错。
- 模型未加载。
- 参考音频路径失效。
- 返回音频格式与播放端不匹配。
- 文本过长导致生成太慢。
- 显存不足。
- 合成音量过大导致通话端削波。

## 人工验收步骤

1. 启动 GPT-SoVITS 本地服务。
2. 执行健康检查。
3. 合成短句：“早安，该起床啦。”
4. 保存临时音频到 ignored 目录。
5. 本机播放确认可听。
6. 通过外置声卡输出到 A 端手机。
7. B 端听音，确认音量合适。
8. 检查是否削波或过小。
9. 记录 endpoint、模型、参考音频配置和耗时。

## 验收门槛

接入完整调度前必须满足：

- 服务健康检查通过。
- 短句合成成功。
- 音频可播放。
- 输出到 B 端可听清。
- 失败时 orchestrator 不播放空音频。
