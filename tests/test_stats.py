import unittest

from mayan_miner.stats import (
    MiningStatsTracker,
    sanitize_line,
    _XMRIG_SPEED_RE,
    _GENERIC_HASHRATE_RE,
    _ACCEPTED_RE,
)


class MiningStatsTrackerTests(unittest.TestCase):
    def setUp(self):
        self.tracker = MiningStatsTracker()

    def test_feed_line_parses_xmrig_speed_line(self):
        line = "[2026-01-01 00:00:00] speed 10s/60s/15m 1234.5 1230.2 1220.0 H/s max 1300.0 H/s\n"
        changed = self.tracker.feed_line(line)
        self.assertTrue(changed)
        self.assertEqual(self.tracker.current_hashrate, 1234.5)
        self.assertEqual(self.tracker.peak_hashrate, 1234.5)
        self.assertEqual(list(self.tracker.hashrate_history), [1234.5])

    def test_feed_line_parses_xmrig_speed_line_lowercase_hs(self):
        # Some XMRig builds use lowercase "h/s".
        line = "[2026-01-01 00:00:00] speed 10s/60s/15m 4321.0 4320.0 4300.0 h/s max 4400.0 h/s\n"
        self.tracker.feed_line(line)
        self.assertEqual(self.tracker.current_hashrate, 4321.0)

    def test_feed_line_parses_xmrig_speed_line_with_ansi_colors(self):
        # XMRig on Windows emits VT/ANSI escape codes even when stdout is
        # piped through subprocess.PIPE (Win10+ console has VT support).
        line = (
            "\x1b[1m\x1b[32mspeed\x1b[0m "
            "\x1b[1m\x1b[32m10s/60s/15m\x1b[0m "
            "\x1b[1m\x1b[32m1234.5\x1b[0m "
            "\x1b[1m\x1b[32m1300.2\x1b[0m "
            "\x1b[1m\x1b[32m1250.0\x1b[0m "
            "\x1b[1m\x1b[32mH/s\x1b[0m max "
            "\x1b[1m\x1b[32m1400.0\x1b[0m \x1b[1m\x1b[32mH/s\x1b[0m\n"
        )
        self.assertTrue(self.tracker.feed_line(line))
        self.assertEqual(self.tracker.current_hashrate, 1234.5)
        self.assertEqual(self.tracker.peak_hashrate, 1234.5)

    def test_feed_line_parses_xmrig_speed_line_with_colored_timestamp(self):
        line = (
            "\x1b[1m\x1b[32m[2026-01-01 00:00:00]\x1b[0m  \x1b[1m\x1b[32mspeed\x1b[0m "
            "\x1b[1m\x1b[32m10s/60s/15m\x1b[0m \x1b[1m\x1b[32m777.0\x1b[0m "
            "\x1b[1m\x1b[32m770.0\x1b[0m \x1b[1m\x1b[32m760.0\x1b[0m \x1b[1m\x1b[32mH/s\x1b[0m\n"
        )
        self.assertTrue(self.tracker.feed_line(line))
        self.assertEqual(self.tracker.current_hashrate, 777.0)

    def test_feed_line_parses_generic_hashrate_line_with_unit(self):
        line = "Hashrate: 12.34 MH/s\n"
        changed = self.tracker.feed_line(line)
        self.assertTrue(changed)
        self.assertAlmostEqual(self.tracker.current_hashrate, 12.34 * 1_000_000.0)

    def test_feed_line_parses_generic_hashrate_with_ansi(self):
        line = "\x1b[1m\x1b[32mHashrate:\x1b[0m \x1b[1m\x1b[32m12.34\x1b[0m \x1b[1m\x1b[32mMH/s\x1b[0m\n"
        self.tracker.feed_line(line)
        self.assertAlmostEqual(self.tracker.current_hashrate, 12.34 * 1_000_000.0)

    def test_feed_line_parses_accepted_rejected_shares(self):
        line = "[2026-01-01 00:00:05] cpu accepted (5/1) diff 1234 (256 ms)\n"
        changed = self.tracker.feed_line(line)
        self.assertTrue(changed)
        self.assertEqual(self.tracker.accepted_shares, 5)
        self.assertEqual(self.tracker.rejected_shares, 1)

    def test_feed_line_parses_accepted_rejected_shares_with_ansi(self):
        line = (
            "\x1b[1m\x1b[32m[2026-01-01 00:00:05]\x1b[0m  cpu \x1b[1m\x1b[32maccepted\x1b[0m "
            "\x1b[1m\x1b[32m(7/2)\x1b[0m diff 1234 algorithm rx/0\n"
        )
        self.tracker.feed_line(line)
        self.assertEqual(self.tracker.accepted_shares, 7)
        self.assertEqual(self.tracker.rejected_shares, 2)

    def test_feed_line_parses_accepted_rejected_srbminer_style(self):
        # SRBMiner-style "Accepted 5/0" without parens.
        line = "[2026-01-01 00:00:05] Accepted 5/0 diff 1234\n"
        self.tracker.feed_line(line)
        self.assertEqual(self.tracker.accepted_shares, 5)
        self.assertEqual(self.tracker.rejected_shares, 0)

    def test_feed_line_ignores_unrelated_output_without_crashing(self):
        line = "Just a normal log line with nothing useful in it.\n"
        changed = self.tracker.feed_line(line)
        self.assertFalse(changed)
        self.assertEqual(self.tracker.current_hashrate, 0.0)

    def test_feed_line_handles_mixed_realistic_log_stream(self):
        # A realistic sequence of lines that XMRig actually emits, including
        # startup banners and color codes. Only the speed + accepted lines
        # should update stats; nothing else should crash or be mis-parsed.
        log_lines = [
            "* ABOUT  XMRig 6.21.0",
            "* LIBS   libuv 1.48.0",
            "* CPU    8 threads / 8 cores",
            "[2026-01-01 00:00:00] READY",
            "[2026-01-01 00:00:00] \x1b[1m\x1b[32mspeed\x1b[0m \x1b[1m\x1b[32m10s/60s/15m\x1b[0m \x1b[1m\x1b[32m1500.0\x1b[0m \x1b[1m\x1b[32m1500.0\x1b[0m \x1b[1m\x1b[32m1500.0\x1b[0m \x1b[1m\x1b[32mH/s\x1b[0m",
            "[2026-01-01 00:00:05] cpu \x1b[1m\x1b[32maccepted\x1b[0m \x1b[1m\x1b[32m(1/0)\x1b[0m diff 100000",
            "[2026-01-01 00:00:10] \x1b[1m\x1b[32mspeed\x1b[0m \x1b[1m\x1b[32m10s/60s/15m\x1b[0m \x1b[1m\x1b[32m2200.0\x1b[0m \x1b[1m\x1b[32m2200.0\x1b[0m \x1b[1m\x1b[32m2200.0\x1b[0m \x1b[1m\x1b[32mH/s\x1b[0m",
            "[2026-01-01 00:00:15] cpu \x1b[1m\x1b[32maccepted\x1b[0m \x1b[1m\x1b[32m(2/0)\x1b[0m diff 110000",
        ]
        for line in log_lines:
            self.tracker.feed_line(line + "\n")

        self.assertEqual(self.tracker.current_hashrate, 2200.0)
        self.assertEqual(self.tracker.peak_hashrate, 2200.0)
        self.assertEqual(list(self.tracker.hashrate_history), [1500.0, 2200.0])
        self.assertEqual(self.tracker.accepted_shares, 2)
        self.assertEqual(self.tracker.rejected_shares, 0)

    def test_reset_clears_history_and_counters(self):
        self.tracker.feed_line("speed 10s/60s/15m 500.0 500.0 500.0 H/s max 500.0 H/s\n")
        self.tracker.feed_line("accepted (2/0)\n")
        self.tracker.reset()
        self.assertEqual(self.tracker.current_hashrate, 0.0)
        self.assertEqual(self.tracker.peak_hashrate, 0.0)
        self.assertEqual(self.tracker.accepted_shares, 0)
        self.assertEqual(self.tracker.rejected_shares, 0)
        self.assertEqual(list(self.tracker.hashrate_history), [])

    def test_format_hashrate_scales_units(self):
        self.assertEqual(MiningStatsTracker.format_hashrate(500.0), "500.0 H/s")
        self.assertEqual(MiningStatsTracker.format_hashrate(1_500.0), "1.50 KH/s")
        self.assertEqual(MiningStatsTracker.format_hashrate(2_500_000.0), "2.50 MH/s")
        self.assertEqual(MiningStatsTracker.format_hashrate(3_500_000_000.0), "3.50 GH/s")

    def test_sanitize_line_removes_ansi_and_carriage_return(self):
        raw = "\x1b[1m\x1b[32mhello\x1b[0m\r\n"
        self.assertEqual(sanitize_line(raw), "hello\n")


if __name__ == "__main__":
    unittest.main()