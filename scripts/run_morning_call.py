"""Placeholder runner for the future scheduled morning call."""

from __future__ import annotations

import argparse
from pathlib import Path

from kaslana.config.loader import load_config


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=Path("config/config.example.yaml"))
    args = parser.parse_args()

    config = load_config(args.config)
    print(f"Loaded {config.project.name}.")
    print("Real morning-call execution will be enabled after adapters are implemented.")


if __name__ == "__main__":
    main()
