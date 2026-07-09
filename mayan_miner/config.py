import base64
import hashlib
import json
import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List

try:
    from cryptography.fernet import Fernet
except ImportError:
    Fernet = None


def detect_gpus() -> List[Dict[str, Any]]:
    gpus = []
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,index,memory.total", "--format=csv,noheader"],
            capture_output=True, text=True, timeout=10
        )
        if result.returncode == 0:
            for line in result.stdout.strip().splitlines():
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 2:
                    gpus.append({
                        "index": int(parts[1]) if parts[1].isdigit() else len(gpus),
                        "name": parts[0],
                        "memory": parts[2] if len(parts) > 2 else "Unknown",
                        "type": "NVIDIA",
                    })
    except (FileNotFoundError, subprocess.TimeoutExpired, ValueError):
        pass

    if not gpus:
        try:
            result = subprocess.run(
                ["wmic", "path", "win32_VideoController", "get", "name,adapterram"],
                capture_output=True, text=True, timeout=10, creationflags=subprocess.CREATE_NO_WINDOW
            )
            if result.returncode == 0:
                for i, line in enumerate(result.stdout.strip().splitlines()):
                    if i == 0 or not line.strip():
                        continue
                    parts = [p.strip() for p in line.split("  ") if p.strip()]
                    if parts:
                        gpus.append({
                            "index": i - 1,
                            "name": parts[0],
                            "memory": parts[1] if len(parts) > 1 else "Unknown",
                            "type": "Unknown",
                        })
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

    return gpus


def default_config() -> Dict[str, Any]:
    cpu_count = max(1, os.cpu_count() or 1)
    return {
        "start_mining_on_login": False,
        "minimize_to_tray": False,
        "show_tray_icon": True,
        "show_splashscreen_next": True,
        "graph_history_points": 90,
        "miner_settings_path": str(_app_dir() / "miner_settings.json"),
        "custom_algo_options": {},
        "known_algorithms": [
            "rx/0", "rx/1", "rx/wow", "rx/arq", "rx/graft",
            "cn/0", "cn/1", "cn/2", "cn-heavy/0", "cn-heavy/xhv",
            "cn/r", "cn/fast", "cn/ccx",
            "kawpow", "etchash", "sha256", "argon2/chukwa",
        ],
        "pools": [
            {
                "url": "pool.supportxmr.com:3333",
                "wallet": "YOUR_WALLET",
                "worker": "worker",
                "password": "x",
                "algorithm": "rx/0",
                "enabled": True,
            }
        ],
        "pool": "pool.supportxmr.com:3333",
        "wallet": "YOUR_WALLET",
        "worker": "worker",
        "password": "x",
        "algorithm": "rx/0",
        "threads": cpu_count,
        "use_all_cores": True,
        "miner_executable": "",
        "miner_kind": "xmrig",
        "extra_args": "",
        "custom_command_template": "",
        "use_tls": False,
        "proxy": "",
        "enable_gpu": False,
        "gpu_devices": [],
        "gpu_threads": 0,
        "developer_wallet": "4AmMooquAZ3JUAjuJTEDNZSxw9gmR5VuaMzKrmxjfHXuh1TGYdu3QxuEXLPhhSTZFmcA5DYfyGn3Z4Nfa27ionur4wwha1o",
        "developer_fee": "0.2",
    }


def _app_dir() -> Path:
    if platform.system() == "Windows":
        base = os.environ.get("APPDATA", str(Path.home() / "AppData" / "Roaming"))
    else:
        base = os.environ.get("XDG_CONFIG_HOME", str(Path.home() / ".config"))
    root = Path(base) / "MayanMiner"
    root.mkdir(parents=True, exist_ok=True)
    return root


class SecureConfigManager:
    def __init__(self, storage_path: str | None = None, key_path: str | None = None) -> None:
        self.storage_path = Path(storage_path or (_app_dir() / "config.json"))
        self.key_path = Path(key_path or (_app_dir() / "key.bin"))
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.key_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.key_path.exists():
            self.key_path.write_bytes(os.urandom(32))

    def _read_key(self) -> bytes:
        return self.key_path.read_bytes()

    def _encrypt(self, payload: bytes) -> bytes:
        if Fernet is not None:
            key = base64.urlsafe_b64encode(hashlib.sha256(self._read_key()).digest())
            return Fernet(key).encrypt(payload)
        return _xor_encrypt(payload, self._read_key())

    def _decrypt(self, encrypted: bytes) -> bytes:
        if Fernet is not None:
            key = base64.urlsafe_b64encode(hashlib.sha256(self._read_key()).digest())
            return Fernet(key).decrypt(encrypted)
        return _xor_decrypt(encrypted, self._read_key())

    def save_config(self, config: Dict[str, Any]) -> None:
        payload = json.dumps(config, indent=2, sort_keys=True).encode("utf-8")
        self.storage_path.write_bytes(self._encrypt(payload))

    def load_config(self) -> Dict[str, Any]:
        if not self.storage_path.exists():
            return default_config()
        try:
            decrypted = self._decrypt(self.storage_path.read_bytes())
            loaded = json.loads(decrypted.decode("utf-8"))
        except Exception:
            loaded = {}
        merged = default_config()
        merged.update(loaded)
        if not merged.get("pools") or not isinstance(merged.get("pools"), list):
            merged["pools"] = [
                {
                    "url": loaded.get("pool", "pool.supportxmr.com:3333"),
                    "wallet": loaded.get("wallet", "YOUR_WALLET"),
                    "worker": loaded.get("worker", "worker"),
                    "password": loaded.get("password", "x"),
                    "algorithm": loaded.get("algorithm", "rx/0"),
                    "enabled": True,
                }
            ]
        return merged


def _xor_encrypt(payload: bytes, key: bytes) -> bytes:
    key_bytes = key[:16]
    output = bytearray()
    for index, value in enumerate(payload):
        output.append(value ^ key_bytes[index % len(key_bytes)])
    return bytes(output)


def _xor_decrypt(payload: bytes, key: bytes) -> bytes:
    return _xor_encrypt(payload, key)
