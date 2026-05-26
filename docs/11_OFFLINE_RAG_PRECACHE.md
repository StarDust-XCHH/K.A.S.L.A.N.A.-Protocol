# 11. 离线预瞄与对话缓存模块

## 模块目标

离线预瞄模块用于把早晨通话中的高延迟 AI 计算前移到夜间空闲时间。

目标链路：

```text
夜间批处理
  -> 读取本地日志/日程
  -> 获取天气/日期上下文
  -> LLM 生成对话状态树
  -> TTS 批量渲染 WAV
  -> 写入 cache/YYYY-MM-DD/state_mapping.json

早晨通话
  -> 优先播放缓存问候
  -> ASR 用户第一句
  -> Regex 意图匹配
  -> 命中缓存音频则直接播放
  -> 未命中再走实时 LLM/TTS
```

当前已接入的是可测骨架，不包含真实天气 API、真实 LLM 结构化生成、真实 GPT-SoVITS 批量渲染或 adapter factory。

## 当前代码位置

- 领域对象：`src/kaslana/domain/offline_cache.py`
- 数据接入 port：`src/kaslana/ports/ingestion.py`
- 天气 port：`src/kaslana/ports/weather.py`
- 缓存 port：`src/kaslana/ports/dialogue_cache.py`
- 意图路由 port：`src/kaslana/ports/intent_router.py`
- JSON 缓存 adapter：`src/kaslana/adapters/dialogue_cache/json_file_cache.py`
- Regex 路由 adapter：`src/kaslana/adapters/intent_router/regex_router.py`
- 本地文件接入 adapter：`src/kaslana/adapters/ingestion/local_files.py`
- 静态天气占位 adapter：`src/kaslana/adapters/weather/static_provider.py`
- 夜间预处理骨架：`src/kaslana/core/offline_preprocessor.py`
- CLI 骨架：`scripts/run_nightly_preprocess.py`

## 缓存结构

默认缓存目录：

```text
cache/
  2026-05-25/
    state_mapping.json
    greeting.wav
    complaint.wav
    schedule_query.wav
    encouragement.wav
```

`cache/` 被 `.gitignore` 忽略。不要提交私密日程、生成音频或真实通话样本。

`state_mapping.json` schema v1：

```json
{
  "schema_version": 1,
  "date": "2026-05-25",
  "greeting": {
    "text": "早安，该起床啦。",
    "audio_path": "greeting.wav"
  },
  "branches": [
    {
      "id": "complaint",
      "intent": "complaint",
      "text": "不许赖床。",
      "audio_path": "complaint.wav",
      "patterns": ["再睡", "赖床"]
    }
  ]
}
```

## Orchestrator 行为

新增状态：

- `INTENT_MATCHING`

新增事件：

- `CACHE_MISS`
- `CACHED_REPLY_READY`

当前主路径：

```text
GREETING
  -> LISTENING
  -> INTENT_MATCHING
  -> SPEAKING
```

缓存未命中路径：

```text
LISTENING
  -> INTENT_MATCHING
  -> THINKING
  -> SPEAKING
```

行为规则：

- `RunOptions.offline_cache_enabled` 默认为 `false`。
- 未配置 `DialogueCachePort` 或 `IntentRouterPort` 时，自动回到实时链路。
- 当日缓存不存在、JSON 损坏、音频文件缺失、Regex 未命中时，走 `CACHE_MISS -> THINKING`。
- 命中缓存时直接 `AudioOutputPort.play_file()`，不调用 LLM/TTS。

## 后续待实现

- adapter factory 根据配置创建缓存、路由、ingestion、weather adapter。
- PromptManager 为夜间 LLM 生成稳定 JSON schema。
- OpenAI-compatible LLM adapter 支持结构化输出错误处理。
- GPT-SoVITS adapter 支持批量 WAV 渲染和健康检查。
- 真实天气 provider，例如和风、高德或 Open-Meteo。
- Windows Task Scheduler 或 cron 触发 `scripts/run_nightly_preprocess.py`。
- 预处理运行报告和缓存健康检查。

## 测试标准

- 状态机覆盖缓存命中和缓存 miss。
- Orchestrator fake 测试证明缓存命中不调用 LLM/TTS。
- JSON 缓存 adapter 覆盖保存、加载、损坏 JSON。
- Regex router 覆盖赖床抱怨、询问日程、清醒鼓励和 miss。
- 配置默认关闭，示例配置可加载。
- `cache/`、生成音频和 IDE 本地文件不进入 Git。
