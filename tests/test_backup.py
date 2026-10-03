import json, tempfile, unittest
from pathlib import Path
from vault_backup_engine.core import snapshot, verify, restore


class BackupTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.source = self.root / "source"
        self.source.mkdir()
        (self.source / "hello.txt").write_text("hello")
        self.vault = self.root / "vault"

    def tearDown(self):
        self.tmp.cleanup()

    def test_roundtrip(self):
        snapshot(self.source, self.vault, "daily")
        restore(self.vault, "daily", self.root / "restored")
        self.assertEqual((self.root / "restored/hello.txt").read_text(), "hello")

    def test_deduplication(self):
        snapshot(self.source, self.vault, "first")
        snapshot(self.source, self.vault, "second")
        self.assertEqual(len(list((self.vault / "blobs").iterdir())), 1)

    def test_corruption_does_not_create_restore(self):
        snapshot(self.source, self.vault, "first")
        next((self.vault / "blobs").iterdir()).write_bytes(b"bad")
        with self.assertRaises(ValueError):
            restore(self.vault, "first", self.root / "restored")
        self.assertFalse((self.root / "restored").exists())

    def test_existing_target_preserved(self):
        snapshot(self.source, self.vault, "first")
        with self.assertRaises(ValueError):
            restore(self.vault, "first", self.source)
        self.assertEqual((self.source / "hello.txt").read_text(), "hello")

    def test_path_traversal_rejected(self):
        snapshot(self.source, self.vault, "first")
        manifest = self.vault / "snapshots/first.json"
        data = json.loads(manifest.read_text())
        data["files"][0]["path"] = "../escape"
        manifest.write_text(json.dumps(data))
        with self.assertRaises(ValueError):
            verify(self.vault, "first")

    def test_vault_inside_source_rejected(self):
        with self.assertRaises(ValueError):
            snapshot(self.source, self.source / "vault", "first")

    def test_duplicate_snapshot_rejected(self):
        snapshot(self.source, self.vault, "first")
        with self.assertRaises(ValueError):
            snapshot(self.source, self.vault, "first")
