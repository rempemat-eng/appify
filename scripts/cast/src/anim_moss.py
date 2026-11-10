"""Moss's table (contract v2): idle, walk, talk and work (arranging produce: an apple from the
basket on her left arm to the counter in front of her; the game faces her to the stall), and two
idle fidgets.

  - work: 12 drawings: the basket comes round, the hand dips in, lifts the apple, sets it down on
    the counter with a little press and comes back.
  - fidget_apple: she takes an apple from the basket, polishes it on her shawl, holds it up to
    look at it and puts it back.
  - fidget_basket: she hitches the basket up her forearm and smooths her apron."""
import anim
import anim_folk as F
from moss import REST_R, REST_L, SCALE, P0

A_STRIDE = 7.5
WALK_SPEED = F.walk_speed(A_STRIDE, SCALE)
BASKET = (8.0, 28.5, -0.5)          # the basket brought round in front of her (left arm in)
LW = (8.0, 32.5, -3.0)


def work():
    keys = []
    path = [(REST_R, None, 0.0), (BASKET, None, 0.3), (add(BASKET, (1.0, 3.0, 1.5)), 'hand', 0.3), ((10.0, 34.0, 2.0), 'hand', 0.8),
            ((14.0, 36.0, 4.0), 'hand', 1.5), ((14.5, 35.0, 4.5), (16.0, 36.5, 5.0), 1.6), ((9.0, 31.0, 9.0), None, 0.8), (REST_R, None, 0.2)]
    ms = [160, 150, 140, 150, 170, 150, 140, 140]
    for (h, apple, lean), t in zip(path, ms):
        keys.append((dict(handR=h, handL=LW, apple=apple, lean=lean, twist=-4.0, crouch=0.5 if lean > 1 else 0.0), t))
    # v2 in-betweens: into the basket, the lift, on the way to the counter and the way back
    # (not between the reach and the set-down, so the apple never lands before the hand does)
    keys, _ = anim.densify(keys, (0, 2, 3, 6), base=P0())
    return keys


IN = (9.0, 31.5, 1.0)                   # the right hand in the basket brought round in front of her


def fidget_apple(T):
    return F.fidget(T, [
        dict(handL=add(LW, (-1.0, -1.0, -3.0)), lean=0.1),                                     # brings the basket round
        dict(handL=LW, handR=(6.0, 27.0, 6.0), lean=0.2),
        dict(handL=LW, handR=IN, lean=0.4, crouch=0.3),                                         # into the basket
        dict(handL=LW, handR=add(IN, (0.5, 1.5, 0.5)), apple='hand', lean=0.3),               # takes one
        dict(handL=LW, handR=(9.0, 35.0, 3.0), apple='hand', breath=1),                       # to her shawl
        dict(handL=LW, handR=(9.0, 35.5, 0.5), apple='hand', breath=1),                       # polishes it
        dict(handL=LW, handR=(9.0, 35.0, 3.5), apple='hand', breath=1),
        dict(handL=LW, handR=(9.0, 35.5, 0.5), apple='hand', breath=1),
        dict(handL=LW, handR=(10.0, 41.0, 5.0), apple='hand', lean=-0.4, breath=1),           # holds it up to look
        dict(handL=LW, handR=(10.0, 41.5, 5.0), apple='hand', lean=-0.4, breath=1),
        dict(handL=LW, handR=add(IN, (0.5, 1.5, 0.5)), apple='hand', lean=0.3),               # back in
        dict(handL=LW, handR=IN, lean=0.3, crouch=0.2),
        dict(handL=add(LW, (-1.0, -1.0, -3.0)), handR=(4.0, 25.5, 11.0), lean=0.1, lag=0.4),
    ], [150, 130, 120, 140, 120, 130, 90, 90, 90, 150, 220, 130, 110, 140, 150])


def fidget_basket(T):
    return F.fidget(T, [
        dict(handL=(6.0, 28.5, -11.5), crouch=0.4, lean=0.2),                                  # dips to lift it
        dict(handL=(6.5, 33.5, -11.0), lean=-0.3, breath=1, lag=-0.4),                         # hitches it up
        dict(handL=(6.0, 30.5, -11.5), lean=0.0, breath=1, lag=0.5),                           # it settles
        dict(handR=(6.0, 27.0, 10.0), lean=0.4),                                                # smooths the apron
        dict(handR=(6.5, 25.0, 9.5), lean=0.6, crouch=0.6),
        dict(handR=(5.0, 26.0, 11.0), lean=0.3),
    ], [150, 120, 140, 160, 150, 160, 140, 160])


def add(a, b):
    return tuple(x + y for x, y in zip(a, b))


TABLE = {
    'idle': F.idle(REST_R, REST_L),
    'walk': F.v2(F.walk(REST_R, REST_L, A_STRIDE, keep_l=True), loop=True),
    'talk': F.v2(F.talk(REST_R, REST_L, 'R', palm=(9.0, 33.0, 8.0)), loop=True),
    'work': F.v2(work(), loop=True),
}
FIDGETS = ['fidget_apple', 'fidget_basket']
TABLE['fidget_apple'] = F.v2(fidget_apple(TABLE), loop=False)
TABLE['fidget_basket'] = F.v2(fidget_basket(TABLE), loop=False)
EXTRA = {c: dict(F.EXTRA_FIDGET) for c in FIDGETS}
RELEASE = {}
RELEASE_ANCHOR = {}
EQUIP = {'basket': dict(always=True, may_hide={'E', 'N'})}   # held before her: hidden from behind
