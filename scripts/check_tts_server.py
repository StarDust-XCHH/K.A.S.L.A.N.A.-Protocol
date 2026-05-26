"""Check a local GSVI TTS server without touching WeChat or audio playback."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from kaslana.adapters.tts.gpt_sovits import (
    GptSovitsError,
    GptSovitsTts,
    load_voice_profile_from_infer_config,
)
from kaslana.config.loader import load_env_file


def build_parser() -> argparse.ArgumentParser:
    infer_config = _path_from_env("KASLANA_TTS_INFER_CONFIG")
    parser = argparse.ArgumentParser(
        description="Check a local GSVI / TTS-for-GPT-SoVITS endpoint.",
    )
    parser.add_argument(
        "--endpoint",
        default=os.environ.get("KASLANA_TTS_ENDPOINT", "http://127.0.0.1:5100"),
        help="Local GSVI endpoint.",
    )
    parser.add_argument(
        "--infer-config",
        type=Path,
        default=infer_config,
        help="Path to infer_config.json, or set KASLANA_TTS_INFER_CONFIG.",
    )
    parser.add_argument(
        "--character",
        default=os.environ.get("KASLANA_TTS_CHARACTER") or _character_from_config(infer_config),
        help="Character expected in /character_list.",
    )
    parser.add_argument(
        "--emotion",
        default=os.environ.get("KASLANA_TTS_EMOTION", "default"),
        help="Emotion to check or synthesize.",
    )
    parser.add_argument(
        "--timeout-s",
        type=float,
        default=float(os.environ.get("KASLANA_TTS_HEALTH_TIMEOUT_S", "5")),
        help="HTTP timeout in seconds.",
    )
    parser.add_argument(
        "--synthesize",
        action="store_true",
        help="Also synthesize one short WAV to diagnostics/tts.",
    )
    parser.add_argument(
        "--text",
        default="早安。",
        help="Short text used with --synthesize.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=_path_from_env("KASLANA_TTS_HEALTH_OUTPUT")
        or Path("diagnostics/tts/kiana_health.wav"),
        help="Output WAV used with --synthesize.",
    )
    return parser


def main() -> None:
    _load_local_env()
    args = build_parser().parse_args()
    endpoint = args.endpoint.rstrip("/")

    try:
        characters = fetch_character_list(endpoint, args.timeout_s)
        print(f"Endpoint reachable: {endpoint}")
        print("Characters:")
        for name, emotions in characters.items():
            emotion_text = ", ".join(emotions) if emotions else "(no emotions listed)"
            print(f"- {name}: {emotion_text}")

        if args.character:
            _require_character(characters, args.character, args.emotion)

        if args.synthesize:
            if args.infer_config is None:
                raise GptSovitsError("--infer-config is required with --synthesize.")
            asyncio.run(_synthesize(args, endpoint))
    except (GptSovitsError, TtsServerCheckError) as exc:
        raise SystemExit(f"TTS server check failed: {exc}") from exc


def fetch_character_list(endpoint: str, timeout_s: float) -> dict[str, tuple[str, ...]]:
    request = Request(
        f"{endpoint.rstrip('/')}/character_list",
        headers={"Accept": "application/json"},
        method="GET",
    )
    try:
        with urlopen(request, timeout=timeout_s) as response:
            raw = json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        details = exc.read().decode("utf-8", errors="replace").strip()
        suffix = f": {details}" if details else ""
        raise TtsServerCheckError(f"/character_list returned HTTP {exc.code}{suffix}") from exc
    except URLError as exc:
        raise TtsServerCheckError(f"endpoint is unreachable: {exc.reason}") from exc
    except json.JSONDecodeError as exc:
        raise TtsServerCheckError("/character_list did not return valid JSON") from exc

    return _extract_characters(raw)


async def _synthesize(args: argparse.Namespace, endpoint: str) -> None:
    profile = load_voice_profile_from_infer_config(args.infer_config, emotion=args.emotion)
    tts = GptSovitsTts(
        endpoint=endpoint,
        voice_profile=profile,
        timeout_s=max(args.timeout_s, 30.0),
        api_style="gsvi",
        character=args.character,
        emotion=args.emotion,
        text_split_method="auto_cut",
    )
    audio = await tts.synthesize(args.text)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(audio.audio)
    print(f"Wrote {args.output}")
    print(
        "Audio: "
        f"{len(audio.audio)} bytes, {audio.sample_rate} Hz, "
        f"{audio.channels} channel(s), format={audio.format}"
    )


def _extract_characters(raw: Any) -> dict[str, tuple[str, ...]]:
    if isinstance(raw, dict) and isinstance(raw.get("characters_and_emotions"), dict):
        raw = raw["characters_and_emotions"]
    if not isinstance(raw, dict):
        raise TtsServerCheckError("/character_list returned an unexpected JSON shape")

    characters: dict[str, tuple[str, ...]] = {}
    for name, emotions in raw.items():
        if isinstance(emotions, list | tuple):
            characters[str(name)] = tuple(str(emotion) for emotion in emotions)
        else:
            characters[str(name)] = ()
    if not characters:
        raise TtsServerCheckError("/character_list returned no characters")
    return characters


def _require_character(
    characters: dict[str, tuple[str, ...]],
    character: str,
    emotion: str,
) -> None:
    if character not in characters:
        available = ", ".join(sorted(characters))
        raise TtsServerCheckError(f"missing character {character!r}; available: {available}")
    emotions = characters[character]
    if emotions and emotion not in emotions:
        available = ", ".join(emotions)
        raise TtsServerCheckError(
            f"missing emotion {emotion!r} for {character!r}; available: {available}"
        )


def _path_from_env(name: str) -> Path | None:
    value = os.environ.get(name)
    if not value:
        return None
    return Path(value)


def _character_from_config(infer_config: Path | None) -> str | None:
    if infer_config is None:
        return None
    return infer_config.expanduser().resolve().parent.name


def _load_local_env() -> None:
    env_path = Path(".env")
    if env_path.exists():
        load_env_file(env_path)


class TtsServerCheckError(RuntimeError):
    """Raised when the GSVI health check fails."""


if __name__ == "__main__":
    main()
