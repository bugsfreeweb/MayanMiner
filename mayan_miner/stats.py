import re
import time
from collections import deque
from typing import Deque, Optional, Tuple


_XMRIG_SPEED_RE = re.compile(
    r"speed\s+(?:\S+/\S+/\S+\s+)?([\d.]+)\s+[\d.]+\s+[\d.]+\s*H/s",
    re.IGNORECASE,
)
_SRB_SPEED_RE = re.compile(
    r"Speed\s*\[.*?\]\s*:\s*([\d.]+)",
    re.IGNORECASE,
)
_GENERIC_HASHRATE_RE = re.compile(
    r"(?:\bhashrate|total|speed)\D{0,20}?([\d.,]+)\s*(K|M|G|T)?H/s",
    re.IGNORECASE,
)
_FALLBACK_HASHRATE_RE = re.compile(
    r"([\d.]+)\s*(K|M|G|T)?H/s",
    re.IGNORECASE,
)
_ACCEPTED_RE = re.compile(
    r"(?:accepted|acc)\D{0,30}?\(?(\d+)\s*[/,:]\s*(\d+)\)?",
    re.IGNORECASE,
)
_SHARE_KEYWORD_RE = re.compile(
    r"\b(?:share\s*found|found\s*share|new\s*share)\b",
    re.IGNORECASE,
)
_UNIT_MULTIPLIER = {None: 1.0, "K": 1_000.0, "M": 1_000_000.0, "G": 1_000_000_000.0, "T": 1_000_000_000_000.0}


class MiningStatsTracker:
    def __init__(self, history_length: int = 8640) -> None:
        self.history_length = history_length
        self.hashrate_history: Deque[float] = deque(maxlen=history_length)
        self.current_hashrate: float = 0.0
        self.peak_hashrate: float = 0.0
        self.accepted_shares: int = 0
        self.rejected_shares: int = 0
        self.started_at: Optional[float] = None
        self.last_share_found_at: Optional[float] = None
        self._last_accepted = 0
        self._last_rejected = 0

    def reset(self) -> None:
        self.hashrate_history.clear()
        self.current_hashrate = 0.0
        self.peak_hashrate = 0.0
        self.accepted_shares = 0
        self.rejected_shares = 0
        self.started_at = time.monotonic()
        self.last_share_found_at = None
        self._last_accepted = 0
        self._last_rejected = 0

    def feed_line(self, line: str) -> str:
        changed = ""
        value = None

        xmrig_match = _XMRIG_SPEED_RE.search(line)
        if xmrig_match:
            try:
                value = float(xmrig_match.group(1))
            except ValueError:
                value = None

        if value is None:
            srb_match = _SRB_SPEED_RE.search(line)
            if srb_match:
                try:
                    value = float(srb_match.group(1))
                except ValueError:
                    value = None

        if value is None:
            generic_match = _GENERIC_HASHRATE_RE.search(line)
            if generic_match:
                raw_value, unit = generic_match.groups()
                try:
                    value = float(raw_value.replace(",", "")) * _UNIT_MULTIPLIER.get(
                        (unit or "").upper() or None, 1.0
                    )
                except ValueError:
                    value = None

        if value is None:
            fallback_match = _FALLBACK_HASHRATE_RE.search(line)
            if fallback_match:
                raw_value, unit = fallback_match.groups()
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
            changed = "hashrate"

        accepted_match = _ACCEPTED_RE.search(line)
        if accepted_match:
            accepted, rejected = accepted_match.groups()
            if int(accepted) > self._last_accepted or int(rejected) > self._last_rejected:
                self.accepted_shares = int(accepted)
                self.rejected_shares = int(rejected)
                self.last_share_found_at = time.monotonic()
                self._last_accepted = self.accepted_shares
                self._last_rejected = self.rejected_shares
                changed = "share"
            else:
                self.accepted_shares = int(accepted)
                self.rejected_shares = int(rejected)
                self._last_accepted = self.accepted_shares
                self._last_rejected = self.rejected_shares
        elif _SHARE_KEYWORD_RE.search(line):
            self.last_share_found_at = time.monotonic()
            changed = "share"

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

    def last_share_label(self) -> str:
        if not self.last_share_found_at:
            return "N/A"
        elapsed = time.monotonic() - self.last_share_found_at
        if elapsed < 60:
            return f"{int(elapsed)}s ago"
        elif elapsed < 3600:
            return f"{int(elapsed // 60)}m {int(elapsed % 60)}s ago"
        else:
            hours = int(elapsed // 3600)
            minutes = int((elapsed % 3600) // 60)
            return f"{hours}h {minutes}m ago"

    @staticmethod
    def format_hashrate(value: float) -> str:
        for unit, factor in (("GH/s", 1e9), ("MH/s", 1e6), ("KH/s", 1e3)):
            if value >= factor:
                return f"{value / factor:.2f} {unit}"
        return f"{value:.1f} H/s"

    @staticmethod
    def estimate_xmr_per_day(hashrate_hs: float) -> float:
        return hashrate_hs * 1.44e-7

    @staticmethod
    def estimate_usd_per_day(hashrate_hs: float, xmr_price_usd: float) -> float:
        return MiningStatsTracker.estimate_xmr_per_day(hashrate_hs) * xmr_price_usd
