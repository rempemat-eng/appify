"""Validate world-editor pieces against game/kit/schema/piece.schema.json.

CI installs only Pillow, numpy and scipy, so this is a small validator for the subset of JSON
Schema the piece schema uses ($ref into $defs, type (one or a list), const, enum, required,
properties, additionalProperties false, items, minItems, maxItems, minimum, maximum, minLength,
pattern). Where the `jsonschema` package is installed the test suite checks the two agree.

    python3 -m scripts.art.kit.schema [paths ...]     # every piece in game/kit/pieces by default
"""
from __future__ import annotations

import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
SCHEMA_PATH = os.path.join(ROOT, 'game', 'kit', 'schema', 'piece.schema.json')
PIECES = os.path.join(ROOT, 'game', 'kit', 'pieces')

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
    return json.load(open(SCHEMA_PATH))


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
    if k == 'terrain' and 'terrain' not in piece:
        out.append('a terrain piece needs a "terrain" block')
    if k == 'transition' and 'transition' not in piece:
        out.append('a transition piece needs a "transition" block')
    if k in ('structure', 'prop') and 'geometry' not in piece:
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


def check(paths=None) -> dict:
    schema = load_schema()
    res = {}
    ids = {}
    for p in paths or piece_files():
        piece = json.load(open(p))
        e = errors(piece, schema) + semantic(piece)
        stem = os.path.splitext(os.path.basename(p))[0]
        if piece.get('id') != stem:
            e.append('id %r differs from its file name %r' % (piece.get('id'), stem))
        if piece.get('id') in ids:
            e.append('id %r also in %s' % (piece.get('id'), ids[piece.get('id')]))
        ids[piece.get('id')] = p
        res[p] = e
    return res


def main(argv=None) -> int:
    res = check(argv or None)
    bad = {p: e for p, e in res.items() if e}
    for p, e in bad.items():
        print(os.path.relpath(p, ROOT))
        for x in e:
            print('  ' + x)
    print('pieces: %d checked, %d with errors' % (len(res), len(bad)))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
