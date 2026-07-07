import base64
import hashlib
import json
import os
import platform
from pathlib import Path
from typing import Any, Dict

try:
    from cryptography.fernet import Fernet
except ImportError:  # pragma: no cover - optional dependency
    Fernet = None


def default_config() -> Dict[str, Any]:
    return {
        # New UI and application settings
        "start_mining_on_login": False,
        "minimize_to_tray": False,
        "show_tray_icon": True,
        "show_splashscreen_next": True, # For animated splash screen
        "theme": "system", # Options: "light", "dark", "system"
        "graph_history_points": 90, # Rolling window size for the live hashrate graph
        "miner_settings_path": str(_app_dir() / "miner_settings.json"), # Specific place for settings file
        # Custom algorithm options
        "custom_algo_options": {},
        "known_algorithms": [
            "rx/0", "cn/0", "cn/1", "cn/2", "cn-heavy/0", "cn/r",
            "etchash", "kawpow", "sha256", "argon2/chukwa",
        ], # Example known algos - the algorithm field also accepts any custom text
        "pool": "mine.example.com:3333",
        "wallet": "YOUR_WALLET",
        "worker": "mayan-cpu",
        "password": "x",
        "algorithm": "rx/0",
        "threads": max(1, os.cpu_count() or 1),
        "use_all_cores": True,
        "miner_executable": "",
        "miner_kind": "xmrig",
        "extra_args": "",
        # Used only when miner_kind == "custom". Lets the app drive ANY third-party
        # miner binary with its own CLI syntax. Supports {executable}, {pool},
        # {wallet}, {worker}, {password}, {algorithm}, {threads}, {extra_args}
        # placeholders. Leave blank to fall back to "<executable> <extra_args>".
        "custom_command_template": "",
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
        return merged


def _xor_encrypt(payload: bytes, key: bytes) -> bytes:
    key_bytes = key[:16]
    output = bytearray()
    for index, value in enumerate(payload):
        output.append(value ^ key_bytes[index % len(key_bytes)])
    return bytes(output)


def _xor_decrypt(payload: bytes, key: bytes) -> bytes:
    return _xor_encrypt(payload, key)
