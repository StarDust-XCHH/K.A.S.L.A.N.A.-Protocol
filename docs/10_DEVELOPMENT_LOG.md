# 10. 开发流水账

这个文件用于给后续 AI 助手和项目维护者快速了解“最近完成了什么、验证了什么、下一步做什么”。每次完成一轮实质任务后，都应该在这里追加一条记录。

不要在这里记录：

- API Key。
- 真实联系人姓名。
- 微信账号信息。
- 设备序列号。
- 私密音频文件路径。
- 模型权重私有路径。

## 2026-05-25 - 初始化架构骨架

- Commit: `a72451b`
- Scope: Python 工程骨架、抽象接口、状态机、配置加载、adapter 占位、fake 测试
- Completed:
  - 创建 `src/kaslana/` 包结构。
  - 定义 automation、audio、vad、asr、llm、tts ports。
  - 定义 call state、event、session 和 orchestrator 骨架。
  - 创建 `config/config.example.yaml` 和 `config/prompts/kiana.yaml`。
  - 添加 adapter 占位类。
  - 添加单元测试。
- Tests:
  - `python -m pytest`: pass
  - `python -m ruff check .`: pass
  - config smoke test: pass
- Updated docs:
  - `README.md`
- Next recommended task:
  - 落盘工程手册和 AI 交接文档。
- Notes/Risks:
  - 真实硬件、微信、音频、VAD、ASR、TTS、LLM 均未实现。

## 2026-05-25 - 落盘工程手册与 AI 交接

- Commit: `4fc2303`
- Scope: 长期工程手册、模块规划、测试标准、AI 交接
- Completed:
  - 新增 `AI_HANDOFF.md`。
  - 新增 `docs/README.md`。
  - 新增 `docs/00_PROJECT_STATUS.md` 到 `docs/09_ROADMAP.md`。
  - 更新 README 作为简洁入口。
  - 更新 `.gitignore`，忽略日志、诊断、音频、模型资产。
- Tests:
  - `python -m pytest`: pass
  - `python -m ruff check .`: pass
  - `git diff --cached --check`: pass
  - config smoke test: pass
- Updated docs:
  - `README.md`
  - `AI_HANDOFF.md`
  - `docs/`
- Next recommended task:
  - 新增 AI 任务模板和开发流水账，方便长期接力。
- Notes/Risks:
  - 文档已详细规划，但真实实现仍未开始。

## Template

```markdown
## YYYY-MM-DD - 简短标题

- Commit: `<hash>` 或 `not committed`
- Scope: 本次改动范围
- Completed:
  - ...
- Tests:
  - `python -m pytest`: pass/fail/not run
  - `python -m ruff check .`: pass/fail/not run
  - `git diff --check`: pass/fail/not run
  - config smoke test: pass/fail/not run
- Updated docs:
  - ...
- Next recommended task:
  - ...
- Notes/Risks:
  - ...
```
