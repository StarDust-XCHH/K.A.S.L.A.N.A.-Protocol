"""CLI skeleton for the nightly offline dialogue pre-rendering job."""

from __future__ import annotations

import argparse
from datetime import date
from pathlib import Path

from kaslana.config.loader import load_config


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=Path("config/config.example.yaml"))
    parser.add_argument("--date", type=date.fromisoformat, default=date.today())
    return parser


def main() -> None:
    args = build_parser().parse_args()
    config = load_config(args.config)
    print(
        "Loaded nightly preprocess config for "
        f"{config.project.name} on {args.date.isoformat()}."
    )
    print("Adapter factory and real LLM/TTS dependencies are not implemented yet.")


if __name__ == "__main__":
    main()
