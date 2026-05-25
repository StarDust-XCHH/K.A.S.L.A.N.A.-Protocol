# AI Task Template

把下面这段提示语复制给后续 AI 助手。每次只替换“本轮任务”部分即可。

```text
你正在接手 K.A.S.L.A.N.A. Protocol 项目。请先完整浏览工程，再开始本轮任务。

必须先阅读这些文件：
1. README.md
2. AI_HANDOFF.md
3. AI_TASK_TEMPLATE.md
4. docs/README.md
5. docs/00_PROJECT_STATUS.md
6. docs/01_ARCHITECTURE.md
7. docs/09_ROADMAP.md
8. docs/10_DEVELOPMENT_LOG.md
9. 与本轮任务相关的模块文档，例如：
   - docs/02_HARDWARE_PURCHASING_AND_SETUP.md
   - docs/03_WECHAT_AUTOMATION.md
   - docs/04_AUDIO_VAD_AND_ASR.md
   - docs/05_TTS_GPT_SOVITS.md
   - docs/06_LLM_OPENAI_COMPATIBLE.md
   - docs/07_ORCHESTRATION_AND_COLLABORATION.md
   - docs/08_TESTING_STANDARDS.md

必须先执行这些只读检查：
1. git status --short --branch
2. git log --oneline -5
3. rg --files
4. 按需读取相关源码和测试

项目绝对底线：
- 不使用微信协议逆向。
- 不 Hook 微信。
- 不修改微信内存。
- 不使用非官方微信 API。
- 不读取、伪造或发送微信网络协议包。
- 所有微信交互只能通过真实安卓手机上的真实 UI 自动化完成。
- 任何真实拨号行为都必须显式配置允许，并且优先要求人工确认。

开发纪律：
- 核心调度层只能依赖 ports 抽象接口。
- 具体 SDK 只能出现在 adapters 或脚本中。
- 设备 ID、坐标、联系人、API Key、模型路径必须来自配置或环境变量。
- 先写或更新测试，再实现。
- 小步提交，不要一次改很多模块。
- 不要把真实联系人、设备序列号、API Key、音色权重、参考音频、生成通话音频提交进仓库。

完成本轮任务后必须：
1. 更新 AI_HANDOFF.md 的当前状态和下一步建议。
2. 更新 docs/00_PROJECT_STATUS.md。
3. 如完成或改变路线，更新 docs/09_ROADMAP.md。
4. 在 docs/10_DEVELOPMENT_LOG.md 增加一条记录。
5. 如修改某模块，更新对应模块文档。
6. 运行：
   - python -m pytest
   - python -m ruff check .
   - git diff --check
   - python -m kaslana.main --config config/config.example.yaml --check-config
7. 生成一个窄范围 Git 提交。

本轮任务：
在这里写具体任务。
```

## 完成记录格式

每次任务结束时，在 `docs/10_DEVELOPMENT_LOG.md` 追加：

```markdown
## YYYY-MM-DD - 简短标题

- Commit: `<hash>` 或 `not committed`
- Scope: 本次改动范围
- Completed:
  - ...
- Tests:
  - `python -m pytest`: pass/fail
  - `python -m ruff check .`: pass/fail
  - `git diff --check`: pass/fail
  - config smoke test: pass/fail
- Updated docs:
  - ...
- Next recommended task:
  - ...
- Notes/Risks:
  - ...
```
