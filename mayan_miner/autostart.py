"""Optional "start on login" support for Windows.

Writes/removes a single value under the current user's Run key. This never
requires admin rights (HKCU, not HKLM) and is a no-op with no error on any
non-Windows platform.
"""
import platform
import sys

_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
_VALUE_NAME = "MayanMiner"


def _executable_command() -> str:
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}" --start-minimized'
    return f'"{sys.executable}" "{sys.argv[0]}" --start-minimized'


def set_autostart(enabled: bool) -> bool:
    """Returns True on success, False if unsupported/failed (never raises)."""
    if platform.system() != "Windows":
        return False
    try:
        import winreg  # type: ignore

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
            if enabled:
                winreg.SetValueEx(key, _VALUE_NAME, 0, winreg.REG_SZ, _executable_command())
            else:
                try:
                    winreg.DeleteValue(key, _VALUE_NAME)
                except FileNotFoundError:
                    pass
        return True
    except Exception:
        return False


def is_autostart_enabled() -> bool:
    if platform.system() != "Windows":
        return False
    try:
        import winreg  # type: ignore

        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _RUN_KEY, 0, winreg.KEY_READ) as key:
            winreg.QueryValueEx(key, _VALUE_NAME)
            return True
    except Exception:
        return False
