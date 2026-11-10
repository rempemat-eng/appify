"""Thornback's table: the boarlet's clips (same family), the telegraph deeper (k 1.2) and fitted
to the elite's 0.65 s wind-up; both shards pop out together when freed."""
import anim_critter as AC
import anim_boarlet as B
import thornback  # noqa: F401  (its ramps, for the checks)
from thornback import SCALE

WALK_SPEED = round(4 * B.STRIDE / 0.56 * SCALE, 1)
TABLE = dict(B.TABLE, telegraph=B.telegraph(1.2))
RELEASE = dict(B.RELEASE)
RELEASE_ANCHOR = dict(B.RELEASE_ANCHOR)
EQUIP = {'shard': AC.shard_rule(TABLE), 'tusk': dict(always=True, may_hide={'N'}), 'bramble': AC.shard_rule(TABLE)}
