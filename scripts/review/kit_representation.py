"""Identify committed kit representations without rating their rendered appearance.

Only direct manifest/index bindings are understood. The caller supplies a pinned
Git-blob reader; this module never imports the subject's painters or opens paths.
A resolved data binding still needs composed/context review and is never a pass.
"""
from __future__ import annotations

import json
import math


TERRAIN = 'game/kit/terrain/'
PROPS = 'game/kit/props/art/'
MANIFEST = TERRAIN + 'manifest.json'
INDEX = 'game/kit/props/index.json'


def _object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f'duplicate metadata key: {key!r}')
        result[key] = value
    return result


def _name(value):
    if not isinstance(value, str) or not value or value in ('.', '..') or any(
            c in value for c in '/\\\0\r\n'):
        raise ValueError('metadata needs a safe nonempty name')
    return value


def _resource(value):
    if not isinstance(value, str) or not value.startswith('res://'):
        raise ValueError('kit image needs a canonical res:// path')
    parts = value[6:].split('/')
    for part in parts:
        _name(part)
    return 'game/' + '/'.join(parts)


def _pair(value):
    if not isinstance(value, list) or len(value) != 2 or any(
            type(v) not in (int, float) or (type(v) is float and not math.isfinite(v)) for v in value):
        raise ValueError('metadata anchor/offset needs two finite numbers')


def _array(value):
    if not isinstance(value, list):
        raise ValueError('metadata needs an array')
    return value


def _dict(value):
    if not isinstance(value, dict):
        raise ValueError('metadata needs an object')
    return value


def _constant(value):
    raise ValueError(f'invalid metadata number: {value}')


def _add(bindings, path, representation, owner):
    if not path.lower().endswith('.png'):
        raise ValueError('direct kit image binding must name a PNG')
    if path in bindings:
        raise ValueError(f'ambiguous kit image ownership: {path!r}')
    bindings[path] = (representation, owner)


def _terrain(value):
    bindings, owners = {}, set()
    for item in _array(value.get('materials')):
        item = _dict(item)
        owner = _name(item.get('id'))
        if owner in owners:
            raise ValueError('ambiguous material identity')
        owners.add(owner)
        _add(bindings, TERRAIN + _name(item.get('fill')), 'palette_codes', owner)
    transitions = set()
    for item in _array(value.get('transitions')):
        item = _dict(item)
        owner = _name(item.get('id'))
        if owner in transitions or owner in owners:
            raise ValueError('ambiguous transition identity')
        transitions.add(owner)
        if item.get('upper') not in owners or item.get('lower') not in owners | {'*', '^'}:
            raise ValueError('transition needs known material partners')
        _add(bindings, TERRAIN + _name(item.get('png')), 'transition_operations', owner)
    for owner, item in _dict(value.get('decals')).items():
        _name(owner)
        item = _dict(item)
        _pair(item.get('anchor'))
        _add(bindings, TERRAIN + _name(item.get('png')), 'decal_codes', owner)
    for key, representation in (('lut', 'palette_lut'), ('noise', 'noise_data'),
                                ('palette', 'editor_palette')):
        _add(bindings, TERRAIN + _name(value.get(key)), representation, key)
    return bindings


def _props(value):
    bindings = {}
    for owner, entry in value.items():
        _name(owner)
        entry = _dict(entry)
        if entry.get('kind') not in ('prop', 'structure'):
            raise ValueError('indexed physical owner needs prop/structure kind')
        role = entry.get('role')
        if role is not None and (not isinstance(role, str) or not role):
            raise ValueError('indexed owner role must be a nonempty string or null')
        variants = _dict(entry.get('variants'))
        if not variants:
            raise ValueError('indexed owner needs physical variants')
        for variant, image in variants.items():
            _name(variant)
            image = _dict(image)
            _pair(image.get('foot'))
            _add(bindings, _resource(image.get('png')), 'physical_sprite', owner)
        shadow = entry.get('shadow')
        if shadow is not None:
            shadow = _dict(shadow)
            if 'mask' in shadow:
                if role != 'tree':
                    raise ValueError('indexed crown mask needs a tree owner')
                mask = _dict(shadow['mask'])
                _pair(mask.get('offset'))
                path = _resource(mask.get('png'))
                if not path.startswith(PROPS):
                    raise ValueError('crown mask must be inside the kit prop art directory')
                _add(bindings, path, 'shadow_operations', owner)
    return bindings


def inspect(path: str, read_committed_blob) -> dict:
    """Return diagnostic routing only; missing or unknown kit metadata stays unresolved.

    ``read_committed_blob(path)`` returns regular committed JSON bytes, recording
    its own ref/blob/mode/hash evidence, or raises a read error. Existing metadata
    recipe hashes are not output hashes: generation freshness is not assessed.
    """
    result = dict(classification='ordinary', representation=None, owners=[],
                  freshness='not_assessed', obligations=[], errors=[])
    if not path.startswith((TERRAIN, PROPS)):
        return result
    result['classification'] = 'unresolved'
    result['obligations'] = [
        'Establish current producer/output freshness separately; recipe hashes do not attest output bytes.',
        'Review the decoded/composed material or owner shadow in its legal scene context.',
        'Retain applicable library gates, reference comparison, independent review and Matt approval.',
    ]
    metadata = MANIFEST if path.startswith(TERRAIN) else INDEX
    try:
        raw = read_committed_blob(metadata)
        value = _dict(json.loads(raw, object_pairs_hook=_object, parse_constant=_constant))
        bindings = _terrain(value) if metadata == MANIFEST else _props(value)
        if path not in bindings:
            raise ValueError('no direct committed kit binding; indirect resources are not interpreted')
        representation, owner = bindings[path]
        result.update(representation=representation, owners=[owner])
        if representation == 'physical_sprite':
            result.update(classification='ordinary', obligations=[])
        else:
            result['classification'] = 'context_required'
    except (OSError, ValueError, TypeError, KeyError) as exc:
        result['errors'].append(str(exc))
    return result
