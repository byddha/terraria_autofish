from __future__ import annotations

import time
from collections import defaultdict
from typing import TYPE_CHECKING

import frida

from terraria_autofish.names import ITEM_NAMES, NPC_NAMES

if TYPE_CHECKING:
    from terraria_autofish.clicker.base import Clicker
    from terraria_autofish.game import Game


def _item_label(item_id: int) -> str:
    if item_id < 0:
        name = NPC_NAMES.get(-item_id, str(-item_id))
        return f"{name} (NPC {-item_id})"
    if item_id > 0:
        name = ITEM_NAMES.get(item_id, str(item_id))
        return f"{name} ({item_id})"
    return "unknown"


class Bot:
    _game: Game
    _clicker: Clicker
    _whitelist: set[int]

    def __init__(
        self,
        game: Game,
        clicker: Clicker,
        whitelist: set[int] | None = None,
    ) -> None:
        self._game = game
        self._clicker = clicker
        self._whitelist = whitelist or set()

    def run(self) -> None:
        if self._whitelist:
            print(f"Whitelist ({len(self._whitelist)}):")
            for item_id in sorted(self._whitelist):
                print(f"  - {_item_label(item_id)}")
        print("Watching for bites... (Ctrl+C to stop)")
        was_biting = False
        did_catch = False
        caught: defaultdict[int, int] = defaultdict(int)
        skipped: defaultdict[int, int] = defaultdict(int)

        try:
            while True:
                try:
                    result = self._game.check_bite()
                except frida.InvalidOperationError:
                    print("Game closed.")
                    break
                if result is not None:
                    ai1, local_ai1 = result
                else:
                    ai1 = None
                    local_ai1 = 0.0
                biting = ai1 is not None and ai1 < 0

                if biting and not was_biting:
                    item_id = int(local_ai1)
                    ts = time.strftime("%H:%M:%S")
                    label = _item_label(item_id)

                    if self._should_catch(item_id):
                        print(f"[{ts}] BITE! {label}")
                        self._clicker.click()
                        did_catch = True
                        caught[item_id] += 1
                    else:
                        print(f"[{ts}] SKIP  {label}")
                        did_catch = False
                        skipped[item_id] += 1
                elif not biting and was_biting and did_catch:
                    time.sleep(0.5)
                    ts = time.strftime("%H:%M:%S")
                    print(f"[{ts}] Re-casting...")
                    self._clicker.click()

                was_biting = biting
                time.sleep(0.033)
        except KeyboardInterrupt:
            pass

        _print_summary(caught, skipped)

    def _should_catch(self, item_id: int) -> bool:
        if not self._whitelist:
            return True
        return item_id in self._whitelist


def _print_summary(
    caught: dict[int, int],
    skipped: dict[int, int],
) -> None:
    if not caught and not skipped:
        return

    print("\n--- Session Summary ---")

    if caught:
        total_caught = sum(caught.values())
        print(f"\nCaught ({total_caught}):")
        for item_id, count in sorted(caught.items(), key=lambda x: x[1], reverse=True):
            print(f"  {_item_label(item_id):.<40} {count}")

    if skipped:
        total_skipped = sum(skipped.values())
        print(f"\nSkipped ({total_skipped}):")
        for item_id, count in sorted(skipped.items(), key=lambda x: x[1], reverse=True):
            print(f"  {_item_label(item_id):.<40} {count}")
