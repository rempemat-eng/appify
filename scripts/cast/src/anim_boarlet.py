"""Boarlet's table.  Telegraph: the head drops, the rump rises, the front right hoof paws twice
and kicks dust, then it holds low and quivers.  Attack: the charge, stretched low.  Stagger: dazed
with sparks circling.  Freed: the shard pops out, it shakes itself off, sits back and stands."""
import anim
import anim_critter as AC
import boarlet  # its ramps (for the checks) and SCALE

STRIDE = 4.0
GAIT = dict(fFR=7.5, fFL=7.5, fHR=-6.5, fHL=-6.5, plant=True)   # plant: the stance hoof stays put (B3)
WALK_SPEED = round(4 * STRIDE / 0.56 * boarlet.SCALE, 1)


def telegraph(k=1.0):
    D = dict(crouchF=3.5 * k, crouchH=-2.5 * k, head=(0.5, -3.0 * k), mouth=0.6)
    return [
        (dict(head=(-0.5, 1.5), crouchH=0.5, bob=-0.3), 110),                                   # rear up (anticipation)
        (dict(D, crouchF=1.5 * k, head=(0.0, -2.0)), 110),
        (dict(D, lifts=(3.0, 0, 0, 0), fFR=11.5), 120),                                          # paw: lift
        (dict(D, fFR=6.0, dust=0.1), 110),                                                       # scrape back
        (dict(D, lifts=(3.0, 0, 0, 0), fFR=11.5, dust=0.5), 120),                                # paw again
        (dict(D, fFR=6.0, dust=0.15), 110),
        (dict(D, crouchF=4.0 * k, head=(1.0, -3.5 * k), shake=0.6, dust=0.6), 130),             # hold low, quiver
        (dict(D, crouchF=4.0 * k, head=(1.0, -3.5 * k), shake=-0.6, dust=0.85), 140),
    ]


def attack():
    C = dict(crouchF=2.0, crouchH=-0.5, head=(3.0, -3.0), mouth=1.0, bob=0.5)
    return [
        (dict(C, fFR=15.0, fFL=13.0, fHR=-14.0, fHL=-12.0, lifts=(1.5, 0, 0, 1.5), dust=0.2), 40),   # launch, stretched
        (dict(C, fFR=12.0, fFL=15.0, fHR=-11.0, fHL=-14.0, lifts=(0, 1.5, 1.5, 0), dust=0.5), 40),
        (dict(C, fFR=15.0, fFL=13.0, fHR=-14.0, fHL=-12.0, lifts=(1.5, 0, 0, 1.5), dust=0.8), 50),
        (dict(C, fFR=12.0, fFL=11.0, fHR=-9.0, fHL=-10.0, crouchF=3.0, dust=0.95), 50),              # dig in
    ]


def hurt():
    return [
        (dict(head=(-2.0, 2.0), crouchH=1.0, shake=-1.5, blink=True), 70),
        (dict(head=(-1.5, 1.5), crouchH=1.0, shake=1.2, blink=True), 80),
        (dict(head=(-0.5, 0.5), crouchH=0.5, shake=-0.6), 80),
        (dict(head=(0.0, 0.0), shake=0.0), 90),
    ]


def stagger():
    D = dict(crouchF=1.5, head=(0.0, -2.0), mouth=0.3)
    seq = [(dict(D, stars=i / 7.0, shake=(-0.8, 0.0, 0.8, 0.0)[i % 4], blink=(i in (2, 5)), head=(0.0, -2.0 + 0.5 * (i % 2))), 90)
            for i in range(7)]
    seq = [(dict(crouchF=2.5, crouchH=-0.5, head=(1.0, -2.0), mouth=0.6), 70)] + seq[1:-1] + [(dict(), 90)]
    return seq


def freed():
    return [
        (dict(head=(-1.0, 2.0), crouchH=1.0, shard=0.0, blink=True), 110),                       # the shard pops
        (dict(head=(-1.0, 2.5), crouchH=1.0, shard=0.25, blink=True), 90),
        (dict(head=(-0.5, 1.5), shard=0.5, calm=0.6), 100),
        (dict(head=(0.0, 1.0), shard=0.8, calm=1.0), 110),
        (dict(shard=1.0, calm=1.0, shake=-2.0, head=(0.0, 1.0)), 70),                            # shakes itself off
        (dict(shard=1.0, calm=1.0, shake=2.0, head=(0.0, 1.0)), 70),
        (dict(shard=1.0, calm=1.0, shake=-1.5, head=(0.0, 1.0)), 70),
        (dict(shard=1.0, calm=1.0, shake=1.0), 70),
        (dict(shard=1.0, calm=1.0, crouchH=3.0, head=(0.0, 2.0)), 180),                          # sits back
        (dict(shard=1.0, calm=1.0, crouchH=3.5, head=(0.0, 2.5), blink=True), 160),
        (dict(shard=1.0, calm=1.0, crouchH=3.5, head=(0.0, 2.5)), 260),
        (dict(shard=1.0, calm=1.0, crouchH=1.0, head=(0.5, 1.0)), 140),                          # stands
        (dict(shard=1.0, calm=1.0), 160),
    ]


TABLE = {
    'idle': AC.idle(),
    'move': AC.move(GAIT, stride=STRIDE),
    'telegraph': telegraph(),
    'attack': attack(),
    'hurt': hurt(),
    'stagger': stagger(),
    'freed': freed(),
    'freed_move': AC.freed_move(GAIT, stride=STRIDE),
}
RELEASE = {'attack': 0}
RELEASE_ANCHOR = {'attack': 'strike'}
EQUIP = {'shard': AC.shard_rule(TABLE), 'tusk': dict(always=True, may_hide={'N'})}
