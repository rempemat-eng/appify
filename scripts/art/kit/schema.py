"""Validate world-editor pieces against game/kit/schema/piece.schema.json.

CI installs only Pillow, numpy and scipy, so this is a small validator for the subset of JSON
Schema the piece schema uses ($ref into $defs, type (one or a list), const, enum, required,
properties, additionalProperties false, items, minItems, maxItems, minimum, maximum, minLength,
pattern). Where the `jsonschema` package is installed the test suite checks the two agree.

    python3 -m scripts.art.kit.schema [paths ...]     # every piece in game/kit/pieces by default
    python3 -m scripts.art.kit.schema --migrate [--dry-run] [paths ...]

Migration follows explicit schema-id steps registered in MIGRATIONS. A piece's `version` is
its content revision, not its schema version. There is no pre-v1 format to guess a conversion
from: current v1 files are left byte-for-byte alone, and unknown schema ids fail without writes.
When a schema is bumped, add its reviewed predecessor conversion to MIGRATIONS alongside it.
"""
from __future__ import annotations

import argparse
import copy
import json
import os
import re
import stat
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
SCHEMA_PATH = os.path.join(ROOT, 'game', 'kit', 'schema', 'piece.schema.json')
PIECES = os.path.join(ROOT, 'game', 'kit', 'pieces')

# source schema id -> (destination schema id, conversion function). Each function accepts and
# returns a piece dictionary. Only real, reviewed historical formats belong here.
MIGRATIONS = {}

_TYPES = {
    'object': lambda v: isinstance(v, dict),
    'array': lambda v: isinstance(v, list),
    'string': lambda v: isinstance(v, str),
    'integer': lambda v: isinstance(v, int) and not isinstance(v, bool),
    'number': lambda v: isinstance(v, (int, float)) and not isinstance(v, bool),
    'boolean': lambda v: isinstance(v, bool),
    'null': lambda v: v is None,
}
_KNOWN = {'$schema', '$id', '$defs', '$ref', 'title', 'description', 'type', 'const', 'enum', 'required',
          'properties', 'additionalProperties', 'items', 'minItems', 'maxItems', 'minimum', 'maximum',
          'minLength', 'pattern'}


def load_schema() -> dict:
    with open(SCHEMA_PATH) as handle:
        return json.load(handle)


def errors(value, schema: dict, root: dict | None = None, path: str = '$') -> list:
    root = root or schema
    out = []
    unknown = set(schema) - _KNOWN
    if unknown:
        raise ValueError('schema keyword(s) %s at %s are not supported by scripts/art/kit/schema.py' % (sorted(unknown), path))
    if '$ref' in schema:
        ref = schema['$ref']
        assert ref.startswith('#/$defs/'), ref
        return errors(value, root['$defs'][ref[len('#/$defs/'):]], root, path)
    t = schema.get('type')
    if t is not None:
        ts = t if isinstance(t, list) else [t]
        if not any(_TYPES[x](value) for x in ts):
            return ['%s: expected %s, got %s' % (path, '/'.join(ts), type(value).__name__)]
    if 'const' in schema and value != schema['const']:
        out.append('%s: must be %r' % (path, schema['const']))
    if 'enum' in schema and value not in schema['enum']:
        out.append('%s: %r is not one of %s' % (path, value, schema['enum']))
    if isinstance(value, dict):
        for k in schema.get('required', []):
            if k not in value:
                out.append('%s: missing %r' % (path, k))
        props = schema.get('properties', {})
        for k, v in value.items():
            if k in props:
                out += errors(v, props[k], root, '%s.%s' % (path, k))
            elif schema.get('additionalProperties') is False:
                out.append('%s: unknown key %r' % (path, k))
    if isinstance(value, list):
        if 'minItems' in schema and len(value) < schema['minItems']:
            out.append('%s: fewer than %d items' % (path, schema['minItems']))
        if 'maxItems' in schema and len(value) > schema['maxItems']:
            out.append('%s: more than %d items' % (path, schema['maxItems']))
        if 'items' in schema:
            for i, v in enumerate(value):
                out += errors(v, schema['items'], root, '%s[%d]' % (path, i))
    if _TYPES['number'](value):
        if 'minimum' in schema and value < schema['minimum']:
            out.append('%s: %s < %s' % (path, value, schema['minimum']))
        if 'maximum' in schema and value > schema['maximum']:
            out.append('%s: %s > %s' % (path, value, schema['maximum']))
    if isinstance(value, str):
        if 'minLength' in schema and len(value) < schema['minLength']:
            out.append('%s: empty' % path)
        if 'pattern' in schema and not re.search(schema['pattern'], value):
            out.append('%s: %r does not match %s' % (path, value, schema['pattern']))
    return out


def semantic(piece: dict) -> list:
    """Rules a JSON Schema cannot say: the kind's own block is present, ids match file names."""
    out = []
    k = piece.get('kind')
    concept = piece.get('approval', {}).get('state') == 'concept'
    # Pre-art concepts may defer renderer/runtime blocks; supplied blocks still obey the schema.
    if not concept and k == 'terrain' and 'terrain' not in piece:
        out.append('a terrain piece needs a "terrain" block')
    if not concept and k == 'transition' and 'transition' not in piece:
        out.append('a transition piece needs a "transition" block')
    if not concept and k in ('structure', 'prop') and 'geometry' not in piece:
        out.append('a %s needs a "geometry" block' % k)
    a = piece.get('approval', {})
    if a.get('state') == 'approved' and not (a.get('by') and a.get('at')):
        out.append('an approved piece names who approved it and when')
    return out


def piece_files(base: str = PIECES) -> list:
    out = []
    for d, _, fs in os.walk(base):
        out += [os.path.join(d, f) for f in fs if f.endswith('.json')]
    return sorted(out)


def _location_errors(piece: dict, path: str) -> list:
    # Concepts remain review documents even when every optional runtime field is supplied.
    if piece.get('approval', {}).get('state') == 'concept' and os.path.commonpath(
            [os.path.abspath(path), os.path.abspath(PIECES)]) == os.path.abspath(PIECES):
        return ['a concept is non-buildable/non-placeable; keep it outside the live piece library (including labs)']
    return []


def check(paths=None) -> dict:
    schema = load_schema()
    res = {}
    ids = {}
    for p in paths or piece_files():
        with open(p) as handle:
            piece = json.load(handle)
        e = errors(piece, schema) + semantic(piece)
        e += _location_errors(piece, p)
        stem = os.path.splitext(os.path.basename(p))[0]
        if piece.get('id') != stem:
            e.append('id %r differs from its file name %r' % (piece.get('id'), stem))
        if piece.get('id') in ids:
            e.append('id %r also in %s' % (piece.get('id'), ids[piece.get('id')]))
        ids[piece.get('id')] = p
        res[p] = e
    return res


def migrate_piece(piece: dict, schema: dict | None = None, migrations: dict | None = None) -> dict:
    """Return a validated copy in the current schema, following explicit registered steps.

    Parameters allow a future schema and its conversion chain to be tested before publication.
    Neither the input dictionary nor its nested records are mutated.
    """
    schema = load_schema() if schema is None else schema
    migrations = MIGRATIONS if migrations is None else migrations
    target = schema['$id']
    result = copy.deepcopy(piece)
    if not isinstance(result, dict):
        raise ValueError('a piece must be an object')
    visited = set()
    while result.get('schema') != target:
        source = result.get('schema')
        if not isinstance(source, str) or source not in migrations:
            raise ValueError('no migration from schema %r to %r' % (source, target))
        if source in visited:
            raise ValueError('migration cycle at schema %r' % source)
        visited.add(source)
        destination, convert = migrations[source]
        result = convert(copy.deepcopy(result))
        if not isinstance(result, dict) or result.get('schema') != destination:
            raise ValueError('migration from %r must produce schema %r' % (source, destination))
    problems = errors(result, schema) + semantic(result)
    if problems:
        raise ValueError('migrated piece is invalid: ' + '; '.join(problems))
    return result


def _stage_bytes(path: str, data: bytes, mode: int) -> str:
    """Stage a replacement on the same filesystem, retaining the original permissions."""
    fd, tmp = tempfile.mkstemp(prefix='.piece-migrate-', dir=os.path.dirname(os.path.abspath(path)))
    try:
        with os.fdopen(fd, 'wb') as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(tmp, mode)
    except BaseException:
        if os.path.exists(tmp):
            os.unlink(tmp)
        raise
    return tmp


def migrate_files(paths=None, *, dry_run: bool = False, schema: dict | None = None,
                  migrations: dict | None = None) -> dict:
    """Validate the whole requested batch before replacing any file.

    Unchanged current-schema files retain their exact bytes and mtime. Converted files are
    replaced atomically; if a later replacement fails, earlier replacements are rolled back.
    Originals are checked again after staging, so a concurrent edit is refused, not overwritten.
    """
    schema = load_schema() if schema is None else schema
    files = list(paths) if paths is not None else piece_files()
    changed = {}
    replacements = []
    ids = {}
    for path in files:
        with open(path, 'rb') as handle:
            original = handle.read()
        piece = json.loads(original)
        try:
            migrated = migrate_piece(piece, schema, migrations)
            location = _location_errors(migrated, path)
            if location:
                raise ValueError('; '.join(location))
            stem = os.path.splitext(os.path.basename(path))[0]
            if migrated.get('id') != stem:
                raise ValueError('id %r differs from its file name %r' % (migrated.get('id'), stem))
            if migrated['id'] in ids:
                raise ValueError('id %r also in %s' % (migrated['id'], ids[migrated['id']]))
        except ValueError as exc:
            raise ValueError('%s: %s' % (path, exc)) from exc
        ids[migrated['id']] = path
        # Compare values, not re-serialized bytes: a current schema never triggers reformatting.
        changed[path] = migrated != piece
        if changed[path]:
            data = (json.dumps(migrated, indent=2, ensure_ascii=False, allow_nan=False) + '\n').encode('utf-8')
            replacements.append((path, original, data, stat.S_IMODE(os.stat(path).st_mode)))
    if dry_run or not replacements:
        return changed

    staged = []
    backups = []
    applied = []
    retained_backups = set()
    try:
        for path, original, data, mode in replacements:
            staged.append(_stage_bytes(path, data, mode))
            backups.append(_stage_bytes(path, original, mode))
        for path, original, _, _ in replacements:
            with open(path, 'rb') as handle:
                if handle.read() != original:
                    raise ValueError('%s changed while migration was being prepared' % path)
        for i, (path, _, _, _) in enumerate(replacements):
            os.replace(staged[i], path)
            applied.append(i)
    except BaseException as exc:
        failed_rollbacks = []
        for i in reversed(applied):
            try:
                os.replace(backups[i], replacements[i][0])
            except OSError:
                retained_backups.add(backups[i])
                failed_rollbacks.append('%s (original retained at %s)' % (replacements[i][0], backups[i]))
        if failed_rollbacks:
            raise OSError('migration failed and could not restore: ' + '; '.join(failed_rollbacks)) from exc
        raise
    finally:
        for tmp in staged + backups:
            if tmp not in retained_backups and os.path.exists(tmp):
                os.unlink(tmp)
    return changed


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--migrate', action='store_true', help='apply registered schema-id migrations; refuse unknown formats')
    parser.add_argument('--dry-run', action='store_true', help='with --migrate, validate and report without writing')
    parser.add_argument('paths', nargs='*', help='piece JSON paths (default: every live-library piece)')
    args = parser.parse_args(argv)
    if args.dry_run and not args.migrate:
        parser.error('--dry-run requires --migrate')
    try:
        if args.migrate:
            changed = migrate_files(args.paths or None, dry_run=args.dry_run)
            print('pieces: %d checked, %d %s' % (len(changed), sum(changed.values()),
                                               'would migrate' if args.dry_run else 'migrated'))
            return 0
        res = check(args.paths or None)
    except (OSError, ValueError) as exc:
        print('pieces: ' + str(exc), file=sys.stderr)
        return 1
    bad = {p: e for p, e in res.items() if e}
    for p, e in bad.items():
        print(os.path.relpath(p, ROOT))
        for x in e:
            print('  ' + x)
    print('pieces: %d checked, %d with errors' % (len(res), len(bad)))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
