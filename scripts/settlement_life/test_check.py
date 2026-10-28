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


CURRENT_COMMIT = "4984438d09b5fe1333d3e6ea6e6ee82be2bdc908"


class TownSources(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from scripts.settlement_life.check import SourcePin
        cls.examples = {}
        template = json.loads((ROOT / TOWN).read_text())["life_planning"]
        for town in ("canalside", "gullwick"):
            path = f"docs/vision/research/blockout/towns/{town}.json"
            raw = subprocess.check_output(["git", "show", f"{CURRENT_COMMIT}:{path}"], cwd=ROOT)
            blob = subprocess.check_output(["git", "rev-parse", f"{CURRENT_COMMIT}:{path}"],
                                           cwd=ROOT, text=True).strip()
            pin = SourcePin(CURRENT_COMMIT, blob, path)
            source = json.loads(raw)
            packet = copy.deepcopy(source)
            packet["life_planning"] = copy.deepcopy(template)
            packet["life_planning"].update(source_commit=pin.commit, source_blob=pin.blob,
                                           source_path=pin.path)
            packet["residents"] = []
            packet["routines"] = []
            for home in source["buildings"]:
                if not home.get("occupants"):
                    continue
                rid = f"{home['id']}-representative"
                packet["residents"].append({
                    "id": rid, "home": home["id"], "role": home["occupants"],
                    "source_occupants": home["occupants"], "district": home["district"],
                    "name": f"{home['occupants']} (placeholder)", "name_status": "placeholder",
                    "workplace": None, "workplace_status": "deferred", "status": "proposal"})
                for phase in ("morning", "day", "evening", "night"):
                    packet["routines"].append({"resident": rid, "time_of_day": phase,
                        "place": home["faces"] if phase == "day" else home["id"],
                        "status": "proposal", "timing": "placeholder"})
            cls.examples[town] = raw, pin, source, packet

    def cli(self, packet_bytes, source_bytes, pin, flags=None):
        with tempfile.TemporaryDirectory(prefix="MyGame town source ") as tmp:
            plan, source = Path(tmp) / "plan.json", Path(tmp) / "source.json"
            plan.write_bytes(packet_bytes)
            source.write_bytes(source_bytes)
            options = flags if flags is not None else ["--source-commit", pin.commit,
                "--source-blob", pin.blob, "--source-path", pin.path]
            result = subprocess.run([sys.executable, "-m", "scripts.settlement_life.check",
                str(plan), "--source", str(source), *options], cwd=ROOT,
                capture_output=True, text=True, timeout=40)
            self.assertEqual(plan.read_bytes(), packet_bytes)
            self.assertEqual(source.read_bytes(), source_bytes)
            self.assertNotIn("Traceback", result.stderr)
            return result

    def test_two_real_current_sources_preserve_authored_metadata(self):
        for town, (raw, pin, source, packet) in self.examples.items():
            with self.subTest(town=town):
                self.assertEqual(check(packet, source, source_pin=pin), [])
                self.assertIn("landmarks", source)
                self.assertTrue(all("counts_as" in b for b in source["buildings"]))
                result = self.cli(json.dumps(packet).encode(), raw, pin)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_current_gullwick_is_not_a_silent_source_refresh(self):
        _, pin, source, _ = self.examples["gullwick"]
        original = json.loads((ROOT / TOWN).read_text())
        findings = check(original, source, source_pin=pin)
        self.assertIn("source: non-life town data changed", findings)
        self.assertIn("provenance: pinned source commit/blob mismatch", findings)
        self.assertIn("provenance: pinned source path mismatch", findings)

    def test_explicit_pin_cannot_be_replaced_by_packet_claim(self):
        raw, pin, source, packet = self.examples["canalside"]
        other = self.examples["gullwick"][1]
        for field, value in [("source_commit", "0" * 40), ("source_blob", other.blob),
                             ("source_path", other.path), ("source_path", None)]:
            with self.subTest(field=field):
                bad = copy.deepcopy(packet)
                bad["life_planning"][field] = value
                self.assertTrue(check(bad, source, source_pin=pin))
                self.assertEqual(self.cli(json.dumps(bad).encode(), raw, pin).returncode, 1)

    def test_new_town_keeps_original_refusal_boundaries(self):
        _, pin, source, packet = self.examples["canalside"]
        mutations = [
            lambda p: p["buildings"][0].update(counts_as=2),
            lambda p: p["landmarks"].append({"id": "invented"}),
            lambda p: p["routines"][0].update(place="missing"),
            lambda p: p["routines"].append(copy.deepcopy(p["routines"][0])),
            lambda p: p["residents"][0].update(role="invented"),
            lambda p: p["life_planning"].update(runtime_enabled=True),
            lambda p: p["life_planning"].update(population_count=10),
            lambda p: p["life_planning"]["animals"].update(instances=["invented"]),
        ]
        for i, mutate in enumerate(mutations):
            with self.subTest(case=i):
                bad = copy.deepcopy(packet)
                mutate(bad)
                self.assertTrue(check(bad, source, source_pin=pin))

    def test_cli_checks_exact_source_bytes_and_commit_path_mapping(self):
        raw, pin, _, packet = self.examples["canalside"]
        content = json.dumps(packet).encode()
        from scripts.settlement_life.check import SourcePin
        for source_bytes, identity in [(raw + b"\n", pin),
                (self.examples["gullwick"][0], pin),
                (raw, SourcePin(SOURCE_COMMIT, pin.blob, pin.path)),
                (raw, SourcePin(pin.commit, pin.blob, self.examples["gullwick"][1].path)),
                (raw, SourcePin("0" * 40, pin.blob, pin.path))]:
            with self.subTest(identity=identity, length=len(source_bytes)):
                self.assertEqual(self.cli(content, source_bytes, identity).returncode, 2)

    def test_cli_identity_must_be_complete_and_canonical(self):
        raw, pin, _, packet = self.examples["canalside"]
        for flags in [["--source-commit", pin.commit],
                ["--source-commit", pin.commit, "--source-blob", pin.blob],
                ["--source-commit", "HEAD", "--source-blob", pin.blob, "--source-path", pin.path],
                ["--source-commit", pin.commit, "--source-blob", pin.blob.upper(), "--source-path", pin.path],
                ["--source-commit", pin.commit, "--source-blob", pin.blob, "--source-path", "../town.json"]]:
            with self.subTest(flags=flags):
                self.assertEqual(self.cli(json.dumps(packet).encode(), raw, pin, flags).returncode, 2)

    def test_cli_rejects_ambiguous_or_malformed_documents(self):
        raw, pin, _, _ = self.examples["canalside"]
        for content in [b"{", b"[]", b'{"id":"first","id":"second"}',
                b'{"value":NaN}', b'{"value":Infinity}', b'\xff']:
            with self.subTest(content=content):
                self.assertEqual(self.cli(content, raw, pin).returncode, 2)

    def test_source_missing_duplicate_and_cross_kind_ids_are_rejected(self):
        _, pin, source, packet = self.examples["canalside"]
        for change in [lambda s: s["buildings"].append(copy.deepcopy(s["buildings"][0])),
                lambda s: s["streets"][0].update(id=s["buildings"][0]["id"]),
                lambda s: s.update(buildings={}), lambda s: s.update(id="gullwick")]:
            bad = copy.deepcopy(source)
            change(bad)
            with self.assertRaises(ValueError):
                check(packet, bad, source_pin=pin)


if __name__ == "__main__":
    unittest.main()
