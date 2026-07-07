"""Parses live miner stdout (XMRig / SRBMiner-style output) into the
hashrate history, share counts, and uptime shown on the dashboard.

This intentionally stays a light regex-based parser rather than talking to
a miner's local HTTP API: it works the same way regardless of which miner
binary is plugged in (xmrig, srbminer, or a fully custom one), which matches
how flexible the rest of this app is about the underlying miner.
"""
import re
import time
from collections import deque
from typing import Deque, Optional, Tuple

# Real XMRig periodic summary line, e.g.:
#   "speed 10s/60s/15m 1234.5 1300.2 1250.0 H/s max 1400.0 H/s"
# The three numbers are always plain H/s (xmrig does not auto-scale units on
# this line), so the first (10s average) is used as the "current" reading.
_XMRIG_SPEED_RE = re.compile(
    r"speed\s+\S*/\S*/\S*\s+([\d.]+)\s+[\d.]+\s+[\d.]+\s*H/s",
    re.IGNORECASE,
)
# Generic "Hashrate: 12.3 MH/s" / "hashrate 1.2KH/s" style line used by other
# miners (e.g. SRBMiner), where the unit prefix does vary.
_GENERIC_HASHRATE_RE = re.compile(
    r"hashrate\D{0,6}?([\d.,]+)\s*(K|M|G)?H/s",
    re.IGNORECASE,
)
_ACCEPTED_RE = re.compile(r"accepted\D{0,10}?\(?(\d+)/(\d+)\)?", re.IGNORECASE)
_UNIT_MULTIPLIER = {None: 1.0, "K": 1_000.0, "M": 1_000_000.0, "G": 1_000_000_000.0}


class MiningStatsTracker:
    """Rolling, thread-safe-enough (single-writer) mining telemetry store."""

    def __init__(self, history_length: int = 120) -> None:
        self.history_length = history_length
        self.hashrate_history: Deque[float] = deque(maxlen=history_length)
        self.current_hashrate: float = 0.0
        self.peak_hashrate: float = 0.0
        self.accepted_shares: int = 0
        self.rejected_shares: int = 0
        self.started_at: Optional[float] = None

    def reset(self) -> None:
        self.hashrate_history.clear()
        self.current_hashrate = 0.0
        self.peak_hashrate = 0.0
        self.accepted_shares = 0
        self.rejected_shares = 0
        self.started_at = time.monotonic()

    def feed_line(self, line: str) -> bool:
        """Update stats from one line of miner output.

        Returns True if the line changed anything worth redrawing for.
        """
        changed = False

        value = None
        xmrig_match = _XMRIG_SPEED_RE.search(line)
        if xmrig_match:
            try:
                value = float(xmrig_match.group(1))
            except ValueError:
                value = None
        else:
            generic_match = _GENERIC_HASHRATE_RE.search(line)
            if generic_match:
                raw_value, unit = generic_match.groups()
                try:
                    value = float(raw_value.replace(",", "")) * _UNIT_MULTIPLIER.get(
                        (unit or "").upper() or None, 1.0
                    )
                except ValueError:
                    value = None

        if value is not None:
            self.current_hashrate = value
            self.peak_hashrate = max(self.peak_hashrate, value)
            self.hashrate_history.append(value)
            changed = True

        accepted_match = _ACCEPTED_RE.search(line)
        if accepted_match:
            accepted, rejected = accepted_match.groups()
            self.accepted_shares = int(accepted)
            self.rejected_shares = int(rejected)
            changed = True

        return changed

    def uptime_seconds(self) -> float:
        if not self.started_at:
            return 0.0
        return time.monotonic() - self.started_at

    def uptime_label(self) -> str:
        total = int(self.uptime_seconds())
        hours, remainder = divmod(total, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    @staticmethod
    def format_hashrate(value: float) -> str:
        for unit, factor in (("GH/s", 1e9), ("MH/s", 1e6), ("KH/s", 1e3)):
            if value >= factor:
                return f"{value / factor:.2f} {unit}"
        return f"{value:.1f} H/s"
