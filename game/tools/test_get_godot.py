"""Exercise the Godot installer with real archive verification and extraction.

The getter runs unchanged except for its SHA-512 pin in a temporary copy. That
copy trusts a small, deterministic fixture archive; no test downloads an engine.
"""

import hashlib
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
import tempfile
import unittest
import zipfile


VERSION = "4.7.2"
BINARY_NAME = f"Godot_v{VERSION}-stable_linux.x86_64"
ARCHIVE_NAME = f"{BINARY_NAME}.zip"
DOWNLOAD_URL = (
    "https://github.com/godotengine/godot/releases/download/"
    f"{VERSION}-stable/{ARCHIVE_NAME}"
)
PRODUCTION_SHA512 = (
    "9aa00f7a605200940bce3027a567b782f49bd8e940dd06ae9e987bd65aee1b1467edd"
    "56ed84fcdcbdd44354bf613bdbb4e5d2913e925850368e150c59ed54c65"
)
BINARY_BYTES = b"#!/bin/sh\nprintf 'fixture Godot 4.7.2\\n'\n"
GETTER = Path(__file__).with_name("get_godot.sh")
WORKFLOW = GETTER.parents[2] / ".github" / "workflows" / "godot.yml"


class GetGodotTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="mygame-godot-test-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.binary_dir = self.root / "binary dir"
        self.archive_dir = self.root / "archive cache"
        self.temp_dir = self.root / "temporary files"
        self.temp_dir.mkdir()
        self.fixture = self.root / "fixture.zip"
        self.log = self.root / "curl calls.jsonl"
        self.script = self.root / "get godot.sh"
        self.stub_dir = self.root / "stub tools"
        self.stub_dir.mkdir()
        self.write_archive({BINARY_NAME: BINARY_BYTES})
        self.write_getter()
        curl = self.stub_dir / "curl"
        curl.write_text(
            f"#!{sys.executable}\n"
            "import json, os, pathlib, sys\n"
            "args = sys.argv[1:]\n"
            "if len(args) != 4 or args[:2] != ['-fsSL', '-o']:\n"
            "    raise SystemExit('unexpected curl arguments: ' + repr(args))\n"
            "with open(os.environ['GETTER_CURL_LOG'], 'a') as log:\n"
            "    log.write(json.dumps({'output': args[2], 'url': args[3]}) + '\\n')\n"
            "payload = pathlib.Path(os.environ['GETTER_FIXTURE']).read_bytes()\n"
            "mode = os.environ.get('GETTER_CURL_MODE', 'success')\n"
            "if mode == 'failure':\n"
            "    raise SystemExit(22)\n"
            "if mode == 'partial':\n"
            "    pathlib.Path(args[2]).write_bytes(payload[:19])\n"
            "    raise SystemExit(22)\n"
            "if mode == 'corrupt':\n"
            "    payload = b'not the pinned archive'\n"
            "pathlib.Path(args[2]).write_bytes(payload)\n",
            encoding="utf-8",
        )
        curl.chmod(0o755)

    @property
    def binary(self):
        return self.binary_dir / BINARY_NAME

    @property
    def archive(self):
        return self.archive_dir / ARCHIVE_NAME

    def write_archive(self, entries):
        with zipfile.ZipFile(self.fixture, "w", zipfile.ZIP_STORED) as archive:
            for name, content in entries.items():
                info = zipfile.ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0))
                info.create_system = 3
                info.external_attr = (stat.S_IFREG | 0o755) << 16
                archive.writestr(info, content)

    def write_getter(self):
        source = GETTER.read_text(encoding="utf-8")
        pin = re.search(r"^SHA512=([0-9a-f]{128})$", source, re.MULTILINE)
        self.assertIsNotNone(pin, "getter must retain its explicit SHA-512 pin")
        self.assertEqual(pin.group(1), PRODUCTION_SHA512)
        digest = hashlib.sha512(self.fixture.read_bytes()).hexdigest()
        source, count = re.subn(
            r"^SHA512=[0-9a-f]{128}$", f"SHA512={digest}", source, flags=re.MULTILINE
        )
        self.assertEqual(count, 1)
        self.script.write_text(source, encoding="utf-8")

    def calls(self):
        if not self.log.exists():
            return []
        rows = [json.loads(line) for line in self.log.read_text().splitlines()]
        for row in rows:
            self.assertEqual(row["url"], DOWNLOAD_URL)
        return rows

    def environment(self, mode="success"):
        env = dict(os.environ)
        env.update(
            PATH=str(self.stub_dir) + os.pathsep + env.get("PATH", ""),
            TMPDIR=str(self.temp_dir),
            GETTER_CURL_LOG=str(self.log),
            GETTER_FIXTURE=str(self.fixture),
            GETTER_CURL_MODE=mode,
        )
        return env

    def run_getter(self, mode="success", single_argument=False):
        args = ["bash", str(self.script), str(self.binary_dir)]
        if not single_argument:
            args.append(str(self.archive_dir))
        return subprocess.run(
            args, env=self.environment(mode), text=True, capture_output=True, timeout=15
        )

    def assert_success(self, result):
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, str(self.binary) + "\n")
        self.assertEqual(self.binary.read_bytes(), BINARY_BYTES)
        self.assertTrue(os.access(self.binary, os.X_OK))
        self.assertTrue((self.binary_dir / "_sc_").is_file())
        self.assertEqual(list(self.temp_dir.iterdir()), [])

    def assert_failure(self, result):
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "", "a failed getter must not publish a binary path")
        self.assertEqual(list(self.temp_dir.iterdir()), [])

    def assert_empty_install(self):
        for directory in (self.binary_dir, self.archive_dir):
            if directory.exists():
                self.assertEqual(list(directory.iterdir()), [], f"residue in {directory}")

    def prime_cache(self):
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        self.archive.write_bytes(self.fixture.read_bytes())

    def test_cold_then_warm_reuses_verified_archive(self):
        self.assert_success(self.run_getter())
        archive_bytes = self.archive.read_bytes()
        binary_bytes = self.binary.read_bytes()
        self.assertEqual(archive_bytes, self.fixture.read_bytes())
        self.assertEqual(len(self.calls()), 1)
        self.assert_success(self.run_getter())
        self.assertEqual(len(self.calls()), 1, "warm installs must not download again")
        self.assertEqual(self.archive.read_bytes(), archive_bytes)
        self.assertEqual(self.binary.read_bytes(), binary_bytes)
        self.assertEqual(
            sorted(path.name for path in self.archive_dir.iterdir()), [ARCHIVE_NAME]
        )
        self.assertEqual(
            sorted(path.name for path in self.binary_dir.iterdir()), [BINARY_NAME, "_sc_"]
        )

    def test_warm_install_replaces_tampered_executable(self):
        self.assert_success(self.run_getter())
        self.binary.write_bytes(b"tampered executable, still marked executable")
        self.binary.chmod(0o755)
        (self.binary_dir / "_sc_").unlink()
        self.assert_success(self.run_getter())
        self.assertEqual(len(self.calls()), 1)

    def test_existing_executable_without_archive_still_requires_verified_download(self):
        self.binary_dir.mkdir()
        self.binary.write_bytes(b"unverified existing executable")
        self.binary.chmod(0o755)
        self.assert_failure(self.run_getter(mode="partial"))
        self.assertEqual(self.binary.read_bytes(), b"unverified existing executable")
        self.assertEqual(list(self.binary_dir.iterdir()), [self.binary])
        self.assertEqual(list(self.archive_dir.iterdir()), [])
        self.assert_success(self.run_getter())
        self.assertEqual(len(self.calls()), 2)

    def test_corrupt_cached_archive_refuses_even_existing_executable(self):
        self.assert_success(self.run_getter())
        self.archive.write_bytes(b"corrupted cached archive")
        previous_binary = self.binary.read_bytes()
        self.assert_failure(self.run_getter())
        self.assertEqual(self.binary.read_bytes(), previous_binary)
        self.assertEqual(self.archive.read_bytes(), b"corrupted cached archive")
        self.assertEqual(len(self.calls()), 1, "corrupt hits must fail closed")
        self.assertEqual(
            sorted(path.name for path in self.archive_dir.iterdir()), [ARCHIVE_NAME]
        )

    def test_failed_download_cleans_temporary_files_and_retry_succeeds(self):
        self.assert_failure(self.run_getter(mode="failure"))
        self.assert_empty_install()
        self.assertEqual(len(self.calls()), 1)
        self.assert_success(self.run_getter())
        self.assertEqual(len(self.calls()), 2)

    def test_partial_failed_download_is_not_published_and_retry_succeeds(self):
        self.assert_failure(self.run_getter(mode="partial"))
        self.assert_empty_install()
        self.assertEqual(len(self.calls()), 1)
        self.assert_success(self.run_getter())
        self.assertEqual(len(self.calls()), 2)

    def test_successful_download_with_bad_digest_is_not_published(self):
        self.assert_failure(self.run_getter(mode="corrupt"))
        self.assert_empty_install()
        self.assertEqual(len(self.calls()), 1)
        self.assert_success(self.run_getter())
        self.assertEqual(len(self.calls()), 2)

    def test_verified_non_zip_archive_cleans_extraction_temporary_files(self):
        self.fixture.write_bytes(b"trusted fixture bytes that are not a zip archive")
        self.write_getter()
        self.prime_cache()
        self.assert_failure(self.run_getter())
        self.assertFalse(self.binary.exists())
        if self.binary_dir.exists():
            self.assertEqual(list(self.binary_dir.iterdir()), [])
        self.assertEqual(list(self.archive_dir.iterdir()), [self.archive])
        self.assertEqual(self.calls(), [])

    def test_verified_archive_missing_expected_binary_is_refused(self):
        self.write_archive({"different-binary": b"wrong archive member"})
        self.write_getter()
        self.prime_cache()
        self.assert_failure(self.run_getter())
        self.assertFalse(self.binary.exists())
        if self.binary_dir.exists():
            self.assertEqual(list(self.binary_dir.iterdir()), [])
        self.assertFalse((self.root / "different-binary").exists())
        self.assertEqual(self.calls(), [])

    def test_failed_extraction_preserves_preexisting_executable(self):
        self.fixture.write_bytes(b"trusted but malformed zip fixture")
        self.write_getter()
        self.prime_cache()
        self.binary_dir.mkdir()
        self.binary.write_bytes(b"old installed binary")
        self.binary.chmod(0o755)
        self.assert_failure(self.run_getter())
        self.assertEqual(self.binary.read_bytes(), b"old installed binary")
        self.assertEqual(list(self.binary_dir.iterdir()), [self.binary])
        self.assertEqual(self.calls(), [])

    def test_one_argument_keeps_archive_beside_binary_and_reuses_it(self):
        self.assert_success(self.run_getter(single_argument=True))
        archive = self.binary_dir / ARCHIVE_NAME
        self.assertEqual(archive.read_bytes(), self.fixture.read_bytes())
        self.assertFalse(self.archive_dir.exists())
        self.assert_success(self.run_getter(single_argument=True))
        self.assertEqual(len(self.calls()), 1)
        self.assertEqual(
            sorted(path.name for path in self.binary_dir.iterdir()),
            [BINARY_NAME, ARCHIVE_NAME, "_sc_"],
        )

    def test_actual_workflow_propagates_getter_failure_before_publishing_environment(self):
        # Execute the real workflow's installer step in a disposable tiny checkout.
        # In particular, echo "GODOT=$(...)" would mask a failed substitution.
        lines = WORKFLOW.read_text(encoding="utf-8").splitlines()
        start = next(
            i for i, line in enumerate(lines) if "- name: Get the pinned Godot" in line
        )
        self.assertEqual(lines[start + 1].strip(), "run: |")
        body = []
        for line in lines[start + 2 :]:
            if line.strip() and not line.startswith("          "):
                break
            body.append(line[10:])
        command = "\n".join(body)
        self.assertTrue(command.strip())
        copied_getter = self.root / "game" / "tools" / "get_godot.sh"
        copied_getter.parent.mkdir(parents=True)
        copied_getter.write_bytes(self.script.read_bytes())
        runner_temp = self.root / "runner temp"
        github_env = self.root / "github environment"

        def run_step(mode):
            env = self.environment(mode)
            env.update(RUNNER_TEMP=str(runner_temp), GITHUB_ENV=str(github_env))
            return subprocess.run(
                ["bash", "--noprofile", "--norc", "-e", "-o", "pipefail", "-c", command],
                cwd=self.root,
                env=env,
                text=True,
                capture_output=True,
                timeout=15,
            )

        result = run_step("partial")
        self.assert_failure(result)
        self.assertFalse(github_env.exists(), "failed steps must not export GODOT")
        self.assertEqual(list((runner_temp / "godot-archives").iterdir()), [])
        self.assertEqual(list((runner_temp / "godot").iterdir()), [])
        result = run_step("success")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "")
        binary = runner_temp / "godot" / BINARY_NAME
        self.assertEqual(github_env.read_text(), f"GODOT={binary}\n")
        self.assertEqual(binary.read_bytes(), BINARY_BYTES)
        self.assertTrue(os.access(binary, os.X_OK))
        self.assertTrue((binary.parent / "_sc_").is_file())
        self.assertEqual(len(self.calls()), 2)


if __name__ == "__main__":
    unittest.main()
