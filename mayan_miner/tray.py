"""System tray integration.

Wraps pystray so the rest of the app doesn't need to know the details, and
degrades gracefully (tray simply unavailable) if pystray/Pillow aren't
installed - the app should never crash just because the tray icon can't
be shown.
"""
import threading
from pathlib import Path
from typing import Callable, Optional

try:
    import pystray
    from PIL import Image
    TRAY_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency
    pystray = None
    Image = None
    TRAY_AVAILABLE = False


class TrayManager:
    def __init__(
        self,
        icon_path: Path,
        *,
        on_show: Callable[[], None],
        on_start_mining: Callable[[], None],
        on_stop_mining: Callable[[], None],
        on_exit: Callable[[], None],
    ) -> None:
        self.icon_path = icon_path
        self.on_show = on_show
        self.on_start_mining = on_start_mining
        self.on_stop_mining = on_stop_mining
        self.on_exit = on_exit
        self._icon = None
        self._thread: Optional[threading.Thread] = None

    @property
    def available(self) -> bool:
        return TRAY_AVAILABLE

    def start(self) -> bool:
        if not TRAY_AVAILABLE or self._icon is not None:
            return False
        try:
            image = Image.open(str(self.icon_path)) if self.icon_path.exists() else Image.new("RGBA", (64, 64), "#10b981")
        except Exception:
            image = Image.new("RGBA", (64, 64), "#10b981")

        menu = pystray.Menu(
            pystray.MenuItem("Show Mayan Miner", lambda: self.on_show(), default=True),
            pystray.MenuItem("Start mining", lambda: self.on_start_mining()),
            pystray.MenuItem("Stop mining", lambda: self.on_stop_mining()),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Exit", lambda: self.on_exit()),
        )
        self._icon = pystray.Icon("mayan_miner", image, "Mayan Miner", menu)
        self._thread = threading.Thread(target=self._icon.run, daemon=True)
        self._thread.start()
        return True

    def stop(self) -> None:
        if self._icon is not None:
            try:
                self._icon.stop()
            except Exception:
                pass
            self._icon = None

    def notify(self, title: str, message: str) -> None:
        if self._icon is not None:
            try:
                self._icon.notify(message, title)
            except Exception:
                pass
