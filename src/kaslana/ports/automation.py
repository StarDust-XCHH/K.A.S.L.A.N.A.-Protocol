"""Automation port for the physical Android/WeChat device."""

from __future__ import annotations

from abc import ABC, abstractmethod


class AutomationPort(ABC):
    """Human-like UI automation capabilities for the calling phone."""

    @abstractmethod
    async def wake_device(self) -> None:
        """Wake and unlock the physical Android device."""

    @abstractmethod
    async def open_wechat(self) -> None:
        """Open WeChat through normal UI automation."""

    @abstractmethod
    async def dial_voice_call(self, contact_alias: str) -> None:
        """Search a contact and start a voice call."""

    @abstractmethod
    async def wait_for_call_connected(self, timeout_s: float) -> bool:
        """Return true if the voice call appears connected before timeout."""

    @abstractmethod
    async def hang_up(self) -> None:
        """End the current voice call through UI automation."""
