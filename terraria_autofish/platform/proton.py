from __future__ import annotations

import lzma
import os
import re
import subprocess
import time
from pathlib import Path
from urllib.request import urlretrieve

import frida

TERRARIA_APP_ID = "105600"
FRIDA_PORT = 27042


class ProtonProvider:
    _server_proc: subprocess.Popen[bytes] | None
    _steam_dir: Path
    _wine_binary: Path
    _wine_prefix: Path
    _server_path: Path

    def __init__(self) -> None:
        self._server_proc = None

        self._steam_dir = _find_steam_dir()
        proton_name = _find_proton_name(self._steam_dir, TERRARIA_APP_ID)
        print(f"Proton: {proton_name}")

        self._wine_binary = _find_wine_binary(self._steam_dir, proton_name)
        self._wine_prefix = (
            self._steam_dir / "steamapps" / "compatdata" / TERRARIA_APP_ID / "pfx"
        )
        self._server_path = _ensure_frida_server()

    def get_device(self) -> frida.core.Device:
        self._start_server()
        return frida.get_device_manager().add_remote_device(f"127.0.0.1:{FRIDA_PORT}")

    def cleanup(self) -> None:
        if self._server_proc:
            self._server_proc.terminate()
            _ = self._server_proc.wait()
            self._server_proc = None

    def _start_server(self) -> None:
        print("Starting frida-server...")
        self._server_proc = subprocess.Popen(
            [
                str(self._wine_binary),
                str(self._server_path),
                "--listen",
                f"0.0.0.0:{FRIDA_PORT}",
            ],
            env={**os.environ, "WINEPREFIX": str(self._wine_prefix)},
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        for _ in range(20):
            try:
                device = frida.get_device_manager().add_remote_device(
                    f"127.0.0.1:{FRIDA_PORT}"
                )
                _ = device.enumerate_processes()
                print("frida-server ready.")
                return
            except Exception:
                time.sleep(0.5)

        self._server_proc.kill()
        raise RuntimeError("frida-server failed to start")


def _find_steam_dir() -> Path:
    for candidate in [
        Path.home() / ".steam" / "steam",
        Path.home() / ".local" / "share" / "Steam",
    ]:
        if (candidate / "config" / "config.vdf").exists():
            return candidate
    raise RuntimeError("Steam directory not found")


def _find_proton_name(steam_dir: Path, app_id: str) -> str:
    config = (steam_dir / "config" / "config.vdf").read_text()

    in_mapping = False
    current_id = None
    default_name = None
    app_name = None

    for line in config.splitlines():
        stripped = line.strip().strip('"')
        if "CompatToolMapping" in line:
            in_mapping = True
            continue
        if not in_mapping:
            continue

        if re.match(r"^\d+$", stripped):
            current_id = stripped
        elif '"name"' in line:
            name = line.split('"name"')[1].strip().strip('"').strip()
            if current_id == "0":
                default_name = name
            elif current_id == app_id:
                app_name = name

    result = app_name or default_name
    if not result:
        raise RuntimeError(f"No Proton version found for app {app_id}")
    return result


def _find_wine_binary(steam_dir: Path, proton_name: str) -> Path:
    for base in [
        steam_dir / "compatibilitytools.d" / proton_name,
        steam_dir / "steamapps" / "common" / proton_name,
    ]:
        wine = base / "files" / "bin" / "wine64"
        if wine.exists():
            return wine
    raise RuntimeError(f"wine64 not found for {proton_name}")


def _ensure_frida_server() -> Path:
    cache_dir = Path.home() / ".cache" / "terraria-autofish"
    cache_dir.mkdir(parents=True, exist_ok=True)
    server_name = f"frida-server-{frida.__version__}-windows-x86_64.exe"
    server_path = cache_dir / server_name

    if server_path.exists():
        print(f"frida-server {frida.__version__} (cached)")
        return server_path

    xz_name = f"{server_name}.xz"
    url = f"https://github.com/frida/frida/releases/download/{frida.__version__}/{xz_name}"
    xz_path = cache_dir / xz_name
    print(f"Downloading frida-server {frida.__version__}...")

    _ = urlretrieve(url, xz_path)
    with lzma.open(xz_path, "rb") as f_in:
        _ = server_path.write_bytes(f_in.read())
    server_path.chmod(0o755)
    xz_path.unlink()

    return server_path
