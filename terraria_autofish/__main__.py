from __future__ import annotations

import atexit
import signal
import sys

from terraria_autofish import clicker, platform
from terraria_autofish.bot import Bot
from terraria_autofish.game import Game


def main() -> None:
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
        Bot(game, input_backend).run()
    except KeyboardInterrupt:
        pass
    finally:
        game.close()


main()
