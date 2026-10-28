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
                self.assertEqual(check(packet, source, source_pin=pin),
                    ["coverage: explicit use contract required for nonlegacy source"])
                self.assertIn("landmarks", source)
                self.assertTrue(all("counts_as" in b for b in source["buildings"]))
                result = self.cli(json.dumps(packet).encode(), raw, pin)
                self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
                self.assertIn("explicit use contract required", result.stdout)

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


class ExplicitUses(unittest.TestCase):
    """Use facts are caller-supplied authoring inputs, never guessed from labels."""
    @classmethod
    def setUpClass(cls):
        TownSources.setUpClass()
        cls.raw, cls.pin, cls.source, cls.packet = TownSources.examples['canalside']

    def contract(self):
        # Audit340 explicitly leaves these two workshop residences unresolved.
        unknown = {'canalside-b003', 'canalside-b009'}
        return {'schema': 'mygame.settlement_use/1',
                'source': {'commit': self.pin.commit, 'blob': self.pin.blob, 'path': self.pin.path},
                'buildings': [{'id': b['id'], 'home': None if b['id'] in unknown else True,
                    'work': True if b['id'] in unknown else None,
                    'evidence': [{'field': 'occupants', 'text': b['occupants']}]} for b in self.source['buildings']],
                'workplaces': [{'home': b['id'], 'workplace': None}
                    for b in self.source['buildings'] if b['id'] not in unknown]}

    def homes_packet(self, contract):
        p = copy.deepcopy(self.packet)
        homes = {b['id'] for b in contract['buildings'] if b['home'] is True}
        p['residents'] = [r for r in p['residents'] if r['home'] in homes]
        ids = {r['id'] for r in p['residents']}
        p['routines'] = [r for r in p['routines'] if r['resident'] in ids]
        return p

    def test_occupational_unknowns_never_pass_or_become_homes(self):
        c = self.contract()
        p = self.homes_packet(c)
        errors = check(p, self.source, source_pin=self.pin, use_contract=c)
        self.assertEqual(len(errors), 2, errors)
        self.assertTrue(all('incomplete: residence unknown' in e for e in errors))
        self.assertTrue(check(self.packet, self.source, source_pin=self.pin, use_contract=c))
        self.assertEqual(len(p['residents']), 8)

    def test_nonlegacy_packet_cannot_select_policy_or_legacy_mode(self):
        p = copy.deepcopy(self.packet)
        p['life_planning']['use_contract'] = self.contract()
        self.assertIn('coverage: explicit use contract required for nonlegacy source',
                      check(p, self.source, source_pin=self.pin))

    def test_mixed_use_and_separate_authored_workplace_bindings(self):
        # Synthetic authoring facts exercise the typed interface, not a new real town packet.
        c = self.contract()
        for b in c['buildings']:
            if b['home'] is None:
                b['home'] = False
        p = self.homes_packet(c)
        h = p['residents'][0]['home']
        next(b for b in c['buildings'] if b['id'] == h)['work'] = True
        next(b for b in c['workplaces'] if b['home'] == h)['workplace'] = h
        p['residents'][0].update(workplace=h, workplace_status='source_explicit')
        self.assertEqual(check(p, self.source, source_pin=self.pin, use_contract=c), [])
        p['residents'][0]['workplace'] = 'canalside-b003'
        self.assertTrue(check(p, self.source, source_pin=self.pin, use_contract=c))
        next(b for b in c['workplaces'] if b['home'] == h)['workplace'] = 'canalside-b003'
        self.assertEqual(check(p, self.source, source_pin=self.pin, use_contract=c), [])
        p['residents'][0]['workplace_status'] = 'approved'
        self.assertTrue(check(p, self.source, source_pin=self.pin, use_contract=c))

    def test_malformed_or_wrong_source_contract_is_invalid(self):
        mutations = [lambda c: c.update(schema='wrong'),
            lambda c: c['source'].update(blob='0' * 40),
            lambda c: c['buildings'].pop(),
            lambda c: c['buildings'].append(copy.deepcopy(c['buildings'][0])),
            lambda c: c['buildings'][0].update(home=1),
            lambda c: c['buildings'][0].update(work='yes'),
            lambda c: c['buildings'][0]['evidence'][0].update(text='invented'),
            lambda c: c['buildings'][0]['evidence'][0].update(field='type'),
            lambda c: c['workplaces'].pop(),
            lambda c: c['workplaces'].append(copy.deepcopy(c['workplaces'][0])),
            lambda c: c['workplaces'][0].update(workplace='missing'),
            lambda c: c.update(extra='silently ignored')]
        for mutation in mutations:
            c = self.contract(); mutation(c)
            with self.subTest(contract=c), self.assertRaises(ValueError):
                check(self.packet, self.source, source_pin=self.pin, use_contract=c)

    def test_actual_explicit_shop_text_allows_mixed_reference(self):
        from scripts.settlement_life.check import SourcePin
        path = 'docs/vision/research/blockout/towns/fernhollow.json'
        raw = subprocess.check_output(['git', 'show', f'{CURRENT_COMMIT}:{path}'], cwd=ROOT)
        source = json.loads(raw)
        blob = subprocess.check_output(['git', 'rev-parse', f'{CURRENT_COMMIT}:{path}'], cwd=ROOT, text=True).strip()
        pin = SourcePin(CURRENT_COMMIT, blob, path)
        b = next(b for b in source['buildings'] if b['id'] == 'fernhollow-b002')
        self.assertEqual(b['occupants'], 'the shopkeeper, living above')
        c = {'schema': 'mygame.settlement_use/1',
             'source': {'commit': pin.commit, 'blob': pin.blob, 'path': pin.path},
             'buildings': [{'id': x['id'], 'home': True if x == b else None,
                 'work': True if x == b else None,
                 'evidence': [{'field': 'occupants', 'text': x['occupants']}]} for x in source['buildings']],
             'workplaces': [{'home': b['id'], 'workplace': b['id']}]}
        p = copy.deepcopy(source);p['life_planning'] = copy.deepcopy(self.packet['life_planning'])
        p['life_planning'].update(source_commit=pin.commit, source_blob=pin.blob, source_path=pin.path)
        resident = copy.deepcopy(self.packet['residents'][0]);resident.update(id='mixed-fixture', home=b['id'],
            district=b['district'], role=b['occupants'], source_occupants=b['occupants'],
            workplace=b['id'], workplace_status='source_explicit')
        p['residents'] = [resident]
        p['routines'] = [{'resident': resident['id'], 'time_of_day': phase,
             'place': b['faces'] if phase == 'day' else b['id'], 'status': 'proposal', 'timing': 'placeholder'}
             for phase in ('morning', 'day', 'evening', 'night')]
        findings = check(p, source, source_pin=pin, use_contract=c)
        self.assertEqual(len(findings), len(source['buildings']) - 1, findings)
        self.assertTrue(all('incomplete: residence unknown' in e for e in findings))

    def test_empty_occupants_unknown_cannot_silently_be_excluded(self):
        for occupants in ('', None):
            for work in (True, None):
                c = self.contract();source = copy.deepcopy(self.source)
                for b in source['buildings']:
                    if b['id'] == 'canalside-b003':
                        if occupants is None:b.pop('occupants')
                        else:b['occupants'] = occupants
                row = next(b for b in c['buildings'] if b['id'] == 'canalside-b003')
                row.update(work=work, evidence=[{'field': 'purpose', 'text':
                    next(b['purpose'] for b in source['buildings'] if b['id'] == row['id'])}])
                p = self.homes_packet(c);p['buildings'] = copy.deepcopy(source['buildings'])
                findings = check(p, source, source_pin=self.pin, use_contract=c)
                self.assertIn('incomplete: residence unknown for canalside-b003', findings)

    def test_cli_independent_pins_complete_incomplete_invalid_and_byte_preservation(self):
        import contextlib
        import io
        from unittest.mock import patch
        import scripts.settlement_life.check as checker
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            def git(*args):
                return subprocess.check_output(['git', *args], cwd=root, text=True).strip()
            def commit(path, raw):
                file = root / path;file.parent.mkdir(parents=True, exist_ok=True);file.write_bytes(raw)
                git('add', path)
                git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
                    'commit', '--allow-empty', '-qm', 'test input')
                return git('rev-parse', 'HEAD'), git('rev-parse', f'HEAD:{path}')
            git('init', '-q')
            source_path = self.pin.path
            source_commit, source_blob = commit(source_path, self.raw)
            c = self.contract()
            c['source'].update(commit=source_commit, blob=source_blob)
            # Synthetic explicit non-residential author input, not a real Canalside decision.
            for b in c['buildings']:
                if b['home'] is None:b['home'] = False
            p = self.homes_packet(c)
            p['life_planning'].update(source_commit=source_commit, source_blob=source_blob)
            plan = root / 'packet.json'
            use_path = 'authoring/use.json'
            def run(contract, packet, expected, extra=None, mutate_bytes=False, raw_override=None):
                raw = json.dumps(contract).encode() if raw_override is None else raw_override
                uc, ub = commit(use_path, raw)
                if mutate_bytes:(root / use_path).write_bytes(raw + b' ')
                plan.write_text(json.dumps(packet))
                files = [root / source_path, root / use_path, plan]
                before = [f.read_bytes() for f in files]
                args = ['check', str(plan), '--source', str(root / source_path),
                    '--source-commit', source_commit, '--source-blob', source_blob,
                    '--source-path', source_path, '--uses', str(root / use_path),
                    '--uses-commit', uc, '--uses-blob', ub, '--uses-path', use_path]
                if extra is not None:args = args[:-8] + extra
                out = io.StringIO()
                with patch.object(checker, 'ROOT', root), patch.object(sys, 'argv', args), contextlib.redirect_stdout(out):
                    rc = checker.main()
                self.assertEqual(rc, expected, out.getvalue())
                self.assertEqual([f.read_bytes() for f in files], before)
                return out.getvalue()
            self.assertIn('PASS', run(c, p, 0))
            bad = copy.deepcopy(p);bad['residents'][0]['workplace'] = 'canalside-b003'
            run(c, bad, 1)
            unknown = copy.deepcopy(c)
            next(b for b in unknown['buildings'] if b['id'] == 'canalside-b003')['home'] = None
            self.assertIn('incomplete: residence unknown', run(unknown, p, 1))
            run(c, p, 2, mutate_bytes=True)
            wrong = copy.deepcopy(c);wrong['source']['blob'] = '0' * 40
            run(wrong, p, 2)
            for malformed in (b'{"schema":1,"schema":1}', b'[]', b'{"schema":NaN}', b'{'):
                run(c, p, 2, raw_override=malformed)
            run(c, p, 2, extra=['--uses', str(root / use_path)])
            claims = copy.deepcopy(p);claims['life_planning']['use_contract'] = c
            self.assertIn('explicit use contract required', run(c, claims, 1, extra=[]))

    def test_use_pin_paths_and_shas_refuse_traversal_and_malformed_values(self):
        from scripts.settlement_life.check import UsePin
        for path in ('../use.json', '/use.json', 'a/../use.json', 'a//use.json', 'a\\use.json', '.hidden/use.json', 'use.md'):
            with self.subTest(path=path), self.assertRaises(ValueError):
                UsePin('a' * 40, 'b' * 40, path)
        for sha in ('a' * 39, 'A' * 40, 3, None):
            with self.subTest(sha=sha), self.assertRaises(ValueError):
                UsePin(sha, 'b' * 40, 'authoring/use.json')
