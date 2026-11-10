"""Bramble toad's table.  Telegraph (the sighting pose): it rises on its front legs and lifts its
head along its facing, the throat sac swells and a glint gathers at its lips, then it holds dead
still.  Attack: the spit (the thorn seed leaves on drawing 0), mouth wide, the sac empties and it
rocks back.  Stagger: flattened, dazed.  Freed: the shard pops out of its back, it blinks, puffs
once and settles."""
import math
import anim_critter as AC
import toad  # its ramps (for the checks) and SCALE

STRIDE = 2.5
WALK_SPEED = round(4 * STRIDE / 0.56 * toad.SCALE, 1)


def hop(g):
    return dict(bob=-1.6 * max(0.0, math.sin(2 * math.pi * g)), crouchH=0.6 * math.cos(2 * math.pi * g),
                reach=1.5 * math.sin(2 * math.pi * g))


def telegraph():
    return [
        (dict(crouchF=0.5, head=(0.0, -0.5), sac=0.1), 110),                                    # settles (anticipation)
        (dict(crouchF=-1.0, crouchH=0.5, head=(0.5, 1.0), sac=0.3), 110),                        # rises on the front legs
        (dict(crouchF=-2.0, crouchH=0.8, head=(1.0, 1.5), sac=0.5, glint=0.2), 120),
        (dict(crouchF=-2.5, crouchH=1.0, head=(1.0, 2.0), sac=0.7, glint=0.4), 120),
        (dict(crouchF=-2.5, crouchH=1.0, head=(1.2, 2.0), sac=0.85, glint=0.6), 120),            # sighting: dead still
        (dict(crouchF=-2.5, crouchH=1.0, head=(1.2, 2.0), sac=0.95, glint=0.8), 120),
        (dict(crouchF=-2.6, crouchH=1.0, head=(1.2, 2.0), sac=1.0, glint=1.0, shake=0.3), 120),
        (dict(crouchF=-2.6, crouchH=1.0, head=(1.2, 2.0), sac=1.0, glint=1.0, shake=-0.3), 130),
    ]


def attack():
    return [
        (dict(crouchF=-2.0, crouchH=1.0, head=(2.0, 1.5), mouth=1.0, sac=0.4), 60),              # spit
        (dict(crouchF=-0.5, crouchH=1.5, head=(1.0, 1.0), mouth=0.8, sac=0.1), 90),
        (dict(crouchF=0.5, crouchH=1.0, head=(-0.5, 0.5), mouth=0.3), 120),                      # rocks back
        (dict(crouchF=0.3, head=(0.0, 0.0)), 130),
        (dict(), 100),
    ]


def hurt():
    return [
        (dict(crouchF=1.5, crouchH=1.5, head=(-1.0, -1.0), shake=-1.2, blink=True), 70),
        (dict(crouchF=1.5, crouchH=1.5, head=(-1.0, -1.0), shake=1.0, blink=True), 80),
        (dict(crouchF=0.7, crouchH=0.7, shake=-0.4), 80),
        (dict(), 90),
    ]


def stagger():
    seq = [(dict(crouchF=1.5, crouchH=1.2, head=(0.0, -1.0), mouth=0.2, stars=i / 7.0,
                  shake=(-0.6, 0.0, 0.6, 0.0)[i % 4], blink=(i in (1, 4))), 90) for i in range(7)]
    seq = [(dict(crouchF=0.3, head=(0.0, 0.0)), 70)] + seq[1:-1] + [(dict(), 90)]
    return seq


def freed():
    return [
        (dict(crouchF=1.0, crouchH=1.0, shard=0.0, blink=True), 110),
        (dict(crouchF=1.0, crouchH=1.0, shard=0.25, blink=True), 90),
        (dict(shard=0.5, calm=0.6), 100),
        (dict(shard=0.8, calm=1.0, sac=0.3), 110),
        (dict(shard=1.0, calm=1.0, sac=0.35, bob=-0.5), 140),                                     # puffs once
        (dict(shard=1.0, calm=1.0, sac=0.3), 120),
        (dict(shard=1.0, calm=1.0, blink=True), 140),
        (dict(shard=1.0, calm=1.0, crouchF=0.5, crouchH=0.5), 260),                              # settles
        (dict(shard=1.0, calm=1.0, blink=True), 140),
        (dict(shard=1.0, calm=1.0), 300),
        (dict(shard=1.0, calm=1.0, crouchH=0.8), 160),
        (dict(shard=1.0, calm=1.0), 180),
    ]


TABLE = {
    'idle': [(dict(k, sac=0.12 * (0.5 + 0.5 * math.sin(2 * math.pi * i / 8))), ms) for i, (k, ms) in enumerate(AC.idle(breathe=0.3, nod=0.3))],
    'move': AC.move(stride=STRIDE, lift=1.5, bob=0.0, extra=hop),
    'telegraph': telegraph(),
    'attack': attack(),
    'hurt': hurt(),
    'stagger': stagger(),
    'freed': freed(),
    'freed_move': AC.freed_move(stride=STRIDE, lift=1.5, bob=0.0, extra=hop),
}
RELEASE = {'attack': 0}
RELEASE_ANCHOR = {'attack': 'muzzle'}
EQUIP = {'shard': AC.shard_rule(TABLE), 'glint': dict(clips={'telegraph': [4, 5, 6, 7]}, may_hide={'N'})}
