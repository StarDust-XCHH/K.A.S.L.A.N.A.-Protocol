# 09. 后续开发路线图

## 路线原则

采用风险优先路线：

1. 先解决真实硬件和外设。
2. 再解决微信 UI 自动化。
3. 再解决音频、VAD、ASR。
4. 再接 TTS。
5. 再接 LLM。
6. 最后做完整调度和定时任务。

不要先追求“能完整跑一次”，因为完整闭环会掩盖底层不稳定问题。

## Milestone 1：文档与采购

目标：

- 工程手册完整落盘。
- 明确采购清单。
- 明确接线方式。
- 明确验收标准。

交付物：

- `docs/` 手册。
- `AI_HANDOFF.md`。
- `AI_TASK_TEMPLATE.md`。
- `docs/10_DEVELOPMENT_LOG.md`。
- README 文档入口。

验收：

- 新 AI 助手能读懂当前状态。
- 新 AI 助手能直接复制通用提示语开始浏览整个工程。
- 每轮完成后有固定流水账落盘位置。
- 你能按硬件文档采购或整理外设。

## Milestone 2：硬件诊断

目标：

- 证明 PC、A 端手机、外置声卡可控。

小功能：

- ADB 路径检测。
- ADB 设备列表解析。
- 目标设备在线检查。
- 屏幕分辨率读取。
- 截图。
- 电量/充电状态读取。
- 音频设备枚举。
- 配置设备匹配。

建议文件：

- `scripts/check_devices.py`
- `scripts/list_audio_devices.py`
- `src/kaslana/ports/hardware.py`
- `src/kaslana/adapters/hardware/`

测试：

- fake adb 输出解析。
- 无设备、多设备、未授权。
- 未安装 `sounddevice`。
- 音频设备不存在。

验收：

- ADB 和声卡诊断报告可读。
- 不打开微信。
- 不真实拨号。

## Milestone 3：音频校准

目标：

- 证明物理音频环回可用。

小功能：

- 输出测试音。
- 输入录音。
- 计算峰值和底噪。
- 检测削波。
- 生成校准报告。

建议文件：

- `scripts/calibrate_audio.py`
- `src/kaslana/adapters/audio/sounddevice_loopback.py`
- `src/kaslana/utils/audio_files.py`

测试：

- fake stream。
- 静音 fixture。
- 正弦波 fixture。
- 削波 fixture。

验收：

- 静音底噪达标。
- 测试音不削波。
- 设备名写入配置。

## Milestone 4：微信自动化 Level 1-3

目标：

- 能打开微信并搜索本人 B 机联系人，但不拨号。

小功能：

- uiautomator2 连接。
- 截图和 XML 保存。
- 唤醒设备。
- 打开微信。
- 搜索联系人。
- UI 选择器解析。

建议文件：

- `src/kaslana/adapters/automation/uiautomator2_wechat.py`
- `scripts/capture_ui_snapshot.py`

测试：

- fake driver。
- XML fixture。
- 未登录微信。
- 联系人未找到。
- 多候选联系人。

验收：

- Level 1-3 通过。
- 默认不拨号。

## Milestone 5：微信自动化 Level 4

目标：

- 人工在场时允许短拨号并挂断。

小功能：

- `allow_real_call` 配置。
- 点击语音通话。
- 接通/等待界面识别。
- 挂断。
- 失败截图。

测试：

- 默认配置禁止拨号。
- fake driver 确认拨号开关。
- 挂断幂等。

验收：

- 本人 B 机收到通话。
- 不误拨。
- 能挂断。

## Milestone 6：VAD 与 ASR

目标：

- 能从真实通话音频中切出 B 端一句话并转文字。

小功能：

- `SoundDeviceAudioInput`
- `SileroVad`
- `FasterWhisperAsr`
- 离线样本测试。

测试：

- 静音。
- 短噪声。
- 中文短句。
- 超时。

验收：

- B 端固定短句可识别。
- 无人说话不触发。

## Milestone 7：TTS

目标：

- 本地 GPT-SoVITS 零样本短句可生成并通过声卡播放给 B 端。

当前已完成：

- 最小 GPT-SoVITS HTTP adapter，可用 official API 或 GSVI 风格向本地 `/tts` 请求 WAV。
- 可从 `infer_config.json` 解析参考音频、prompt 和权重路径。
- 可选调用 `/set_gpt_weights`、`/set_sovits_weights` 切换模型。
- 新增 `scripts/try_gpt_sovits_tts.py` 做安全单句试音，不触发微信或拨号。
- 新增 ignored 的可复用本地 GSVI 预打包服务部署，模型复制到 `local_assets/.../trained/琪亚娜E7/`。
- 新增 `scripts/start_gsvi_tts_server.ps1`，用 GSVI 自带 runtime 只监听 `127.0.0.1`。
- 新增 `scripts/stop_gsvi_tts_server.ps1`，只停止项目启动的 GSVI 进程。
- 新增 `scripts/check_tts_server.py`，检查角色列表并可选合成短句。
- 新增 `scripts/tts_control_panel.py` 和 `scripts/start_tts_control_panel.ps1`，提供本地浏览器试音控制台。
- 本机因 `verge-mihomo` 占用 `5000`，当前 `.env` endpoint 使用 `http://127.0.0.1:5100`。
- 新增 fake HTTP 风格单元测试，覆盖 payload、文本清理和权重切换。

小功能：

- adapter factory / preflight 接线。
- 音频播放到受控输出设备。
- 音频格式解析。
- 缓存。

测试：

- fake HTTP server。
- 服务未启动。
- 空音频。
- 格式错误。

验收：

- B 端能听清短句。
- 音量不削波。

## Milestone 8：LLM

目标：

- 云端 LLM 生成短、自然、适合电话朗读的回复。

小功能：

- PromptManager。
- OpenAI-compatible adapter。
- 回复长度控制。
- 错误处理。

测试：

- fake server。
- API Key 缺失。
- 401、429、500。
- 空文本。

验收：

- 固定输入能生成合适回复。
- 日志不泄露密钥。

## Milestone 9：总调度 dry-run

目标：

- 不真实拨号，用 fake 或半真实模块跑完整状态流。

小功能：

- adapter factory。
- runtime profile。
- preflight。
- dry-run CLI。

测试：

- fake 全链路。
- 硬件缺失时失败。
- 模式切换。

验收：

- dry-run 报告完整。
- 不触发真实微信拨号。

## Milestone 10：完整人工通话

目标：

- 人工在场完成一轮真实早安通话。

步骤：

- preflight。
- 允许真实拨号。
- 拨打本人 B 机。
- 接通。
- 播放问候。
- B 端说一句话。
- ASR。
- LLM。
- TTS。
- 播放回复。
- 挂断。

验收：

- 不误拨。
- 能听清。
- 能识别。
- 能回复。
- 能挂断。
- 日志可复盘。

## Milestone 11：定时任务

目标：

- 早晨自动触发前先执行健康检查。

小功能：

- scheduler 实装。
- 运行窗口。
- 失败通知。
- 日志轮转。

验收：

- 不满足 preflight 不拨号。
- 失败不重试骚扰。
- 可手动关闭。

## Milestone 12：离线预瞄与缓存加速

目标：

- 把早晨 LLM/TTS 高延迟前移到夜间批处理。
- 早晨首句优先播放预渲染音频。
- 用户第一句 ASR 后通过本地 Regex 路由命中缓存分支。
- 未命中时保守回落实时 LLM/TTS。

当前已完成：

- 离线缓存领域对象、ports、JSON cache adapter、Regex router adapter。
- `INTENT_MATCHING` 状态和缓存命中/未命中状态流转。
- Orchestrator fake 测试覆盖缓存命中不调用 LLM/TTS。
- `scripts/run_nightly_preprocess.py` 安全 CLI 骨架。

后续小功能：

- adapter factory 读取 `offline_cache`、`ingestion`、`intent_matching`、`batch_preprocess` 配置。
- PromptManager 生成稳定的对话状态树 JSON prompt。
- LLM fake server 测试结构化输出成功和错误路径。
- GPT-SoVITS fake server 测试批量 WAV 渲染。
- 真实天气 provider 选择与配置。
- 缓存健康检查和过期策略。

验收：

- 夜间脚本能在 fake LLM/TTS 下生成完整日期缓存。
- 早晨 Orchestrator 命中缓存时零 LLM/TTS 调用。
- 缓存缺失、损坏、音频缺失都能回落实时链路。
- 生成缓存、日程资料和音频不进入 Git。

## 长期优化方向

- 流式 ASR。
- 流式 LLM。
- 分句 TTS。
- 更准确的接通检测。
- UI 选择器自校准。
- 音频自动增益建议。
- 每日健康报告。
- 更细的错误分类。
