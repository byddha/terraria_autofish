from __future__ import annotations

import time
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from terraria_autofish.clicker.base import Clicker
    from terraria_autofish.game import Game


class Bot:
    def __init__(self, game: Game, clicker: Clicker) -> None:
        self._game = game
        self._clicker = clicker

    def run(self) -> None:
        print("Watching for bites... (Ctrl+C to stop)")
        was_biting = False

        while True:
            ai1 = self._game.check_bite()
            biting = ai1 is not None and ai1 < 0

            if biting and not was_biting:
                print(f"[{time.strftime('%H:%M:%S')}] BITE! Clicking...")
                self._clicker.click()
            elif not biting and was_biting:
                time.sleep(0.5)
                print(f"[{time.strftime('%H:%M:%S')}] Re-casting...")
                self._clicker.click()

            was_biting = biting
            time.sleep(0.033)
