"""Compose the cast in the density-3 woodland on the 960x540 grid; scale exactly 2x for 1080p.

world(): the woodland strip (two bands of scene_3x joined by a minimum-error seam through the
grass, whole pixels, no blending).  shadow(): hard-edged cast shadow multiplied into the ground,
offset right and down (house style).  frame(): one 960x540 frame with sprites sorted by feet."""
import numpy as np
from PIL import Image

S = '/tmp/claude-0/-home-claude/740ae43f-1e6f-546c-a61b-113cd8f682fd/scratchpad'
OUT = S + '/examples/eastward'
_W = None


def world():
    global _W
    if _W is not None:
        return _W
    sc = np.array(Image.open(S + '/opt/pilot_d3/scene_3x.png').convert('RGB')).astype(int)
    A = sc[800:1340]
    B = sc[1300:1840]
    ov = 48
    a, b = A[:, -ov:], B[:, :ov]
    err = ((a - b) ** 2).sum(-1).astype(float)
    H = err.shape[0]
    cost = err.copy()
    back = np.zeros_like(err, int)
    for y in range(1, H):
        prev = cost[y - 1]
        l = np.r_[np.inf, prev[:-1]]
        r = np.r_[prev[1:], np.inf]
        st = np.stack([l, prev, r])
        k = st.argmin(0)
        back[y] = np.arange(ov) + k - 1
        cost[y] += st.min(0)
    seam = np.zeros(H, int)
    seam[-1] = cost[-1].argmin()
    for y in range(H - 1, 0, -1):
        seam[y - 1] = back[y, seam[y]]
    mid = np.zeros((H, ov, 3), int)
    for y in range(H):
        mid[y, :seam[y]] = a[y, :seam[y]]
        mid[y, seam[y]:] = b[y, seam[y]:]
    _W = np.concatenate([A[:, :-ov], mid, B[:, ov:]], 1).astype(np.uint8)
    return _W


MUL = np.array([0.66, 0.66, 0.76])


def shadow(canvas, x, y, rx, ry):
    yy, xx = np.mgrid[0:canvas.shape[0], 0:canvas.shape[1]]
    m = ((xx + 0.5 - x - 2) / rx) ** 2 + ((yy + 0.5 - y - 0.5) / ry) ** 2 <= 1
    canvas[m] = (canvas[m] * MUL).astype(np.uint8)


def blit(canvas, spr, x, y):
    """spr: RGBA array; (x, y) = its top-left on the canvas (whole pixels)."""
    h, w = spr.shape[:2]
    x0, y0 = max(x, 0), max(y, 0)
    x1, y1 = min(x + w, canvas.shape[1]), min(y + h, canvas.shape[0])
    if x1 <= x0 or y1 <= y0:
        return
    s = spr[y0 - y:y1 - y, x0 - x:x1 - x]
    m = s[..., 3] > 0
    c = canvas[y0:y1, x0:x1]
    c[m] = s[..., :3][m]


def compose(cam_x, actors, extras=()):
    """actors: list of (fig, rendered RGBA, foot x, foot y, shadow rx, ry) in screen coords."""
    canvas = world()[:, cam_x:cam_x + 960].copy()
    for (fig, spr, fx, fy, rx, ry) in actors:
        shadow(canvas, fx, fy, rx, ry)
    for (fig, spr, fx, fy, rx, ry) in sorted(actors, key=lambda a: a[3]):
        blit(canvas, spr, int(round(fx)) - fig.gx, int(round(fy)) - fig.gy)
    for fn in extras:
        fn(canvas)
    return canvas


def up2(canvas):
    return np.repeat(np.repeat(canvas, 2, 0), 2, 1)
