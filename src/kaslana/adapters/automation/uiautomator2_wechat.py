"""uiautomator2 WeChat adapter placeholder."""

from __future__ import annotations

from kaslana.ports.automation import AutomationPort


class Uiautomator2WechatAutomation(AutomationPort):
    """Future adapter for physical Android UI automation via uiautomator2."""

    async def wake_device(self) -> None:
        raise NotImplementedError("uiautomator2 wake_device is not implemented yet.")

    async def open_wechat(self) -> None:
        raise NotImplementedError("uiautomator2 open_wechat is not implemented yet.")

    async def dial_voice_call(self, contact_alias: str) -> None:
        raise NotImplementedError("uiautomator2 dial_voice_call is not implemented yet.")

    async def wait_for_call_connected(self, timeout_s: float) -> bool:
        raise NotImplementedError("uiautomator2 wait_for_call_connected is not implemented yet.")

    async def hang_up(self) -> None:
        raise NotImplementedError("uiautomator2 hang_up is not implemented yet.")
