from __future__ import annotations

import shutil

from terraria_autofish.clicker.base import Clicker
from terraria_autofish.clicker.ydotool import YdotoolClicker


def auto_detect() -> Clicker:
    if shutil.which("ydotool"):
        return YdotoolClicker()
    raise RuntimeError("No supported input backend found. Install ydotool.")
