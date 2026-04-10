from __future__ import annotations

import frida


class LinuxNativeProvider:
    """Direct Frida attach for native Linux (MonoKickstart) Terraria."""

    def __init__(self) -> None:
        print("Terraria (Linux native)")

    def get_device(self) -> frida.core.Device:
        return frida.get_local_device()

    def cleanup(self) -> None:
        pass
