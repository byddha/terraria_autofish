from __future__ import annotations

import atexit
import shutil
import signal
import subprocess
import sys

from terraria_autofish import clicker, platform
from terraria_autofish.bot import Bot
from terraria_autofish.game import Game
from terraria_autofish.names import ITEM_NAMES, NPC_NAMES


def _fzf_whitelist() -> set[int]:
    fzf = shutil.which("fzf")
    if not fzf:
        print("fzf not found, skipping whitelist selection (catching everything)")
        return set()

    lines: list[str] = []
    for item_id, name in sorted(ITEM_NAMES.items(), key=lambda x: x[1]):
        lines.append(f"{item_id}\t{name}")
    for npc_id, name in sorted(NPC_NAMES.items(), key=lambda x: x[1]):
        lines.append(f"n{npc_id}\t{name} (NPC)")

    try:
        result = subprocess.run(
            [
                fzf,
                "--multi",
                "--exact",
                "--bind",
                "ctrl-a:select-all,ctrl-d:deselect-all",
                "--prompt",
                "TAB select, Ctrl-A all visible, ESC catch all: ",
                "--header",
                "Whitelist fish to catch. ESC = catch everything.\n"
                + "Tip: search ' Crate' (with space) for exact word matching.",
            ],
            input="\n".join(lines),
            capture_output=True,
            text=True,
            check=False,
        )
    except (OSError, KeyboardInterrupt):
        return set()

    if result.returncode != 0:
        return set()

    whitelist: set[int] = set()
    for line in result.stdout.strip().splitlines():
        raw_id = line.split("\t", 1)[0]
        if raw_id.startswith("n"):
            whitelist.add(-int(raw_id[1:]))
        else:
            whitelist.add(int(raw_id))
    return whitelist


def main() -> None:
    whitelist = _fzf_whitelist()

    provider = platform.detect()
    _ = atexit.register(provider.cleanup)
    _ = signal.signal(signal.SIGTERM, lambda signum, frame: sys.exit(0))

    device = provider.get_device()

    try:
        game = Game.connect(device)
    except RuntimeError as e:
        print(e)
        sys.exit(1)

    input_backend = clicker.auto_detect()

    try:
        Bot(game, input_backend, whitelist=whitelist).run()
    except KeyboardInterrupt:
        pass
    finally:
        game.close()


main()
