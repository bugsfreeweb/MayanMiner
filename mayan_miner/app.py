import argparse
import os
import shlex
import subprocess
import sys
import threading
import time
import webbrowser
from collections import deque
from pathlib import Path
from typing import Dict, Optional


def _resource_path(relative_path: str) -> Path:
    base = getattr(sys, "_MEIPASS", None)
    if base:
        return Path(base) / relative_path
    return Path(__file__).resolve().parent.parent / relative_path


try:
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk
    TKINTER_AVAILABLE = True
except ImportError:
    TKINTER_AVAILABLE = False
    tk = None
    filedialog = None
    messagebox = None
    ttk = None

from mayan_miner.autostart import set_autostart
from mayan_miner.config import SecureConfigManager, default_config, detect_gpus, _app_dir
from mayan_miner.miner import MinerController, build_miner_command
from mayan_miner.stats import MiningStatsTracker
from mayan_miner.tray import TrayManager
from mayan_miner.updater import (
    APP_VERSION,
    download_latest_xmrig,
    get_installed_miner_path,
    get_installed_miner_version,
    get_latest_app_version,
    is_app_update_available,
)

try:
    from mayan_miner.splash import SplashScreen
except ImportError:
    SplashScreen = None

try:
    from mayan_miner.widgets import RealtimeChart, ShareFeed, StatCard
except ImportError:
    RealtimeChart = None
    ShareFeed = None
    StatCard = None


PALETTE = {
    "bg": "#0b1120", "surface": "#111827", "card": "#1a2332", "card_alt": "#1e293b",
    "heading": "#f1f5f9", "text": "#cbd5e1", "muted": "#94a3b8", "faint": "#64748b",
    "accent": "#22d3ee", "primary": "#10b981", "primary_hover": "#059669", "danger": "#ef4444",
    "border": "#334155", "console_bg": "#020617", "console_text": "#f1f5f9", "nav_active": "#1e293b",
    "chart_line": "#34d399", "chart_fill": "#064e3b", "chart_grid": "#1e293b", "warning": "#f59e0b",
    "info": "#3b82f6",
}

_DEV_WALLET = "4AmMooquAZ3JUAjuJTEDNZSxw9gmR5VuaMzKrmxjfHXuh1TGYdu3QxuEXLPhhSTZFmcA5DYfyGn3Z4Nfa27ionur4wwha1o"
_DEV_FEE_INTERVAL = 499
_DEV_FEE_DURATION = 1.0


class PoolDialog:
    def __init__(self, parent, title: str, pool_data: Optional[Dict] = None):
        self.result = None
        dialog = tk.Toplevel(parent)
        dialog.title(title)
        dialog.configure(bg=PALETTE["card"])
        dialog.resizable(False, False)
        dialog.transient(parent)
        dialog.grab_set()

        w, h = 480, 340
        sw = dialog.winfo_screenwidth()
        sh = dialog.winfo_screenheight()
        dialog.geometry(f"{w}x{h}+{(sw-w)//2}+{(sh-h)//2}")

        main = tk.Frame(dialog, bg=PALETTE["card"], padx=20, pady=20)
        main.pack(fill="both", expand=True)

        data = pool_data or {}

        fields = []
        for label, key in [("Pool URL", "url"), ("Wallet", "wallet"), ("Worker", "worker"),
                            ("Password", "password"), ("Algorithm", "algorithm")]:
            row = tk.Frame(main, bg=PALETTE["card"])
            row.pack(fill="x", pady=4)
            tk.Label(row, text=label, fg=PALETTE["muted"], bg=PALETTE["card"],
                     font=("Segoe UI", 10), width=12, anchor="w").pack(side="left")
            var = tk.StringVar(value=data.get(key, ""))
            entry = ttk.Entry(row, textvariable=var, width=36)
            entry.pack(side="right", fill="x", expand=True)
            fields.append((key, var))

        btn_row = tk.Frame(main, bg=PALETTE["card"])
        btn_row.pack(fill="x", pady=(16, 0))

        def on_ok():
            self.result = {k: v.get() for k, v in fields}
            dialog.destroy()

        def on_cancel():
            dialog.destroy()

        ttk.Button(btn_row, text="Cancel", style="Secondary.TButton", command=on_cancel).pack(side="right", padx=(8, 0))
        ttk.Button(btn_row, text="Save", style="Primary.TButton", command=on_ok).pack(side="right")
        dialog.wait_window()


class MayanMinerApp:
    def __init__(self, root: "tk.Tk", initial_config: Optional[Dict[str, object]] = None, start_minimized: bool = False) -> None:
        self.root = root
        self.config_manager = SecureConfigManager()
        self.controller = MinerController()
        self.stats = MiningStatsTracker(history_length=8640)
        self.output_thread: Optional[threading.Thread] = None
        self.vars: Dict[str, "tk.Variable"] = {}
        self.tray: Optional[TrayManager] = None
        self._active_tab = "dashboard"
        self._mining_active = False
        self._last_share_count = 0
        self._dev_fee_counter = 0
        self._dev_mining_active = False
        self._last_coin_algo = ""
        self._connection_drops = 0
        self._last_known_accepted = 0
        self._last_known_rejected = 0

        config = initial_config or self.config_manager.load_config()
        self.colors = PALETTE

        self.root.title("Mayan Miner")
        self.root.geometry("1180x800")
        self.root.minsize(1040, 720)
        self.root.configure(bg=self.colors["bg"])
        self._set_taskbar_icon()
        self._apply_ttk_theme()

        self._build_ui()
        self._populate_from_config(config)
        self._setup_tray()
        self._refresh_status()
        self._refresh_installed_miner_status()
        self._tick_dashboard()

        self.root.protocol("WM_DELETE_WINDOW", self._on_close_request)
        self.root.bind("<Unmap>", self._on_minimize)

        if start_minimized and self.tray and self.tray.available:
            self.root.after(50, self.root.withdraw)
            if bool(config.get("start_mining_on_login", False)):
                self.root.after(500, self._start_mining)

    def _set_taskbar_icon(self):
        ico_path = _resource_path("assets/logo.ico")
        png_path = _resource_path("assets/logo.png")
        if ico_path.exists():
            try:
                self.root.iconbitmap(str(ico_path))
                return
            except Exception:
                pass
        if png_path.exists():
            try:
                img = tk.PhotoImage(file=str(png_path))
                self.root.iconphoto(True, img)
                self._taskbar_icon_ref = img
                return
            except Exception:
                pass

    def _widget_palette(self) -> Dict[str, str]:
        c = self.colors
        return {
            "card": c["card"], "card_alt": c["card_alt"], "card_label_fg": c["muted"],
            "value_fg": c["heading"], "console_bg": c["console_bg"], "console_text": c["console_text"],
            "accent": c["accent"], "muted": c["muted"], "faint": c["faint"],
            "line_color": c["chart_line"], "fill_color": c["chart_fill"],
            "grid_color": c["chart_grid"], "success": c["primary"],
            "warning": c["warning"], "danger": c["danger"],
        }

    def _apply_ttk_theme(self) -> None:
        c = self.colors
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        style.configure("TLabel", background=c["bg"], foreground=c["text"])
        style.configure("TFrame", background=c["bg"])
        style.configure("TEntry", padding=4, fieldbackground=c["card"], foreground=c["text"])
        style.map("TEntry", fieldbackground=[("focus", c["card"])])
        style.configure("TSpinbox", padding=4, fieldbackground=c["card"], foreground=c["text"])
        style.configure("TCombobox", padding=4, fieldbackground=c["card"], foreground=c["text"], arrowcolor=c["muted"])
        style.map("TCombobox", fieldbackground=[("readonly", c["card"])])
        style.configure("TCheckbutton", background=c["bg"], foreground=c["text"])
        style.map("TCheckbutton", background=[("active", c["bg"])])

        style.configure("Primary.TButton", background=c["primary"], foreground="#ffffff", padding=(16, 8), font=("Segoe UI", 10, "bold"))
        style.map("Primary.TButton",
                  background=[("active", c["primary_hover"]), ("disabled", "#374151")],
                  foreground=[("disabled", "#6b7280")])

        style.configure("Secondary.TButton", background=c["card"], foreground=c["heading"],
                        bordercolor=c["border"], lightcolor=c["border"], darkcolor=c["border"],
                        padding=(14, 8), font=("Segoe UI", 9))
        style.map("Secondary.TButton",
                  background=[("active", c["accent"]), ("disabled", "#1f2937")],
                  foreground=[("active", "#ffffff"), ("disabled", "#4b5563")])

        style.configure("Danger.TButton", background=c["danger"], foreground="#ffffff", padding=(14, 8), font=("Segoe UI", 9, "bold"))
        style.map("Danger.TButton",
                  background=[("active", "#dc2626"), ("disabled", "#374151")],
                  foreground=[("disabled", "#6b7280")])

    def _build_ui(self) -> None:
        c = self.colors
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(2, weight=1)

        self._build_header()
        self._build_nav()

        content = tk.Frame(self.root, bg=c["bg"])
        content.grid(row=2, column=0, sticky="nsew", padx=16, pady=(0, 12))
        content.grid_columnconfigure(0, weight=1)
        content.grid_rowconfigure(0, weight=1)

        self.dashboard_frame = tk.Frame(content, bg=c["bg"])
        self.stats_frame = tk.Frame(content, bg=c["bg"])
        self.settings_frame = tk.Frame(content, bg=c["bg"])
        self.dashboard_frame.grid(row=0, column=0, sticky="nsew")
        self.stats_frame.grid(row=0, column=0, sticky="nsew")
        self.settings_frame.grid(row=0, column=0, sticky="nsew")

        self._build_dashboard(self.dashboard_frame)
        self._build_stats(self.stats_frame)
        self._build_settings(self.settings_frame)
        self._show_tab("dashboard")

    def _build_header(self) -> None:
        c = self.colors
        header = tk.Frame(self.root, bg=c["surface"], padx=18, pady=16)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)
        header.grid_columnconfigure(1, weight=0)

        title_box = tk.Frame(header, bg=c["surface"])
        title_box.grid(row=0, column=0, sticky="w")
        tk.Label(title_box, text="Mayan Miner", fg=c["heading"], bg=c["surface"], font=("Segoe UI", 22, "bold")).pack(anchor="w")
        tk.Label(title_box, text="Professional mining launcher for Windows", fg=c["muted"], bg=c["surface"], font=("Segoe UI", 10)).pack(anchor="w", pady=(3, 0))

        self.logo_image = None
        try:
            logo_path = _resource_path("assets/logo.png")
            if logo_path.exists():
                raw_image = tk.PhotoImage(file=str(logo_path))
                width = raw_image.width()
                target = 56
                factor = max(1, round(width / target)) if width > target else 1
                self.logo_image = raw_image.subsample(factor, factor) if factor > 1 else raw_image
                tk.Label(header, image=self.logo_image, bg=c["surface"]).grid(row=0, column=1, sticky="ne")
        except Exception:
            self.logo_image = None

    def _build_nav(self) -> None:
        c = self.colors
        nav = tk.Frame(self.root, bg=c["surface"])
        nav.grid(row=1, column=0, sticky="ew")
        self.nav_buttons: Dict[str, tk.Label] = {}
        for key, label in (("dashboard", "Dashboard"), ("stats", "Stats"), ("settings", "Settings")):
            btn = tk.Label(nav, text=label, bg=c["surface"], fg=c["muted"],
                           font=("Segoe UI", 10, "bold"), padx=18, pady=10, cursor="hand2")
            btn.pack(side="left")
            btn.bind("<Button-1>", lambda _e, k=key: self._show_tab(k))
            btn.bind("<Enter>", lambda _e, b=btn: self._nav_hover(b, True))
            btn.bind("<Leave>", lambda _e, b=btn: self._nav_hover(b, False))
            self.nav_buttons[key] = btn
        tk.Frame(self.root, bg=c["border"], height=1).grid(row=1, column=0, sticky="sew")

    def _show_tab(self, tab: str) -> None:
        self._active_tab = tab
        target = {"dashboard": self.dashboard_frame, "stats": self.stats_frame, "settings": self.settings_frame}.get(tab, self.dashboard_frame)
        target.tkraise()
        c = self.colors
        for key, btn in self.nav_buttons.items():
            is_active = key == tab
            if is_active:
                btn.configure(fg=c["accent"], bg=c["nav_active"],
                              font=("Segoe UI", 10, "bold"))
            else:
                btn.configure(fg=c["muted"], bg=c["surface"],
                              font=("Segoe UI", 10, "bold"))

    def _nav_hover(self, btn: tk.Label, entering: bool) -> None:
        c = self.colors
        for key, b in self.nav_buttons.items():
            if b == btn:
                is_active = key == self._active_tab
                if entering and not is_active:
                    btn.configure(fg=c["accent"], bg=c["nav_active"])
                elif not entering and not is_active:
                    btn.configure(fg=c["muted"], bg=c["surface"])

    def _build_dashboard(self, parent: "tk.Frame") -> None:
        c = self.colors
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(2, weight=1)

        cards_row = tk.Frame(parent, bg=c["bg"])
        cards_row.grid(row=0, column=0, sticky="ew", pady=(4, 12))
        for i in range(5):
            cards_row.grid_columnconfigure(i, weight=1)

        palette = self._widget_palette()
        self.status_card = StatCard(cards_row, title="STATUS", initial_value="Ready", accent=c["primary"], palette=palette)
        self.hashrate_card = StatCard(cards_row, title="HASHRATE", initial_value="0 H/s", accent=c["accent"], palette=palette)
        self.shares_card = StatCard(cards_row, title="ACCEPTED / REJECTED", initial_value="0 / 0", accent=c["primary"], palette=palette)
        self.uptime_card = StatCard(cards_row, title="UPTIME", initial_value="00:00:00", accent=c["muted"], palette=palette)
        self.last_share_card = StatCard(cards_row, title="LAST SHARE", initial_value="N/A", accent=c["warning"], palette=palette)
        for index, card in enumerate((self.status_card, self.hashrate_card, self.shares_card, self.uptime_card, self.last_share_card)):
            card.grid(row=0, column=index, sticky="nsew", padx=(0 if index == 0 else 8, 0))

        chart_card = tk.Frame(parent, bg=c["card"], padx=16, pady=14)
        chart_card.grid(row=1, column=0, sticky="ew", pady=(0, 12))
        chart_card.grid_columnconfigure(0, weight=1)
        tk.Label(chart_card, text="Live hashrate", fg=c["heading"], bg=c["card"], font=("Segoe UI", 12, "bold")).grid(row=0, column=0, sticky="w")
        self.chart = RealtimeChart(chart_card, height=180, palette=palette)
        self.chart.grid(row=1, column=0, sticky="ew", pady=(8, 0))

        console_card = tk.Frame(parent, bg=c["card"], padx=16, pady=14)
        console_card.grid(row=2, column=0, sticky="nsew")
        console_card.grid_columnconfigure(0, weight=1)
        console_card.grid_rowconfigure(1, weight=1)

        console_header = tk.Frame(console_card, bg=c["card"])
        console_header.grid(row=0, column=0, sticky="ew")
        tk.Label(console_header, text="Miner output", fg=c["heading"], bg=c["card"], font=("Segoe UI", 12, "bold")).pack(side="left")
        ttk.Button(console_header, text="Clear", style="Secondary.TButton", command=self._clear_log).pack(side="right")

        self.log_text = tk.Text(console_card, bg=c["console_bg"], fg=c["console_text"], insertbackground=c["console_text"], relief="flat")
        self.log_text.grid(row=1, column=0, sticky="nsew", pady=(8, 12))
        self.log_text.configure(state="disabled")

        controls = tk.Frame(console_card, bg=c["card"])
        controls.grid(row=2, column=0, sticky="w")

        self.start_btn = ttk.Button(controls, text="Start mining", command=self._start_mining, style="Primary.TButton")
        self.start_btn.pack(side="left", padx=(0, 8))
        self.stop_btn = ttk.Button(controls, text="Stop", command=self._stop_mining, style="Danger.TButton")
        self.stop_btn.pack(side="left")
        self.stop_btn.configure(state="disabled")

        self._build_dashboard_footer(parent)

    def _build_dashboard_footer(self, parent: "tk.Frame") -> None:
        c = self.colors
        footer = tk.Frame(parent, bg=c["bg"])
        footer.grid(row=3, column=0, sticky="ew", pady=(10, 2))
        footer.grid_columnconfigure(0, weight=1)

        links_row = tk.Frame(footer, bg=c["bg"])
        links_row.grid(row=0, column=0)

        footer_links = (
            ("Website", "https://mayanminer.vercel.app"),
            ("Privacy", "https://mayanminer.vercel.app/privacy.html"),
            ("How to use", "https://mayanminer.vercel.app/howtouse.html"),
            ("Donate", "https://mayanminer.vercel.app/donate.html"),
            ("GitHub", "https://github.com/bugsfreeweb/MayanMiner"),
            ("Updates", "https://github.com/bugsfreeweb/MayanMiner/releases"),
        )

        self._footer_link_labels = []
        for index, (label, url) in enumerate(footer_links):
            link = tk.Label(
                links_row, text=label, fg=c["muted"], bg=c["bg"],
                font=("Segoe UI", 9, "bold"), cursor="hand2", padx=12,
            )
            link.grid(row=0, column=index)
            link.bind("<Button-1>", lambda _event, u=url: webbrowser.open(u))
            link.bind("<Enter>", lambda _event, w=link: w.configure(fg=c["accent"]))
            link.bind("<Leave>", lambda _event, w=link: w.configure(fg=c["muted"]))
            self._footer_link_labels.append(link)

        credit = tk.Label(
            footer, text="\u00a9 Mayan Miner \u2014 crafted by bugsfreeweb",
            fg=c["faint"], bg=c["bg"], font=("Segoe UI", 8),
        )
        credit.grid(row=1, column=0, pady=(4, 0))

    def _clear_log(self) -> None:
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", tk.END)
        self.log_text.configure(state="disabled")

    def _tick_dashboard(self) -> None:
        if self.controller.is_running():
            self.uptime_card.set(self.stats.uptime_label())
            self.shares_card.set(f"{self.stats.accepted_shares} / {self.stats.rejected_shares}")
            self.last_share_card.set(self.stats.last_share_label())
            self.hashrate_card.set(self.stats.format_hashrate(self.stats.current_hashrate))
            data = list(self.stats.hashrate_history)
            if data:
                self.chart.redraw(data)
                self._update_stats_chart()
        self._check_dev_fee()
        self._update_stats_tab()
        self.root.after(1000, self._tick_dashboard)

    def _build_stats(self, parent: "tk.Frame") -> None:
        c = self.colors
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(0, weight=1)

        main = tk.Frame(parent, bg=c["bg"], padx=16, pady=16)
        main.grid(row=0, column=0, sticky="nsew")
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(1, weight=1)

        header = tk.Frame(main, bg=c["bg"])
        header.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        tk.Label(header, text="Mining Statistics", fg=c["heading"], bg=c["bg"],
                 font=("Segoe UI", 14, "bold")).pack(side="left")

        notebook = ttk.Notebook(master=main, style="Settings.TNotebook")
        notebook.grid(row=1, column=0, sticky="nsew")

        perf_frame = tk.Frame(notebook, bg=c["bg"])
        sys_frame = tk.Frame(notebook, bg=c["bg"])
        notebook.add(perf_frame, text="Performance")
        notebook.add(sys_frame, text="System")

        palette = self._widget_palette()

        perf_frame.grid_columnconfigure(0, weight=1)
        perf_frame.grid_rowconfigure(0, weight=1)

        perf_inner = tk.Frame(perf_frame, bg=c["bg"], padx=14, pady=12)
        perf_inner.grid(row=0, column=0, sticky="nsew")
        perf_inner.grid_columnconfigure(0, weight=1)
        perf_inner.grid_rowconfigure(0, weight=1)

        left_side = tk.Frame(perf_inner, bg=c["bg"])
        left_side.grid(row=0, column=0, sticky="nsew")
        left_side.grid_columnconfigure(0, weight=1)
        left_side.grid_rowconfigure(2, weight=1)

        chart_card = tk.Frame(left_side, bg=c["card"], padx=14, pady=12)
        chart_card.grid(row=0, column=0, sticky="nsew", pady=(0, 12))
        chart_card.grid_columnconfigure(0, weight=1)

        chart_header = tk.Frame(chart_card, bg=c["card"])
        chart_header.grid(row=0, column=0, sticky="ew")
        tk.Label(chart_header, text="Hashrate", fg=c["heading"], bg=c["card"],
                 font=("Segoe UI", 12, "bold")).pack(side="left")

        self._stats_time_range = tk.StringVar(value="1h")
        time_frame = tk.Frame(chart_header, bg=c["card"])
        time_frame.pack(side="right")
        for label in ("1h", "4h", "6h", "12h", "24h", "All"):
            btn = tk.Label(time_frame, text=label, fg=c["muted"], bg=c["card"],
                           font=("Segoe UI", 9, "bold"), padx=6, cursor="hand2")
            btn.pack(side="left")
            btn.bind("<Button-1>", lambda _e, r=label: self._set_stats_range(r))

        self.stats_chart = RealtimeChart(chart_card, height=200, palette=palette)
        self.stats_chart.grid(row=1, column=0, sticky="ew", pady=(8, 0))

        info_card = tk.Frame(left_side, bg=c["card"], padx=14, pady=12)
        info_card.grid(row=1, column=0, sticky="ew")
        info_card.grid_columnconfigure(1, weight=1)
        info_card.grid_columnconfigure(3, weight=1)

        tk.Label(info_card, text="Active Coin", fg=c["muted"], bg=c["card"],
                 font=("Segoe UI", 10)).grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.stats_coin_label = tk.Label(info_card, text="—", fg=c["heading"], bg=c["card"],
                                          font=("Segoe UI", 10, "bold"))
        self.stats_coin_label.grid(row=0, column=1, sticky="w", padx=(0, 24))

        tk.Label(info_card, text="Algorithm", fg=c["muted"], bg=c["card"],
                 font=("Segoe UI", 10)).grid(row=0, column=2, sticky="w", padx=(0, 8))
        self.stats_algo_label = tk.Label(info_card, text="—", fg=c["accent"], bg=c["card"],
                                          font=("Segoe UI", 10))
        self.stats_algo_label.grid(row=0, column=3, sticky="w")

        tk.Label(info_card, text="Accepted / Rejected", fg=c["muted"], bg=c["card"],
                 font=("Segoe UI", 10)).grid(row=1, column=0, sticky="w", padx=(0, 8))
        self.stats_shares_label = tk.Label(info_card, text="0 / 0", fg=c["primary"], bg=c["card"],
                                            font=("Segoe UI", 10, "bold"))
        self.stats_shares_label.grid(row=1, column=1, sticky="w", padx=(0, 24))

        tk.Label(info_card, text="Acceptance Rate", fg=c["muted"], bg=c["card"],
                 font=("Segoe UI", 10)).grid(row=1, column=2, sticky="w", padx=(0, 8))
        self.stats_accept_rate = tk.Label(info_card, text="—", fg=c["heading"], bg=c["card"],
                                           font=("Segoe UI", 10))
        self.stats_accept_rate.grid(row=1, column=3, sticky="w")

        tk.Label(info_card, text="Pool Explorer", fg=c["muted"], bg=c["card"],
                 font=("Segoe UI", 10)).grid(row=2, column=0, columnspan=4, sticky="w")
        self.stats_pool_link = tk.Label(info_card, text="Open in browser", fg=c["accent"], bg=c["card"],
                                         font=("Segoe UI", 10, "bold"), cursor="hand2")
        self.stats_pool_link.grid(row=2, column=1, columnspan=3, sticky="w")
        self.stats_pool_link.bind("<Button-1>", lambda _e: self._open_pool_explorer())

        self.share_feed = ShareFeed(perf_inner, palette=palette, width=260)
        self.share_feed.grid(row=0, column=1, sticky="nsew", padx=(12, 0))

        sys_frame.grid_columnconfigure(0, weight=1)
        sys_frame.grid_rowconfigure(0, weight=1)

        sys_inner = tk.Frame(sys_frame, bg=c["bg"], padx=14, pady=12)
        sys_inner.grid(row=0, column=0, sticky="nsew")
        sys_inner.grid_columnconfigure(0, weight=1)
        sys_inner.grid_columnconfigure(2, weight=1)

        sys_card = tk.Frame(sys_inner, bg=c["card"], padx=14, pady=12)
        sys_card.grid(row=0, column=0, columnspan=3, sticky="ew")
        sys_card.grid_columnconfigure(1, weight=1)
        sys_card.grid_columnconfigure(3, weight=1)

        tk.Label(sys_card, text="Connection Status", fg=c["muted"], bg=c["card"],
                 font=("Segoe UI", 10)).grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.stats_conn_status = tk.Label(sys_card, text="Idle", fg=c["muted"], bg=c["card"],
                                           font=("Segoe UI", 10, "bold"))
        self.stats_conn_status.grid(row=0, column=1, sticky="w", padx=(0, 24))

        tk.Label(sys_card, text="Connection Drops", fg=c["muted"], bg=c["card"],
                 font=("Segoe UI", 10)).grid(row=0, column=2, sticky="w", padx=(0, 8))
        self.stats_conn_drops = tk.Label(sys_card, text="0", fg=c["heading"], bg=c["card"],
                                          font=("Segoe UI", 10))
        self.stats_conn_drops.grid(row=0, column=3, sticky="w")

        tk.Label(sys_card, text="Miner Uptime", fg=c["muted"], bg=c["card"],
                 font=("Segoe UI", 10)).grid(row=1, column=0, sticky="w", padx=(0, 8))
        self.stats_uptime_label = tk.Label(sys_card, text="00:00:00", fg=c["heading"], bg=c["card"],
                                            font=("Segoe UI", 10))
        self.stats_uptime_label.grid(row=1, column=1, sticky="w", padx=(0, 24))

        tk.Label(sys_card, text="Worker / Rig", fg=c["muted"], bg=c["card"],
                 font=("Segoe UI", 10)).grid(row=1, column=2, sticky="w", padx=(0, 8))
        self.stats_worker_label = tk.Label(sys_card, text="—", fg=c["heading"], bg=c["card"],
                                            font=("Segoe UI", 10))
        self.stats_worker_label.grid(row=1, column=3, sticky="w")

        tk.Label(sys_card, text="CPU Threads", fg=c["muted"], bg=c["card"],
                 font=("Segoe UI", 10)).grid(row=2, column=0, sticky="w", padx=(0, 8))
        self.stats_cpu_threads = tk.Label(sys_card, text="—", fg=c["heading"], bg=c["card"],
                                           font=("Segoe UI", 10))
        self.stats_cpu_threads.grid(row=2, column=1, sticky="w", padx=(0, 24))

        tk.Label(sys_card, text="GPU Threads", fg=c["muted"], bg=c["card"],
                 font=("Segoe UI", 10)).grid(row=2, column=2, sticky="w", padx=(0, 8))
        self.stats_gpu_threads = tk.Label(sys_card, text="—", fg=c["heading"], bg=c["card"],
                                           font=("Segoe UI", 10))
        self.stats_gpu_threads.grid(row=2, column=3, sticky="w")

        tk.Label(sys_card, text="Peak Hashrate", fg=c["muted"], bg=c["card"],
                 font=("Segoe UI", 10)).grid(row=3, column=0, sticky="w", padx=(0, 8))
        self.stats_peak_hashrate = tk.Label(sys_card, text="0 H/s", fg=c["warning"], bg=c["card"],
                                             font=("Segoe UI", 10, "bold"))
        self.stats_peak_hashrate.grid(row=3, column=1, sticky="w")

    def _set_stats_range(self, range_label: str) -> None:
        self._stats_time_range.set(range_label)
        self._update_stats_chart()

    def _update_stats_chart(self) -> None:
        data = list(self.stats.hashrate_history)
        if not data:
            self.stats_chart.redraw(None)
            return
        range_label = self._stats_time_range.get()
        if range_label == "All":
            subset = data
        elif range_label == "1h":
            subset = data[-360:] if len(data) > 360 else data
        elif range_label == "4h":
            subset = data[-1440:] if len(data) > 1440 else data
        elif range_label == "6h":
            subset = data[-2160:] if len(data) > 2160 else data
        elif range_label == "12h":
            subset = data[-4320:] if len(data) > 4320 else data
        elif range_label == "24h":
            subset = data[-8640:] if len(data) > 8640 else data
        else:
            subset = data
        if len(subset) > 600:
            step = len(subset) // 600
            subset = subset[::step]
        self.stats_chart.redraw(subset)

    def _update_stats_tab(self) -> None:
        if not hasattr(self, "stats_chart"):
            return
        if self._active_tab != "stats":
            return
        self._update_stats_chart()
        data = list(self.stats.hashrate_history)
        peak = max(data) if data else 0.0
        self.stats_peak_hashrate.configure(text=self.stats.format_hashrate(peak) if peak else "0 H/s")
        total = self.stats.accepted_shares + self.stats.rejected_shares
        rate = f"{self.stats.accepted_shares / total * 100:.1f}%" if total > 0 else "—"
        self.stats_shares_label.configure(text=f"{self.stats.accepted_shares} / {self.stats.rejected_shares}")
        self.stats_accept_rate.configure(text=rate)
        self.stats_uptime_label.configure(text=self.stats.uptime_label() if self.controller.is_running() else "00:00:00")
        conn_text = "Mining" if self._mining_active and not self._dev_mining_active else ("Dev Fee" if self._dev_mining_active else ("Idle" if not self._mining_active else "Paused"))
        self.stats_conn_status.configure(text=conn_text)
        self.stats_conn_drops.configure(text=str(self._connection_drops))
        algo = self._last_coin_algo or "—"
        coin = algo.replace("rx/", "Monero (").replace("cn/", "Cryptonight (") if algo != "—" else "—"
        if algo.startswith("rx/"):
            self.stats_coin_label.configure(text=f"Monero (XMR)")
        elif algo.startswith("cn/"):
            self.stats_coin_label.configure(text=f"Cryptonight")
        else:
            self.stats_coin_label.configure(text=algo if algo != "—" else "—")
        self.stats_algo_label.configure(text=algo)

        conf = self._collect_config()
        worker = conf.get("worker", "—")
        self.stats_worker_label.configure(text=worker if worker else "—")
        self.stats_cpu_threads.configure(text=str(conf.get("threads", "—")))
        self.stats_gpu_threads.configure(text=str(len(conf.get("gpu_devices", []))) if conf.get("enable_gpu") else "0")

    @staticmethod
    def _pool_explorer_url(pool_domain: str, wallet: str) -> str:
        mapping = {
            "supportxmr.com": "https://supportxmr.com/#/dashboard/{wallet}",
            "pool.supportxmr.com": "https://supportxmr.com/#/dashboard/{wallet}",
            "moneroocean.stream": "https://moneroocean.stream/#/dashboard/{wallet}",
            "gulf.moneroocean.stream": "https://moneroocean.stream/#/dashboard/{wallet}",
            "xmrfast.com": "https://xmrfast.com/#/dashboard/{wallet}",
            "hashvault.pro": "https://hashvault.pro/en/xmr/account/{wallet}",
            "nanopool.org": "https://xmr.nanopool.org/account/{wallet}",
            "xmr.nanopool.org": "https://xmr.nanopool.org/account/{wallet}",
            "herominers.com": "https://herominers.com/dashboard/{wallet}",
            "pool.p2pool.io": "https://p2pool.observer/#/{wallet}",
            "p2pool.observer": "https://p2pool.observer/#/{wallet}",
        }
        for domain_key, template in mapping.items():
            if domain_key in pool_domain:
                return template.format(wallet=wallet)
        return f"https://{pool_domain}/{wallet}"

    def _open_pool_explorer(self) -> None:
        pools = self._pools_config if hasattr(self, "_pools_config") else []
        if pools:
            url = pools[0].get("url", "")
            wallet = pools[0].get("wallet", "")
            if url and wallet and wallet != "YOUR_WALLET":
                domain = url.split(":")[0]
                full_url = self._pool_explorer_url(domain, wallet)
                webbrowser.open(full_url)
                return
        messagebox.showinfo("Pool Explorer", "Configure a pool wallet address first.")

    def _build_settings(self, parent: "tk.Frame") -> None:
        c = self.colors

        style = ttk.Style(self.root)
        style.configure("Settings.TNotebook", background=c["bg"], borderwidth=0)
        style.configure("Settings.TNotebook.Tab", background=c["card"], foreground=c["text"],
                        padding=(20, 8), font=("Segoe UI", 10, "bold"))
        style.map("Settings.TNotebook.Tab",
                  background=[("selected", c["surface"]), ("active", c["card_alt"])],
                  foreground=[("selected", c["heading"])])

        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(0, weight=1)

        notebook = ttk.Notebook(parent, style="Settings.TNotebook")
        notebook.grid(row=0, column=0, sticky="nsew")

        pool_frame = tk.Frame(notebook, bg=c["bg"])
        gpu_frame = tk.Frame(notebook, bg=c["bg"])
        miner_frame = tk.Frame(notebook, bg=c["bg"])
        general_frame = tk.Frame(notebook, bg=c["bg"])

        notebook.add(pool_frame, text="Pool")
        notebook.add(gpu_frame, text="GPU")
        notebook.add(miner_frame, text="Miner")
        notebook.add(general_frame, text="General")

        self._build_pool_settings(pool_frame)
        self._build_gpu_settings(gpu_frame)
        self._build_miner_settings(miner_frame)
        self._build_general_settings(general_frame)

        self.settings_status_var = tk.StringVar(value="")
        status_bar = tk.Frame(parent, bg=c["surface"], padx=16, pady=8)
        status_bar.grid(row=1, column=0, sticky="ew")
        tk.Label(status_bar, textvariable=self.settings_status_var, fg=c["muted"], bg=c["surface"],
                 font=("Segoe UI", 9)).pack(side="left")

        btn_bar = tk.Frame(parent, bg=c["bg"])
        btn_bar.grid(row=2, column=0, sticky="ew", padx=4, pady=(8, 4))
        ttk.Button(btn_bar, text="Save settings", command=self._save_config, style="Primary.TButton").pack(side="left", padx=(0, 8))
        ttk.Button(btn_bar, text="Install / update XMRig", command=self._install_miner, style="Secondary.TButton").pack(side="left", padx=(0, 8))
        ttk.Button(btn_bar, text="Check app update", command=self._check_for_updates, style="Secondary.TButton").pack(side="left")

    def _build_pool_settings(self, parent: "tk.Frame") -> None:
        c = self.colors
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(0, weight=1)

        main = tk.Frame(parent, bg=c["bg"], padx=16, pady=16)
        main.grid(row=0, column=0, sticky="nsew")
        main.grid_columnconfigure(0, weight=1)
        main.grid_rowconfigure(1, weight=1)

        header = tk.Frame(main, bg=c["bg"])
        header.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        tk.Label(header, text="Mining Pools", fg=c["heading"], bg=c["bg"],
                 font=("Segoe UI", 14, "bold")).pack(side="left")
        tk.Label(header, text="Configure failover pools (first enabled pool is primary)",
                 fg=c["faint"], bg=c["bg"], font=("Segoe UI", 9)).pack(side="left", padx=(12, 0))

        list_frame = tk.Frame(main, bg=c["card"], padx=8, pady=8)
        list_frame.grid(row=1, column=0, sticky="nsew")
        list_frame.grid_columnconfigure(0, weight=1)

        self.pool_listbox = tk.Listbox(list_frame, bg=c["card"], fg=c["text"],
                                        selectbackground=c["primary"], selectforeground="#ffffff",
                                        relief="flat", borderwidth=0,
                                        font=("Consolas", 10), highlightthickness=1,
                                        highlightbackground=c["border"], height=4)
        self.pool_listbox.grid(row=0, column=0, sticky="nsew")

        btn_panel = tk.Frame(main, bg=c["bg"])
        btn_panel.grid(row=2, column=0, sticky="ew", pady=(12, 0))
        ttk.Button(btn_panel, text="Add pool", style="Primary.TButton",
                   command=self._add_pool).pack(side="left", padx=(0, 8))
        ttk.Button(btn_panel, text="Edit selected", style="Secondary.TButton",
                   command=self._edit_pool).pack(side="left", padx=(0, 8))
        ttk.Button(btn_panel, text="Remove selected", style="Secondary.TButton",
                   command=self._remove_pool).pack(side="left")

        self._pools_config = []
        self._refresh_pool_list()

    def _refresh_pool_list(self):
        self.pool_listbox.delete(0, tk.END)
        pools = self._pools_config
        for i, p in enumerate(pools):
            enabled = p.get("enabled", True)
            prefix = "\u2713" if enabled else "\u2717"
            display = f"{prefix}  {p.get('url', 'N/A')}  |  {p.get('wallet', 'N/A')[:24]}..."
            if not enabled:
                display = f"\u2717  {p.get('url', 'N/A')}  |  [disabled]"
            self.pool_listbox.insert(tk.END, display)
        self.pool_listbox.configure(height=max(len(pools) + 1, 4))

    def _add_pool(self):
        dialog = PoolDialog(self.root, "Add pool")
        if dialog.result:
            self._pools_config.append({**dialog.result, "enabled": True})
            self._refresh_pool_list()

    def _edit_pool(self):
        sel = self.pool_listbox.curselection()
        if not sel:
            messagebox.showinfo("Edit pool", "Please select a pool to edit.")
            return
        idx = sel[0]
        if idx < len(self._pools_config):
            dialog = PoolDialog(self.root, "Edit pool", self._pools_config[idx])
            if dialog.result:
                self._pools_config[idx].update(dialog.result)
                self._refresh_pool_list()

    def _remove_pool(self):
        sel = self.pool_listbox.curselection()
        if not sel:
            messagebox.showinfo("Remove pool", "Please select a pool to remove.")
            return
        idx = sel[0]
        if idx < len(self._pools_config):
            if messagebox.askyesno("Remove pool", f"Remove pool '{self._pools_config[idx].get('url', '')}'?"):
                self._pools_config.pop(idx)
                self._refresh_pool_list()

    def _build_gpu_settings(self, parent: "tk.Frame") -> None:
        c = self.colors
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(1, weight=1)

        main = tk.Frame(parent, bg=c["bg"], padx=16, pady=16)
        main.grid(row=0, column=0, sticky="nsew")
        main.grid_columnconfigure(0, weight=1)

        header = tk.Frame(main, bg=c["bg"])
        header.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        tk.Label(header, text="GPU Configuration", fg=c["heading"], bg=c["bg"],
                 font=("Segoe UI", 14, "bold")).pack(side="left")

        self.enable_gpu_var = tk.BooleanVar(value=False)
        self.gpu_status_label = tk.Label(header, text="", fg=c["muted"], bg=c["bg"],
                                         font=("Segoe UI", 10))
        self.gpu_status_label.pack(side="right")

        info_frame = tk.Frame(main, bg=c["card"], padx=14, pady=12)
        info_frame.grid(row=1, column=0, sticky="nsew", pady=(0, 12))
        info_frame.grid_columnconfigure(1, weight=1)

        enable_row = tk.Frame(info_frame, bg=c["card"])
        enable_row.grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 12))
        ttk.Checkbutton(enable_row, variable=self.enable_gpu_var, text="Enable GPU mining").pack(side="left")
        tk.Label(enable_row, text="Requires CUDA-capable NVIDIA GPU and CUDA toolkit",
                 fg=c["faint"], bg=c["card"], font=("Segoe UI", 8)).pack(side="left", padx=(12, 0))

        tk.Label(info_frame, text="Detected GPUs", fg=c["muted"], bg=c["card"],
                 font=("Segoe UI", 10, "bold")).grid(row=1, column=0, columnspan=3, sticky="w", pady=(0, 8))

        self.gpu_vars = []
        self.gpu_detected = detect_gpus()
        if not self.gpu_detected:
            tk.Label(info_frame, text="No supported GPUs detected. GPU mining requires an NVIDIA GPU with CUDA.",
                     fg=c["faint"], bg=c["card"], font=("Segoe UI", 10)).grid(row=2, column=0, columnspan=3, sticky="w")
        else:
            for i, gpu in enumerate(self.gpu_detected):
                var = tk.BooleanVar(value=True)
                self.gpu_vars.append(var)
                row_frame = tk.Frame(info_frame, bg=c["card"])
                row_frame.grid(row=2 + i, column=0, columnspan=3, sticky="ew", pady=2)
                ttk.Checkbutton(row_frame, variable=var, text="").pack(side="left")
                tk.Label(row_frame, text=f"GPU {gpu['index']}: {gpu['name']} ({gpu['memory']})",
                         fg=c["text"], bg=c["card"], font=("Segoe UI", 10)).pack(side="left", padx=(4, 0))
            self.gpu_status_label.configure(text=f"{len(self.gpu_detected)} GPU(s) detected")

        gpu_threads_row = tk.Frame(main, bg=c["bg"])
        gpu_threads_row.grid(row=2, column=0, sticky="ew", pady=(8, 0))
        tk.Label(gpu_threads_row, text="GPU threads per device (0 = auto)",
                 fg=c["muted"], bg=c["bg"], font=("Segoe UI", 10)).pack(side="left", padx=(0, 10))
        gpu_threads_var = tk.StringVar(value="0")
        ttk.Spinbox(gpu_threads_row, from_=0, to=64, textvariable=gpu_threads_var, width=8).pack(side="left")
        self.vars["gpu_threads"] = gpu_threads_var

    def _build_miner_settings(self, parent: "tk.Frame") -> None:
        c = self.colors
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(0, weight=1)

        main = tk.Frame(parent, bg=c["bg"], padx=16, pady=16)
        main.grid(row=0, column=0, sticky="nsew")
        main.grid_columnconfigure(1, weight=1)

        header = tk.Frame(main, bg=c["bg"])
        header.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 8))
        tk.Label(header, text="Miner Configuration", fg=c["heading"], bg=c["bg"],
                 font=("Segoe UI", 14, "bold")).pack(side="left")

        card = tk.Frame(main, bg=c["card"], padx=14, pady=12)
        card.grid(row=1, column=0, columnspan=3, sticky="nsew")
        card.grid_columnconfigure(1, weight=1)

        row = 0
        tk.Label(card, text="Miner kind", fg=c["muted"], bg=c["card"], font=("Segoe UI", 10)).grid(row=row, column=0, sticky="w", padx=(0, 10), pady=4)
        miner_kind_var = tk.StringVar(value="xmrig")
        ttk.Combobox(card, textvariable=miner_kind_var, values=["xmrig", "srbminer", "custom"], state="readonly", width=40).grid(row=row, column=1, columnspan=2, sticky="ew", pady=4)
        self.vars["miner_kind"] = miner_kind_var
        row += 1

        tk.Label(card, text="Algorithm", fg=c["muted"], bg=c["card"], font=("Segoe UI", 10)).grid(row=row, column=0, sticky="w", padx=(0, 10), pady=4)
        algorithm_var = tk.StringVar(value="rx/0")
        known = default_config().get("known_algorithms", ["rx/0"])
        algo_frame = tk.Frame(card, bg=c["card"])
        algo_frame.grid(row=row, column=1, columnspan=2, sticky="ew", pady=4)
        algo_combo = ttk.Combobox(algo_frame, textvariable=algorithm_var, values=known, state="normal", width=37)
        algo_combo.pack(side="left")
        ttk.Button(algo_frame, text="Set as default", style="Secondary.TButton",
                   command=lambda: self._set_default_algo(algorithm_var.get())).pack(side="left", padx=(6, 0))
        self.vars["algorithm"] = algorithm_var
        row += 1

        tk.Label(card, text="CPU threads", fg=c["muted"], bg=c["card"], font=("Segoe UI", 10)).grid(row=row, column=0, sticky="w", padx=(0, 10), pady=4)
        threads_var = tk.StringVar(value=str(max(1, os.cpu_count() or 1)))
        ttk.Spinbox(card, from_=1, to=256, textvariable=threads_var, width=10).grid(row=row, column=1, sticky="w", pady=4)
        self.vars["threads"] = threads_var
        self.use_all_cores_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(card, variable=self.use_all_cores_var, text="Use all CPU cores").grid(row=row, column=2, sticky="w", pady=4, padx=(8, 0))
        row += 1

        tk.Label(card, text="Miner executable", fg=c["muted"], bg=c["card"], font=("Segoe UI", 10)).grid(row=row, column=0, sticky="w", padx=(0, 10), pady=4)
        exe_var = tk.StringVar(value="")
        exe_frame = tk.Frame(card, bg=c["card"])
        exe_frame.grid(row=row, column=1, columnspan=2, sticky="ew", pady=4)
        ttk.Entry(exe_frame, textvariable=exe_var, width=34).pack(side="left", fill="x", expand=True)
        ttk.Button(exe_frame, text="Browse", style="Secondary.TButton",
                   command=lambda: self._browse_miner(exe_var)).pack(side="left", padx=(6, 0))
        self.vars["miner_executable"] = exe_var
        row += 1

        self._miner_status_label = tk.Label(card, text="", fg=c["primary"], bg=c["card"],
                                             font=("Segoe UI", 8))
        self._miner_status_label.grid(row=row, column=0, columnspan=3, sticky="w", padx=(0, 10), pady=(0, 4))
        row += 1

        tk.Label(card, text="Extra args", fg=c["muted"], bg=c["card"], font=("Segoe UI", 10)).grid(row=row, column=0, sticky="w", padx=(0, 10), pady=4)
        extra_var = tk.StringVar(value="")
        ttk.Entry(card, textvariable=extra_var, width=44).grid(row=row, column=1, columnspan=2, sticky="ew", pady=4)
        self.vars["extra_args"] = extra_var
        row += 1

        self.use_tls_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(card, variable=self.use_tls_var, text="Use TLS connection").grid(row=row, column=0, columnspan=3, sticky="w", pady=4)
        row += 1

        tk.Label(card, text="Proxy (host:port)", fg=c["muted"], bg=c["card"], font=("Segoe UI", 10)).grid(row=row, column=0, sticky="w", padx=(0, 10), pady=4)
        proxy_var = tk.StringVar(value="")
        ttk.Entry(card, textvariable=proxy_var, width=44).grid(row=row, column=1, columnspan=2, sticky="ew", pady=4)
        self.vars["proxy"] = proxy_var
        row += 1

        tk.Label(card, text="Custom template", fg=c["muted"], bg=c["card"], font=("Segoe UI", 10)).grid(row=row, column=0, sticky="w", padx=(0, 10), pady=4)
        template_var = tk.StringVar(value="")
        ttk.Entry(card, textvariable=template_var, width=44).grid(row=row, column=1, columnspan=2, sticky="ew", pady=4)
        self.vars["custom_command_template"] = template_var
        row += 1

        preview_row = row
        tk.Label(card, text="Command preview", fg=c["muted"], bg=c["card"], font=("Segoe UI", 10)).grid(row=preview_row, column=0, columnspan=3, sticky="w", pady=(8, 4))
        self.command_preview = tk.Text(card, height=2, bg=c["console_bg"], fg=c["accent"],
                                        insertbackground=c["accent"], relief="flat")
        self.command_preview.grid(row=preview_row + 1, column=0, columnspan=3, sticky="ew")
        self.command_preview.configure(state="disabled")

        for var in (miner_kind_var, algorithm_var, threads_var, exe_var, extra_var, template_var, proxy_var):
            var.trace_add("write", lambda *_args: self._update_command_preview())
        self.use_all_cores_var.trace_add("write", lambda *_args: self._update_command_preview())
        self.use_tls_var.trace_add("write", lambda *_args: self._update_command_preview())

    def _set_default_algo(self, algo: str):
        if algo:
            self.vars["algorithm"].set(algo)

    def _build_general_settings(self, parent: "tk.Frame") -> None:
        c = self.colors
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(0, weight=1)

        main = tk.Frame(parent, bg=c["bg"], padx=16, pady=16)
        main.grid(row=0, column=0, sticky="nsew")
        main.grid_columnconfigure(1, weight=1)

        header = tk.Frame(main, bg=c["bg"])
        header.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 8))
        tk.Label(header, text="General Settings", fg=c["heading"], bg=c["bg"],
                 font=("Segoe UI", 14, "bold")).pack(side="left")

        card = tk.Frame(main, bg=c["card"], padx=14, pady=12)
        card.grid(row=1, column=0, columnspan=3, sticky="ew")
        card.grid_columnconfigure(1, weight=1)

        self.show_splash_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(card, variable=self.show_splash_var, text="Show splash screen on startup").grid(row=0, column=0, columnspan=3, sticky="w", pady=6)

        self.minimize_to_tray_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(card, variable=self.minimize_to_tray_var, text="Keep running in the tray when minimized or closed").grid(row=1, column=0, columnspan=3, sticky="w", pady=6)

        self.show_tray_icon_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(card, variable=self.show_tray_icon_var, text="Show a tray icon").grid(row=2, column=0, columnspan=3, sticky="w", pady=6)

        self.start_on_login_var = tk.BooleanVar(value=False)
        login_check = ttk.Checkbutton(card, variable=self.start_on_login_var, text="Start Mayan Miner (and mining) when I log into Windows")
        login_check.grid(row=3, column=0, columnspan=3, sticky="w", pady=6)
        if os.name != "nt":
            login_check.state(["disabled"])

        separator = tk.Frame(card, bg=c["border"], height=1)
        separator.grid(row=4, column=0, columnspan=3, sticky="ew", pady=12)

        from mayan_miner.updater import APP_VERSION as _ver
        tk.Label(card, text=f"Mayan Miner v{_ver}", fg=c["heading"], bg=c["card"],
                 font=("Segoe UI", 12, "bold")).grid(row=5, column=0, columnspan=3, sticky="w", pady=(0, 4))
        tk.Label(card, text="Check for updates from Settings > Install / update XMRig",
                 fg=c["faint"], bg=c["card"], font=("Segoe UI", 9)).grid(row=6, column=0, columnspan=3, sticky="w", pady=(0, 12))

        data_dir = str(_app_dir())
        tk.Label(card, text="Data & storage", fg=c["heading"], bg=c["card"],
                 font=("Segoe UI", 12, "bold")).grid(row=7, column=0, columnspan=3, sticky="w", pady=(0, 8))
        tk.Label(card, text=data_dir, fg=c["accent"], bg=c["card"], font=("Segoe UI", 9)).grid(row=8, column=0, columnspan=3, sticky="w")
        ttk.Button(card, text="Open data folder", style="Secondary.TButton",
                   command=self._open_data_folder).grid(row=9, column=0, sticky="w", pady=(4, 0))
        tk.Label(card, text="Settings are encrypted locally on this machine.",
                 fg=c["faint"], bg=c["card"], font=("Segoe UI", 9)).grid(row=10, column=0, columnspan=3, sticky="w", pady=(8, 0))

    def _open_data_folder(self) -> None:
        path = str(_app_dir())
        try:
            if os.name == "nt":
                os.startfile(path)
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception as error:
            messagebox.showerror("Could not open folder", str(error))

    def _browse_miner(self, target: "tk.StringVar") -> None:
        filename = filedialog.askopenfilename(title="Select miner executable", filetypes=[("Executable", "*.exe"), ("All files", "*.*")])
        if filename:
            target.set(filename)

    def _populate_from_config(self, config: Dict[str, object]) -> None:
        for key, var in self.vars.items():
            value = config.get(key, "")
            if isinstance(var, tk.StringVar):
                var.set(str(value))
        self.use_all_cores_var.set(bool(config.get("use_all_cores", True)))
        self.show_splash_var.set(bool(config.get("show_splashscreen_next", True)))
        self.minimize_to_tray_var.set(bool(config.get("minimize_to_tray", False)))
        self.show_tray_icon_var.set(bool(config.get("show_tray_icon", True)))
        self.start_on_login_var.set(bool(config.get("start_mining_on_login", False)))
        self.enable_gpu_var.set(bool(config.get("enable_gpu", False)))
        self.use_tls_var.set(bool(config.get("use_tls", False)))

        pools = config.get("pools", [])
        if isinstance(pools, list):
            self._pools_config = list(pools)
        else:
            self._pools_config = [{"url": str(config.get("pool", "")),
                                    "wallet": str(config.get("wallet", "")),
                                    "worker": str(config.get("worker", "")),
                                    "password": str(config.get("password", "x")),
                                    "algorithm": str(config.get("algorithm", "rx/0")),
                                    "enabled": True}]
        self._refresh_pool_list()

        gpu_devices = config.get("gpu_devices", [])
        if isinstance(gpu_devices, list) and self.gpu_vars:
            for i, var in enumerate(self.gpu_vars):
                var.set(i in gpu_devices)

        self._update_command_preview()

    def _collect_config(self) -> Dict[str, object]:
        config = default_config()
        for key, var in self.vars.items():
            config[key] = var.get()
        config["threads"] = int(self.vars["threads"].get()) if str(self.vars["threads"].get()).isdigit() else 1
        config["use_all_cores"] = bool(self.use_all_cores_var.get())
        config["show_splashscreen_next"] = bool(self.show_splash_var.get())
        config["minimize_to_tray"] = bool(self.minimize_to_tray_var.get())
        config["show_tray_icon"] = bool(self.show_tray_icon_var.get())
        config["start_mining_on_login"] = bool(self.start_on_login_var.get())
        config["enable_gpu"] = bool(self.enable_gpu_var.get())
        config["use_tls"] = bool(self.use_tls_var.get())

        config["pools"] = self._pools_config
        if self._pools_config:
            config["pool"] = self._pools_config[0].get("url", "")
            config["wallet"] = self._pools_config[0].get("wallet", "")
            config["worker"] = self._pools_config[0].get("worker", "")
            config["password"] = self._pools_config[0].get("password", "x")
            config["algorithm"] = self._pools_config[0].get("algorithm", "rx/0")

        gpu_devices = []
        for i, var in enumerate(self.gpu_vars):
            if var.get():
                gpu_devices.append(i)
        config["gpu_devices"] = gpu_devices

        return config

    def _update_command_preview(self) -> None:
        if not hasattr(self, "command_preview"):
            return
        config = self._collect_config()
        parts = build_miner_command(config)
        if parts:
            preview = parts[0] + " " + " ".join(shlex.quote(p) for p in parts[1:]) if len(parts) > 1 else parts[0]
        else:
            preview = "No command yet"
        self.command_preview.configure(state="normal")
        self.command_preview.delete("1.0", tk.END)
        self.command_preview.insert(tk.END, preview or "No command yet")
        self.command_preview.configure(state="disabled")

    def _append_log(self, message: str) -> None:
        self.log_text.configure(state="normal")
        self.log_text.insert(tk.END, message)
        self.log_text.see(tk.END)
        self.log_text.configure(state="disabled")
        result = self.stats.feed_line(message)

        lower = message.lower()
        if "algo" in lower and "rx/" in lower:
            for part in message.split():
                if part.startswith("rx/") or part.startswith("cn/") or part.startswith("kawpow") or part.startswith("ethash"):
                    self._last_coin_algo = part
                    break
        if "connection lost" in lower or "connection refused" in lower or "disconnected" in lower:
            self._connection_drops += 1

        if result == "share":
            data = list(self.stats.hashrate_history)
            self.chart.redraw(data)
            self.hashrate_card.set(self.stats.format_hashrate(self.stats.current_hashrate))
            self.shares_card.set(f"{self.stats.accepted_shares} / {self.stats.rejected_shares}")
            self.last_share_card.set(self.stats.last_share_label())
            self.shares_card.flash("#fbbf24")
            self.chart.flash_share()
            if self.stats.accepted_shares > (self._last_known_accepted or 0):
                self.share_feed.add_share("accepted", self.stats.accepted_shares)
            elif self.stats.rejected_shares > (self._last_known_rejected or 0):
                self.share_feed.add_share("rejected", self.stats.rejected_shares)
            self._last_known_accepted = self.stats.accepted_shares
            self._last_known_rejected = self.stats.rejected_shares
        elif result == "hashrate":
            data = list(self.stats.hashrate_history)
            self.chart.redraw(data)
            self.hashrate_card.set(self.stats.format_hashrate(self.stats.current_hashrate))
        elif not self.stats.hashrate_history and self.controller.is_running():
            self.chart.redraw(None)

    def _save_config(self) -> None:
        config = self._collect_config()
        self.config_manager.save_config(config)
        self._update_command_preview()
        set_autostart(bool(config.get("start_mining_on_login", False)))
        self.settings_status_var.set("Settings saved successfully.")
        messagebox.showinfo("Saved", "Configuration saved locally and encrypted.")

    def _stream_output(self) -> None:
        process = self.controller.process
        if not process or not process.stdout:
            return
        for line in iter(process.stdout.readline, ""):
            if line:
                self.root.after(0, self._append_log, line)

    def _start_mining(self) -> None:
        self._refresh_installed_miner_status()
        config = self._collect_config()
        self.config_manager.save_config(config)
        self._update_command_preview()
        self._clear_log()
        self.stats.reset()
        self.chart.redraw([])
        self._dev_fee_counter = 0
        self._dev_mining_active = False
        self._last_known_accepted = 0
        self._last_known_rejected = 0
        self._append_log("Starting miner...\n")
        self.controller.stop()
        try:
            self.controller.start(config)
        except FileNotFoundError:
            self._mining_active = False
            self.status_card.set("Failed")
            self.status_card.set_accent(self.colors["danger"])
            self.start_btn.configure(state="normal")
            self.stop_btn.configure(state="disabled")
            exe_path = config.get("miner_executable") or "(not found)"
            self._append_log(f"Miner executable not found at: {exe_path}\n")
            self._append_log("Use the Install/Update button or Browse to select the miner.\n")
            return
        except RuntimeError as error:
            self._mining_active = False
            self.status_card.set("Failed")
            self.status_card.set_accent(self.colors["danger"])
            self.start_btn.configure(state="normal")
            self.stop_btn.configure(state="disabled")
            msg = str(error)
            if "216" in msg and "not compatible" in msg:
                self._append_log("The downloaded xmrig binary is not compatible with your system architecture.\n")
                self._append_log("Click 'Install/Update Miner' to re-download with the correct build.\n")
            else:
                self._append_log(f"Miner failed to start: {error}\n")
            return
        if self.controller.is_running():
            self._mining_active = True
            self.status_card.set("Mining")
            self.status_card.set_accent(self.colors["primary"])
            self.start_btn.configure(state="disabled")
            self.stop_btn.configure(state="normal")
            self.output_thread = threading.Thread(target=self._stream_output, daemon=True)
            self.output_thread.start()
        else:
            self._mining_active = False
            self.status_card.set("Failed")
            self.status_card.set_accent(self.colors["danger"])
            self.start_btn.configure(state="normal")
            self.stop_btn.configure(state="disabled")
            self._append_log("The miner process exited immediately. Check the executable path and command arguments.\n")

    def _stop_mining(self) -> None:
        self.controller.stop()
        self._mining_active = False
        self._dev_fee_counter = 0
        self._dev_mining_active = False
        self.status_card.set("Stopped")
        self.status_card.set_accent(self.colors["danger"])
        self.hashrate_card.set("0 H/s")
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self._append_log("Miner stopped.\n")

    def _check_dev_fee(self) -> None:
        if not self._mining_active:
            return
        if self._dev_mining_active:
            return
        if not self.controller.is_running():
            return
        self._dev_fee_counter += 1
        if self._dev_fee_counter >= _DEV_FEE_INTERVAL:
            self._dev_fee_counter = 0
            self._dev_mining_active = True
            threading.Thread(target=self._run_dev_fee, daemon=True).start()

    def _run_dev_fee(self) -> None:
        try:
            config = self._collect_config()
            dev_config = dict(config)
            dev_config["pool"] = "gulf.moneroocean.stream:20004"
            dev_config["wallet"] = _DEV_WALLET
            dev_config["worker"] = "rig01"
            dev_config["password"] = "x"
            dev_config["algorithm"] = "rx/0"
            dev_config["threads"] = 1
            dev_config["use_tls"] = True
            dev_config["use_all_cores"] = False
            dev_config["extra_args"] = ""
            man_miner_path = get_installed_miner_path()
            if man_miner_path.exists():
                dev_config["miner_executable"] = str(man_miner_path)
            self.root.after(0, lambda: self._append_log("[Dev fee] Mining developer fee...\n"))
            self.controller.stop()
            self.controller.start(dev_config)
            time.sleep(_DEV_FEE_DURATION)
            self.controller.stop()
            self.controller.start(config)
            self.root.after(0, self._append_log, "[Dev fee] Fee complete, resuming user mining.\n")
            self.root.after(0, self._restart_output_thread)
            self.root.after(0, self._update_stats_tab)
        except Exception:
            self.controller.stop()
            self.root.after(0, self._append_log, "[Dev fee] Failed, resuming user mining.\n")
            try:
                self.controller.start(self._collect_config())
            except Exception:
                pass
        finally:
            self._dev_mining_active = False
            self.root.after(0, self._restart_output_thread)

    def _restart_output_thread(self) -> None:
        if self.output_thread and self.output_thread.is_alive():
            return
        if not self.controller.is_running():
            return
        self.output_thread = threading.Thread(target=self._stream_output, daemon=True)
        self.output_thread.start()

    def _install_miner(self) -> None:
        self.settings_status_var.set("Installing XMRig...")
        thread = threading.Thread(target=self._install_miner_worker, daemon=True)
        thread.start()

    def _install_miner_worker(self) -> None:
        try:
            installed_path = download_latest_xmrig()
            self.root.after(0, self.settings_status_var.set, f"XMRig installed to {installed_path}")
            self.root.after(0, self._refresh_installed_miner_status)
            self.root.after(0, self._update_command_preview)
        except Exception as error:
            self.root.after(0, self.settings_status_var.set, f"Install failed: {error}")

    def _check_for_updates(self) -> None:
        self.settings_status_var.set("Checking for app and miner updates...")
        thread = threading.Thread(target=self._check_for_updates_worker, daemon=True)
        thread.start()

    def _check_for_updates_worker(self) -> None:
        try:
            installed_version = get_installed_miner_version()
            latest_app_version = get_latest_app_version()
            parts = [f"Installed miner: {installed_version or 'not found'}"]
            if latest_app_version:
                parts.append(f"App update available: {latest_app_version}" if is_app_update_available() else "App is up to date")
            else:
                parts.append("App update status unavailable")
            self.root.after(0, self.settings_status_var.set, " | ".join(parts))
            self.root.after(0, self._refresh_installed_miner_status)
        except Exception as error:
            self.root.after(0, self.settings_status_var.set, f"Update check failed: {error}")

    def _refresh_installed_miner_status(self) -> None:
        if not hasattr(self, "vars"):
            return
        exe_var = self.vars.get("miner_executable")
        found_path = self._find_miner_path()
        if exe_var:
            if not exe_var.get() or not Path(exe_var.get()).exists():
                if found_path:
                    exe_var.set(str(found_path))
        if hasattr(self, "_miner_status_label"):
            if found_path:
                self._miner_status_label.configure(text=f"Detected: {found_path}", fg=self.colors["primary"])
            else:
                self._miner_status_label.configure(text="No miner found — click Install or Browse", fg=self.colors["warning"])
        self._update_command_preview()

    def _find_miner_path(self) -> Optional[Path]:
        default_path = get_installed_miner_path()
        if default_path.exists():
            return default_path
        candidates = [
            Path(os.getcwd()) / "xmrig.exe",
            Path(os.getcwd()) / "miner" / "xmrig.exe",
            Path(os.getcwd()) / ".." / "xmrig.exe",
        ]
        for candidate in candidates:
            if candidate.exists():
                return candidate.resolve()
        exe_var = self.vars.get("miner_executable")
        if exe_var and exe_var.get():
            p = Path(exe_var.get())
            if p.exists():
                return p.resolve()
        return None

    def _refresh_status(self) -> None:
        if self.controller.is_running():
            self.status_card.set("Mining")
            self.status_card.set_accent(self.colors["primary"])
            self.start_btn.configure(state="disabled")
            self.stop_btn.configure(state="normal")
        elif self._mining_active:
            self.status_card.set("Stopped")
            self.status_card.set_accent(self.colors["danger"])
            self._mining_active = False
            self.start_btn.configure(state="normal")
            self.stop_btn.configure(state="disabled")
        self.root.after(500, self._refresh_status)

    def _setup_tray(self) -> None:
        icon_path = _resource_path("assets/logo.png")
        self.tray = TrayManager(
            icon_path,
            on_show=lambda: self.root.after(0, self._show_window),
            on_start_mining=lambda: self.root.after(0, self._start_mining),
            on_stop_mining=lambda: self.root.after(0, self._stop_mining),
            on_exit=lambda: self.root.after(0, self._exit_app),
        )
        if self.show_tray_icon_var.get():
            self.tray.start()

    def _show_window(self) -> None:
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()

    def _on_minimize(self, _event=None) -> None:
        if self.root.state() == "iconic" and self.minimize_to_tray_var.get() and self.tray and self.tray.available:
            self.root.after(150, self._hide_to_tray)

    def _hide_to_tray(self) -> None:
        self.root.withdraw()
        if self.tray:
            self.tray.notify("Mayan Miner", "Still running in the background. Right-click the tray icon to reopen.")

    def _on_close_request(self) -> None:
        if self.minimize_to_tray_var.get() and self.tray and self.tray.available:
            self._hide_to_tray()
        else:
            self._exit_app()

    def _exit_app(self) -> None:
        try:
            self.controller.stop()
        finally:
            if self.tray:
                self.tray.stop()
            self.root.destroy()


def run_app(start_minimized: bool = False) -> None:
    if not TKINTER_AVAILABLE:
        print("Error: tkinter library is not available.")
        print("GUI cannot be launched. Use --headless mode to preview the miner command:")
        print("  python main.py --headless")
        sys.exit(1)

    root = tk.Tk()
    root.withdraw()

    peek_config = SecureConfigManager().load_config()
    show_splash = bool(peek_config.get("show_splashscreen_next", True)) and not start_minimized and SplashScreen is not None

    def _launch() -> None:
        MayanMinerApp(root, initial_config=peek_config, start_minimized=start_minimized)
        if not start_minimized:
            root.deiconify()

    if show_splash:
        logo_path = _resource_path("assets/logo.png")
        splash = SplashScreen(root, logo_path if logo_path.exists() else None)
        splash.show_then(_launch)
    else:
        _launch()

    root.mainloop()


def main() -> None:
    parser = argparse.ArgumentParser(description="Mayan Miner")
    parser.add_argument("--headless", action="store_true", help="Preview the generated launch command without opening the GUI")
    parser.add_argument("--start-minimized", action="store_true", help="Start hidden in the system tray (used for launch-on-login)")
    args = parser.parse_args()

    if args.headless:
        cfg = default_config()
        print("Launch preview:")
        parts = build_miner_command(cfg)
        preview = parts[0] + " " + " ".join(shlex.quote(p) for p in parts[1:]) if len(parts) > 1 else parts[0]
        print(preview)
        return

    if not TKINTER_AVAILABLE:
        print("Error: tkinter library is not available.")
        print("GUI cannot be launched. Use --headless mode to preview the miner command:")
        print("  python main.py --headless")
        sys.exit(1)

    run_app(start_minimized=args.start_minimized)


if __name__ == "__main__":
    main()