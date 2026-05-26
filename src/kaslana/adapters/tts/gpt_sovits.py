"""GPT-SoVITS HTTP TTS adapter."""

from __future__ import annotations

import asyncio
import json
import re
import wave
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from kaslana.ports.tts import TtsAudio, TtsPort


class GptSovitsError(RuntimeError):
    """Raised when a GPT-SoVITS request or response is invalid."""


@dataclass(frozen=True)
class GptSovitsVoiceProfile:
    """Resolved voice assets used by the GPT-SoVITS API."""

    root_dir: Path
    reference_audio_path: Path
    prompt_text: str
    prompt_language: str
    gpt_path: Path | None = None
    sovits_path: Path | None = None


class GptSovitsTts(TtsPort):
    """Adapter for a local GPT-SoVITS HTTP service.

    The adapter intentionally talks only to a local HTTP endpoint. It does not
    start model processes, play audio, or interact with WeChat.
    """

    def __init__(
        self,
        endpoint: str = "http://127.0.0.1:9880",
        *,
        voice_profile: GptSovitsVoiceProfile | None = None,
        timeout_s: float = 60.0,
        text_language: str = "zh",
        text_split_method: str = "cut5",
        media_type: str = "wav",
        api_style: str = "official",
        character: str | None = None,
        emotion: str = "default",
        top_k: int = 5,
        top_p: float = 1.0,
        temperature: float = 1.0,
        speed_factor: float = 1.0,
        parallel_infer: bool = True,
        repetition_penalty: float = 1.35,
    ) -> None:
        self.endpoint = endpoint.rstrip("/")
        self.voice_profile = voice_profile
        self.timeout_s = timeout_s
        self.text_language = _normalize_language(text_language)
        self.text_split_method = text_split_method
        self.media_type = media_type
        self.api_style = api_style
        self.character = character
        self.emotion = emotion
        self.top_k = top_k
        self.top_p = top_p
        self.temperature = temperature
        self.speed_factor = speed_factor
        self.parallel_infer = parallel_infer
        self.repetition_penalty = repetition_penalty
        if self.api_style not in {"official", "gsvi"}:
            raise GptSovitsError("api_style must be 'official' or 'gsvi'.")

    async def synthesize(self, text: str) -> TtsAudio:
        if self.voice_profile is None:
            raise GptSovitsError("GPT-SoVITS voice profile is required before synthesis.")

        normalized_text = normalize_tts_text(text)
        if not normalized_text:
            raise GptSovitsError("TTS text is empty after normalization.")

        payload = self._build_payload(normalized_text)
        audio = await asyncio.to_thread(self._post_json, "tts", payload)
        if not audio:
            raise GptSovitsError("GPT-SoVITS returned an empty audio response.")

        sample_rate, channels = _read_wav_info(audio)
        return TtsAudio(
            audio=audio,
            sample_rate=sample_rate,
            channels=channels,
            format=self.media_type,
        )

    async def load_weights(self) -> None:
        """Ask a compatible GPT-SoVITS service to switch to this voice profile."""

        if self.voice_profile is None:
            raise GptSovitsError("GPT-SoVITS voice profile is required before loading weights.")
        if self.api_style == "gsvi":
            return

        if self.voice_profile.gpt_path is not None:
            await asyncio.to_thread(
                self._get_query,
                "set_gpt_weights",
                {"weights_path": str(self.voice_profile.gpt_path)},
            )
        if self.voice_profile.sovits_path is not None:
            await asyncio.to_thread(
                self._get_query,
                "set_sovits_weights",
                {"weights_path": str(self.voice_profile.sovits_path)},
            )

    def _build_payload(self, text: str) -> dict[str, Any]:
        if self.voice_profile is None:
            raise GptSovitsError("GPT-SoVITS voice profile is required before synthesis.")

        if self.api_style == "gsvi":
            character = self.character or self.voice_profile.root_dir.name
            return {
                "text": text,
                "text_language": self.text_language,
                "character": character,
                "cha_name": character,
                "emotion": self.emotion,
                "character_emotion": self.emotion,
                "format": self.media_type,
                "stream": False,
                "save_temp": False,
                "batch_size": 1,
                "speed": self.speed_factor,
                "speed_factor": self.speed_factor,
                "top_k": self.top_k,
                "top_p": self.top_p,
                "temperature": self.temperature,
                "cut_method": self.text_split_method,
            }

        return {
            "text": text,
            "text_lang": self.text_language,
            "ref_audio_path": str(self.voice_profile.reference_audio_path),
            "prompt_text": self.voice_profile.prompt_text,
            "prompt_lang": self.voice_profile.prompt_language,
            "text_split_method": self.text_split_method,
            "batch_size": 1,
            "media_type": self.media_type,
            "streaming_mode": False,
            "top_k": self.top_k,
            "top_p": self.top_p,
            "temperature": self.temperature,
            "speed_factor": self.speed_factor,
            "parallel_infer": self.parallel_infer,
            "repetition_penalty": self.repetition_penalty,
        }

    def _post_json(self, route: str, payload: dict[str, Any]) -> bytes:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request = Request(
            self._url_for(route),
            data=body,
            headers={
                "Accept": "audio/wav",
                "Content-Type": "application/json; charset=utf-8",
            },
            method="POST",
        )
        return self._open(request)

    def _get_query(self, route: str, params: dict[str, str]) -> bytes:
        request = Request(
            f"{self._url_for(route)}?{urlencode(params)}",
            method="GET",
        )
        return self._open(request)

    def _open(self, request: Request) -> bytes:
        try:
            with urlopen(request, timeout=self.timeout_s) as response:
                return response.read()
        except HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace").strip()
            suffix = f": {details}" if details else ""
            raise GptSovitsError(f"GPT-SoVITS HTTP {exc.code}{suffix}") from exc
        except URLError as exc:
            raise GptSovitsError(f"GPT-SoVITS endpoint is unreachable: {exc.reason}") from exc

    def _url_for(self, route: str) -> str:
        return f"{self.endpoint}/{route.lstrip('/')}"


def load_voice_profile_from_infer_config(
    infer_config_path: Path,
    *,
    emotion: str = "default",
) -> GptSovitsVoiceProfile:
    """Load the small voice profile used by TTS-for-GPT-SoVITS config files."""

    resolved_config = infer_config_path.expanduser().resolve()
    try:
        raw = json.loads(resolved_config.read_text(encoding="utf-8"))
    except OSError as exc:
        raise GptSovitsError(f"Cannot read infer config: {resolved_config}") from exc
    except json.JSONDecodeError as exc:
        raise GptSovitsError(f"Invalid infer config JSON: {resolved_config}") from exc

    emotion_list = raw.get("emotion_list")
    if not isinstance(emotion_list, dict) or not emotion_list:
        raise GptSovitsError("infer_config.json must contain a non-empty emotion_list mapping.")

    selected = emotion_list.get(emotion)
    if not isinstance(selected, dict):
        available = ", ".join(sorted(str(name) for name in emotion_list))
        raise GptSovitsError(f"Unknown emotion {emotion!r}. Available emotions: {available}")

    root_dir = resolved_config.parent
    reference_audio_path = _resolve_profile_path(
        root_dir,
        _required_str(selected, "ref_wav_path"),
    )
    prompt_text = _required_str(selected, "prompt_text")
    prompt_language = _normalize_language(_required_str(selected, "prompt_language"))

    gpt_path = _optional_profile_path(root_dir, raw.get("gpt_path"))
    sovits_path = _optional_profile_path(root_dir, raw.get("sovits_path"))

    return GptSovitsVoiceProfile(
        root_dir=root_dir,
        reference_audio_path=reference_audio_path,
        prompt_text=prompt_text,
        prompt_language=prompt_language,
        gpt_path=gpt_path,
        sovits_path=sovits_path,
    )


def list_infer_config_emotions(infer_config_path: Path) -> tuple[str, ...]:
    resolved_config = infer_config_path.expanduser().resolve()
    raw = json.loads(resolved_config.read_text(encoding="utf-8"))
    emotion_list = raw.get("emotion_list")
    if not isinstance(emotion_list, dict):
        raise GptSovitsError("infer_config.json must contain an emotion_list mapping.")
    return tuple(sorted(str(name) for name in emotion_list))


def normalize_tts_text(text: str) -> str:
    """Lightly clean assistant text before sending it to speech synthesis."""

    lines: list[str] = []
    in_code_block = False
    for raw_line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = raw_line.strip()
        if line.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue
        line = re.sub(r"^[-*+]\s+", "", line)
        line = re.sub(r"^\d+[.)]\s+", "", line)
        line = line.replace("`", "")
        if line:
            lines.append(line)
    return re.sub(r"\s+", " ", " ".join(lines)).strip()


def _read_wav_info(audio: bytes) -> tuple[int, int]:
    try:
        with wave.open(BytesIO(audio), "rb") as wav_file:
            return wav_file.getframerate(), wav_file.getnchannels()
    except wave.Error as exc:
        raise GptSovitsError("GPT-SoVITS response is not a valid WAV file.") from exc


def _required_str(raw: dict[str, Any], key: str) -> str:
    value = raw.get(key)
    if not isinstance(value, str) or not value:
        raise GptSovitsError(f"infer_config.json missing non-empty string: {key}")
    return value


def _optional_profile_path(root_dir: Path, value: Any) -> Path | None:
    if not isinstance(value, str) or not value:
        return None
    return _resolve_profile_path(root_dir, value)


def _resolve_profile_path(root_dir: Path, value: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        path = root_dir / path
    return path.resolve()


def _normalize_language(language: str) -> str:
    aliases = {
        "中文": "zh",
        "汉语": "zh",
        "普通话": "zh",
        "英文": "en",
        "英语": "en",
        "日文": "ja",
        "日语": "ja",
        "韩文": "ko",
        "韩语": "ko",
        "粤语": "yue",
    }
    return aliases.get(language.strip(), language.strip())
