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

小功能：

- GPT-SoVITS 健康检查。
- 短句合成。
- 音频格式解析。
- 缓存。
- 输出播放。

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

## 长期优化方向

- 流式 ASR。
- 流式 LLM。
- 分句 TTS。
- 更准确的接通检测。
- UI 选择器自校准。
- 音频自动增益建议。
- 每日健康报告。
- 更细的错误分类。
