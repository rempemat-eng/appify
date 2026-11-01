"""Subprocess controls using real temporary Git indexes and actual file bytes."""
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).with_name('godot-import-cache.py').resolve()
WORKFLOW = SCRIPT.parent.parent / '.github/workflows/godot.yml'


class ImportKeyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='MyGame cache with spaces ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / 'repository'
        self.root.mkdir()
        self.git('init', '-q')
        for name in ['game/project.godot', 'game/art with spaces.png',
                     'game/scene.tscn', '.github/workflows/godot.yml',
                     'scripts/godot-import-cache.py', 'scripts/godot-import-cache.test.py']:
            self.write(name, name.encode())
        self.git('add', '.')
        self.git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
                 'commit', '-qm', 'Initial fixture')
        self.engine = Path(self.temp.name) / 'engine with spaces'
        self.engine.write_bytes(b'engine bytes')

    def git(self, *args):
        return subprocess.check_output(['git', '-C', str(self.root), *args], stderr=subprocess.PIPE)

    def write(self, name, data):
        p = self.root / name
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)

    def run_key(self, *extra, ok=True):
        result = subprocess.run(['python3', str(SCRIPT), '--root', str(self.root),
                                 '--engine', str(self.engine), '--runner-os', 'Linux',
                                 '--runner-arch', 'X64', *extra], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0 if ok else 2, result.stderr)
        if ok:
            self.assertRegex(result.stdout, r'^godot-import-v1-[0-9a-f]{64}\n$')
        else:
            self.assertEqual(result.stdout, '')
            self.assertIn('Godot import cache:', result.stderr)
        return result.stdout

    def test_stable_across_paths_and_mtime(self):
        before = self.run_key()
        shutil.copytree(self.root, Path(self.temp.name) / 'second')
        self.root = Path(self.temp.name) / 'second'
        (self.root / 'game/scene.tscn').touch()
        self.assertEqual(before, self.run_key())

    def test_every_tracked_game_input_invalidates(self):
        before = self.run_key()
        for name in ['game/project.godot', 'game/art with spaces.png', 'game/scene.tscn']:
            with self.subTest(name=name):
                old = (self.root / name).read_bytes()
                self.write(name, old + b'changed')
                self.assertNotEqual(before, self.run_key())
                self.write(name, old)

    def test_engine_and_platform_invalidate(self):
        before = self.run_key()
        for option, value in [('--runner-os', 'macOS'), ('--runner-arch', 'ARM64')]:
            self.assertNotEqual(before, self.run_key(option, value))
        self.engine.write_bytes(b'different executable')
        self.assertNotEqual(before, self.run_key())

    def test_helpers_and_workflow_invalidate(self):
        before = self.run_key()
        for name in ['.github/workflows/godot.yml', 'scripts/godot-import-cache.py',
                     'scripts/godot-import-cache.test.py']:
            old = (self.root / name).read_bytes()
            self.write(name, old + b'change')
            self.assertNotEqual(before, self.run_key())
            self.write(name, old)

    def test_add_delete_rename_and_mode(self):
        before = self.run_key()
        self.write('game/new.gd', b'new')
        self.git('add', 'game/new.gd')
        self.assertNotEqual(before, self.run_key())
        self.git('rm', '-f', 'game/new.gd')
        self.assertEqual(before, self.run_key())
        self.git('mv', 'game/scene.tscn', 'game/new.tscn')
        renamed = self.run_key()
        self.assertNotEqual(before, renamed)
        self.git('update-index', '--chmod=+x', 'game/new.tscn')
        self.assertNotEqual(renamed, self.run_key())
        self.git('rm', '-f', 'game/new.tscn')
        self.assertNotEqual(before, self.run_key())

    def test_generated_ignored_output_does_not_invalidate(self):
        self.write('.gitignore', b'game/.godot/\ngame/reports/\n')
        before = self.run_key()
        self.write('game/.godot/imported/sprite.ctex', b'generated')
        self.write('game/reports/result.xml', b'result')
        self.assertEqual(before, self.run_key())

    def test_untracked_or_missing_source_refused(self):
        self.write('game/new source.gd', b'untracked')
        self.run_key(ok=False)
        (self.root / 'game/new source.gd').unlink()
        (self.root / 'game/scene.tscn').unlink()
        self.run_key(ok=False)

    def test_symlink_and_tracked_generated_input_refused(self):
        self.git('rm', '-f', 'game/scene.tscn')
        (self.root / 'game/scene.tscn').symlink_to(self.engine)
        self.git('add', 'game/scene.tscn')
        self.run_key(ok=False)
        self.git('rm', '-f', 'game/scene.tscn')
        self.write('game/.godot/imported/x', b'output')
        self.git('add', '-f', 'game/.godot/imported/x')
        self.run_key(ok=False)

    def test_missing_project_engine_or_helper_refused(self):
        self.git('rm', '-f', 'game/project.godot')
        self.run_key(ok=False)
        self.write('game/project.godot', b'project')
        self.git('add', 'game/project.godot')
        self.engine.unlink()
        self.run_key(ok=False)
        self.engine.write_bytes(b'engine')
        (self.root / 'scripts/godot-import-cache.py').unlink()
        self.run_key(ok=False)

    def test_irrelevant_docs_do_not_invalidate(self):
        before = self.run_key()
        self.write('docs/note.md', b'documentation')
        self.git('add', 'docs/note.md')
        self.assertEqual(before, self.run_key())

    def test_non_repository_refused(self):
        shutil.rmtree(self.root / '.git')
        self.run_key(ok=False)

    def test_workflow_preserves_full_check_and_exact_restore(self):
        text = WORKFLOW.read_text()
        self.assertEqual(text.count('run: bash game/tools/check.sh'), 1)
        restore = text.index('uses: actions/cache/restore@')
        check = text.index('run: bash game/tools/check.sh')
        save = text.index('uses: actions/cache/save@')
        self.assertLess(restore, check)
        self.assertLess(check, save)
        self.assertNotIn('restore-keys:', text)
        self.assertEqual(text.count('path: game/.godot/imported'), 2)
        self.assertIn("if: success() && steps.imports.outputs.cache-hit != 'true'", text)
        self.assertNotIn('continue-on-error', text)
        check_step = text[text.rfind('      - name:', 0, check):save]
        self.assertNotIn('if:', check_step.split('      - name: Save')[0])


if __name__ == '__main__':
    unittest.main()
