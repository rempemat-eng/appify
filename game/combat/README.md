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

## Clock/resource binding checkpoint

`AbilityRunner` now connects clock eligibility, synchronous time slices and release commands.
Time slices run with the interval's old action/form state before clock mutation. Resource reload
and strict heat eligibility boundaries split coarse advances, allowing held primary to resume
without depending on frame size. The <92 heat comparison crosses by a 0.000001 heat-point numeric
margin to avoid a zero-time retry loop; no cooldown, heat rate or resource balance is changed.
A token produces at most one release command, carrying live `powered_at_release`, historical
`powered_at_commit` and actual emitted round count. Special resource activation runs at contact,
before the new powered clock starts. Inactive time freezes both components.

This is a simulation binding, not world effects or a production Player driver. Callers can drain
clock events and release commands separately; they must not independently consume resources again.
Future world effects must capture launch state, present contact before dispatch, and preserve all
stateful rules listed above. The runner does not select facings: forthcoming presentation must use
manifest-defined available facings and release_anchor (A decision6403878182), without assuming four.

Next executable step: implement finite canonical effect commands/handlers and stateful rules from
#245, then the granted Player hook and J/A presentation bridge. Do not apply raw damage to world HP
until Claude A approves the mapping: #275's 1:1 health proposal is not yet that approval. #279's
progression modifiers remain outside this task; powered-form changes need the canonical owner's
approval and must not rewrite the base kit. No new dodge, balance or reward rule is adopted here.

Validation includes seven runner integration cases: cancellation across all fourteen kits,
coarse/fine held fire across reload and overheat, partial fan at exact canonical contact, form
expiry during preparation, special heat cap/cooling interval order and inactive/reconfigure state.
The initial partial-fan test mistakenly sampled0.18s, before canonical0.1824s contact; its failure
was corrected to read the canonical release value, without changing production timing. Final test
result and exact source tree are recorded on PR #261. Full verify/art/CI/rendered/device testing
remains pending until the port is complete. Keep DRAFT.

## Projectile launch checkpoint

`AbilityProjectiles.plan` now converts a release command plus canonical ground origin, locked
continuous action direction, current aim point and airborne height into independent launch records.
It ports the original E/q/I projectile branches for every primary, Cairn's secondary boulder and
Pendle's partial fan (powered secondary emits no projectiles). It captures live release form,
keeps Mote's shards per-shot, and computes Morel's finite clamped flight lifetime. It never consumes
ammo again. Radius, velocity, ground seed and damage stay in canonical units; source-texel release
anchors and the explicit factor3/Cairn manifest conversion belong to a later world bridge. Launch
height is independent of ground position. The planner is not attached to Runner or Player yet.

`test/combat/projectile-oracle.json` has68 samples from original hash-verified #245 E/q/I code,
covering all14 kits in both forms with straight and diagonal/airborne shots, fan counts0..3,
powered stock, base/powered boulders and Morel range clamps. To reproduce, extract #245's
`canonical/reference/adapter.mjs` and `original-modules.json` into the same directory, then run:
`node game/test/combat/build_projectile_oracle.mjs /path/to/reference/adapter.mjs`.
GdUnit compares complete launch records, plus real Runner partial-fan/form-expiry cases.

Remaining: finite projectile advancement, swept collision/terrain, impact/status/field/stateful
handlers, contact presentation and Player hook. These launch records are not an implemented world
combat system; do not attach them as raw HP hits pending Claude A's mapping decision. Keep DRAFT.

## Finite projectile flight checkpoint

`AbilityFlight.tick` advances one **player** projectile by the original fixed 1/60 second step
in canonical planar coordinates. It preserves clipped final motion, age/remaining, inclusive
arena bounds, swept target overlap, stable original centre-distance contact order, piercing
and previous-hit snapshots, splash placement on a contacted target, and seal-before-target
water amplification (including ties). It returns independent shot snapshots and ordered impact
commands; it does not mutate targets/seals, apply damage/status, consume resources or attach
anything to Player. Discard a shot when `alive` is false. Enemy projectiles are deliberately
rejected until their guard/decoy path is ported.

The 189 free-flight cases and 14 contact cases in `test/combat/flight*-oracle.json` are sampled
from original hash-checked F, with test-only impact tracing in T. Reproduce with:
`node game/test/combat/build_flight_oracle.mjs /path/to/original-modules.json`.
Tests also cover swept tunnelling, dead/previous targets, hit history before insertion,
short final steps, single expiry blasts, inclusive bounds and zero-length sweeps.

Next: implement original T/B/Y/G impact/status/field handlers and remaining stateful kit rules,
then wire a once-per-release dispatcher and the granted Player hook. The dispatcher must apply
ordered impacts synchronously and refresh alive targets between projectile ticks. This primitive
uses caller-provided target snapshots; it is not the full multi-projectile/world loop. Canonical
F contains arena bounds, not world terrain: the later Godot bridge must add terrain collision
against actual APIs without inventing a new reference rule. No terrain collision is claimed here.
Health application remains gated on A's mapping decision, and presentation remains A/J-owned.
Full verify/art-repro/hosted CI and rendered/device checks remain pending. Keep DRAFT.

## Impact/status/reagent checkpoint

`AbilityImpacts` ports original T/B/Y/G as a pure snapshot reducer. Its public `impact`,
`damage`, `field` and `react` functions deep-copy input, then preserve canonical damage,
vulnerability, knockback/clamps, immortal targets, defeat/tether cleanup, Tam frost/shatter,
Iona nearest-target lightning, powered arrow root transfer, harpoon tether, water slow,
Rook designation, field caps/oldest eviction, and breadth-first reagent reactions.

This boundary intentionally uses the reference state's canonical x/y, camelCase dictionaries.
It is NOT an actor-health adapter: do not feed its damage to foundation low-integer HP until
A settles the mapping. Convert `AbilityFlight` snake_case/Vector2 shot snapshots in a future
explicit dispatcher adapter; don't pass them directly. Live player power controls passives,
while captured projectile power controls projectile effects, as in the original. Apply each
returned state synchronously before processing the next impact. No elapsed-time field ticks,
status countdown, melee/stateful release dispatcher, terrain, guard/decoy path or Player hook
is supplied by this reducer. These remain next steps, not completed gameplay.

Effects preserve kind, geometry, lifetime, serial ordering and optional line origins; colours
are omitted for presentation to supply. Field `source` remains the originating character.
`impact-oracle.json` compares207 original-engine snapshots (all projectile launch families,
base/powered passives, lethal/surviving targets, caps/clamps, chain/cycle/duplicate patch ids,
immortality, zero/negative damage, coincident knockback and the80-event cap). Only colour
fields are stripped from the original snapshots. Original function bodies are unmodified:
`node game/test/combat/build_impact_oracle.mjs /path/to/original-modules.json`.
Keep DRAFT; full verify/art/CI and rendered/device validation remain pending.

Canonical edge retained for owner review: when powered Tam's shatter is itself lethal, original B
records defeat/kills in the nested call and again in its caller. The207th oracle records this
unchanged. C60 does not silently correct the canonical rule; A/canonical owner should decide
before final integration. No reward is granted by this standalone reducer.
