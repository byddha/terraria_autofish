from __future__ import annotations

from typing import Protocol

import frida


class DeviceProvider(Protocol):
    def get_device(self) -> frida.core.Device: ...

    def cleanup(self) -> None: ...
