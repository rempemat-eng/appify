# Character animation: the shared spec

Claude J, 21 Oct (stream 1, characters and animation). **Status: proposal.** The data is [`art/characters/animation-spec.json`](../../../art/characters/animation-spec.json), typed and checked by `lib/character-animation.ts` and `lib/character-animation.test.ts` (in `check:core`). Nothing in the app reads it yet, and no game rule depends on it. It covers every animated character: the 14 folk ([cast.md](../cast.md)), the three Grassling familiars, the nine visitors, the residents and the rivals.

## 1. What it fixes

- **States and frames.** A folk has a world set (four facings) and a fight set (east and west only, because fights are on the battle screen: [fights.md](../fights.md), decided 21 Oct).
- **Timings.** Every frame has a time in ms and a phase: anticipate, act, settle or hold.
- **Effects.** Each effect is finite and has a reduced-motion form.
- **The sheet format.** It has a density, a cell size, anchors and a memory budget.
- **The state machine.** It maps the game's own events to animations, and ignores stale ones.

## 2. The states

| Set   | State            | Facings | Frames (ms)                                                                 | Reduced motion                            |
| ----- | ---------------- | ------- | --------------------------------------------------------------------------- | ----------------------------------------- |
| world | idle             | S N E W | breath out 900, breath in 700, looped                                       | held on breath out                        |
| world | blink (overlay)  | S E W   | 140, every 3 to 5 s                                                         | none                                      |
| world | fidget           | S       | anticipate 220, act 260 + 300, settle 220, every 10 to 15 s                 | none                                      |
| world | walk_start       | S N E W | anticipate 80 (a lean, 1 rig px down)                                       | skipped                                   |
| world | walk             | S N E W | six frames, 100 each at 40 px/s, timed to the speed so the feet never slide | a standing still, facing the way          |
| world | walk_stop        | S N E W | settle 70 + 90, with a puff of dust                                         | skipped                                   |
| world | react (tap, pat) | S       | anticipate 110, act 90 + 160 (up 6 rig px, a heart), settle 180             | the happy frame held 400, the heart still |
| world | nap_down         | S       | yawn 180, sit 140, curl 160 (480 ms, inside the game's 500 ms delay)        | cut                                       |
| world | nap              | S       | breath 1400 + 1400, Zs while on screen                                      | held, one still Z                         |
| world | nap_up           | S       | stir 260, sit up 140, stretch 300                                           | cut                                       |
| fight | ready            | E W     | 520 + 480, looped                                                           | held                                      |
| fight | attack           | E W     | wind-up 100, strike 60, impact 200, recover 160; the impact frame at 160 ms | wind-up still, then the impact still 300  |
| fight | cast             | E W     | gather 140, release 260 (the card's effect), recover 160                    | two stills                                |
| fight | guard            | E W     | 80, braced 360, 120                                                         | the braced still 300                      |
| fight | hit              | E W     | knocked back 220 (a spark), recover 140                                     | the hit still 300, no flash, no knockback |
| fight | faint            | E W     | hit 180, then sits down for a breather, held                                | sitting                                   |
| fight | victory          | E W     | crouch 120, cheer 160 + 220 + 160, twice                                    | the cheer held 600                        |

A folk draws **75 frames** (51 world, 24 fight) and about 14 effect frames for its four cards. cast.md planned about 110; the saving comes from keeping fight poses off the world set. A familiar draws 41 (follow, hop, curl, react, and six perched poses a side). A visitor uses the familiar's spec. A resident draws 26 (idle, four-frame walk, talk). A rival draws 38: a resident plus the fight set facing west.

**West is drawn, never mirrored:** the light comes from the upper left in every facing, and a mirrored east would light the wrong side. The test fails if a state draws east without west.

## 3. Rules the test enforces

1. **Anticipate, act, settle.** A state the character starts itself (walk, react, nap, fidget, attack, cast, guard, victory, cheer, special) opens with an anticipate frame, acts, and ends settled or held. A blow it receives (hit, faint, cling) opens with act.
2. **The game leads.** Animation never delays, gates or changes a callback.
   - The sit-down ends before `act('nap')` calls `onNap` (500 ms).
   - The attack's impact frame shows 160 ms after the card, inside `game-battle.tsx`'s 200 ms impact step.
   - An event that arrives mid-animation cuts it.
3. **Effects are finite.** Each one plays once, or loops only while its state is on an active screen (the Zs). Each one is either left out or shown still under reduced motion. The hit flash steps the character's own ramp to tone 5 for 34 ms; it is never a white overlay.
4. **Reduced motion.** For every state, at every moment: no translation, and no loop showing more than one frame.
5. **Stale events are ignored.**
   - An arrival with no walk under way does nothing.
   - A nap or a reaction during a walk does nothing.
   - A tap does not wake a sleeper.
   - A walk started from a nap starts at once, so the feet never slide.
   - Nothing cheers after sitting down.
   - World events do nothing in a fight.
   - An inactive screen pauses the machine and stops all effects.
6. **Budgets.**
   - Frame counts match the plan.
   - Every sheet fits within 2048 px at 1x, 1.5x and 2x.
   - Every cell lands on whole pixels at 1.5x.
   - A world screen (your folk, your familiar and six residents) decodes to 3.25 MB at 2x, against a budget of 4.
   - A fight screen decodes to 1.30 MB, against a budget of 3.

## 4. Sheets, density and memory

- **Units.** Sizes are in world px; art px are world px times the density. The rig authors at 2x: an adult is about 50 art px, a cell 16. Offsets are in rig px (2x art px) and are rounded at other densities.
- **Cells (world px).**
  - folk: 32 x 36 (foot at 16, 33)
  - small folk (Puffcap, Puddle, Mote): 28 x 30
  - large folk (Cairn, Tuff): 40 x 40
  - familiar: 16 x 16 (a Grassling about 12 world px, 24 art px at 2x)
  - resident: 20 x 30
- **Sheets.** There is one PNG per character, set and density: a grid 8 cells wide, frames in the manifest's order, nearest-neighbour only, bundled with `import` (native-readiness). Each frame in the manifest carries:
  - its foot anchor
  - head (hat), eyes (blink, sleep) and hand (effect spawn) anchors
  - in the fight set, the perch anchor where the familiar sits
- **Shadows** are not baked into the sheets. The renderer throws each frame's silhouette down and to the right and steps the ground two tones down under it (house-style 6), plus the contact line. Open question for Claude A: should the sheet carry a 1-bit mask per frame, or should it be computed at load?
- **Only what is on screen is loaded:** your folk's world set and your familiar's current growth stage, while walking; both fight sets, while fighting.

## 5. Wiring, without changing a rule

The machine is pure (`onEvent`, `frameAt`, `settle`), so components only translate the state changes they already make into events. No game logic moves.

| Today                                                                         | Event                                                                                                       |
| ----------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- |
| `garden-world` / `atlas-walk` `walkTo` sets `walking` true, with a leg facing | `WALK_START` (facing)                                                                                       |
| `runOnJS(setFacing)` on a new leg                                             | `FACE`                                                                                                      |
| `arrived()` / `arrive()`                                                      | `ARRIVE`                                                                                                    |
| `stopJourney()`, a new tap, leaving the screen                                | `WALK_CANCEL`                                                                                               |
| `patGuardian()`, `respond()`                                                  | `REACT`                                                                                                     |
| the idle yawn or look timer                                                   | `IDLE_BEAT`                                                                                                 |
| `act('nap')`; waking                                                          | `NAP_START`; `NAP_END`                                                                                      |
| battle opens; `setAttack`; `setHit`; hp 0 or a loss; a win; close             | `FIGHT_ENTER`, `CARD_ATTACK` or `CARD_CAST` or `CARD_GUARD`, `TAKE_HIT`, `KNOCKED_OUT`, `WIN`, `FIGHT_EXIT` |
| `active` false, app in the background, unmount                                | `SCREEN_INACTIVE` / `SCREEN_ACTIVE`                                                                         |

Steps, each a small PR behind a flag that is off by default (`FOLK_SPRITES`):

1. **This PR:** the spec, the machine and the test.
2. **`CharacterSprite`**: draws one cell of a sheet at whole device pixels (`usePixelGrid` from #183), with a `useCharacterAnimation(kind, events, { reduced, active })` hook. It holds one clock, never `setInterval` per character, and stops when inactive. The web gets nearest-neighbour from `Platform.OS === 'web'` CSS; native depends on C34's spike (#152).
3. **The garden:** with the flag on, Bramble and the Mossling follow from the rig's output in `garden-world.tsx`, where `GuardianPet` stands today. Hit areas stay 44 px or more; the ghost behind occluders is kept.
4. **The atlas walk** (`atlas-walk.tsx`) and the residents (`atlas-life.tsx`) on the same component.
5. **The battle screen** (`game-battle.tsx`): your folk faces east with the familiar perched, and the rival faces west.
6. **The flag comes off** once Matt has seen it on a phone-size preview; the old 32 px `Pet` is kept for the spin-off (tagged, not deleted).

The save change (folk plus familiar) is Codex's (cast.md 2). Until it lands, the flag shows Bramble for every save, and nothing is written.

## 6. Open

- **Density:** 2x is pending Matt's verdict on the pilot. Everything here is in world px, so a 1.5x verdict changes only the sheets.
- **Shadow masks:** see section 4.
- **Rig parts and painters:** these come from Claude A's first-screen PR (`scripts/art/native/`). When it lands, its timing tables are merged into this spec, never forked from it.
