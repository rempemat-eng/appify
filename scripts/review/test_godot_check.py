"""Exercise check.sh with a fake executable; never start Godot or import a project."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest


CHECK = Path(__file__).resolve().parents[2] / "game/tools/check.sh"
ROOT_KEYS = ("HOME", "XDG_DATA_HOME", "XDG_CONFIG_HOME", "XDG_CACHE_HOME", "TMPDIR")
FAKE = r'''
import hashlib, json, os, pathlib, stat, sys
p = pathlib.Path(sys.argv[0]).resolve()
a = sys.argv[1:]
phase = "version" if "--version" in a else "import" if "--import" in a else "main" if "--quit-after" in a else "tests"
keys = ("HOME", "XDG_DATA_HOME", "XDG_CONFIG_HOME", "XDG_CACHE_HOME", "TMPDIR")
roots = {k: os.environ.get(k) for k in keys}
record = {"phase": phase, "args": a, "executable": str(p),
          "sha256": hashlib.sha256(p.read_bytes()).hexdigest(), "roots": roots,
          "root_modes": {k: stat.S_IMODE(pathlib.Path(v).stat().st_mode) if v and pathlib.Path(v).is_dir() else None for k, v in roots.items()},
          "siblings": sorted(q.name for q in p.parent.iterdir())}
with open(os.environ["FAKE_RECORDS"], "a") as f:
    f.write(json.dumps(record) + "\n")
# Simulate the observed portable-mode override of configured XDG roots.
if (p.parent / "_sc_").exists():
    (p.parent / "editor_data/settings.cfg").write_text("portable settings touched")
mode = os.environ.get("FAKE_MODE", "")
if phase == "version":
    print("4.6.0.stable" if mode == "wrong_version" else "4.7.2.stable.fake")
    sys.exit(9 if mode == "version_exit" else 0)
if mode == phase + "_fatal":
    print("SCRIPT ERROR: injected", flush=True)
if mode == "cannot_open" and phase == "tests":
    print("Cannot open file injected", flush=True)
if mode == "audio_noise":
    print("ERROR: ALSA: cannot initialize audio", flush=True)
print("Overall PASSED", flush=True)
sys.exit(7 if mode == phase + "_exit" else 0)
'''


class GodotCheck(unittest.TestCase):
    def exercise(self, mode="", *, lookup="absolute", fail_tool=None, fail_at=1, frames=None):
        with tempfile.TemporaryDirectory(prefix="mygame checker controls ") as raw:
            root = Path(raw)
            project = root / "small project"
            tools = project / "game/tools"
            tools.mkdir(parents=True)
            check = tools / "check.sh"
            check.write_bytes(CHECK.read_bytes())
            original = root / "original portable engine"
            original.mkdir()
            binary = original / "godot"
            binary.write_text(f"#!{sys.executable}\n" + FAKE)
            binary.chmod(0o755)
            (original / "_sc_").write_text("keep marker")
            (original / "editor_data").mkdir()
            (original / "editor_data/settings.cfg").write_text("keep original settings")
            (original / "editor_data/player.json").write_text("keep player profile")

            def snapshot():
                return {str(p.relative_to(original)): (stat.S_IMODE(p.stat().st_mode), p.read_bytes() if p.is_file() else None)
                        for p in original.rglob("*")}

            before = snapshot()
            expected_hash = hashlib.sha256(binary.read_bytes()).hexdigest()
            temp = root / "caller temp"
            temp.mkdir()
            home = root / "caller home"
            home.mkdir()
            records = root / "calls.jsonl"
            shim = root / "command shims"
            shim.mkdir()
            if fail_tool:
                stub = shim / fail_tool
                counter = shlex.quote(str(root / "injected command count"))
                real_command = shlex.quote(shutil.which(fail_tool))
                stub.write_text(
                    "#!/bin/sh\n"
                    f"count=$(cat {counter} 2>/dev/null || echo 0)\n"
                    "count=$((count + 1))\n"
                    f"echo \"$count\" > {counter}\n"
                    f"[ \"$count\" -ne {fail_at} ] || exit 73\n"
                    f"exec {real_command} \"$@\"\n"
                )
                stub.chmod(0o755)
            env = os.environ.copy()
            env.update(FAKE_RECORDS=str(records), FAKE_MODE=mode, TMPDIR=str(temp), HOME=str(home),
                       XDG_DATA_HOME=str(home / "data"), XDG_CONFIG_HOME=str(home / "config"), XDG_CACHE_HOME=str(home / "cache"),
                       PATH=os.pathsep.join((str(shim), str(original), env.get("PATH", ""))))
            if lookup == "default":
                env.pop("GODOT", None)
            elif lookup == "symlink":
                link = root / "engine link"
                link.symlink_to(binary)
                env["GODOT"] = str(link)
            elif lookup == "missing":
                env["GODOT"] = str(root / "missing engine")
            else:
                env["GODOT"] = str(binary)
            if frames is not None:
                env["FRAMES"] = str(frames)
            else:
                env.pop("FRAMES", None)
            result = subprocess.run(["bash", str(check)], env=env, text=True, capture_output=True, timeout=15)
            calls = [json.loads(s) for s in records.read_text().splitlines()] if records.exists() else []
            observation = dict(result=result, calls=calls, before=before, after=snapshot(),
                               binary=str(binary), hash=expected_hash, temp=str(temp), home=str(home),
                               leftovers=list(temp.iterdir()), project=str(project / "game"))
            return observation

    def test_copies_only_executable_before_version_and_preserves_portable_source(self):
        o = self.exercise()
        self.assertEqual(o["result"].returncode, 0, o["result"].stderr)
        self.assertEqual([x["phase"] for x in o["calls"]], ["version", "import", "main", "tests"])
        self.assertEqual(o["before"], o["after"])
        for call in o["calls"]:
            self.assertNotEqual(call["executable"], o["binary"])
            self.assertEqual(call["sha256"], o["hash"])
            self.assertNotIn("_sc_", call["siblings"])
            self.assertNotIn("editor_data", call["siblings"])
        self.assertEqual(o["leftovers"], [])

    def test_all_children_have_fresh_existing_private_roots(self):
        o = self.exercise()
        for key in ROOT_KEYS:
            values = [c["roots"][key] for c in o["calls"]]
            self.assertEqual(len(set(values)), 4, (key, values))
            for call in o["calls"]:
                value = call["roots"][key]
                self.assertTrue(value and Path(value).is_relative_to(o["temp"]), (key, value))
                self.assertIsNotNone(call["root_modes"][key])
                self.assertEqual(call["root_modes"][key] & 0o077, 0)

    def test_default_command_resolution(self):
        o = self.exercise(lookup="default")
        self.assertEqual(o["result"].returncode, 0)
        self.assertTrue(o["calls"])
        self.assertTrue(all(c["executable"] != o["binary"] for c in o["calls"]))

    def test_symlink_and_space_paths_preserve_executable_bytes(self):
        o = self.exercise(lookup="symlink")
        self.assertEqual(o["result"].returncode, 0, o["result"].stderr)
        self.assertTrue(all(c["sha256"] == o["hash"] for c in o["calls"]))
        self.assertEqual(o["before"], o["after"])

    def test_missing_binary_keeps_diagnostic(self):
        o = self.exercise(lookup="missing")
        self.assertEqual(o["result"].returncode, 2)
        self.assertIn("no Godot binary", o["result"].stderr)
        self.assertEqual(o["calls"], [])

    def test_wrong_version_stops_before_project_and_cleans_up(self):
        o = self.exercise("wrong_version")
        self.assertEqual(o["result"].returncode, 2)
        self.assertIn("expected Godot 4.7.2", o["result"].stderr)
        self.assertEqual([c["phase"] for c in o["calls"]], ["version"])
        self.assertEqual(o["leftovers"], [])

    def test_nonzero_version_stops_before_project(self):
        o = self.exercise("version_exit")
        self.assertEqual(o["result"].returncode, 2)
        self.assertEqual([c["phase"] for c in o["calls"]], ["version"])
        self.assertEqual(o["leftovers"], [])

    def test_copy_failure_is_closed_before_any_engine_call(self):
        o = self.exercise(fail_tool="cp")
        self.assertEqual(o["result"].returncode, 2)
        self.assertEqual(o["calls"], [])
        self.assertEqual(o["leftovers"], [])

    def test_compare_failure_is_closed_before_any_engine_call(self):
        o = self.exercise(fail_tool="cmp")
        self.assertEqual(o["result"].returncode, 2)
        self.assertEqual(o["calls"], [])
        self.assertEqual(o["leftovers"], [])

    def test_root_setup_failure_is_closed_before_any_engine_call(self):
        # Initial runtime, version roots, and import roots are separate failure
        # boundaries. The last must stop after version, before any project call.
        for tool in ("mkdir", "mktemp"):
            for occurrence in (1, 2, 3):
                with self.subTest(tool=tool, occurrence=occurrence):
                    o = self.exercise(fail_tool=tool, fail_at=occurrence)
                    self.assertEqual(o["result"].returncode, 2)
                    self.assertEqual(
                        [c["phase"] for c in o["calls"]],
                        ["version"] if occurrence == 3 else [],
                    )
                    self.assertEqual(o["before"], o["after"])
                    self.assertEqual(o["leftovers"], [])

    def test_original_import_main_and_gdunit_arguments_preserved(self):
        o = self.exercise()
        version, imp, main, tests = [c["args"] for c in o["calls"]]
        self.assertEqual(version, ["--version"])
        self.assertEqual(imp, ["--headless", "--path", o["project"], "--import"])
        self.assertEqual(main, ["--headless", "--audio-driver", "Dummy", "--path", o["project"], "--quit-after", "300", "--", "--fresh"])
        self.assertEqual(tests, ["--headless", "--audio-driver", "Dummy", "--path", o["project"], "-s", "res://addons/gdUnit4/bin/GdUnitCmdTool.gd", "--ignoreHeadlessMode", "-a", "res://test", "-rd", "reports", "-c"])

    def test_frame_override_is_preserved(self):
        o = self.exercise(frames=19)
        main = next(c["args"] for c in o["calls"] if c["phase"] == "main")
        self.assertEqual(main[main.index("--quit-after") + 1], "19")

    def test_each_phase_nonzero_exit_fails_without_suppressing_later_checks(self):
        for phase in ("import", "main", "tests"):
            with self.subTest(phase=phase):
                o = self.exercise(phase + "_exit")
                self.assertEqual(o["result"].returncode, 1)
                self.assertIn("FAIL", o["result"].stdout)
                self.assertEqual(len(o["calls"]), 4)
                self.assertEqual(o["leftovers"], [])

    def test_zero_exit_fatal_logs_fail_in_each_phase_and_cannot_open(self):
        for mode in ("import_fatal", "main_fatal", "tests_fatal", "cannot_open"):
            with self.subTest(mode=mode):
                o = self.exercise(mode)
                self.assertEqual(o["result"].returncode, 1)
                self.assertIn("check:godot FAILED", o["result"].stdout)
                self.assertEqual(o["leftovers"], [])

    def test_audio_noise_is_still_excluded(self):
        o = self.exercise("audio_noise")
        self.assertEqual(o["result"].returncode, 0)
        self.assertIn("check:godot passed", o["result"].stdout)


if __name__ == "__main__":
    unittest.main()
