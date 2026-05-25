"""Command-line entrypoint for architecture checks."""

from __future__ import annotations

import argparse
from pathlib import Path

from kaslana.config.loader import load_config


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="kaslana")
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("config/config.example.yaml"),
        help="Path to the YAML configuration file.",
    )
    parser.add_argument(
        "--check-config",
        action="store_true",
        help="Load configuration and print a short validation summary.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    config = load_config(args.config)

    if args.check_config:
        print(
            "Loaded config for "
            f"{config.project.name} "
            f"targeting {config.automation.wechat.target_contact_alias!r}."
        )
        return

    print("K.A.S.L.A.N.A. architecture package is installed.")
    print("Use --check-config to validate the current configuration file.")


if __name__ == "__main__":
    main()
