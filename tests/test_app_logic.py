import importlib
import os
import sys
import tempfile
import unittest
from unittest import mock


class AppLogicTests(unittest.TestCase):
    def setUp(self) -> None:
        # Force a temp home so config/storage do not touch the real filesystem.
        self.tempdir = tempfile.TemporaryDirectory()
        self.addCleanup(self.tempdir.cleanup)
        self.env_patch = mock.patch.dict(
            os.environ, {"OVER_SSH_HOME": self.tempdir.name}
        )
        self.env_patch.start()
        self.addCleanup(self.env_patch.stop)
        for mod in ["over_ssh.config", "over_ssh.storage", "over_ssh.app"]:
            if mod in sys.modules:
                del sys.modules[mod]
        self.config = importlib.import_module("over_ssh.config")
        self.app_mod = importlib.import_module("over_ssh.app")

    def test_next_status_cycles(self) -> None:
        next_status = self.app_mod.next_status
        columns = ["todo", "doing", "done"]
        self.assertEqual(next_status("todo", columns), "doing")
        self.assertEqual(next_status("doing", columns), "done")
        self.assertEqual(next_status("done", columns), "todo")
        self.assertEqual(next_status("unknown", columns), "todo")
        self.assertEqual(next_status("todo", []), "todo")

    def test_status_labels_default_merge(self) -> None:
        cfg = self.config.load_config()
        app = self.app_mod.TaskBoardApp(cfg, [])
        self.assertIn("backlog", app.status_labels)
        self.assertTrue(app.status_labels["backlog"].lower().startswith("backlog"))


if __name__ == "__main__":
    unittest.main()
