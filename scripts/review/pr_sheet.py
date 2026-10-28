"""Bundle pinned Git changes with the existing asset/scene detector evidence.

This is an offline review aid. A PR label is descriptive; base/head Git objects
are the provenance. Detector passes never constitute Matt's art approval.
"""
from __future__ import annotations

import argparse
import hashlib
import html
import json
import math
import os
from pathlib import Path
import re
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from urllib.parse import quote

from PIL import Image


REPO = Path(__file__).resolve().parents[2]
IMAGE_SUFFIXES = {'.png', '.jpg', '.jpeg', '.gif', '.webp', '.svg', '.bmp', '.aseprite'}
# These are repository namespaces, not guesses from a filename containing "test".
# A fixture moved into production loses the exemption; either side of a rename
# can still require production evidence.
TEST_FIXTURE_ROOTS = ('game/test/fixtures/', 'game/kit/schema/invalid/',
                      'scripts/review/fixtures/', 'scripts/art/kit/fixtures/',
                      'scripts/art/native/fixtures/', 'tests/fixtures/')
KIT_REQUIREMENTS = {'docs/codex/' + name + '-kit.md' for name in
                    ('crossroads', 'coast-city', 'sunstone', 'fire-country', 'tidebloom', 'highgarth')}
ENGINE_ERROR = re.compile(r'^\s*(?:SCRIPT ERROR|ERROR:|Parse Error|Failed loading resource|Cannot open file|godot errors at)', re.M)


class ReviewError(ValueError):
    """A preflight or evidence failure that must not become a passing sheet."""


def _decode(value: bytes) -> str:
    return value.decode('utf-8', errors='surrogateescape')


def _git(repo: Path, *args: str) -> bytes:
    result = subprocess.run(['git', '--literal-pathspecs', '-C', str(repo), *args],
                            capture_output=True, timeout=30,
                            env=dict(os.environ, GIT_NO_REPLACE_OBJECTS='1'))
    if result.returncode:
        raise ReviewError(result.stderr.decode('utf-8', errors='replace').strip() or 'Git command failed')
    return result.stdout


def _commit(repo: Path, ref: str) -> str:
    return _git(repo, 'rev-parse', '--verify', '--end-of-options', ref + '^{commit}').decode().strip()


def collect_changes(repo: Path, base: str, head: str) -> dict:
    """Resolve refs once and read Git's NUL-delimited, three-dot PR diff."""
    repo = Path(repo).resolve()
    base_sha, head_sha = _commit(repo, base), _commit(repo, head)
    ancestors = _git(repo, 'merge-base', '--all', base_sha, head_sha).decode().splitlines()
    if len(ancestors) != 1:
        raise ReviewError('base and head need exactly one merge base')
    fields = _git(repo, 'diff', '--no-ext-diff', '--name-status', '-z', '--find-renames',
                  ancestors[0], head_sha, '--').split(b'\0')
    if fields[-1:] == [b'']:
        fields.pop()
    changes = []
    index = 0
    while index < len(fields):
        status = fields[index].decode('ascii')
        index += 1
        if not status or status[0] not in 'ACDMRTUXB':
            raise ReviewError('unsupported Git change record')
        count = 2 if status[0] in 'RC' else 1
        if index + count > len(fields):
            raise ReviewError('incomplete Git change record')
        paths = [_decode(value) for value in fields[index:index + count]]
        index += count
        changes.append(dict(status=status, path=paths[-1], old_path=paths[0] if count == 2 else None))
    return dict(base=base_sha, head=head_sha, merge_base=ancestors[0],
                head_tree=_git(repo, 'rev-parse', head_sha + '^{tree}').decode().strip(), changes=changes)


def _guard(repo: Path, head: str):
    if _commit(repo, 'HEAD') != head:
        raise ReviewError('subject checkout moved away from the pinned head; it has not been reset')
    if _git(repo, 'status', '--porcelain', '-z', '--untracked-files=no'):
        raise ReviewError('subject has tracked changes; preserve them and use a clean checkout')
    flags = _git(repo, 'ls-files', '-v', '-z').split(b'\0')
    if any(entry and (entry[:1].islower() or entry[:1].upper() == b'S') for entry in flags):
        raise ReviewError('assume-unchanged/skip-worktree entries hide source changes; use a full verified checkout')


def _blob(repo: Path, ref: str, path: str) -> tuple[str, str, bytes]:
    entries = _git(repo, 'ls-tree', '-z', ref, '--', path).split(b'\0')
    entries = [value for value in entries if value]
    if len(entries) != 1:
        raise ReviewError(f'expected one committed file: {path!r}')
    metadata, actual_path = entries[0].split(b'\t', 1)
    mode, kind, sha = metadata.decode('ascii').split()
    if _decode(actual_path) != path or kind != 'blob':
        raise ReviewError(f'not a regular committed blob: {path!r}')
    return mode, sha, _git(repo, 'cat-file', 'blob', sha)


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _relative(out: Path, path: Path) -> str:
    resolved = path.resolve()
    if not resolved.is_relative_to(out.resolve()) or path.is_symlink() or not path.is_file():
        raise ReviewError(f'evidence must be a regular file inside the fresh bundle: {path.name!r}')
    return path.relative_to(out).as_posix()


def _png(path: Path) -> tuple[int, int]:
    with Image.open(path) as image:
        if image.format != 'PNG':
            raise ReviewError('expected PNG evidence')
        size = image.size
        image.verify()
    return size


def _command(repo: Path, out: Path, folder: Path, args: list[str], *, timeout=900, env=None) -> dict:
    folder.mkdir(parents=True, exist_ok=True)
    started = time.time()
    environment = dict(os.environ, PYTHONDONTWRITEBYTECODE='1')
    if env:
        environment.update(env)
    stdout, stderr, code = b'', b'', 127
    error = None
    try:
        process = subprocess.Popen(args, cwd=repo, env=environment, stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE, start_new_session=os.name == 'posix')
        try:
            stdout, stderr = process.communicate(timeout=timeout)
            code = process.returncode
        except subprocess.TimeoutExpired:
            try:
                if os.name == 'posix':
                    os.killpg(process.pid, signal.SIGKILL)
                else:
                    process.kill()
            except ProcessLookupError:
                pass
            stdout, stderr = process.communicate()
            code, error = 124, 'producer timed out; its owned process group was stopped'
    except OSError as exc:
        error = str(exc)
        stderr = str(exc).encode('utf-8', errors='backslashreplace')
    stdout_path, stderr_path = folder / 'stdout.txt', folder / 'stderr.txt'
    stdout_path.write_bytes(stdout)
    stderr_path.write_bytes(stderr)
    return dict(command=args, returncode=code, started=started, duration_seconds=round(time.time() - started, 3),
                stdout=_relative(out, stdout_path), stderr=_relative(out, stderr_path),
                stdout_sha256=_sha(stdout), stderr_sha256=_sha(stderr), error=error,
                stdout_text=stdout.decode('utf-8', errors='replace'),
                stderr_text=stderr.decode('utf-8', errors='replace'))


def _attach(row: dict, result: dict):
    for name in ('command', 'returncode', 'duration_seconds', 'stdout_sha256', 'stderr_sha256'):
        row[name] = result[name]
    row['evidence'].update(stdout=result['stdout'], stderr=result['stderr'])


def _counts(report: dict) -> dict:
    counts = report.get('counts')
    if not isinstance(counts, dict) or any(type(counts.get(k)) is not int or counts[k] < 0
                                           for k in ('blocker', 'fault', 'polish')):
        raise ReviewError('missing or malformed reported counts')
    return counts


def _findings(value) -> list[dict]:
    if not isinstance(value, list):
        raise ReviewError('expected a finding array')
    for finding in value:
        if not isinstance(finding, dict):
            raise ReviewError('finding entries must be objects')
        if not isinstance(finding.get('detector'), str) or not finding['detector']:
            raise ReviewError('finding needs a detector identifier')
        if finding.get('severity') not in ('blocker', 'fault', 'polish'):
            raise ReviewError('finding has an unsupported severity')
        if any(not isinstance(finding.get(key), str) for key in ('message', 'fix')):
            raise ReviewError('finding message/fix must be strings (blank text is allowed)')
        box = finding.get('box')
        if not isinstance(box, list) or len(box) != 4 or any(
                type(v) not in (int, float) or (isinstance(v, float) and not math.isfinite(v)) for v in box):
            raise ReviewError('finding needs four finite numeric box coordinates')
    return value


def _consistent_counts(report: dict, findings: list[dict]) -> dict:
    counts = _counts(report)
    if any(counts[key] != sum(f['severity'] == key for f in findings)
           for key in ('blocker', 'fault', 'polish')):
        raise ReviewError('reported counts do not match reported finding occurrences')
    return counts


def _report(row: dict, out: Path, path: Path, started: float) -> dict:
    row['evidence']['report'] = _relative(out, path)
    raw = path.read_bytes()
    row['report_sha256'] = _sha(raw)
    if path.stat().st_mtime < started - 2:
        raise ReviewError('stale report timestamp')
    value = json.loads(raw)
    if not isinstance(value, dict):
        raise ReviewError('expected a report object')
    return value


def _row(path: str, change=None) -> dict:
    return dict(path=path, change=change, status='incomplete', counts=None, input_sha256=None,
                command=[], returncode=None, report_sha256=None, errors=[],
                evidence=dict(report=None, preview=None, gate_sheet=None, stdout=None, stderr=None, pictures=[]))


def _asset(repo: Path, out: Path, pinned: dict, change: dict) -> dict:
    path = change['path']
    row = _row(path, change)
    removed = change['status'].startswith('D')
    source_ref = pinned['merge_base'] if removed else pinned['head']
    source_path = change.get('old_path') if removed and change.get('old_path') else path
    row['input_ref'] = source_ref
    try:
        mode, blob, data = _blob(repo, source_ref, source_path)
        row.update(input_blob=blob, input_sha256=_sha(data))
        if mode not in ('100644', '100755'):
            row['status'] = 'unsupported'
            raise ReviewError('linked or nonregular art is not committed image evidence')
        if Path(path).suffix.lower() != '.png':
            row['status'] = 'unsupported'
            raise ReviewError('image category is not supported by this PNG review bundle')
        preview = out / 'previews' / (blob + '.png')
        preview.parent.mkdir(exist_ok=True)
        preview.write_bytes(data)
        row['size'] = list(_png(preview))
        row['evidence']['preview'] = _relative(out, preview)
        if removed:
            row['status'] = 'removed'
            row['errors'].append('removed art has a base preview, not a head detector pass')
            return row
        _guard(repo, pinned['head'])
        if _sha((repo / path).read_bytes()) != row['input_sha256']:
            raise ReviewError('checkout image differs from the pinned Git blob')
        folder = out / 'gates' / ('asset-' + _sha(os.fsencode(path))[:20])
        result = _command(repo, out, folder, [sys.executable, '-m', 'scripts.review.assets',
                                            str(repo / path), '--out', str(folder), '--no-sheet'])
        _attach(row, result)
        _guard(repo, pinned['head'])
        reports = list(folder.glob('*.json'))
        if len(reports) != 1:
            raise ReviewError('asset command did not produce exactly one report')
        report = _report(row, out, reports[0], result['started'])
        reported_path = report.get('file')
        if not isinstance(reported_path, str) or (repo / reported_path).resolve() != (repo / path).resolve():
            raise ReviewError('report describes a different source image')
        if report.get('sha256') != row['input_sha256']:
            raise ReviewError('report image hash does not match the pinned input')
        counts = _consistent_counts(report, _findings(report.get('findings')))
        if report.get('size') != row['size']:
            raise ReviewError('report image dimensions/findings are incomplete')
        status = report.get('status')
        if status not in ('pass', 'fail') or result['returncode'] != (0 if status == 'pass' else 1):
            raise ReviewError('producer exit and reported detector status do not agree')
        if status == 'pass' and (counts['blocker'] or counts['fault']):
            raise ReviewError('passing status contradicts reported blockers/faults')
        # The public --no-sheet gate keeps all detector metrics, without the
        # legacy contact sheet's generated kit-reference cache dependency.
        # The byte-identical pinned preview is already beside these numbers.
        row.update(status=status, counts=counts, metrics={k: report.get(k) for k in
                   ('id', 'kind', 'biome', 'H', 'density', 'detail_bar')})
    except (ReviewError, OSError, ValueError, TypeError, Image.DecompressionBombError) as exc:
        row['errors'].append(str(exc))
    return row


def _safe_component(value: str) -> bool:
    return isinstance(value, str) and bool(value) and value not in ('.', '..') and not any(c in value for c in '/\\\0\r\n')


def _zones(repo: Path) -> dict:
    path = repo / 'game/data/zones.json'
    if not path.is_file():
        return {}
    value = json.loads(path.read_bytes())
    if not isinstance(value, dict):
        raise ReviewError('zone registry is not an object')
    return value


def _import_project(repo: Path, out: Path) -> dict:
    folder = out / 'gates' / 'godot-import'
    engine = os.environ.get('GODOT')
    if engine and not Path(engine).is_file():
        engine = shutil.which(engine)
    if not engine:
        resolve = _command(repo, out, folder / 'resolve', ['bash', str(repo / 'game/tools/get_godot.sh')])
        lines = resolve['stdout_text'].strip().splitlines()
        if resolve['returncode'] or not lines:
            resolve['error'] = 'cannot resolve the project Godot binary'
            return resolve
        engine = lines[-1]
    with tempfile.TemporaryDirectory(prefix='pr-sheet-godot-') as temporary:
        env = {key: str(Path(temporary) / name) for key, name in
               (('XDG_DATA_HOME', 'data'), ('XDG_CONFIG_HOME', 'config'), ('XDG_CACHE_HOME', 'cache'))}
        result = _command(repo, out, folder, [engine, '--headless', '--audio-driver', 'Dummy',
                                             '--path', 'game', '--import'], timeout=600, env=env)
    if ENGINE_ERROR.search(result['stdout_text'] + '\n' + result['stderr_text']):
        result['error'] = 'Godot import logged engine errors'
    return result


def _scene(repo: Path, out: Path, pinned: dict, zone: str, registry: dict,
           spawns: tuple, preflight: dict | None) -> dict:
    row = _row(zone)
    try:
        if not _safe_component(zone) or zone not in registry:
            raise ReviewError('request a registered zone ID; arbitrary scene/plan overrides are unsupported')
        scene_path = registry[zone]
        if not isinstance(scene_path, str) or not scene_path.startswith('res://'):
            raise ReviewError('zone registry lacks a res:// scene path')
        path = scene_path.removeprefix('res://')
        if (repo / 'game' / path).resolve().is_relative_to((repo / 'game').resolve()) is False:
            raise ReviewError('registered scene escapes the game root')
        mode, blob, data = _blob(repo, pinned['head'], 'game/' + path)
        if mode not in ('100644', '100755'):
            raise ReviewError('registered scene is not a regular committed file')
        row.update(input_blob=blob, input_sha256=_sha(data), registered_scene='game/' + path)
        if not preflight or preflight['returncode'] != 0 or preflight.get('error'):
            raise ReviewError('observed Godot import did not pass; see preflight evidence')
        _guard(repo, pinned['head'])
        folder = out / 'gates' / ('scene-' + _sha(os.fsencode(zone))[:20])
        command = [sys.executable, '-m', 'scripts.review.run', zone, '--out', str(folder)]
        for spawn in spawns:
            command += ['--spawn', spawn]
        result = _command(repo, out, folder, command)
        _attach(row, result)
        _guard(repo, pinned['head'])
        report = _report(row, out, folder / 'report.json', result['started'])
        if report.get('target') != zone or not isinstance(report.get('scene'), dict) or report['scene'].get('zone') != zone:
            raise ReviewError('scene report describes another or missing registered target')
        declared = report['scene'].get('spawns')
        if not isinstance(declared, list) or not declared or any(not _safe_component(s) for s in declared):
            raise ReviewError('scene report has no usable declared spawn coverage')
        requested = list(spawns) if spawns else declared
        if any(spawn not in declared for spawn in requested):
            raise ReviewError('requested spawn is not declared; a runtime fallback is not requested coverage')
        if 'zone' in requested:
            raise ReviewError("spawn 'zone' collides with the producer's composite filename; distinct capture evidence is unavailable")
        pictures = report.get('pictures')
        if not isinstance(pictures, list) or not all(isinstance(p, dict) for p in pictures):
            raise ReviewError('scene pictures are malformed')
        names = [p.get('picture') for p in pictures]
        expected = [f'{zone}_{spawn}' for spawn in requested]
        if not expected or any(name not in names for name in expected):
            raise ReviewError('one or more requested rendered captures are missing; the composite is not a capture')
        for name in [f'{zone}_zone', *expected]:
            raw = folder / (name + '.png')
            rel = _relative(out, raw)
            _png(raw)
            row['evidence']['pictures'].append(rel)
        occurrences = list(_findings(report['scene'].get('findings')))
        for picture in pictures:
            occurrences.extend(_findings(picture.get('findings')))
            name = picture.get('picture')
            if not _safe_component(name):
                raise ReviewError('unsafe picture identifier in scene report')
            boxed = folder / (name + '_boxed.png')
            rel = _relative(out, boxed)
            _png(boxed)
            row['evidence']['pictures'].append(rel)
            grids = picture.get('grid', [])
            if not isinstance(grids, list) or any(not isinstance(value, str) for value in grids):
                raise ReviewError('malformed grid evidence paths')
            for grid in grids:
                image = folder / grid
                rel = _relative(out, image)
                _png(image)
                row['evidence']['pictures'].append(rel)
        if ENGINE_ERROR.search(result['stdout_text'] + '\n' + result['stderr_text']):
            raise ReviewError('scene producer logged Godot errors even though it wrote a report')
        counts = _consistent_counts(report, occurrences)
        expected_code = 1 if counts['blocker'] or counts['fault'] else 0
        if result['returncode'] != expected_code:
            raise ReviewError('scene producer exit does not agree with its reported detector counts')
        row.update(status='fail' if expected_code else 'pass', counts=counts,
                   expected_spawns=requested, capture_count=len(expected),
                   counts_note='Reported occurrences: scene findings also appear in the zone composite; not unique faults.')
        row['evidence']['preview'] = _relative(out, folder / (expected[0] + '.png'))
        row['evidence']['gate_sheet'] = _relative(out, folder / (expected[0] + '_boxed.png'))
    except (ReviewError, OSError, ValueError, TypeError, Image.DecompressionBombError) as exc:
        row['errors'].append(str(exc))
    return row


def _escape(value) -> str:
    return html.escape(str(value), quote=True)


def _fixture(path: str) -> bool:
    return path.startswith(TEST_FIXTURE_ROOTS)


def _source_category(path: str) -> str | None:
    """Bounded production-source routing; not schema or art validation."""
    if path.startswith('docs/vision/research/blockout/towns/') or (
            path.startswith('docs/codex/') and path.endswith('-town-polish.md')):
        return 'town_plan'
    if path.startswith('game/data/kit/concepts/') or path in KIT_REQUIREMENTS:
        return 'kit_concept'
    if path.startswith(('art/characters/', 'art/cast/', 'castwork/', 'docs/vision/characters/',
                        'docs/characters/', 'scripts/characters/',
                        'game/assets/characters/', 'game/data/cast/', 'game/data/progression/')) or path in (
            'docs/vision/cast.md', 'docs/vision/world-and-cast.md', 'docs/vision/progression.md',
            'game/data/weapon_lines.json', 'game/actors/cast_sprite.gd'):
        return 'cast_source'
    if path.startswith(('scripts/art/', 'game/art/', 'game/kit/', 'game/data/plans/')) or (
            path.startswith('docs/vision/research/blockout/') and Path(path).suffix.lower() == '.py') or (
            Path(path).suffix.lower() in ('.gdshader', '.ase')):
        return 'art_source'
    return None


def _source_row(repo: Path, out: Path, pinned: dict, change: dict, status: str, category: str,
                *, zones=()) -> dict:
    """Attest both sides without executing or interpreting source/fixture bytes."""
    row = dict(path=change['path'], status=status, category=category, change=change,
               inputs=[], errors=[])
    if zones:
        row['zones'] = list(zones)
    versions = []
    if change['status'][0] not in ('A', '?') and change['status'] != 'requested':
        versions.append(('before', pinned['merge_base'], change.get('old_path') or change['path']))
    if not change['status'].startswith('D'):
        versions.append(('after', pinned['head'], change['path']))
    try:
        for side, ref, path in versions:
            mode, blob, data = _blob(repo, ref, path)
            row['inputs'].append(dict(side=side, ref=ref, path=path, mode=mode,
                                      blob=blob, sha256=_sha(data)))
            if mode not in ('100644', '100755'):
                raise ReviewError('source/fixture evidence is not a regular committed file')
            folder = out / 'sources'
            folder.mkdir(exist_ok=True)
            source = folder / (blob + '.txt')
            source.write_bytes(data)
            row['inputs'][-1]['evidence'] = _relative(out, source)
    except (ReviewError, OSError, ValueError) as exc:
        row['errors'].append(str(exc))
    return row


def _link(value: str | None, label: str) -> str:
    return f'<a href="{quote(value, safe="/")}">{_escape(label)}</a>' if value else ''


def _render(manifest: dict) -> str:
    cards = []
    for row in manifest['assets'] + manifest['scenes']:
        evidence = row['evidence']
        preview = evidence.get('preview')
        image = f'<a href="{quote(preview, safe="/")}"><img src="{quote(preview, safe="/")}" alt="{_escape(row["path"])}"></a>' if preview else '<p>No verified preview</p>'
        links = ' · '.join(filter(None, [_link(evidence.get(k), k.replace('_', ' ')) for k in
                                          ('report', 'gate_sheet', 'stdout', 'stderr')]))
        counts = json.dumps(row['counts'], ensure_ascii=True) if row['counts'] is not None else 'Unavailable'
        errors = ''.join(f'<li>{_escape(value)}</li>' for value in row['errors'])
        metrics = json.dumps(row.get('metrics', {}), ensure_ascii=True, indent=2)
        cards.append(f'<article><div>{image}</div><div><h2>{_escape(row["path"])}</h2>'
                     f'<p>Selection: {_escape((row.get("change") or {}).get("status", "requested scene"))}</p>'
                     f'<p><strong>{_escape(row["status"])}</strong> · reported gate counts: {_escape(counts)}</p>'
                     f'<p>{_escape(row.get("counts_note", ""))}</p><ul>{errors}</ul>'
                     f'<p>Input SHA256: <code>{_escape(row["input_sha256"])}</code></p>'
                     f'<p>Command exit: {_escape(row["returncode"])}</p><p>{links}</p>'
                     f'<details><summary>Existing gate metrics and command</summary><pre>{_escape(metrics)}\n'
                     f'{_escape(json.dumps(row["command"], ensure_ascii=True))}</pre></details></div></article>')
    changed = ''.join(f'<li><code>{_escape(c["status"])} {_escape(c["path"])}</code>'
                      f'{" ← " + _escape(c["old_path"]) if c.get("old_path") else ""}</li>' for c in manifest['changes'])
    others = ''.join(f'<li>{_escape(c["path"])}: {_escape(c["status"])} '
                     f'({_escape(c.get("category", "not_art"))})'
                     + ' '.join(_link(v.get('evidence'), v['side'] + ' source bytes')
                                for v in c.get('inputs', [])) +
                     f'<pre>{_escape(json.dumps(c.get("inputs", []), ensure_ascii=True, sort_keys=True))}</pre>'
                     f'{_escape("; ".join(c.get("errors", [])))}</li>' for c in manifest['other_changes'])
    errors = ''.join(f'<li>{_escape(value)}</li>' for value in manifest['errors'])
    return f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>PR pre-review evidence</title><style>
body{{font:16px/1.5 system-ui,sans-serif;max-width:1250px;margin:32px auto;padding:0 20px;color:#20272b;background:#f5f5f2}}
article{{display:grid;grid-template-columns:minmax(220px,360px) minmax(0,1fr);gap:24px;padding:24px;margin:20px 0;background:white;border:1px solid #ccd0d0}}
img{{max-width:100%;max-height:420px;object-fit:contain;image-rendering:pixelated;background:#ddd}}h2{{font-size:20px;overflow-wrap:anywhere}}
pre,code{{overflow-wrap:anywhere;white-space:pre-wrap;font-size:13px}}a{{color:#164f78}}@media(max-width:650px){{article{{grid-template-columns:1fr}}}}
</style><header><h1>PR pre-review evidence</h1><p>{_escape(manifest.get('pr') or 'Pinned Git comparison')}</p>
<p><strong>Manual art review: not assessed.</strong> Detector results are not approval.</p>
<p>Scope: {_escape(manifest['scope'])}; requested detector evidence complete and passing: {_escape(manifest['complete'])}.</p>
<p>Base <code>{manifest['base']}</code><br>Head <code>{manifest['head']}</code><br>Merge base <code>{manifest['merge_base']}</code><br>Head tree <code>{manifest['head_tree']}</code></p>
<p>{_link('manifest.json', 'Exact provenance, commands, hashes and all changes')}</p><ul>{errors}</ul></header>
{''.join(cards) if cards else '<p>No raster or scene detector row. Source-only changes need review; test evidence is not a production art pass.</p>'}
<h2>Other changed files (not rated as art)</h2><ul>{others}</ul><details><summary>All Git changes</summary><ul>{changed}</ul></details></html>'''


def build_sheet(repo: Path, base: str, head: str, out: Path, *, scenes=(), pr=None, spawns=(), assets=()) -> dict:
    """Run existing gates on a clean pinned checkout and write an honest bundle."""
    repo, out = Path(repo).resolve(), Path(out).resolve()
    pinned = collect_changes(repo, base, head)
    _guard(repo, pinned['head'])
    spawns = tuple(dict.fromkeys(spawns))
    if any(not _safe_component(spawn) for spawn in spawns):
        raise ReviewError('spawn IDs must be safe single filename components')
    if out.exists() and (not out.is_dir() or any(out.iterdir())):
        raise ReviewError('output must be fresh or empty; existing evidence was not reused or deleted')
    git_dir = Path(_git(repo, 'rev-parse', '--absolute-git-dir').decode().strip()).resolve()
    common_dir = (repo / _decode(_git(repo, 'rev-parse', '--git-common-dir')).strip()).resolve()
    if out == repo or out.is_relative_to(git_dir) or out.is_relative_to(common_dir):
        raise ReviewError('output must not replace the repository or Git metadata')
    out.mkdir(parents=True, exist_ok=True)
    manifest = dict(**pinned, pr=pr, manual_review='not_assessed', scope='no_art', complete=False,
                    exit_code=1, assets=[], scenes=[], other_changes=[], errors=[], preflight=None,
                    tool_sha256=_sha(Path(__file__).read_bytes()), python_version=sys.version.split()[0],
                    generated_at=time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()))
    try:
        registry = _zones(repo)
    except (OSError, ValueError) as exc:
        registry = {}
        manifest['errors'].append(f'zone registry unavailable: {exc}')
    requested = set(scenes)
    pending_assets = []
    for change in pinned['changes']:
        path = change['path']
        suffix = Path(path).suffix.lower()
        previous = change.get('old_path') or path
        old_suffix = Path(previous).suffix.lower()
        if all(_fixture(value) for value in (path, previous)):
            manifest['other_changes'].append(_source_row(repo, out, pinned, change, 'test_evidence', 'test_fixture'))
        elif suffix in IMAGE_SUFFIXES or old_suffix in IMAGE_SUFFIXES:
            pending_assets.append(change)
            # Raster evidence cannot discharge a non-image source obligation on
            # either side of a rename, even when malformed source has PNG bytes.
            source_paths = [value for value in (path, previous)
                            if Path(value).suffix.lower() not in IMAGE_SUFFIXES]
            category = next((_source_category(value) for value in source_paths
                             if _source_category(value)), None)
            if category:
                manifest['other_changes'].append(_source_row(
                    repo, out, pinned, change, 'source_only', category))
        elif '.tscn' in (suffix, old_suffix):
            zones = [zone for zone, scene in registry.items()
                     if isinstance(scene, str) and scene.startswith('res://')
                     and path == 'game/' + scene.removeprefix('res://')]
            requested.update(zones)
            manifest['other_changes'].append(_source_row(repo, out, pinned, change,
                'scene_source' if zones else 'source_only', 'scene_source', zones=zones))
        elif any(_source_category(value) for value in (path, previous)):
            category = _source_category(path) or _source_category(previous)
            manifest['other_changes'].append(_source_row(repo, out, pinned, change, 'source_only', category))
        else:
            manifest['other_changes'].append(dict(path=path, status='not_art', change=change))
    selected = {change['path'] for change in pending_assets}
    selected.update(row['path'] for row in manifest['other_changes'] if row['status'] == 'test_evidence')
    for asset in assets:
        path = Path(asset)
        if path.is_absolute():
            try:
                path = path.relative_to(repo)
            except ValueError as exc:
                raise ReviewError('requested asset must be inside the subject repository') from exc
        name = path.as_posix()
        if name not in selected:
            change = dict(status='requested', path=name, old_path=None)
            if _fixture(name):
                manifest['other_changes'].append(_source_row(repo, out, pinned, change, 'test_evidence', 'test_fixture'))
            else:
                pending_assets.append(change)
            selected.add(name)
    fatal = False
    for change in pending_assets:
        if fatal:
            row = _row(change['path'], change)
            row['errors'].append('source changed; remaining checks were not run')
        else:
            row = _asset(repo, out, pinned, change)
            try:
                _guard(repo, pinned['head'])
            except ReviewError as exc:
                fatal = True
                row['status'], row['counts'] = 'incomplete', None
                manifest['errors'].append(str(exc))
        manifest['assets'].append(row)
    preflight = None
    eligible = {zone for zone in requested if _safe_component(zone) and zone in registry}
    if spawns and not requested:
        raise ReviewError('requested spawns need an explicit or inferred registered scene')
    if eligible and not fatal:
        try:
            _guard(repo, pinned['head'])
            preflight = _import_project(repo, out)
            _guard(repo, pinned['head'])
            manifest['preflight'] = {k: v for k, v in preflight.items() if not k.endswith('_text')}
        except (ReviewError, OSError, ValueError) as exc:
            fatal = True
            manifest['errors'].append(str(exc))
    for zone in sorted(requested):
        if fatal:
            row = _row(zone)
            row['errors'].append('source preflight failed; scene checks were not run')
        else:
            row = _scene(repo, out, pinned, zone, registry, tuple(spawns), preflight)
            try:
                _guard(repo, pinned['head'])
            except ReviewError as exc:
                fatal = True
                row['status'], row['counts'] = 'incomplete', None
                manifest['errors'].append(str(exc))
        manifest['scenes'].append(row)
    try:
        _guard(repo, pinned['head'])
    except ReviewError as exc:
        manifest['errors'].append(str(exc))
    for row in manifest['other_changes']:
        for value in row.get('inputs', []):
            if 'evidence' not in value:
                continue
            try:
                source = out / value['evidence']
                _relative(out, source)
                if _sha(source.read_bytes()) != value['sha256']:
                    raise ReviewError('bundled source bytes changed after classification')
            except (ReviewError, OSError) as exc:
                row['errors'].append(str(exc))
    source_only = any(row['status'] == 'source_only' for row in manifest['other_changes'])
    if manifest['assets'] or manifest['scenes']:
        manifest['scope'] = 'detector_evidence'
    elif source_only:
        manifest['scope'] = 'source_only'
    elif any(row['status'] == 'test_evidence' for row in manifest['other_changes']):
        manifest['scope'] = 'test_evidence'
    source_errors = any(row.get('errors') for row in manifest['other_changes'])
    manifest['complete'] = (not manifest['errors'] and not source_only and not source_errors
                            and all(row['status'] == 'pass' for row in manifest['assets'] + manifest['scenes']))
    manifest['exit_code'] = 0 if manifest['complete'] else 1
    (out / 'index.html').write_text(_render(manifest), encoding='utf-8', errors='backslashreplace')
    # Hash every evidence file, including the index, previews and raw logs. The
    # manifest itself is excluded rather than claiming a recursive self-hash.
    manifest['files'] = {p.relative_to(out).as_posix(): _sha(p.read_bytes()) for p in sorted(out.rglob('*'))
                         if p.is_file() and not p.is_symlink()}
    (out / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=True, sort_keys=True, indent=2) + '\n', encoding='utf-8')
    return manifest


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--repo', type=Path, default=REPO)
    parser.add_argument('--base', required=True, help='target/base Git ref, resolved once')
    parser.add_argument('--head', default='HEAD', help='subject Git ref; must match clean checkout')
    parser.add_argument('--out', type=Path, required=True, help='fresh or empty output directory')
    parser.add_argument('--scene', action='append', default=[], help='registered zone ID, repeatable')
    parser.add_argument('--asset', action='append', default=[], help='additional committed PNG context, repeatable; not a Git change')
    parser.add_argument('--spawn', action='append', default=[], help='declared spawn, repeatable; default every spawn')
    parser.add_argument('--pr', help='descriptive PR label; Git SHAs, not this label, establish provenance')
    args = parser.parse_args(argv)
    try:
        manifest = build_sheet(args.repo, args.base, args.head, args.out,
                               scenes=args.scene, spawns=args.spawn, assets=args.asset, pr=args.pr)
        print(f'PR sheet: {manifest["scope"]}, detector evidence complete={manifest["complete"]}; manual review not assessed.')
        print(str((args.out / 'index.html').resolve()).encode(sys.stdout.encoding or 'utf-8', errors='backslashreplace').decode(sys.stdout.encoding or 'utf-8'))
        return manifest['exit_code']
    except (ReviewError, OSError, ValueError, TypeError, subprocess.SubprocessError) as exc:
        message = f'PR sheet: {exc}'
        print(message.encode(sys.stderr.encoding or 'utf-8', errors='backslashreplace').decode(sys.stderr.encoding or 'utf-8'), file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
