import importlib
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


class ConfigStorageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.home = Path(self.tempdir.name)
        self.env_patch = mock.patch.dict(os.environ, {"OVER_SSH_HOME": str(self.home)})
        self.env_patch.start()
        self.addCleanup(self.env_patch.stop)
        # Reload modules so they pick up the new OVER_SSH_HOME.
        for mod in ["over_ssh.config", "over_ssh.storage"]:
            if mod in sys.modules:
                del sys.modules[mod]
        self.config = importlib.import_module("over_ssh.config")
        self.storage = importlib.import_module("over_ssh.storage")

    def test_config_respects_env_and_creates_file(self) -> None:
        cfg_path = self.config.DEFAULT_CONFIG_PATH
        self.assertFalse(cfg_path.exists())
        cfg = self.config.load_config()
        self.assertTrue(cfg_path.exists())
        self.assertEqual(cfg.data_path.parent, self.home)
        self.assertIn("backlog", cfg.status_labels)

    def test_storage_loads_defaults_and_writes_file(self) -> None:
        tasks_path = self.storage.DEFAULT_TASK_PATH
        self.assertFalse(tasks_path.exists())
        tasks = self.storage.load_tasks()
        self.assertTrue(tasks_path.exists())
        self.assertGreaterEqual(len(tasks), 1)

    def test_storage_recovers_from_corrupt_json(self) -> None:
        tasks_path = self.storage.DEFAULT_TASK_PATH
        tasks_path.parent.mkdir(parents=True, exist_ok=True)
        tasks_path.write_text("{not valid json", encoding="utf-8")
        tasks = self.storage.load_tasks()
        self.assertGreaterEqual(len(tasks), 1)
        backup = tasks_path.with_suffix(".bak")
        self.assertTrue(backup.exists())


if __name__ == "__main__":
    unittest.main()
