"""Mossback tortoise's table.  Telegraph (the stomp, matching the ring on the ground): the head
draws in under the brow plate, the front rears off the ground and hangs.  Attack: the slam, both
front feet down, a dust ring.  Stagger: it sits stunned with its head out (the recover window,
when its front is open).  Freed: the shard pops out of the moss, the head comes out, it blinks."""
import anim_critter as AC
import tortoise  # its ramps (for the checks) and SCALE

STRIDE = 3.0
WALK_SPEED = round(4 * STRIDE / 0.56 * tortoise.SCALE, 1)


def telegraph():
    return [
        (dict(neck=0.7, crouchF=0.8), 110),                                                       # dips (anticipation)
        (dict(neck=0.35, crouchF=0.0), 110),                                                      # head draws in
        (dict(neck=0.0, crouchF=-3.0, crouchH=0.5, lifts=(3.0, 3.0, 0, 0)), 120),                # rears
        (dict(neck=0.0, crouchF=-5.0, crouchH=0.8, lifts=(5.0, 5.0, 0, 0)), 120),
        (dict(neck=0.0, crouchF=-6.5, crouchH=1.0, lifts=(6.5, 6.5, 0, 0)), 120),
        (dict(neck=0.0, crouchF=-7.5, crouchH=1.0, lifts=(7.5, 7.5, 0, 0)), 120),                # hangs
        (dict(neck=0.0, crouchF=-7.8, crouchH=1.0, lifts=(7.8, 7.8, 0, 0), shake=0.3), 120),
        (dict(neck=0.0, crouchF=-7.8, crouchH=1.0, lifts=(7.8, 7.8, 0, 0), shake=-0.3), 130),
    ]


def attack():
    return [
        (dict(neck=0.0, crouchF=1.5, dust=0.0, fFR=11.0, fFL=11.0), 40),                         # slam
        (dict(neck=0.2, crouchF=1.0, dust=0.4, fFR=11.0, fFL=11.0), 50),
        (dict(neck=0.4, crouchF=0.5, dust=0.75, fFR=10.5, fFL=10.5), 50),
        (dict(neck=0.5, crouchF=0.3, dust=0.95), 50),
    ]


def hurt():
    return [
        (dict(neck=0.2, crouchF=0.8, shake=-1.2, blink=True), 70),
        (dict(neck=0.2, crouchF=0.8, shake=1.0, blink=True), 80),
        (dict(neck=0.6, shake=-0.4), 80),
        (dict(), 90),
    ]


def stagger():
    seq = [(dict(neck=1.0, head=(0.5, -0.5), crouchF=1.0, crouchH=0.5, stars=i / 7.0,
                  shake=(-0.5, 0.0, 0.5, 0.0)[i % 4], blink=(i in (2, 5))), 90) for i in range(7)]
    seq = [(dict(neck=0.5, crouchF=0.3), 70)] + seq[1:-1] + [(dict(), 90)]
    return seq


def freed():
    return [
        (dict(neck=0.3, shard=0.0, blink=True), 110),
        (dict(neck=0.2, shard=0.25, blink=True), 90),
        (dict(neck=0.2, shard=0.5, calm=0.6), 100),
        (dict(neck=0.3, shard=0.8, calm=1.0), 120),
        (dict(neck=0.5, shard=1.0, calm=1.0), 160),                                              # the head comes out
        (dict(neck=0.8, shard=1.0, calm=1.0), 160),
        (dict(neck=1.0, shard=1.0, calm=1.0, head=(0.5, 0.5)), 200),
        (dict(neck=1.0, shard=1.0, calm=1.0, head=(0.5, 0.5), blink=True), 140),
        (dict(neck=1.0, shard=1.0, calm=1.0, head=(0.0, 0.0)), 300),
        (dict(neck=1.0, shard=1.0, calm=1.0, shake=-1.0), 90),                                   # a little shiver
        (dict(neck=1.0, shard=1.0, calm=1.0, shake=1.0), 90),
        (dict(neck=1.0, shard=1.0, calm=1.0), 240),
    ]


TABLE = {
    'idle': AC.idle(breathe=0.3, nod=0.5),
    'move': AC.move(dict(plant=True), stride=STRIDE, lift=2.0, bob=0.5),          # plant: the stance foot stays put (K3)
    'telegraph': telegraph(),
    'attack': attack(),
    'hurt': hurt(),
    'stagger': stagger(),
    'freed': freed(),
    'freed_move': AC.freed_move(dict(plant=True), stride=STRIDE, lift=2.0, bob=0.5),
}
RELEASE = {'attack': 0}
RELEASE_ANCHOR = {'attack': 'strike'}
EQUIP = {'shard': AC.shard_rule(TABLE, may_hide=()), 'moss': dict(always=True), 'shell': dict(always=True)}
