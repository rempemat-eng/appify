"""Hale's table (contract v2): idle, walk, talk and work (hammering at the anvil once the forge
is restored; the game faces her to the anvil), and two idle fidgets.  The hammer stays in her
right hand throughout.

  - work: 12 drawings: the hammer rises (load), hangs at the top, a smear on the way down, the
    strike (sparks), the rebound, then the lift eases back to the top.
  - fidget_hammer: she lifts the hammer, turns it to look along the face, and lets it hang again.
  - fidget_neck: she rubs the back of her neck with her left hand and lets the arm drop."""
import anim
import anim_folk as F
from anim_folk import add
from hale import REST_R, REST_L, SCALE, P0

A_STRIDE = 8.5
WALK_SPEED = F.walk_speed(A_STRIDE, SCALE)


def work():
    L = (14.0, 40.0, -3.0)                      # left hand: tongs holding the bar on the anvil
    W = dict(bar=1, handL=L, footR=(-2.0, 0.0), footL=(3.0, 0.0), poleR=(-1.0, -0.4, 0.6))
    keys = [
        (dict(W, handR=(-7.0, 46.0, 12.0), hammer=(-0.7, 0.75, 0.0), lean=-1.0), 140),                 # 0 raised (load)
        (dict(W, handR=(-8.0, 47.0, 12.0), hammer=(-0.8, 0.6, 0.0), lean=-1.2), 170),                  # 1 top
        (dict(W, handR=(9.0, 48.0, 7.0), hammer=(0.6, 0.7, 0.0), lean=0.5), 50),                       # 2 swing
        (dict(W, handR=(13.0, 41.0, 6.0), hammer=(1.0, -0.3, 0.0), lean=1.5, crouch=1.0, sparks=0.0), 60),   # 3 strike
        (dict(W, handR=(12.5, 43.0, 6.0), hammer=(0.9, 0.1, 0.0), lean=1.2, crouch=0.5, sparks=0.5), 90),    # 4 rebound
        (dict(W, handR=(2.0, 45.0, 10.5), hammer=(-0.3, 0.95, 0.0), sparks=1.0), 110),                 # 5 lift
        (dict(W, handR=(-2.0, 48.0, 11.0), hammer=(-0.35, 0.95, 0.0), lean=-0.5), 120),
        (dict(W, handR=(-5.5, 47.0, 11.5), hammer=(-0.65, 0.8, 0.0), lean=-0.9), 100),
    ]
    # v2 in-betweens: the ease up into the top, the smear just before contact, the settle out of
    # the rebound and the ease back up into the load (none behind her head in W: the hammer stays in sight)
    keys, _ = anim.densify(keys, (0, 2, 4, 6), base=P0())
    for P, _ms in keys:
        if P.get('sparks') is None:
            P.pop('sparks', None)
    return keys


def fidget_hammer(T):
    up = (8.0, 38.0, 10.5)
    return F.fidget(T, [
        dict(handR=(4.0, 28.5, 13.5), hammer=(0.4, -0.9, 0.0), lean=0.2),                          # gathers it
        dict(handR=(7.0, 34.0, 11.5), hammer=(0.6, 0.6, 0.0), lean=0.1),                           # lifts
        dict(handR=up, hammer=(0.3, 0.95, 0.0), lean=-0.2, breath=1),                              # head up before her eyes
        dict(handR=up, hammer=(0.0, 1.0, 0.25), lean=-0.3, breath=1),                      # turns it: looks along the face
        dict(handR=up, hammer=(-0.15, 1.0, -0.2), lean=-0.3, breath=1),
        dict(handR=up, hammer=(0.3, 0.95, 0.0), lean=-0.2, breath=1),
        dict(handR=(6.0, 31.0, 12.0), hammer=(0.5, -0.5, 0.0), lean=0.1),                          # lowers
        dict(handR=(2.5, 25.5, 14.5), hammer=(0.2, -1.0, 0.0), lag=0.4),                           # hangs, a small swing past
    ], [150, 110, 120, 160, 200, 200, 140, 120, 140, 160])


def fidget_neck(T):
    """A long day at the anvil: she reaches up and rubs the back of her neck, rolls her shoulders
    and lets the arm drop."""
    nape = (-1.5, 50.5, -5.0)
    return F.fidget(T, [
        dict(handL=(3.0, 36.0, -12.5), lean=0.2),                                                 # the arm comes up
        dict(handL=(1.0, 46.0, -9.5), lean=0.0, breath=1),
        dict(handL=nape, lean=-0.3, breath=1, face='shut'),                                       # hand on her nape
        dict(handL=add(nape, (0.0, 0.8, 1.5)), lean=-0.5, breath=1, face='shut'),                 # rubs it
        dict(handL=add(nape, (0.0, -0.6, -1.0)), lean=-0.4, breath=1, face='shut'),
        dict(handL=add(nape, (0.0, 0.8, 1.5)), lean=-0.5, breath=1),
        dict(handL=(2.0, 40.0, -11.5), lean=0.2, breath=0, lag=0.6),                              # drops the arm
        dict(handL=(1.5, 27.5, -14.5), lean=0.1, lag=0.3),
    ], [150, 110, 120, 130, 110, 110, 130, 130, 140, 160])


TABLE = {
    'idle': F.idle(REST_R, REST_L),
    'walk': F.v2(F.walk(REST_R, REST_L, A_STRIDE), loop=True),
    'talk': F.v2(F.talk(REST_R, REST_L, 'L', palm=(9.0, 33.0, -7.0)), loop=True),
    'work': F.v2(work(), loop=True),
}
FIDGETS = ['fidget_hammer', 'fidget_neck']
TABLE['fidget_hammer'] = F.v2(fidget_hammer(TABLE), loop=False)
TABLE['fidget_neck'] = F.v2(fidget_neck(TABLE), loop=False)
EXTRA = {c: dict(F.EXTRA_FIDGET) for c in FIDGETS}
RELEASE = {}
RELEASE_ANCHOR = {}
EQUIP = {'hammer': dict(always=True, may_hide={'W', 'N', 'NW'}), 'bar': dict(clips={'work': list(range(12))}, may_hide={'N'})}
