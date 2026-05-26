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
- GPT-SoVITS HTTP adapter：`src/kaslana/adapters/tts/gpt_sovits.py`
- 本地试音脚本：`scripts/try_gpt_sovits_tts.py`
- 本地 GSVI 启动脚本：`scripts/start_gsvi_tts_server.ps1`
- 本地 GSVI 关闭脚本：`scripts/stop_gsvi_tts_server.ps1`
- 本地 GSVI 健康检查脚本：`scripts/check_tts_server.py`
- 本地浏览器试音控制台：`scripts/tts_control_panel.py`
- TTS 配置：`config/config.example.yaml`

当前配置：

```yaml
tts:
  provider: "gpt_sovits"
  endpoint: "http://127.0.0.1:9880"
  speaker: "kiana"
  timeout_s: 60.0
```

`config/config.example.yaml` 仍保留 official API 的 `9880` 示例；当前 GSVI 试音脚本优先读取 `.env` 中的 `KASLANA_TTS_ENDPOINT=http://127.0.0.1:5100`。

## 当前最小实现

已完成一个不接入微信、不播放声卡、只调用本地 GPT-SoVITS HTTP 服务的最小试音模块：

- `GptSovitsTts.synthesize(text)`：向本地 `/tts` 发送 JSON 请求，要求返回 WAV，并解析采样率和声道数。
- `GptSovitsTts.load_weights()`：可选调用 `/set_gpt_weights` 和 `/set_sovits_weights`。
- `load_voice_profile_from_infer_config()`：读取 `infer_config.json`，解析参考音频、prompt、GPT 权重和 SoVITS 权重路径。
- `scripts/try_gpt_sovits_tts.py`：用命令行或环境变量指定模型配置，生成一个 ignored 的测试 WAV。
- 兼容两种请求风格：`official` 对应 GPT-SoVITS `api_v2.py`，`gsvi` 对应 GSVI / TTS-for-GPT-SoVITS。
- GSVI 预打包服务已部署到 ignored 的 `local_assets/GSVI-2.2.4-240318/GPT-SoVITS-Inference/`。
- `scripts/start_gsvi_tts_server.ps1` 使用 GSVI 自带 `runtime/python.exe` 启动服务，并只监听 `127.0.0.1`。
- `scripts/check_tts_server.py` 可检查 `/character_list`，也可用 `--synthesize` 合成短句到 `diagnostics/tts/`。
- `scripts/tts_control_panel.py` 提供本地浏览器控制台，可一键启动/关闭服务、选择角色与 emotion、输入测试语句并在网页内播放 WAV。

### 本地试音命令

本项目当前使用 GSVI / TTS-for-GPT-SoVITS 预打包服务。由于本机网络代理 `verge-mihomo` 已绑定 `5000` 端口，本项目默认把 GSVI endpoint 固定为 `http://127.0.0.1:5100`。

启动服务端：

```powershell
.\scripts\start_gsvi_tts_server.ps1 -Port 5100
```

检查服务端角色列表：

```powershell
conda run -n kaslana-protocol python scripts\check_tts_server.py
```

合成短句：

```powershell
conda run -n kaslana-protocol python scripts\check_tts_server.py --synthesize --character "琪亚娜E7" --text "早安。"
conda run -n kaslana-protocol python scripts\try_gpt_sovits_tts.py --api-style gsvi --character "琪亚娜E7" --text "早安，该起床啦。" --output diagnostics\tts\kiana_test.wav
```

浏览器控制台：

```powershell
.\scripts\start_tts_control_panel.ps1
```

控制台地址是 `http://127.0.0.1:8765`。页面只绑定本机，可启动/关闭 GSVI 服务、刷新角色列表、选择 emotion、切换 `auto`/`zh`/`en`/`ja` 语言参数，并把生成音频保存到 ignored 的 `diagnostics/tts/control_panel/` 后在网页内播放。

如果只想关闭 GSVI 服务端：

```powershell
.\scripts\stop_gsvi_tts_server.ps1
```

如果本地 official API 服务已经加载好模型，可加 `--skip-weight-switch` 跳过权重切换。输出目录 `diagnostics/` 和 WAV 文件默认不进入 Git。
试音脚本会自动读取项目根目录 `.env`，所以通过 `scripts/setup_kaslana_conda_env.ps1` 生成本机配置后无需手动重复设置这些环境变量。

当前限制：

- 脚本只保存 WAV，不负责播放。
- 本地浏览器控制台只播放网页音频，不播放到外置声卡。
- 只验证 TTS 单模块，不进入 orchestrator，也不触发微信或真实通话。

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

当前已完成独立脚本 `scripts/check_tts_server.py` 和本地浏览器控制台，均可检查 GSVI `/character_list` 并可选合成短句。尚未把健康检查接入 adapter factory 或 orchestrator preflight。

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
