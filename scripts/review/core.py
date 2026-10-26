"""Shared pieces for the review detectors: loading a picture at its native pixel grid,
colour helpers, regions, findings and the annotated contact sheets.

Everything the detectors measure is in native texels (one art pixel), and every size
threshold is a fraction of the character height H in those texels, so one threshold works
for the game (density 3, Bramble 74 texels), the pilot golden (density 2, adult 50) and
Eastward (native 640 x 360, adult about 54).
"""
from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass, field, asdict

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
GAME_H = 74.0          # Bramble, feet to crown, in game texels (docs/godot.md, "The cast")
SEVERITIES = ('blocker', 'fault', 'polish')


# ------------------------------------------------------------------------------------------
# Findings
@dataclass
class Finding:
    detector: str                 # e.g. 'logic.water_staircase'
    severity: str                 # blocker, fault or polish
    box: tuple                    # (x0, y0, x1, y1) in native texels of the reviewed picture
    message: str                  # what is wrong, in one sentence
    fix: str                      # a concrete fix
    score: float = 0.0            # the measured value that tripped the threshold
    threshold: float = 0.0
    subject: str = ''             # the object id or kind, when known
    extra: dict = field(default_factory=dict)

    def to_json(self, scale: float = 1.0, origin=(0.0, 0.0)) -> dict:
        d = asdict(self)
        d['box'] = [int(v) for v in self.box]
        d['box_source'] = [int(round(origin[i % 2] + v * scale)) for i, v in enumerate(self.box)]
        return d


def merge_findings(fs: list[Finding], iou: float = 0.3) -> list[Finding]:
    """Drop near-duplicate findings of the same detector (overlapping boxes)."""
    out: list[Finding] = []
    for f in sorted(fs, key=lambda f: -f.score):
        if any(g.detector == f.detector and box_iou(g.box, f.box) > iou for g in out):
            continue
        out.append(f)
    return out


def box_iou(a, b) -> float:
    ix = max(0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = ix * iy
    if inter == 0:
        return 0.0
    ua = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / max(1, ua)


def box_overlap(a, b) -> float:
    """The share of the smaller box covered by the other."""
    ix = max(0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0, min(a[3], b[3]) - max(a[1], b[1]))
    sa = max(1, (a[2] - a[0]) * (a[3] - a[1]))
    sb = max(1, (b[2] - b[0]) * (b[3] - b[1]))
    return ix * iy / min(sa, sb)


# ------------------------------------------------------------------------------------------
# The native grid
def _edge_profile(a: np.ndarray, axis: int) -> np.ndarray:
    d = np.abs(np.diff(a, axis=axis)).sum(-1)
    return d.sum(axis=0) if axis == 1 else d.sum(axis=1)


def _period(p: np.ndarray, lo: float, hi: float):
    """The dominant period of an edge profile, its prominence (the best peak against the
    second-best one that is not a near neighbour) and the edge phase."""
    p = p - p.mean()
    n = len(p)
    N = 1 << 16
    F = np.fft.rfft(p * np.hanning(n), N)
    P = np.abs(F) ** 2
    fr = np.fft.rfftfreq(N)
    ok = (fr > 1 / hi) & (fr < 1 / lo)
    if not ok.any():
        return 1.0, 0.0, 0.0
    order = np.argsort(np.where(ok, P, 0))[::-1]
    best = order[0]
    second = next((j for j in order[1:4000] if abs(fr[j] - fr[best]) > 0.01), best)
    s = 1 / fr[best]
    prom = P[best] / max(P[second], 1e-9)
    # phase: edges sit where cos(2 pi (x - x0) / s) peaks; rfft uses exp(-2 pi i f x)
    x = np.arange(n)
    c = np.sum(p * np.exp(-2j * np.pi * x / s))
    x0 = (-np.angle(c) / (2 * np.pi) * s) % s
    return float(s), float(prom), float(x0)


def estimate_scale(rgb: np.ndarray, lo: float = 1.3, hi: float = 14.0) -> tuple[float, float, float]:
    """How many source pixels one art pixel covers, and where the cell lines fall in x and y.

    Colour changes along rows and columns fall on the art grid's cell lines, so the summed
    edge profile is periodic with the cell size, also for fractional upscales (a 3.14x
    Retina screenshot of the 2x game) and smooth resampling. The period is the profile's
    strongest spectral peak; it counts only when it clearly dominates (prominence 2.5 in
    both axes and both axes agree), otherwise the picture is taken as native art.
    """
    a = rgb[..., :3].astype(np.float32)
    if min(a.shape[:2]) < 24:
        return 1.0, 0.0, 0.0
    sx, px, x0 = _period(_edge_profile(a, 1), lo, hi)
    sy, py, y0 = _period(_edge_profile(a, 0), lo, hi)
    if px < 2.5 or py < 2.5 or abs(sx - sy) > 0.05 * max(sx, sy):
        return 1.0, 0.0, 0.0
    s = (sx + sy) / 2
    # an edge between pixels i-1 and i shows in the diff profile at index i-1, so the cell
    # line sits at x0 + 1 (in source pixel coordinates)
    return s, (x0 + 1) % s, (y0 + 1) % s


def to_native(img: Image.Image, scale: float | None = None) -> tuple[np.ndarray, float, tuple]:
    """The picture at its art grid as an RGBA array, plus the scale and origin used."""
    rgba = np.asarray(img.convert('RGBA'))
    if scale is None:
        s, px, py = estimate_scale(rgba[..., :3])
    else:
        s, px, py = float(scale), 0.0, 0.0
        if s > 1.01:
            _, px, py = estimate_scale(rgba[..., :3], lo=s - 0.05, hi=s + 0.05)
    if s <= 1.01:
        return rgba.copy(), 1.0, (0.0, 0.0)
    H, W = rgba.shape[:2]
    nx = int((W - px) // s)
    ny = int((H - py) // s)
    xs = np.clip((px + (np.arange(nx) + 0.5) * s).astype(int), 0, W - 1)
    ys = np.clip((py + (np.arange(ny) + 0.5) * s).astype(int), 0, H - 1)
    return rgba[ys][:, xs].copy(), s, (px, py)


# ------------------------------------------------------------------------------------------
# Colour
def lum(rgb: np.ndarray) -> np.ndarray:
    rgb = rgb[..., :3].astype(np.float32)
    return rgb @ np.array([0.299, 0.587, 0.114], np.float32)


def hsv(rgb: np.ndarray):
    """Hue in degrees, saturation and value in 0..1."""
    x = rgb[..., :3].astype(np.float32) / 255.0
    mx = x.max(-1)
    mn = x.min(-1)
    d = mx - mn
    h = np.zeros(mx.shape, np.float32)
    r, g, b = x[..., 0], x[..., 1], x[..., 2]
    m = d > 1e-6
    rm = m & (mx == r)
    gm = m & (mx == g) & ~rm
    bm = m & ~rm & ~gm
    h[rm] = (60 * ((g - b)[rm] / d[rm])) % 360
    h[gm] = 60 * ((b - r)[gm] / d[gm]) + 120
    h[bm] = 60 * ((r - g)[bm] / d[bm]) + 240
    s = np.where(mx > 1e-6, d / np.maximum(mx, 1e-6), 0)
    return h, s, mx


def keys(rgb: np.ndarray, levels: int = 32) -> np.ndarray:
    """A colour key per pixel, quantised to `levels` steps a channel (absorbs JPEG noise)."""
    q = (rgb[..., :3].astype(np.int32) * levels) // 256
    return (q[..., 0] * levels + q[..., 1]) * levels + q[..., 2]


def water_mask(rgb: np.ndarray, alpha: np.ndarray | None = None) -> np.ndarray:
    """Open water: blue to cyan, saturated, not sky-pale. Foam and falls are separate."""
    h, s, v = hsv(rgb)
    m = (h >= 185) & (h <= 235) & (s >= 0.32) & (v >= 0.25)
    if alpha is not None:
        m &= alpha
    return m


def foam_mask(rgb: np.ndarray) -> np.ndarray:
    h, s, v = hsv(rgb)
    return (v >= 0.82) & (s <= 0.3) & ((h >= 170) & (h <= 250) | (s <= 0.08))


def green_mask(rgb: np.ndarray) -> np.ndarray:
    h, s, v = hsv(rgb)
    return (h >= 55) & (h <= 160) & (s >= 0.18) & (v >= 0.12)


def regions(mask: np.ndarray, min_area: int = 1, connectivity: int = 1):
    """Labelled connected regions (scipy.ndimage.label) and their slices, filtered by area."""
    st = ndi.generate_binary_structure(2, connectivity)
    lab, n = ndi.label(mask, structure=st)
    if n == 0:
        return lab, []
    areas = ndi.sum(mask, lab, index=np.arange(1, n + 1))
    sl = ndi.find_objects(lab)
    out = [(i + 1, sl[i], int(areas[i])) for i in range(n) if areas[i] >= min_area]
    return lab, out


def slice_box(sl) -> tuple:
    return (sl[1].start, sl[0].start, sl[1].stop, sl[0].stop)


def same_colour_regions(rgba: np.ndarray, mask: np.ndarray | None = None, levels: int = 64):
    """Label 4-connected regions of one exact colour (quantised to `levels`)."""
    k = keys(rgba, levels)
    if mask is None:
        mask = np.ones(k.shape, bool)
    k = np.where(mask, k, -1)
    lab = np.zeros(k.shape, np.int32)
    nxt = 0
    for v in np.unique(k[k >= 0]):
        l, n = ndi.label(k == v)
        lab[l > 0] = l[l > 0] + nxt
        nxt += n
    return lab, nxt


# ------------------------------------------------------------------------------------------
# Contact sheets
COLOURS = {'blocker': (230, 40, 40), 'fault': (255, 150, 0), 'polish': (60, 160, 255)}


def annotate(native: np.ndarray, findings: list[Finding], path: str, zoom: int = 2,
             title: str = '') -> None:
    """The whole picture at `zoom` with every finding boxed and numbered."""
    im = Image.fromarray(native[..., :3].astype(np.uint8)).resize(
        (native.shape[1] * zoom, native.shape[0] * zoom), Image.NEAREST)
    d = ImageDraw.Draw(im)
    for i, f in enumerate(findings):
        x0, y0, x1, y1 = [v * zoom for v in f.box]
        c = COLOURS.get(f.severity, (255, 255, 0))
        d.rectangle([x0, y0, x1 - 1, y1 - 1], outline=c, width=2)
        d.rectangle([x0, y0, x0 + 22, y0 + 11], fill=c)
        d.text((x0 + 2, y0), str(i + 1), fill=(0, 0, 0))
    if title:
        d.rectangle([0, 0, 8 * len(title) + 8, 14], fill=(0, 0, 0))
        d.text((4, 1), title, fill=(255, 255, 255))
    im.save(path)


def crop_sheet(native: np.ndarray, findings: list[Finding], path: str, zoom: int = 4,
               cols: int = 4, cell: int = 280) -> None:
    """One enlarged crop per finding (the box plus a margin), labelled with its number,
    detector and severity: the evidence crops the auditors attach."""
    if not findings:
        Image.new('RGB', (cell, 40), (30, 30, 30)).save(path)
        return
    H, W = native.shape[:2]
    rows = (len(findings) + cols - 1) // cols
    sheet = Image.new('RGB', (cols * cell, rows * (cell + 26)), (24, 24, 24))
    d = ImageDraw.Draw(sheet)
    for i, f in enumerate(findings):
        x0, y0, x1, y1 = f.box
        m = max(4, int(0.25 * max(x1 - x0, y1 - y0)))
        cx0, cy0, cx1, cy1 = max(0, x0 - m), max(0, y0 - m), min(W, x1 + m), min(H, y1 + m)
        cr = Image.fromarray(native[cy0:cy1, cx0:cx1, :3].astype(np.uint8))
        z = max(1, min(zoom * 2, cell // max(1, max(cr.width, cr.height))))
        cr = cr.resize((cr.width * z, cr.height * z), Image.NEAREST)
        if cr.width > cell or cr.height > cell:
            cr.thumbnail((cell, cell), Image.NEAREST)
            z = cr.width / max(1, cx1 - cx0)
        dd = ImageDraw.Draw(cr)
        rx0, ry0 = (x0 - cx0) * z, (y0 - cy0) * z            # a thin box at a fractional zoom must not invert
        dd.rectangle([rx0, ry0, max(rx0, (x1 - cx0) * z - 1), max(ry0, (y1 - cy0) * z - 1)],
                     outline=COLOURS.get(f.severity, (255, 255, 0)), width=2)
        gx, gy = (i % cols) * cell, (i // cols) * (cell + 26)
        sheet.paste(cr, (gx, gy + 26))
        d.text((gx + 3, gy + 2), f'{i + 1}. {f.detector}', fill=COLOURS.get(f.severity, (255, 255, 0)))
        d.text((gx + 3, gy + 13), f'{f.subject[:40]}', fill=(220, 220, 220))
    sheet.save(path)


def write_json(path: str, data) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, 'w') as fh:
        json.dump(data, fh, indent=1)
        fh.write('\n')


def load_rgba(path: str) -> Image.Image:
    return Image.open(path).convert('RGBA')


def crop_nonblack(img: Image.Image) -> tuple[Image.Image, tuple]:
    """Trim a uniform near-black frame (window borders in screenshots)."""
    a = np.asarray(img.convert('RGB')).astype(int)
    L = a.sum(-1)
    rows = np.nonzero((L > 90).mean(1) > 0.2)[0]
    cols = np.nonzero((L > 90).mean(0) > 0.2)[0]
    if len(rows) < 10 or len(cols) < 10:
        return img, (0, 0)
    y0, y1, x0, x1 = rows.min(), rows.max() + 1, cols.min(), cols.max() + 1
    if y0 < 4 and x0 < 4 and y1 > a.shape[0] - 4 and x1 > a.shape[1] - 4:
        return img, (0, 0)
    return img.crop((x0, y0, x1, y1)), (x0, y0)


def clamp_box(b, W, H):
    return (max(0, int(b[0])), max(0, int(b[1])), min(W, int(math.ceil(b[2]))), min(H, int(math.ceil(b[3]))))
