"""Negative references and planning boundaries against the real pinned town."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from scripts.settlement_life.check import SOURCE_COMMIT, check

ROOT = Path(__file__).resolve().parents[2]
TOWN = Path("docs/vision/research/blockout/towns/gullwick.json")


class Planning(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source_bytes = subprocess.check_output(
            ["git", "show", f"{SOURCE_COMMIT}:{TOWN.as_posix()}"], cwd=ROOT)
        cls.source = json.loads(cls.source_bytes)
        cls.packet = json.loads((ROOT / TOWN).read_text())

    def test_current_packet_and_layout_preservation(self):
        self.assertEqual(check(self.packet, self.source), [])
        self.assertEqual(len(self.packet["residents"]), 8)
        self.assertEqual(len(self.packet["routines"]), 32)

    def test_source_geometry_and_roles_cannot_drift(self):
        for field, value in [("occupants", "a new invented profession"),
                             ("door_cells", [1, 2]), ("faces", "elsewhere")]:
            with self.subTest(field=field):
                packet = copy.deepcopy(self.packet)
                packet["buildings"][0][field] = value
                self.assertIn("source: non-life town data changed", check(packet, self.source))

    def test_rejects_missing_duplicate_and_dangling_references(self):
        mutations = [
            lambda p: p["residents"].pop(),
            lambda p: p["residents"].append(copy.deepcopy(p["residents"][0])),
            lambda p: p["residents"][0].update(home="missing"),
            lambda p: p["residents"][0].update(district="missing"),
            lambda p: p["residents"][0].update(role="smith"),
            lambda p: p["routines"][0].update(resident="missing"),
            lambda p: p["routines"][0].update(place="missing"),
            lambda p: p["routines"].pop(),
            lambda p: p["routines"].append(copy.deepcopy(p["routines"][0])),
            lambda p: p["routines"][0].update(time_of_day="25:00"),
            lambda p: p["routines"][0].update(place=p["residents"][1]["home"]),
        ]
        for i, mutate in enumerate(mutations):
            with self.subTest(case=i):
                packet = copy.deepcopy(self.packet)
                mutate(packet)
                self.assertTrue(check(packet, self.source))

    def test_cannot_silently_activate_or_invent_inputs(self):
        mutations = [
            lambda p: p["life_planning"].update(runtime_enabled=0),
            lambda p: p["life_planning"].update(status="approved"),
            lambda p: p["life_planning"].update(population_count=8),
            lambda p: p["life_planning"].update(source_blob="0" * 40),
            lambda p: p["life_planning"]["animals"].update(instances=["gull"]),
            lambda p: p["life_planning"]["props"].update(status="approved"),
            lambda p: p["residents"][0].update(name="Invented", name_status="approved"),
            lambda p: p["residents"][0].update(workplace=p["residents"][0]["home"]),
            lambda p: p["routines"][0].update(timing="production"),
        ]
        for i, mutate in enumerate(mutations):
            with self.subTest(case=i):
                packet = copy.deepcopy(self.packet)
                mutate(packet)
                self.assertTrue(check(packet, self.source))

    def test_cli_valid_invalid_and_malformed_leave_bytes_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, plan = Path(tmp) / "source.json", Path(tmp) / "plan.json"
            source.write_bytes(self.source_bytes)
            invalid = copy.deepcopy(self.packet)
            invalid["routines"][0]["place"] = "missing"
            for content, expected in [(json.dumps(self.packet), 0),
                                      (json.dumps(invalid), 1), ("{", 2), ("[]", 2)]:
                plan.write_text(content)
                result = subprocess.run([sys.executable, "-m", "scripts.settlement_life.check",
                                         str(plan), "--source", str(source)],
                                        cwd=ROOT, capture_output=True, text=True)
                self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
                self.assertEqual(plan.read_text(), content)
                self.assertEqual(source.read_bytes(), self.source_bytes)


if __name__ == "__main__":
    unittest.main()
