"""Tongyi / DashScope OpenAI-compatible chat client (stdlib urllib only)."""

from __future__ import annotations

import json
import os
import re
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DEFAULT_MODEL = "qwen-flash"
DEFAULT_LONG_TEXT_MODEL = "qwen-long"
DEFAULT_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
DEFAULT_TIMEOUT_S = 120.0
DEFAULT_FLASH_TIMEOUT_S = 60.0

UrlopenFn = Callable[..., Any]


class TongyiChatError(RuntimeError):
    """Raised when a Tongyi chat request or response is invalid."""


@dataclass(frozen=True)
class TongyiChatResult:
    text: str
    model: str
    usage: dict[str, int] | None = None


@dataclass(frozen=True)
class TongyiChatStatus:
    available: bool
    configured: bool
    model: str
    base_url: str
    message: str

    def as_dict(self) -> dict[str, object]:
        return {
            "available": self.available,
            "configured": self.configured,
            "model": self.model,
            "base_url": self.base_url,
            "message": self.message,
        }


def read_api_key() -> str | None:
    """Return the first configured API key without logging it."""
    for name in ("TONGYI_API_KEY", "DASHSCOPE_API_KEY"):
        value = os.environ.get(name, "").strip()
        if value:
            return value
    return None


def sanitize_markdown_fences(text: str) -> str:
    """Remove common Markdown fence wrappers from model output."""
    cleaned = text.strip()
    cleaned = re.sub(r"^```(?:[\w-]+)?\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    return cleaned.strip()


class TongyiChatClient:
    """OpenAI-compatible chat completions client for Tongyi / DashScope."""

    def __init__(
        self,
        *,
        model: str | None = None,
        base_url: str | None = None,
        timeout_s: float | None = None,
        api_key: str | None = None,
        urlopen_fn: UrlopenFn | None = None,
    ) -> None:
        self.model = (model or os.environ.get("KASLANA_TONGYI_MODEL") or DEFAULT_MODEL).strip()
        self.base_url = (
            base_url or os.environ.get("KASLANA_TONGYI_BASE_URL") or DEFAULT_BASE_URL
        ).rstrip("/")
        if timeout_s is None:
            timeout_s = (
                DEFAULT_FLASH_TIMEOUT_S
                if self.model.lower() in {"qwen-flash", "qwen-flash-latest"}
                else DEFAULT_TIMEOUT_S
            )
        self.timeout_s = timeout_s
        self._api_key = api_key if api_key is not None else read_api_key()
        self._urlopen = urlopen_fn or urlopen

    def get_status(self) -> TongyiChatStatus:
        configured = bool(self._api_key)
        if configured:
            return TongyiChatStatus(
                available=True,
                configured=True,
                model=self.model,
                base_url=self.base_url,
                message=f"已连接默认服务：{self.model}",
            )
        return TongyiChatStatus(
            available=False,
            configured=False,
            model=self.model,
            base_url=self.base_url,
            message=(
                "服务端未读取到环境变量 TONGYI_API_KEY 或 DASHSCOPE_API_KEY，"
                "通义长文生成已禁用"
            ),
        )

    def complete(self, messages: list[dict[str, str]]) -> TongyiChatResult:
        if not self._api_key:
            raise TongyiChatError(
                "未配置 TONGYI_API_KEY 或 DASHSCOPE_API_KEY，无法调用通义服务。"
            )
        if not messages:
            raise TongyiChatError("messages 不能为空。")

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
        }
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request = Request(
            f"{self.base_url}/chat/completions",
            data=body,
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        try:
            with self._urlopen(request, timeout=self.timeout_s) as response:
                raw = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            raise TongyiChatError(_http_error_message(exc)) from exc
        except URLError as exc:
            raise TongyiChatError(f"通义服务网络错误：{exc.reason}") from exc
        except TimeoutError as exc:
            raise TongyiChatError("通义服务请求超时，请稍后重试。") from exc
        except json.JSONDecodeError as exc:
            raise TongyiChatError("通义服务返回了无效的 JSON。") from exc

        return _parse_completion_response(raw, default_model=self.model)


def _http_error_message(exc: HTTPError) -> str:
    details = exc.read().decode("utf-8", errors="replace").strip()
    if exc.code == 401:
        return "通义 API 认证失败（401），请检查 TONGYI_API_KEY 或 DASHSCOPE_API_KEY。"
    if exc.code == 429:
        return "通义 API 请求过于频繁或额度不足（429），请稍后重试。"
    if exc.code >= 500:
        return f"通义服务暂时不可用（HTTP {exc.code}），请稍后重试。"
    suffix = f"：{details}" if details else ""
    return f"通义 API 请求失败（HTTP {exc.code}）{suffix}"


def _parse_completion_response(raw: Any, *, default_model: str) -> TongyiChatResult:
    if not isinstance(raw, dict):
        raise TongyiChatError("通义服务响应格式无效。")

    choices = raw.get("choices")
    if not isinstance(choices, list) or not choices:
        raise TongyiChatError("通义服务未返回有效 choices。")

    first = choices[0]
    if not isinstance(first, dict):
        raise TongyiChatError("通义服务 choices 格式无效。")

    message = first.get("message")
    if not isinstance(message, dict):
        raise TongyiChatError("通义服务未返回 message。")

    content = message.get("content")
    if not isinstance(content, str) or not content.strip():
        raise TongyiChatError("AI 服务未返回有效内容。")

    model = raw.get("model")
    resolved_model = model.strip() if isinstance(model, str) and model.strip() else default_model
    usage = _parse_usage(raw.get("usage"))
    text = sanitize_markdown_fences(content)
    if not text:
        raise TongyiChatError("AI 服务未返回有效内容。")
    return TongyiChatResult(text=text, model=resolved_model, usage=usage)


def _parse_usage(raw: Any) -> dict[str, int] | None:
    if not isinstance(raw, dict):
        return None
    usage: dict[str, int] = {}
    for key in ("prompt_tokens", "completion_tokens", "total_tokens"):
        value = raw.get(key)
        if isinstance(value, int):
            usage[key] = value
    return usage or None
