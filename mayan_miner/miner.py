import os
import shlex
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

from mayan_miner.config import _app_dir
from mayan_miner.updater import get_installed_miner_path


def _default_installed_miner() -> str:
    default_path = get_installed_miner_path()
    return str(default_path) if default_path.exists() else "xmrig"


def _normalize_algorithm(algorithm: Any, miner_kind: str) -> str:
    value = str(algorithm or "rx/0").strip().lower()
    aliases = {
        "rx/0": "randomx",
        "randomx": "randomx",
        "rx": "randomx",
        "cn/0": "cn/0",
        "cn/1": "cn/1",
        "cn/2": "cn/2",
        "cn-lite": "cn-lite",
        "kawpow": "kawpow",
        "sha256": "sha256",
        "ethash": "ethash",
        "custom": "custom",
    }
    if miner_kind == "srbminer":
        return aliases.get(value, str(algorithm or "rx/0"))
    return aliases.get(value, str(algorithm or "rx/0"))


def build_miner_command(config: Dict[str, Any]) -> List[str]:
    miner_kind = str(config.get("miner_kind", "xmrig")).lower()
    executable = config.get("miner_executable") or _default_installed_miner()
    pool = config.get("pool") or "mine.example.com:3333"
    wallet = config.get("wallet") or "YOUR_WALLET"
    worker = config.get("worker") or "mayan-cpu"
    password = config.get("password") or "x"
    algorithm = _normalize_algorithm(config.get("algorithm"), miner_kind)
    threads = config.get("threads") or max(1, os.cpu_count() or 1)

    if miner_kind == "custom":
        command = [executable]
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

    extra_args = config.get("extra_args", "")
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

        working_dir = Path(config.get("working_dir") or (_app_dir() / "workdir"))
        working_dir.mkdir(parents=True, exist_ok=True)
        cache_dir = working_dir / "Cache"
        cache_dir.mkdir(parents=True, exist_ok=True)

        try:
            self.process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                text=True,
                bufsize=1,
                creationflags=creationflags,
                cwd=str(working_dir),
            )
        except OSError:
            self.process = None
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
