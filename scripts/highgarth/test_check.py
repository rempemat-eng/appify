"""Real packet copies and subprocess controls; no art or runtime acceptance."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

from . import check as gate


class Concepts(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.packet = self.root / "scripts/highgarth"
        shutil.copytree(gate.HERE, self.packet, ignore=shutil.ignore_patterns("__pycache__"))
        self.data = self.root / "game/data/kit/concepts"
        self.data.mkdir(parents=True)
        for path in (gate.ROOT / "game/data/kit/concepts").glob("highgarth_*.json"):
            shutil.copyfile(path, self.data / path.name)

    def tearDown(self):
        self.temp.cleanup()

    def manifest(self, change):
        path = self.packet / "manifest.json"
        value = json.loads(path.read_text())
        change(value)
        path.write_text(json.dumps(value))

    def record(self, change, suffix="machiya"):
        path = self.data / ("highgarth_" + suffix + ".json")
        value = json.loads(path.read_text())
        change(value)
        path.write_text(json.dumps(value))

    def refuses(self, text):
        with self.assertRaisesRegex(ValueError, text):
            gate.check(self.root)

    def hashes(self):
        return {str(p.relative_to(self.root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in self.root.rglob("*") if p.is_file() and "__pycache__" not in str(p)}

    def cli(self):
        return subprocess.run([sys.executable, "-m", "scripts.highgarth.check", "--root", str(self.root), "--json"],
            cwd=gate.ROOT, capture_output=True, text=True, check=False)

    def test_all_real_concepts_variants_and_building_maps_pass_read_only(self):
        before = self.hashes()
        result = gate.check(self.root)
        self.assertEqual((result["concepts"], result["variants"], result["source_buildings_covered"]), (19, 32, 17))
        self.assertIs(result["approved"], False)
        self.assertIs(result["placeable"], False)
        self.assertIs(result["buildable"], False)
        self.assertEqual(before, self.hashes())

    def test_real_source_review_limits_remain_visible(self):
        limits = gate.check(self.root)["source_limits"]
        self.assertEqual(limits["legacy_purpose_labels"], ["highgarth-b001"])
        self.assertEqual(len(limits["machiya_bay_storeys"]), 6)
        self.assertEqual((limits["building_records"], limits["counted_buildings"], limits["declared_buildings_counted"]), (20, 20, 20))

    def test_missing_concept_file_fails(self):
        (self.data / "highgarth_pagoda.json").unlink()
        self.refuses("file inventory")

    def test_extra_concept_file_fails(self):
        shutil.copyfile(self.data / "highgarth_machiya.json", self.data / "highgarth_extra.json")
        self.refuses("file inventory")

    def test_duplicate_or_missing_brief_entry_fails(self):
        self.manifest(lambda m: m["concepts"].__setitem__(1, m["concepts"][0]))
        self.refuses("coverage")

    def test_unapproved_flags_are_boolean_not_numeric(self):
        for flag in ["approved", "buildable", "placeable"]:
            with self.subTest(flag=flag):
                self.manifest(lambda m: m.__setitem__(flag, 0))
                self.refuses("proposal flag")
                self.manifest(lambda m: m.__setitem__(flag, False))

    def test_material_or_gameplay_block_is_not_sneaked_into_concepts(self):
        self.record(lambda r: r.__setitem__("gameplay", {}))
        self.refuses("runtime/unknown block")

    def test_drawn_geometry_is_not_inferred_from_plan_envelope(self):
        self.record(lambda r: r["geometry"].__setitem__("size_px", [72, 120]))
        self.refuses("runtime geometry")

    def test_promotion_requires_receiving_owner_not_data_edit(self):
        self.record(lambda r: r["approval"].__setitem__("state", "approved"))
        self.refuses("promotion")

    def test_w0_structural_error_is_not_accepted(self):
        self.record(lambda r: r["placement"].__setitem__("snap", "diagonal"))
        self.refuses("W0 structural schema")

    def test_duplicate_variants_fail(self):
        self.record(lambda r: r["variants"].append(r["variants"][0]))
        self.refuses("duplicate variants")

    def test_variant_sprite_binding_is_not_an_approval(self):
        self.record(lambda r: r["variants"][0].__setitem__("png", "unreviewed.png"))
        self.refuses("variant/asset")

    def test_wrong_source_form_fails(self):
        self.manifest(lambda m: m["concepts"][0].__setitem__("source_form", "kura"))
        self.refuses("wrong source form")

    def test_unknown_source_reference_fails(self):
        self.manifest(lambda m: m["concepts"][0]["references"]["district_ids"].append("invented-place"))
        self.refuses("source reference")

    def test_other_building_cannot_replace_actual_form_mapping(self):
        self.manifest(lambda m: m["concepts"][0]["references"]["building_ids"].__setitem__(0, "highgarth-b001"))
        self.refuses("building mapping")

    def test_source_widths_and_json_number_types_are_exact(self):
        self.manifest(lambda m: m["concepts"][0]["widths"]["classes"][0].__setitem__("width_cells", 3.0))
        self.refuses("width/depth/type")

    def test_colour_and_modern_script_boundaries_cannot_be_expanded(self):
        self.manifest(lambda m: m["constraints"].__setitem__("modern_elements", True))
        self.refuses("design constraints")

    def test_vermilion_does_not_spread_to_shrine_gates(self):
        self.manifest(lambda m: next(r for r in m["concepts"] if r["id"] == "highgarth_shrine_gate").__setitem__("vermilion_scope", "gate"))
        self.refuses("vermilion scope")

    def test_source_schema_and_plan_snapshots_are_frozen(self):
        for name in gate.SOURCE_LOCK:
            with self.subTest(name=name):
                path = self.packet / "fixtures" / name
                before = path.read_bytes()
                path.write_bytes(before + b" ")
                self.refuses("source fingerprint")
                path.write_bytes(before)

    def test_changed_provenance_is_refused(self):
        self.manifest(lambda m: m["sources"]["source_highgarth.json"].__setitem__("commit", "wrong"))
        self.refuses("source provenance")

    def test_brief_snapshot_and_its_hash_cannot_be_relabelled(self):
        path = self.packet / "fixtures/brief.txt"
        path.write_text("different brief\n")
        self.manifest(lambda m: m["sources"]["brief.txt"].__setitem__("sha256", hashlib.sha256(path.read_bytes()).hexdigest()))
        self.refuses("brief fingerprint")

    def test_source_limit_is_not_hidden(self):
        self.manifest(lambda m: m["source_limits"].__setitem__("machiya_bay_storeys", []))
        self.refuses("limitations")

    def test_missing_deferred_or_nonplaceable_label_fails(self):
        self.record(lambda r: r["audit"]["todo"].remove(gate.PROPOSAL_NOTE))
        self.refuses("deferred labels")

    def test_missing_plinth_relation_fails(self):
        self.record(lambda r: r["placement"]["requires"].__setitem__(slice(None), [x for x in r["placement"]["requires"] if x.get("what") != "stone_plinth"]), "temple_hall")
        self.refuses("plinth relationship")

    def test_cli_is_deterministic_read_only_and_reports_limits(self):
        before = self.hashes()
        first, second = self.cli(), self.cli()
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(first.stdout, second.stdout)
        self.assertEqual(before, self.hashes())
        self.assertEqual(json.loads(first.stdout)["source_limits"]["declared_buildings_counted"], 20)

    def test_cli_rejects_bad_utf8_duplicates_nonfinite_and_unicode(self):
        path = self.data / "highgarth_machiya.json"
        good = path.read_bytes()
        cases = [b"\xff", b'{"id":1,"id":2}', b'{"id":NaN}', b'{"name":"\\ud800"}', b'{"name":"\\u0000"}']
        for bad in cases:
            with self.subTest(bad=bad):
                path.write_bytes(bad)
                result = self.cli()
                self.assertEqual(result.returncode, 1)
                self.assertNotIn("Traceback", result.stderr)
                self.assertEqual(path.read_bytes(), bad)
        path.write_bytes(good)

    def test_symlink_concept_is_refused(self):
        path = self.data / "highgarth_machiya.json"
        other = self.root / "outside.json"
        path.rename(other)
        path.symlink_to(other)
        self.refuses("symlink input")


if __name__ == "__main__":
    unittest.main()
