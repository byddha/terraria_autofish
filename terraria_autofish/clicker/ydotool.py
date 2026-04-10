from __future__ import annotations

import subprocess


class YdotoolClicker:
    def click(self) -> None:
        subprocess.run(
            ["ydotool", "click", "-D", "50", "0xC0"],
            check=True, stdout=subprocess.DEVNULL,
        )
