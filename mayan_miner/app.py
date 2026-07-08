import argparse
import os
import shlex
import subprocess
import sys
import threading
import webbrowser
from pathlib import Path
from typing import Dict, Optional


def _resource_path(relative_path: str) -> Path:
    """Resolve a bundled resource both when running from source and when
    running as a frozen PyInstaller --onefile executable.

    PyInstaller extracts bundled data files to a temporary directory exposed
    as sys._MEIPASS at runtime; when running from source there is no such
    attribute and we fall back to the project root (parent of this package).
    """
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
from mayan_miner.config import SecureConfigManager, default_config, _app_dir
from mayan_miner.miner import MinerController, build_miner_command
from mayan_miner.stats import MiningStatsTracker, sanitize_line
from mayan_miner.tray import TrayManager
from mayan_miner.updater import (
    download_latest_xmrig,
    get_installed_miner_version,
    get_latest_app_version,
    is_app_update_available,
)

try:
    from mayan_miner.splash import SplashScreen
except ImportError:  # pragma: no cover - only if tkinter missing
    SplashScreen = None

try:
    from mayan_miner.widgets import RealtimeChart, StatCard
except ImportError:  # pragma: no cover - only if tkinter missing
    RealtimeChart = None
    StatCard = None


DARK_PALETTE = {
    "bg": "#07111f", "surface": "#0f172a", "card": "#111827", "card_alt": "#0f1724",
    "heading": "#f8fafc", "text": "#e2e8f0", "muted": "#94a3b8", "faint": "#64748b",
    "accent": "#06b6d4", "primary": "#10b981", "primary_hover": "#0ea46a", "danger": "#f87171",
    "border": "#1e293b", "console_bg": "#020617", "console_text": "#f8fafc", "nav_active": "#111827",
    "chart_line": "#34d399", "chart_fill": "#0f3b2c", "chart_grid": "#1e293b", "warning": "#f59e0b",
}
LIGHT_PALETTE = {
    "bg": "#eef2f7", "surface": "#ffffff", "card": "#ffffff", "card_alt": "#f8fafc",
    "heading": "#0b1220", "text": "#1e293b", "muted": "#64748b", "faint": "#94a3b8",
    "accent": "#0891b2", "primary": "#059669", "primary_hover": "#047857", "danger": "#dc2626",
    "border": "#e2e8f0", "console_bg": "#0f172a", "console_text": "#e2e8f0", "nav_active": "#e2e8f0",
    "chart_line": "#059669", "chart_fill": "#d1fae5", "chart_grid": "#e2e8f0", "warning": "#d97706",
}


class MayanMinerApp:
    def __init__(self, root: "tk.Tk", initial_config: Optional[Dict[str, object]] = None, start_minimized: bool = False) -> None:
        self.root = root
        self.config_manager = SecureConfigManager()
        self.controller = MinerController()
        self.stats = MiningStatsTracker()
        self.output_thread: Optional[threading.Thread] = None
        self.vars: Dict[str, "tk.Variable"] = {}
        self.tray: Optional[TrayManager] = None
        self._active_tab = "dashboard"
        self._mining_active = False

        config = initial_config or self.config_manager.load_config()
        self.colors = LIGHT_PALETTE if str(config.get("theme")) == "light" else DARK_PALETTE

        self.root.title("Mayan Miner")
        self.root.geometry("1180x800")
        self.root.minsize(1040, 720)
        self.root.configure(bg=self.colors["bg"])
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

    # ------------------------------------------------------------------ #
    # Theme / chrome
    # ------------------------------------------------------------------ #
    def _widget_palette(self) -> Dict[str, str]:
        """Map the app-level theme palette onto the color keys that the
        theme-aware StatCard / RealtimeChart widgets expect.

        Without this, those widgets fell back to their own hardcoded
        (dark-only) default colors regardless of which theme was selected,
        which is why the dashboard looked wrong / inconsistent on the light
        theme.
        """
        c = self.colors
        return {
            "card": c["card"],
            "card_alt": c["card_alt"],
            "card_label_fg": c["muted"],
            "value_fg": c["heading"],
            "console_bg": c["console_bg"],
            "console_text": c["console_text"],
            "accent": c["accent"],
            "muted": c["muted"],
            "faint": c["faint"],
            "line_color": c["chart_line"],
            "fill_color": c["chart_fill"],
            "grid_color": c["chart_grid"],
            "success": c["primary"],
            "warning": c["warning"],
            "danger": c["danger"],
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
        style.configure("TEntry", padding=4)
        style.configure("TCheckbutton", background=c["card"], foreground=c["text"])
        style.map("TCheckbutton", background=[("active", c["card"])])

        style.configure("Primary.TButton", background=c["primary"], foreground="#ffffff", padding=8, font=("Segoe UI", 10, "bold"))
        style.map("Primary.TButton", background=[("active", c["primary_hover"]), ("!disabled", c["primary"])], foreground=[("disabled", "#9ca3af")])

        style.configure("Secondary.TButton", background=c["card_alt"], foreground=c["text"], padding=6, font=("Segoe UI", 9))
        style.map("Secondary.TButton", background=[("active", c["border"]), ("!disabled", c["card_alt"])])

        style.configure("Danger.TButton", background=c["danger"], foreground="#ffffff", padding=6, font=("Segoe UI", 9, "bold"))
        style.map("Danger.TButton", background=[("active", "#dc2626"), ("!disabled", c["danger"])])

        style.configure("Nav.TButton", background=c["surface"], foreground=c["muted"], padding=(16, 10), font=("Segoe UI", 10, "bold"), borderwidth=0)
        style.map("Nav.TButton", background=[("active", c["nav_active"])])
        style.configure("NavActive.TButton", background=c["nav_active"], foreground=c["heading"], padding=(16, 10), font=("Segoe UI", 10, "bold"), borderwidth=0)

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
        self.settings_frame = tk.Frame(content, bg=c["bg"])
        for frame in (self.dashboard_frame, self.settings_frame):
            frame.grid(row=0, column=0, sticky="nsew")

        self._build_dashboard(self.dashboard_frame)
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
        tk.Label(title_box, text="Professional CPU-only mining launcher for Windows", fg=c["muted"], bg=c["surface"], font=("Segoe UI", 10)).pack(anchor="w", pady=(3, 0))

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
        self.nav_buttons: Dict[str, ttk.Button] = {}
        for key, label in (("dashboard", "Dashboard"), ("settings", "Settings")):
            btn = ttk.Button(nav, text=label, style="Nav.TButton", command=lambda k=key: self._show_tab(k))
            btn.pack(side="left", padx=(18 if key == "dashboard" else 4, 4), pady=(0, 0))
            self.nav_buttons[key] = btn
        tk.Frame(self.root, bg=c["border"], height=1).grid(row=1, column=0, sticky="sew")

    def _show_tab(self, tab: str) -> None:
        self._active_tab = tab
        (self.dashboard_frame if tab == "dashboard" else self.settings_frame).tkraise()
        for key, btn in self.nav_buttons.items():
            btn.configure(style="NavActive.TButton" if key == tab else "Nav.TButton")

    # ------------------------------------------------------------------ #
    # Dashboard tab
    # ------------------------------------------------------------------ #
    def _build_dashboard(self, parent: "tk.Frame") -> None:
        c = self.colors
        parent.grid_columnconfigure(0, weight=1)
        parent.grid_rowconfigure(2, weight=1)

        cards_row = tk.Frame(parent, bg=c["bg"])
        cards_row.grid(row=0, column=0, sticky="ew", pady=(4, 12))
        for i in range(4):
            cards_row.grid_columnconfigure(i, weight=1)

        palette = self._widget_palette()
        self.status_card = StatCard(cards_row, title="STATUS", initial_value="Ready", accent=c["primary"], palette=palette)
        self.hashrate_card = StatCard(cards_row, title="HASHRATE", initial_value="0 H/s", accent=c["accent"], palette=palette)
        self.shares_card = StatCard(cards_row, title="ACCEPTED / REJECTED", initial_value="0 / 0", accent=c["primary"], palette=palette)
        self.uptime_card = StatCard(cards_row, title="UPTIME", initial_value="00:00:00", accent=c["muted"], palette=palette)
        for index, card in enumerate((self.status_card, self.hashrate_card, self.shares_card, self.uptime_card)):
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
        ttk.Button(controls, text="Start mining", command=self._start_mining, style="Primary.TButton").pack(side="left", padx=(0, 8))
        ttk.Button(controls, text="Stop", command=self._stop_mining, style="Secondary.TButton").pack(side="left")

        self._build_dashboard_footer(parent)

    def _build_dashboard_footer(self, parent: "tk.Frame") -> None:
        c = self.colors
        footer = tk.Frame(parent, bg=c["bg"])
        footer.grid(row=3, column=0, sticky="ew", pady=(10, 2))
        footer.grid_columnconfigure(0, weight=1)

        links_row = tk.Frame(footer, bg=c["bg"])
        links_row.grid(row=0, column=0)  # no sticky -> stays centered in the cell

        footer_links = (
            ("\U0001F310", "Website", "https://mayanminer.vercel.app"),
            ("\U0001F512", "Privacy", "https://mayanminer.vercel.app/privacy.html"),
            ("\u2753", "How to use", "https://mayanminer.vercel.app/howtouse.html"),
            ("\u2764", "Donate", "https://mayanminer.vercel.app/donate.html"),
            ("\U0001F419", "GitHub", "https://github.com/bugsfreeweb/mayanminer"),
        )

        self._footer_link_labels = []
        for index, (icon, label, url) in enumerate(footer_links):
            link = tk.Label(
                links_row, text=f"{icon}  {label}", fg=c["muted"], bg=c["bg"],
                font=("Segoe UI", 9, "bold"), cursor="hand2", padx=10,
            )
            link.grid(row=0, column=index)
            link.bind("<Button-1>", lambda _event, u=url: webbrowser.open(u))
            link.bind("<Enter>", lambda _event, w=link: w.configure(fg=c["accent"]))
            link.bind("<Leave>", lambda _event, w=link: w.configure(fg=c["muted"]))
            self._footer_link_labels.append(link)

        credit = tk.Label(
            footer, text="\u00A9 Mayan Miner \u2014 crafted by bugsfreeweb",
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
        self.root.after(1000, self._tick_dashboard)

    # ------------------------------------------------------------------ #
    # Settings tab
    # ------------------------------------------------------------------ #
    def _build_settings(self, parent: "tk.Frame") -> None:
        c = self.colors
        canvas = tk.Canvas(parent, bg=c["bg"], highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scroll_area = tk.Frame(canvas, bg=c["bg"])
        scroll_area.bind("<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scroll_area, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        self._build_section(
            scroll_area, "Pool & wallet",
            [
                ("Pool URL", "pool", "entry", "mine.example.com:3333"),
                ("Wallet", "wallet", "entry", "YOUR_WALLET"),
                ("Worker", "worker", "entry", "mayan-cpu"),
                ("Password", "password", "entry", "x"),
            ],
        )
        self._build_miner_section(scroll_area)
        self._build_appearance_section(scroll_area)
        self._build_storage_section(scroll_area)

        buttons = tk.Frame(scroll_area, bg=c["bg"])
        buttons.pack(fill="x", padx=4, pady=(4, 20))
        ttk.Button(buttons, text="Save settings", command=self._save_config, style="Primary.TButton").pack(side="left", padx=(0, 8))
        ttk.Button(buttons, text="Install / update XMRig", command=self._install_miner, style="Secondary.TButton").pack(side="left", padx=(0, 8))
        ttk.Button(buttons, text="Check app update", command=self._check_for_updates, style="Secondary.TButton").pack(side="left")

        self.settings_status_var = tk.StringVar(value="")
        tk.Label(scroll_area, textvariable=self.settings_status_var, fg=c["muted"], bg=c["bg"], font=("Segoe UI", 9)).pack(anchor="w", padx=4)

    def _section_card(self, parent, title: str) -> "tk.Frame":
        c = self.colors
        card = tk.Frame(parent, bg=c["card"], padx=16, pady=14)
        card.pack(fill="x", padx=4, pady=(0, 12))
        card.grid_columnconfigure(1, weight=1)
        tk.Label(card, text=title, fg=c["heading"], bg=c["card"], font=("Segoe UI", 12, "bold")).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 10))
        return card

    def _build_section(self, parent, title: str, rows) -> None:
        c = self.colors
        card = self._section_card(parent, title)
        for index, (label, key, kind, default) in enumerate(rows, start=1):
            tk.Label(card, text=label, fg=c["muted"], bg=c["card"], font=("Segoe UI", 10)).grid(row=index, column=0, sticky="w", padx=(0, 10), pady=6)
            var = tk.StringVar(value=default)
            ttk.Entry(card, textvariable=var, width=44).grid(row=index, column=1, columnspan=2, sticky="ew", pady=6)
            self.vars[key] = var

    def _build_miner_section(self, parent) -> None:
        c = self.colors
        card = self._section_card(parent, "Miner & algorithm")

        row = 1
        tk.Label(card, text="Miner kind", fg=c["muted"], bg=c["card"], font=("Segoe UI", 10)).grid(row=row, column=0, sticky="w", padx=(0, 10), pady=6)
        miner_kind_var = tk.StringVar(value="xmrig")
        ttk.Combobox(card, textvariable=miner_kind_var, values=["xmrig", "srbminer", "custom"], state="readonly", width=41).grid(row=row, column=1, columnspan=2, sticky="ew", pady=6)
        self.vars["miner_kind"] = miner_kind_var
        row += 1

        tk.Label(card, text="Algorithm", fg=c["muted"], bg=c["card"], font=("Segoe UI", 10)).grid(row=row, column=0, sticky="w", padx=(0, 10), pady=6)
        algorithm_var = tk.StringVar(value="rx/0")
        known = default_config().get("known_algorithms", ["rx/0"])
        # Editable combobox: presets are offered, but any custom algorithm name can be typed.
        ttk.Combobox(card, textvariable=algorithm_var, values=known, state="normal", width=41).grid(row=row, column=1, columnspan=2, sticky="ew", pady=6)
        self.vars["algorithm"] = algorithm_var
        row += 1

        tk.Label(card, text="Threads", fg=c["muted"], bg=c["card"], font=("Segoe UI", 10)).grid(row=row, column=0, sticky="w", padx=(0, 10), pady=6)
        threads_var = tk.StringVar(value=str(max(1, os.cpu_count() or 1)))
        ttk.Spinbox(card, from_=1, to=256, textvariable=threads_var, width=12).grid(row=row, column=1, sticky="w", pady=6)
        self.vars["threads"] = threads_var
        self.use_all_cores_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(card, variable=self.use_all_cores_var, text="Use all CPU cores").grid(row=row, column=2, sticky="w", pady=6)
        row += 1

        tk.Label(card, text="Miner executable", fg=c["muted"], bg=c["card"], font=("Segoe UI", 10)).grid(row=row, column=0, sticky="w", padx=(0, 10), pady=6)
        exe_var = tk.StringVar(value="")
        ttk.Entry(card, textvariable=exe_var, width=34).grid(row=row, column=1, sticky="ew", pady=6)
        ttk.Button(card, text="Browse", style="Secondary.TButton", command=lambda: self._browse_miner(exe_var)).grid(row=row, column=2, padx=(6, 0), pady=6, sticky="w")
        self.vars["miner_executable"] = exe_var
        row += 1

        tk.Label(card, text="Extra args", fg=c["muted"], bg=c["card"], font=("Segoe UI", 10)).grid(row=row, column=0, sticky="w", padx=(0, 10), pady=6)
        extra_var = tk.StringVar(value="")
        ttk.Entry(card, textvariable=extra_var, width=44).grid(row=row, column=1, columnspan=2, sticky="ew", pady=6)
        self.vars["extra_args"] = extra_var
        row += 1

        tk.Label(card, text="Custom command template", fg=c["muted"], bg=c["card"], font=("Segoe UI", 10)).grid(row=row, column=0, sticky="w", padx=(0, 10), pady=6)
        template_var = tk.StringVar(value="")
        ttk.Entry(card, textvariable=template_var, width=44).grid(row=row, column=1, columnspan=2, sticky="ew", pady=6)
        self.vars["custom_command_template"] = template_var
        row += 1

        hint = (
            "Custom command template is only used when Miner kind = custom, and lets this app drive\n"
            "any other miner's own CLI syntax with {executable} {pool} {wallet} {worker} {password}\n"
            "{algorithm} {threads} {extra_args} placeholders. Leave it blank for the default behavior."
        )
        tk.Label(card, text=hint, fg=c["faint"], bg=c["card"], font=("Segoe UI", 8), justify="left").grid(row=row, column=0, columnspan=3, sticky="w", pady=(6, 0))

        preview_row = row + 1
        tk.Label(card, text="Launch command preview", fg=c["muted"], bg=c["card"], font=("Segoe UI", 10)).grid(row=preview_row, column=0, columnspan=3, sticky="w", pady=(12, 4))
        self.command_preview = tk.Text(card, height=3, bg=c["console_bg"], fg=c["accent"], insertbackground=c["accent"], relief="flat")
        self.command_preview.grid(row=preview_row + 1, column=0, columnspan=3, sticky="ew")
        self.command_preview.configure(state="disabled")

        for var in (miner_kind_var, algorithm_var, threads_var, exe_var, extra_var, template_var):
            var.trace_add("write", lambda *_args: self._update_command_preview())
        self.use_all_cores_var.trace_add("write", lambda *_args: self._update_command_preview())

    def _build_appearance_section(self, parent) -> None:
        c = self.colors
        card = self._section_card(parent, "Appearance & behavior")

        tk.Label(card, text="Theme", fg=c["muted"], bg=c["card"], font=("Segoe UI", 10)).grid(row=1, column=0, sticky="w", padx=(0, 10), pady=6)
        theme_var = tk.StringVar(value="dark")
        ttk.Combobox(card, textvariable=theme_var, values=["dark", "light", "system"], state="readonly", width=41).grid(row=1, column=1, columnspan=2, sticky="ew", pady=6)
        self.vars["theme"] = theme_var
        tk.Label(card, text="Theme changes apply the next time the app starts.", fg=c["faint"], bg=c["card"], font=("Segoe UI", 8)).grid(row=2, column=1, columnspan=2, sticky="w")

        self.show_splash_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(card, variable=self.show_splash_var, text="Show splash screen on startup").grid(row=3, column=0, columnspan=3, sticky="w", pady=(12, 4))

        self.minimize_to_tray_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(card, variable=self.minimize_to_tray_var, text="Keep running in the tray when minimized or closed").grid(row=4, column=0, columnspan=3, sticky="w", pady=4)

        self.show_tray_icon_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(card, variable=self.show_tray_icon_var, text="Show a tray icon").grid(row=5, column=0, columnspan=3, sticky="w", pady=4)

        self.start_on_login_var = tk.BooleanVar(value=False)
        login_check = ttk.Checkbutton(card, variable=self.start_on_login_var, text="Start Mayan Miner (and mining) when I log into Windows")
        login_check.grid(row=6, column=0, columnspan=3, sticky="w", pady=4)
        if os.name != "nt":
            login_check.state(["disabled"])
            tk.Label(card, text="Windows-only feature.", fg=c["faint"], bg=c["card"], font=("Segoe UI", 8)).grid(row=7, column=0, columnspan=3, sticky="w")

    def _build_storage_section(self, parent) -> None:
        c = self.colors
        card = self._section_card(parent, "Data & storage")
        data_dir = str(_app_dir())
        tk.Label(card, text="All settings, the encryption key, and the downloaded miner are stored in:", fg=c["muted"], bg=c["card"], font=("Segoe UI", 10)).grid(row=1, column=0, columnspan=3, sticky="w")
        tk.Label(card, text=data_dir, fg=c["accent"], bg=c["card"], font=("Segoe UI", 10, "bold")).grid(row=2, column=0, columnspan=3, sticky="w", pady=(2, 8))
        ttk.Button(card, text="Open data folder", style="Secondary.TButton", command=self._open_data_folder).grid(row=3, column=0, sticky="w")
        tk.Label(card, text="Settings are encrypted locally on this machine.", fg=c["faint"], bg=c["card"], font=("Segoe UI", 9)).grid(row=4, column=0, columnspan=3, sticky="w", pady=(10, 0))

    def _open_data_folder(self) -> None:
        path = str(_app_dir())
        try:
            if os.name == "nt":
                os.startfile(path)  # type: ignore[attr-defined]
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception as error:
            messagebox.showerror("Could not open folder", str(error))

    # ------------------------------------------------------------------ #
    # Config <-> UI
    # ------------------------------------------------------------------ #
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
        return config

    def _update_command_preview(self) -> None:
        if not hasattr(self, "command_preview"):
            return
        config = self._collect_config()
        preview = " ".join(shlex.quote(part) for part in build_miner_command(config))
        self.command_preview.configure(state="normal")
        self.command_preview.delete("1.0", tk.END)
        self.command_preview.insert(tk.END, preview or "No command yet")
        self.command_preview.configure(state="disabled")

    def _append_log(self, message: str) -> None:
        # Strip ANSI / VT escape codes from the rendered log too, otherwise
        # XMRig's colorized output (emitted even on a piped stdout on
        # Windows) shows up as raw "\x1b[1m\x1b[32m..." garbage in the log.
        clean_message = sanitize_line(message)
        self.log_text.configure(state="normal")
        self.log_text.insert(tk.END, clean_message)
        self.log_text.see(tk.END)
        self.log_text.configure(state="disabled")
        if self.stats.feed_line(message):
            self.chart.redraw(list(self.stats.hashrate_history))
            self.hashrate_card.set(self.stats.format_hashrate(self.stats.current_hashrate))
            self.shares_card.set(f"{self.stats.accepted_shares} / {self.stats.rejected_shares}")

    def _save_config(self) -> None:
        config = self._collect_config()
        self.config_manager.save_config(config)
        self._update_command_preview()
        set_autostart(bool(config.get("start_mining_on_login", False)))
        self.settings_status_var.set("Settings saved.")
        messagebox.showinfo("Saved", "Configuration saved locally and encrypted.")

    def _stream_output(self) -> None:
        process = self.controller.process
        if not process or not process.stdout:
            return
        for line in iter(process.stdout.readline, ""):
            if line:
                self.root.after(0, self._append_log, line)

    def _start_mining(self) -> None:
        config = self._collect_config()
        self.config_manager.save_config(config)
        self._update_command_preview()
        self._clear_log()
        self.stats.reset()
        self.chart.redraw([])
        self._append_log("Starting miner...\n")
        self.controller.stop()
        self.controller.start(config)
        if self.controller.is_running():
            self._mining_active = True
            self.status_card.set("Mining")
            self.output_thread = threading.Thread(target=self._stream_output, daemon=True)
            self.output_thread.start()
        else:
            self._mining_active = False
            self.status_card.set("Failed")
            self._append_log("The miner process exited immediately. Check the executable path and command arguments.\n")

    def _stop_mining(self) -> None:
        self.controller.stop()
        self._mining_active = False
        self.status_card.set("Stopped")
        self.hashrate_card.set("0 H/s")
        self._append_log("Miner stopped.\n")

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
        pass  # kept for future use; version now surfaced via settings_status_var

    def _refresh_status(self) -> None:
        if self.controller.is_running():
            self.status_card.set("Mining")
        elif self._mining_active:
            self.status_card.set("Stopped")
            self._mining_active = False
        self.root.after(500, self._refresh_status)

    # ------------------------------------------------------------------ #
    # Tray / window lifecycle
    # ------------------------------------------------------------------ #
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
        print(" ".join(shlex.quote(part) for part in build_miner_command(cfg)))
        return

    if not TKINTER_AVAILABLE:
        print("Error: tkinter library is not available.")
        print("GUI cannot be launched. Use --headless mode to preview the miner command:")
        print("  python main.py --headless")
        sys.exit(1)

    run_app(start_minimized=args.start_minimized)


if __name__ == "__main__":
    main()
