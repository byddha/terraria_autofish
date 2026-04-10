from __future__ import annotations

import frida

from terraria_autofish.platform.base import DeviceProvider


def detect() -> DeviceProvider:
    if _terraria_native_running():
        from terraria_autofish.platform.linux_native import LinuxNativeProvider

        return LinuxNativeProvider()

    from terraria_autofish.platform.proton import ProtonProvider

    return ProtonProvider()


def _terraria_native_running() -> bool:
    try:
        device = frida.get_local_device()
        return any(
            p.name == "Terraria.bin.x86_64" for p in device.enumerate_processes()
        )
    except Exception:
        return False
