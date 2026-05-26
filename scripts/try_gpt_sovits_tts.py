"""Generate one local GPT-SoVITS test WAV without touching WeChat."""

from __future__ import annotations

import argparse
import asyncio
import os
from pathlib import Path

from kaslana.adapters.tts.gpt_sovits import (
    GptSovitsError,
    GptSovitsTts,
    list_infer_config_emotions,
    load_voice_profile_from_infer_config,
)
from kaslana.config.loader import load_env_file


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Call a local GPT-SoVITS HTTP service and save one test WAV.",
    )
    parser.add_argument(
        "--infer-config",
        type=Path,
        default=_path_from_env("KASLANA_TTS_INFER_CONFIG"),
        help="Path to infer_config.json, or set KASLANA_TTS_INFER_CONFIG.",
    )
    parser.add_argument(
        "--api-style",
        choices=("official", "gsvi"),
        default=os.environ.get("KASLANA_TTS_API_STYLE", "official"),
        help="API payload style: official GPT-SoVITS api_v2 or GSVI/TTS-for-GPT-SoVITS.",
    )
    parser.add_argument(
        "--endpoint",
        default=os.environ.get("KASLANA_TTS_ENDPOINT"),
        help="Local TTS endpoint. Defaults to 9880 for official or 5100 for gsvi.",
    )
    parser.add_argument(
        "--character",
        default=os.environ.get("KASLANA_TTS_CHARACTER"),
        help="GSVI character name. Defaults to the infer_config parent folder name.",
    )
    parser.add_argument(
        "--emotion",
        default=os.environ.get("KASLANA_TTS_EMOTION", "default"),
        help="Emotion/reference key inside infer_config.json.",
    )
    parser.add_argument(
        "--text",
        default="早安，该起床啦。今天也要元气满满哦。",
        help="Text to synthesize.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=_path_from_env("KASLANA_TTS_OUTPUT")
        or Path("diagnostics/tts/kiana_test.wav"),
        help="Output WAV path. Defaults to diagnostics/tts/kiana_test.wav.",
    )
    parser.add_argument(
        "--timeout-s",
        type=float,
        default=float(os.environ.get("KASLANA_TTS_TIMEOUT_S", "60")),
        help="HTTP timeout in seconds.",
    )
    parser.add_argument(
        "--list-emotions",
        action="store_true",
        help="List infer_config emotion keys and exit.",
    )
    parser.add_argument(
        "--skip-weight-switch",
        action="store_true",
        help="Do not call set_gpt_weights or set_sovits_weights before synthesis.",
    )
    return parser


def main() -> None:
    _load_local_env()
    parser = build_parser()
    args = parser.parse_args()
    if args.infer_config is None:
        parser.error("--infer-config is required unless KASLANA_TTS_INFER_CONFIG is set.")

    if args.list_emotions:
        for emotion in list_infer_config_emotions(args.infer_config):
            print(emotion)
        return

    try:
        asyncio.run(_run(args))
    except GptSovitsError as exc:
        raise SystemExit(f"TTS failed: {exc}") from exc


async def _run(args: argparse.Namespace) -> None:
    profile = load_voice_profile_from_infer_config(args.infer_config, emotion=args.emotion)
    tts = GptSovitsTts(
        endpoint=_resolve_endpoint(args),
        voice_profile=profile,
        timeout_s=args.timeout_s,
        api_style=args.api_style,
        character=args.character,
        emotion=args.emotion,
    )

    if args.api_style == "official" and not args.skip_weight_switch:
        await tts.load_weights()

    audio = await tts.synthesize(args.text)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(audio.audio)

    print(f"Wrote {args.output}")
    print(
        "Audio: "
        f"{len(audio.audio)} bytes, {audio.sample_rate} Hz, "
        f"{audio.channels} channel(s), format={audio.format}"
    )


def _path_from_env(name: str) -> Path | None:
    value = os.environ.get(name)
    if not value:
        return None
    return Path(value)


def _resolve_endpoint(args: argparse.Namespace) -> str:
    if args.endpoint:
        return args.endpoint
    if args.api_style == "gsvi":
        return "http://127.0.0.1:5100"
    return "http://127.0.0.1:9880"


def _load_local_env() -> None:
    env_path = Path(".env")
    if env_path.exists():
        load_env_file(env_path)


if __name__ == "__main__":
    main()
