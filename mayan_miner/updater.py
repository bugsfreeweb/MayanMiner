import json
import platform
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from mayan_miner.config import _app_dir

APP_VERSION = "1.0.0"
APP_REPO = "MayanMiner/MayanMiner"
XMRIG_REPO = "xmrig/xmrig"
USER_AGENT = "MayanMiner/1.0"


def _github_api_json(url: str) -> Dict:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return {}
        raise
    except urllib.error.URLError:
        return {}


def get_miner_install_dir() -> Path:
    path = _app_dir() / "miner"
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_update_download_dir() -> Path:
    path = _app_dir() / "update"
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_installed_miner_path() -> Path:
    return get_miner_install_dir() / "xmrig.exe"


def get_latest_xmrig_release() -> Dict:
    url = f"https://api.github.com/repos/{XMRIG_REPO}/releases/latest"
    return _github_api_json(url)


def _is_windows_asset(name: str) -> bool:
    return any(tag in name for tag in ("windows", "win64", "win32", "win-arm64", "mingw"))


def _arch_score(name: str) -> int:
    """Return higher score for better architecture match on current system."""
    is_64bit = platform.machine().endswith("64")
    # Prefer exact win64/x64 on 64-bit; win32/x86 on 32-bit
    if is_64bit:
        if "win64" in name or "x64" in name or "amd64" in name:
            return 3 if "cuda" not in name else 2
        if "windows" in name and "arm" not in name:
            return 2
        if "win32" in name or "x86" in name:
            return 1
    else:
        if "win32" in name or "x86" in name:
            return 3
        if "windows" in name and "arm" not in name:
            return 2
        if "win64" in name or "x64" in name:
            return 1
    if "arm64" in name or "aarch64" in name:
        return -1
    return 0


def _choose_xmrig_asset(release_data: Dict) -> Optional[Dict]:
    candidates: List[Dict] = []
    for asset in release_data.get("assets", []):
        name = asset.get("name", "").lower()
        if not name.endswith(".zip"):
            continue
        if _is_windows_asset(name) or "msvc" in name or "mingw" in name:
            candidates.append(asset)
    if not candidates:
        return None
    candidates.sort(key=lambda a: _arch_score(a.get("name", "").lower()), reverse=True)
    return candidates[0]


def download_latest_xmrig() -> Path:
    release_data = get_latest_xmrig_release()
    asset = _choose_xmrig_asset(release_data)
    if not asset:
        raise RuntimeError("Could not find a Windows zip asset for XMRig.")
    url = asset["browser_download_url"]
    target_zip = get_miner_install_dir() / asset["name"]
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": USER_AGENT}), timeout=120) as response:
        with open(target_zip, "wb") as handle:
            shutil.copyfileobj(response, handle)
    with zipfile.ZipFile(target_zip, "r") as archive:
        exe_name = next((name for name in archive.namelist() if name.lower().endswith("xmrig.exe")), None)
        if not exe_name:
            raise RuntimeError("Downloaded XMRig archive did not contain xmrig.exe")
        archive.extract(exe_name, path=get_miner_install_dir())
        extracted_path = get_miner_install_dir() / exe_name
        installed_path = get_installed_miner_path()
        extracted_path.replace(installed_path)
    try:
        target_zip.unlink()
    except OSError:
        pass
    try:
        result = subprocess.run([str(installed_path), "--version"], capture_output=True, text=True, timeout=10)
        if result.returncode != 0:
            raise RuntimeError(f"XMRig binary at {installed_path} failed verification: {result.stderr.strip()}")
    except FileNotFoundError:
        raise RuntimeError(f"XMRig binary not found at {installed_path} after download")
    except OSError as error:
        raise RuntimeError(f"XMRig binary at {installed_path} is not compatible with this system: {error}")
    except subprocess.TimeoutExpired:
        raise RuntimeError("XMRig --version timed out")
    return installed_path


def get_installed_miner_version() -> Optional[str]:
    path = get_installed_miner_path()
    if not path.exists():
        return None
    try:
        result = subprocess.run([str(path), "--version"], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            return result.stdout.strip().splitlines()[0]
    except Exception:
        pass
    return None


def get_latest_app_release() -> Dict:
    url = f"https://api.github.com/repos/{APP_REPO}/releases/latest"
    return _github_api_json(url)


def get_latest_app_version() -> Optional[str]:
    data = get_latest_app_release()
    return data.get("tag_name") if isinstance(data, dict) else None


def is_app_update_available() -> bool:
    latest = get_latest_app_version()
    return bool(latest and latest != APP_VERSION)


def download_latest_app_installer() -> Path:
    release_data = get_latest_app_release()
    assets = release_data.get("assets", [])
    for asset in assets:
        name = asset.get("name", "")
        if name.lower().endswith("setup.exe") or name.lower().endswith("mayanminer.exe"):
            url = asset["browser_download_url"]
            output_dir = get_update_download_dir()
            target_file = output_dir / name
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": USER_AGENT}), timeout=60) as response:
                with open(target_file, "wb") as handle:
                    shutil.copyfileobj(response, handle)
            return target_file
    raise RuntimeError("No application installer asset was found in the latest release.")
