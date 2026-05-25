# 04. 音频、VAD 与 ASR 模块

## 模块目标

音频链路负责让 AI 能听见 B 端用户，也能把 AI 回复送入 A 端手机麦克风。

链路：

```text
B 端说话
  -> 微信通话
  -> A 端耳机输出
  -> PC 外置声卡输入
  -> VAD
  -> ASR
  -> LLM
  -> TTS
  -> PC 外置声卡输出
  -> A 端麦克风输入
  -> 微信通话
  -> B 端听见
```

本模块覆盖：

- 音频输入。
- 音频输出。
- 物理环回校准。
- VAD 检测。
- 语音片段切分。
- Faster-Whisper ASR 接入规划。

## 当前代码位置

- 音频 port：`src/kaslana/ports/audio.py`
- VAD port：`src/kaslana/ports/vad.py`
- ASR port：`src/kaslana/ports/asr.py`
- 音频 adapter 占位：`src/kaslana/adapters/audio/sounddevice_loopback.py`
- VAD adapter 占位：`src/kaslana/adapters/vad/silero_vad.py`
- ASR adapter 占位：`src/kaslana/adapters/asr/faster_whisper.py`
- 音频配置：`config/config.example.yaml`

## 输入与输出

音频输入：

- 输入设备名或 index。
- 采样率。
- 通道数。
- chunk 时长。

音频输出：

- 输出设备名或 index。
- PCM 字节。
- WAV 文件路径。
- 采样率和通道数。

VAD 输入：

- `AudioChunk` 异步流。

VAD 输出：

- `SpeechSegment`
- 或超时返回 `None`

ASR 输入：

- `SpeechSegment`

ASR 输出：

- `Transcript`

## 采样率策略

推荐默认：

- 内部语音识别采样率：16kHz。
- 外置声卡可用采样率：优先 48kHz 或设备默认。
- 必要时在 adapter 内重采样。

开发建议：

- 第一版可以要求配置采样率与设备一致。
- 后续再加入重采样工具。
- 不要让 orchestrator 处理采样率转换。

测试标准：

- `AudioChunk.sample_rate` 与配置一致。
- `TtsAudio.sample_rate` 可被输出端播放。
- ASR 输入必须是模型可接受格式。

## 待实现小功能

### 1. `sounddevice` 输入流

开发建议：

- 使用 `sounddevice.InputStream`。
- 将 callback 数据放入 `asyncio.Queue`。
- `stream_chunks()` 返回 `AsyncIterator[AudioChunk]`。
- `stop()` 必须关闭 stream。

测试标准：

- fake stream 可单元测试队列逻辑。
- 无设备时错误清晰。
- 输入设备不支持目标采样率时失败。
- Ctrl+C 或异常时 stream 关闭。

### 2. `sounddevice` 输出流

开发建议：

- 第一版支持播放 WAV 文件。
- 第二步支持播放 PCM bytes。
- 输出音量从低开始。
- 播放前检查音频非空。

测试标准：

- fake output 可验证播放调用。
- 空音频拒绝播放。
- 不支持采样率时失败清晰。
- 播放结束后资源释放。

### 3. 音频校准脚本

开发建议：

- 新增 `scripts/calibrate_audio.py`。
- 播放 1kHz 正弦波。
- 同时录制输入。
- 输出峰值、RMS、底噪、削波比例。
- 可选保存 WAV 到 ignored 目录。

测试标准：

- 静音输入 10 秒底噪目标低于 `-50 dBFS`。
- 测试音峰值在 `-12 dBFS` 到 `-3 dBFS`。
- 削波比例接近 0。
- 检测到削波时建议降低输出音量。

### 4. Silero VAD

开发建议：

- VAD adapter 不负责录音设备，只消费 `AudioChunk`。
- 根据 `threshold`、`min_speech_ms`、`silence_ms`、`max_utterance_s` 切分一句话。
- 超过最大时长强制截断。
- 长时间无语音返回 `None`。

测试标准：

- 使用离线 WAV fixture 测试有声/无声。
- 短噪声不应被识别为完整发言。
- 长句达到 `max_utterance_s` 后截断。
- 静音超时返回 `None`。

### 5. Faster-Whisper ASR

开发建议：

- adapter 接收 `SpeechSegment`。
- 将 PCM 转成模型需要的数组或临时 WAV。
- 第一版使用非流式 `transcribe()`。
- 后续再考虑 streaming ASR。

测试标准：

- fake ASR 单元测试调度逻辑。
- 离线中文短音频可返回非空文本。
- 静音音频返回空文本或低置信度。
- ASR 报错时 orchestrator 进入 `HUNG_UP`。

### 6. 通话音频采样验收

开发建议：

- 在 A/B 手机建立真实通话后录制 B 端说话。
- 保存短样本到 ignored 目录。
- 检查波形和 VAD。
- 不提交真实私人语音。

测试标准：

- B 端正常音量说话，PC 输入清楚。
- VAD 能在 1 秒内识别开始。
- 句尾静音后能结束 segment。
- 无人说话时不触发。

## 常见失败模式

- 录到的是 PC 内置麦克风而不是外置声卡。
- 播放到了电脑扬声器而不是 A 端手机麦克风链路。
- 输出音量过大导致手机麦克风输入削波。
- Windows 自动降噪影响 VAD。
- 线材接错方向。
- 声卡输入输出采样率不一致。
- 电话通话压缩导致 VAD 参数需要调整。
- ASR 模型对远端通话音质识别不稳。

## 人工验收步骤

1. 枚举音频设备。
2. 在配置中指定输入输出设备。
3. 进行静音底噪测试。
4. 进行 1kHz 回环测试。
5. 让 B 端手机播放或说一句固定短语。
6. 录制 PC 输入。
7. 用 VAD 切分。
8. 用 ASR 识别。
9. 人工核对识别文本。
10. 记录音量、设备名、采样率、阈值。

## 验收门槛

接入完整调度前必须满足：

- 输入输出设备匹配配置。
- 底噪和削波达标。
- VAD 在真实通话样本上可用。
- ASR 对固定中文短句有稳定结果。
- 音频流异常时能关闭资源。
