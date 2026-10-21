"""Weathering and wall dressing for old town brick and stone (Claude C, 20 Oct).

Candidate parts for the city kit, not a patch on today's sprites: Claude A's ruling
(crew board to-c-2110) keeps these out of the old Cogsworth sprites, which the asset
ledger grades REWORK (redraw). The city kit builds its walls from them.

- weathered_bricks: a brick wall weathered whole brick by whole brick (a hotter-fired
  brick, smoke-blackened ones under the eaves, a buff repair, lime repointing, salt and
  moss low down, damp stretches, each brick's east end turned from the light).
- weathered_stone: ashlar greyed by soot under the eaves, with damp creeping up.
- pattress, airbrick, soot_over, bill, window_box, fire_buckets, hopper: small built
  things a wall carries, in the house ramps, lit from the upper left, in clusters.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from pixel import Canvas, noise2, smooth_noise  # noqa: E402
import detail  # noqa: E402
from materials import MATERIALS, WOOD, RED  # noqa: E402

IRON, BRICK, ASHLAR = (MATERIALS[k] for k in ('iron', 'brick', 'ashlar'))


def rect_set(x, y, w, h):
    return {(xx, yy) for yy in range(y, y + h) for xx in range(x, x + w)}


HOT = ['#3A1C14', '#5E2C1E', '#844230', '#A85A40', '#C87A58']  # a hotter-fired brick, redder
SOOTED = ['#1C1426', '#2C2433', '#3B343E', '#4A4448', '#655B57']  # a brick blackened by the town's smoke
STOCK = MATERIALS['path']  # a buff stock brick, laid in a repair


def weathered_bricks(cv: Canvas, x0: int, y0: int, w: int, h: int, ramp, seed: int = 0, base: int = 3):
    """A Cogsworth brick wall in the house's ramps, weathered as old town brick is, whole
    brick by whole brick (detail in clusters, never single pixels): detail.bricks' courses,
    then here and there a hotter-fired brick, one blackened by smoke (more of them high up,
    under the eaves the smoke rolls along), a patch rebuilt in buff stock brick, a stretch
    repointed in pale lime mortar, salt blooming white on the bricks of the lowest courses
    and moss in their joints where the wall stands in the damp."""
    detail.bricks(cv, x0, y0, w, h, ramp, seed=seed, base=base)
    courses = h // 3
    for ci in range(courses + 1):
        shift = 3 if ci % 2 else 0
        high = 1 - ci / max(1, courses)  # 1 at the top course, 0 at the foot
        low = ci >= courses - 2
        for bi in range(-1, w // 6 + 2):
            n = noise2(bi, ci, 1830 + seed)
            fam = None
            if n > 0.93:
                fam = HOT if ramp is not HOT else BRICK
            elif n < 0.05 + 0.12 * high:
                fam = SOOTED
            elif smooth_noise(bi * 6.0, ci * 3.0, 14, 1831 + seed) > 0.8:
                fam = STOCK
            repoint = smooth_noise(bi * 6.0, ci * 3.0, 12, 1832 + seed) < 0.2
            salt = low and noise2(bi, ci, 1833 + seed) > 0.55
            t = base + (1 if noise2(bi, ci, 1834 + seed) > 0.7 else 0)
            if smooth_noise(bi * 6.0, ci * 3.0, 18, 1836 + seed) > 0.68:
                t -= 1  # a damp stretch of wall, whole bricks a step darker
            for r in range(3):
                y = y0 + ci * 3 + r
                if y >= y0 + h:
                    continue
                for c in range(6):
                    x = x0 + bi * 6 + c - shift
                    if not (x0 <= x < x0 + w):
                        continue
                    if r == 2 or c == 5:
                        if repoint:
                            cv.set(x, y, ASHLAR[2] if r == 2 else ASHLAR[1])  # fresh lime mortar
                        elif low and r == 2 and noise2(bi, ci, 1835 + seed) > 0.6 and c < 4:
                            cv.set(x, y, '#2E4426' if c % 2 else '#3E5A30')  # moss along the bed joint
                        continue
                    f_ = fam or ramp
                    if fam is not None or t != base or (r == 1 and c == 4):
                        k_ = t + 1 if r == 0 else t - 1 if c == 4 else t  # lit top, the body, its east end turned from the light
                        cv.set(x, y, f_[max(0, min(len(f_) - 1, k_))])
                    if salt and r == 1 and 1 <= c <= 3:
                        cv.set(x, y, '#B8B0A0' if c < 3 else '#9A9284')  # salt dried out of the brick


# ---- what a Cogsworth wall carries (the facade pass, 20 Oct): each a small built thing in
# the house's ramps, lit from the upper left, in clusters of two or more pixels

def pattress(cv: Canvas, x: int, y: int):
    """A cast-iron tie plate, the end of a rod that holds the floor to the wall: a round
    plate 4 px across, lit on its upper left, its nut in the middle."""
    for (dx, dy) in ((1, 0), (2, 0), (0, 1), (1, 1), (2, 1), (3, 1), (0, 2), (1, 2), (2, 2), (3, 2), (1, 3), (2, 3)):
        cv.set(x + dx, y + dy, IRON[4] if dx + dy < 2 else IRON[3] if dx + dy < 4 else IRON[1])
    cv.set(x + 1, y + 1, IRON[0]); cv.set(x + 2, y + 1, IRON[0])


def airbrick(cv: Canvas, x: int, y: int):
    """A cast-iron air brick low in the wall, a brick's size: its frame and two slots."""
    cv.hline(x, y, 5, IRON[3]); cv.hline(x, y + 2, 5, IRON[1])
    cv.set(x, y + 1, IRON[2]); cv.set(x + 1, y + 1, IRON[0]); cv.set(x + 2, y + 1, IRON[0])
    cv.set(x + 3, y + 1, IRON[0]); cv.set(x + 4, y + 1, IRON[2])


def soot_over(cv: Canvas, x0: int, x1: int, y: int, rows: int = 4):
    """Smoke has stained the bricks over an opening: darkest just above it, fading upward
    and narrowing, a step darker on whatever ramp it lies on."""
    for i in range(rows):
        for x in range(x0 + i, x1 - i):
            if noise2(x // 2, (y - i) // 2, 1840) > 0.25 + i * 0.12:
                detail.shade(cv, x, y - 1 - i, 1)


def bill(cv: Canvas, x: int, y: int, w: int = 5, h: int = 7, ink='#2E4A7A', paper='#E8DCC0'):
    """A bill pasted to the wall: its paper, a heading in colour, lines of print, a corner
    curling off in the damp."""
    for (xx, yy) in rect_set(x, y, w, h):
        c = paper if xx < x + w - 1 else '#B8AE94'
        if yy - y in (1, 2) and x < xx < x + w - 1:
            c = ink
        elif (yy - y) % 2 == 0 and yy - y > 3 and x < xx < x + w - 2:
            c = '#6A6458'
        cv.set(xx, yy, c)
    cv.set(x + w - 1, y + h - 1, '#9A9078')


def window_box(cv: Canvas, x: int, y: int, w: int, flowers=('#D23A30', '#F0A020')):
    """A timber box on two brackets under a sill: earth, leaves, flowers in pairs."""
    for (xx, yy) in rect_set(x, y, w, 3):
        cv.set(xx, yy, WOOD[3] if yy == y else WOOD[2] if xx < x + w - 2 else WOOD[1])
    cv.set(x + 1, y + 3, IRON[2]); cv.set(x + w - 2, y + 3, IRON[2])
    for k in range(0, w - 1, 2):
        cv.set(x + k, y - 1, '#3E6438'); cv.set(x + k + 1, y - 1, '#2E4A2E')
        if noise2(x + k, y, 1841) > 0.4:
            col = flowers[(k // 2) % len(flowers)]
            cv.set(x + k, y - 2, col); cv.set(x + k + 1, y - 2, col)
        elif noise2(x + k, y, 1842) > 0.5:
            cv.set(x + k, y - 2, '#5A8046')


def fire_buckets(cv: Canvas, x: int, y: int, n: int = 3):
    """A row of red fire buckets hung on a board, each lit on its rim."""
    cv.hline(x - 1, y - 1, n * 4 + 1, WOOD[3]); cv.hline(x - 1, y, n * 4 + 1, WOOD[1])
    for k in range(n):
        bx = x + k * 4
        for (xx, yy) in rect_set(bx, y + 1, 3, 3):
            cv.set(xx, yy, RED[3] if yy == y + 1 else RED[2] if xx < bx + 2 else RED[1])
        cv.set(bx + 1, y + 1, '#E8E2D0')  # the white of FIRE on its side


def hopper(cv: Canvas, x: int, y: int, y1: int):
    """A downpipe from a hopper head under the gutter, its clips, a shoe at the foot."""
    for (xx, yy) in rect_set(x - 1, y, 5, 3):
        cv.set(xx, yy, IRON[3] if yy == y else IRON[2] if xx < x + 2 else IRON[1])
    for yy in range(y + 3, y1):
        cv.set(x, yy, IRON[3]); cv.set(x + 1, yy, IRON[2]); cv.set(x + 2, yy, IRON[1])
        if (yy - y) % 8 == 0:
            cv.hline(x - 1, yy, 5, IRON[2])
    cv.hline(x, y1, 4, IRON[2])


def weathered_stone(cv: Canvas, x0: int, y0: int, w: int, h: int, ramp, seed: int = 0):
    """Dressed stone as the town's smoke and damp have left it, after detail.stones: broad
    patches blackened by soot where rain does not wash the face (thickest under the eaves),
    green damp creeping up from the foot, and rust run down from an iron fixing here and
    there, each in clusters, keeping every stone's lit and shaded edges."""
    idx = {tuple(int(c[k:k + 2], 16) for k in (1, 3, 5)): i for i, c in enumerate(ramp)}
    DAMP = ['#24301E', '#34442A', '#4A5A36', '#627044', '#7C8854', '#96A268']
    STAINED = ['#2E2A2E', '#46403F', '#5E5753', '#78706A', '#948A80', '#B0A698']  # the stone a step greyer under its soot
    for y in range(y0, y0 + h):
        high = 1 - (y - y0) / max(1, h)
        for x in range(x0, x0 + w):
            i = idx.get(cv.get(x, y)[:3])
            if i is None:
                continue
            if smooth_noise(x, y * 1.3, 9, 1845 + seed) > 0.78 - 0.18 * high:
                cv.set(x, y, STAINED[max(0, min(5, i))])
            elif y > y0 + h - 7 and smooth_noise(x, y, 4, 1846 + seed) > 0.55 - (y - (y0 + h - 7)) * 0.04:
                cv.set(x, y, DAMP[max(0, min(5, i))])
