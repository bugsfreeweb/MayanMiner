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

    pools = config.get("pools", [])
    if not pools or not isinstance(pools, list) or not pools[0].get("url"):
        pools = []
    if not pools:
        pools = [{
            "url": config.get("pool", "pool.supportxmr.com:3333"),
            "wallet": config.get("wallet", "YOUR_WALLET"),
            "worker": config.get("worker", "worker"),
            "password": config.get("password", "x"),
            "algorithm": config.get("algorithm", "rx/0"),
        }]
    elif pools and pools[0].get("url") == "pool.supportxmr.com:3333":
        pool_flat = config.get("pool")
        wallet_flat = config.get("wallet")
        if pool_flat and pool_flat != "pool.supportxmr.com:3333":
            pools[0]["url"] = pool_flat
        if wallet_flat and wallet_flat != "YOUR_WALLET":
            pools[0]["wallet"] = wallet_flat
        worker_flat = config.get("worker")
        if worker_flat and worker_flat != "worker":
            pools[0]["worker"] = worker_flat
        algo_flat = config.get("algorithm")
        if algo_flat and algo_flat != "rx/0":
            pools[0]["algorithm"] = algo_flat
        pw_flat = config.get("password")
        if pw_flat and pw_flat != "x":
            pools[0]["password"] = pw_flat

    pool = pools[0]
    pool_url = pool.get("url", "pool.supportxmr.com:3333")
    wallet = pool.get("wallet", "YOUR_WALLET")
    worker = pool.get("worker", "worker")
    password = pool.get("password", "x")
    algorithm = pool.get("algorithm", "rx/0")

    threads = config.get("threads") or max(1, os.cpu_count() or 1)
    extra_args = config.get("extra_args", "")
    enable_gpu = bool(config.get("enable_gpu", False))
    gpu_devices = config.get("gpu_devices", [])

    use_tls = bool(config.get("use_tls", False))
    proxy = str(config.get("proxy", "")).strip()

    if miner_kind == "custom":
        template = str(config.get("custom_command_template") or "").strip()
        if template:
            fields = {
                "executable": executable,
                "pool": pool_url,
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
                rendered = template
            return shlex.split(rendered)

        command = [executable]
        if algorithm and algorithm != "rx/0":
            command.extend(["--algo", algorithm])
    elif miner_kind == "srbminer":
        command = [executable, "--algorithm", algorithm, "--pool", pool_url, "--wallet", wallet, "--password", password]
        if threads:
            command.extend(["--threads", str(threads)])
        if use_tls:
            command.append("--tls")
    else:
        command = [
            executable,
            "--url", pool_url,
            "--user", wallet,
            "--pass", password,
            "--algo", algorithm,
            "--keepalive",
        ]
        if worker and worker != "worker":
            command.extend(["--rig-id", worker])

        for extra_pool in pools[1:]:
            if extra_pool.get("enabled", True):
                extra_url = extra_pool.get("url", "")
                if extra_url:
                    command.extend(["--url", extra_url])

        command.extend(["--threads", str(threads)])
        if use_tls:
            command.append("--tls")
            command.append("--tls-fingerprint")

    if proxy:
        command.extend(["--proxy", proxy])

    if bool(config.get("use_all_cores", True)) and miner_kind != "custom":
        command.append("--use-all-cores")

    if enable_gpu and miner_kind == "xmrig":
        command.append("--cuda")
        if gpu_devices:
            devices_str = ",".join(str(d) for d in gpu_devices)
            command.extend(["--cuda-devices", devices_str])

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

        try:
            self.process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                text=True,
                bufsize=1,
                creationflags=creationflags,
            )
        except FileNotFoundError:
            self.process = None
            raise
        except OSError as error:
            self.process = None
            raise RuntimeError(f"Failed to start miner: {error}") from error
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
