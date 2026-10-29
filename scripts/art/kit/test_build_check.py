"""Tiny real build/main controls; generated fixtures live only in temporary directories."""
from __future__ import annotations

import contextlib
import copy
import hashlib
import io
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np

from scripts.art.kit import build as B
from scripts.art.kit import dressing as DR


class BuildCheckTests(unittest.TestCase):
    def setUp(self):
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.root = Path(self.stack.enter_context(tempfile.TemporaryDirectory(prefix="kit-check-fixture-")))
        self.out = self.root / "outputs"
        self.terrain = {
            "id": "fixture_ground", "kind": "terrain", "approval": {"state": "candidate"},
            "terrain": {"material_id": 1, "priority": 1, "walkable": True,
                        "surface": "fixture", "fill": {"module": "scripts.art.kit.fills", "fn": "fixture"}},
        }
        self.transition = {
            "id": "fixture_edge", "kind": "transition", "approval": {"state": "candidate"},
            "transition": {"upper": "fixture_ground", "lower": "fixture_ground", "variants": 1,
                           "painter": {"fn": "fixture"}},
        }
        self.lib = {p["id"]: p for p in [self.terrain, self.transition]}
        self.stack.enter_context(patch.object(B, "OUT", str(self.out)))
        self.stack.enter_context(patch.object(B, "load_library", side_effect=lambda: copy.deepcopy(self.lib)))
        self.stack.enter_context(patch.object(B.F, "PERIOD", B.E.CELL))
        self.fill = self.stack.enter_context(patch.object(B, "paint_fill", side_effect=lambda _: np.full((B.E.CELL, B.E.CELL), 2, np.int32)))
        self.edge = self.stack.enter_context(patch.object(B, "paint_transition", return_value=np.ones((B.E.CELL, B.E.CELL, 2), np.int32)))
        self.stack.enter_context(patch.object(DR, "paint_decals", return_value={
            "fixture": (np.array([[1, -1], [2, 3]], np.int32), (0, 1)),
        }))
        self.assertEqual(self.run_main([]), 0)

    def run_main(self, argv):
        with contextlib.redirect_stdout(io.StringIO()):
            return B.main(argv)

    def snapshot(self, metadata=True):
        result = {}
        for p in self.root.rglob("*"):
            st = p.stat()
            entry = (st.st_mode, hashlib.sha256(p.read_bytes()).hexdigest() if p.is_file() else "directory")
            result[str(p.relative_to(self.root))] = entry + ((st.st_mtime_ns,) if metadata else ())
        return result

    def check_unchanged(self, expected):
        before = self.snapshot()
        self.assertEqual(self.run_main(["--check"]), expected)
        self.assertEqual(self.snapshot(), before)

    def test_clean_check_does_not_write_or_repaint_fill_and_transition(self):
        self.fill.reset_mock()
        self.edge.reset_mock()
        self.check_unchanged(0)
        self.fill.assert_not_called()
        self.edge.assert_not_called()

    def test_missing_auxiliary_outputs_are_refused_without_repair(self):
        for name in ["lut.png", "palette.png", "materials.tres", "tiers.png", "tiers.tres", "noise.png", "decal_fixture.png"]:
            with self.subTest(output=name):
                path = self.out / name
                data = path.read_bytes()
                path.unlink()
                self.check_unchanged(1)
                self.assertFalse(path.exists())
                path.write_bytes(data)

    def test_changed_auxiliary_bytes_are_refused_without_repair(self):
        for name in ["lut.png", "palette.png", "materials.tres", "tiers.png", "tiers.tres", "noise.png", "decal_fixture.png"]:
            with self.subTest(output=name):
                path = self.out / name
                data = path.read_bytes()
                path.write_bytes(data + b"unexpected output drift")
                self.check_unchanged(1)
                path.write_bytes(data)

    def test_manifest_output_metadata_drift_is_refused_without_repair(self):
        import json
        path = self.out / "manifest.json"
        man = json.loads(path.read_text())
        man["noise"] = "wrong.png"
        path.write_text(json.dumps(man, indent=1))
        self.check_unchanged(1)

    def test_missing_output_directory_is_not_created(self):
        missing = self.root / "not-created" / "outputs"
        with patch.object(B, "OUT", str(missing)):
            self.check_unchanged(1)
        self.assertFalse(missing.parent.exists())

    def test_missing_fill_and_transition_remain_refusals(self):
        for name in ["fill_fixture_ground.png", "over_fixture_edge.png"]:
            with self.subTest(output=name):
                path = self.out / name
                data = path.read_bytes()
                path.unlink()
                self.check_unchanged(1)
                path.write_bytes(data)

    def test_stale_piece_input_remains_refused_without_writes(self):
        self.terrain["terrain"]["fill"]["args"] = {"fixture_input_change": True}
        self.check_unchanged(1)

    def test_stale_transition_input_remains_refused_without_writes(self):
        self.transition["transition"]["painter"]["args"] = {"fixture_input_change": True}
        self.check_unchanged(1)

    def test_missing_manifest_remains_refused_without_recreation(self):
        (self.out / "manifest.json").unlink()
        self.check_unchanged(1)

    def test_new_dynamic_decal_output_is_not_silently_ignored(self):
        decals = {"fixture": (np.array([[1, -1], [2, 3]], np.int32), (0, 1)),
                  "another": (np.array([[3]], np.int32), (0, 0))}
        with patch.object(DR, "paint_decals", return_value=decals):
            self.check_unchanged(1)
        self.assertFalse((self.out / "decal_another.png").exists())

    def test_changed_auxiliary_input_is_refused_even_with_matching_piece_hashes(self):
        modified = B.PAL.LUT.copy()
        modified[2, 0] ^= 1
        with patch.object(B.PAL, "LUT", modified):
            self.check_unchanged(1)

    def test_normal_generation_stays_incremental_and_byte_identical(self):
        before = self.snapshot(metadata=False)
        self.fill.reset_mock()
        self.edge.reset_mock()
        self.assertEqual(self.run_main([]), 0)
        self.assertEqual(self.snapshot(metadata=False), before)
        self.fill.assert_not_called()
        self.edge.assert_not_called()

    def test_force_generation_retains_bytes_and_repaints(self):
        before = self.snapshot(metadata=False)
        self.fill.reset_mock()
        self.edge.reset_mock()
        self.assertEqual(self.run_main(["--all"]), 0)
        self.assertEqual(self.snapshot(metadata=False), before)
        self.fill.assert_called_once()
        self.edge.assert_called_once()


if __name__ == "__main__":
    unittest.main()
