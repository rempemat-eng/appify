"""Source-only receiving contract. Never imports or runs the map producer.

Allocated command (NOT run during authoring):
  FIRST_SLICE_INPUTS="$RUN/inputs" PYTHONDONTWRITEBYTECODE=1 \
    python3 -B -m unittest scripts.review.test_first_slice_adoption -v

Stage all 15 exact raw Git blobs, named by blob SHA, in that offline directory.
Missing, altered or oversized inputs FAIL preflight; nothing downloads or skips.
One CPU, 128 MiB RSS, 30 s wall ceiling; no engine/display/dependencies/network.
Capture stdout/stderr, exit and exact source/fixture pins in the lead's run packet.
All cases below were authored, not executed, for SLICE-DATA/r1.
"""

import ast
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import unittest


PINS = {
    "cinderwick-baseline": {
        "commit": "4984438d09b5fe1333d3e6ea6e6ee82be2bdc908",
        "path": "docs/vision/research/blockout/towns/cinderwick.json",
        "blob": "b1a6b82b71ba055bf6dc351f81a58766775bf1c4"
    },
    "cinderwick-proposal": {
        "commit": "4669140421d7d8c69482fc90b78fea0a50d1d4bc",
        "path": "docs/vision/research/blockout/towns/cinderwick.json",
        "blob": "9cacbd0833c090c5365d3a9afea84a15ac9c5977"
    },
    "hearthold-baseline": {
        "commit": "4984438d09b5fe1333d3e6ea6e6ee82be2bdc908",
        "path": "docs/vision/research/blockout/towns/hearthold.json",
        "blob": "f19a9108cf07a3b8140ba136c04149a8c0ddd31d"
    },
    "hearthold-proposal": {
        "commit": "59f3722d1b39050cc81709fa5933d4c9c093ee98",
        "path": "docs/vision/research/blockout/towns/hearthold.json",
        "blob": "51fad9db44e2a9be22d2bbb5b007249ae9ecebce"
    },
    "launch-cape-baseline": {
        "commit": "4984438d09b5fe1333d3e6ea6e6ee82be2bdc908",
        "path": "docs/vision/research/blockout/towns/launch-cape.json",
        "blob": "06faf55d311d78016966c977bedcc7598348b817"
    },
    "launch-cape-proposal": {
        "commit": "9276174000e47858e92a25803e606fb9dea1fc87",
        "path": "docs/vision/research/blockout/towns/launch-cape.json",
        "blob": "9aab428f54a898b2c19049857bc092fe39d6e009"
    },
    "report": {
        "commit": "ae2d5f658bb64bb7c321045011887e1ae3bfb28c",
        "path": "docs/codex/first-town-v56-adoption.md",
        "blob": "973a344214f8e00d7246a6c68546c49e618bbb1d"
    },
    "current-packets": {
        "commit": "44f6b7adaacb9900c40a13dd340dca990e580c5d",
        "path": "docs/vision/research/blockout/towns55.py",
        "blob": "dfd90fd6e9c9aa2ec3e32612935a2b399275683a"
    },
    "current-producer": {
        "commit": "44f6b7adaacb9900c40a13dd340dca990e580c5d",
        "path": "docs/vision/research/blockout/geo55.py",
        "blob": "4e198d81f178b6530c714dd39d6f9078d2b11354"
    },
    "exporter": {
        "commit": "44f6b7adaacb9900c40a13dd340dca990e580c5d",
        "path": "docs/vision/research/blockout/town_plans.py",
        "blob": "f643cdd362d7d81e81f3d9d5eb462d78271d4ebb"
    },
    "slice-plan": {
        "commit": "885b45ea4d6fd8cd2246d90903b8cebbba2705b4",
        "path": "game/data/plans/crossroads.json",
        "blob": "0ec43431f13f5086a5a96e997b60c7eccb7cab30"
    },
    "slice-spec": {
        "commit": "885b45ea4d6fd8cd2246d90903b8cebbba2705b4",
        "path": "docs/vision/vertical-slice.md",
        "blob": "5325c3a91de6865991feba5c2d02ebf60de65aa5"
    },
    "slice-region": {
        "commit": "885b45ea4d6fd8cd2246d90903b8cebbba2705b4",
        "path": "docs/vision/regions/home-valley-frostline-brackens.md",
        "blob": "3e9bc35eec3511dc9fad9f470283e26cfaf0fb73"
    },
    "woodland": {
        "commit": "885b45ea4d6fd8cd2246d90903b8cebbba2705b4",
        "path": "game/zones/woodland/woodland.tscn",
        "blob": "3640095ff54112750622c077dbd03f978b4a6c36"
    },
    "valley": {
        "commit": "885b45ea4d6fd8cd2246d90903b8cebbba2705b4",
        "path": "art/regions/valley.json",
        "blob": "8c1d357860e392a143ba11cb7b455ab7a14049e7"
    }
}

TOWNS = ("cinderwick", "hearthold", "launch-cape")
OFF = {"enabled": False, "selected": [], "approved": False,
       "foundation_included": False, "live_placement": False}
HOLDS = ["real-ground", "fresh-baseline-identity", "actual-approach",
         "source-feedback", "fullgates", "Y12", "Matt-on-PR", "foundation-inclusion"]
MISSING = {"fresh_baseline_identity", "real_ground", "actual_access",
           "cinderwick_frontage", "hearthold_workshop", "cape_clearance",
           "approval_and_foundation"}
SLICE_MISSING = {"home_valley_to_garden_runtime_binding", "regional_town_to_crossroads_origin",
                 "stone_circle_footprint", "live_approaches", "life_bindings"}
POINTERS = [("slice-plan", p) for p in (
    "/id", "/origin_on_canvas", "/box", "/buildings", "/routes/3", "/stairs/0",
    "/spawns/1", "/spawns/2", "/doors/0")] + [("valley", p) for p in (
        "/id", "/box", "/zones/0", "/zones/1", "/zones/3", "/stairs/2")]
NODE_SELECTORS = ("StoneSign", "Hatch", "start", "crossroads", "ToCrossroads")
TEXT = [("slice-spec", "entry",
         "The entry is the garden walk on the terrace (the woodland's east door)"),
        ("slice-region", "home valley", "the garden 320 x 576 unchanged")]


class ContractError(ValueError):
    """The receiving proposal is incomplete, changed or not authorised."""


def require(condition, field):
    if not condition:
        raise ContractError(field)


def canonical(value):
    # Unlike Python equality, this distinguishes True from 1 and 8 from 8.0.
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False)


def exact(actual, expected, field):
    require(canonical(actual) == canonical(expected), field)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "duplicate JSON key: " + key)
        result[key] = value
    return result


def read_json(raw):
    def no_constant(value):
        raise ContractError("non-JSON numeric constant: " + value)
    return json.loads(raw, object_pairs_hook=unique_object, parse_constant=no_constant)


def pinned_inputs(raw):
    """Validate actual bytes before parsing; never accept an asserted digest."""
    exact(sorted(raw), sorted(PINS), "source inputs missing or extra")
    result = {}
    for key, pin in PINS.items():
        data = raw[key]
        require(type(data) is bytes and len(data) <= 512 * 1024, key + ": raw byte limit")
        digest = hashlib.sha1(b"blob " + str(len(data)).encode("ascii") + b"\0" + data).hexdigest()
        require(digest == pin["blob"], key + ": immutable blob mismatch")
        result[key] = data.decode("utf-8", errors="strict")
    return result


def load_inputs(directory):
    require(bool(directory), "FIRST_SLICE_INPUTS is required; no source bodies executed")
    root = Path(directory)
    result = {}
    for key, pin in PINS.items():
        path = root / pin["blob"]
        require(path.is_file(), key + ": missing source input " + pin["blob"])
        require(path.stat().st_size <= 512 * 1024, key + ": source byte limit")
        result[key] = path.read_bytes()
    return result


def identified(records, field):
    require(type(records) is list, field + ": expected list")
    ids = [record.get("id") for record in records]
    require(all(type(value) is str and value for value in ids), field + ": missing identity")
    require(len(ids) == len(set(ids)), field + ": duplicate identity")
    return ids


def pointer(document, path):
    value = document
    for part in path.split("/")[1:]:
        value = value[int(part)] if isinstance(value, list) else value[part]
    return value


def function(tree, name):
    found = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == name]
    require(len(found) == 1, "missing/ambiguous source function " + name)
    return found[0]


def packet_literal(tree):
    found = [n for n in tree.body if isinstance(n, ast.Assign) and any(
        isinstance(t, ast.Name) and t.id == "PROPOSED_ADOPTIONS" for t in n.targets)]
    require(len(found) == 1, "PROPOSED_ADOPTIONS literal missing")
    return ast.literal_eval(found[0].value)


def validate_source_interface(text):
    """AST-only inspection of the real receiving path, not synthetic terrain."""
    tree = ast.parse(text["current-packets"])
    for name in ("lay_all", "hearthold", "launch_cape"):
        fn = function(tree, name)
        defaults = dict(zip((a.arg for a in fn.args.kwonlyargs), fn.args.kw_defaults))
        require("authored" in defaults and isinstance(defaults["authored"], ast.Constant)
                and defaults["authored"].value is None, name + ": default must remain None")
    fn = function(tree, "lay_feedback")
    require("authored" not in [a.arg for a in fn.args.args + fn.args.kwonlyargs],
            "lay_feedback selection forwarding changed; explicit review needed")
    calls = [n for n in ast.walk(fn) if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
             and n.func.id == "lay_all"]
    require(len(calls) == 1 and len(calls[0].args) == 2 and not calls[0].keywords,
            "lay_feedback silent default adoption")
    producer = ast.parse(text["current-producer"])
    calls = [n for n in ast.walk(producer) if isinstance(n, ast.Call)]
    cape = [n for n in calls if isinstance(n.func, ast.Attribute) and n.func.attr == "launch_cape"]
    require(len(cape) == 1 and len(cape[0].args) == 2 and not cape[0].keywords,
            "producer silent Cape selection")
    dispatch = [n for n in calls if isinstance(n.func, ast.IfExp)
                and isinstance(n.func.body, ast.Attribute) and n.func.body.attr == "lay_feedback"
                and isinstance(n.func.orelse, ast.Attribute) and n.func.orelse.attr == "lay_all"]
    require(len(dispatch) == 1 and len(dispatch[0].args) == 2 and not dispatch[0].keywords,
            "producer silent first-town selection")
    return packet_literal(tree)


def validate_contract(contract, raw):
    """Accept a receiving proposal, never approve its use on live ground."""
    require(set(contract) == {"schema", "task", "owner", "purpose", "ancestry", "adoption",
                              "sources", "consumer", "towns", "slice", "missing"}, "unknown contract fields")
    exact(contract["sources"], PINS, "exact immutable input pins")
    exact(contract["schema"], "mygame.first_slice_adoption.proposal.v1", "schema")
    exact(contract["adoption"], OFF, "adoption must remain explicitly OFF")
    exact(contract["ancestry"], {
        "parent": "ae2d5f658bb64bb7c321045011887e1ae3bfb28c",
        "reconciliation_blob": PINS["report"]["blob"],
        "receiving_snapshot": PINS["current-packets"]["commit"]}, "ancestry")
    exact(contract["consumer"]["owner"], "map-revision", "producer owner")
    require(set(contract["consumer"]) == {"owner", "interface", "selection", "v56_forwarding",
                                          "evidence", "required_inputs"}, "unknown consumer fields")
    exact(contract["consumer"]["selection"], {}, "consumer default selection")
    text = pinned_inputs(raw)
    packets = validate_source_interface(text)
    require(set(contract["missing"]) == MISSING and all(
        type(v) is str and v.strip() for v in contract["missing"].values()), "missing evidence fields")
    exact([t["id"] for t in contract["towns"]], list(TOWNS), "town identity/order")
    total_existing = total_added = 0
    for town in contract["towns"]:
        tid = town["id"]
        require(set(town) == {"id", "coordinate_frame", "baseline_source", "proposal_source", "packet_key",
                              "existing", "adoptable", "proposal_metadata", "existing_access",
                              "unapproved", "missing", "producer_packet"}, tid + ": unknown town fields")
        exact(town["baseline_source"], tid + "-baseline", tid + ": baseline source")
        exact(town["proposal_source"], tid + "-proposal", tid + ": proposal source")
        exact(town["packet_key"], tid, tid + ": packet identity")
        baseline = read_json(text[tid + "-baseline"])
        proposal = read_json(text[tid + "-proposal"])
        old_ids = identified(baseline["buildings"], tid + ": pinned baseline")
        identified(proposal["buildings"], tid + ": pinned proposal")
        identified(town["existing"], tid + ": existing")
        identified(town["adoptable"], tid + ": adoptable")
        additions = [b for b in proposal["buildings"] if b["id"] not in old_ids]
        retained = [b for b in proposal["buildings"] if b["id"] in old_ids]
        exact(retained, baseline["buildings"], tid + ": source retained identity/record")
        exact(town["existing"], baseline["buildings"], tid + ": lost/changed retained record")
        exact(town["adoptable"], additions, tid + ": lost/changed proposed record/door/plot")
        packet = packets[tid]
        exact(town["producer_packet"], packet, tid + ": exact source receiving packet")
        exact(packet["buildings"], additions, tid + ": receiving packet additions")
        for label, suffix in (("source", "-proposal"), ("baseline", "-baseline")):
            exact(packet[label], PINS[tid + suffix], tid + ": packet " + label)
        exact(packet["status"], "proposal", tid + ": packet approval")
        delta = {k: v for k, v in proposal.items() if k != "buildings"
                 and canonical(baseline.get(k)) != canonical(v)}
        exact(town["proposal_metadata"], delta, tid + ": metadata/open-use/district delta")
        exact(town["existing_access"], {k: baseline[k] for k in ("streets", "squares", "arrivals")},
              tid + ": access identities/approach geometry")
        for key in ("streets", "squares", "arrivals"):
            exact(proposal[key], baseline[key], tid + ": original approach changed")
        exact(town["unapproved"], {"ids": [b["id"] for b in additions], "status": "proposal",
              "live_placement": False, "holds": HOLDS}, tid + ": unapproved holds")
        missing = town["missing"]
        require(set(missing) == {"homes", "jobs", "residents", "routines", "animals"},
                tid + ": missing life fields")
        for field, value in missing.items():
            exact(value["status"], "missing", tid + ": inferred life " + field)
            require(type(value["detail"]) is str and bool(value["detail"].strip()),
                    tid + ": missing life explanation " + field)
            expected_keys = {"status", "detail"}
            if field in ("residents", "routines"):
                expected_keys.add("source_literal")
                exact(value["source_literal"], baseline[field], tid + ": life source literal")
            require(set(value) == expected_keys, tid + ": invented life binding " + field)
        total_existing += len(town["existing"])
        total_added += len(town["adoptable"])
    exact([total_existing, total_added], [51, 10], "record conservation")
    slice_ = contract["slice"]
    require(set(slice_) == {"status", "sequence_labels", "json_references", "text_references", "missing"},
            "unknown slice fields")
    exact(slice_["status"], "source_references_only", "slice approval")
    exact(slice_["sequence_labels"], ["home valley", "garden", "Crossroads", "woodland", "stone circle"],
          "slice scope; sequence labels do not prove route traversal")
    require(set(slice_["missing"]) == SLICE_MISSING and all(
        type(v) is str and v.strip() for v in slice_["missing"].values()), "slice missing fields")
    exact([(r["source"], r["pointer"]) for r in slice_["json_references"]], POINTERS,
          "slice exact access selectors")
    for ref in slice_["json_references"]:
        exact(ref["value"], pointer(read_json(text[ref["source"]]), ref["pointer"]),
              "slice changed door/route/identity: " + ref["pointer"])
    expected_text = []
    for node in NODE_SELECTORS:
        match = re.search(r'\[node name="' + re.escape(node) + r'"[^\n]*\]\n[\s\S]*?(?=\n\[|$)',
                          text["woodland"])
        require(match is not None, "woodland missing node " + node)
        expected_text.append({"source": "woodland", "selector": node,
                              "verbatim": match.group(0).rstrip()})
    for source, selector, literal in TEXT:
        require(literal in text[source], source + ": missing supported prose")
        expected_text.append({"source": source, "selector": selector, "verbatim": literal})
    exact(slice_["text_references"], expected_text, "slice text/node access bindings")
    return {"status": "proposal", "existing_records": total_existing, "proposed_records": total_added,
            "adoption_enabled": False, "placement_evidence": "missing"}


def receiving_offer(contract, raw, *, selected=()):
    """Consumer preflight. This revision refuses every attempted live selection."""
    summary = validate_contract(contract, raw)
    require(type(selected) in (list, tuple) and not selected,
            "selection is unapproved; retain default OFF and obtain a reviewed successor contract")
    return {"summary": summary, "selected": [],
            "existing": {t["id"]: copy.deepcopy(t["existing"]) for t in contract["towns"]},
            "adoptable": {t["id"]: copy.deepcopy(t["adoptable"]) for t in contract["towns"]},
            "proposal_packets": {t["id"]: copy.deepcopy(t["producer_packet"]) for t in contract["towns"]}}


def check_received_existing(contract, raw, records):
    """Future producer boundary: stop on baseline drift, never rename or overwrite it.

    An exact match is identity compatibility only, not ground/access/approval.
    The caller must provide actual records; this module fabricates none.
    """
    validate_contract(contract, raw)
    exact(sorted(records), sorted(TOWNS), "received town inventory")
    for town in contract["towns"]:
        tid = town["id"]
        identified(records[tid], tid + ": received baseline")
        exact(records[tid], town["existing"], tid + ": received baseline drift; reconcile with map owner")
    return {"historical_identity_compatible": True, "adoption_enabled": False,
            "placement_evidence": "missing"}


class FirstSliceAdoptionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = load_inputs(os.environ.get("FIRST_SLICE_INPUTS"))
        pinned_inputs(cls.raw)
        cls.fixture = read_json((Path(__file__).parent / "fixtures" / "first_slice_adoption.json").read_text())

    def reject(self, mutate, message):
        candidate = copy.deepcopy(self.fixture)
        mutate(candidate)
        with self.assertRaisesRegex((ContractError, KeyError), message):
            validate_contract(candidate, self.raw)

    def test_positive_receiving_proposal_matches_real_pinned_packets(self):
        self.assertEqual(validate_contract(self.fixture, self.raw), {
            "status": "proposal", "existing_records": 51, "proposed_records": 10,
            "adoption_enabled": False, "placement_evidence": "missing"})

    def test_positive_off_offer_does_not_alias_or_adopt_records(self):
        offer = receiving_offer(self.fixture, self.raw)
        self.assertEqual(offer["selected"], [])
        offer["existing"]["cinderwick"][0]["id"] = "changed"
        self.assertEqual(self.fixture["towns"][0]["existing"][0]["id"], "cinderwick-b001")

    def test_negative_lost_duplicate_or_changed_retained_identity(self):
        for mode in ("lost", "duplicate", "renamed"):
            with self.subTest(mode=mode):
                def mutate(c):
                    rows = c["towns"][0]["existing"]
                    if mode == "lost":
                        rows.pop()
                    elif mode == "duplicate":
                        rows.append(copy.deepcopy(rows[0]))
                    else:
                        rows[0]["id"] = "cinderwick-b099"
                self.reject(mutate, "retained|duplicate identity")

    def test_positive_received_exact_historical_records_still_do_not_approve_placement(self):
        records = {t["id"]: copy.deepcopy(t["existing"]) for t in self.fixture["towns"]}
        self.assertEqual(check_received_existing(self.fixture, self.raw, records), {
            "historical_identity_compatible": True, "adoption_enabled": False, "placement_evidence": "missing"})

    def test_negative_real_receiving_boundary_refuses_drift_without_rewriting(self):
        for mode in ("lost", "duplicate", "changed_id", "changed_door", "extra_town"):
            with self.subTest(mode=mode):
                records = {t["id"]: copy.deepcopy(t["existing"]) for t in self.fixture["towns"]}
                rows = records["cinderwick"]
                if mode == "lost":
                    rows.pop()
                elif mode == "duplicate":
                    rows.append(copy.deepcopy(rows[0]))
                elif mode == "changed_id":
                    rows[0]["id"] = "cinderwick-b999"
                elif mode == "changed_door":
                    rows[0]["door_cells"][0] += 1
                else:
                    records["invented_town"] = []
                before = canonical(records)
                with self.assertRaisesRegex(ContractError, "baseline drift|duplicate identity|town inventory"):
                    check_received_existing(self.fixture, self.raw, records)
                self.assertEqual(canonical(records), before)

    def test_negative_lost_duplicate_or_changed_authored_addition(self):
        for mode in ("lost", "duplicate", "renamed"):
            with self.subTest(mode=mode):
                def mutate(c):
                    rows = c["towns"][0]["adoptable"]
                    if mode == "lost":
                        rows.pop()
                    elif mode == "duplicate":
                        rows.append(copy.deepcopy(rows[0]))
                    else:
                        rows[0]["id"] = "cinderwick-b999"
                self.reject(mutate, "proposed record|duplicate identity")

    def test_negative_door_street_plot_or_purpose_changed(self):
        for key, value in (("door_cells", [305, 726]), ("faces", "cinderwick-s01"),
                           ("plot_cells", [301, 717, 8, 3]), ("purpose", "invented trade")):
            with self.subTest(field=key):
                self.reject(lambda c: c["towns"][0]["adoptable"][0].__setitem__(key, value),
                            "proposed record")

    def test_negative_missing_source_bytes_are_not_a_skip(self):
        raw = dict(self.raw)
        del raw["hearthold-baseline"]
        with self.assertRaisesRegex(ContractError, "source inputs missing"):
            validate_contract(self.fixture, raw)

    def test_negative_tampered_source_bytes_even_with_unchanged_claimed_pin(self):
        raw = dict(self.raw)
        raw["current-packets"] += b"\n"
        with self.assertRaisesRegex(ContractError, "immutable blob mismatch"):
            validate_contract(self.fixture, raw)

    def test_negative_changed_commit_blob_or_source_path(self):
        for field, value in (("commit", "0" * 40), ("blob", "0" * 40), ("path", "fake.json")):
            with self.subTest(field=field):
                self.reject(lambda c: c["sources"]["cinderwick-proposal"].__setitem__(field, value),
                            "immutable input pins")

    def test_boundary_no_selection_is_valid_but_explicit_none_is_not(self):
        self.assertEqual(receiving_offer(self.fixture, self.raw, selected=[])["selected"], [])
        with self.assertRaisesRegex(ContractError, "selection is unapproved"):
            receiving_offer(self.fixture, self.raw, selected=None)

    def test_negative_any_selected_packet_refused_while_unapproved(self):
        for selected in (["cinderwick"], ["cinderwick", "cinderwick"], ["unknown"]):
            with self.subTest(selected=selected), self.assertRaisesRegex(ContractError, "unapproved"):
                receiving_offer(self.fixture, self.raw, selected=selected)

    def test_negative_changed_receiving_window_or_packet_identity(self):
        self.reject(lambda c: c["towns"][0]["producer_packet"]["terrain_box_cells"].__setitem__(0, 0),
                    "source receiving packet")
        self.reject(lambda c: c["towns"][0]["producer_packet"].__setitem__("status", "approved"),
                    "source receiving packet")

    def test_negative_implicit_or_promoted_adoption_fields(self):
        for field in OFF:
            with self.subTest(field=field):
                self.reject(lambda c: c["adoption"].pop(field), "explicitly OFF")
        self.reject(lambda c: c["adoption"].__setitem__("enabled", 0), "explicitly OFF")
        self.reject(lambda c: c["consumer"].__setitem__("selection", {"cinderwick": True}),
                    "consumer default")

    def test_interacting_valid_records_do_not_override_approval_or_foundation(self):
        for field in ("approved", "foundation_included", "live_placement"):
            with self.subTest(field=field):
                self.reject(lambda c: c["adoption"].__setitem__(field, True), "explicitly OFF")

    def test_boundary_zero_contribution_sheds_and_excluded_landmarks_survive(self):
        towns = self.fixture["towns"]
        self.assertEqual([sum(b["counts_as"] for b in t["existing"]) for t in towns], [13, 28, 3])
        self.assertEqual([sum(b["counts_as"] for b in t["adoptable"]) for t in towns], [2, 3, 3])
        self.assertEqual(len(towns[0]["adoptable"]), 4)
        self.assertTrue(all(b["counted"] for b in towns[2]["existing"] if b["counts_as"] == 0))

    def test_interacting_boatyard_open_use_cannot_erase_shed_footprints(self):
        self.reject(lambda c: c["towns"][0]["proposal_metadata"]["open_uses"].pop(), "metadata")
        self.reject(lambda c: c["towns"][0]["adoptable"].pop(), "proposed record")

    def test_negative_original_access_or_district_delta_changed(self):
        self.reject(lambda c: c["towns"][1]["existing_access"]["streets"][0].__setitem__(
            "vertices_px", [[0, 0], [8, 0]]), "access identities")
        self.reject(lambda c: c["towns"][2]["proposal_metadata"]["districts"].pop(), "metadata")

    def test_negative_empty_life_names_or_work_flags_do_not_complete_semantics(self):
        for field in ("homes", "jobs", "residents", "routines", "animals"):
            with self.subTest(field=field):
                self.reject(lambda c: c["towns"][0]["missing"][field].__setitem__("status", "complete"),
                            "inferred life")
        self.reject(lambda c: c["towns"][0]["missing"]["homes"].__setitem__("work", True),
                    "invented life")
        self.reject(lambda c: c["towns"][0]["missing"]["residents"].__setitem__(
            "source_literal", [{"name": "fisher", "work": True}]), "life source literal")

    def test_negative_missing_life_or_ground_approach_evidence_must_stay_named(self):
        self.reject(lambda c: c["towns"][0]["missing"].pop("homes"), "missing life fields")
        self.reject(lambda c: c["missing"].pop("actual_access"), "missing evidence")
        self.reject(lambda c: c["slice"]["missing"].pop("stone_circle_footprint"), "slice missing")

    def test_negative_slice_door_route_node_and_frame_must_stay_exact(self):
        self.reject(lambda c: c["slice"]["json_references"][4]["value"].__setitem__(
            "points", [[0, 0], [8, 0]]), "slice changed")
        self.reject(lambda c: c["slice"]["text_references"][-3].__setitem__(
            "verbatim", "invented ToCrossroads"), "access bindings")
        self.reject(lambda c: c["slice"]["json_references"][1].__setitem__(
            "value", [5976, 3376]), "slice changed")

    def test_interacting_regional_labels_never_renumber_runtime_identities(self):
        self.reject(lambda c: c["slice"]["json_references"][0].__setitem__("value", "town"),
                    "slice changed")
        self.reject(lambda c: c["slice"].__setitem__("status", "approved_route"), "slice approval")

    def test_negative_duplicate_json_keys_and_nonfinite_numbers(self):
        for raw in ('{"selected":[],"selected":["cinderwick"]}', '{"tier":NaN}'):
            with self.subTest(raw=raw), self.assertRaises(ContractError):
                read_json(raw)

    def test_boundary_consumer_rejects_failed_contract_without_mutation(self):
        candidate = copy.deepcopy(self.fixture)
        candidate["towns"][2]["adoptable"][0]["door_cells"][0] += 1
        before = canonical(candidate)
        with self.assertRaises(ContractError):
            receiving_offer(candidate, self.raw)
        self.assertEqual(canonical(candidate), before)


if __name__ == "__main__":
    unittest.main()
