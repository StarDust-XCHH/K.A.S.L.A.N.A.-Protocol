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

## 2026-05-25 - 接入离线预瞄与缓存骨架

- Commit: `not committed`
- Scope: 离线预瞄缓存可测骨架、Orchestrator 缓存优先分支、AI 交接文档、PyCharm 忽略项
- Completed:
  - 新增离线缓存领域对象和 ingestion、weather、dialogue cache、intent router ports。
  - 新增 JSON dialogue cache、Regex intent router、本地文件接入和静态天气占位 adapter。
  - 新增 `INTENT_MATCHING` 状态，缓存命中直接播放本地音频，缓存未命中回落实时 LLM/TTS。
  - 新增 `scripts/run_nightly_preprocess.py` 安全 CLI 骨架。
  - 更新 `.gitignore`，忽略 `cache/`、`.idea/` 和 `*.iml`。
- Tests:
  - `python -m pytest`: pass
  - `python -m ruff check .`: pass
  - `git diff --check`: pass
  - config smoke test: pass
- Updated docs:
  - `AI_HANDOFF.md`
  - `docs/00_PROJECT_STATUS.md`
  - `docs/01_ARCHITECTURE.md`
  - `docs/07_ORCHESTRATION_AND_COLLABORATION.md`
  - `docs/09_ROADMAP.md`
  - `docs/11_OFFLINE_RAG_PRECACHE.md`
  - `docs/README.md`
  - `docs/10_DEVELOPMENT_LOG.md`
- Next recommended task:
  - 若继续离线缓存方向，先做 adapter factory 与 OfflinePreprocessor fake LLM/TTS 测试。
  - 若按风险优先路线推进，继续做硬件诊断与音频校准。
- Notes/Risks:
  - 当前仍不是可生产运行的夜间批处理；真实天气、真实 LLM/TTS 和定时任务实战运行尚未实现。

## 2026-05-25 - 增加 GPT-SoVITS 单句试音模块

- Commit: `not committed`
- Scope: GPT-SoVITS HTTP adapter、infer_config 读取、TTS 试音脚本、单元测试、文档交接
- Completed:
  - 实现 `GptSovitsTts.synthesize()`，可用 official API 或 GSVI 风格向本地 `/tts` 请求 WAV 并解析音频元信息。
  - 实现 `load_voice_profile_from_infer_config()`，从模型包的 `infer_config.json` 读取参考音频、prompt 和权重路径。
  - 实现可选的 `/set_gpt_weights`、`/set_sovits_weights` 权重切换。
  - 新增 `scripts/try_gpt_sovits_tts.py`，支持 `cbu5201_torch_env` 下列出 emotion 和生成一段测试 WAV。
  - 将 `ports/__init__.py` 改为懒加载，避免 TTS 脚本在 Python 3.9 conda 环境中导入无关模块。
- Tests:
  - `python -m pytest`: pass
  - `python -m ruff check .`: pass
  - `git diff --check`: pass
  - config smoke test: pass
- Updated docs:
  - `AI_HANDOFF.md`
  - `docs/00_PROJECT_STATUS.md`
  - `docs/05_TTS_GPT_SOVITS.md`
  - `docs/09_ROADMAP.md`
  - `docs/10_DEVELOPMENT_LOG.md`
- Next recommended task:
  - 启动本地 GPT-SoVITS API 服务后运行试音脚本生成 WAV，再补 TTS endpoint 健康检查。
- Notes/Risks:
  - 当前只验证 TTS 单模块，不播放声卡、不进入 orchestrator、不触发微信或真实通话。
  - 本机验证时 GPT-SoVITS endpoint 未启动，单句合成 smoke test 以清晰超时失败结束。

## 2026-05-26 - 落盘专属 Conda GPU 环境

- Commit: `not committed`
- Scope: `kaslana-protocol` conda 环境模板、GPU 检查脚本、本机配置引导、文档交接
- Completed:
  - 新增 `environment.yml`，定义 Python 3.11、项目核心、硬件诊断和 TTS HTTP 客户端依赖。
  - 新增 `scripts/setup_kaslana_conda_env.ps1`，创建或更新专属 conda 环境，并安装 CUDA 12.8 PyTorch wheels。
  - 新增 `scripts/check_gpu.py`，输出 PyTorch/CUDA/GPU 显存和 compute capability。
  - 更新 `.env.example`，加入专属环境名和 TTS 试音默认变量。
  - 更新 README、AI handoff、项目状态和 TTS 文档。
- Tests:
  - `conda run -n kaslana-protocol python --version`: pass, Python 3.11.15
  - dependency import smoke test: pass
  - `conda run -n kaslana-protocol python scripts\check_gpu.py`: pass, CUDA available on RTX 4060 Laptop GPU
  - `conda run -n kaslana-protocol python scripts\try_gpt_sovits_tts.py --list-emotions`: pass
  - `conda run -n kaslana-protocol python -m pytest`: pass
  - `conda run -n kaslana-protocol python -m ruff check .`: pass
  - `git diff --check`: pass
  - config smoke test: pass
- Updated docs:
  - `README.md`
  - `AI_HANDOFF.md`
  - `docs/00_PROJECT_STATUS.md`
  - `docs/05_TTS_GPT_SOVITS.md`
  - `docs/10_DEVELOPMENT_LOG.md`
- Next recommended task:
  - 用 `scripts/setup_kaslana_conda_env.ps1` 创建环境后运行 GPU、测试和 TTS emotion 检查。
- Notes/Risks:
  - `environment.yml` keeps audio packages under pip because conda resolution on this Windows setup could not find `sounddevice`/`soundfile`.
  - GSVI/GPT-SoVITS 服务端仍不放进主项目环境，需在 `local_assets/` 或外部目录单独启动。

## 2026-05-26 - 部署可复用本地 GSVI TTS 服务

- Commit: `not committed`
- Scope: ignored 的本地 GSVI 服务端部署、loopback 启动脚本、TTS 健康检查脚本、文档交接
- Completed:
  - 将 GSVI 预打包服务部署到 ignored 的 `local_assets/GSVI-2.2.4-240318/GPT-SoVITS-Inference/`。
  - 将琪亚娜模型复制到 ignored 的 GSVI `trained/` 目录，并把本地默认角色切到 `琪亚娜E7`。
  - 新增 `scripts/start_gsvi_tts_server.ps1`，使用 GSVI 自带 runtime 启动服务，并只监听 `127.0.0.1`。
  - 新增 `scripts/check_tts_server.py`，检查 `/character_list` 并可选合成短句到 ignored 的 `diagnostics/tts/`。
  - 发现当前网络代理 `verge-mihomo` 已绑定 `5000`，因此本机 `.env` 和示例 endpoint 改为 `http://127.0.0.1:5100`。
  - 成功生成 `diagnostics/tts/kiana_health.wav` 和 `diagnostics/tts/kiana_test.wav`。
- Tests:
  - `.\scripts\start_gsvi_tts_server.ps1 -Port 5100`: pass
  - `conda run -n kaslana-protocol python scripts\check_tts_server.py`: pass
  - `conda run -n kaslana-protocol python scripts\check_tts_server.py --synthesize --character "琪亚娜E7" --text "早安。"`: pass
  - `conda run -n kaslana-protocol python scripts\try_gpt_sovits_tts.py --api-style gsvi --character "琪亚娜E7" --text "早安，该起床啦。"`: pass
  - `conda run -n kaslana-protocol python -m pytest`: pass, 27 passed
  - `conda run -n kaslana-protocol python -m ruff check .`: pass
  - `git diff --check`: pass
  - config smoke test: pass
- Updated docs:
  - `README.md`
  - `.env.example`
  - `AI_HANDOFF.md`
  - `docs/00_PROJECT_STATUS.md`
  - `docs/05_TTS_GPT_SOVITS.md`
  - `docs/09_ROADMAP.md`
  - `docs/10_DEVELOPMENT_LOG.md`
- Next recommended task:
  - 把 TTS 健康检查接入 adapter factory / preflight，再考虑受控声卡播放。
- Notes/Risks:
  - GSVI 服务端、预训练模型、模型权重、运行日志和生成 WAV 都在 ignored 目录，不进入 Git。
  - 当前仍不接入微信、不播放声卡、不进入真实通话。

## 2026-05-26 - 增加本地 TTS 试音控制台

- Commit: `not committed`
- Scope: 本地浏览器 TTS 控制台、GSVI 安全停止脚本、fake API 测试、文档交接
- Completed:
  - 新增 `scripts/tts_control_panel.py`，用 Python 标准库提供只绑定 `127.0.0.1` 的本地 Web UI。
  - 新增 `scripts/start_tts_control_panel.ps1`，一条命令启动控制台并打开浏览器。
  - 新增 `scripts/stop_gsvi_tts_server.ps1`，只停止项目 PID 文件指向且路径属于本项目 GSVI root 的进程。
  - 控制台支持服务状态、启动/关闭、角色与 emotion 选择、`auto`/`zh`/`en`/`ja` 语言参数、高级采样参数和网页音频播放。
  - 控制台生成 WAV 到 ignored 的 `diagnostics/tts/control_panel/`。
- Tests:
  - `conda run -n kaslana-protocol python -m pytest tests\unit\test_tts_control_panel.py`: pass, 5 passed
  - `conda run -n kaslana-protocol python -m ruff check scripts\tts_control_panel.py tests\unit\test_tts_control_panel.py`: pass
  - `Invoke-RestMethod http://127.0.0.1:8765/api/status`: pass
  - `POST http://127.0.0.1:8765/api/synthesize`: pass, generated WAV
  - `conda run -n kaslana-protocol python -m pytest`: pass, 32 passed
  - `conda run -n kaslana-protocol python -m ruff check .`: pass
  - `git diff --check`: pass
  - config smoke test: pass
- Updated docs:
  - `README.md`
  - `AI_HANDOFF.md`
  - `docs/00_PROJECT_STATUS.md`
  - `docs/05_TTS_GPT_SOVITS.md`
  - `docs/09_ROADMAP.md`
  - `docs/10_DEVELOPMENT_LOG.md`
- Next recommended task:
  - 在控制台试听稳定后，再实现受控声卡输出 adapter；仍不要接入微信或真实通话。
- Notes/Risks:
  - 控制台只是本地试音工具，不是生产服务；页面播放浏览器音频，不播放外置声卡。

## 2026-05-26 - 整理可测功能文档和提交边界

- Commit: `not committed`
- Scope: 根目录功能测试说明、脚本维护策略、Git ignore 私有模型资产
- Completed:
  - 新增 `FEATURES_TESTING.md`，按模块列出当前可安全测试的小功能、命令、预期结果和安全边界。
  - 明确 `scripts/` 顶层入口暂不移动，后续优先抽 `scripts/lib/` 共享逻辑。
  - 更新 README、docs 索引和 AI handoff，把功能测试说明列为入口文档。
  - 更新 `.gitignore`，明确忽略本地 `assets/琪亚娜E7/` 模型包。
- Tests:
  - `conda run -n kaslana-protocol python -m pytest`: pass, 32 passed
  - `conda run -n kaslana-protocol python -m ruff check .`: pass
  - `git diff --check`: pass
  - config smoke test: pass
- Updated docs:
  - `FEATURES_TESTING.md`
  - `README.md`
  - `AI_HANDOFF.md`
  - `docs/README.md`
  - `docs/10_DEVELOPMENT_LOG.md`
- Next recommended task:
  - 完成提交并推送后，优先继续硬件诊断或受控声卡输出 adapter。
- Notes/Risks:
  - `assets/琪亚娜E7/`、`local_assets/`、`diagnostics/`、`.env` 和真实配置仍必须保持本地私有。

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
