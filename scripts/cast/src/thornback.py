"""Thornback (elite): an old wild boar of the deep woods, heavier and darker than a boarlet, with
long curved tusks, a mossy grey-brown coat and a bramble grown over its back, rooted around a
second, larger Starfall shard (two shards: the right shoulder and the back).  The boarlet's body
drawn 1.35x larger, so it reads as the same family and as the bigger threat.  About 42 px tall.

Telegraph (0.65 s, the elite's shorter tell): the boarlet's, faster and deeper.  Freed: both
shards pop out together."""
from ew import mat
import critter as C
import boarlet

mat('tback',    ['#1E1814', '#38302A', '#5A4C40', '#7E6E5C', '#A2927A'])
mat('tback_dk', ['#120E0C', '#221A16', '#362A22', '#4C3C30'])
mat('tsnout',   ['#4A2E2A', '#7A5048', '#A2766A', '#C89E8C'])

ID = 'thornback'
NAME = 'Thornback'
HEIGHT = 56
BAND = (50, 72)
ONE_BODY = True
DETACHED_OK = ('shard', 'shardglow', 'cream', 'gold', 'tell')
SCALE = 1.8
LOOK = dict(coat='tback', dark='tback_dk', snout='tsnout', tusk=4.0, ridge=5.0, canes=True, back_shard=True)


def P0(**k):
    return C.P0(**k)


def build(f, facing, P):
    boarlet.build(f, facing, P, LOOK)


def draw(facing='S', P=None, W=None, H=None):
    return C.draw_fig(build, facing, P or P0(), SCALE)
