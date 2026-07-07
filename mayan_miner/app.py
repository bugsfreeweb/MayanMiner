import argparse
import os
import shlex
import threading
import sys
from typing import Dict, Optional
from pathlib import Path


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
    # Provide stub classes for when tkinter is not available
    tk = None
    filedialog = None
    messagebox = None
    ttk = None

from mayan_miner.config import SecureConfigManager, default_config
from mayan_miner.miner import MinerController, build_miner_command
from mayan_miner.updater import (
    download_latest_app_installer,
    download_latest_xmrig,
    get_installed_miner_version,
    get_installed_miner_path,
    get_latest_app_version,
    is_app_update_available,
)


class MayanMinerApp:
    def __init__(self, root: "tk.Tk") -> None:
        self.root = root
        self.root.title("Mayan Miner")
        self.root.geometry("1120x760")
        self.root.minsize(1024, 700)
        self.root.configure(bg="#07111f")
        self._apply_theme()

        self.config_manager = SecureConfigManager()
        self.controller = MinerController()
        self.process: Optional[object] = None
        self.output_thread: Optional[threading.Thread] = None

        self.vars: Dict[str, "tk.Variable"] = {}
        self._build_ui()
        self._populate_from_config()
        self._refresh_status()
        self._refresh_installed_miner_status()

    def _apply_theme(self) -> None:
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        # Base colors
        bg = "#07111f"
        card = "#0f1724"
        text = "#e2e8f0"
        accent = "#06b6d4"  # teal
        primary = "#10b981"  # emerald green for primary actions

        style.configure("TLabel", background=bg, foreground=text)
        style.configure("TFrame", background=bg)
        style.configure("TEntry", padding=4)

        # Primary button style
        style.configure("Primary.TButton", background=primary, foreground="#ffffff", padding=8, font=("Segoe UI", 10, "bold"))
        style.map("Primary.TButton", background=[("active", "#0ea46a"), ("!disabled", primary)], foreground=[("disabled", "#9ca3af")])

        # Secondary button style (subtle)
        style.configure("Secondary.TButton", background=card, foreground=text, padding=6, font=("Segoe UI", 9))
        style.map("Secondary.TButton", background=[("active", "#0b1220"), ("!disabled", card)])

    def _build_ui(self) -> None:
        self.root.grid_columnconfigure(0, weight=1)
        self.root.grid_rowconfigure(1, weight=1)

        header = tk.Frame(self.root, bg="#0f172a", padx=18, pady=16)
        header.grid(row=0, column=0, sticky="ew")
        # Two columns: title/subtitle stretch on the left, logo is pinned to
        # the top-right corner of the header.
        header.grid_columnconfigure(0, weight=1)
        header.grid_columnconfigure(1, weight=0)

        title_box = tk.Frame(header, bg="#0f172a")
        title_box.grid(row=0, column=0, sticky="w")
        tk.Label(title_box, text="Mayan Miner", fg="#f8fafc", bg="#0f172a", font=("Segoe UI", 24, "bold")).pack(anchor="w")
        tk.Label(title_box, text="Professional CPU-only mining launcher for Windows", fg="#94a3b8", bg="#0f172a", font=("Segoe UI", 10)).pack(anchor="w", pady=(3, 0))

        # Try to load application logo (keeps a reference on self to avoid GC).
        # Uses a bundle-safe resource path so it also works from a frozen
        # PyInstaller --onefile exe, and is downscaled from its source
        # resolution (512x512) to a sane on-screen icon size.
        self.logo_image = None
        try:
            logo_path = _resource_path("assets/logo.png")
            if logo_path.exists():
                raw_image = tk.PhotoImage(file=str(logo_path))
                width = raw_image.width()
                target = 64
                factor = max(1, round(width / target)) if width > target else 1
                self.logo_image = raw_image.subsample(factor, factor) if factor > 1 else raw_image
                tk.Label(header, image=self.logo_image, bg="#0f172a").grid(row=0, column=1, sticky="ne")
        except Exception:
            # Fail gracefully if image can't be loaded
            self.logo_image = None

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
            # Algorithm: provide common choices but allow custom input by making combobox editable
            ("Algorithm", "algorithm", "combo", "rx/0"),
            ("Threads", "threads", "spin", "4"),
            ("Miner executable", "miner_executable", "path", ""),
            ("Extra args", "extra_args", "entry", ""),
            # Only used when Miner kind = Custom. Lets the app drive any other
            # miner binary regardless of its CLI syntax, including whatever
            # flag that miner uses for its own algorithm option.
            ("Custom command template (Custom kind only)", "custom_command_template", "entry", ""),
            # Developer wallet intentionally not shown in UI for security — kept in config
            # Developer fee kept at default (not editable in UI)
        ]

        for index, (label, key, kind, default) in enumerate(rows, start=1):
            tk.Label(left, text=label, fg="#cbd5e1", bg="#111827", font=("Segoe UI", 10)).grid(row=index, column=0, sticky="w", padx=(0, 10), pady=6)
            if kind == "entry":
                var = tk.StringVar(value=default)
                ttk.Entry(left, textvariable=var, width=40).grid(row=index, column=1, sticky="ew", pady=6)
            elif kind == "combo":
                var = tk.StringVar(value=default)
                if key == "miner_kind":
                    values = ["xmrig", "srbminer", "custom"]
                    ttk.Combobox(left, textvariable=var, values=values, state="readonly", width=37).grid(row=index, column=1, sticky="ew", pady=6)
                else:
                    # Algorithm combobox: provide defaults but allow typing a custom algorithm
                    try:
                        known = default_config().get("known_algorithms", ["rx/0", "cn/0", "cn/1", "kawpow", "randomx", "sha256"])
                    except Exception:
                        known = ["rx/0", "cn/0", "cn/1", "kawpow", "randomx", "sha256"]
                    ttk.Combobox(left, textvariable=var, values=known, state="normal", width=37).grid(row=index, column=1, sticky="ew", pady=6)
            elif kind == "spin":
                var = tk.StringVar(value=default)
                ttk.Spinbox(left, from_=1, to=256, textvariable=var, width=12).grid(row=index, column=1, sticky="w", pady=6)
            elif kind == "path":
                var = tk.StringVar(value=default)
                ttk.Entry(left, textvariable=var, width=32).grid(row=index, column=1, sticky="ew", pady=6)
                ttk.Button(left, text="Browse", command=lambda target=var: self._browse_miner(target)).grid(row=index, column=2, padx=(6, 0), pady=6)
            self.vars[key] = var

        self.use_all_cores_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(left, variable=self.use_all_cores_var, text="Use all CPU cores").grid(row=len(rows) + 1, column=1, sticky="w", pady=(8, 0))

        hint_text = (
            "Tip: the Algorithm box accepts any custom algorithm name, not just the presets.\n"
            "For a fully custom miner app, set Miner kind to \"custom\" and optionally fill in\n"
            "the command template using {executable} {pool} {wallet} {worker} {password}\n"
            "{algorithm} {threads} {extra_args} placeholders for that program's own CLI syntax."
        )
        tk.Label(
            left, text=hint_text, fg="#64748b", bg="#111827", font=("Segoe UI", 8), justify="left",
        ).grid(row=len(rows) + 2, column=0, columnspan=3, sticky="w", pady=(8, 0))

        button_row = len(rows) + 3
        buttons = tk.Frame(left, bg="#111827")
        buttons.grid(row=button_row, column=0, columnspan=3, sticky="w", pady=(16, 0))
        ttk.Button(buttons, text="Save", command=self._save_config, style="Secondary.TButton").pack(side="left", padx=(0, 8))
        ttk.Button(buttons, text="Start mining", command=self._start_mining, style="Primary.TButton").pack(side="left", padx=(0, 8))
        ttk.Button(buttons, text="Stop", command=self._stop_mining, style="Secondary.TButton").pack(side="left", padx=(0, 8))
        ttk.Button(buttons, text="Install XMRig", command=self._install_miner, style="Secondary.TButton").pack(side="left", padx=(0, 8))
        ttk.Button(buttons, text="Check app update", command=self._check_for_updates, style="Secondary.TButton").pack(side="left")

        tk.Label(right, text="Live status", fg="#f8fafc", bg="#111827", font=("Segoe UI", 16, "bold")).grid(row=0, column=0, sticky="w")
        self.status_var = tk.StringVar(value="Ready to mine")
        tk.Label(right, textvariable=self.status_var, fg="#34d399", bg="#111827", font=("Segoe UI", 11, "bold")).grid(row=1, column=0, sticky="w", pady=(4, 10))

        self.miner_version_var = tk.StringVar(value="Installed miner: not found")
        tk.Label(right, textvariable=self.miner_version_var, fg="#cbd5e1", bg="#111827", font=("Segoe UI", 10)).grid(row=1, column=1, sticky="e", pady=(4, 10))

        self.app_update_var = tk.StringVar(value="App update status: unknown")
        tk.Label(right, textvariable=self.app_update_var, fg="#cbd5e1", bg="#111827", font=("Segoe UI", 10)).grid(row=2, column=0, columnspan=2, sticky="w", pady=(0, 10))

        tk.Label(right, text="Launch command", fg="#cbd5e1", bg="#111827").grid(row=3, column=0, sticky="w")
        self.command_preview = tk.Text(right, height=5, width=56, bg="#020617", fg="#7dd3fc", insertbackground="#7dd3fc")
        self.command_preview.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(4, 12))
        self.command_preview.configure(state="disabled")

        tk.Label(right, text="Miner output", fg="#cbd5e1", bg="#111827").grid(row=5, column=0, sticky="w")
        self.log_text = tk.Text(right, height=18, bg="#020617", fg="#f8fafc", insertbackground="#f8fafc")
        self.log_text.grid(row=6, column=0, columnspan=2, sticky="nsew")
        self.log_text.configure(state="disabled")

        tk.Label(right, text="Security: settings are encrypted locally on this machine.", fg="#64748b", bg="#111827", font=("Segoe UI", 9)).grid(row=7, column=0, columnspan=2, sticky="w", pady=(8, 0))

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
        self.use_all_cores_var.set(bool(config.get("use_all_cores", True)))
        self._update_command_preview()

    def _collect_config(self) -> Dict[str, object]:
        config = default_config()
        for key, var in self.vars.items():
            config[key] = var.get()
        config["threads"] = int(self.vars["threads"].get()) if str(self.vars["threads"].get()).isdigit() else 1
        config["use_all_cores"] = bool(self.use_all_cores_var.get())
        return config

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

    def _save_config(self) -> None:
        config = self._collect_config()
        self.config_manager.save_config(config)
        self._update_command_preview()
        self.status_var.set("Settings saved")
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
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", tk.END)
        self.log_text.configure(state="disabled")
        self._append_log("Starting miner...\n")
        self.controller.stop()
        self.controller.start(config)
        if self.controller.is_running():
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
