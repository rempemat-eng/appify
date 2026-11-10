"""Automated checks for exported character frames, and review sheets.

python3 checks.py <id> [<id> ...]     reads out/<id>/manifest.json and its PNGs, writes
review/<id>/<clip>_<F>.png contact sheets (4x, pivot row, anchors marked) and
review/<id>/checks.json, and prints a summary.  Exit code 1 when an error is found.

Per frame:
  palette    every opaque colour is a ramp tone, an outline tone or a face stamp colour
             (no blended or stray colours); colours per material <= 5 (4 tones + edge)
  colours    distinct colours in the frame <= COLOUR_BUDGET
  alpha      alpha is 0 or 255 only
  lone       isolated single pixels inside a fill (a pixel unlike all 4 neighbours, which
             are opaque and agree with each other); a few are allowed for glints and studs
  edge       nothing touches the cell border (clipping)
  ground     clips the contract marks 'exact': the lowest opaque row is the pivot row;
             'stance': the lowest row is within K * stride of it (S and N walks)
  size       idle height within the character's band; every frame's height <= band max + 12
  arms       (per character, when its module declares ARM) both arms' rig segments equal ARM's and
             the drawn arms in S and N differ by at most 1 px (arm_symmetry)
  equipment  each tag the character's EQUIP table requires has at least MIN_EQUIP visible
             pixels in the drawings where the rule applies
"""
import json
import os
import sys
import importlib

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import anim
import palette  # noqa: F401
from ew import MATS, INK, hx
import parts

COLOUR_BUDGET = 64
LONE_ALLOW = 8
MIN_EQUIP = 4
RELEASE_MIN_PX = 12                # the held weapon's visible pixels at the release, every facing and aim
BANDS = {'bramble': (72, 80), 'pendle': (70, 80), 'cairn': (84, 98), 'iona': (70, 80)}
FONT = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 13)


def palette_map():
    m = {}
    for name, M in MATS.items():
        for i, t in enumerate(M.tones):
            m.setdefault(tuple(int(round(v)) for v in t), set()).add(name)
        m.setdefault(tuple(int(round(v)) for v in M.edge), set()).add(name)
    for h in (INK, parts.EYE, parts.GLINT):
        m.setdefault(tuple(int(v) for v in hx(h)), set()).add('face')
    return m


def pieces(a, pm, exclude, min_px=4):
    """Separate opaque pieces (8-connected) of a drawing. A piece drawn only in effect materials
    (a flying shard, dust, dazed stars, with their outline ink) does not count."""
    from scipy import ndimage as ndi
    op = a[..., 3] > 0
    lab, n = ndi.label(op, structure=np.ones((3, 3), int))
    fx = set(exclude) | {'face', 'eye'}
    sizes = []
    for i in range(1, n + 1):
        ys, xs = np.where(lab == i)
        if len(ys) < min_px:
            continue
        cols = {tuple(int(v) for v in a[y, x, :3]) for y, x in zip(ys, xs)}
        if all((pm.get(c) or {'?'}) & fx for c in cols):
            continue
        sizes.append(len(ys))
    return len(sizes), sorted(sizes, reverse=True)


def lone_pixels(a):
    rgb = a[..., :3].astype(int)
    op = a[..., 3] > 0
    key = (rgb[..., 0] << 16) | (rgb[..., 1] << 8) | rgb[..., 2]
    H, W = key.shape
    k = key[1:-1, 1:-1]
    nb = [key[:-2, 1:-1], key[2:, 1:-1], key[1:-1, :-2], key[1:-1, 2:]]
    on = [op[:-2, 1:-1], op[2:, 1:-1], op[1:-1, :-2], op[1:-1, 2:]]
    allop = op[1:-1, 1:-1] & on[0] & on[1] & on[2] & on[3]
    diff = (nb[0] != k) & (nb[1] != k) & (nb[2] != k) & (nb[3] != k)
    agree = (nb[0] == nb[1]) & (nb[1] == nb[2]) & (nb[2] == nb[3])
    ys, xs = np.where(allop & diff & agree)
    return [(int(x) + 1, int(y) + 1) for y, x in zip(ys, xs)]


BACK = ('N', 'NE', 'NW')          # facings with the back toward the camera


def face_colours(mod, A):
    """Colours only the face uses (26 Oct, Pendle's N head): the colours under the 'face' tag of
    the S, E and turned idle drawings whose material no other part of those drawings uses."""
    inside, outside = set(), set()
    poses = [(fc, A.TABLE['idle'][0][0]) for fc in ('S', 'E', 'SE')]
    for clip, r in getattr(A, 'RELEASE', {}).items():       # effects at the release (a muzzle flash) are not face
        if clip in A.TABLE and r is not None and r < len(A.TABLE[clip]):
            poses += [(fc, A.TABLE[clip][r][0]) for fc in ('S', 'E')]
    for fc, P in poses:
        try:
            f = mod.draw(fc, mod.P0(**P))
            a = f.render()
        except Exception:
            continue
        fm = getattr(f, 'tagmasks', {}).get('face')
        op = a[..., 3] > 0
        rgb = a[..., :3]
        if fm is not None:
            inside |= {tuple(int(v) for v in c) for c in rgb[op & fm]}
            outside |= {tuple(int(v) for v in c) for c in rgb[op & ~fm]}
        else:
            outside |= {tuple(int(v) for v in c) for c in rgb[op]}
    # a colour counts only when its material is used by no other part (Pendle's bandana: the front is
    # the face, but its tie and knot show from behind in the same cloth)
    pm = palette_map()
    mats = set()
    for c in outside:
        mats |= set(pm.get(c, ())) - {'face'}         # 'face' is the eye ink and glint pseudo-material
    return {c for c in inside - outside if not ((set(pm.get(c, ())) - {'face'}) & mats)}


def arm_symmetry(mod, A):
    """CONTRACT V2.13: a character whose module declares ARM (its one set of arm segment lengths)
    and records its arms (f.arms, f.groups) has two arms of the same length.  In every idle
    drawing and facing, each arm's rig segments (shoulder socket to elbow, elbow to hand) equal
    ARM's (no stretched arm); in S and N the drawn arms (top of the shoulder stone to the lowest
    hand pixel) differ by at most 1 px."""
    errs = []
    arm = getattr(mod, 'ARM', None)
    if arm is None or A is None or 'idle' not in getattr(A, 'TABLE', {}):
        return errs
    for fc in anim.FACINGS8:
        for i, (P, _ms) in enumerate(A.TABLE['idle']):
            f = mod.draw(fc, mod.P0(**P))
            arms = getattr(f, 'arms', None)
            if not arms:
                return ['%s: ARM declared but the draw records no arms' % mod.__name__]
            for key, d in arms.items():
                s3, e3, h3 = d['rig']
                lu = float(np.linalg.norm(np.subtract(e3, s3)))
                lf = float(np.linalg.norm(np.subtract(h3, e3)))
                if abs(lu - arm['upper']) > 0.05 or abs(lf - arm['fore']) > 0.05:
                    errs.append('%s idle %s #%d: arm %s segments %.2f / %.2f, rig %.2f / %.2f (stretched)'
                                % (mod.__name__, fc, i, key, lu, lf, arm['upper'], arm['fore']))
            if fc in ('S', 'N') and hasattr(f, 'groups'):
                ln = {}
                for key in arms:
                    top = min(np.where(np.any([f.parts[j].mask for j in f.groups['shoulder_' + key]], axis=0).any(1))[0])
                    low = max(np.where(np.any([f.parts[j].mask for j in f.groups['hand_' + key]], axis=0).any(1))[0])
                    ln[key] = low - top + 1
                if len(ln) == 2 and abs(ln['R'] - ln['L']) > 1:
                    errs.append('%s idle %s #%d: drawn arms %d px (R) and %d px (L), more than 1 px apart'
                                % (mod.__name__, fc, i, ln['R'], ln['L']))
    return errs


def check_char(cid, write_sheets=True):
    root = anim.ROOT
    od = os.path.join(root, 'out', cid)
    man = json.load(open(os.path.join(od, 'manifest.json')))
    try:
        A = importlib.import_module('anim_' + cid)
        equip = getattr(A, 'EQUIP', {})
    except ImportError:
        A, equip = None, {}
    pm = palette_map()
    gy = man['foot_pivot'][1]
    band = BANDS.get(cid)
    try:
        mod = importlib.import_module(cid)
        band = getattr(mod, 'BAND', band)
    except ImportError:
        pass
    band = band or (56, 100)
    # creatures are one connected silhouette: no detached head or limb (effects excepted)
    one_body = set(getattr(mod, 'DETACHED_OK', ())) if getattr(mod, 'ONE_BODY', False) else None
    fcols = face_colours(mod, A) if A is not None and 'idle' in getattr(A, 'TABLE', {}) else set()
    fkey = {(c[0] << 16) | (c[1] << 8) | c[2] for c in fcols}
    errors, warns = [], []
    errors += arm_symmetry(mod, A)
    stats = dict(frames=0, max_colours=0, lone=0)
    rd = os.path.join(root, 'review', cid)
    os.makedirs(rd, exist_ok=True)
    for clip, ce in man['clips'].items():
        spec = anim.clip_specs(cid, A).get(clip, {}) if A is not None else (anim.CLIPS.get(clip) or anim.EXTRA_CLIPS.get(cid, {}).get(clip, {}))
        sets = list(ce['facings'].items())
        for fc0, fe0 in list(ce['facings'].items()):          # weapon aims: checked like their facing
            for tag, ae in fe0.get('aims', {}).items():
                if tag != '0':
                    sets.append(('%s~%s' % (fc0, tag), dict(ae, release_anchor_name=fe0.get('release_anchor_name'))))
        for d, te in ce.get('turns', {}).items():             # v2 turn in-betweens: checked like a facing
            sets.append((d, te))
        for fc, fe in sets:
            bf = fc.split('~')[0]
            ims = []
            for i, fr in enumerate(fe['frames']):
                stats['frames'] += 1
                tag = '%s %s %s #%d' % (cid, clip, fc, i)
                im = Image.open(os.path.join(od, fr['file'])).convert('RGBA')
                a = np.array(im)
                ims.append((im, fr))
                al = a[..., 3]
                if not np.isin(al, (0, 255)).all():
                    errors.append(tag + ': soft alpha')
                op = al > 0
                cols = {tuple(c) for c in a[op][:, :3]}
                stats['max_colours'] = max(stats['max_colours'], len(cols))
                if len(cols) > COLOUR_BUDGET:
                    warns.append(tag + ': %d colours' % len(cols))
                bad = [c for c in cols if c not in pm]
                if bad:
                    errors.append(tag + ': %d colours outside the palette, e.g. %s' % (len(bad), bad[:3]))
                lp = lone_pixels(a)
                stats['lone'] = max(stats['lone'], len(lp))
                if len(lp) > LONE_ALLOW:
                    warns.append(tag + ': %d lone pixels, e.g. %s' % (len(lp), lp[:4]))
                if op[0].any() or op[-1].any() or op[:, 0].any() or op[:, -1].any():
                    errors.append(tag + ': touches the cell border')
                ys = np.where(op.any(1))[0]
                low, top = ys.max(), ys.min()
                g = spec.get('ground')
                if g == 'exact' and bf in ('E', 'W') and low != gy - 1:
                    errors.append(tag + ': lowest row %d, pivot row %d' % (low, gy - 1))
                # S/N: a foot toward the camera projects up to 4 px lower; with the front foot
                # lifted (anim.unskate) the planted rear foot sits up to 3 px higher
                if g == 'exact' and bf not in ('E', 'W') and not (gy - 4 <= low <= gy + 3):
                    errors.append(tag + ': lowest row %d, pivot row %d (-3/+4 allowed in S and N)' % (low, gy - 1))
                if g == 'stance' and not (gy - 1 - 1 <= low <= gy - 1 + 5):
                    errors.append(tag + ': walking feet off the ground (lowest row %d)' % low)
                if one_body:
                    n, sizes = pieces(a, pm, one_body)
                    if n > 1:
                        errors.append(tag + ': %d separate pieces %s (one connected body expected)' % (n, sizes))
                h = low - top + 1
                if clip == 'idle' and not (band[0] <= h <= band[1]):
                    errors.append(tag + ': idle height %d outside band %s' % (h, band))
                if h > band[1] + 26:
                    warns.append(tag + ': height %d' % h)
                # 26 Oct (Pendle's N head): from behind no face part shows, by tag ('face': eyes,
                # lamps, visor glass, the bandana's front) or by a colour only the face uses
                if bf in BACK:
                    nf = fr['equipment'].get('face', 0)
                    if nf:
                        errors.append(tag + ': %d px of the face from behind' % nf)
                    if fkey:
                        k = (a[..., 0].astype(int) << 16) | (a[..., 1].astype(int) << 8) | a[..., 2]
                        nc = int((np.isin(k, list(fkey)) & op).sum())
                        if nc:
                            errors.append(tag + ': %d px in face-only colours from behind' % nc)
                for et, rule in equip.items():
                    need = False
                    if rule.get('always'):
                        need = bf not in rule.get('may_hide', set())
                    if clip in rule.get('clips', {}):
                        need = i in rule['clips'][clip] and bf not in rule.get('may_hide', set()) and fc not in rule.get('may_hide', set())
                    if i in rule.get('except', {}).get(clip, ()):       # a drawing where it is honestly occluded
                        need = False
                    if need and fr['equipment'].get(et, 0) < MIN_EQUIP:
                        errors.append(tag + ': %s not visible (%d px)' % (et, fr['equipment'].get(et, 0)))
            # v2 polish (Matt, 26 Oct): no pixel blinks on or off for a single drawing (anim.deflicker)
            bl = anim.flicker([np.array(x[0]) for x in ims], bool(ce.get('loop')))
            bl = [(i, n) for i, n in bl if not (i == 0 and clip in ('idle', 'powered_idle'))]
            nb = sum(n for _, n in bl)
            if nb:
                warns.append('%s %s %s: %d pixels flicker for one drawing (drawings %s)' % (cid, clip, fc, nb, sorted({i for i, _ in bl})))
            if write_sheets:
                sheet(ims, ce, fe, gy, os.path.join(rd, '%s_%s.png' % (clip, fc)), '%s  %s  %s' % (man['name'], clip, fc))
    # contract v2: eight facings, a release anchor in every facing, fidgets that start and end on
    # idle 0 (so the runtime's cut in and out never pops)
    if man.get('contract') == 2:
        dirs = man.get('directions', [])
        if sorted(dirs) not in (sorted(anim.FACINGS8), sorted(anim.FACINGS)):
            errors.append('%s: v2 manifest directions %s' % (cid, dirs))
        for clip in man.get('aim_clips', []):
            ce = man['clips'][clip]
            for fc, fe in ce['facings'].items():
                tags = sorted(fe.get('aims', {}))
                if tags != sorted(anim.AIM_TAG.values()):
                    errors.append('%s %s %s: aims %s' % (cid, clip, fc, tags))
                for tag, ae in fe.get('aims', {}).items():
                    if len(ae['frames']) != ce['frame_count']:
                        errors.append('%s %s %s %s: %d drawings' % (cid, clip, fc, tag, len(ae['frames'])))
                    if ce.get('release_frame') is not None and not ae.get('release_anchor'):
                        errors.append('%s %s %s %s: no release_anchor' % (cid, clip, fc, tag))
        # v2: the release anchor lies on the held item (within 2 px of its pixels) in every facing and
        # aim; the item may be hidden only from behind (N), where the body covers it
        for clip, ce in man['clips'].items():
            rel = ce.get('release_frame')
            if rel is None:
                continue
            for fc, fe in ce['facings'].items():
                name = fe.get('release_anchor_name')
                if not name:
                    continue
                sets = [(fc, fe)] + [('%s~%s' % (fc, t), ae) for t, ae in fe.get('aims', {}).items() if t != '0']
                for lab, se in sets:
                    frs = se['frames']
                    i = rel if name in frs[rel]['anchors'] else rel - 1
                    gaps = frs[i].get('anchor_gap')
                    if gaps is None or name not in gaps:
                        continue                   # an anchor that is not a held item (a hand, the lantern's light)
                    g = gaps[name]
                    if g is None and fc != 'N':
                        errors.append('%s %s %s #%d: release anchor %s with its item out of sight' % (cid, clip, lab, i, name))
                    elif g is not None and g > 2.0:
                        errors.append('%s %s %s #%d: release anchor %s %.1f px off its item' % (cid, clip, lab, i, name, g))
        # v2 (26 Oct review of Ashe's cut): at the release the held weapon shows at least
        # RELEASE_MIN_PX pixels in every facing and aim, N included: the strike itself is never hidden
        # behind the body.  The weapon is the module's WEAPON_TAG[clip], else the release anchor's item.
        wtags = dict(anim.ANCHOR_TAG, **(getattr(A, 'ANCHOR_TAG', {}) if A else {}))
        for clip, ce in man['clips'].items():
            rel = ce.get('release_frame')
            if rel is None:
                continue
            for fc, fe in ce['facings'].items():
                name = fe.get('release_anchor_name')
                tag = (getattr(A, 'WEAPON_TAG', {}) if A else {}).get(clip) or wtags.get(name)
                if not tag:
                    continue
                sets = [(fc, fe)] + [('%s~%s' % (fc, t), ae) for t, ae in fe.get('aims', {}).items() if t != '0']
                for lab, se in sets:
                    eq = se['frames'][rel]['equipment']
                    n = eq.get(tag, 0) + sum(eq.get(t, 0) for t in ((getattr(A, 'WEAPON_WITH', {}) if A else {}).get(clip, ())))
                    if n < RELEASE_MIN_PX:
                        errors.append('%s %s %s #%d: the %s shows %d px at the release (%d needed)' % (cid, clip, lab, rel, tag, n,
                                                                                                      RELEASE_MIN_PX))
        ti = man.get('turn_inbetweens')
        if ti:
            for clip in ti['clips']:
                ce = man['clips'][clip]
                if sorted(ce.get('turns', {})) != sorted(anim.TURN_FACINGS):
                    errors.append('%s %s: turn in-betweens %s' % (cid, clip, sorted(ce.get('turns', {}))))
                for d, te in ce.get('turns', {}).items():
                    if len(te['frames']) != ce['frame_count']:
                        errors.append('%s %s %s: %d turn drawings' % (cid, clip, d, len(te['frames'])))
        for clip, ce in man['clips'].items():
            if sorted(ce['facings']) != sorted(dirs):
                errors.append('%s %s: facings %s' % (cid, clip, sorted(ce['facings'])))
            if ce.get('release_frame') is not None:
                for fc, fe in ce['facings'].items():
                    if not fe.get('release_anchor'):
                        errors.append('%s %s %s: no release_anchor' % (cid, clip, fc))
        idle = man['clips'].get('idle')
        for fid in man.get('idle_fidgets', {}).get('clips', []):
            ce = man['clips'].get(fid)
            if ce is None:
                errors.append('%s: fidget %s not exported' % (cid, fid))
                continue
            for fc, fe in ce['facings'].items():
                i0 = idle['facings'][fc]['frames'][0]['sha256']
                if fe['frames'][0]['sha256'] != i0 or fe['frames'][-1]['sha256'] != i0:
                    errors.append('%s %s %s: does not start and end on idle 0' % (cid, fid, fc))
    rep = dict(errors=errors, warnings=warns, stats=stats)
    json.dump(rep, open(os.path.join(rd, 'checks.json'), 'w'), indent=1)
    return rep


def sheet(ims, ce, fe, gy, path, title, z=4):
    """Contact sheet: drawings in a row at 4x on a mid green, pivot row, release anchor, timings."""
    boxes = [fr['packed_bounds'] for _, fr in ims]
    x0 = max(0, min(b[0] for b in boxes) - 4)
    x1 = min(anim.CELL[0], max(b[2] for b in boxes) + 4)
    y0 = max(0, min(b[1] for b in boxes) - 4)
    y1 = gy + 6
    w, h = (x1 - x0) * z, (y1 - y0) * z
    pad = 26
    S = Image.new('RGBA', (w * len(ims) + 8 * (len(ims) - 1), h + pad * 2), (40, 42, 46, 255))
    d = ImageDraw.Draw(S)
    d.text((6, 5), title, font=FONT, fill=(230, 226, 214))
    for i, (im, fr) in enumerate(ims):
        cell = Image.new('RGBA', (x1 - x0, y1 - y0), (126, 159, 80, 255))
        cell.alpha_composite(im.crop((x0, y0, x1, y1)))
        big = cell.resize((w, h), Image.NEAREST)
        X = i * (w + 8)
        S.alpha_composite(big, (X, pad))
        d.line([(X, pad + (gy - y0) * z), (X + w, pad + (gy - y0) * z)], fill=(70, 96, 50, 255))
        rel = ce.get('release_frame')
        an = fe.get('release_anchor_name')
        if an and fr['anchors'].get(an):
            ax, ay = fr['anchors'][an]
            px, py = X + (anim.PIVOT[0] + ax - x0) * z, pad + (gy + ay - y0) * z
            d.ellipse([px - 4, py - 4, px + 4, py + 4], outline=(255, 80, 200, 255), width=2)
        lab = '%d  %dms%s' % (i, round(ce['durations'][i] * 1000), '  RELEASE' if rel == i else ('  HOLD' if ce.get('hold_frame') == i else ''))
        d.text((X + 4, pad + h + 5), lab, font=FONT, fill=(255, 210, 120) if rel == i else (210, 206, 196))
    S.convert('RGB').save(path)


if __name__ == '__main__':
    bad = False
    for cid in sys.argv[1:]:
        r = check_char(cid)
        print('%s: %d frames, max %d colours, max %d lone pixels; %d errors, %d warnings'
              % (cid, r['stats']['frames'], r['stats']['max_colours'], r['stats']['lone'], len(r['errors']), len(r['warnings'])))
        for e in r['errors'][:40]:
            print('  ERROR', e)
        for w in r['warnings'][:20]:
            print('  warn ', w)
        bad |= bool(r['errors'])
    sys.exit(1 if bad else 0)
