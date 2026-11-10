"""Ada Fern's table (contract v2): idle, walk, talk and work (sweeping her doorstep with the
birch broom), and two idle fidgets.

  - work: a 12-drawing sweep loop: the bristles push out, the body follows a beat later.
  - fidget_tap: she lifts the broom and knocks the dust out of the bristles, twice.
  - fidget_hair: she tucks her bob behind her left ear."""
import math
import anim
import anim_folk as F
from anim_folk import add
from ada import REST_R, REST_L, SCALE

A_STRIDE = 8.5
WALK_SPEED = F.walk_speed(A_STRIDE, SCALE)


def work():
    keys = []
    for i in range(12):
        s = math.sin(2 * math.pi * i / 12)
        c = math.cos(2 * math.pi * i / 12)
        keys.append((dict(broom='sweep', bgrip=27.0, handR=(7.0 + 1.0 * c, 26.5, 4.0 + 4.0 * s), handL=(3.0, 38.0, -1.0 + 3.0 * s),
                          lean=1.5, crouch=0.5, twist=1.5 * s, lag=0.3 * s, footR=(1.0, 0.0), footL=(-2.0, 0.0)), 100))
    return keys


def fidget_tap(T):
    up = lambda d: add(REST_R, (0.5, d, 0.0))
    return F.fidget(T, [
        dict(handR=up(-0.8), crouch=0.4, lean=0.2),                         # a small dip to lift
        dict(handR=up(4.0), lean=-0.2, breath=1),                           # the broom comes up
        dict(handR=up(-0.5), lean=0.3, crouch=0.3, lag=0.5),                # knock
        dict(handR=up(3.0), lean=-0.1),
        dict(handR=up(-0.5), lean=0.3, crouch=0.3, lag=0.5),                # knock
        dict(handR=up(0.8), lean=0.1, blink=True),
    ], [150, 120, 130, 70, 110, 70, 140, 160])


def fidget_hair(T):
    ear = (3.0, 58.5, -9.5)
    return F.fidget(T, [
        dict(handL=(4.0, 34.0, -12.0), lean=0.1),
        dict(handL=(5.0, 50.0, -10.5), breath=1),
        dict(handL=add(ear, (1.0, 0.5, 0.5)), breath=1),                    # fingers at the fringe
        dict(handL=ear, breath=1, blink=True),                              # tucks it behind the ear
        dict(handL=add(ear, (-1.5, -1.0, 0.0)), breath=1),
        dict(handL=(4.0, 44.0, -11.5)),
        dict(handL=(2.0, 29.0, -12.5), lag=0.4),
    ], [150, 120, 130, 140, 160, 120, 130, 140, 160])


TABLE = {
    'idle': F.idle(REST_R, REST_L),
    'walk': F.v2(F.walk(REST_R, REST_L, A_STRIDE, swing_r=1.5), loop=True),
    'talk': F.v2(F.talk(REST_R, REST_L, 'L', palm=(8.0, 33.0, -7.0)), loop=True),
    'work': F.v2(work(), loop=True),
}
FIDGETS = ['fidget_tap', 'fidget_hair']
TABLE['fidget_tap'] = F.v2(fidget_tap(TABLE), loop=False)
TABLE['fidget_hair'] = F.v2(fidget_hair(TABLE), loop=False)
EXTRA = {c: dict(F.EXTRA_FIDGET) for c in FIDGETS}
RELEASE = {}
RELEASE_ANCHOR = {}
EQUIP = {'broom': dict(always=True, may_hide={'W', 'N'})}
