"""Theme-aware UI building blocks shared by the dashboard.

The real-time chart is drawn directly on a tk.Canvas rather than pulling in
matplotlib: it keeps the frozen .exe smaller and startup fast, and a simple
scrolling line is all a live hashrate readout needs.

Every visual element takes an optional `palette` dict so the host can swap
dark/light themes at runtime without recreating widgets.
"""
import tkinter as tk
from typing import Callable, Dict, Optional, Sequence


# Fallback palette used when a widget is created without one.
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
        super().__init__(
            master,
            width=width,
            height=height,
            bg=p["console_bg"],
            highlightthickness=0,
            **kwargs,
        )
        self._palette = p
        self.bind("<Configure>", lambda _event: self.redraw())
        self._last_values: Sequence[float] = []

    def set_palette(self, palette: Dict[str, str]) -> None:
        self._palette = {**_FALLBACK, **palette}
        self.configure(bg=self._palette["console_bg"])
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

        for fraction in (0.25, 0.5, 0.75):
            y = pad_top + (height - pad_top - pad_bottom) * fraction
            self.create_line(pad_left, y, width - pad_right, y, fill=p["grid_color"], dash=(2, 3))

        if not values or len(values) < 2:
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
    """Small rounded-feeling stat tile used across the dashboard header.

    Theme-aware: call `set_palette(...)` to re-skin without rebuilding.
    """

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
        # Keep the original accent unless the new palette wants a different "value" color
        self._value_label.configure(bg=bg, fg=self._accent)

    def set_accent(self, accent: str) -> None:
        self._accent = accent
        self._value_label.configure(fg=accent)

    def set(self, value: str) -> None:
        self.value_var.set(value)