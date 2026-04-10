from __future__ import annotations

from typing import Protocol


class Clicker(Protocol):
    def click(self) -> None: ...
