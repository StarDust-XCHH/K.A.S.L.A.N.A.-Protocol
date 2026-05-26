"""Local browser control panel for safe GSVI TTS smoke tests."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import socket
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import unquote, urlparse
from urllib.request import Request, urlopen

from kaslana.adapters.tts.gpt_sovits import (
    GptSovitsError,
    GptSovitsTts,
    load_voice_profile_from_infer_config,
)
from kaslana.config.loader import load_env_file

DEFAULT_ENDPOINT = "http://127.0.0.1:5100"
DEFAULT_PANEL_HOST = "127.0.0.1"
DEFAULT_PANEL_PORT = 8765
DEFAULT_GSV_ROOT = Path("local_assets/GSVI-2.2.4-240318/GPT-SoVITS-Inference")
DEFAULT_OUTPUT_DIR = Path("diagnostics/tts/control_panel")


@dataclass(frozen=True)
class ControlPanelConfig:
    repo_root: Path
    endpoint: str
    infer_config: Path
    gsv_root: Path
    output_dir: Path
    logs_dir: Path
    pid_file: Path
    character: str
    tts_timeout_s: float = 60.0
    start_timeout_s: float = 180.0


class ControlPanelError(RuntimeError):
    """Raised for user-facing control panel failures."""


class TtsControlPanel:
    def __init__(self, config: ControlPanelConfig) -> None:
        self.config = config
        self.port = _port_from_endpoint(config.endpoint)

    def status(self) -> dict[str, Any]:
        pid = self._read_pid()
        process_info = self._read_process_info(pid) if pid is not None else None
        managed = process_info is not None and self._is_managed_process(process_info)
        running = self.is_endpoint_reachable()
        return {
            "running": running,
            "managed": managed,
            "endpoint": self.config.endpoint,
            "pid": pid if process_info is not None else None,
            "port": self.port,
            "logs": self._read_log_summary(),
        }

    def start_server(self) -> dict[str, Any]:
        if self.is_endpoint_reachable():
            status = self.status()
            status["message"] = "GSVI service is already reachable."
            return status

        runtime = self.config.gsv_root / "runtime" / "python.exe"
        backend = self.config.gsv_root / "Inference" / "src" / "tts_backend.py"
        if not runtime.exists():
            raise ControlPanelError(f"Missing GSVI runtime Python: {runtime}")
        if not backend.exists():
            raise ControlPanelError(f"Missing GSVI backend: {backend}")

        wrapper = self._write_backend_wrapper()
        self.config.logs_dir.mkdir(parents=True, exist_ok=True)
        stamp = time.strftime("%Y%m%d-%H%M%S")
        stdout_path = self.config.logs_dir / f"gsvi-{stamp}.stdout.log"
        stderr_path = self.config.logs_dir / f"gsvi-{stamp}.stderr.log"
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        stdout_file = stdout_path.open("w", encoding="utf-8", errors="replace")
        stderr_file = stderr_path.open("w", encoding="utf-8", errors="replace")
        try:
            process = subprocess.Popen(
                [str(runtime), str(wrapper)],
                cwd=self.config.gsv_root,
                stdout=stdout_file,
                stderr=stderr_file,
                creationflags=creationflags,
            )
        finally:
            stdout_file.close()
            stderr_file.close()

        self.config.pid_file.write_text(str(process.pid), encoding="ascii")
        deadline = time.monotonic() + self.config.start_timeout_s
        while time.monotonic() < deadline:
            if process.poll() is not None:
                raise ControlPanelError(
                    "GSVI backend exited before the endpoint became reachable. "
                    f"Check {stdout_path} and {stderr_path}."
                )
            if self.is_endpoint_reachable():
                status = self.status()
                status["message"] = "GSVI service started."
                return status
            time.sleep(2)
        raise ControlPanelError(
            "GSVI backend is still starting or blocked after "
            f"{int(self.config.start_timeout_s)} seconds. Check {stdout_path} and {stderr_path}."
        )

    def stop_server(self) -> dict[str, Any]:
        pid = self._read_pid()
        if pid is None:
            if self.is_endpoint_reachable():
                return {
                    "ok": False,
                    "message": (
                        "Port is reachable, but no project PID file exists. "
                        "Refusing to stop it."
                    ),
                    "status": self.status(),
                }
            return {"ok": True, "message": "GSVI service is not running.", "status": self.status()}

        process_info = self._read_process_info(pid)
        if process_info is None:
            self._remove_pid_file()
            if self.is_endpoint_reachable():
                return {
                    "ok": False,
                    "message": (
                        "PID is stale, but the port is still reachable. Refusing to stop it."
                    ),
                    "status": self.status(),
                }
            return {"ok": True, "message": "Removed stale PID file.", "status": self.status()}

        if not self._is_managed_process(process_info):
            return {
                "ok": False,
                "message": (
                    "PID file does not point to this project's GSVI process. "
                    "Refusing to stop it."
                ),
                "status": self.status(),
            }

        self._kill_process(pid)
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            if not self.is_endpoint_reachable():
                self._remove_pid_file()
                return {"ok": True, "message": "GSVI service stopped.", "status": self.status()}
            time.sleep(0.5)
        return {
            "ok": False,
            "message": "Stop was requested, but the endpoint is still reachable.",
            "status": self.status(),
        }

    def fetch_characters(self) -> dict[str, tuple[str, ...]]:
        request = Request(
            f"{self.config.endpoint.rstrip('/')}/character_list",
            headers={"Accept": "application/json"},
            method="GET",
        )
        try:
            with urlopen(request, timeout=5) as response:
                raw = json.loads(response.read().decode("utf-8"))
        except HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace").strip()
            suffix = f": {details}" if details else ""
            raise ControlPanelError(f"/character_list returned HTTP {exc.code}{suffix}") from exc
        except URLError as exc:
            raise ControlPanelError(f"GSVI endpoint is unreachable: {exc.reason}") from exc
        except json.JSONDecodeError as exc:
            raise ControlPanelError("/character_list did not return valid JSON") from exc
        return self._extract_characters(raw)

    def synthesize(self, payload: dict[str, Any]) -> dict[str, Any]:
        text = str(payload.get("text", "")).strip()
        if not text:
            raise ControlPanelError("Text is required.")

        character = str(payload.get("character") or self.config.character).strip()
        emotion = str(payload.get("emotion") or "default").strip()
        text_language = str(payload.get("text_language") or "auto").strip()
        speed = _float_param(payload, "speed", 1.0, min_value=0.25, max_value=2.0)
        top_k = _int_param(payload, "top_k", 5, min_value=1, max_value=100)
        top_p = _float_param(payload, "top_p", 1.0, min_value=0.05, max_value=1.0)
        temperature = _float_param(payload, "temperature", 1.0, min_value=0.05, max_value=2.0)

        characters = self.fetch_characters()
        if character not in characters:
            available = ", ".join(sorted(characters))
            raise ControlPanelError(f"Unknown character {character!r}. Available: {available}")
        emotions = characters[character]
        if emotions and emotion not in emotions:
            available = ", ".join(emotions)
            raise ControlPanelError(
                f"Unknown emotion {emotion!r} for {character!r}. Available: {available}"
            )

        profile = load_voice_profile_from_infer_config(self.config.infer_config, emotion=emotion)
        tts = GptSovitsTts(
            endpoint=self.config.endpoint,
            voice_profile=profile,
            timeout_s=self.config.tts_timeout_s,
            api_style="gsvi",
            character=character,
            emotion=emotion,
            text_language=text_language,
            text_split_method="auto_cut",
            speed_factor=speed,
            top_k=top_k,
            top_p=top_p,
            temperature=temperature,
        )
        audio = asyncio.run(tts.synthesize(text))

        self.config.output_dir.mkdir(parents=True, exist_ok=True)
        filename = f"{time.strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:8]}.wav"
        output_path = self.config.output_dir / filename
        output_path.write_bytes(audio.audio)
        return {
            "filename": filename,
            "audio_url": f"/audio/{filename}",
            "bytes": len(audio.audio),
            "sample_rate": audio.sample_rate,
            "channels": audio.channels,
            "format": audio.format,
        }

    def resolve_audio_file(self, raw_name: str) -> Path:
        name = unquote(raw_name)
        if "/" in name or "\\" in name or name in {"", ".", ".."}:
            raise ControlPanelError("Invalid audio filename.")
        if not name.lower().endswith(".wav"):
            raise ControlPanelError("Only WAV files can be served.")
        output_dir = self.config.output_dir.resolve()
        candidate = (output_dir / name).resolve()
        if candidate.parent != output_dir:
            raise ControlPanelError("Invalid audio path.")
        if not candidate.exists() or not candidate.is_file():
            raise ControlPanelError("Audio file not found.")
        return candidate

    def is_endpoint_reachable(self) -> bool:
        try:
            with socket.create_connection(("127.0.0.1", self.port), timeout=0.5):
                return True
        except OSError:
            return False

    def _write_backend_wrapper(self) -> Path:
        wrapper = self.config.gsv_root / ".kaslana_start_backend.py"
        wrapper.write_text(
            "\n".join(
                [
                    "from __future__ import annotations",
                    "",
                    "from pathlib import Path",
                    "import os",
                    "import sys",
                    "",
                    "root = Path(__file__).resolve().parent",
                    "os.chdir(root)",
                    'sys.path.insert(0, str(root / "Inference" / "src"))',
                    "",
                    "import tts_backend  # noqa: E402",
                    "",
                    'if __name__ == "__main__":',
                    f"    tts_backend.app.run(host='127.0.0.1', port={self.port})",
                    "",
                ]
            ),
            encoding="utf-8",
        )
        return wrapper

    def _read_pid(self) -> int | None:
        try:
            raw = self.config.pid_file.read_text(encoding="ascii").strip()
        except OSError:
            return None
        try:
            return int(raw)
        except ValueError:
            return None

    def _remove_pid_file(self) -> None:
        try:
            self.config.pid_file.unlink()
        except FileNotFoundError:
            return

    def _read_process_info(self, pid: int | None) -> dict[str, Any] | None:
        if pid is None:
            return None
        command = (
            "$p = Get-CimInstance Win32_Process -Filter \"ProcessId = "
            f"{pid}\"; "
            "if ($p) { [pscustomobject]@{"
            "ProcessId=$p.ProcessId; ExecutablePath=$p.ExecutablePath; "
            "CommandLine=$p.CommandLine} | ConvertTo-Json -Compress }"
        )
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", command],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            return None
        if result.returncode != 0 or not result.stdout.strip():
            return None
        try:
            raw = json.loads(result.stdout)
        except json.JSONDecodeError:
            return None
        if not isinstance(raw, dict):
            return None
        return raw

    def _is_managed_process(self, process_info: dict[str, Any]) -> bool:
        command_line = str(process_info.get("CommandLine") or "").lower()
        executable = str(process_info.get("ExecutablePath") or "").lower()
        root = str(self.config.gsv_root.resolve()).lower()
        return root in command_line or root in executable

    def _kill_process(self, pid: int) -> None:
        try:
            os.kill(pid, 15)
        except OSError as exc:
            raise ControlPanelError(f"Failed to stop process {pid}: {exc}") from exc

    def _read_log_summary(self) -> dict[str, str]:
        return {
            "stdout": self._tail_newest_log("*.stdout.log"),
            "stderr": self._tail_newest_log("*.stderr.log"),
        }

    def _tail_newest_log(self, pattern: str) -> str:
        try:
            candidates = sorted(
                self.config.logs_dir.glob(pattern),
                key=lambda path: path.stat().st_mtime,
                reverse=True,
            )
        except OSError:
            return ""
        if not candidates:
            return ""
        try:
            lines = candidates[0].read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            return ""
        return "\n".join(lines[-20:])[-4000:]

    def _extract_characters(self, raw: Any) -> dict[str, tuple[str, ...]]:
        if isinstance(raw, dict) and isinstance(raw.get("characters_and_emotions"), dict):
            raw = raw["characters_and_emotions"]
        if not isinstance(raw, dict):
            raise ControlPanelError("/character_list returned an unexpected JSON shape.")

        characters: dict[str, tuple[str, ...]] = {}
        for name, emotions in raw.items():
            if isinstance(emotions, list | tuple):
                characters[str(name)] = tuple(str(emotion) for emotion in emotions)
            else:
                characters[str(name)] = ()
        if not characters:
            raise ControlPanelError("/character_list returned no characters.")
        return characters


class ControlPanelRequestHandler(BaseHTTPRequestHandler):
    controller: TtsControlPanel

    @classmethod
    def create(cls, controller: TtsControlPanel) -> type[ControlPanelRequestHandler]:
        class BoundControlPanelRequestHandler(cls):
            pass

        BoundControlPanelRequestHandler.controller = controller
        return BoundControlPanelRequestHandler

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self._send_html(INDEX_HTML)
            return
        if parsed.path == "/api/status":
            self._send_json({"ok": True, "status": self.controller.status()})
            return
        if parsed.path == "/api/characters":
            self._handle_characters()
            return
        if parsed.path.startswith("/audio/"):
            self._handle_audio(parsed.path.removeprefix("/audio/"))
            return
        self._send_error_json(HTTPStatus.NOT_FOUND, "Not found.")

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path == "/api/start":
            self._call_json(self.controller.start_server)
            return
        if parsed.path == "/api/stop":
            self._handle_stop()
            return
        if parsed.path == "/api/synthesize":
            self._handle_synthesize()
            return
        self._send_error_json(HTTPStatus.NOT_FOUND, "Not found.")

    def log_message(self, format: str, *args: Any) -> None:
        return

    def _handle_characters(self) -> None:
        self._call_json(lambda: {"characters": self.controller.fetch_characters()})

    def _handle_stop(self) -> None:
        try:
            result = self.controller.stop_server()
        except ControlPanelError as exc:
            self._send_error_json(HTTPStatus.CONFLICT, str(exc))
            return
        status = HTTPStatus.OK if result.get("ok", True) else HTTPStatus.CONFLICT
        self._send_json({"ok": bool(result.get("ok", True)), **result}, status=status)

    def _handle_synthesize(self) -> None:
        try:
            payload = self._read_json_body()
            result = self.controller.synthesize(payload)
        except (ControlPanelError, GptSovitsError) as exc:
            self._send_error_json(HTTPStatus.BAD_REQUEST, str(exc))
            return
        self._send_json({"ok": True, "audio": result})

    def _handle_audio(self, raw_name: str) -> None:
        try:
            path = self.controller.resolve_audio_file(raw_name)
            data = path.read_bytes()
        except (ControlPanelError, OSError) as exc:
            self._send_error_json(HTTPStatus.NOT_FOUND, str(exc))
            return
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "audio/wav")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _call_json(self, callback: Any) -> None:
        try:
            result = callback()
        except (ControlPanelError, GptSovitsError) as exc:
            self._send_error_json(HTTPStatus.CONFLICT, str(exc))
            return
        self._send_json({"ok": True, **result})

    def _read_json_body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        if length <= 0:
            return {}
        raw = self.rfile.read(length).decode("utf-8")
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise ControlPanelError("Request body must be valid JSON.") from exc
        if not isinstance(payload, dict):
            raise ControlPanelError("Request body must be a JSON object.")
        return payload

    def _send_html(self, html: str) -> None:
        body = html.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, payload: dict[str, Any], *, status: HTTPStatus = HTTPStatus.OK) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _send_error_json(self, status: HTTPStatus, message: str) -> None:
        self._send_json({"ok": False, "error": message}, status=status)


def build_config(args: argparse.Namespace) -> ControlPanelConfig:
    repo_root = Path(__file__).resolve().parents[1]
    _load_local_env(repo_root)
    endpoint = args.endpoint or os.environ.get("KASLANA_TTS_ENDPOINT", DEFAULT_ENDPOINT)
    infer_config = Path(
        args.infer_config
        or os.environ.get("KASLANA_TTS_INFER_CONFIG", "assets/琪亚娜E7/琪亚娜E7/infer_config.json")
    )
    gsv_root = Path(args.gsv_root or DEFAULT_GSV_ROOT)
    output_dir = Path(args.output_dir or DEFAULT_OUTPUT_DIR)
    if not infer_config.is_absolute():
        infer_config = repo_root / infer_config
    if not gsv_root.is_absolute():
        gsv_root = repo_root / gsv_root
    if not output_dir.is_absolute():
        output_dir = repo_root / output_dir
    logs_dir = repo_root / "local_assets" / "logs"
    character = (
        args.character or os.environ.get("KASLANA_TTS_CHARACTER") or infer_config.parent.name
    )
    return ControlPanelConfig(
        repo_root=repo_root,
        endpoint=endpoint,
        infer_config=infer_config,
        gsv_root=gsv_root,
        output_dir=output_dir,
        logs_dir=logs_dir,
        pid_file=logs_dir / "gsvi-server.pid",
        character=character,
        tts_timeout_s=args.tts_timeout_s,
        start_timeout_s=args.start_timeout_s,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the local KASLANA TTS control panel.")
    parser.add_argument("--host", default=DEFAULT_PANEL_HOST, help="Control panel host.")
    parser.add_argument("--port", type=int, default=DEFAULT_PANEL_PORT, help="Control panel port.")
    parser.add_argument("--endpoint", help="GSVI endpoint, defaults to KASLANA_TTS_ENDPOINT.")
    parser.add_argument("--infer-config", help="Path to infer_config.json.")
    parser.add_argument("--gsv-root", help="Path to the local GSVI prepack root.")
    parser.add_argument("--output-dir", help="Directory for generated WAV files.")
    parser.add_argument("--character", help="Default GSVI character.")
    parser.add_argument("--tts-timeout-s", type=float, default=60.0, help="Synthesis timeout.")
    parser.add_argument("--start-timeout-s", type=float, default=180.0, help="Startup timeout.")
    return parser


def run_server(args: argparse.Namespace) -> None:
    if args.host != "127.0.0.1":
        raise SystemExit("The control panel must bind to 127.0.0.1.")
    config = build_config(args)
    controller = TtsControlPanel(config)
    handler = ControlPanelRequestHandler.create(controller)
    server = ThreadingHTTPServer((args.host, args.port), handler)
    print(f"TTS control panel: http://{args.host}:{args.port}")
    print(f"GSVI endpoint: {config.endpoint}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("Stopping TTS control panel.")
    finally:
        server.server_close()


def _load_local_env(repo_root: Path) -> None:
    env_path = repo_root / ".env"
    if env_path.exists():
        load_env_file(env_path)


def _port_from_endpoint(endpoint: str) -> int:
    parsed = urlparse(endpoint)
    if parsed.hostname not in {"127.0.0.1", "localhost"}:
        raise ControlPanelError("Only loopback GSVI endpoints are allowed.")
    if parsed.port is None:
        raise ControlPanelError("GSVI endpoint must include a port.")
    return parsed.port


def _int_param(
    payload: dict[str, Any],
    key: str,
    default: int,
    *,
    min_value: int,
    max_value: int,
) -> int:
    value = payload.get(key, default)
    try:
        parsed = int(value)
    except (TypeError, ValueError) as exc:
        raise ControlPanelError(f"{key} must be an integer.") from exc
    if parsed < min_value or parsed > max_value:
        raise ControlPanelError(f"{key} must be between {min_value} and {max_value}.")
    return parsed


def _float_param(
    payload: dict[str, Any],
    key: str,
    default: float,
    *,
    min_value: float,
    max_value: float,
) -> float:
    value = payload.get(key, default)
    try:
        parsed = float(value)
    except (TypeError, ValueError) as exc:
        raise ControlPanelError(f"{key} must be a number.") from exc
    if parsed < min_value or parsed > max_value:
        raise ControlPanelError(f"{key} must be between {min_value} and {max_value}.")
    return parsed


INDEX_HTML = r"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>KASLANA TTS Control Panel</title>
  <style>
    :root {
      color-scheme: light;
      --bg: #f5f7fa;
      --surface: #ffffff;
      --line: #d8dee8;
      --text: #18202f;
      --muted: #667085;
      --accent: #0f766e;
      --accent-strong: #115e59;
      --danger: #b42318;
      --warn: #b54708;
      --ok-bg: #dff8ee;
      --warn-bg: #fff3d6;
      --danger-bg: #fde5e2;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      min-height: 100vh;
      background: var(--bg);
      color: var(--text);
      font-family: "Microsoft YaHei", "Segoe UI", Arial, sans-serif;
      letter-spacing: 0;
    }
    .app {
      display: grid;
      grid-template-columns: 320px minmax(0, 1fr);
      min-height: 100vh;
    }
    aside {
      background: #202936;
      color: #f8fafc;
      padding: 24px;
    }
    main {
      padding: 24px;
      display: grid;
      grid-template-columns: minmax(320px, 520px) minmax(320px, 1fr);
      gap: 20px;
      align-content: start;
    }
    h1, h2 {
      margin: 0;
      font-weight: 700;
      line-height: 1.2;
    }
    h1 { font-size: 24px; }
    h2 { font-size: 17px; }
    .subtitle {
      margin: 8px 0 24px;
      color: #cbd5e1;
      line-height: 1.5;
      font-size: 14px;
    }
    .panel {
      background: var(--surface);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 18px;
    }
    .stack { display: grid; gap: 14px; }
    .row {
      display: flex;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
    }
    .field { display: grid; gap: 7px; }
    label {
      color: #344054;
      font-size: 13px;
      font-weight: 600;
    }
    input, select, textarea {
      width: 100%;
      border: 1px solid #cfd6e2;
      border-radius: 7px;
      background: #ffffff;
      color: var(--text);
      font: inherit;
      min-height: 38px;
      padding: 9px 10px;
    }
    textarea {
      min-height: 132px;
      resize: vertical;
      line-height: 1.5;
    }
    button {
      min-height: 38px;
      border: 1px solid transparent;
      border-radius: 7px;
      padding: 8px 12px;
      font: inherit;
      font-weight: 700;
      cursor: pointer;
      background: #eef2f7;
      color: #202936;
    }
    button.primary {
      background: var(--accent);
      color: #ffffff;
    }
    button.primary:hover { background: var(--accent-strong); }
    button.danger {
      background: var(--danger);
      color: #ffffff;
    }
    button:disabled {
      cursor: wait;
      opacity: 0.65;
    }
    .status {
      display: inline-flex;
      align-items: center;
      min-height: 28px;
      padding: 4px 9px;
      border-radius: 999px;
      font-size: 13px;
      font-weight: 700;
      color: #1d2939;
      background: var(--warn-bg);
    }
    .status.running { background: var(--ok-bg); color: #05603a; }
    .status.stopped { background: var(--danger-bg); color: var(--danger); }
    .meta {
      display: grid;
      gap: 9px;
      margin-top: 18px;
      color: #d7dee9;
      font-size: 13px;
      overflow-wrap: anywhere;
    }
    .meta strong { color: #ffffff; }
    .message {
      min-height: 28px;
      border-left: 3px solid var(--accent);
      padding: 6px 10px;
      color: #344054;
      background: #eef8f7;
      font-size: 13px;
      line-height: 1.45;
    }
    .message.error {
      border-color: var(--danger);
      background: var(--danger-bg);
      color: var(--danger);
    }
    details {
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 10px 12px;
    }
    summary {
      cursor: pointer;
      font-weight: 700;
      color: #344054;
    }
    .grid-2 {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 12px;
      margin-top: 12px;
    }
    audio {
      width: 100%;
      margin-top: 12px;
    }
    pre {
      white-space: pre-wrap;
      overflow-wrap: anywhere;
      margin: 8px 0 0;
      padding: 10px;
      max-height: 220px;
      overflow: auto;
      background: #101828;
      color: #e4e7ec;
      border-radius: 7px;
      font-size: 12px;
      line-height: 1.45;
    }
    .result {
      border-top: 1px solid var(--line);
      padding-top: 12px;
      color: #344054;
      font-size: 14px;
      line-height: 1.6;
    }
    @media (max-width: 920px) {
      .app, main {
        grid-template-columns: 1fr;
      }
      aside { padding: 20px; }
      main { padding: 16px; }
    }
  </style>
</head>
<body>
  <div class="app">
    <aside>
      <h1>KASLANA TTS</h1>
      <p class="subtitle">本地 GSVI 试音控制台</p>
      <div class="row">
        <span id="statusPill" class="status">checking</span>
      </div>
      <div class="meta">
        <div><strong>Endpoint</strong><br><span id="endpointText">-</span></div>
        <div><strong>PID</strong><br><span id="pidText">-</span></div>
        <div><strong>Port</strong><br><span id="portText">-</span></div>
      </div>
      <div class="row" style="margin-top: 22px;">
        <button id="startBtn" class="primary">启动服务</button>
        <button id="stopBtn" class="danger">关闭服务</button>
        <button id="refreshBtn">刷新</button>
      </div>
    </aside>
    <main>
      <section class="panel stack">
        <h2>合成测试</h2>
        <div id="message" class="message">正在读取服务状态。</div>
        <div class="grid-2">
          <div class="field">
            <label for="character">角色</label>
            <select id="character"></select>
          </div>
          <div class="field">
            <label for="emotion">Emotion</label>
            <select id="emotion"></select>
          </div>
        </div>
        <div class="field">
          <label for="language">语言</label>
          <select id="language">
            <option value="auto">auto</option>
            <option value="zh">zh</option>
            <option value="en">en</option>
            <option value="ja">ja</option>
          </select>
        </div>
        <div class="field">
          <label for="text">测试语句</label>
          <textarea id="text">早安呀，该起床啦。今天也要元气满满哦。</textarea>
        </div>
        <details>
          <summary>高级参数</summary>
          <div class="grid-2">
            <div class="field">
              <label for="speed">Speed</label>
              <input id="speed" type="number" min="0.25" max="2" step="0.05" value="1">
            </div>
            <div class="field">
              <label for="topK">Top K</label>
              <input id="topK" type="number" min="1" max="100" step="1" value="5">
            </div>
            <div class="field">
              <label for="topP">Top P</label>
              <input id="topP" type="number" min="0.05" max="1" step="0.05" value="1">
            </div>
            <div class="field">
              <label for="temperature">Temperature</label>
              <input id="temperature" type="number" min="0.05" max="2" step="0.05" value="1">
            </div>
          </div>
        </details>
        <div class="row">
          <button id="synthBtn" class="primary">生成音频</button>
        </div>
      </section>
      <section class="panel stack">
        <h2>输出</h2>
        <div id="result" class="result">还没有生成音频。</div>
        <audio id="player" controls hidden></audio>
        <details>
          <summary>最近日志</summary>
          <pre id="logs">-</pre>
        </details>
      </section>
    </main>
  </div>
  <script>
    const els = {
      statusPill: document.getElementById("statusPill"),
      endpointText: document.getElementById("endpointText"),
      pidText: document.getElementById("pidText"),
      portText: document.getElementById("portText"),
      startBtn: document.getElementById("startBtn"),
      stopBtn: document.getElementById("stopBtn"),
      refreshBtn: document.getElementById("refreshBtn"),
      synthBtn: document.getElementById("synthBtn"),
      character: document.getElementById("character"),
      emotion: document.getElementById("emotion"),
      language: document.getElementById("language"),
      text: document.getElementById("text"),
      speed: document.getElementById("speed"),
      topK: document.getElementById("topK"),
      topP: document.getElementById("topP"),
      temperature: document.getElementById("temperature"),
      message: document.getElementById("message"),
      result: document.getElementById("result"),
      player: document.getElementById("player"),
      logs: document.getElementById("logs")
    };
    let characters = {};

    async function api(path, options = {}) {
      const response = await fetch(path, {
        headers: {"Content-Type": "application/json"},
        ...options
      });
      const payload = await response.json();
      if (!response.ok || payload.ok === false) {
        throw new Error(payload.error || payload.message || "Request failed");
      }
      return payload;
    }

    function setBusy(isBusy) {
      [els.startBtn, els.stopBtn, els.refreshBtn, els.synthBtn].forEach((button) => {
        button.disabled = isBusy;
      });
    }

    function say(text, isError = false) {
      els.message.textContent = text;
      els.message.classList.toggle("error", isError);
    }

    function renderStatus(status) {
      els.statusPill.textContent = status.running ? "running" : "stopped";
      els.statusPill.className = "status " + (status.running ? "running" : "stopped");
      els.endpointText.textContent = status.endpoint || "-";
      els.pidText.textContent = status.pid || (status.running ? "external" : "-");
      els.portText.textContent = status.port || "-";
      const stdout = status.logs && status.logs.stdout ? status.logs.stdout : "";
      const stderr = status.logs && status.logs.stderr ? status.logs.stderr : "";
      els.logs.textContent = [stdout, stderr].filter(Boolean).join("\n\n--- stderr ---\n") || "-";
    }

    function renderCharacters(data) {
      characters = data || {};
      const names = Object.keys(characters);
      els.character.innerHTML = "";
      names.forEach((name) => {
        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        els.character.appendChild(option);
      });
      if (names.includes("琪亚娜E7")) {
        els.character.value = "琪亚娜E7";
      }
      renderEmotions();
    }

    function renderEmotions() {
      const selected = els.character.value;
      const emotions = characters[selected] || [];
      els.emotion.innerHTML = "";
      emotions.forEach((name) => {
        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        els.emotion.appendChild(option);
      });
      if (emotions.includes("default")) {
        els.emotion.value = "default";
      }
    }

    async function refresh() {
      setBusy(true);
      try {
        const statusPayload = await api("/api/status");
        renderStatus(statusPayload.status);
        if (statusPayload.status.running) {
          const chars = await api("/api/characters");
          renderCharacters(chars.characters);
          say("服务在线，可以合成测试音频。");
        } else {
          renderCharacters({});
          say("服务未启动。");
        }
      } catch (error) {
        say(error.message, true);
      } finally {
        setBusy(false);
      }
    }

    async function startServer() {
      setBusy(true);
      say("正在启动 GSVI 服务。");
      try {
        const payload = await api("/api/start", {method: "POST", body: "{}"});
        renderStatus(payload);
        say(payload.message || "服务已启动。");
        await refresh();
      } catch (error) {
        say(error.message, true);
      } finally {
        setBusy(false);
      }
    }

    async function stopServer() {
      setBusy(true);
      say("正在关闭 GSVI 服务。");
      try {
        const payload = await api("/api/stop", {method: "POST", body: "{}"});
        renderStatus(payload.status || {});
        say(payload.message || "服务已关闭。");
        await refresh();
      } catch (error) {
        say(error.message, true);
        await refresh();
      } finally {
        setBusy(false);
      }
    }

    async function synthesize() {
      setBusy(true);
      say("正在合成音频。");
      try {
        const payload = await api("/api/synthesize", {
          method: "POST",
          body: JSON.stringify({
            character: els.character.value,
            emotion: els.emotion.value,
            text_language: els.language.value,
            text: els.text.value,
            speed: els.speed.value,
            top_k: els.topK.value,
            top_p: els.topP.value,
            temperature: els.temperature.value
          })
        });
        const audio = payload.audio;
        els.result.textContent = [
          audio.filename,
          `${audio.bytes} bytes`,
          `${audio.sample_rate} Hz`,
          `${audio.channels} channel(s)`
        ].join(" · ");
        els.player.src = audio.audio_url + "?t=" + Date.now();
        els.player.hidden = false;
        els.player.load();
        say("音频已生成。");
      } catch (error) {
        say(error.message, true);
      } finally {
        setBusy(false);
      }
    }

    els.character.addEventListener("change", renderEmotions);
    els.refreshBtn.addEventListener("click", refresh);
    els.startBtn.addEventListener("click", startServer);
    els.stopBtn.addEventListener("click", stopServer);
    els.synthBtn.addEventListener("click", synthesize);
    refresh();
  </script>
</body>
</html>
"""


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    try:
        run_server(args)
    except ControlPanelError as exc:
        raise SystemExit(str(exc)) from exc


if __name__ == "__main__":
    sys.exit(main())
