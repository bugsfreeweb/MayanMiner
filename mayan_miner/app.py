import argparse
import os
import re
import shlex
import sys
import threading
import time
from pathlib import Path
from typing import Dict, List, Optional

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

from mayan_miner.config import SecureConfigManager, default_config
from mayan_miner.miner import MinerController, build_miner_command
from mayan_miner.updater import (
    download_latest_xmrig,
    get_installed_miner_version,
    get_latest_app_version,
    is_app_update_available,
)


class SplashScreen:
    def __init__(self, parent: "tk.Tk") -> None:
        self.root = tk.Toplevel(parent)
        self.root.overrideredirect(True)
        self.root.configure(bg="#081120")
        self.root.attributes("-topmost", True)
        self.root.withdraw()
        self._build_ui(parent)

    def _build_ui(self, parent: "tk.Tk") -> None:
        width = 420
        height = 240
        x = parent.winfo_x() + max(0, (parent.winfo_width() - width) // 2)
        y = parent.winfo_y() + max(0, (parent.winfo_height() - height) // 2)
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        self.root.deiconify()

        frame = tk.Frame(self.root, bg="#081120")
        frame.pack(fill="both", expand=True, padx=22, pady=22)
        tk.Label(frame, text="Mayan Miner", fg="#f8fafc", bg="#081120", font=("Segoe UI", 24, "bold")).pack(anchor="w")
        tk.Label(frame, text="Starting a polished mining experience…", fg="#93c5fd", bg="#081120", font=("Segoe UI", 10)).pack(anchor="w", pady=(4, 16))

        logo_path = Path(__file__).resolve().parent.parent / "assets" / "logo.png"
        try:
            image = tk.PhotoImage(master=self.root, file=str(logo_path))
            tk.Label(frame, image=image, bg="#081120").pack(anchor="w", pady=(0, 12))
            self.logo_image = image
        except Exception:
            tk.Label(frame, text="◉", fg="#38bdf8", bg="#081120", font=("Segoe UI", 44, "bold")).pack(anchor="w", pady=(0, 12))

        self.progress_var = tk.DoubleVar(value=0)
        progress = ttk.Progressbar(frame, variable=self.progress_var, maximum=100, length=360)
        progress.pack(fill="x", pady=(8, 0))
        self.progress_bar = progress
        self._animate()

    def _animate(self) -> None:
        value = self.progress_var.get() + 8
        if value >= 100:
            value = 0
        self.progress_var.set(value)
        self.root.after(80, self._animate)

    def close(self) -> None:
        self.root.after(0, self.root.destroy)


class MayanMinerApp:
    def __init__(self, root: "tk.Tk") -> None:
        self.root = root
        self.root.title("Mayan Miner")
        self.root.geometry("1240x820")
        self.root.minsize(1100, 760)
        self.root.configure(bg="#07111f")

        self.config_manager = SecureConfigManager()
        self.controller = MinerController()
        self.output_thread: Optional[threading.Thread] = None
        self.splash: Optional[SplashScreen] = None
        self.tray_icon = None
        self.performance_history: List[float] = []
        self.theme_mode = "system"
        self.vars: Dict[str, "tk.Variable"] = {}
        self.bool_vars: Dict[str, tk.BooleanVar] = {}

        self._build_ui()
        self._populate_from_config()
        self._refresh_status()
        self._refresh_installed_miner_status()

        if self._should_show_splash():
            self.root.after(120, self._show_splash_screen)

    def _should_show_splash(self) -> bool:
        return bool(self.bool_vars.get("show_splash_screen", tk.BooleanVar(value=True)).get())

    def _show_splash_screen(self) -> None:
        self.splash = SplashScreen(self.root)
        self.root.after(1400, lambda: self._close_splash() if self.splash else None)

    def _close_splash(self) -> None:
        if self.splash:
            self.splash.close()
            self.splash = None

    def _apply_theme(self, mode: str) -> None:
        self.theme_mode = mode
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        if mode == "light":
            bg = "#f8fafc"
            panel = "#ffffff"
            border = "#dbe4f0"
            fg = "#0f172a"
            muted = "#475569"
            accent = "#2563eb"
            accent_fg = "#ffffff"
            input_bg = "#ffffff"
            output_bg = "#f8fafc"
            output_fg = "#0f172a"
        else:
            bg = "#07111f"
            panel = "#0f172a"
            border = "#233247"
            fg = "#e2e8f0"
            muted = "#94a3b8"
            accent = "#38bdf8"
            accent_fg = "#081120"
            input_bg = "#020617"
            output_bg = "#020617"
            output_fg = "#f8fafc"

        self.root.configure(bg=bg)
        style.configure("Card.TFrame", background=panel)
        style.configure("Panel.TFrame", background=panel)
        style.configure("TLabel", background=bg, foreground=fg)
        style.configure("TFrame", background=bg)
        style.configure("TButton", padding=7, background=accent, foreground=accent_fg)
        style.configure("TEntry", padding=4, fieldbackground=input_bg, foreground=fg)
        style.configure("TCombobox", padding=4, fieldbackground=input_bg, foreground=fg)
        style.configure("TCheckbutton", background=bg, foreground=fg)
        style.map("TButton", background=[("active", accent), ("!disabled", accent)], foreground=[("active", accent_fg), ("!disabled", accent_fg)])
        style.map("TCombobox", fieldbackground=[("readonly", input_bg)])

        self._apply_widget_colors(self.root, bg=bg, fg=fg, panel=panel, muted=muted)
        if hasattr(self, "command_preview"):
            self.command_preview.configure(bg=output_bg, fg="#7dd3fc" if mode != "light" else accent)
            self.log_text.configure(bg=output_bg, fg=output_fg)
            self.performance_canvas.configure(bg=panel)

    def _apply_widget_colors(self, widget: tk.Misc, bg: str, fg: str, panel: str, muted: str) -> None:
        try:
            if isinstance(widget, (tk.Frame, tk.LabelFrame, tk.Canvas)):
                widget.configure(bg=panel)
            elif isinstance(widget, tk.Label):
                widget.configure(bg=bg, fg=fg)
                if widget.cget("text") in {"", " "}:
                    widget.configure(bg=bg)
            elif isinstance(widget, tk.Text):
                widget.configure(bg=bg, fg=fg)
            elif isinstance(widget, ttk.Frame):
                widget.configure(style="Card.TFrame")
        except Exception:
            pass

        for child in widget.winfo_children():
            self._apply_widget_colors(child, bg=bg, fg=fg, panel=panel, muted=muted)

    def _build_ui(self) -> None:
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=1)

        header = tk.Frame(self.root, bg="#0f172a", padx=18, pady=16)
        header.grid(row=0, column=0, sticky="ew")
        header.grid_columnconfigure(0, weight=1)

        logo_row = tk.Frame(header, bg="#0f172a")
        logo_row.grid(row=0, column=0, sticky="ew")
        logo_row.grid_columnconfigure(1, weight=1)

        logo_path = Path(__file__).resolve().parent.parent / "assets" / "logo.png"
        try:
            logo_image = tk.PhotoImage(file=str(logo_path))
            label_image = tk.Label(logo_row, image=logo_image, bg="#0f172a")
            label_image.image = logo_image
            label_image.grid(row=0, column=0, sticky="w")
        except Exception:
            tk.Label(logo_row, text="◉", fg="#38bdf8", bg="#0f172a", font=("Segoe UI", 22, "bold")).grid(row=0, column=0, sticky="w")

        tk.Label(logo_row, text="Mayan Miner", fg="#f8fafc", bg="#0f172a", font=("Segoe UI", 24, "bold")).grid(row=0, column=1, sticky="w", padx=(10, 0))
        tk.Label(logo_row, text="Modern CPU-only mining launcher for Windows", fg="#94a3b8", bg="#0f172a", font=("Segoe UI", 10)).grid(row=1, column=1, sticky="w", padx=(10, 0), pady=(2, 0))

        main = tk.Frame(self.root, bg="#07111f")
        main.grid(row=1, column=0, sticky="nsew", padx=16, pady=12)
        main.grid_columnconfigure(0, weight=1)
        main.grid_columnconfigure(1, weight=1)
        main.grid_rowconfigure(0, weight=1)

        left = tk.Frame(main, bg="#111827", padx=14, pady=14)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        left.grid_columnconfigure(1, weight=1)

        right = tk.Frame(main, bg="#111827", padx=14, pady=14)
        right.grid(row=0, column=1, sticky="nsew")
        right.grid_columnconfigure(0, weight=1)
        right.grid_rowconfigure(2, weight=1)

        tk.Label(left, text="Mining settings", fg="#f8fafc", bg="#111827", font=("Segoe UI", 16, "bold")).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

        rows = [
            ("Pool URL", "pool", "entry", "mine.example.com:3333"),
            ("Wallet", "wallet", "entry", "YOUR_WALLET"),
            ("Worker", "worker", "entry", "mayan-cpu"),
            ("Password", "password", "entry", "x"),
            ("Miner kind", "miner_kind", "combo", "xmrig"),
            ("Algorithm", "algorithm", "combo", "rx/0"),
            ("Threads", "threads", "spin", "4"),
            ("Miner executable", "miner_executable", "path", ""),
            ("Extra args", "extra_args", "entry", ""),
        ]

        for index, (label, key, kind, default) in enumerate(rows, start=1):
            tk.Label(left, text=label, fg="#cbd5e1", bg="#111827", font=("Segoe UI", 10)).grid(row=index, column=0, sticky="w", padx=(0, 10), pady=6)
            if kind == "entry":
                var = tk.StringVar(value=default)
                ttk.Entry(left, textvariable=var, width=40).grid(row=index, column=1, sticky="ew", pady=6)
            elif kind == "combo":
                var = tk.StringVar(value=default)
                values = ["xmrig", "srbminer", "custom"] if key == "miner_kind" else ["rx/0", "randomx", "cn/0", "cn/1", "cn/2", "cn-lite", "kawpow", "sha256", "ethash", "custom"]
                combo = ttk.Combobox(left, textvariable=var, values=values, state="normal", width=37)
                combo.grid(row=index, column=1, sticky="ew", pady=6)
            elif kind == "spin":
                var = tk.StringVar(value=default)
                ttk.Spinbox(left, from_=1, to=256, textvariable=var, width=12).grid(row=index, column=1, sticky="w", pady=6)
            elif kind == "path":
                var = tk.StringVar(value=default)
                ttk.Entry(left, textvariable=var, width=32).grid(row=index, column=1, sticky="ew", pady=6)
                ttk.Button(left, text="Browse", command=lambda target=var: self._browse_miner(target)).grid(row=index, column=2, padx=(6, 0), pady=6)
            self.vars[key] = var

        self.bool_vars["use_all_cores"] = tk.BooleanVar(value=True)
        ttk.Checkbutton(left, variable=self.bool_vars["use_all_cores"], text="Use all CPU cores").grid(row=len(rows) + 1, column=1, sticky="w", pady=(8, 0))

        self.bool_vars["start_on_login"] = tk.BooleanVar(value=False)
        ttk.Checkbutton(left, variable=self.bool_vars["start_on_login"], text="Start mining on system login").grid(row=len(rows) + 2, column=1, sticky="w")

        self.bool_vars["minimize_to_tray"] = tk.BooleanVar(value=False)
        ttk.Checkbutton(left, variable=self.bool_vars["minimize_to_tray"], text="Minimize to tray instead of the taskbar").grid(row=len(rows) + 3, column=1, sticky="w")

        self.bool_vars["show_tray_icon"] = tk.BooleanVar(value=False)
        ttk.Checkbutton(left, variable=self.bool_vars["show_tray_icon"], text="Show tray icon").grid(row=len(rows) + 4, column=1, sticky="w")

        self.bool_vars["show_splash_screen"] = tk.BooleanVar(value=True)
        ttk.Checkbutton(left, variable=self.bool_vars["show_splash_screen"], text="Show splash screen").grid(row=len(rows) + 5, column=1, sticky="w")

        self.theme_var = tk.StringVar(value="system")
        ttk.Label(left, text="Theme").grid(row=len(rows) + 6, column=0, sticky="w", pady=(10, 0))
        ttk.Combobox(left, textvariable=self.theme_var, values=["light", "dark", "system"], state="readonly", width=20).grid(row=len(rows) + 6, column=1, sticky="w", pady=(10, 0))

        button_row = len(rows) + 7
        buttons = tk.Frame(left, bg="#111827")
        buttons.grid(row=button_row, column=0, columnspan=3, sticky="w", pady=(16, 0))
        ttk.Button(buttons, text="Save", command=self._save_config).pack(side="left", padx=(0, 8))
        ttk.Button(buttons, text="Export config", command=self._export_config).pack(side="left", padx=(0, 8))
        ttk.Button(buttons, text="Import config", command=self._import_config).pack(side="left", padx=(0, 8))
        ttk.Button(buttons, text="Start mining", command=self._start_mining).pack(side="left", padx=(0, 8))
        ttk.Button(buttons, text="Stop", command=self._stop_mining).pack(side="left", padx=(0, 8))
        ttk.Button(buttons, text="Install XMRig", command=self._install_miner).pack(side="left", padx=(0, 8))
        ttk.Button(buttons, text="Check app update", command=self._check_for_updates).pack(side="left")

        tk.Label(right, text="Live status", fg="#f8fafc", bg="#111827", font=("Segoe UI", 16, "bold")).grid(row=0, column=0, sticky="w")
        self.status_var = tk.StringVar(value="Ready to mine")
        tk.Label(right, textvariable=self.status_var, fg="#34d399", bg="#111827", font=("Segoe UI", 11, "bold")).grid(row=1, column=0, sticky="w", pady=(4, 10))

        self.miner_version_var = tk.StringVar(value="Installed miner: not found")
        tk.Label(right, textvariable=self.miner_version_var, fg="#cbd5e1", bg="#111827", font=("Segoe UI", 10)).grid(row=1, column=1, sticky="e", pady=(4, 10))

        self.app_update_var = tk.StringVar(value="App update status: unknown")
        tk.Label(right, textvariable=self.app_update_var, fg="#cbd5e1", bg="#111827", font=("Segoe UI", 10)).grid(row=2, column=0, columnspan=2, sticky="w", pady=(0, 10))

        self.notice_var = tk.StringVar(value="Developer support notice: a small fee may be applied to contributions.")
        tk.Label(right, textvariable=self.notice_var, fg="#93c5fd", bg="#111827", font=("Segoe UI", 10)).grid(row=3, column=0, columnspan=2, sticky="w", pady=(0, 6))

        tk.Label(right, text="Launch command", fg="#cbd5e1", bg="#111827").grid(row=4, column=0, sticky="w")
        self.command_preview = tk.Text(right, height=5, width=56, bg="#020617", fg="#7dd3fc", insertbackground="#7dd3fc")
        self.command_preview.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(4, 12))
        self.command_preview.configure(state="disabled")

        self.performance_canvas = tk.Canvas(right, height=100, bg="#111827", highlightthickness=0)
        self.performance_canvas.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(0, 8))
        tk.Label(right, text="Live performance", fg="#cbd5e1", bg="#111827").grid(row=7, column=0, sticky="w")

        tk.Label(right, text="Miner output", fg="#cbd5e1", bg="#111827").grid(row=8, column=0, sticky="w")
        self.log_text = tk.Text(right, height=16, bg="#020617", fg="#f8fafc", insertbackground="#f8fafc")
        self.log_text.grid(row=9, column=0, columnspan=2, sticky="nsew")
        self.log_text.configure(state="disabled")

        tk.Label(right, text="Security: settings are encrypted locally on this machine.", fg="#64748b", bg="#111827", font=("Segoe UI", 9)).grid(row=10, column=0, columnspan=2, sticky="w", pady=(8, 0))

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self.root.bind("<Configure>", self._handle_window_state)

    def _handle_window_state(self, event: object) -> None:
        if event.widget == self.root and self.root.state() == "iconic" and self.bool_vars.get("minimize_to_tray", tk.BooleanVar()).get():
            self._minimize_to_tray()

    def _on_close(self) -> None:
        self.controller.stop()
        self._hide_tray_icon()
        self.root.destroy()

    def _minimize_to_tray(self) -> None:
        if self.bool_vars.get("show_tray_icon", tk.BooleanVar()).get():
            self._show_tray_icon()
        self.root.withdraw()

    def _show_tray_icon(self) -> None:
        if self.tray_icon is not None:
            return
        try:
            import pystray
            from PIL import Image

            image = Image.open(Path(__file__).resolve().parent.parent / "assets" / "logo.png")
            menu = pystray.Menu(pystray.MenuItem("Restore", self._restore_from_tray), pystray.MenuItem("Exit", self._on_close))
            self.tray_icon = pystray.Icon("MayanMiner", image, "Mayan Miner", menu)
            threading.Thread(target=self.tray_icon.run, daemon=True).start()
        except Exception:
            self._append_log("Tray support unavailable. Install pystray and Pillow for a system tray icon.\n")

    def _hide_tray_icon(self) -> None:
        if self.tray_icon is not None:
            try:
                self.tray_icon.stop()
            except Exception:
                pass
            self.tray_icon = None

    def _restore_from_tray(self) -> None:
        self.root.deiconify()
        self._hide_tray_icon()

    def _browse_miner(self, target: "tk.StringVar") -> None:
        filename = filedialog.askopenfilename(title="Select miner executable", filetypes=[("Executable", "*.exe"), ("All files", "*.*")])
        if filename:
            target.set(filename)

    def _populate_from_config(self) -> None:
        config = self.config_manager.load_config()
        for key, var in self.vars.items():
            value = config.get(key, "")
            if isinstance(var, tk.StringVar):
                var.set(str(value))
        for key, var in self.bool_vars.items():
            var.set(bool(config.get(key, False)))
        self.theme_var.set(config.get("theme", "system"))
        self._apply_theme(self.theme_var.get())
        self._update_notice(config)
        self._update_command_preview()

    def _collect_config(self) -> Dict[str, object]:
        config = default_config()
        for key, var in self.vars.items():
            config[key] = var.get()
        config["threads"] = int(self.vars["threads"].get()) if str(self.vars["threads"].get()).isdigit() else 1
        for key, var in self.bool_vars.items():
            config[key] = bool(var.get())
        config["theme"] = self.theme_var.get()
        return config

    def _update_notice(self, config: Dict[str, object]) -> None:
        wallet = str(config.get("developer_wallet", "")).strip()
        fee = str(config.get("developer_fee", "")).strip()
        if wallet and fee:
            self.notice_var.set(f"Developer support: wallet configured with {fee}% fee contribution.")
        else:
            self.notice_var.set("Developer support notice: a small fee may be applied to contributions.")

    def _update_command_preview(self) -> None:
        config = self._collect_config()
        preview = " ".join(shlex.quote(part) for part in build_miner_command(config))
        self.command_preview.configure(state="normal")
        self.command_preview.delete("1.0", tk.END)
        self.command_preview.insert(tk.END, preview or "No command yet")
        self.command_preview.configure(state="disabled")

    def _append_log(self, message: str) -> None:
        self.log_text.configure(state="normal")
        self.log_text.insert(tk.END, message)
        self.log_text.see(tk.END)
        self.log_text.configure(state="disabled")
        self._update_graph_from_line(message)

    def _update_graph_from_line(self, message: str) -> None:
        match = re.search(r"(?i)(\d+(?:\.\d+)?)\s*(k|m|g)?h/s", message)
        if match:
            amount = float(match.group(1))
            unit = match.group(2).lower() if match.group(2) else ""
            multiplier = {"k": 1000.0, "m": 1000000.0, "g": 1000000000.0}.get(unit, 1.0)
            self.performance_history.append(amount * multiplier)
        elif self.controller.is_running():
            self.performance_history.append(float(len(self.performance_history) + 1))
        if len(self.performance_history) > 40:
            self.performance_history = self.performance_history[-40:]
        self._render_graph()

    def _render_graph(self) -> None:
        self.performance_canvas.delete("all")
        if not self.performance_history:
            return
        width = self.performance_canvas.winfo_width() or 640
        height = self.performance_canvas.winfo_height() or 100
        if width < 10:
            width = 640
        if height < 10:
            height = 100
        max_value = max(self.performance_history) or 1
        step = width / max(1, len(self.performance_history) - 1)
        points = []
        for index, value in enumerate(self.performance_history):
            x = index * step
            y = height - (value / max_value) * (height - 12) - 6
            points.append((x, y))
        self.performance_canvas.create_line(*sum(points, ()), fill="#38bdf8", width=2)
        self.performance_canvas.create_rectangle(0, 0, width, height, outline="#234", fill="")

    def _save_config(self) -> None:
        config = self._collect_config()
        self.config_manager.save_config(config)
        self._apply_theme(str(config.get("theme", "system")))
        self._update_notice(config)
        self._update_command_preview()
        self.status_var.set("Settings saved")
        messagebox.showinfo("Saved", "Configuration saved locally and encrypted.")
        if bool(config.get("start_on_login", False)):
            self._configure_startup_shortcut(True)
        else:
            self._configure_startup_shortcut(False)

    def _export_config(self) -> None:
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
        if not path:
            return
        self.config_manager.export_config(path)
        self.status_var.set("Configuration exported")
        messagebox.showinfo("Exported", f"Configuration export saved to {path}")

    def _import_config(self) -> None:
        path = filedialog.askopenfilename(filetypes=[("JSON files", "*.json"), ("All files", "*.*")])
        if not path:
            return
        self.config_manager.import_config(path)
        self._populate_from_config()
        self._update_command_preview()
        self.status_var.set("Configuration imported")
        messagebox.showinfo("Imported", f"Configuration imported from {path}")

    def _configure_startup_shortcut(self, enable: bool) -> None:
        if os.name != "nt":
            return
        startup_dir = Path(os.environ.get("APPDATA", "")) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
        if not startup_dir.exists():
            startup_dir.mkdir(parents=True, exist_ok=True)
        shortcut_path = startup_dir / "MayanMiner.cmd"
        if enable:
            target = Path(sys.executable).resolve()
            content = f'@echo off\n"{target}" "{Path(__file__).resolve().parent.parent / "main.py"}"\n'
            shortcut_path.write_text(content, encoding="utf-8")
        else:
            try:
                shortcut_path.unlink(missing_ok=True)
            except Exception:
                pass

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
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", tk.END)
        self.log_text.configure(state="disabled")
        self._append_log("Starting miner...\n")
        self.controller.stop()
        started = self.controller.start(config)
        if started and self.controller.is_running():
            self.status_var.set("Mining is running")
            self.output_thread = threading.Thread(target=self._stream_output, daemon=True)
            self.output_thread.start()
        else:
            self.status_var.set("Unable to start miner")
            self._append_log("The miner process exited immediately. Check the executable path and command arguments.\n")

    def _stop_mining(self) -> None:
        self.controller.stop()
        self.status_var.set("Mining stopped")
        self._append_log("Miner stopped.\n")

    def _install_miner(self) -> None:
        self.status_var.set("Installing XMRig...")
        self._append_log("Downloading and installing the latest XMRig release...\n")
        thread = threading.Thread(target=self._install_miner_worker, daemon=True)
        thread.start()

    def _install_miner_worker(self) -> None:
        try:
            installer_path = download_latest_xmrig()
            self.root.after(0, self._append_log, f"XMRig installed to {installer_path}\n")
            self.root.after(0, self._refresh_installed_miner_status)
            self.root.after(0, self._update_command_preview)
            self.root.after(0, self.status_var.set, "XMRig installed")
        except Exception as error:
            self.root.after(0, self._append_log, f"Install failed: {error}\n")
            self.root.after(0, self.status_var.set, "Install failed")

    def _check_for_updates(self) -> None:
        self.status_var.set("Checking for app updates...")
        self._append_log("Checking for app and miner updates...\n")
        thread = threading.Thread(target=self._check_for_updates_worker, daemon=True)
        thread.start()

    def _check_for_updates_worker(self) -> None:
        try:
            installed_version = get_installed_miner_version()
            latest_app_version = get_latest_app_version()
            if installed_version:
                text = f"Installed miner: {installed_version}\n"
            else:
                text = "Installed miner: not found\n"
            if latest_app_version:
                if is_app_update_available():
                    text += f"App update available: {latest_app_version}\n"
                else:
                    text += "App is up to date\n"
            else:
                text += "App update status unavailable\n"
            self.root.after(0, self._append_log, text)
            self.root.after(0, self._refresh_installed_miner_status)
            self.root.after(0, self.status_var.set, "Update check complete")
        except Exception as error:
            self.root.after(0, self._append_log, f"Update check failed: {error}\n")
            self.root.after(0, self.status_var.set, "Update check failed")

    def _refresh_installed_miner_status(self) -> None:
        version = get_installed_miner_version()
        if version:
            self.miner_version_var.set(f"Installed miner: {version}")
        else:
            self.miner_version_var.set("Installed miner: not found")
        latest_app_version = get_latest_app_version()
        if latest_app_version:
            if is_app_update_available():
                self.app_update_var.set(f"App update available: {latest_app_version}")
            else:
                self.app_update_var.set("App is up to date")
        else:
            self.app_update_var.set("App update status unavailable")

    def _refresh_status(self) -> None:
        if self.controller.is_running():
            self.status_var.set("Mining is running")
        else:
            self.status_var.set("Ready to mine")
        self.root.after(250, self._refresh_status)


def run_app() -> None:
    if not TKINTER_AVAILABLE:
        print("Error: tkinter library is not available.")
        print("GUI cannot be launched. Use --headless mode to preview the miner command:")
        print("  python main.py --headless")
        sys.exit(1)
    root = tk.Tk()
    MayanMinerApp(root)
    root.mainloop()


def main() -> None:
    parser = argparse.ArgumentParser(description="Mayan Miner")
    parser.add_argument("--headless", action="store_true", help="Preview the generated launch command without opening the GUI")
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

    run_app()


if __name__ == "__main__":
    main()
