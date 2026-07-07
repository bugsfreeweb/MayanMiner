import os
import tempfile
import unittest

from mayan_miner.config import SecureConfigManager, default_config
from mayan_miner.miner import build_miner_command


class SecureConfigManagerTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage_path = os.path.join(self.temp_dir.name, "config.json")
        self.key_path = os.path.join(self.temp_dir.name, "key.key")
        self.manager = SecureConfigManager(storage_path=self.storage_path, key_path=self.key_path)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_round_trip(self):
        cfg = default_config()
        cfg["wallet"] = "42"
        cfg["pool"] = "mine.example"
        self.manager.save_config(cfg)
        loaded = self.manager.load_config()
        self.assertEqual(loaded["wallet"], "42")
        self.assertEqual(loaded["pool"], "mine.example")

    def test_build_command_contains_key_settings(self):
        cfg = default_config()
        cfg.update(
            {
                "pool": "pool.example:3333",
                "wallet": "wallet123",
                "worker": "cpu-worker",
                "password": "x",
                "algorithm": "rx/0",
                "threads": 4,
                "use_all_cores": False,
            }
        )
        command = build_miner_command(cfg)
        self.assertIn("--url", command)
        self.assertIn("pool.example:3333", command)
        self.assertIn("--user", command)
        self.assertIn("wallet123", command)
        self.assertIn("--threads", command)
        self.assertIn("4", command)

    def test_custom_miner_kind_uses_custom_flags(self):
        cfg = default_config()
        cfg.update(
            {
                "miner_kind": "custom",
                "miner_executable": "miner.exe",
                "extra_args": "--api-port 8080",
            }
        )
        command = build_miner_command(cfg)
        self.assertEqual(command[0], "miner.exe")
        self.assertIn("--api-port", command)
        self.assertNotIn("--url", command)

    def test_custom_miner_kind_uses_custom_algorithm_flag_when_non_default(self):
        cfg = default_config()
        cfg.update(
            {
                "miner_kind": "custom",
                "miner_executable": "miner.exe",
                "algorithm": "my-special-algo",
            }
        )
        command = build_miner_command(cfg)
        self.assertIn("--algo", command)
        self.assertIn("my-special-algo", command)

    def test_custom_miner_kind_uses_command_template(self):
        cfg = default_config()
        cfg.update(
            {
                "miner_kind": "custom",
                "miner_executable": "otherminer.exe",
                "pool": "pool.example:5555",
                "wallet": "abc123",
                "algorithm": "some-algo",
                "threads": 6,
                "custom_command_template": (
                    "{executable} -a {algorithm} -o {pool} -u {wallet} -t {threads}"
                ),
            }
        )
        command = build_miner_command(cfg)
        self.assertEqual(
            command,
            ["otherminer.exe", "-a", "some-algo", "-o", "pool.example:5555", "-u", "abc123", "-t", "6"],
        )


if __name__ == "__main__":
    unittest.main()
