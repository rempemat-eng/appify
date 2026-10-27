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

## Field/current and status phase checkpoint

`AbilityFields.tick_fields` ports original `_`: fixed1/60 field lifetime and tick cadence,
ordered damage, gravity pull (heavy targets resist), passive suppression on gravity damage,
ice slow, expiration after the final tick, and powered Mirra's player-to-seal current chain.
Currents follow surviving seal insertion order and hit each target once across all segments.
It shares the canonical damage/event/effect reducers rather than changing passive or defeat rules.
`tick_statuses` ports only L's status prelude: root/slow/stun/vulnerability countdown, strict
three-second frost expiry, and dead-target defeat countdown. It never runs legacy enemy AI,
even in live mode; C61 retains AI ownership.

Both are independent, input-preserving canonical snapshot phases. They do not advance state.time,
state.tick, player timers/form, projectiles, turret clocks or effect lifetimes. The future fixed-step
dispatcher must preserve the original phase order: time/player/action/movement, enemy statuses/AI,
projectiles with synchronous impacts, fields/currents, turrets, effect expiry and end-of-wave rules.
The field phase deliberately lets an expiring field act before removing it. Do not combine these
phases by applying all status expiry after field damage, or reduce a coarse delta in one pass.

`field-oracle.json` holds208 whole-state comparisons from hash-verified original `_` and L bodies.
For L comparisons the original mode is `encounter` to skip its old AI after the status prelude;
a separate live-mode test proves the port still leaves AI untouched. Cases include all8 field kinds,
base/powered passives, final ticks, shared/degenerate current segments, dead/immortal targets,
strict frost boundary and repeated status-before-field phases up to190 ticks. Reproduce with
`node game/test/combat/build_field_oracle.mjs /path/to/original-modules.json`.

Next: remaining stateful releases/melee/guard/decoy/turrets, explicit Flight-to-canonical snapshot
adapter, fixed-step once-per-token dispatcher and granted Player hook. World HP and the inherited
Tam duplicate-defeat edge still await A/canonical-owner decisions at the existing PR checkpoint;
no mapping or correction is inferred here. This is not integrated gameplay. Keep DRAFT; full
verify/art/hosted CI/rendered/device checks remain unfinished.

## Turret phase checkpoint

`AbilityTurrets.tick` ports the original fixed1/60 N phase on canonical snapshots. Rook's
surviving turrets follow the player in array order, aim only at the designated living target
strictly within190 canonical units of the player, and fire only after the cooldown and
strict55-unit post-interpolation leash tests. No autonomous target acquisition is added.
Each shot captures canonical turret-pulse data, ordered serial IDs and finite flight duration.
As in the reference, an expiring turret may fire on its final tick before removal. Wrong
character, inactive form or dead player clears turrets without launching a shot.

The caller owns active/playing gates, form/designation expiry and original phase order.
Invoke this phase after projectiles and fields: newly launched pulses remain age0 until the
next projectile phase. This method never advances player/time/effect clocks or dispatches
world HP damage. It deep-copies input and deliberately does not inspect designationRemaining:
the player phase clears designation before this phase, as in the original. Formation uses
survivor array index rather than remembered left/right identity, including a lone survivor.

`turret-oracle.json` compares126 whole-state snapshots from hash-verified, unmodified original N.
Reproduce with `node game/test/combat/build_turret_oracle.mjs /path/to/original-modules.json`.
Coverage includes missing/dead/invalid designations, strict range/leash boundaries, final ticks,
coincident-aim fallback, wrong/dead/expired owners, survivor ordering and repeated phases.
Colour alone is omitted for presentation, consistent with the other snapshot reducers.
Next: stateful action/melee/guard/decoy releases, Flight snapshot adapter, once-per-token dispatcher,
contact bridge and the granted Player hook. Health mapping/Tam edge remain A-owned decisions.
Full verify/art/hosted/rendered/device validation remains pending; keep DRAFT.

Turret oracle numbers use little-endian IEEE-754 binary encoding for non-integer values.
Godot4.7.2's JSON/literal decimal conversion rounds the17-digit remaining lifetime
0.016666676666666668 down enough that subtracting1/60 falls below1e-8, whereas the
original JS double stays just above it. A direct binary-decode regression preserves the
original side of this strict expiry boundary; no gameplay epsilon or test tolerance was
widened. Formation interpolation uses7/60, the exact double of the reference coefficient,
instead of a long decimal literal subject to the same parser rounding.

## Ordered player-projectile phase checkpoint

`AbilityProjectilePhase` supplies the explicit camelCase/x-y ↔ snake_case/scalar-point adapter
between the canonical snapshot reducers and `AbilityFlight`. Unknown shot fields and hit
history are deep-copied and preserved. Spatial conversion here stays in canonical units;
actor scaling and source-texel anchors remain future world/presentation boundaries.

Its fixed-step `tick` rebuilds target/seal snapshots before each projectile, applies ordered
water-shaped effects and impact commands synchronously, and then keeps only surviving shots.
This avoids stale targets after an earlier kill or reagent reaction. Contact history is
inserted after each impact as in F, preserving powered arrow root transfer. The original
per-shot contact list/order remains unchanged. It clears all shots on initial defeat; enemy shots now use the canonical defence/decoy path below.

The phase advances no world time, player/form/status/field/turret/effect clocks, owns no
active/playing gate and does not settle a wave. It is not attached to Player or Godot actor
health. Call it once per1/60 step in the documented phase order; never replay its impacts.
New turret shots are created later in the step and move next time.

`projectile-phase-oracle.json` has189 whole-state comparisons against original unmodified F
and real T/B/Y/G after hash verification. Reproduce with
`node game/test/combat/build_projectile_phase_oracle.mjs /path/to/original-modules.json`.
It covers canonical launch families (including melee/no-shot releases), repeated phases,
consecutive kills, root transfer, seal amplification, reagent reactions, expiry/outside
blasts and defeat cleanup. Exact IEEE754 fixture doubles avoid decimal-parser boundary
changes. All numeric comparisons use1e-6 and discrete outcomes remain exact.
Seven near-boundary cases exposed a real Vector2 float32 rounding error: x320.000001
survived inside the arena and a gap10.000001 incorrectly hit a target. `AbilityFlight`
now shares one scalar-double core: the phase calls `tick_scalar` with x/y dictionaries;
legacy `tick` converts Vector2 inputs/outputs only at its compatibility boundary. Sweeps,
entry tests, contact ordering, movement and inclusive bounds retain double precision.
No gameplay epsilon or test tolerance was widened. The original failures are now regressions. The first fixture builder
incorrectly assumed all primary releases produced a projectile; melee kits are now covered
as empty launches, without inventing a projectile for them.

Next: stateful action/melee releases, full fixed-step dispatcher/contact bridge
and granted Player hook. World HP and Tam duplicate-defeat remain A/canonical-owner decisions.
Keep DRAFT; full npm verify/art/hosted/rendered/device validation remains pending.


## Canonical defence and enemy projectiles

`AbilityDefence.damage` ports original P, guard break and defeat-interrupted power cleanup
on snapshots, without converting damage to Godot HP. Frontal guard uses the original dot
threshold and guard cost; full absorption preserves queued actions. Exhausted guard breaks
before any residual hit, which can replace the break animation. Powered Velvet primes a
counter only on absorption. Airborne Rook avoids melee/field hits, not projectiles. Death
clears projectiles/fields/turrets and interrupts power without Ashe's expiry finisher.

`AbilityProjectilePhase.tick` accepts mixed player/enemy shots in array order. Enemy swept
collisions break all live intersecting echo/hologram fields but do not absorb the bolt;
the same bolt can still hit the player. Guard uses the shot's previous position, exactly
as original F. A lethal hit clears earlier survivors and stops later shots. Scalar doubles
preserve contact/bounds thresholds. No player, field or global clocks advance here.

`defence-oracle.json` has 460 whole-state comparisons from hash-verified unmodified P/F
and their real helpers. Includes all fourteen kits, guard depletion/overflow, front/rear
and threshold hits, airborne cases, defeat/power cleanup, capped event history, mixed-shot
ordering, decoys and strict contact/expiry bounds. Regenerate using
`node game/test/combat/build_defence_oracle.mjs /path/to/original-modules.json`.
This remains pure canonical simulation; Godot Player/health/contact attachment is unfinished.

## Powered-form exit checkpoint

`AbilityFormExit.finish` ports original X on an independent canonical snapshot. It clears
Rook's turrets/designation on either exit. Ashe's normal living exit sets power to zero
before its forward finisher, temporarily uses current aim rather than the committed action
direction, damages the captured distance-ordered beam targets, restores the action direction,
then creates the capped/clamped flame patch. Interrupted/dead exits never launch that finisher.
Misses, serial/effect order and the 80-event cap match the reference. Other fields and shots
survive normal exit, as in X; this is not generic effect deletion or defeat cleanup.

The caller owns expiry detection and exactly-once invocation, including the later Player
phase's threshold/order. This transition does not advance clocks, attach Player, apply world
HP or replace the existing defence reducer's interrupted-death path. Stateful releases,
fixed-step dispatcher/contact and Player integration remain unfinished. Keep DRAFT.

`form-exit-oracle.json` has130 whole-state comparisons against hash-verified unmodified X
and its real S/A/B/Y helpers. Covers all14 kits, both exit reasons, living/dead players,
Ashe cardinal/diagonal aim, lethal/immortal targets, beam boundaries, field/event caps and
misses. Regenerate with `node game/test/combat/build_form_exit_oracle.mjs /path/to/original-modules.json`.
Exact IEEE754 fixture numbers and 1e-6 comparisons follow the existing snapshot suites.
Full npm verify/art/hosted/rendered/native/device validation remains pending.

## Arc, beam and body-limited dash checkpoint

`AbilityStrikes` ports original O/H, S/A and C as independent canonical snapshots. Arc
membership is captured before damage/passives mutate targets. Beams capture eligible
segment hits, retain array order for equal distances, then hit the closest or all captured
targets; only `lunge` applies its canonical knockback. Misses, effect/serial order and
passive/defeat handling use the existing reducers. Dash uses the nearest living body in
its strictly open side-clearance corridor, a two-unit stop gap and arena clamps. It does
not test world terrain. No action/resource clocks, actor movement or HP conversion occur.

`strike-oracle.json` contains166 whole-state comparisons from hash-verified original
O/S/C and their unmodified helpers: all14 kits, powered/base passives, arc/beam/clearance
boundaries, dead/immortal targets, cardinal/diagonal/zero direction, stable ties, misses
and capped events. Regenerate with
`node game/test/combat/build_strike_oracle.mjs /path/to/original-modules.json`.
Fixtures retain exact IEEE754 numbers, full state comparison and input-immutability checks.

Next: stateful secondary/special releases using these primitives, then the fixed-step
player/dispatcher and granted Player hook. World HP and Tam duplicate-defeat remain owner
decisions; this checkpoint does not resolve them. C60 remains IMPLEMENTING and PR261 DRAFT.
Full npm verify/art, matching hosted CI, rendered/native/device validation remain pending.

## Secondary release checkpoint

`AbilitySecondary.release` ports original q on an input-preserving canonical snapshot for
all fourteen characters. It retains committed action direction, Morel's patchless burst or
powered reagent chain, Brine's heavy-target versus light-target reel and untethered strike,
Pendle's partial fan/reload or powered rifle stock, Nix's commitment-origin decoy and
Rook's vault timer. Melee/passives, serial/effect ordering, field caps/clamps and airborne
projectile launch state share the existing canonical reducers. No world actor is attached.

This method includes Pendle secondary ammo/reload consumption. The future dispatcher must
choose one authoritative resource application and synchronize the resource component; it
must not call both this mutation and AbilityResources.release for the same token. It also
launches Cairn/Pendle projectiles itself; do not duplicate them via AbilityProjectiles.plan.
The caller owns contact presentation, eligibility, once-per-token dispatch and clock expiry.

`secondary-oracle.json` contains298 whole-state cases from hash-verified original q and
unmodified helpers. Covers all14 kits in both forms, three directions and lethal/surviving
targets; reagent range/chain, tether reach/coincident/heavy cases, partial fans, field caps,
clamps, passives and empty/capped events. Exact IEEE754 fixture numbers and1e-6 comparisons
match the other reducers. Reproduce with
`node game/test/combat/build_secondary_oracle.mjs /path/to/original-modules.json`.
Initial reference tests caught the sketch's incorrect non-chaining powered Morel call;
using live power for G's default now preserves the original reaction and chain behaviour.

Next: original special activation and remaining primary/melee state mutations, then the
fixed-step dispatcher/contact bridge and granted Player hook. World HP/Tam decisions stay
A-owned. Full verify/art/hosted/rendered/native/device coverage remains pending; keep DRAFT.

## Special activation snapshot phase

`AbilitySpecial.activate` ports original M on an independent canonical snapshot. Powered
lifetime and the event name come from each pinned kit. It preserves the original ordering:
set live power, append the activation effect and event, then refill Brine/Clack, cap Nix heat,
add Mirra's seal under the powered cap, replace Rook's pair, and add Mote's orbit effect.
Rook's two turrets capture current aim and have fresh serial IDs in left/right order; existing
designation remains. The orbit is a finite visual effect and creates no idle damage or shards.

This reducer does not check input eligibility, advance time, or spend cooldowns. The future
dispatcher must call it once at contact and reconcile the resource mirror without applying
`AbilityResources.release("special", ...)` a second time. It does not attach actors or map HP.

`special-oracle.json` contains177 whole-state comparisons against hash-verified, unmodified
original M: all fourteen kits, live/unpowered states and directions, refill versus Pendle
non-refill, Nix's strict cap vicinity, Mirra's seal cap/clamping, Rook replacement/designation,
event limits, repeated dispatch and unknown fields. Input snapshots remain unchanged.
Regenerate with `node game/test/combat/build_special_oracle.mjs /path/to/original-modules.json`.
Next: canonical primary/melee mutations, then fixed-step dispatcher/contact and Player hook.

## Primary release snapshot phase

`AbilityPrimary.release` ports original E's primary branch, composing the shared scalar
strike and launch helpers on an independent canonical snapshot. It increments the combo
first and preserves original resource, damage/passive, projectile and event order. Brine
clears tether and all previous harpoons before launching one replacement; powered Pendle
ignores ordinary ammo/reload. Velvet's primed counter uses its independent timer even after
power ends. Cairn's shockwave and Ashe's crescent follow the first melee/passive resolution.
Nix adds heat before the beam; Mote emits shards only with a powered primary release.

The dispatcher owns eligibility and exactly-once contact. This phase already consumes ammo,
sets reload, adds heat and launches shots: do not also replay `AbilityResources.release` or
`AbilityProjectiles.plan`. Cancelled preparation must never call it. It does not attach actors,
convert HP, advance clocks or resolve projectile flight/impact a second time.

`primary-oracle.json` contains312 complete snapshots against hash-verified, unmodified E:
all kits/forms/directions, lethal/immortal/heavy targets and passive follow-ups, ordinary and
powered resource states, old harpoons, counter expiry, heat caps, flask lifetime clamps,
event limits and unknown-field preservation. Source input stays unchanged. Regenerate with
`node game/test/combat/build_primary_oracle.mjs /path/to/original-modules.json`.
Next: compose the fixed-step player/action/movement and ordered simulation dispatcher,
then contact presentation and the granted Player hook. World HP mapping and the inherited
Tam edge remain A/canonical-owner decisions on the existing remote checkpoint.


## Canonical movement/vault subphase checkpoint

`AbilityMovement.tick` ports the contiguous movement/vault/Velvet-echo section of original v,
between action commitment and enemy/status phase L. It uses fixed1/60 canonical units and scalar
double arithmetic, preserving action-specific speeds, Tam's live-form multiplier, the strict
movement threshold, sequential body separation, double separation on landing, arena clamps,
vault height/airborne threshold, walk-distance suppression during a vault, and finite echo caps.
A tiny positive vault timer at or below epsilon still suppresses walk distance but does not
advance the vault, as in the reference. Input snapshots and unknown fields remain untouched.

The caller must perform timers/releases/commitment before this phase and status/projectile/field/
turret/effect phases after it. It does not advance time, cooldowns or previous-input state, and is
not attached to Player. The later actor bridge must use Player's collision/movement ownership;
these reference arena/body constraints are not Godot terrain or support-height validation.
Do not invoke both this canonical movement and Player movement independently in the same step.

`movement-oracle.json` contains1272 whole-state comparisons from the hash-verified original engine.
The builder wraps the exact contiguous movement source slice, closing its trailing if condition
with an empty body at the L boundary. This is explicit test-only phase instrumentation, not a
claim that the whole original v ran unchanged. All14 kits/forms/actions, strict movement and
vault epsilon boundaries, simultaneous landing/body separation, dead/coincident targets, clamps,
echo-cap replacement and90-step movement/echo sequences are covered. Reproduce:
`node game/test/combat/build_movement_oracle.mjs /path/to/original-modules.json`.

Next: remaining player timer/guard/commitment phase and ordered fixed-step dispatcher, then contact
presentation and the granted Player hook. World-health/#275 and Tam's inherited duplicate-defeat
remain A/canonical-owner decisions. #290 weapon forms/tree proposals remain future coordination,
not changes to canonical kits. Full verify/art/hosted/rendered/native/device checks remain pending;
this checkpoint is pure simulation work. Keep DRAFT.

## Canonical player timers, guard and action commitment

`AbilityPlayerPhase.tick` ports the contiguous prefix of original v, ending immediately
before movement. It advances time/tick, clamps aim and resolves facing, expires cooldowns
and the input queue, tracks rising edges with special priority, expires counter/designation/
tether identity, completes reloads, cools heat using the old action/form, and expires power.
It then handles guard interruption/regeneration, releases the current action, completes it,
and attempts the next commitment. Rook may commit during a released vault as in the source.
The queue is consumed even if resource eligibility rejects that commitment.

Activation and release use the existing canonical reducers, including their resource and
launch mutations exactly once. Form expiry precedes release, so an expiring powered attack
can release unpowered; a special release can activate a new form on that same tick. Guard
interrupts an unreleased action. Commitment duration/cooldown reads the audited kit JSON.
The source's strictly positive power check for duration is deliberately distinct from its
epsilon-based live-form/eligibility check. Release timing still uses the committed duration,
not the length of a presentation clip or the current form's new duration.

The input contract is the dispatcher's already-normalised input. The phase does not update
previous-input state, advance movement, enemies, fields, projectiles, turrets or effects,
settle a wave, or attach actors. Compose it once before `AbilityMovement`, without also
advancing AbilityClock/AbilityResources for the same canonical interval. Contact presentation
and the Player bridge remain unfinished; no Godot/world HP conversion is implied.

`player-phase-oracle.json` has2330 whole-state comparisons against the hash-verified original
v prefix and its unchanged called helpers. The builder exposes that exact contiguous prefix
at the movement boundary, plus original R/D for boundary setup; this is explicit test-only
instrumentation, not a claim of a full unmodified v run. Coverage includes all14 kits/forms,
release epsilon boundaries, power expiry before guard/release, reload/heat eligibility,
queue edges and priorities, Rook's vault interruption, identity expiry, aim fallback and
clamps, repeated inputs and unknown fields. Exact IEEE754 fixture values,1e-6 comparisons
and input-immutability checks follow the other snapshot suites. Reproduce with
`node game/test/combat/build_player_phase_oracle.mjs /path/to/original-modules.json`.

Next: ordered fixed-step dispatcher, contact presentation and the granted Player hook.
Health mapping/#275 and the inherited Tam edge remain A/canonical-owner decisions; no
progression proposals are adopted. Full verify/art/hosted/rendered/device checks remain
unfinished. Keep DRAFT.


## Ordered canonical arena dispatcher

`AbilitySimulation.step` composes the existing pure reducers once per canonical 1/60 step:
player timer/action/release, movement/vault, enemy statuses, synchronous projectiles, fields,
turrets, effect expiry, resource display, previous inputs and wave settlement. The 0.1-second
outer clamp, accumulator epsilon, inactive/invalid-time no-op and terminal-state clock/effect
path match original `stepCombat`. Death before/after projectiles skips the same later phases.
A turret shot remains age zero until the next projectile phase. Victory clears the original
combat arrays and airborne/form/guard state without changing unrelated data or rewards.

Only the original encounter/practice modes are supported. `live` returns unchanged: legacy
AI is deliberately not copied over C61's enemy ownership. This is pure arena simulation, not
a C61/world bridge or terrain/actor movement. Do not tick AbilityClock/AbilityRunner/resources
or replay launch planning alongside it; these releases already spend and launch once.

`simulation-oracle.json.gz` is a deterministic gzip-compressed, exact IEEE754 fixture with
5317 complete-state comparisons against the HASH-VERIFIED UNMODIFIED original `stepCombat`.
Unlike earlier isolated-phase oracles, it does not instrument or replace any original body.
It covers all14 kits/forms over180 repeated inputs each, clamps/accumulator, terminal clocks,
input coercion, defeat order and practice/encounter settlement boundaries. Only presentation
colour is omitted, consistently with previous suites. The comparator checks every key, array
position and numeric leaf at the existing absolute1e-6 tolerance, reporting the first failing
path once per case rather than allocating one assertion per leaf. Tests also cover nonfinite
inputs/time, immutable snapshots and unsupported live-mode no-op.

Regenerate with `node game/test/combat/build_simulation_oracle.mjs /path/to/original-modules.json`.
The committed compressed fixture avoids adding30MB of redundant test JSON. Contact presentation,
Player's granted action hook and real C61/world HP integration remain unfinished. Existing health
mapping/#275 and inherited Tam defeat decisions remain A-owned; no progression proposal adopted.
Full npm verify/art-repro/hosted/rendered/native/device validation remains pending. Keep DRAFT.

## Contact drawing sequence (presentation boundary only)

`AbilityContactTrack` selects exact `clips.<clip>.facings.<facing>.frames` (or an explicitly
requested `aims.<tag>.frames`) and takes an explicit approved canonical duration per drawing.
It never derives kit timing from art-template duration, interpolates a missing variant, or
retimes a manifest. The caller must supply the schedule agreed by A/J; current v2 template
clocks and canonical kit clocks differ. The helper does not imply that #282 is integrated.

Feed each active presentation delta once. Process the ordered `drawing` event before the
following `contact` event: a coarse step can cross windup, contact and recovery together,
so use the contact event's retained sample rather than `sample()`'s final recovery drawing.
The contact is a presentation boundary, not another canonical damage/resource/projectile
command. Canonical simulation already releases once. The forthcoming bridge must coordinate
that existing release with presentation; attaching this helper alone does not delay, replay
or render any canonical effect. No production actor is attached by this change.

At an exact boundary the new drawing owns the time. Drawing zero (including release zero)
enters on the first valid active advance, even at zero delta; repeated advances never replay
contacts. Inactive/negative/nonfinite deltas freeze, completion holds the last drawing, and
cancellation discards remaining contacts. Action-instance tokens must increase even after
cancellation. Invalid configuration preserves the old sequence without consuming the token.

Anchors are copied from the actual selected drawing in authored source texels relative to
the foot pivot, already screen-oriented: no W mirroring, factor3 conversion, pivot addition
or support-height adjustment. `anchor()` returns an explicit missing result rather than
guessing zero or a previous frame. A genuine [0,0] anchor remains valid. Bramble's reviewed
previous-frame arrow-tip policy, where applicable, belongs to the explicit bridge contract.

Eleven tests cover exact/coarse ordered contact, variable canonical schedules independent
of template clocks, aim/facing selection, invalid inputs, cancellation/token replay, inactive
time, release zero and independent snapshots. Player input/hook and real world/C61 HP mapping
remain unfinished; full npm/hosted/rendered/native/device checks are still pending. Keep DRAFT.

## Player action-driver boundary (optional, not a live combat attachment)

`Player.attach_action_driver(AbilityActionDriver)` is the narrow actor hook authorised by
Claude A in6402597915. No driver is attached by default. A concrete driver implements
`tick(controls, context, delta)`, `request(action, direction)`, `cancel(reason)`, `is_busy()`
and `character_changed(id)`. It owns action clocks, powered state, presentation and combat
commands. The protocol itself is not a canonical runner or a world-health adapter.

While attached, Player reads held attack/ranged/special, optional existing guard input and
the dodge edge, keeps facing and performs exactly one collision-aware movement, then calls
the driver once with its actual post-collision actor position/velocity. Existing mercy/hurt
timers stay with Player. Legacy roll/recharge/swing/action animation clocks are bypassed;
direct start_shot/start_swing/start_roll forward a request, and legacy swing hits/Arrow
release callbacks do nothing. The driver must not run canonical AbilityMovement as a second
movement pass for this body, or replay canonical releases through AbilityRunner/resources.

Disabled input, dialogue and defeat provide neutral controls with active=false and zero
movement. The driver must freeze combat time and clear held controls in that case; invalid
frame deltas never reach it. Reset, defeat and detach cancel explicitly. Attachment rejects
null, duplicate, defeated or already acting players. Character selection refuses zero HP,
legacy actions and a busy driver, while preserving HP/position on an idle switch. Detach
restores the legacy path, without reviving a defeated player. No guard key is invented.

Eight actor tests cover forwarding and legacy suppression, held and inactive inputs,
post-movement position/one move, cancellation, guarded switching, invalid time and detach.
This is the tested hook and protocol, not a production canonical driver: the concrete
contact/presentation consumer, movement modifiers for canonical actions, damage/health
mapping, powered/empty/exit presentation and C61/world attachment still need implementation
and the existing A/J decisions. Full verify/art-repro/hosted/rendered/device checks remain
pending; keep the PR draft. No scene or world automatically enables this hook.

## Concrete arena driver and collision-resolution seam

`AbilityArenaDriver.configure(snapshot, origin)` accepts a full caller-supplied canonical
encounter/practice snapshot and the actor-texel location of its canonical origin. It is not
a world-state factory or a C61 HP adapter. The approved canonical-to-actor factor is read
from units.json. No scene installs it. `snapshot()` returns an independent copy.

When attached, this driver's `plans_movement()` bypasses Player's ordinary walk pass. It
calls the existing canonical dispatcher once with a position resolver: first resolve any
action-release displacement (such as Iona's lunge), then resolve ordinary movement at each
fixed1/60 step. Player alone executes each ordered target, using explicit displacement
through move_and_collide and one wall-slide remainder. This avoids applying the outer
physics-frame duration to each fixed substep. Canonical movement is the plan, never a
second actor mover. Walk distance and later echo/field work use the actual resolved ground.
Without a resolver, original pure simulation behavior and its oracle remain unchanged.

Held inputs, canonical absolute aim and queued direct requests use that one dispatcher.
Requests survive an incomplete substep and clear after an actual tick; no extra clock,
resource handler, release reducer or Godot Arrow is run. Inactive time freezes clocks and
clears queued/held controls. Cancel/reset or a different character disables the driver
until an explicit configure; invalid time, missing mover and mismatched identity do not
advance. Direct universal dodge is rejected because the recovered engine has no such
input rule. Guard still needs the input owner's approved binding.

Snapshot damage/projectiles are isolated canonical arena state, not world HP or rendered
actors. Terrain-resolved positions do not establish world cover/line-of-sight for a
release that already ran in canonical action order. Contact-drawing dispatch, world damage
mapping, support/airborne drawing, powered/empty/exit art, dodge mapping and real C61/world
attachment remain unfinished and retain their existing owner decisions. Do not use this
as a default live-world driver before those contracts and rendered coverage are complete.

## Ordered contact consumer checkpoint

`AbilityArenaDriver.player_phase_observed(before, after, dt)` now emits every canonical
player phase, before movement/projectile/field phases. Snapshots are deep copies, so observers
cannot change simulation state. The optional fifth `AbilitySimulation.step` argument supplies
that observation seam without changing the original reducer ordering or running another clock.

`AbilityContactConsumer` can connect its `observe` method to this signal. Its provider receives
an independent state and action and must return explicit `manifest`, `clip`, `facing`, `durations`
and optional `aim`. Both total duration and the release drawing's onset must match the canonical
committed clock within numeric tolerance; mismatches fail closed rather than retiming art.
Draw callbacks precede contact callbacks, including coarse advances and a previous action ending
on the same tick as a new commitment. Anchors remain authored source texels; callbacks never apply
canonical damage, consume resources or spawn another projectile. Cancellation/guard/death/identity
changes discard stale contacts, and reentrant cancellation cannot resume the remaining event list.
The caller must cancel the consumer on actor detach/reset/driver replacement. Inactive drivers
emit no player phase, freezing presentation time. This does not add live scene attachment.

The tests use explicit synthetic approved-clock contracts, not a claim that A/J's production
schedules or CastSprite bindings have been integrated. Next: lifecycle/actor presentation binding,
support/airborne and powered/empty/exit forms, then owner-agreed C61/world HP/cover/input/dodge
integration. No CastSprite, art, enemy, world, save, package or progression change in this step.

## Managed presentation lifecycle

`AbilityArenaDriver.bind_presentation(provider, draw, contact)` now owns the optional consumer's
signal connection. Call it only after configuring the canonical snapshot. The provider still
supplies explicit approved per-drawing durations and exact authored variants; this API never
chooses a production clock or attaches a scene. Invalid callback replacements leave the old
binding intact. A valid replacement disconnects and cancels its predecessor, and cannot resume
an already committed action midway through its clock.

`clear_presentation()` is idempotent. Driver cancellation, character mismatch and successful
snapshot reconfiguration clear the old binding. Player's existing reset/detach/defeat paths
therefore clear pending contacts; leaving the scene tree now cancels the driver as well. A
reentered actor requires explicit reconfiguration/rebinding. Cancellation from inside a drawing
callback suppresses its contact and later phase notifications/movement callbacks in that tick.
Inactive time freezes the sequence. No separate simulation, damage or projectile dispatch is
introduced. Existing standalone consumer users retain their documented cancellation duty.

This checkpoint tests the lifecycle with synthetic explicit schedules and real Player nodes.
It does not bind CastSprite drawings, load A/J production schedules, handle support/airborne or
powered/empty/exit art, or attach live-world HP/cover/input/dodge rules. Those remain the next
integration work and owner decisions. No driver is enabled by default.

## Exact Player drawing callback

`Player.bind_ability_presentation(provider, contact)` explicitly connects the configured arena
runner to its loaded body. The provider must return that body's exact manifest and an explicit
canonical schedule. `AbilitySpritePresenter` selects the exact `<clip>_<facing>[_<aim>]` sheet and
index, stops AnimatedSprite playback, and aligns CastSprite's frame/anchor fields. It does not
call `play_clip` or `advance`: art template durations, automatic turns and aim easing must not
replace the runner's contact drawing. The current V2 `playing`, `shown_facing`, `aim_tag` and
`turn_path` fields are synchronised when present, without editing CastSprite. West is never
mirrored, source anchors stay unscaled, and missing variants, unequal frame counts, fractional
indices or forged anchor samples fail closed. No facing fallback or missing-anchor zero is used.

The contact callback runs only after that exact sample has been shown successfully, for the
same attached, living actor. A replaced/detached driver cannot draw on its replacement. This
callback is presentation only; legacy arrow/damage dispatch stays suppressed. Tests exercise
real Player/CastSprite nodes and the loaded base art, with explicit synthetic canonical clocks;
an aimed-sheet fixture checks exact variant selection. Current-main CastSprite compatibility
is source-reviewed, not a claim of combined-main or rendered play testing. Production A/J
schedules, locomotion/guard/support/airborne, powered/empty/exit forms and live-world integration
remain unfinished. No binding is installed by default.

### Optional body elevation (C60, support/airborne step)

The existing Player presentation binding also supplies a pose callback. Before each
fixed player-phase drawing/contact and after final movement/landing, the arena driver
passes an immutable snapshot. Player lifts only its sprite node from the captured ground
pivot: `ability_support_height` (explicit actor texels, default zero) plus canonical
`vaultHeight * canonical_to_actor`. It never derives height from a drawing, scales frame
anchors, moves collision shapes/ground position or moves a sibling ground shadow.
No terrain support provider or new shadow art is installed. Canonical vault mechanics
and their airborne damage rules are unchanged. Inactive drivers freeze the pose.

Reset, detach, driver cancellation/reconfiguration and scene exit restore the captured
body position. Rebinding first releases the old offset, so it cannot accumulate height.
Nonfinite support or nonnumeric/negative/nonfinite vault heights fail closed before
release/contact delivery. The optional pose callback receives an empty snapshot on
binding release; general consumers must return true after applying a valid snapshot.
Existing three-callback bindings remain supported. No scene attaches a driver by default.

The height suite covers real Player/body/collider nodes with explicit support and vault
fixtures, unchanged anchors/state, lifecycle cancellation, pause, landing and height-before-
contact ordering. It is headless field evidence, not rendered gameplay, A/J production
schedules, terrain support integration, powered/empty/exit animation or live-world combat.
Those and the existing HP/Tam/input/cover/dodge agreements remain outstanding.

### Explicit passive/form drawing clock (C60)

`AbilityPoseTrack` accepts an explicit state identity, clip, facing/aim and approved per-drawing
schedule. It presents looping idle/walk poses and finite guard/exit poses without requiring or
emitting a release/contact event. Finite clips hold their final drawing; the caller must select
the next state. It does not infer powered transitions, harpoon state, defeat routing or clocks.
A new state identity restarts at drawing zero. Facing/aim changes retain phase only with the
same clip, loop rule and duration schedule; implicit retiming is rejected. Pauses freeze,
cancellation invalidates the sample and monotonic tokens reject stale replays. Frame/anchor
copies remain in authored screen texels, including west. Invalid replacement preserves the
current valid state. The fixture suite also reads all fourteen published passive/form clip
sets and Brine's empty variants; fixture template clocks are not production timing approval.

The optional third argument of `Player.bind_ability_presentation(action_provider, contact,
passive_provider)` now binds this timeline through the existing action consumer. The passive
provider receives an isolated snapshot and an empty action string; it returns `key`, the loaded
body's exact `manifest`, `clip`, `facing`, explicit `durations` and optional `aim`. It owns state
selection, including whether a form/empty clip is appropriate. The consumer selects no production
state and guesses no timing. A new key displays drawing zero; the same key advances at fixed ticks,
and a facing/aim change keeps phase only if the clock is unchanged.

Active action drawings/contact callbacks take priority. A passive pose may resume once the action
finishes, after its ordered contact delivery; guard poses can advance without any contact event.
Inactive time, duplicate ticks, detach/reset/reconfigure/scene exit and reentrant provider cancellation
preserve the existing lifecycle guarantees. Invalid or foreign contracts show no new drawing and
cannot deliver a contact. Existing two-argument Player bindings and driver callback APIs remain valid.
The new suite covers real Player/body selection, action priority, simulation equality, guard/pause,
explicit state/facing changes, foreign-contract rejection/recovery and lifecycle cancellation.

Production A/J provider/state selection, powered-idle start/end and powered-defeat exit routing
remain unfinished. No default attachment, combat event, art/renderer or canonical rule change.

### Explicit form drawing plans (C60)

`AbilityFormPlan.build` supplies the next selection layer without attaching a provider or
changing simulation state. Its inputs name the character, requested pose, runner-supplied
powered/harpoon-out flags, loaded manifest and exact facing/aim. Brine alone selects the
authored `_empty` variants while the harpoon is out. Ammo, tether and template animation
state are never used to guess that flag. Missing variants reject the whole plan, including
an unavailable empty primary, rather than falling back to a drawing with the weapon present.

Powered walk/action/guard/reaction/traversal plans start and end with `powered_idle` drawing zero
(or Brine's empty equivalent). Powered idle selects its own looping form clip; special remains
the activation clip. Powered defeat selects `powered_exit` drawings 0 to 3, then the ordinary
defeat clip, retaining Brine's empty state. Segments preserve authored frame indices and source
anchors, with independent copies. Invalid character/pose/facing/aim or a short exit rejects
the entire sequence. The real-manifest suite covers all fourteen characters and four facings.

This is a drawing plan, not an executable schedule. It supplies no durations, contact or damage
events and does not stretch canonical action time to insert boundary poses. A/J must supply
approved per-drawing clocks and the runner must bind the plan through its lifecycle, including
the living-actor cancellation currently used by the contact consumer. That binding, actual
powered-defeat playback, production state/provider/importer and world integration are still
unfinished. No scene or default driver uses these plans. Headless source-frame equality is
not rendered acceptance.

### Optional finite form playback (C60)

`AbilityFormTrack` now binds a plan to an explicitly injected array of per-segment,
per-drawing durations. It validates every segment against the supplied manifest before
replacing a valid timeline, preserves original drawing indices and anchors, and holds
the final drawing. It never reads template durations or invents loops. A stable state key
allows a facing/aim change at the same phase, but rejects changed segments or clocks;
state/empty-variant transitions require a new key. Pause, invalid delta and cancellation
cannot advance or revive the timeline. Returned samples own their copied frame data.

The existing optional passive provider may return `key`, the loaded body's exact
`manifest`, `plan` and `segment_durations` instead of the single-clip contract. The
contact consumer displays these only during passive/guard observations. Active actions
keep their canonical contact track and cancel the passive form timeline. Player
reset/detach/scene exit/reconfiguration keep the existing cancellation boundary.
No new Player API, scene attachment or default driver is added.

Tests use synthetic injected clocks and real authored powered-walk/idle drawings;
they are not approval of a production schedule. Finite walk/guard plans finish on their
authored idle boundary rather than guessing a repeating gait. Continuous gait policy,
production A/J schedules/provider/importer, active-action boundaries and powered-defeat
playback through the existing living-actor cancellation gate remain unfinished. A pure
track can sequence the exit drawings, but this does not claim the Player plays them
after defeat. No combat/contact events, HP mapping, art or canonical rules change.
