import tempfile
from pathlib import Path
from braink_node.paths import default_dekstop_paths
from braink_node.ledger import LedgerStore
from braink_node.pass_runner import run_dekstop_pass

class NodeFixture:
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / "workspace"
        self.root.mkdir()
        self.paths = default_dekstop_paths(self.root)
        self.store = LedgerStore(self.base / "state/ledger.sqlite3")
        self.artifacts = self.base / "state/artifacts"

    def file(self, name, data=b"hello"):
        p = self.root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
        return p

    def check(self, **kwargs):
        return run_dekstop_pass(store=self.store, dekstop=self.paths, artifacts_dir=self.artifacts,
                                pass_route="test", **kwargs)


