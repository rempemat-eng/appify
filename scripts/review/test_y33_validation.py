#!/usr/bin/env python3
"""Source-only Y33 receiving regressions; execution needs a separate lead GO.

Future command (no engine/setup/download): python -I -B scripts/review/test_y33_validation.py
The H1 import artifact and raw logs remain immutable. These controls exercise only
capacity(), snapshot() refusal, diagnostic_text() and orphan_diagnostics().
"""
from __future__ import annotations

import errno
import importlib.util
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest import mock

spec = importlib.util.spec_from_file_location(
    "y33_receiving_under_test", Path(__file__).with_name("y33_validation.py")
)
receiver = importlib.util.module_from_spec(spec)
spec.loader.exec_module(receiver)

# Exact two raw lines from H1 run41050143988 artifact12973498718/import.log.
# ZIP SHA256 68c447e83db0ff44a59d17e8d78cc15011c4379788a1870915835d1d03ccb8ae
# import.log SHA256 470294dc20a89886ad5b43344c4b49703a060726e96eaf99c186d5d5ceb0c6fc
H1_REGISTRATIONS = (
    "[  49% ] \x1b[90m\x1b[1mupdate_scripts_classes\x1b[22m | GdUnitOrphanNodeInfo\x1b[39m\x1b[0m",
    "[  49% ] \x1b[90m\x1b[1mupdate_scripts_classes\x1b[22m | GdUnitOrphanNodesMonitor\x1b[39m\x1b[0m",
)


class ReceivingRegressions(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="y33-receiving-regression-")
        self.addCleanup(self.temporary.cleanup)
        base = Path(self.temporary.name)
        self.controller = object.__new__(receiver.Controller)
        self.controller.root = base / "private"
        self.controller.source = base / "source"
        self.controller.candidate = base / "candidate"
        self.controller.game = self.controller.source / "game"
        self.controller.owned_roots = (
            self.controller.root, self.controller.source, self.controller.candidate
        )
        for root in self.controller.owned_roots:
            root.mkdir()
        # Reserve is a separate deterministic refusal control. Ambient host free
        # space must not decide whether the other tiny unit controls can run.
        self.usage = mock.patch.object(
            receiver.shutil, "disk_usage", return_value=shutil._ntuple_diskusage(
                receiver.FREE_RESERVE * 4, 0, receiver.FREE_RESERVE * 4
            )
        )
        self.usage.start()
        self.addCleanup(self.usage.stop)

    def real_file(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"owned regression bytes\n" * 256)
        return path

    def disappear_at_lstat(self, victim: Path):
        original = Path.lstat
        removed = []

        def lstat(path, *args, **kwargs):
            if path == victim and not removed:
                # Actual inode removal AFTER os.walk yielded the real file.
                path.unlink()
                removed.append(path)
            return original(path, *args, **kwargs)

        return mock.patch.object(Path, "lstat", new=lstat), removed

    def test_mutable_owned_file_disappearance_at_lstat_is_tolerated(self) -> None:
        keeper = self.real_file(self.controller.root / "retained.log")
        for parent in (
            self.controller.game / ".godot/imported",
            self.controller.game / "reports-y33-red",
            self.controller.root / "evidence",
        ):
            with self.subTest(parent=parent):
                victim = self.real_file(parent / "texture.ctex-temp")
                patch, removed = self.disappear_at_lstat(victim)
                with patch:
                    result = self.controller.capacity()
                self.assertEqual(removed, [victim])
                self.assertFalse(victim.exists())
                self.assertGreaterEqual(
                    result["owned_allocated_bytes"], keeper.stat().st_blocks * 512
                )
                self.assertEqual(keeper.read_bytes(), b"owned regression bytes\n" * 256)

    def test_missing_tracked_or_candidate_file_is_not_tolerated(self) -> None:
        for victim in (
            self.controller.game / "game.gd",
            self.controller.candidate / "scripts/review/y33_validation.py",
        ):
            with self.subTest(victim=victim):
                self.real_file(victim)
                patch, removed = self.disappear_at_lstat(victim)
                with patch, self.assertRaises(FileNotFoundError):
                    self.controller.capacity()
                self.assertEqual(removed, [victim])

    def test_snapshot_missing_tracked_source_still_refuses(self) -> None:
        victim = self.real_file(self.controller.game / "game.gd")
        expected = {"game/game.gd": ("100644", receiver.blob(victim))}
        patch, removed = self.disappear_at_lstat(victim)
        with mock.patch.object(receiver, "git", side_effect=[
            receiver.GAME_SHA.encode(), receiver.GAME_TREE.encode()
        ]), mock.patch.object(receiver, "tree", return_value=expected), patch:
            with self.assertRaises(FileNotFoundError):
                self.controller.snapshot()
        self.assertEqual(removed, [victim])

    def test_lstat_permission_and_other_io_errors_propagate(self) -> None:
        victim = self.real_file(self.controller.game / ".godot/imported/owned.ctex-temp")
        original = Path.lstat
        for error in (
            PermissionError(errno.EACCES, "regression permission refusal", str(victim)),
            OSError(errno.EIO, "regression IO refusal", str(victim)),
        ):
            with self.subTest(error=error):
                def lstat(path, *args, **kwargs):
                    if path == victim:
                        raise error
                    return original(path, *args, **kwargs)
                with mock.patch.object(Path, "lstat", new=lstat):
                    with self.assertRaises(type(error)) as caught:
                        self.controller.capacity()
                self.assertIs(caught.exception, error)
                self.assertTrue(victim.is_file())

    def test_directory_scan_permission_refusal_is_not_silenced(self) -> None:
        blocked = self.controller.game / ".godot/imported"
        self.real_file(blocked / "owned.ctex-temp")
        original = receiver.os.scandir
        error = PermissionError(errno.EACCES, "regression scandir refusal", str(blocked))

        def scandir(path):
            if Path(path) == blocked:
                raise error
            return original(path)

        with mock.patch.object(receiver.os, "scandir", side_effect=scandir):
            with self.assertRaises(PermissionError) as caught:
                self.controller.capacity()
        self.assertIs(caught.exception, error)

    def test_real_symlink_is_refused(self) -> None:
        target = self.real_file(self.controller.root / "target")
        link = self.controller.game / ".godot/imported/link.ctex-temp"
        link.parent.mkdir(parents=True)
        link.symlink_to(target)
        with self.assertRaisesRegex(RuntimeError, "symlink"):
            self.controller.capacity()
        self.assertTrue(link.is_symlink())

    def test_real_allocated_blocks_over_budget_are_refused(self) -> None:
        victim = self.real_file(self.controller.root / "allocated")
        self.assertGreater(victim.stat().st_blocks * 512, 0)
        # Exercise real allocated blocks with a tiny threshold; never allocate512MiB.
        with mock.patch.object(receiver, "OWNED_LIMIT", 0):
            with self.assertRaisesRegex(RuntimeError, "owned disk/reserve limit"):
                self.controller.capacity()

    def test_free_reserve_shortfall_is_refused(self) -> None:
        with mock.patch.object(receiver.shutil, "disk_usage",
                               return_value=shutil._ntuple_diskusage(1, 1, 0)):
            with self.assertRaisesRegex(RuntimeError, "owned disk/reserve limit"):
                self.controller.capacity()

    def test_actual_healthy_registration_lines_are_not_orphans(self) -> None:
        raw = ("\n".join(H1_REGISTRATIONS) + "\n").encode()
        path = self.controller.root / "import-fragment.log"
        path.write_bytes(raw)
        text = receiver.diagnostic_text(path)
        self.assertEqual(receiver.orphan_diagnostics(text), [])
        self.assertEqual(path.read_bytes(), raw)

    def test_positive_orphan_and_engine_leak_diagnostics_remain_visible(self) -> None:
        # GdUnit GdAssertMessages.orphan_detected emits the first text; its
        # console reporter emits the numeric summary. These are positive
        # fixtures, NOT messages observed in H1's healthy registration fragment.
        for line in (
            "WARNING: Detected 2 orphan nodes.",
            "7 test cases | 0 errors | 0 failures | 0 skipped | 1 orphans |",
            "Orphans: 1",
            "ObjectDB instances leaked at exit (run with --verbose for details).",
            "ERROR: 1 resources still in use at exit (run with --verbose for details).",
            "WARNING: 1 RID allocations of type 'CanvasItem' were leaked at exit.",
        ):
            with self.subTest(line=line):
                self.assertEqual(receiver.orphan_diagnostics(line), [line])

    def test_zero_orphan_summaries_are_not_positive_diagnostics(self) -> None:
        for line in (
            "7 test cases | 0 errors | 0 failures | 0 skipped | 0 orphans |",
            "Orphans: 0", "Orphan nodes = 0", "0 orphan nodes",
        ):
            with self.subTest(line=line):
                self.assertEqual(receiver.orphan_diagnostics(line), [])

    def test_zero_summary_never_hides_positive_count_on_same_line(self) -> None:
        line = "Orphans: 0 | WARNING: Detected 2 orphan nodes."
        self.assertEqual(receiver.orphan_diagnostics(line), [line])


if __name__ == "__main__":
    unittest.main(verbosity=2)

