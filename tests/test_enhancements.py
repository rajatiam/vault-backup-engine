import unittest, json, csv, io
from tests import test_backup as fixtures
from vault_backup_engine.core import snapshot, compare


class FeatureTests(unittest.TestCase):
    setUp = fixtures.BackupTests.setUp
    tearDown = fixtures.BackupTests.tearDown

    def test_compare_added_removed_and_changed(self):
        (self.source / "removed.txt").write_text("old")
        snapshot(self.source, self.vault, "before")
        (self.source / "removed.txt").unlink()
        (self.source / "hello.txt").write_text("new")
        (self.source / "added.txt").write_text("added")
        snapshot(self.source, self.vault, "after")
        result = compare(self.vault, "before", "after")
        self.assertEqual(result["added"], ["added.txt"])
        self.assertEqual(result["removed"], ["removed.txt"])
        self.assertEqual(result["changed"], ["hello.txt"])

    def test_comparison_does_not_mutate_vault(self):
        snapshot(self.source, self.vault, "one")
        before = {p: p.read_bytes() for p in self.vault.rglob("*") if p.is_file()}
        self.assertEqual(compare(self.vault, "one", "one")["changed"], [])
        self.assertEqual(
            before, {p: p.read_bytes() for p in self.vault.rglob("*") if p.is_file()}
        )
