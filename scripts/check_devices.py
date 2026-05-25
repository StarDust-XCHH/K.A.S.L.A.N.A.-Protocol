"""Print configured physical-device targets without touching WeChat."""

from __future__ import annotations

import argparse
from pathlib import Path

from kaslana.config.loader import load_config


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=Path("config/config.example.yaml"))
    args = parser.parse_args()

    config = load_config(args.config)
    print("Configured Android device:", config.automation.android_device_id)
    print("WeChat package:", config.automation.wechat.package_name)
    print("Target contact alias:", config.automation.wechat.target_contact_alias)
    print("This architecture-stage script does not open WeChat or dial calls.")


if __name__ == "__main__":
    main()
