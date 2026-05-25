"""List sounddevice devices when the optional runtime dependency is installed."""

from __future__ import annotations


def main() -> None:
    try:
        import sounddevice as sd
    except ImportError:
        print("sounddevice is not installed. Install the future audio adapter dependencies first.")
        return

    print(sd.query_devices())


if __name__ == "__main__":
    main()
