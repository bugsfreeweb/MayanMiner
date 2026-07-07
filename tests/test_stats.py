import unittest

from mayan_miner.stats import MiningStatsTracker


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

    def test_feed_line_parses_generic_hashrate_line_with_unit(self):
        line = "Hashrate: 12.34 MH/s\n"
        changed = self.tracker.feed_line(line)
        self.assertTrue(changed)
        self.assertAlmostEqual(self.tracker.current_hashrate, 12.34 * 1_000_000.0)

    def test_feed_line_parses_accepted_rejected_shares(self):
        line = "[2026-01-01 00:00:05] cpu accepted (5/1) diff 1234 (256 ms)\n"
        changed = self.tracker.feed_line(line)
        self.assertTrue(changed)
        self.assertEqual(self.tracker.accepted_shares, 5)
        self.assertEqual(self.tracker.rejected_shares, 1)

    def test_feed_line_ignores_unrelated_output_without_crashing(self):
        line = "Just a normal log line with nothing useful in it.\n"
        changed = self.tracker.feed_line(line)
        self.assertFalse(changed)
        self.assertEqual(self.tracker.current_hashrate, 0.0)

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


if __name__ == "__main__":
    unittest.main()
