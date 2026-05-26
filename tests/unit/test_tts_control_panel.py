from __future__ import annotations

import importlib.util
import json
import sys
import threading
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


def _load_panel_module() -> Any:
    script = Path(__file__).resolve().parents[2] / "scripts" / "tts_control_panel.py"
    spec = importlib.util.spec_from_file_location("tts_control_panel", script)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


panel_module = _load_panel_module()


def test_status_reports_stopped_without_endpoint(tmp_path: Path) -> None:
    controller = _controller(tmp_path)
    controller.is_endpoint_reachable = lambda: False  # type: ignore[method-assign]

    status = controller.status()

    assert status["running"] is False
    assert status["managed"] is False
    assert status["endpoint"] == "http://127.0.0.1:5100"


def test_stop_refuses_unmanaged_pid(tmp_path: Path) -> None:
    controller = _controller(tmp_path)
    controller.config.pid_file.write_text("1234", encoding="ascii")
    controller.is_endpoint_reachable = lambda: True  # type: ignore[method-assign]
    controller._read_process_info = lambda pid: {  # type: ignore[method-assign]
        "ProcessId": pid,
        "ExecutablePath": "C:\\Windows\\System32\\python.exe",
        "CommandLine": "python something_else.py",
    }

    killed: list[int] = []
    controller._kill_process = killed.append  # type: ignore[method-assign]

    result = controller.stop_server()

    assert result["ok"] is False
    assert "Refusing" in result["message"]
    assert killed == []


def test_audio_path_rejects_traversal(tmp_path: Path) -> None:
    controller = _controller(tmp_path)

    for name in ("../secret.wav", "..%2Fsecret.wav", "nested/file.wav", "test.mp3"):
        try:
            controller.resolve_audio_file(name)
        except panel_module.ControlPanelError:
            pass
        else:
            raise AssertionError(f"Expected {name!r} to be rejected")


def test_http_api_with_fake_controller(tmp_path: Path) -> None:
    audio_dir = tmp_path / "audio"
    audio_dir.mkdir()
    (audio_dir / "sample.wav").write_bytes(b"RIFFsample")
    fake = FakeController(audio_dir)
    handler = panel_module.ControlPanelRequestHandler.create(fake)
    server = panel_module.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_address[1]}"
    try:
        status = _get_json(f"{base_url}/api/status")
        characters = _get_json(f"{base_url}/api/characters")
        synth = _post_json(
            f"{base_url}/api/synthesize",
            {"text": "早安。", "character": "琪亚娜E7", "emotion": "default"},
        )
        audio_url = f"{base_url}/audio/{synth['audio']['filename']}"
        with urllib.request.urlopen(audio_url, timeout=5) as response:
            audio = response.read()
    finally:
        server.shutdown()
        server.server_close()

    assert status["status"]["running"] is True
    assert characters["characters"] == {"琪亚娜E7": ["default"]}
    assert synth["audio"]["audio_url"] == "/audio/sample.wav"
    assert audio == b"RIFFsample"


def test_http_api_rejects_empty_text(tmp_path: Path) -> None:
    fake = FakeController(tmp_path)
    handler = panel_module.ControlPanelRequestHandler.create(fake)
    server = panel_module.ThreadingHTTPServer(("127.0.0.1", 0), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base_url = f"http://127.0.0.1:{server.server_address[1]}"
    try:
        try:
            _post_json(f"{base_url}/api/synthesize", {"text": ""})
        except urllib.error.HTTPError as exc:
            body = json.loads(exc.read().decode("utf-8"))
            status = exc.code
        else:
            raise AssertionError("Expected HTTPError")
    finally:
        server.shutdown()
        server.server_close()

    assert status == 400
    assert "Text is required" in body["error"]


class FakeController:
    def __init__(self, audio_dir: Path) -> None:
        self.audio_dir = audio_dir

    def status(self) -> dict[str, Any]:
        return {
            "running": True,
            "managed": True,
            "endpoint": "http://127.0.0.1:5100",
            "pid": 123,
            "port": 5100,
            "logs": {"stdout": "ready", "stderr": ""},
        }

    def start_server(self) -> dict[str, Any]:
        return self.status() | {"message": "started"}

    def stop_server(self) -> dict[str, Any]:
        return {"ok": True, "message": "stopped", "status": self.status()}

    def fetch_characters(self) -> dict[str, tuple[str, ...]]:
        return {"琪亚娜E7": ("default",)}

    def synthesize(self, payload: dict[str, Any]) -> dict[str, Any]:
        if not str(payload.get("text", "")).strip():
            raise panel_module.ControlPanelError("Text is required.")
        return {
            "filename": "sample.wav",
            "audio_url": "/audio/sample.wav",
            "bytes": 10,
            "sample_rate": 32000,
            "channels": 1,
            "format": "wav",
        }

    def resolve_audio_file(self, raw_name: str) -> Path:
        if raw_name != "sample.wav":
            raise panel_module.ControlPanelError("Audio file not found.")
        return self.audio_dir / "sample.wav"


def _controller(tmp_path: Path) -> Any:
    gsv_root = tmp_path / "local_assets" / "GPT-SoVITS-Inference"
    logs_dir = tmp_path / "local_assets" / "logs"
    output_dir = tmp_path / "diagnostics" / "tts"
    logs_dir.mkdir(parents=True)
    config = panel_module.ControlPanelConfig(
        repo_root=tmp_path,
        endpoint="http://127.0.0.1:5100",
        infer_config=tmp_path / "infer_config.json",
        gsv_root=gsv_root,
        output_dir=output_dir,
        logs_dir=logs_dir,
        pid_file=logs_dir / "gsvi-server.pid",
        character="琪亚娜E7",
    )
    return panel_module.TtsControlPanel(config)


def _get_json(url: str) -> Any:
    with urllib.request.urlopen(url, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))


def _post_json(url: str, payload: dict[str, Any]) -> Any:
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=5) as response:
        return json.loads(response.read().decode("utf-8"))
