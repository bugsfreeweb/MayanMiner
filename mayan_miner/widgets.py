import time
import tkinter as tk
from collections import deque
from typing import Dict, List, Optional, Sequence, Tuple


_FALLBACK = {
    "card": "#111827", "card_alt": "#1a2332", "card_label_fg": "#94a3b8",
    "value_fg": "#f8fafc", "console_bg": "#020617", "console_text": "#f8fafc",
    "accent": "#06b6d4", "muted": "#94a3b8",
    "line_color": "#34d399", "fill_color": "#0f3b2c", "grid_color": "#1e293b",
    "success": "#10b981", "warning": "#f59e0b", "danger": "#ef4444", "faint": "#64748b",
}


class RealtimeChart(tk.Canvas):
    def __init__(
        self,
        master,
        *,
        width: int = 640,
        height: int = 200,
        palette: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> None:
        p = {**_FALLBACK, **(palette or {})}
        bg_color = kwargs.pop("bg", p["console_bg"])
        super().__init__(
            master,
            width=width,
            height=height,
            bg=bg_color,
            highlightthickness=0,
            **kwargs,
        )
        self._palette = p
        self.bind("<Configure>", lambda _event: self.redraw())
        self._last_values: Sequence[float] = []
        self._share_flash = 0
        self._flash_id = None

    def set_palette(self, palette: Dict[str, str]) -> None:
        self._palette = {**_FALLBACK, **palette}
        self.configure(bg=self._palette["console_bg"])
        self.redraw()

    def flash_share(self) -> None:
        self._share_flash = 6
        self.redraw()

    def redraw(self, values: Optional[Sequence[float]] = None) -> None:
        if values is not None:
            self._last_values = list(values)
        values = self._last_values
        p = self._palette

        self.delete("all")
        width = max(self.winfo_width(), 10)
        height = max(self.winfo_height(), 10)
        pad_left, pad_right, pad_top, pad_bottom = 8, 8, 12, 20

        if self._share_flash > 0:
            flash_color = "#fbbf24"
            self.create_rectangle(0, 0, width, height, fill=flash_color, stipple="gray12", outline="")
            self._share_flash -= 1
            if self._flash_id:
                self.after_cancel(self._flash_id)
            self._flash_id = self.after(200, lambda: (setattr(self, "_share_flash", max(0, self._share_flash - 1)), self.redraw()))

        for fraction in (0.25, 0.5, 0.75):
            y = pad_top + (height - pad_top - pad_bottom) * fraction
            self.create_line(pad_left, y, width - pad_right, y, fill=p["grid_color"], dash=(2, 3))

        if not values:
            self.create_text(
                width / 2, height / 2,
                text="Waiting for miner output...",
                fill=p["faint"], font=("Segoe UI", 10),
            )
            return

        max_value = max(values) or 1.0
        min_value = min(values)
        span = (max_value - min_value) or max_value or 1.0
        plot_w = width - pad_left - pad_right
        plot_h = height - pad_top - pad_bottom
        count = len(values)
        step = plot_w / max(count - 1, 1)

        points = []
        for index, value in enumerate(values):
            x = pad_left + index * step
            normalized = (value - min_value) / span
            y = pad_top + plot_h - (normalized * plot_h)
            points.append((x, y))

        polygon = [pad_left, pad_top + plot_h]
        for x, y in points:
            polygon.extend([x, y])
        polygon.extend([points[-1][0], pad_top + plot_h])
        self.create_polygon(polygon, fill=p["fill_color"], outline="")

        flat_points = [coord for point in points for coord in point]
        self.create_line(*flat_points, fill=p["line_color"], width=2, smooth=True)

        latest = values[-1]
        self.create_text(
            width - pad_right, pad_top - 4, anchor="ne",
            text=f"{latest:,.1f} H/s", fill=p["console_text"],
            font=("Segoe UI", 10, "bold"),
        )


class StatCard(tk.Frame):
    def __init__(
        self,
        master,
        *,
        title: str,
        initial_value: str = "-",
        accent: str = "#34d399",
        palette: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> None:
        p = {**_FALLBACK, **(palette or {})}
        super().__init__(master, bg=p["card"], padx=14, pady=12, **kwargs)
        self._palette = p
        self._title_color = p.get("card_label_fg", "#94a3b8")
        self._accent = accent

        self._title_label = tk.Label(
            self, text=title, fg=self._title_color, bg=p["card"],
            font=("Segoe UI", 9, "bold"),
        )
        self._title_label.pack(anchor="w")

        self.value_var = tk.StringVar(value=initial_value)
        self._value_label = tk.Label(
            self, textvariable=self.value_var, fg=accent, bg=p["card"],
            font=("Segoe UI", 18, "bold"),
        )
        self._value_label.pack(anchor="w", pady=(4, 0))

    def set_palette(self, palette: Dict[str, str]) -> None:
        p = {**_FALLBACK, **palette}
        self._palette = p
        bg = p["card"]
        self.configure(bg=bg)
        self._title_label.configure(bg=bg, fg=p.get("card_label_fg", "#94a3b8"))
        self._value_label.configure(bg=bg, fg=self._accent)

    def set_accent(self, accent: str) -> None:
        self._accent = accent
        self._value_label.configure(fg=accent)

    def set(self, value: str) -> None:
        self.value_var.set(value)

    def set_title(self, title: str) -> None:
        self._title_label.configure(text=title)

    def flash(self, color: str = "#fbbf24") -> None:
        original = self._accent
        self._value_label.configure(fg=color)
        self.after(500, lambda: self._value_label.configure(fg=original))


class ShareFeed(tk.Frame):
    def __init__(self, master, *, palette: Optional[Dict[str, str]] = None, **kwargs):
        p = {**_FALLBACK, **(palette or {})}
        super().__init__(master, bg=p["card"], padx=14, pady=12, **kwargs)
        self._palette = p
        self._events: Deque[Tuple[str, str, float]] = deque(maxlen=50)
        self._entry_labels: List[tk.Frame] = []
        self._max_visible = 8

        header = tk.Frame(self, bg=p["card"])
        header.pack(fill="x")
        tk.Label(header, text="Recent Events", fg=p["card_label_fg"], bg=p["card"],
                 font=("Segoe UI", 9, "bold")).pack(side="left")

        self._body = tk.Frame(self, bg=p["card"])
        self._body.pack(fill="both", expand=True, pady=(8, 0))

    def set_palette(self, palette: Dict[str, str]) -> None:
        p = {**_FALLBACK, **palette}
        self._palette = p
        self.configure(bg=p["card"])
        for child in self.winfo_children():
            try:
                child.configure(bg=p["card"])
            except tk.TclError:
                pass

    def add_share(self, share_type: str, count: int = 1) -> None:
        now = time.monotonic()
        self._events.appendleft((share_type, str(count), now))
        self._rebuild()
        children = self._body.winfo_children()
        if children:
            self.after(50, lambda: self._flash_entry(children[0], 4))

    def _flash_entry(self, widget: tk.Frame, remaining: int) -> None:
        if remaining <= 0:
            widget.configure(bg=self._palette["card"])
            return
        target = self._palette["card_alt"] if remaining % 2 else self._palette["card"]
        widget.configure(bg=target)
        for child in widget.winfo_children():
            try:
                child.configure(bg=target)
            except tk.TclError:
                pass
        self.after(120, lambda: self._flash_entry(widget, remaining - 1))

    def _rebuild(self) -> None:
        for child in self._body.winfo_children():
            child.destroy()
        self._entry_labels.clear()
        p = self._palette

        visible = list(self._events)[:self._max_visible]
        if not visible:
            empty = tk.Label(self._body, text="Waiting for shares...", fg=p["faint"],
                              bg=p["card"], font=("Segoe UI", 9))
            empty.pack(fill="x", pady=2)
            self._entry_labels.append(empty)
            return

        for share_type, count, timestamp in visible:
            elapsed = time.monotonic() - timestamp
            time_str = f"{int(elapsed)}s ago" if elapsed < 60 else f"{int(elapsed//60)}m ago"

            if share_type == "accepted":
                icon = "\U0001f60a"
                icon_color = p["success"]
                desc = f"Share accepted"
            elif share_type == "rejected":
                icon = "\U0001f61e"
                icon_color = p["danger"]
                desc = f"Share rejected"
            elif share_type == "error":
                icon = "\u26a0\ufe0f"
                icon_color = p["warning"]
                desc = count
            else:
                icon = "\U0001f4a1"
                icon_color = p["accent"]
                desc = count

            row = tk.Frame(self._body, bg=p["card"])
            row.pack(fill="x", pady=2)

            dot = tk.Label(row, text=icon, fg=icon_color, bg=p["card"],
                           font=("Segoe UI", 11))
            dot.pack(side="left", padx=(0, 6))

            tk.Label(row, text=f"{desc}  {time_str}", fg=p["card_label_fg"],
                      bg=p["card"], font=("Segoe UI", 9)).pack(side="left")

            self._entry_labels.append(row)
