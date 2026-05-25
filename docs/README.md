# K.A.S.L.A.N.A. 工程手册索引

这套文档面向两类读者：项目本人维护者，以及后续接手开发的 AI 助手。阅读目标不是一次性实现全部功能，而是让每一次迭代都知道边界、顺序、验收标准和不能碰的禁区。

## 当前阶段

项目处于“架构骨架已搭建，真实外设和模型适配器尚未实现”的阶段。当前仓库已经包含：

- Python 包结构与 `pyproject.toml`
- `ports/` 抽象接口
- `core/` 状态机和异步调度器骨架
- `config/` YAML 与 `.env` 加载
- `adapters/` 占位类
- fake 驱动单元测试
- 本地 Git 首次架构提交

还没有实现真实 ADB 控制、微信 UI 自动化、音频采集播放、VAD、ASR、GPT-SoVITS、LLM API 调用和定时任务实战运行。

## 绝对底线

K.A.S.L.A.N.A. Protocol 的目标是零微信协议风险。任何后续开发都必须遵守：

- 不使用微信协议逆向。
- 不 Hook 微信进程。
- 不修改微信内存。
- 不使用非官方微信 API。
- 不读取、伪造或发送微信网络协议包。
- 所有微信交互只能通过真实安卓手机上的真实 UI 自动化完成。

如果某个方案需要绕过真实 UI，它就不属于本项目。

## 推荐阅读顺序

1. [AI_HANDOFF.md](../AI_HANDOFF.md)
   后续 AI 助手的交接入口，先读它可以快速知道当前状态和开发纪律。

2. [00_PROJECT_STATUS.md](00_PROJECT_STATUS.md)
   当前已经完成什么、还没有完成什么、验证命令是什么。

3. [01_ARCHITECTURE.md](01_ARCHITECTURE.md)
   代码架构、依赖方向、接口边界和状态机设计。

4. [02_HARDWARE_PURCHASING_AND_SETUP.md](02_HARDWARE_PURCHASING_AND_SETUP.md)
   手机、声卡、线材、隔离器、ADB、Windows 音频设置和硬件验收。

5. [03_WECHAT_AUTOMATION.md](03_WECHAT_AUTOMATION.md)
   微信自动呼叫模块的分级解锁、定位策略、失败保守退出。

6. [04_AUDIO_VAD_AND_ASR.md](04_AUDIO_VAD_AND_ASR.md)
   音频 I/O、VAD、录音切片、ASR 的开发建议和测试标准。

7. [05_TTS_GPT_SOVITS.md](05_TTS_GPT_SOVITS.md)
   本地 GPT-SoVITS 零样本接入和音频输出规范。

8. [06_LLM_OPENAI_COMPATIBLE.md](06_LLM_OPENAI_COMPATIBLE.md)
   云端 OpenAI-compatible LLM 接入、Prompt 管理和回复约束。

9. [07_ORCHESTRATION_AND_COLLABORATION.md](07_ORCHESTRATION_AND_COLLABORATION.md)
   总调度、依赖注入、配置、日志、preflight 和协同开发规范。

10. [08_TESTING_STANDARDS.md](08_TESTING_STANDARDS.md)
    全项目测试标准、手工验收矩阵和真实拨号安全门槛。

11. [09_ROADMAP.md](09_ROADMAP.md)
    风险优先的后续开发路线图。

## 下一步建议

推荐下一次迭代先做“硬件诊断与外设校准”模块，而不是直接写微信拨号。原因是 ADB、旧安卓机稳定性、外置声卡、音频环回噪声会决定后续所有模块是否可测。

最低下一步交付物：

- 增强 `scripts/check_devices.py`，输出 ADB、设备授权、屏幕、电量、分辨率。
- 增强 `scripts/list_audio_devices.py`，在安装 `sounddevice` 后枚举输入/输出设备。
- 新增音频校准脚本的计划或实现：播放测试音、录制回环、检测底噪和削波。

## 上游资料入口

- Android Debug Bridge: https://developer.android.com/tools/adb
- uiautomator2: https://github.com/openatx/uiautomator2
- python-sounddevice: https://python-sounddevice.readthedocs.io/
- Silero VAD: https://github.com/snakers4/silero-vad
- Faster-Whisper: https://github.com/SYSTRAN/faster-whisper
- GPT-SoVITS: https://github.com/RVC-Boss/GPT-SoVITS
- OpenAI API: https://platform.openai.com/docs
- CTIA/OMTP headset wiring reference: https://www.startech.com/en-us/faq/audio-cables-ctia-vs-omtp-4-position
