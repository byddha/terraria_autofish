from __future__ import annotations

from terraria_autofish.platform.base import DeviceProvider
from terraria_autofish.platform.proton import ProtonProvider


def detect() -> DeviceProvider:
    return ProtonProvider()
