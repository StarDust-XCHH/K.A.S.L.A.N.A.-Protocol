from __future__ import annotations

import json
from io import BytesIO
from urllib.error import HTTPError

import pytest

from kaslana.adapters.llm.tongyi_chat import (
    TongyiChatClient,
    TongyiChatError,
    read_api_key,
    sanitize_markdown_fences,
)


class FakeResponse:
    def __init__(self, body: str) -> None:
        self._body = body.encode("utf-8")

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> FakeResponse:
        return self

    def __exit__(self, *args: object) -> None:
        return None


def test_sanitize_removes_code_fence() -> None:
    raw = "```markdown\n你好，我是琪亚娜。\n```"
    assert sanitize_markdown_fences(raw) == "你好，我是琪亚娜。"


def test_read_api_key_prefers_tongyi(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TONGYI_API_KEY", " tongyi-key ")
    monkeypatch.setenv("DASHSCOPE_API_KEY", "dash-key")
    assert read_api_key() == "tongyi-key"


def test_read_api_key_falls_back_to_dashscope(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TONGYI_API_KEY", raising=False)
    monkeypatch.setenv("DASHSCOPE_API_KEY", "dash-key")
    assert read_api_key() == "dash-key"


def test_status_unavailable_without_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TONGYI_API_KEY", raising=False)
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
    status = TongyiChatClient(api_key=None).get_status()
    assert status.available is False
    assert "TONGYI_API_KEY" in status.message


def test_default_model_is_qwen_flash(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("KASLANA_TONGYI_MODEL", raising=False)
    client = TongyiChatClient(api_key="test-key")
    assert client.model == "qwen-flash"
    assert client.timeout_s == 60.0


def test_qwen_long_uses_longer_default_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    client = TongyiChatClient(api_key="test-key", model="qwen-long")
    assert client.timeout_s == 120.0


def test_complete_parses_chat_completion(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_urlopen(request, timeout: float = 0) -> FakeResponse:
        assert request.full_url.endswith("/chat/completions")
        payload = json.loads(request.data.decode("utf-8"))
        assert payload["model"] == "qwen-flash"
        assert payload["stream"] is False
        assert "《崩坏三》" in payload["messages"][0]["content"]
        body = {
            "model": "qwen-long",
            "choices": [{"message": {"role": "assistant", "content": "你好，我是琪亚娜。"}}],
            "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
        }
        return FakeResponse(json.dumps(body))

    client = TongyiChatClient(api_key="test-key", urlopen_fn=fake_urlopen)
    result = client.complete(
        [
            {"role": "system", "content": "请模仿《崩坏三》角色“琪亚娜”。"},
            {"role": "user", "content": "写一段长文"},
        ]
    )

    assert result.text == "你好，我是琪亚娜。"
    assert result.model == "qwen-long"
    assert result.usage == {
        "prompt_tokens": 10,
        "completion_tokens": 20,
        "total_tokens": 30,
    }


def test_complete_raises_on_http_401() -> None:
    def fake_urlopen(request, timeout: float = 0) -> FakeResponse:
        raise HTTPError(
            request.full_url,
            401,
            "Unauthorized",
            hdrs=None,
            fp=BytesIO(b'{"error":"invalid"}'),
        )

    client = TongyiChatClient(api_key="bad-key", urlopen_fn=fake_urlopen)

    with pytest.raises(TongyiChatError, match="401"):
        client.complete([{"role": "user", "content": "topic"}])


def test_complete_raises_on_empty_content() -> None:
    def fake_urlopen(request, timeout: float = 0) -> FakeResponse:
        body = {"choices": [{"message": {"role": "assistant", "content": ""}}]}
        return FakeResponse(json.dumps(body))

    client = TongyiChatClient(api_key="test-key", urlopen_fn=fake_urlopen)

    with pytest.raises(TongyiChatError, match="未返回有效内容"):
        client.complete([{"role": "user", "content": "topic"}])


def test_status_does_not_embed_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TONGYI_API_KEY", "secret-key-value")
    status = TongyiChatClient().get_status()
    assert "secret-key-value" not in status.message
