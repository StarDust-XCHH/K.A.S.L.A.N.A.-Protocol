# 13. AI 任务书：硬件诊断第一版

这份文档给后续 AI 助理使用。目标是把下一轮开发收敛到安全、可测、可验证的硬件诊断功能。

本任务只实现诊断脚本，不打开微信、不点击 UI、不拨号。

## 可直接复制的任务提示

```text
你正在接手 K.A.S.L.A.N.A. Protocol 项目。请先完整浏览工程，再开始本轮任务。

必须先阅读这些文件：
1. README.md
2. AI_HANDOFF.md
3. AI_TASK_TEMPLATE.md
4. docs/README.md
5. docs/00_PROJECT_STATUS.md
6. docs/01_ARCHITECTURE.md
7. docs/02_HARDWARE_PURCHASING_AND_SETUP.md
8. docs/12_OWNER_HARDWARE_PREP_MANUAL.md
9. docs/13_AI_TASK_HARDWARE_DIAGNOSTICS.md
10. docs/09_ROADMAP.md
11. docs/10_DEVELOPMENT_LOG.md

必须先执行这些只读检查：
1. git status --short --branch
2. git log --oneline -5
3. rg --files
4. 按需读取 scripts/check_devices.py、config/config.example.yaml、配置 schema 和现有测试

项目绝对底线：
- 不使用微信协议逆向。
- 不 Hook 微信。
- 不修改微信内存。
- 不使用非官方微信 API。
- 不读取、伪造或发送微信网络协议包。
- 所有微信交互只能通过真实安卓手机上的真实 UI 自动化完成。
- 本轮任务禁止打开微信、点击微信 UI 或真实拨号。

本轮任务：
实现硬件诊断第一版，增强 scripts/check_devices.py。

范围：
1. 自动检测 adb 可执行文件。
   - 优先使用 KASLANA_ADB_PATH 环境变量。
   - 其次使用 PATH 中的 adb。
   - 找不到时输出清晰诊断，不抛未捕获异常。
2. 执行 adb devices -l 并解析设备列表。
   - 支持 device、unauthorized、offline、其他未知状态。
   - 输出所有发现的设备摘要。
3. 根据配置中的 automation.android_device_id 判断目标设备。
   - 配置目标在线时继续读取详情。
   - 配置目标不存在时输出清晰提示。
   - 多设备时不自动随便选择。
4. 目标设备在线时读取：
   - 屏幕分辨率：adb shell wm size
   - 电池和充电状态：adb shell dumpsys battery
5. 支持可选截图诊断。
   - 默认不截图。
   - 增加命令行参数显式开启截图。
   - 截图保存到 diagnostics/，该目录不应进入 Git。
6. 输出人类可读诊断摘要。
   - 能区分 pass、warning、fail。
   - 不打印真实联系人。
   - 不打印 API Key。
7. 添加 fake ADB 输出解析单元测试。
   - 覆盖无设备、单设备在线、未授权、离线、多设备。
   - 覆盖 wm size 解析。
   - 覆盖 dumpsys battery 解析。

完成后必须：
1. 更新 AI_HANDOFF.md 的当前状态和下一步建议。
2. 更新 docs/00_PROJECT_STATUS.md。
3. 如改变路线，更新 docs/09_ROADMAP.md。
4. 在 docs/10_DEVELOPMENT_LOG.md 增加一条记录。
5. 如修改硬件模块文档，更新 docs/02_HARDWARE_PURCHASING_AND_SETUP.md。
6. 运行：
   - python -m pytest
   - python -m ruff check .
   - git diff --check
   - python -m kaslana.main --config config/config.example.yaml --check-config
7. 生成一个窄范围 Git 提交。
```

## 实现边界

允许：

- 读取配置。
- 调用 ADB 只读命令。
- 解析 ADB 文本输出。
- 创建本地 `diagnostics/` 目录保存显式请求的截图。
- 增加纯 Python 解析函数和单元测试。

禁止：

- 打开微信。
- 搜索联系人。
- 点击屏幕。
- 输入文本。
- 发起语音通话。
- 自动选择不明确的目标设备。
- 记录真实联系人、API Key 或私密路径。
- 把真实截图、设备序列号清单或诊断产物提交进 Git。

## 建议实现形态

第一版保持脚本简单，不要急着引入完整 `HardwareProbePort`。

建议把 `scripts/check_devices.py` 拆成两层：

- 纯解析函数：解析 `adb devices -l`、`wm size`、`dumpsys battery`。
- 命令执行层：负责调用 `subprocess.run()`、处理超时和返回码。

解析函数必须能在没有真实硬件时被单元测试覆盖。命令执行层只需要对失败给出清晰提示。

建议命令行参数：

- `--config`：默认 `config/config.example.yaml`。
- `--adb`：可选，手动指定 adb 路径。
- `--screenshot`：显式开启截图。
- `--diagnostics-dir`：默认 `diagnostics`。

ADB 查找优先级：

1. `--adb`
2. `KASLANA_ADB_PATH`
3. PATH 中的 `adb`

## 输出建议

人类可读输出示例：

```text
K.A.S.L.A.N.A. hardware diagnostics

ADB: pass
Devices: warning
- replace-with-adb-device-id: not found
- 1234567890abcdef: device

Target device: fail
Reason: configured android_device_id was not found.

No WeChat action was performed.
No call was placed.
```

目标设备在线时：

```text
ADB: pass
Target device: pass
Screen: 1080x2400
Battery: 82%, charging
Screenshot: skipped

No WeChat action was performed.
No call was placed.
```

## 测试要求

最低测试：

- `adb devices -l` 空列表解析。
- 单个 `device` 状态解析。
- `unauthorized` 状态解析。
- `offline` 状态解析。
- 多设备解析。
- `Physical size: 1080x2400` 解析。
- `dumpsys battery` 中 `level`、`status`、`AC powered`、`USB powered` 解析。

验收命令：

```powershell
python -m pytest
python -m ruff check .
git diff --check
python -m kaslana.main --config config/config.example.yaml --check-config
```

## 完成定义

本轮任务完成时应满足：

- 无真实设备也能给出清晰诊断。
- 有 Xiaomi 13 且授权后，能打印分辨率、电量和充电状态。
- 只有显式 `--screenshot` 时才保存截图。
- 脚本不会打开微信或触发任何真实通话行为。
- fake 输出解析测试通过。
- 文档和交接状态已更新。
