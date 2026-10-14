"""Fail-closed authorizer configuration regressions; no network required."""
import tempfile
import unittest
from pathlib import Path
from vfs_server.auth import MutationAuthorizer

class TestSecurityStartup(unittest.TestCase):
    def test_missing_configuration_denies(self):
        auth = MutationAuthorizer()
        for header in (None, "Bearer anything", "Basic anything", ""):
            self.assertFalse(auth.allowed(header))

    def test_empty_token_file_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "token"
            path.write_text("  ")
            with self.assertRaises(ValueError):
                MutationAuthorizer(str(path))

    def test_token_enforced_and_nonmatching_denied(self):
        with tempfile.TemporaryDirectory() as root:
            path = Path(root) / "token"
            path.write_text("only-valid-token")
            auth = MutationAuthorizer(str(path))
            self.assertTrue(auth.allowed("Bearer only-valid-token"))
            for header in (None, "Bearer wrong", "Bearer ", "Basic only-valid-token"):
                self.assertFalse(auth.allowed(header))

    def test_conflicting_auth_modes_rejected(self):
        with self.assertRaises(ValueError):
            MutationAuthorizer("anything", insecure_local_dev=True)

if __name__ == "__main__":
    unittest.main()
