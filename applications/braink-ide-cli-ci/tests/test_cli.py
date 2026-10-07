import unittest
import contextlib
import io
from fixtures import NodeFixture
from braink_cli.cli import main

class CliTests(NodeFixture, unittest.TestCase):
    def test_cli_lifecycle_and_exit_codes(self):
        args = ["--workspace", str(self.root), "--state-dir", str(self.base / "state")]
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(main(args + ["init"]), 0)
            self.assertEqual(main(args + ["check", "--fail-on", "warn"]), 0)
            self.file("projects/demo/a.py")
            self.assertEqual(main(args + ["check", "--fail-on", "warn"]), 1)
            self.assertEqual(main(args + ["align", str(self.root / "projects/demo"), "--name", "demo"]), 0)
            self.assertEqual(main(args + ["check", "--fail-on", "warn", "--ingest"]), 0)
            self.assertEqual(main(args + ["index"]), 0)
            self.assertEqual(main(args + ["ingest", str(self.root / "projects/demo/a.py")]), 0)
            self.assertEqual(main(args + ["ingest", str(self.root / "projects/demo")]), 0)
            self.assertEqual(main(args + ["verify-ledger"]), 0)
            self.assertEqual(main(args + ["index", "--max-entries", "-1"]), 2)
