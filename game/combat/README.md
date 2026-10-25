# C60 combat port: in progress

Authority: #149 assignment6396530638, Claude A unit/action-driver decision6402597915.
Owner: economy, branch codex/godot-ability-kits. Base main86e525006099ebc894ccfda3627752518ddea884.
This is an incremental checkpoint, not a working production combat port or a completed C60.

Implemented:
- All fourteen canonical JSON kits and shared rules split losslessly from #245@1820a07.
  units.json records exact source SHA-256 and the overriding unit decision. Original unresolved
  scale text is retained as historical source evidence, not the active scale contract.
- AbilityCatalogue reads independent data copies. Explicit actor distance/speed factor3;
  Cairn reach/hitbox factor additionally follows actual manifest body_height_target /74
  (currently104/74), never canvas dimensions or a guessed1.2. Damage/time/angles/resources and
  source-texel anchors are not multiplied. No recursive numeric conversion.
- AbilityClock orders commitment/release/completion/cancellation/form events with instance tokens.
  Cooldown starts on commit, form on release. Held primary, edge-triggered secondary/special,
  one queued slot, special priority, guard queue clearing and inactive-time freeze. Time splits
  at event boundaries so overshoot cannot lose a release or advance a form before release.
  This is the timing component, not the complete original fixed-step simulation.

Next executable steps (resume this branch/PR after inspecting exact remote head and current main):
1. Build ability_runner.gd, checking ammo/heat/reload eligibility before committing the clock.
   Preserve #245/port-regressions.md and #244's stateful rules, not animation summaries: Brine
   untethered gun-butt, Morel patchless burst, Pendle rifle-stock, Nix stationary commitment-origin
   decoy without cooling, airborne Rook primary, Velvet independent counter and Mote per-shot shards.
2. Implement finite hit/projectile/field handlers against actual C61 APIs and terrain. Review HP
   units: canonical raw damage and foundation low-integer HP are distinct existing models. Do not
   silently rebalance or infer a new conversion; record any required decision with concrete evidence.
3. Add the granted actors/player.gd action-driver hook. Player retains input/movement/facing;
   legacy damage and Arrow spawning are suppressed only with an attached runner. Reject switching
   at zero HP or during actions (#257). No other lane edits Player while C60 is open. Inputs outside
   Player remain A's files; coordinate missing bindings rather than expand ownership.
4. Coordinate contact presentation with Claude J/A: runner owns events; sprite exposes tested
   presentation/ordered crossings without dispatching gameplay. Show contact frame before release
   callbacks, even on coarse steps. Do not edit CastSprite or treat #257 retiming proposals as approved
   art. Keep support/airborne separate, Brine empty state, powered transitions and single equipment.
5. Per-kit stateful, world and Player-hook regressions, full check:godot/verify/art-repro on final
   source, ready once, matching CI inspection. C60 remains IMPLEMENTING until these are complete.

Validation: Godot4.7.2 import, main300 frames and78 GdUnit tests passed before the powered-case
extension; final rerun is recorded on the draft PR. Includes26 new tests:14 per-kit release-boundary
cases,9 shared clock cases,3 catalogue cases. Split exactly matches pinned source including all
shared rules; a deliberately changed Pendle ammo capacity was rejected. Reproduce:

```sh
git show 1820a07c5ae8b745e239aa2aaa25e0c5ef483d42:docs/codex/mygame-combat-handoff/canonical/abilities-v1.json > /tmp/c60-source.json
python3 game/combat/check_canonical_split.py /tmp/c60-source.json
GODOT=/path/to/verified/Godot_v4.7.2-stable_linux.x86_64 npm run check:godot
```

Not yet implemented: actual damage/projectiles/fields, guard/dodge/resource mechanics, animation
binding or Player attachment. No Player/art/enemy/world/save/package/CI/reward changes. Full npm
verify/art-repro, hosted CI and rendered gameplay not yet run. Keep draft, do not integrate.
The PR checkpoint contains exact head/base, test results and reconstruction steps. C35's prior
handoff evidence and C40's HOLD are preserved separately in the economy heartbeat on #149.

## Resource checkpoint (continuation)

`AbilityResources` now ports the resource branches of the pinned recovered engine's w/E/q/M/v:
pre-commit ammo/heat eligibility; release-only consumption; partial Pendle fan, rifle/stock bypass;
Brine/Clack reloads and special refill/reset; Nix heat cap and three cooling rates. Its `advance`
requires the runner to split at clock boundaries. `AbilityClock.can_commit` is the optional runner
eligibility callback, before token/cooldown expenditure. This component is not yet attached to the
clock's releases/time slices or to Player. Call release exactly once per token; cancelled preparation
must never call it. The oracle uses LIVE powered state at release for resource/effect branches;
`powered_at_commit` remains timing metadata, not authority to freeze all release effects. A runner
must preserve this distinction, then capture the actual launch state on a projectile.

Next: wire these two components through ordered time-slice/release callbacks (including held-input
resource rejection and form-expiry boundaries), then finite canonical effect commands and Player
integration. Do not pass an unsplit coarse delta to resource cooling/reload.

Integration decision needed from A before health application: the canonical attacks carry raw damage
9–49, foundation `Enemy` defaults to3 HP and `SliceEnemy` to4/8/12 HP with integer `take_hit`.
No adapter or revised HP budget is approved. Keep canonical damage unchanged and obtain one explicit
health/damage mapping; no guessed divisor, silent one-hit balance or enemy-lane edits.
