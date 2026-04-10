from __future__ import annotations

import importlib.resources
import time

import frida

PROCESS_NAMES = ["Terraria.exe", "Terraria.bin.x86_64"]


class Game:
    _session: frida.core.Session
    _script: frida.core.Script

    def __init__(self, session: frida.core.Session, script: frida.core.Script) -> None:
        self._session = session
        self._script = script

    @classmethod
    def connect(cls, device: frida.core.Device) -> Game:
        procs = [p for p in device.enumerate_processes() if p.name in PROCESS_NAMES]
        if not procs:
            raise RuntimeError("Terraria not found. Is the game running?")

        proc = procs[0]
        print(f"Attaching to {proc.name} (PID {proc.pid})...")
        session = device.attach(proc.pid)

        js_source = (
            importlib.resources.files("terraria_autofish.js")
            .joinpath("check_bite.js")
            .read_text()
        )
        script = session.create_script(js_source)
        script.on("message", lambda m, d: None)
        script.load()
        time.sleep(0.3)

        return cls(session, script)

    def check_bite(self) -> float | None:
        return self._script.exports_sync.check_bite()  # pyright: ignore[reportAny]

    def close(self) -> None:
        self._session.detach()
