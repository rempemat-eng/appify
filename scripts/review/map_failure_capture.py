"""R6 replacement map diagnostics: committed source, portable first-failure evidence.

This is NEW recovery evidence, never a recreation of missing R4/R5 bytes. Imports
are stdlib-only until an explicitly allocated worker starts. ``plan`` describes
the single conditional recovery sequence; ``run`` requires a reviewed allocation
JSON, a fresh external output directory and an exact committed source head.

Cheap codec/schema/ABI/source checks precede the expensive producer. The REAL T
inventory only exists after data_stage reaches PRE-CROSSROADS AFTER RESTORE.
Capture core/trials precede optional snapshots. Original returns/errors remain
original; target125/19/20-23 is comparison evidence, never a replacement return.

Every phase packages source, allocation, command, versions, log, partial inputs
and results. A local ZIP is NOT a completed handoff: upload it and have another
workspace/reviewer retrieve and verify its actual bytes before proceeding.
"""
from collections import OrderedDict
from contextlib import ExitStack, contextmanager
from pathlib import Path
from unittest.mock import patch
import argparse
import ast
import copy
import datetime
import fcntl
import hashlib
import json
import math
import os
import platform
import resource
import runpy
import secrets
import selectors
import shutil
import signal
import stat
import subprocess
import sys
import tempfile
import threading
import time
import traceback
import unittest
import zipfile

REPO = Path(__file__).resolve().parents[2]
BLOCKOUT = REPO / 'docs/vision/research/blockout'
BASE = 'aeb3bb3b971ad3ef1567977a1428f4d1dc24c10c'
BASE_TREE = '2151673d74346d51a969f2213e0a62e9ba0f48cd'
SCHEMA = 'mygame.map_failure_capture/r6'
SEED = 'crc32-utf8/355; explicit town seeds retained'
CROSS = (5632, 2944, 7424, 4608)
NEON = (9600, 3904, 12544, 5888)
REQUIRED = ('K', 'K0', 'h', 'land', 'tiers_pre', 'street', 'used', 'taken', 'barrier', 'hardbar', 'keepout', 'slope')
OBJECT_FIELDS = {'K', 'K0', 'ground0'}
MASK_FIELDS = ('taken', 'street', 'used', 'barrier', 'hardbar', 'keepout')
EXPECTED_ERROR = 'Crossroads: authored street blocks cannot place [20, 21, 22, 23]'
MAX_RAW = 24 * 1024**2
MAX_JSON = 8 * 1024**2
MAX_PACKET = 32 * 1024**2
MAX_OWNED = 128 * 1024**2
MAX_ZIP = 64 * 1024**2
MAX_LOG = 16 * 1024**2
MAX_TRIALS = 5000
PRODUCTION_BLOBS = {'docs/vision/research/blockout/geo5.py': 'cfd2ab2a2d9d214448f4bd6441c9e547426c7de0', 'docs/vision/research/blockout/geo52.py': '784421e4b51386d23cd846932fbb63f8e6657a37', 'docs/vision/research/blockout/geo53.py': 'a0ddf6ae347a6be69c525cde97e656122bf6dcfb', 'docs/vision/research/blockout/geo54.py': 'e4913ae98346b8c3590ba41a87ab7f7f831a430e', 'docs/vision/research/blockout/geo55.py': '4e198d81f178b6530c714dd39d6f9078d2b11354', 'docs/vision/research/blockout/map53.py': '810d8f863da7902c148c734e04be9abb8f9f55ef', 'docs/vision/research/blockout/map54.py': 'aaa2eeb19dbe158acc8767d556fbacace92a0b6b', 'docs/vision/research/blockout/map55.py': '280fbe8d61a0fec40e2a3d876d92d41d8af33404', 'docs/vision/research/blockout/town_plans.py': 'f643cdd362d7d81e81f3d9d5eb462d78271d4ebb', 'docs/vision/research/blockout/towns55.py': 'dfd90fd6e9c9aa2ec3e32612935a2b399275683a', 'game/data/plans/crossroads.json': '0ec43431f13f5086a5a96e997b60c7eccb7cab30', 'scripts/review/town_plan.py': 'f330fa94673a9d2cea5de49e971f5b6eefe7be08'}
N = None
CORRECTION_TOWNS_BLOB = 'f23c793baf4a3b937a223c2a9fd2ac2786442f94'


class CaptureError(RuntimeError):
    pass


class MissingInput(CaptureError):
    pass


class ReturnedBoundary(RuntimeError):
    """External stop after an ORIGINAL return; never labelled producer failure."""


def now():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as handle:
        while block := handle.read(1024**2):
            h.update(block)
    return h.hexdigest()


def plain(value):
    if N is not None and isinstance(value, N.generic):
        return plain(value.item())
    if type(value) in (str, bool, int) or value is None:
        return value
    if type(value) is float and math.isfinite(value):
        return value
    if isinstance(value, (list, tuple)):
        return [plain(item) for item in value]
    if isinstance(value, dict) and all(type(k) is str for k in value):
        return {k: plain(v) for k, v in value.items()}
    raise CaptureError('nonliteral JSON metadata: ' + type(value).__name__)


def json_read(path):
    path = Path(path)
    if path.is_symlink() or not path.is_file() or path.stat().st_size > MAX_JSON:
        raise CaptureError('unsafe/oversized JSON: ' + str(path))
    return json.loads(path.read_text())


def owned_blocks(folder, recursive=True):
    """Sample only mutable owned output; a vanished entry is no longer allocated.

    One lstat per entry avoids is_file/stat races and refuses symlinks rather
    than following them. Missing roots, permissions and other I/O still fail.
    This is never used to verify canonical source or portable input identities.
    """
    root = Path(folder)
    if stat.S_ISLNK(root.lstat().st_mode):
        raise CaptureError('owned output root symlink refused')
    pending, total = [root], 0
    while pending:
        directory = pending.pop()
        try:
            for path in directory.iterdir():
                try:
                    metadata = path.lstat()
                except FileNotFoundError:
                    continue  # Actual mutable entry vanished after enumeration.
                if stat.S_ISLNK(metadata.st_mode):
                    raise CaptureError('owned output symlink refused: ' + str(path))
                if stat.S_ISREG(metadata.st_mode):
                    total += metadata.st_blocks * 512
                elif recursive and stat.S_ISDIR(metadata.st_mode):
                    pending.append(path)
        except FileNotFoundError:
            if directory == root:
                raise
            # A previously observed owned child directory was removed.
    return total


@contextmanager
def sampling_boundary(path, identity, exclusive=False):
    """Bound only deliberate receiving probes against the outer strict scan.

    Each participant opens the precreated inode independently. The raw sampler
    stays unlocked and strict, including while a probe asserts its refusal.
    A busy/missing/replaced lock is a failure, never a clean skipped sample.
    """
    path = Path(path)
    if (not path.is_absolute() or type(identity) not in (list, tuple) or len(identity) != 2
            or any(type(value) is not int or value < 0 for value in identity)):
        raise CaptureError('invalid owned sampling coordination')
    descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC)
    def same_inode():
        current, opened = path.lstat(), os.fstat(descriptor)
        if (not stat.S_ISREG(current.st_mode) or not stat.S_ISREG(opened.st_mode)
                or [current.st_dev, current.st_ino] != list(identity)
                or [opened.st_dev, opened.st_ino] != list(identity)):
            raise CaptureError('owned sampling coordination inode changed')
    try:
        same_inode()
        deadline = time.monotonic() + .25
        operation = (fcntl.LOCK_EX if exclusive else fcntl.LOCK_SH) | fcntl.LOCK_NB
        while True:
            try:
                fcntl.flock(descriptor, operation)
                break
            except BlockingIOError:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise CaptureError('owned sampling coordination deadline exceeded')
                time.sleep(min(.005, remaining))
        same_inode()
        acquired = time.monotonic()
        yield
        same_inode()
        if exclusive and time.monotonic() - acquired > .25:
            raise CaptureError('owned sampling probe held beyond deadline')
    finally:
        os.close(descriptor)  # Closing this independent description releases its flock.


def coordinated_owned_blocks(folder, path, identity):
    if Path(path).parent != Path(folder):
        raise CaptureError('owned sampling lock must stay inside the sampled root')
    with sampling_boundary(path, identity):
        return owned_blocks(folder)


def write_json(path, value):
    """Atomic partial/final metadata, bounded BEFORE committing the new state."""
    path = Path(path)
    data = (json.dumps(plain(value), sort_keys=True, indent=2, allow_nan=False) + '\n').encode()
    if len(data) > MAX_JSON:
        raise CaptureError('JSON bound exceeded')
    temp = path.with_name(path.name + '.tmp')
    created = False
    try:
        with temp.open('xb') as handle:
            created = True
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        if owned_blocks(path.parent) > MAX_PACKET:
            raise CaptureError('packet allocation bound exceeded before metadata commit')
        temp.replace(path)
    finally:
        if created:
            try:
                temp.unlink(missing_ok=True)
            except OSError:
                pass  # Never replace the original write/commit error during cleanup.


def best_effort_json(path, value):
    try:
        write_json(path, value)
        return True
    except Exception:
        return False


def numeric(paths=()):
    global N
    for path in reversed(paths):
        if not Path(path).is_dir():
            raise CaptureError('approved numeric dependency path unavailable')
        sys.path.insert(0, str(path))
    import numpy
    import scipy
    import skimage
    import PIL
    N = numpy
    return {'numpy': numpy.__version__, 'scipy': scipy.__version__,
            'scikit-image': skimage.__version__, 'Pillow': PIL.__version__}


def primitive(array, key):
    if array.nbytes > MAX_RAW:
        raise CaptureError('array pointer/raw bound exceeded')
    if array.dtype.kind == 'O':
        if key not in OBJECT_FIELDS or any(type(v) not in (str, N.str_) for v in array.flat):
            raise CaptureError('unknown/nonliteral object array: ' + key)
        width = max(1, max((len(v) for v in array.flat), default=0))
        if width * 4 * array.size > MAX_RAW:
            raise CaptureError('projected string bound exceeded')
        result = array.astype(str)
        if not N.array_equal(result, array):
            raise CaptureError('literal terrain conversion changed values')
    elif array.dtype.kind in 'buifUS':
        result = array.copy()
    else:
        raise CaptureError('nonprimitive dtype: ' + str(array.dtype))
    return result


def inventory(T):
    shape = T['K'].shape
    rows = []
    for key, value in sorted(T.items()):
        if isinstance(value, N.ndarray) and value.shape == shape:
            rows.append(('T', key, value))
    for container in ('barriers', 'river_masks'):
        if not isinstance(T.get(container), dict):
            raise MissingInput('actual nested mask dictionary missing: ' + container)
        for key, value in sorted(T[container].items()):
            if not isinstance(value, N.ndarray) or value.shape != shape:
                raise MissingInput('actual nested mask shape: ' + container + '/' + key)
            rows.append((container, key, value))
    if not set(REQUIRED).issubset({key for container, key, _ in rows if container == 'T'}):
        raise MissingInput('actual required arrays absent')
    return rows


def snapshot(T, box, path, required_only=False):
    x0, y0, x1, y1 = box
    H, W = T['K'].shape
    if any(v % 8 for v in box) or not (0 <= x0 < x1 <= W * 8 and 0 <= y0 < y1 <= H * 8):
        raise MissingInput('snapshot leaves actual global dimensions')
    cells = (x1 - x0) * (y1 - y0) // 64
    if cells > (100000 if required_only else 50000):
        raise CaptureError('crop cell bound exceeded')
    sources = [('T', k, T[k]) for k in REQUIRED] if required_only else inventory(T)
    arrays, records, total = {}, [], 0
    for index, (container, key, source) in enumerate(sources):
        if not isinstance(source, N.ndarray) or source.shape != (H, W):
            raise MissingInput('snapshot source shape mismatch')
        value = primitive(source[y0 // 8:y1 // 8, x0 // 8:x1 // 8], key)
        total += value.nbytes
        if total > MAX_RAW:
            raise CaptureError('raw snapshot total bound exceeded')
        name = f'a{index:03d}'
        arrays[name] = value
        records.append({'archive_key': name, 'container': container, 'source_key': key,
                        'shape': list(value.shape), 'dtype': value.dtype.str,
                        'source_dtype': str(source.dtype), 'bytes': value.nbytes,
                        'sha256': hashlib.sha256(value.tobytes(order='C')).hexdigest()})
    temp = Path(path).with_name(Path(path).name + '.tmp')
    with temp.open('xb') as handle:
        N.savez_compressed(handle, **arrays)
        handle.flush()
        os.fsync(handle.fileno())
    if owned_blocks(Path(path).parent, recursive=False) > MAX_PACKET:
        temp.unlink()
        raise CaptureError('packet bound exceeded before NPZ commit')
    temp.replace(path)
    return {'kind': 'initial_neon' if required_only else 'consumer',
            'file': Path(path).name, 'bytes': Path(path).stat().st_size, 'sha256': sha(path),
            'box_px': list(box), 'global_shape': [H, W], 'raw_bytes': total, 'arrays': records}


def validate_archive(path, meta):
    """Stdlib primitive-only header/data validation BEFORE any np.load call."""
    kind = meta.get('kind')
    if kind not in ('consumer', 'initial_neon'):
        raise CaptureError('unknown snapshot context')
    box, global_shape = meta.get('box_px'), meta.get('global_shape')
    if (not isinstance(box, (list, tuple)) or len(box) != 4
            or any(type(v) is not int or v % 8 for v in box)
            or not isinstance(global_shape, (list, tuple)) or len(global_shape) != 2
            or any(type(v) is not int or v <= 0 for v in global_shape)):
        raise CaptureError('invalid crop/global shape metadata')
    x0, y0, x1, y1 = box
    H, W = global_shape
    crop_shape = [(y1 - y0) // 8, (x1 - x0) // 8]
    if (not (0 <= x0 < x1 <= W * 8 and 0 <= y0 < y1 <= H * 8)
            or math.prod(crop_shape) > (100000 if kind == 'initial_neon' else 50000)):
        raise CaptureError('crop leaves actual global bounds/context limit')
    records = meta.get('arrays')
    if not isinstance(records, list) or not records:
        raise CaptureError('missing snapshot array descriptors')
    identities = set()
    for record in records:
        container, key = record.get('container'), record.get('source_key')
        if container not in ('T', 'barriers', 'river_masks') or type(key) is not str or not key:
            raise CaptureError('invalid semantic array identity')
        identity = (container, key)
        if identity in identities:
            raise CaptureError('duplicate semantic array identity')
        identities.add(identity)
        if record.get('shape') != crop_shape:
            raise CaptureError('array shape differs from crop/global context')
        if (record.get('source_dtype') == 'object'
                and (container != 'T' or key not in OBJECT_FIELDS
                     or not isinstance(record.get('dtype'), str) or record['dtype'][1:2] != 'U')):
            raise CaptureError('invalid object-string semantic descriptor')
    required = {('T', key) for key in REQUIRED}
    if not required.issubset(identities) or (kind == 'initial_neon' and identities != required):
        raise CaptureError('required snapshot context inventory mismatch')
    if (Path(path).is_symlink() or Path(path).stat().st_size != meta['bytes']
            or sha(path) != meta['sha256']):
        raise CaptureError('snapshot file identity mismatch')
    expected = {r['archive_key'] + '.npy': r for r in records}
    if len(expected) != len(records):
        raise CaptureError('duplicate primitive archive key')
    total = 0
    with zipfile.ZipFile(path) as archive:
        if set(archive.namelist()) != set(expected) or len(archive.infolist()) != len(expected):
            raise CaptureError('archive inventory mismatch')
        for info in archive.infolist():
            record = expected[info.filename]
            if info.file_size > MAX_RAW + 65548:
                raise CaptureError('NPY allocation bound exceeded')
            with archive.open(info) as stream:
                prefix = stream.read(8)
                if prefix[:6] != b'\x93NUMPY' or prefix[6:] not in (b'\x01\x00', b'\x02\x00', b'\x03\x00'):
                    raise CaptureError('invalid NPY prefix')
                n = 2 if prefix[6:] == b'\x01\x00' else 4
                length = stream.read(n)
                if len(length) != n:
                    raise CaptureError('truncated NPY header length')
                size = int.from_bytes(length, 'little')
                if not 0 < size <= 65536:
                    raise CaptureError('NPY header bound exceeded')
                header = ast.literal_eval(stream.read(size).decode('utf-8' if prefix[6:] == b'\x03\x00' else 'latin1').strip())
                if set(header) != {'descr', 'fortran_order', 'shape'} or header['fortran_order'] is not False:
                    raise CaptureError('unsupported NPY structure/order')
                dtype = header['descr']
                if not isinstance(dtype, str) or len(dtype) < 3 or dtype[0] not in '<>|=' or dtype[1] not in 'buifUS' or not dtype[2:].isdigit():
                    raise CaptureError('object/structured/nonprimitive dtype refused')
                shape = header['shape']
                if not isinstance(shape, tuple) or len(shape) != 2 or any(type(v) is not int or v <= 0 for v in shape):
                    raise CaptureError('unsafe NPY shape')
                if list(shape) != record['shape'] or dtype != record['dtype'] or math.prod(shape) > 100000:
                    raise CaptureError('primitive descriptor mismatch')
                width = int(dtype[2:]) * (4 if dtype[1] == 'U' else 1)
                scalar_width = int(dtype[2:])
                if ((dtype[1] in 'ui' and scalar_width not in (1, 2, 4, 8))
                        or (dtype[1] == 'b' and scalar_width != 1)
                        or (dtype[1] == 'f' and scalar_width not in (2, 4, 8, 16))):
                    raise CaptureError('unsupported primitive item width')
                count = math.prod(shape) * width
                total += count
                if width <= 0 or total > MAX_RAW or count != record['bytes'] or info.file_size != 8 + n + size + count:
                    raise CaptureError('primitive byte bound/count mismatch')
                h = hashlib.sha256()
                remaining = count
                while remaining:
                    data = stream.read(min(65536, remaining))
                    if not data:
                        raise CaptureError('truncated primitive array')
                    remaining -= len(data)
                    h.update(data)
                if stream.read(1) or h.hexdigest() != record['sha256']:
                    raise CaptureError('primitive bytes/hash mismatch')
    if total != meta['raw_bytes']:
        raise CaptureError('primitive total mismatch')
    return True


def load_snapshot(folder, meta):
    validate_archive(Path(folder) / meta['file'], meta)
    result = {}
    with N.load(Path(folder) / meta['file'], allow_pickle=False) as archive:
        for record in meta['arrays']:
            value = archive[record['archive_key']]
            if value.dtype.hasobject:
                raise CaptureError('unsafe loaded object dtype')
            if record['source_dtype'] == 'object':
                value = value.astype(object)  # Restore mutable object-string semantics; no Unicode truncation.
            result[(record['container'], record['source_key'])] = value
    return result


def array_facts(town, a, b, c, d, kinds, returned):
    T = town.T
    item = {'return': bool(returned), 'bounds_yxyx': [a, b, c, d],
            'hand': bool(getattr(town, '_hand', False)), 'kinds': sorted(kinds),
            'level': town.level, 'slope_max': town.slope_max}
    H, W = T['K'].shape
    if a < 1 or b < 1 or c >= H - 1 or d >= W - 1:
        item['global_bounds_refusal'] = True
        return item
    ground = T['K'][a:c, b:d]
    names, counts = N.unique(ground, return_counts=True)
    item['ground'] = {str(k): int(v) for k, v in zip(names, counts)}
    masks = {k: T[k][a:c, b:d] for k in MASK_FIELDS}
    masks['nonbuildable'] = ~N.isin(ground, list(kinds))
    item['masks'] = {k: {'shape': list(v.shape), 'true': int(v.sum()),
                         'packbits_little_hex': N.packbits(v, bitorder='little').tobytes().hex()} for k, v in masks.items()}
    item['tiers'] = [int(T['tiers_pre'][a:c, b:d].min()), int(T['tiers_pre'][a:c, b:d].max())]
    item['max_slope'] = float(T['slope'][a:c, b:d].max())
    return item


class Recorder:
    def __init__(self, tw, folder, replay=False):
        self.tw, self.folder, self.replay = tw, Path(folder), replay
        self.events, self.groups, self.errors, self.supports = [], [], [], []
        self.active = None
        self.target_active = False
        self.terrain = None
        self.town = None
        self.core = {'schema': SCHEMA, 'stage': 'INCOMPLETE_BEFORE_CONSUMER', 'complete': False,
                     'world_state': 'NOT_COMPLETED', 'replacement_evidence': True, 'errors': []}
        self.originals = {}

    def save_core(self):
        self.core['errors'] = list(self.errors)
        write_json(self.folder / 'capture.json', self.core)

    def best_effort(self, operation):
        try:
            return operation()
        except Exception as exc:
            self.errors.append({'type': type(exc).__name__, 'message': str(exc)})
            try:
                self.save_core()
            except Exception:
                pass
            return None

    def support(self, name, rect, halo=0):
        a, b, c, d = map(int, rect)
        x0, y0, x1, y1 = CROSS
        known = y0 // 8 <= a - halo and b - halo >= x0 // 8 and c + halo <= y1 // 8 and d + halo <= x1 // 8
        self.supports.append({'operation': name, 'bounds_yxyx': [a, b, c, d], 'halo': halo, 'captured': bool(known)})
        if self.replay and not known:
            raise MissingInput('active dependency/halo leaves captured crop: ' + name)

    def row(self, frame):
        if frame.f_code.co_name != '_feedback_rows' or Path(frame.f_code.co_filename).resolve() != Path(self.tw.__file__).resolve():
            raise CaptureError('original frontage frame absent')
        q = frame.f_locals
        result = {k: plain(q[k]) for k in ('row_index', 'axis', 'fixed', 'lo', 'hi', 'side', 'name', 'edge', 'pos', 'row_target')}
        result['queue'] = [int(r[0]) for r in q['queue']]
        result['selected_street'] = {k: plain(q['street'][k]) for k in ('name', 'cls', 'width_cells', 'width_px', 'pts', 'route', 'metric')}
        return result

    def begin(self, T):
        self.terrain = T
        self.core.update(stage='PRE_CROSSROADS_AFTER_RESTORE_PARTIAL', global_shape=list(T['K'].shape),
                         town_dimensions=[self.tw.H, self.tw.W], cell_px=int(self.tw.CELL),
                         before_routes=plain(T['route_px']), before_rivers=plain(T['river_px']),
                         palette=plain(self.tw.g.COL),
                         before_metadata={k: plain(T[k]) for k in ('hand_fail', 'levelled', 'authored_protected_cells') if k in T})
        self.save_core()  # Global metadata survives a later unknown dtype or NPZ failure.
        rows = inventory(T)
        write_json(self.folder / 'actual-inventory.json', {'stage': 'REAL T AT PRE_CROSSROADS AFTER RESTORE',
            'arrays': [{'container': c, 'key': k, 'shape': list(v.shape), 'dtype': str(v.dtype)} for c, k, v in rows]})
        self.core['before'] = snapshot(T, CROSS, self.folder / 'before.npz')
        self.save_core()
        if not self.replay:
            self.core['initial_neon'] = snapshot(T, NEON, self.folder / 'initial-neon.npz', required_only=True)
            self.core['initial_neon']['stage'] = 'ACTUAL INITIAL NEON CROP AT PRE-CROSSROADS; NO NEON CONSUMER RUN'
            self.save_core()

    def finish(self, error, returned):
        T = self.terrain
        queue = None
        tb = error.__traceback__ if error else None
        while tb is not None:
            frame = tb.tb_frame
            if frame.f_code.co_name == '_feedback_rows' and Path(frame.f_code.co_filename).resolve() == Path(self.tw.__file__).resolve():
                queue = [int(r[0]) for r in frame.f_locals['queue']]
            tb = tb.tb_next
        town = self.town or returned
        self.core.update(stage='FAILURE_CORE_PARTIAL' if error else 'ORIGINAL_RETURN_CORE_PARTIAL',
                         world_state='FAILED' if error else 'NOT_COMPLETED',
                         producer_outcome={'kind': 'EXCEPTION' if error else 'RETURN',
                             'type': type(error).__name__ if error else None, 'message': str(error) if error else None},
                         queued_ids=queue, trial_count=len(self.events), supports=self.supports,
                         after_routes=plain(T['route_px']), after_rivers=plain(T['river_px']),
                         after_metadata={k: plain(T[k]) for k in ('hand_fail', 'levelled', 'authored_protected_cells') if k in T},
                         buildings=plain(town.buildings) if town else None, streets=plain(town.streets) if town else None,
                         spaces=plain(town.spaces) if town else None, outskirts=plain(town.outskirts) if town else None)
        self.save_core()  # Failure/core is durable BEFORE trials and optional snapshots.
        write_json(self.folder / 'trials.json', {'groups': self.groups, 'events': self.events, 'complete': not self.errors})
        self.core['trials'] = {'file': 'trials.json', 'sha256': sha(self.folder / 'trials.json')}
        self.save_core()
        self.core['after'] = snapshot(T, CROSS, self.folder / 'after.npz')
        self.core['comparison_target'] = {'trial125': len(self.events) == 125,
            'records19': town is not None and len(town.buildings) == 19,
            'queue20_23': queue == [20, 21, 22, 23], 'original_error': type(error) is ValueError and str(error) == EXPECTED_ERROR}
        complete = (not self.errors and self.core.get('before') is not None
                    and all('return' in e and e['free'] for e in self.events)
                    and all(q['captured'] for q in self.supports))
        self.core.update(stage='COMPLETE' if complete else 'INCOMPLETE', complete=complete)
        self.save_core()  # Complete state is committed LAST; original error remains original.

    def __enter__(self):
        tw, observer = self.tw, self
        self.stack = ExitStack()
        self.originals = {'cross': tw._feedback_crossroads, 'rows': tw._feedback_rows,
                          'hand': tw.Town.hand, 'free': tw.Town.free, 'band': tw.band_mask,
                          'lm': tw._lm, 'fixed': tw.Town.fixed, 'square': tw.Town.square, 'yard': tw.Town.yard}

        def cross(T, X):
            previous, observer.target_active = observer.target_active, True
            try:
                observer.best_effort(lambda: observer.begin(T))
                try:
                    returned = observer.originals['cross'](T, X)
                except BaseException as error:
                    observer.best_effort(lambda: observer.finish(error, None))
                    raise  # Never substitute an observer/serializer exception for the original.
                observer.best_effort(lambda: observer.finish(None, returned))
                raise ReturnedBoundary('external stop AFTER original Crossroads return; no world export')
            finally:
                observer.target_active = previous

        def rows(town, records, fronts, **kwargs):
            if not observer.target_active:
                return observer.originals['rows'](town, records, fronts, **kwargs)
            observer.town = town
            observer.best_effort(lambda: observer.groups.append({'records': plain(records), 'rows': plain(fronts), 'kwargs': plain(kwargs)}))
            return observer.originals['rows'](town, records, fronts, **kwargs)

        def hand(town, *args, **kwargs):
            if not observer.target_active:
                return observer.originals['hand'](town, *args, **kwargs)
            trial = None
            row_frame = sys._getframe(1)
            def begin_trial():
                if len(observer.events) >= MAX_TRIALS:
                    raise CaptureError('trial bound exceeded')
                value = {'args': plain(args), 'kwargs': plain(kwargs), 'row': observer.row(row_frame),
                         'count_before': town.count(), 'cap': town.cap, 'free': []}
                observer.events.append(value)
                return value
            trial = observer.best_effort(begin_trial)
            previous, observer.active = observer.active, trial
            try:
                result = observer.originals['hand'](town, *args, **kwargs)
                if trial is not None:
                    trial['return'] = bool(result)
                    if result:
                        observer.best_effort(lambda: trial.__setitem__('placed', plain(town.buildings[-1])))
                return result
            finally:
                observer.active = previous

        def free(town, a, b, c, d, kinds=tw.BUILDABLE):
            if not observer.target_active:
                return observer.originals['free'](town, a, b, c, d, kinds)
            H, W = town.T['K'].shape
            if not (a < 1 or b < 1 or c >= H - 1 or d >= W - 1):
                observer.support('free-and-put-used-halo', (a, b, c, d), 1)
            result = observer.originals['free'](town, a, b, c, d, kinds)
            if observer.active is not None:
                observer.best_effort(lambda: observer.active['free'].append(array_facts(town, a, b, c, d, kinds, result)))
            return result

        def band(line, width, metric):
            result = observer.originals['band'](line, width, metric)
            if not observer.target_active:
                return result
            rr, cc = N.nonzero(result)
            if len(rr):
                observer.support('street-band-' + metric, (rr.min(), cc.min(), rr.max() + 1, cc.max() + 1), max(2, math.ceil(width / 2) + 2))
            return result

        def lm(line, width):
            result = observer.originals['lm'](line, width)
            if not observer.target_active:
                return result
            rr, cc = N.nonzero(result)
            if len(rr):
                observer.support('route-mask', (rr.min(), cc.min(), rr.max() + 1, cc.max() + 1), 1)
            return result

        def fixed(town, records, *args, **kwargs):
            if not observer.target_active:
                return observer.originals['fixed'](town, records, *args, **kwargs)
            for x, y, w, h, *_ in records:
                observer.support('fixed', (y // 8, x // 8, (y + h) // 8, (x + w) // 8))
            return observer.originals['fixed'](town, records, *args, **kwargs)

        def square(town, cx, cy, rx, ry, *args, **kwargs):
            if not observer.target_active:
                return observer.originals['square'](town, cx, cy, rx, ry, *args, **kwargs)
            observer.support('square', (round((cy - ry) / 8), round((cx - rx) / 8), round((cy + ry) / 8), round((cx + rx) / 8)))
            return observer.originals['square'](town, cx, cy, rx, ry, *args, **kwargs)

        def yard(town, x0, y0, x1, y1, *args, **kwargs):
            if not observer.target_active:
                return observer.originals['yard'](town, x0, y0, x1, y1, *args, **kwargs)
            observer.support('yard', (y0 // 8, x0 // 8, y1 // 8, x1 // 8))
            return observer.originals['yard'](town, x0, y0, x1, y1, *args, **kwargs)

        for obj, name, value in ((tw, '_feedback_crossroads', cross), (tw, '_feedback_rows', rows),
                (tw.Town, 'hand', hand), (tw.Town, 'free', free), (tw, 'band_mask', band), (tw, '_lm', lm),
                (tw.Town, 'fixed', fixed), (tw.Town, 'square', square), (tw.Town, 'yard', yard)):
            self.stack.enter_context(patch.object(obj, name, value))
        return self

    def __exit__(self, *args):
        self.stack.close()
        return False


class NoiseCache(OrderedDict):
    """Same four-entry read-only cache policy; no production noise arithmetic edit."""
    def __getitem__(self, key):
        value = super().__getitem__(key)
        self.move_to_end(key)
        return value

    def __setitem__(self, key, value):
        value.flags.writeable = False
        super().__setitem__(key, value)
        self.move_to_end(key)
        while len(self) > 4:
            self.popitem(last=False)


class UsagePulse:
    """Worker SELF measurements avoid assuming mounted /proc uses our PID namespace."""
    def __init__(self, folder, nonce):
        self.path, self.nonce, self.sequence = Path(folder) / 'usage.json', nonce, 0
        self.done, self.error = threading.Event(), None
        self.thread = None

    def sample(self, terminal=False):
        value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        if value <= 0:
            raise CaptureError('positive worker SELF RSS unavailable')
        self.sequence += 1
        write_json(self.path, {'pid': os.getpid(), 'nonce': self.nonce, 'sequence': self.sequence,
            'monotonic': time.monotonic(), 'peak_rss_bytes': int(value * 1024), 'terminal': bool(terminal)})

    def loop(self):
        while not self.done.wait(.5):
            try:
                self.sample()
            except Exception as error:
                self.error = str(error)
                return

    def start(self):
        self.sample()
        self.thread = threading.Thread(target=self.loop, daemon=True)
        self.thread.start()

    def close(self):
        self.done.set()
        self.thread.join(timeout=2)
        if self.thread.is_alive() or self.error:
            raise CaptureError('worker resource telemetry did not finish: ' + str(self.error))
        self.sample(terminal=True)


def usage_record(folder, pid, nonce, start, terminal=False):
    record = json_read(Path(folder) / 'usage.json')
    clock = time.monotonic()
    if record.get('pid') != pid or record.get('nonce') != nonce:
        raise CaptureError('worker resource identity mismatch')
    if type(record.get('peak_rss_bytes')) is not int or record['peak_rss_bytes'] <= 0 or type(record.get('sequence')) is not int or record['sequence'] < 1:
        raise CaptureError('worker resource measurement unavailable')
    sample = record.get('monotonic')
    if type(sample) not in (float, int) or not math.isfinite(sample) or not start - 1 <= sample <= clock + 1 or clock - sample > 5:
        raise CaptureError('worker resource sample stale')
    if terminal and record.get('terminal') is not True:
        raise CaptureError('worker final resource sample not terminal')
    return record


def shared_anon():
    for line in Path('/sys/fs/cgroup/memory.stat').read_text().splitlines():
        if line.startswith('anon '):
            return int(line.split()[1])
    raise CaptureError('shared anonymous-memory observation unavailable')


def source_files():
    files = list(BLOCKOUT.glob('*.py'))
    files += [REPO / 'scripts/review/town_plan.py', REPO / 'game/data/plans/crossroads.json',
              Path(__file__), Path(__file__).with_name('test_map_failure_capture.py')]
    return sorted(set(files))


def git(*args):
    return subprocess.check_output(['git', '-C', str(REPO), *args], env={**os.environ, 'GIT_OPTIONAL_LOCKS': '0'}).decode().strip()


def source_guard(overrides=None):
    overrides = overrides or {}
    permitted = {'docs/vision/research/blockout/towns55.py', 'docs/vision/research/blockout/geo55.py'}
    if not set(overrides).issubset(permitted) or not PRODUCTION_BLOBS:
        raise CaptureError('unknown production override or unpinned source')
    for name, expected in {**PRODUCTION_BLOBS, **overrides}.items():
        data = (REPO / name).read_bytes()
        actual = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
        if actual != expected:
            raise CaptureError('production source differs from frozen R6 baseline: ' + name)
    return {'head': git('rev-parse', 'HEAD'), 'tree': git('rev-parse', 'HEAD^{tree}'),
            'status': git('status', '--porcelain=v1'),
            'source_sha256': {str(p.relative_to(REPO)): sha(p) for p in source_files()}}


def bundle(folder):
    """Always package existing partial evidence; no promise survives SIGKILL of this controller."""
    folder = Path(folder)
    archive = folder.parent / (folder.name + '.zip')
    if archive.exists():
        raise CaptureError('portable artifact already exists; no implicit overwrite')
    records = []
    for path in sorted(folder.rglob('*')):
        if path.is_symlink():
            raise CaptureError('portable evidence symlink refused')
        if path.is_file():
            records.append({'path': path.relative_to(folder).as_posix(), 'bytes': path.stat().st_size, 'sha256': sha(path)})
    manifest = {'schema': SCHEMA, 'kind': 'NEW_R6_REPLACEMENT', 'complete_handoff': False,
                'publication_and_independent_byte_retrieval_required': True, 'files': records}
    temp = archive.with_name(archive.name + '.tmp')
    with zipfile.ZipFile(temp, 'x', compression=zipfile.ZIP_DEFLATED) as output:
        output.writestr('PORTABLE-MANIFEST.json', json.dumps(manifest, sort_keys=True, indent=2) + '\n')
        for row in records:
            output.write(folder / row['path'], row['path'])
    if temp.stat().st_size > MAX_ZIP:
        raise CaptureError('portable artifact bound exceeded; preserve partial archive')
    temp.replace(archive)
    return {'file': str(archive), 'bytes': archive.stat().st_size, 'sha256': sha(archive),
            'complete_handoff': False, 'required_next': 'upload; independent reviewer retrieves and verifies actual ZIP bytes'}


def verify_bundle(path, expected):
    if Path(path).is_symlink() or Path(path).stat().st_size > MAX_ZIP or sha(path) != expected:
        raise CaptureError('portable file identity/bound mismatch')
    with zipfile.ZipFile(path) as archive:
        if len(archive.infolist()) > 256 or sum(p.file_size for p in archive.infolist()) > MAX_OWNED:
            raise CaptureError('portable member bound exceeded')
        if archive.getinfo('PORTABLE-MANIFEST.json').file_size > MAX_JSON:
            raise CaptureError('portable manifest bound exceeded')
        manifest = json.loads(archive.read('PORTABLE-MANIFEST.json'))
        rows = {r['path']: r for r in manifest['files']}
        if len(rows) != len(manifest['files']) or len(archive.namelist()) != len(rows) + 1 or set(archive.namelist()) != set(rows) | {'PORTABLE-MANIFEST.json'}:
            raise CaptureError('portable inventory mismatch')
        for name, row in rows.items():
            if Path(name).is_absolute() or '..' in Path(name).parts or '\\' in name or Path(name).as_posix() != name:
                raise CaptureError('unsafe portable path')
            data = archive.read(name)
            if len(data) != row['bytes'] or hashlib.sha256(data).hexdigest() != row['sha256']:
                raise CaptureError('portable member mismatch')
    return {'retrieved_bytes_verified': True, 'sha256': expected, 'files': len(rows), 'replacement': True}


def plan():
    return {'schema': SCHEMA, 'state': 'REQUIRES_REVIEWED_EXECUTION_ALLOCATION',
        'history': 'Missing R4/R5 bytes remain unavailable; R6 is new evidence, not historical equality.',
        'sequence': ['committed two-file source + independent review', 'new cheap contracts/ABI/source pins',
            'fresh prospective first-failure capture + portable partial/final artifact',
            'UPLOAD and independent byte retrieval before handoff',
            'unchanged actual-input reproduction before geometry',
            'same-input measured correction and labelled Crossroads crop', 'full-world/all21-town/Neon-Cape later'],
        'capture_bounds': {'seconds': 900, 'cpus': 1, 'rss_gib': 3.2, 'address_gib': 6, 'shared_anon_gib': 4.2,
            'log_mib': 16, 'packet_mib': 32, 'raw_snapshot_mib': 24, 'owned_with_portable_mib': 128},
        'replay_crop_following_bound_proposal': {'seconds': 180, 'cpus': 1, 'rss_gib': 1, 'address_gib': 1.5},
        'scope': 'No production geometry/physics/default-v55 edits or generator export/render in this source step.',
        'cheap_inventory_limit': 'Codec/schema/known K/K0/ground0 tests first; real array inventory is captured only when actual T exists.',
        'cross_crop': CROSS, 'initial_neon_crop': NEON, 'seed': SEED,
        'handoff': 'Hashes/local paths are insufficient; a reviewer must retrieve actual portable bytes.'}


def retain_input_reference(folder, source):
    """Each later phase carries the actual comparison input and its source bytes."""
    source = Path(source).resolve()
    core = json_read(source / 'capture.json')
    if core.get('schema') != SCHEMA or core.get('complete') is not True:
        raise MissingInput('complete actual R6 input required before following phase')
    provenance = json_read(source / 'source-before.json')
    names = {'capture.json', 'trials.json', 'before.npz', 'after.npz', 'source-before.json',
             'versions.json', 'command.json', 'allocation.json'}
    names |= {key for key in ('initial-neon.npz', 'actual-inventory.json') if (source / key).is_file()}
    names |= {'source/' + name for name in provenance['source_sha256']}
    for name in sorted(names):
        if Path(name).is_absolute() or '..' in Path(name).parts:
            raise CaptureError('unsafe input reference path')
        original = source / name
        if original.is_symlink() or not original.is_file() or original.stat().st_size > MAX_RAW:
            raise MissingInput('actual input/source reference unavailable: ' + name)
        if name.startswith('source/') and sha(original) != provenance['source_sha256'][name[7:]]:
            raise CaptureError('actual input source byte mismatch')
        dest = Path(folder) / 'reference' / name
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(original.read_bytes())


def replay(folder, allocation):
    """Receiving consumer on actual R6 input, with UNKNOWN outside, no guessed routes."""
    original = Path(allocation['input']).resolve()
    meta = json_read(original / 'capture.json')
    if meta.get('schema') != SCHEMA or meta.get('complete') is not True:
        raise MissingInput('complete NEW R6 input packet required')
    if meta['before']['box_px'] != list(CROSS) or meta['cell_px'] != 8:
        raise MissingInput('actual input crop/cell mismatch')
    original_trials = json_read(original / 'trials.json')
    if sha(original / 'trials.json') != meta['trials']['sha256']:
        raise CaptureError('actual trial file changed')
    actual = load_snapshot(original, meta['before'])
    expected = load_snapshot(original, meta['after'])
    H, W = meta['global_shape']
    if [H, W] != meta['town_dimensions']:
        raise MissingInput('actual global dimensions differ')
    x0, y0, x1, y1 = CROSS
    sl = (slice(y0 // 8, y1 // 8), slice(x0 // 8, x1 // 8))
    T, sentinels = {}, {}
    for (container, key), value in actual.items():
        if value.dtype.kind in 'OUS':
            sentinel = 'UNKNOWN'
        elif value.dtype.kind == 'f':
            sentinel = float('nan')
        elif value.dtype.kind in 'iu':
            sentinel = N.iinfo(value.dtype).min
        else:
            sentinel = key in MASK_FIELDS
        full = N.full((H, W), sentinel, dtype=value.dtype)
        full[sl] = value
        if container == 'T':
            T[key] = full
        else:
            T.setdefault(container, {})[key] = full
        sentinels[(container, key)] = sentinel
    T['route_px'] = copy.deepcopy(meta['before_routes'])
    T['river_px'] = copy.deepcopy(meta['before_rivers'])
    T.update(copy.deepcopy(meta.get('before_metadata', {})))
    sys.path.insert(0, str(BLOCKOUT))
    import geo5 as g
    import geo52 as G
    import towns55 as tw
    if not isinstance(meta.get('palette'), dict):
        raise MissingInput('actual palette metadata absent')
    g.COL = copy.deepcopy(meta['palette'])
    yy, xx = N.mgrid[:H, :W]
    values = {'H': H, 'W': W, 'HPX': H * 8, 'WPX': W * 8, 'xx': xx, 'yy': yy, 'PX': xx * 8 + 4.0, 'PY': yy * 8 + 4.0}
    for module in (g, G, tw):
        for key, value in values.items():
            if hasattr(module, key):
                setattr(module, key, value)
    observed = Recorder(tw, folder, replay=True)
    error = None
    try:
        with observed:
            tw._feedback_crossroads(T, type('ActualSourceRoot', (), {'ROOT': str(REPO)})())
    except Exception as caught:
        error = caught
    after = observed.core
    array_parity, outside_changes = {}, {}
    outside = N.ones((H, W), bool); outside[sl] = False
    for pair, value in expected.items():
        container, key = pair
        full = T[key] if container == 'T' else T[container][key]
        array_parity[container + '/' + key] = bool(N.array_equal(full[sl], value, equal_nan=value.dtype.kind == 'f'))
        sentinel = sentinels[pair]
        unchanged = N.isnan(full[outside]) if isinstance(sentinel, float) and math.isnan(sentinel) else full[outside] == sentinel
        outside_changes[container + '/' + key] = int((~unchanged).sum())
    comparisons = {key: after.get(key) == meta.get(key) for key in
        ('producer_outcome', 'queued_ids', 'buildings', 'streets', 'spaces', 'outskirts', 'after_routes', 'after_rivers', 'after_metadata')}
    comparisons['all_original_trials'] = observed.events == original_trials['events']
    comparisons['all_original_groups'] = observed.groups == original_trials['groups']
    comparisons['all_literal_after_arrays'] = set(actual) == set(expected) and all(array_parity.values())
    comparisons['all_active_support_captured'] = bool(observed.supports) and all(q['captured'] for q in observed.supports)
    comparisons['zero_outside_changed_cells'] = not any(outside_changes.values())
    comparisons['capture_complete'] = after.get('complete') is True
    result = {'schema': SCHEMA, 'phase': 'unchanged_actual_input_reproduction',
        'input_capture_sha256': sha(original / 'capture.json'), 'comparison': comparisons,
        'all_equal': all(comparisons.values()), 'array_parity': array_parity, 'outside_changed_cells': outside_changes,
        'limits': 'Global pointwise scans and in-place OR touch UNKNOWN/refused buffers; zero outside reads/writes is NOT claimed.',
        'world_success': False, 'art_approval': False}
    write_json(folder / 'replay-result.json', result)
    if error is not None:
        error.__traceback__ = None
    if not result['all_equal']:
        raise CaptureError('actual unchanged consumer did not reproduce; preserve diagnostic and stop')



def _correction_inventory_valid(buildings, inventory):
    by_id = {b['layout_id']: b for b in buildings}
    return all(f'crossroads-b{i:03d}' in by_id
        and sorted((by_id[f'crossroads-b{i:03d}']['w'], by_id[f'crossroads-b{i:03d}']['h'])) == sorted((w, h))
        and by_id[f'crossroads-b{i:03d}'].get('form', by_id[f'crossroads-b{i:03d}']['use']) == form
        and by_id[f'crossroads-b{i:03d}'].get('bays', []) == bays for i, form, w, h, bays in inventory)


def correction(folder, allocation):
    """One measured candidate on actual BEFORE; original replay() stays unchanged."""
    source = Path(allocation['input']).resolve()
    meta = json_read(source / 'capture.json')
    original_source = json_read(source / 'source-before.json')
    current = source_guard(allocation.get('production_overrides'))
    town_path = 'docs/vision/research/blockout/towns55.py'
    changed = {name for name in current['source_sha256'] if current['source_sha256'][name] != original_source['source_sha256'].get(name)}
    if (allocation.get('production_overrides') != {town_path: CORRECTION_TOWNS_BLOB}
            or changed != {town_path, 'scripts/review/map_failure_capture.py', 'scripts/review/test_map_failure_capture.py'}
            or set(current['source_sha256']) != set(original_source['source_sha256'])
            or original_source != json_read(source / 'source-after.json')
            or allocation.get('original_source_sha256') != original_source['source_sha256']
            or allocation.get('physical_tables') != 'SOURCE_DERIVED_geo55_warp_tables_ONCE_before_dimension_rebind'):
        raise CaptureError('explicit original/candidate source and physical-table provenance required')
    if meta.get('complete') is not True or meta.get('schema') != SCHEMA or meta['before']['box_px'] != list(CROSS) or meta['cell_px'] != 8:
        raise MissingInput('complete exact actual BEFORE packet required')
    actual = load_snapshot(source, meta['before'])
    H, W = meta['global_shape']
    if [H, W] != meta['town_dimensions']:
        raise MissingInput('actual dimensions differ')
    # Fresh import MUST precede dimension rebinding: geo55 freezes OLD_W/H at
    # import. This initializes source-defined tables, never captured-state parity.
    sys.path.insert(0, str(BLOCKOUT))
    import geo55 as producer
    import town_plans as plans
    tw, g = producer.towns55, producer.g
    if (producer.OLD_W, producer.OLD_H) != (11264, 6912) or producer.REVISION != 'v56':
        raise MissingInput('fresh original-dimension source namespace required')
    producer.warp_tables()
    producer.set_dims(W * 8, H * 8)
    g.COL = copy.deepcopy(meta['palette'])
    x0, y0, x1, y1 = CROSS
    sl = (slice(y0 // 8, y1 // 8), slice(x0 // 8, x1 // 8))
    T, sentinels = {}, {}
    for pair, value in actual.items():
        container, key = pair
        sentinel = ('UNKNOWN' if value.dtype.kind in 'OUS' else float('nan') if value.dtype.kind == 'f'
                    else N.iinfo(value.dtype).min if value.dtype.kind in 'iu' else key in MASK_FIELDS)
        full = N.full((H, W), sentinel, dtype=value.dtype); full[sl] = value
        (T if container == 'T' else T.setdefault(container, {}))[key] = full
        sentinels[pair] = sentinel
    T['route_px'] = copy.deepcopy(meta['before_routes']); T['river_px'] = copy.deepcopy(meta['before_rivers'])
    T.update(copy.deepcopy(meta['before_metadata']))
    observer = Recorder(tw, folder, replay=True)
    failure, P, physical_failures, notes, counted = None, None, [], [], None
    checker_executed = False
    checks = {}
    try:
        try:
            with observer:
                tw._feedback_crossroads(T, producer)
        except ReturnedBoundary:
            if observer.core.get('producer_outcome', {}).get('kind') != 'RETURN':
                raise
        town = observer.town
        if town is None:
            raise MissingInput('actual candidate Town missing')
        ids = {f'crossroads-b{i:03d}' for i in range(1, 41)}
        by_id = {b['layout_id']: b for b in town.buildings}
        checks['all40_original_ids_and_cap'] = len(town.buildings) == len(by_id) == town.count() == town.cap == 40 and set(by_id) == ids
        def geometry(b):
            return {key: b.get(key) for key in ('x', 'y', 'w', 'h', 'use', 'form', 'counted', 'bays')}
        checks['original19_unchanged'] = all(b['layout_id'] in by_id and geometry(by_id[b['layout_id']]) == geometry(b) for b in meta['buildings'])
        checks['inventory_dimensions_preserved'] = _correction_inventory_valid(town.buildings, tw.FEEDBACK_BUILDINGS['crossroads'])
        def descriptors(value):
            return {(row['container'], row['source_key']): (row['dtype'], row['shape'], row['sha256']) for row in value['arrays']}
        checks['exact_saved_before'] = descriptors(observer.core['before']) == descriptors(meta['before'])
        if not all(value is True for value in checks.values()):
            raise CaptureError('candidate did not preserve the required40 inventory/before state')
        fb = plans._box([town])
        c0, r0 = max(0, (fb[0] - plans.PAD) // 8), max(0, (fb[1] - plans.PAD) // 8)
        c1, r1 = min(W, (fb[2] + plans.PAD) // 8 + 1), min(H, (fb[3] + plans.PAD) // 8 + 1)
        if not (x0 // 8 <= c0 < c1 <= x1 // 8 and y0 // 8 <= r0 < r1 <= y1 // 8):
            raise MissingInput('native padded physical window leaves actual captured ground')
        if N.any(T['K'][r0:r1, c0:c1] == 'UNKNOWN'):
            raise MissingInput('UNKNOWN cannot become ordinary land in terrain_rows')
        for name, pts in T['route_px'].items():
            if any(c0 * 8 <= x < c1 * 8 and r0 * 8 <= y < r1 * 8 for x, y in pts) and name not in g.ROUTES:
                raise MissingInput('local actual route lacks authoritative source kind: ' + name)
        context = {'kind': allocation['physical_tables'], 'actual_captured_global_table_parity': False,
            'source': current, 'window_px': [c0 * 8, r0 * 8, c1 * 8, r1 * 8],
            'route_kinds': {name: value[1] for name, value in g.ROUTES.items()}, 'stations': plain(g.STATIONS),
            'circle': plain(producer.V.CIRCLE), 'craters': plain(producer.V.CRATERS), 'waystones': plain(producer.V.WAYSTONES)}
        write_json(folder / 'correction-context.json', context)
        original_geometry = {name: geometry(b) for name, b in by_id.items()}
        P = plans.plan_one(T, 'Crossroads', [town], producer, tw._review())
        # This is the existing complete checker, called explicitly even though
        # this Town is not an authored packet. No fabricated doors or theme.
        blockout = {'routes': {name: {'polyline': pts} for name, pts in T['route_px'].items()}, 'stations': g.STATIONS}
        checker_executed = True
        physical_failures, notes, counted = tw._review().check_plan(P, blockout)
        checks['existing_physical_checker_passed'] = not physical_failures and counted == P['buildings_counted'] == 40
        exported = {b['id']: b for b in P['buildings']}
        checks['export_preserves40_without_lifting_or_refill'] = (len(P['buildings']) == len(exported) == 40 and set(exported) == ids
            and not P['lifted'] and len(town.buildings) == 40
            and {b['layout_id']: geometry(b) for b in town.buildings} == original_geometry)
        literal_failures = []
        for b in P['buildings']:
            c, r, w, h = b['footprint_cells']
            if not (x0 // 8 <= c and y0 // 8 <= r and c + w <= x1 // 8 and r + h <= y1 // 8):
                literal_failures.append(b['id'] + ': footprint leaves actual input'); continue
            before = actual[('T', 'K')][r-y0//8:r-y0//8+h, c-x0//8:c-x0//8+w]
            if N.isin(before, plans.WATER_K + plans.BARRIER_K).any() or N.isin(T['K'][r:r+h, c:c+w], plans.WATER_K + plans.BARRIER_K).any():
                literal_failures.append(b['id'] + ': initial/final literal water or barrier')
        checks['literal_initial_and_final_ground'] = not literal_failures
        yards = [q for q in town.outskirts if q['name'] == 'the halt yard' and q['kind'] == 'yard']
        yard_box = [5840, 4304, 6080, 4368]
        checks['named_working_yard_preserved'] = (len(yards) == 1 and yards[0]['box'] == yard_box
            and [730, 538, 30, 8] in T['authored_protected_cells']
            and all(b['x'] + b['w'] <= yard_box[0] or b['x'] >= yard_box[2] or b['y'] + b['h'] <= yard_box[1] or b['y'] >= yard_box[3] for b in town.buildings))
        write_json(folder / 'correction-plan.json', P)
        physical_failures = list(physical_failures) + literal_failures
    except Exception as error:
        failure = {'type': type(error).__name__, 'message': str(error)}
    outside = N.ones((H, W), bool); outside[sl] = False
    outside_changes = {}
    for pair, sentinel in sentinels.items():
        container, key = pair; full = T[key] if container == 'T' else T[container][key]
        same = N.isnan(full[outside]) if isinstance(sentinel, float) and math.isnan(sentinel) else full[outside] == sentinel
        outside_changes[container + '/' + key] = int((~same).sum())
    checks['zero_outside_changes_including_exporter'] = not any(outside_changes.values())
    checks['all_consumer_support_captured'] = bool(observer.supports) and all(q['captured'] for q in observer.supports)
    checks['candidate_capture_complete'] = observer.core.get('complete') is True and not observer.errors
    required = {'all40_original_ids_and_cap', 'original19_unchanged', 'inventory_dimensions_preserved', 'exact_saved_before',
        'existing_physical_checker_passed', 'export_preserves40_without_lifting_or_refill', 'literal_initial_and_final_ground',
        'named_working_yard_preserved', 'zero_outside_changes_including_exporter', 'all_consumer_support_captured', 'candidate_capture_complete'}
    report = {'schema': SCHEMA, 'kind': 'MEASURED_CROSSROADS_CANDIDATE', 'accepted': False, 'checks': checks,
        'failure': failure, 'physical_checker_executed': checker_executed, 'physical_failures': physical_failures, 'physical_notes': notes,
        'counted': counted, 'input_capture_sha256': sha(source / 'capture.json'), 'original_source': original_source,
        'candidate_source': current, 'source_derived_tables': allocation['physical_tables'], 'after': None,
        'outside_changed_cells': outside_changes, 'producer_outcome': observer.core.get('producer_outcome'),
        'world_success': False, 'art_approval': False, 'original_replay_oracle_unchanged': True}
    write_json(folder / 'correction-result.json', report)
    try:
        report['after'] = snapshot(T, CROSS, folder / 'correction-after.npz')
    except Exception as error:
        report['snapshot_error'] = {'type': type(error).__name__, 'message': str(error)}
    report['accepted'] = (set(checks) == required and all(value is True for value in checks.values())
        and failure is None and report['after'] is not None)
    write_json(folder / 'correction-result.json', report)
    if not report['accepted']:
        raise CaptureError('measured candidate failed; preserve first failure and stop')


def corrected_preview(folder, allocation):
    """Render only an accepted physical candidate; original preview() stays unchanged."""
    candidate = Path(allocation['candidate']).resolve()
    original = Path(allocation['input']).resolve()
    result = json_read(candidate / 'correction-result.json')
    if (result.get('accepted') is not True or result.get('physical_checker_executed') is not True
            or result.get('world_success') is not False or result.get('physical_failures')
            or result['input_capture_sha256'] != sha(original / 'capture.json')
            or result['candidate_source'] != source_guard(allocation.get('production_overrides'))):
        raise MissingInput('accepted exact-source measured candidate required before corrected preview')
    for name in ('correction-result.json', 'correction-plan.json', 'correction-context.json', 'correction-after.npz'):
        target = folder / 'reference-candidate' / name
        target.parent.mkdir(exist_ok=True)
        target.write_bytes((candidate / name).read_bytes())
    arrays = load_snapshot(candidate, result['after'])
    meta = json_read(original / 'capture.json')
    P = json_read(candidate / 'correction-plan.json')
    from PIL import Image, ImageDraw
    ground = arrays[('T', 'K')]; height, width = ground.shape
    image = diagnostic_image(ground, meta['palette']).resize((width * 4, height * 4), Image.Resampling.NEAREST)
    framed = Image.new('RGB', (image.width, image.height + 56), '#fff3dd'); framed.paste(image, (0, 56))
    draw = ImageDraw.Draw(framed)
    draw.text((8, 6), 'MyGame Crossroads MEASURED CANDIDATE - not art approval', fill='#201820')
    draw.text((8, 24), '40 records; native physical checks passed; world still incomplete', fill='#201820')
    x0, y0, _, _ = result['after']['box_px']
    for b in P['buildings']:
        x, y, w, h = b['rect_px']; x, y = (x-x0)/2, 56+(y-y0)/2
        draw.rectangle((x, y, x+w/2, y+h/2), outline='#ff3333', width=1)
        draw.text((x+1, y+1), b['id'].rsplit('-b', 1)[-1], fill='#111111')
    path = folder / 'crossroads-corrected-candidate.png'; framed.save(path)
    write_json(folder / 'preview-result.json', {'file': path.name, 'sha256': sha(path), 'label': 'CORRECTED CANDIDATE DIAGNOSTIC',
        'input_sha256': sha(original / 'capture.json'), 'candidate_result_sha256': sha(candidate / 'correction-result.json'),
        'world_success': False, 'art_approval': False})


def diagnostic_image(ground, palette):
    from PIL import Image, ImageColor
    rgb = {key: ImageColor.getrgb(value) if isinstance(value, str) else tuple(value[:3]) for key, value in palette.items()}
    height, width = ground.shape
    image = Image.new('RGB', (width, height))
    image.putdata([rgb.get(str(v), (255, 0, 255)) for v in ground.flat])
    return image


def preview(folder, allocation):
    """Labelled exact-data diagnostic, not finished art or whole-map approval."""
    source = Path(allocation['input']).resolve()
    meta = json_read(source / 'capture.json')
    if meta.get('complete') is not True or meta.get('schema') != SCHEMA:
        raise MissingInput('complete R6 input required for diagnostic preview')
    arrays = load_snapshot(source, meta['after'])
    from PIL import Image, ImageDraw
    ground = arrays[('T', 'K')]
    height, width = ground.shape
    if not isinstance(meta.get('palette'), dict):
        raise MissingInput('actual captured palette required; no guessed colour fallback')
    image = diagnostic_image(ground, meta['palette'])
    image = image.resize((width * 4, height * 4), Image.Resampling.NEAREST)
    framed = Image.new('RGB', (image.width, image.height + 56), '#fff3dd')
    framed.paste(image, (0, 56))
    draw = ImageDraw.Draw(framed)
    draw.text((8, 6), 'MyGame R6 Crossroads DIAGNOSTIC - not art approval', fill='#201820')
    draw.text((8, 24), 'Captured state; world success is not established', fill='#201820')
    x0, y0, _, _ = meta['after']['box_px']
    for b in meta.get('buildings') or []:
        x, y = (b['x'] - x0) / 2, 56 + (b['y'] - y0) / 2
        draw.rectangle((x, y, x + b['w'] / 2, y + b['h'] / 2), outline='#ff3333', width=1)
        draw.text((x + 1, y + 1), b.get('layout_id', '?').rsplit('-b', 1)[-1], fill='#111111')
    path = folder / 'crossroads-diagnostic.png'
    framed.save(path)
    write_json(folder / 'preview-result.json', {'input_sha256': sha(source / 'capture.json'),
        'file': path.name, 'sha256': sha(path), 'label': 'DIAGNOSTIC', 'art_approval': False, 'world_success': False})


@contextmanager
def preflight_inputs(folder):
    """Retain mandatory receiving fixtures before their original cleanup.

    Same copy/digest/owned-finalizer protocol as the reviewed hosted receiver;
    errors remain separate from the original unittest result and block producer.
    """
    folder = Path(folder)
    temporary = Path(os.environ['TMPDIR'])
    state = {'retained_inputs': [], 'input_retention_errors': []}
    original_cleanup = tempfile.TemporaryDirectory.cleanup

    def preserve_fixture_then_cleanup(directory):
        source = Path(directory.name)
        target = folder / 'preflight-inputs' / str(len(state['retained_inputs']) + len(state['input_retention_errors']))
        owned, copied = source.is_relative_to(temporary), False
        try:
            if not owned:
                raise CaptureError('prerequisite input outside private TMP')
            if source.exists():
                if owned_blocks(folder) + owned_blocks(source) > MAX_PACKET:
                    raise CaptureError('prerequisite input retention allocation bound')
                shutil.copytree(source, target)
                digest = lambda root: {str(p.relative_to(root)): sha(p) for p in root.rglob('*') if p.is_file()}
                if digest(source) != digest(target) or owned_blocks(folder) > MAX_PACKET:
                    raise CaptureError('prerequisite input copy identity/allocation mismatch')
                state['retained_inputs'].append(str(target.relative_to(folder)))
            copied = True
        except Exception as error:
            detached, detach_error = False, None
            if owned:
                try:
                    directory._finalizer.detach()
                    detached = True
                except Exception as finalizer_error:
                    detach_error = repr(finalizer_error)
            state['input_retention_errors'].append(dict(original=str(source), partial_copy=str(target),
                original_retained=owned and detached and source.exists(), finalizer_detached=detached,
                error=repr(error), detach_error=detach_error))
            best_effort_json(folder / 'preflight-input-retention.json', state)
        finally:
            if copied:
                original_cleanup(directory)

    with patch.object(tempfile.TemporaryDirectory, 'cleanup', preserve_fixture_then_cleanup):
        yield state


def worker(folder, allocation):
    current = source_guard(allocation.get('production_overrides'))
    if current['head'] != allocation['head'] or current['source_sha256'] != allocation['source_sha256']:
        raise CaptureError('worker exact source identity differs from allocation')
    versions = numeric(allocation.get('python_paths', []))
    if versions != allocation['versions']:
        raise CaptureError('actual numeric versions differ from reviewed allocation')
    write_json(folder / 'versions.json', {'python': sys.version, 'platform': platform.platform(),
        'versions': versions, 'import_paths': list(sys.path), 'seed': SEED, 'cwd': str(REPO),
        'command': list(sys.argv), 'environment': {k: os.environ[k] for k in
            ('MYGAME_MAP_REVISION', 'BLOCKOUT_OUT', 'OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'MKL_NUM_THREADS') if k in os.environ}})
    if allocation['phase'] == 'replay':
        replay(folder, allocation)
        return
    if allocation['phase'] == 'preview':
        preview(folder, allocation)
        return
    if allocation['phase'] == 'correction':
        correction(folder, allocation)
        return
    if allocation['phase'] == 'corrected-preview':
        corrected_preview(folder, allocation)
        return
    suite_module = runpy.run_path(str(Path(__file__).with_name('test_map_failure_capture.py')), run_name='new_R6_contract_definitions')
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(suite_module['Contracts'])
    with preflight_inputs(folder) as inputs:
        tested = unittest.TextTestRunner(verbosity=2).run(suite)
    passed = tested.wasSuccessful() and not inputs['input_retention_errors']
    write_json(folder / 'cheap-preflight.json', {'source': 'NEW R6 contracts, not repeated historical24+12+3',
        'ran': tested.testsRun, 'passed': passed, 'actual_unittest_success': tested.wasSuccessful(),
        'real_T_inventory': 'NOT_YET_AVAILABLE', **inputs})
    if not passed:
        raise CaptureError('cheap R6 prerequisites failed; no data_stage')
    sys.path.insert(0, str(BLOCKOUT))
    import geo5 as g
    import geo55 as producer
    import map55  # Preserve the production discovery graph; no rendering called.
    import towns55 as tw
    if producer.REVISION != 'v56' or producer.PROSPECTIVE_SEED != SEED:
        raise CaptureError('prospective producer/seed binding mismatch')
    g.NOISE_CACHE = NoiseCache()
    with Recorder(tw, folder) as recorder:
        producer.data_stage()
    raise CaptureError('unexpected complete data_stage; export/render forbidden')


def run_capture(allocation_path, out):
    allocation = json_read(allocation_path)
    phase = allocation.get('phase')
    if phase not in ('capture', 'replay', 'preview', 'correction', 'corrected-preview'):
        raise CaptureError('unknown allocated phase')
    if phase == 'capture' and allocation.get('production_overrides'):
        raise CaptureError('initial R6 replacement capture must use unchanged frozen production')
    before = source_guard(allocation.get('production_overrides'))
    if (not allocation.get('go_id') or allocation.get('head') != before['head']
            or allocation.get('source_sha256') != before['source_sha256']
            or allocation.get('out') != str(Path(out).resolve())):
        raise CaptureError('new exact committed source allocation required')
    out = Path(out).resolve()
    if out == REPO or REPO in out.parents:
        raise CaptureError('capture output must be outside the repository')
    disk = os.statvfs(out.parent)
    if disk.f_bavail * disk.f_frsize < 256 * 1024**2:
        raise CaptureError('less than256MiB free before replacement phase')
    out.mkdir(mode=0o700)
    def limits():
        os.sched_setaffinity(0, {min(os.sched_getaffinity(0))})
        bound = 6 * 1024**3 if phase == 'capture' else int(1.5 * 1024**3)
        resource.setrlimit(resource.RLIMIT_AS, (bound, bound))
    child = None
    raw = None
    usage = None
    reason = None
    size = 0
    start = time.monotonic()
    last_usage = None
    peak_anon = 0
    previous_term = None
    selector = None
    identity_lost = False
    terminal = None
    group_signalled_before_reap = False
    def interrupted(signum, frame):
        raise KeyboardInterrupt('controller interrupted by signal ' + str(signum))
    try:
        write_json(out / 'allocation.json', allocation)
        write_json(out / 'source-before.json', before)
        write_json(out / 'capture.json', {'schema': SCHEMA, 'stage': 'INCOMPLETE_BEFORE_WORKER', 'complete': False,
            'replacement_evidence': True, 'world_state': 'NOT_COMPLETED'})
        for path in source_files():
            dest = out / 'source' / path.relative_to(REPO)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(path.read_bytes())
        if phase != 'capture':
            retain_input_reference(out, allocation['input'])
        private = out / 'private'
        for name in ('tmp', 'config', 'data', 'cache', 'runtime', 'blockout'):
            (private / name).mkdir(parents=True, mode=0o700)
        env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', GIT_OPTIONAL_LOCKS='0',
            MYGAME_MAP_REVISION='v56', OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', NUMEXPR_NUM_THREADS='1',
            BLOCKOUT_OUT=str(private / 'blockout'), TMPDIR=str(private / 'tmp'), TMP=str(private / 'tmp'), TEMP=str(private / 'tmp'),
            XDG_CONFIG_HOME=str(private / 'config'), XDG_DATA_HOME=str(private / 'data'), XDG_CACHE_HOME=str(private / 'cache'),
            XDG_RUNTIME_DIR=str(private / 'runtime'), REPO_ROOT=str(REPO))
        nonce = secrets.token_hex(16)
        env['MYGAME_R6_WORKER_NONCE'] = nonce
        for key in ('DISPLAY', 'XAUTHORITY', 'OLD_CACHE', 'DEV_PRE', 'DEV_PKL', 'QUICK', 'RENDER_ONLY', 'MAP55_OUT'):
            env.pop(key, None)
        command = [sys.executable, '-I', '-B', str(Path(__file__)), '_worker', '--out', str(out)]
        write_json(out / 'command.json', {'command': command, 'cwd': str(REPO), 'replacement': True})
        if signal.getsignal(signal.SIGCHLD) != signal.SIG_DFL:
            raise CaptureError('default SIGCHLD policy required for owned-child identity')
        previous_term = signal.getsignal(signal.SIGTERM)
        signal.signal(signal.SIGTERM, interrupted)
        child = subprocess.Popen(command, cwd=REPO, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                 start_new_session=True, preexec_fn=limits)
        selector = selectors.DefaultSelector()
        selector.register(child.stdout, selectors.EVENT_READ)
        with (out / 'worker.log').open('xb') as log:
            while True:
                for key, _ in selector.select(.1):
                    data = os.read(key.fd, 65536)
                    if not data:
                        selector.unregister(key.fileobj)
                        continue
                    room = MAX_LOG - size
                    log.write(data[:room]); log.flush(); size += min(len(data), room)
                    if len(data) > room:
                        reason = 'log_bound'
                try:
                    terminal = os.waitid(os.P_PID, child.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT)
                except ChildProcessError:
                    identity_lost, reason = True, 'nonreaping_child_identity_lost'
                    break
                if terminal is not None:
                    break  # Keep the exited leader unreaped until the last owned-group signal.
                if time.monotonic() - start > (900 if phase == 'capture' else 180):
                    reason = 'wall_bound'
                try:
                    last_usage = usage_record(out, child.pid, nonce, start)
                    if last_usage['peak_rss_bytes'] > int((3.2 if phase == 'capture' else 1) * 1024**3):
                        reason = 'live_RSS_bound'
                except Exception:
                    if time.monotonic() - start > 10:
                        reason = 'resource_telemetry_missing_stale_or_invalid'
                if owned_blocks(out) > MAX_OWNED // 2:
                    reason = 'owned_bound_before_portable'
                peak_anon = max(peak_anon, shared_anon())
                if peak_anon > int(4.2 * 1024**3):
                    reason = 'shared_anon_bound'
                disk = os.statvfs(out)
                if disk.f_bavail * disk.f_frsize < 64 * 1024**2:
                    reason = 'emergency_free_floor'
                if reason:
                    break
    except BaseException as error:
        reason = reason or 'controller_error'
        try:
            write_json(out / 'controller-error.json', {'type': type(error).__name__, 'message': str(error)})
        except Exception:
            pass  # Keep existing partial files and continue owned-child cleanup/bundling.
    finally:
        if child is not None and not identity_lost:
            try:
                # Reconfirm the unreaped child before signalling its owned session.
                os.waitid(os.P_PID, child.pid, os.WEXITED | os.WNOHANG | os.WNOWAIT)
            except OSError:
                identity_lost, reason = True, 'cleanup_child_identity_lost'
            if not identity_lost:
                # The leader remains an unreaped identity anchor, even if it exited first.
                try:
                    os.killpg(child.pid, signal.SIGKILL)
                    group_signalled_before_reap = True
                except ProcessLookupError:
                    pass
                except OSError:
                    reason = reason or 'owned_group_signal_failed'
                deadline = time.monotonic() + 5
                while True:
                    try:
                        pid, status, observed = os.wait4(child.pid, os.WNOHANG)
                    except ChildProcessError:
                        identity_lost, reason = True, 'destructive_wait_child_identity_lost'
                        break
                    if pid:
                        raw, usage = os.waitstatus_to_exitcode(status), observed
                        child.returncode = raw
                        break
                    if time.monotonic() >= deadline:
                        reason = reason or 'owned_child_collection_bound'
                        break
                    time.sleep(.05)
        try:
            if selector is not None:
                # Drain only currently observable pipe bytes after disposition; no new child.
                deadline = time.monotonic() + 1
                with (out / 'worker.log').open('ab') as log:
                    while selector.get_map() and time.monotonic() < deadline:
                        for key, _ in selector.select(.05):
                            data = os.read(key.fd, 65536)
                            if not data:
                                selector.unregister(key.fileobj)
                                continue
                            room = MAX_LOG - size
                            log.write(data[:room]); log.flush(); size += min(len(data), room)
                            if len(data) > room:
                                reason = reason or 'log_bound'
        except Exception:
            reason = reason or 'terminal_log_collection_failed'
        finally:
            if selector is not None:
                selector.close()
            if child is not None and child.stdout:
                child.stdout.close()
            if previous_term is not None:
                signal.signal(signal.SIGTERM, previous_term)
    try:
        if child is not None:
            last_usage = usage_record(out, child.pid, nonce, start, terminal=True)
    except Exception:
        reason = reason or 'terminal_resource_telemetry_invalid'
    try:
        after = source_guard(allocation.get('production_overrides'))
        write_json(out / 'source-after.json', after)
    except Exception as error:
        after = {'error': type(error).__name__, 'message': str(error)}
        reason = reason or 'source_guard_failed'
    # Malformed/missing worker metadata must not prevent packaging partial evidence.
    try:
        if phase in ('preview', 'corrected-preview'):
            view = json_read(out / 'preview-result.json')
            label = 'DIAGNOSTIC' if phase == 'preview' else 'CORRECTED CANDIDATE DIAGNOSTIC'
            complete = sha(out / view['file']) == view['sha256'] and view['label'] == label
        else:
            capture = json_read(out / 'capture.json')
            complete = capture.get('complete') is True and not capture.get('errors')
            for key in (('before', 'after', 'initial_neon') if phase == 'capture' else ('before', 'after')):
                if key not in capture:
                    complete = False
                else:
                    validate_archive(out / capture[key]['file'], capture[key])
            if 'trials' not in capture or sha(out / 'trials.json') != capture['trials']['sha256']:
                complete = False
            if phase == 'replay':
                complete = complete and json_read(out / 'replay-result.json').get('all_equal') is True
            if phase == 'correction':
                candidate = json_read(out / 'correction-result.json')
                complete = complete and candidate.get('accepted') is True and candidate.get('physical_checker_executed') is True
                validate_archive(out / candidate['after']['file'], candidate['after'])
    except Exception as error:
        complete = False
        best_effort_json(out / 'collection-error.json', {'type': type(error).__name__, 'message': str(error)})
    peak = int(usage.ru_maxrss * 1024) if usage is not None else None
    if peak is None or not 0 < peak <= int((3.2 if phase == 'capture' else 1) * 1024**3):
        reason = reason or 'observed_RSS_bound_or_missing'
    group_absent = True
    if child is not None:
        try:
            os.killpg(child.pid, 0)
            group_absent = False
        except ProcessLookupError:
            pass
    result = {'schema': SCHEMA, 'replacement': True, 'phase': phase, 'raw_exit': raw, 'stop_reason': reason,
        'world_success': False, 'capture_complete': complete, 'source_unchanged': before == after,
        'child_reaped': raw is not None, 'owned_group_absent': group_absent, 'peak_child_rss_bytes': peak,
        'child_identity_lost': identity_lost, 'group_signalled_before_reap': group_signalled_before_reap,
        'cpu_user': usage.ru_utime if usage else None, 'cpu_system': usage.ru_stime if usage else None,
        'seconds': round(time.monotonic() - start, 3), 'finished_at': now(), 'handoff_complete': False,
        'final_self_usage': last_usage, 'peak_shared_anon_bytes': peak_anon}
    try:
        write_json(out / 'result.json', result)
    finally:
        portable = bundle(out)  # FIRST failure is a portable artifact too.
    print(json.dumps({'result': result, 'portable': portable}, sort_keys=True), flush=True)
    return 0 if phase != 'capture' and raw == 0 and complete and reason is None and before == after and group_absent else 1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('plan', 'capture', 'verify-portable', '_worker'))
    parser.add_argument('--allocation')
    parser.add_argument('--out')
    parser.add_argument('--archive')
    parser.add_argument('--sha256')
    args = parser.parse_args()
    if args.action == 'plan':
        print(json.dumps(plan(), indent=2, sort_keys=True)); return 0
    if args.action == 'verify-portable':
        print(json.dumps(verify_bundle(args.archive, args.sha256), sort_keys=True)); return 0
    if args.action == 'capture':
        return run_capture(args.allocation, args.out)
    folder = Path(args.out)
    allocation = json_read(folder / 'allocation.json')
    nonce = os.environ.get('MYGAME_R6_WORKER_NONCE')
    if not nonce:
        raise CaptureError('owned controller invocation required')
    pulse = UsagePulse(folder, nonce)
    pulse.start()
    code = 0
    try:
        worker(folder, allocation)
    except BaseException as error:
        # The parent owns cleanup/portable publication; original traceback is retained.
        traceback.print_exc()
        code = 3 if isinstance(error, ReturnedBoundary) else 1
    finally:
        try:
            pulse.close()
        except Exception as error:
            print(json.dumps({'resource_collection_error': str(error)}), file=sys.stderr, flush=True)
            code = code or 1
    return code


if __name__ == '__main__':
    sys.exit(main())
