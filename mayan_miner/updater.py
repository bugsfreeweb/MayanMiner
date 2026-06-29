import json
import shutil
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
import zipfile
from pathlib import Path
from typing import Dict, Optional, Tuple

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


def _choose_xmrig_asset(release_data: Dict) -> Optional[Dict]:
    for asset in release_data.get("assets", []):
        name = asset.get("name", "").lower()
        if name.endswith(".zip") and "windows" in name:
            return asset
    return None


def download_latest_xmrig() -> Path:
    release_data = get_latest_xmrig_release()
    asset = _choose_xmrig_asset(release_data)
    if not asset:
        raise RuntimeError("Could not find a Windows zip asset for XMRig.")
    url = asset["browser_download_url"]
    target_zip = get_miner_install_dir() / asset["name"]
    with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": USER_AGENT}), timeout=60) as response:
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
