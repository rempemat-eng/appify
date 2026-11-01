# Folk progression runtime (Y1/r1)

`game/core/folk_progression.gd` extends the existing authored progression proposal
with an isolated Godot state API. It consumes `catalogue.json` and the fourteen folk
files in `game/data/progression/`; it does not edit them or rebuild their trees.
The level/point rules come from `docs/vision/progression.md`, section 2. Levels are
shared, points are per folk, and every level from 2 supplies one point. Node levels,
costs and prerequisite IDs come from each tree. Weapon tiers use the authored
1/8/16/24 thresholds, sockets, forge conditions and folk-specific material costs.

Every balance number remains a placeholder. `catalogue_status()` and every offer
carry the original proposal/placeholder status. The runtime does not apply node
numbers, weapon mechanics or damage multipliers to C60's canonical kits. New
unlocks marked `touches_canonical` return `c60_approval_required`; this reflects the
existing approval requirement, not approval or implementation of those effects.
Restore can retain their historical ownership without activating an effect.

## API

Create `FolkProgression.new()`, read the existing JSON documents, and call
`configure(catalogue, documents)`. Configuration validates all used nested fields,
unique IDs, the prerequisite graph and matching common/folk tier gates. Unknown
metadata is retained. A rejected configuration preserves the previous model;
a successful one explicitly starts a new level-1 progression projection.

- `advance_level(level)` accepts a whole level in the configured range at or above
  the current one. It grants no XP or currency and does not repeat point grants.
- `join_folk(id)` creates an unspent tree at the shared level. A late joiner inherits
  the highest reached weapon tier, capped at tier 3; Starfall remains a forge step.
- `available_points(id)` computes `level - 1 - spent`, rather than keeping a second
  balance that can drift. An unjoined/unknown folk returns -1.
- `node_offer(id, node)` returns detached metadata, availability and a reason:
  unknown, owned, level, prerequisite, points, C60 approval or available.
  `unlock_node` records a permitted node exactly once.
- `tier_offer(id, tier, access)` checks next-tier order, shared level and all
  authored Boolean forge conditions. Its cost uses the folk's named material,
  falling back to common costs only if the folk has none. It never spends money.
- `record_tier` records an eligible forge result. The caller must validate the
  offer and complete Y3's approved payment/forge transaction before recording it.
  This API is not a shop, receipt verifier or cross-system transaction manager.
- `snapshot()` returns a deep copy. `restore(projection)` validates the proposed
  level, each owned node/prerequisite/budget and each reached tier's level before
  replacing state. Node ownership need not be stored in purchase order. Unknown
  extensions, including the catalogue's proposed XP/look/fitting fields, stay
  opaque and are copied. Known level/tier integers are normalised after JSON.
- `changed(snapshot)` emits detached state only after a successful change.

The projection follows the existing catalogue's proposed paths:
`progression.level`, `folk.<id>.nodes`, and `folk.<id>.weapon_tier`. It does not add
these to SaveGame or install an autoload. A restoring caller should pass this
projection, not assume this validates the rest of an entire game save. Current
content IDs are validated; unknown future folk/node ownership requires an explicit
schema/content migration, rather than being silently dropped.

## Integration boundary

Claude A retains live integration and review of the proposal. This PR does not
change Player, abilities, combat, quests, SaveGame, project settings, UI, art or
package/check registrations. There is no XP curve, earning rule, currency sink,
respec transaction or "choose for me" UI. Y3 owns payment/respec integration; C60
owns canonical effect approvals. Noncanonical effect numbers are metadata too,
not new applied combat behaviour. The runtime alone cannot prove the full Y1–Y3
systems work in the slice.

The GdUnit suite consumes all fourteen real trees and every authored tier. It
covers level and forge boundaries, point conservation and prerequisites, independent
folk, late-join inheritance, canonical approval refusal, JSON restore/unknown fields,
alias isolation, failed-operation signals and malformed/cyclic/unsupported inputs.
It runs through the existing `npm run check:godot`. These are engine/data tests,
not gameplay, rendered-art, native-phone or balance-approval evidence.
