import tkinter as tk
from tkinter import ttk
from pathlib import Path
from typing import Optional


class SplashScreen(tk.Toplevel):
    def __init__(self, master: tk.Tk, logo_path: Optional[Path], duration_ms: int = 1400) -> None:
        super().__init__(master)
        self.overrideredirect(True)
        self.configure(bg="#0b1120")
        self.attributes("-topmost", True)

        width, height = 420, 260
        self.update_idletasks()
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = (screen_w - width) // 2
        y = (screen_h - height) // 2
        self.geometry(f"{width}x{height}+{x}+{y}")

        border = tk.Frame(self, bg="#10b981", padx=1, pady=1)
        border.pack(fill="both", expand=True)
        card = tk.Frame(border, bg="#111827")
        card.pack(fill="both", expand=True)

        self._logo_image = None
        if logo_path and logo_path.exists():
            try:
                raw = tk.PhotoImage(file=str(logo_path))
                w = raw.width()
                target = 96
                factor = max(1, round(w / target)) if w > target else 1
                self._logo_image = raw.subsample(factor, factor) if factor > 1 else raw
                tk.Label(card, image=self._logo_image, bg="#111827").pack(pady=(36, 12))
            except Exception:
                self._logo_image = None

        tk.Label(card, text="Mayan Miner", fg="#f1f5f9", bg="#111827", font=("Segoe UI", 18, "bold")).pack()
        tk.Label(card, text="Starting up...", fg="#94a3b8", bg="#111827", font=("Segoe UI", 10)).pack(pady=(4, 16))

        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("Splash.Horizontal.TProgressbar", troughcolor="#1e293b", background="#10b981", thickness=6)
        progress = ttk.Progressbar(card, style="Splash.Horizontal.TProgressbar", mode="indeterminate", length=280)
        progress.pack(pady=(0, 8))
        progress.start(12)

        self._duration_ms = duration_ms

    def show_then(self, on_done) -> None:
        self.after(self._duration_ms, lambda: (self.destroy(), on_done()))

    def show_with_countdown(self, seconds: int, on_done) -> None:
        label = tk.Label(self, text="", fg="#f59e0b", bg="#111827",
                         font=("Segoe UI", 14, "bold"))
        label.pack(pady=(4, 0))

        def tick(remaining: int) -> None:
            if remaining <= 0:
                self.destroy()
                on_done()
                return
            label.configure(text=f"Mining starts in {remaining}...")
            self.after(1000, lambda: tick(remaining - 1))
        tick(seconds)
