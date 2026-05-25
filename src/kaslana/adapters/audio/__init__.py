"""Audio adapters."""

from kaslana.adapters.audio.sounddevice_loopback import (
    SoundDeviceAudioInput,
    SoundDeviceAudioOutput,
)

__all__ = ["SoundDeviceAudioInput", "SoundDeviceAudioOutput"]
