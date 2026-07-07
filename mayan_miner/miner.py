import os
import shlex
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from mayan_miner.updater import get_installed_miner_path


def _default_installed_miner() -> str:
    default_path = get_installed_miner_path()
    return str(default_path) if default_path.exists() else "xmrig"


def build_miner_command(config: Dict[str, Any]) -> List[str]:
    miner_kind = str(config.get("miner_kind", "xmrig")).lower()
    executable = config.get("miner_executable") or _default_installed_miner()
    pool = config.get("pool") or "mine.example.com:3333"
    wallet = config.get("wallet") or "YOUR_WALLET"
    worker = config.get("worker") or "mayan-cpu"
    password = config.get("password") or "x"
    algorithm = config.get("algorithm") or "rx/0"
    threads = config.get("threads") or max(1, os.cpu_count() or 1)

    extra_args = config.get("extra_args", "")

    if miner_kind == "custom":
        # A "custom" miner kind lets this app drive literally any other miner
        # executable, which may use a completely different CLI syntax (or none
        # of the standard xmrig-style flags at all). If the user has supplied a
        # command template, render it with the current settings - including the
        # chosen algorithm, which previously had no effect for custom miners.
        template = str(config.get("custom_command_template") or "").strip()
        if template:
            fields = {
                "executable": executable,
                "pool": pool,
                "wallet": wallet,
                "worker": worker,
                "password": password,
                "algorithm": algorithm,
                "threads": str(threads),
                "extra_args": extra_args,
            }
            try:
                rendered = template.format(**fields)
            except (KeyError, IndexError, ValueError):
                # Fall back to the raw template text if it has bad/unknown
                # placeholders, rather than crashing the whole app.
                rendered = template
            return shlex.split(rendered)

        # No template: keep the original, minimal behavior (bare executable +
        # extra args), but still expose --algo when the user has typed a
        # non-default algorithm so a custom-but-xmrig-like miner can pick it up.
        command = [executable]
        if algorithm and algorithm != "rx/0":
            command.extend(["--algo", algorithm])
    elif miner_kind == "srbminer":
        command = [executable, "--algorithm", algorithm, "--pool", pool, "--wallet", wallet, "--password", password]
        if threads:
            command.extend(["--threads", str(threads)])
    else:
        command = [
            executable,
            "--url",
            pool,
            "--user",
            wallet,
            "--pass",
            f"{worker}:{password}",
            "--threads",
            str(threads),
            "--algo",
            algorithm,
        ]

    if bool(config.get("use_all_cores", True)) and miner_kind != "custom":
        command.append("--use-all-cores")

    if extra_args:
        command.extend(shlex.split(extra_args))
    return command


class MinerController:
    def __init__(self) -> None:
        self.process: Optional[subprocess.Popen[str]] = None

    def start(self, config: Dict[str, Any]) -> Optional[subprocess.Popen[str]]:
        command = build_miner_command(config)
        creationflags = 0
        if os.name == "nt":
            creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)

        self.process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            text=True,
            bufsize=1,
            creationflags=creationflags,
        )
        return self.process

    def stop(self) -> None:
        if self.process and self.process.poll() is None:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
                self.process.wait(timeout=5)
        self.process = None

    def is_running(self) -> bool:
        return bool(self.process and self.process.poll() is None)
