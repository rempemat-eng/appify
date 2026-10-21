# NapAttack prototype: in-world, turn-based fights (MOCK)

`index.html` is one self-contained file (716 KB, all art and fonts embedded, no network). Open it on a phone in portrait. It fills the screen, keeps the safe areas clear and draws the world at a whole number of device pixels per art pixel (5 on the walk, 10 in a fight on a 402 px phone at 3x), so the pixel grid stays crisp.

## Controls

- **Walk:** tap the ground. Bramble walks (runs on long trips) along the woodland path; Moss follows a step behind. A new tap replaces the old path.
- **A Glare** drifts in from the east along the stream, with a banner and an edge marker while it is off screen. It never chases. Walk on past it, or walk into it (or tap it, or its edge marker) to spar right there.
- **In a fight:** choose a card on the ring under your right thumb, then tap the big button (it never moves). With nothing chosen the big button is BE STILL. The left column says what the chosen card does, shows energy, and holds BE STILL (acts at once) and MOSS HUMS (choose, then the big button).
- **Ground:** marked spots near you (BRIDGE, SHADE, BANK; LEE in the ring) can be tapped and chosen like a card; stepping uses your turn.
- **Target:** when there is more than one foe, tap one to aim at it (a gold chevron marks it).
- **Timed tap:** during LOOSE and LONG SHOT a gold ring closes on the target. A tap anywhere as it meets the white ring is NICE (+25%). No tap or a wrong tap is a plain hit. TIMING in the fight header cycles TAP (160 ms), RELAXED (320 ms), OFF.
- **The arena:** follow the signpost south of the footbridge (or the ARENA tab) into the stone ring.
- **LEAVE** (top right, on your turn) ends a fight with nothing lost. **?** reopens the how-to; the gear holds TIMING, SCREEN SHAKE and MOTION.

## The rules in the prototype (today's card engine, kept simple)

Energy +1 a turn up to 3 (start 2); a hand of 4 drawn from a shuffled 9-card deck (LOOSE x3, LONG SHOT x2, TAKE COVER x2, STRETCH x2); one action a turn; guard halves the next hit once; 12-turn limit (a draw, "a good match"). Damage is power + 2 per level (level 2) + 0 to 3, as in `lib/battle.ts`.

- LOOSE 1: 9 + 4 per Aim. LONG SHOT 2: 12 + 5 per Aim, ignores guard and shields. TAKE COVER 1: guard, +1 Aim. STRETCH 0: 8.
- BE STILL: +1 energy, +1 Aim. **Steady:** ending a turn with energy left also banks Aim. At most one Aim a turn, cap 3; an arrow spends it all.
- MOSS HUMS (REST family's rested special): heal 8 per pip and guard, once a fight. The pips are fixed at 3 here; the real game fills them from time away.
- Terrain: FOOTBRIDGE arrows +3; TREE SHADE and STONE'S LEE its hits -3; STREAM BANK +4 HP each turn; a Glare over the water DAZZLEs +2 (its light doubles in the stream).
- **Glare** (48 brightness): DAZZLE 7, FLICKER (guard), GLOW UP +6 once. Its intent shows above its head. It dims to a paler blue below half; calmed, it turns gold, closes its eyes and folds into a spark that drifts home.
- **Static Storm** (arena, two phases). Phase 1, a knot of three glares (100): CRACKLE 6, then GATHER (a lane lights up across your spot), then STORM SWEEP 18 along that lane (step to a LEE spot out of the lane and it misses, or TAKE COVER to halve it), then STATIC SHIELD. At half it SPLITS (a shudder, a burst, the pieces swing out): a CORE (36) shielded by two SHARDS (14 each, ZAP 4 every turn). While a shard is bright the core takes half (LONG SHOT pierces). The core telegraphs OVERLOAD 20 with a countdown (OVERLOAD IN 3, 2, then it lands). Calming the core calms the rest: a victory pose, Bramble's happy cheer, Moss hopping, confetti, WALK ON.
- Losing: Bramble lies down for a breather, Moss curls up beside him, the Glare drifts off, he wakes, HP is full again. Nothing is lost. A spar pays nothing in the prototype.

## What to look for

- No screen change: the camera eases in through whole zoom steps (5 to 10) on the same world, the HUD and hotbar slide away, the ring rises; on the way out the reverse.
- Anticipate, act, settle on every action: the bow draw is held before the release, foes swell and rise before they lunge, numbers pop with a small overshoot then rise, hits freeze for 70 to 110 ms (hit pause), the screen shakes a little (off with the toggle or reduced motion).
- Whether choosing then confirming on the ring feels quick enough one-handed, and whether tapping spots and foes in the world reads as "I am in the place".
- Whether the timed tap feels like a bonus or a chore, on TAP and RELAXED.
- Fight length: a field Glare takes 4 to 6 turns, the Storm 8 to 10 (about a minute and a half).

## Tested

Playwright, Chromium (from /opt/pw-browsers), 402 x 874 at 3x with touch emulation, taps through `touchscreen.tap`: a full field fight (Take Cover, a step to the stream bank, Long Shots with timed taps, the calm), the walk on, the ARENA tab to the ring, the whole Storm (the sweep dodged by stepping to the lee, the split, both shards, Take Cover on the Overload, the victory and WALK ON); also walking past a lingering Glare (no fight), an interrupted walk (the second tap wins, no stale path), LEAVE, losing (lie down, wake, HP full), reduced motion (`?reduced=1`: camera cuts, still rings), TIMING OFF (no ring), the settings panel, and a 360 x 780 phone. No console errors. Every tappable area measured at least 44 x 44 CSS px. A selection of the screenshots is in `shots/`, reduced to 256 colours; `tools/play.py` writes the full set there again.

Not tested: a real phone, real touch latency, Safari or iOS, a notch's safe areas, performance on a low-end Android, sound (there is none), day and night.

## Placeholder or missing

- **The Glare and the Storm are procedural mock art** (`tools/lib/glare.py`), not drawn to the Eastward-level counts in `art-style.md` and not compared side by side with the references. Their motion (bob, swell, lunge, squint) is code, not frames.
- **Bramble has no guard pose and no sit pose.** TAKE COVER uses his cast frames with a code-drawn leaf shield; losing uses his lie and sleep frames ("lay down for a breather") instead of sitting.
- The Mossling uses its perch idle and attack frames for watching and humming; there are no cheer frames (it hops in code).
- Card illustrations: LOOSE and LONG SHOT are quick mock icons; TAKE COVER is the game's shield icon; STRETCH is today's card art.
- The signpost and the banner pole at the ring come from other zones and are placed by hand; they were not checked against the asset ledger. The water was blocked off in the walk grid by colour (the zone data lets you walk on the stream).
- Arrows, sparks, beams, the sweep, notes, confetti, the ground glow and the reflections are code-drawn pixels, not effect frames.
- Spots and foe placement are found by a small search around where you meet; there is no fight-pocket check in the zone data yet.
- No sound, no day and night, no AUTO, no BRACED press on incoming hits, no left-handed mirror, no Dream Dust pay.

## Bringing it into the real app

- **Keep the engine, extend it.** The prototype's rules are `lib/battle.ts` plus three things `fights.md` already plans: numeric stacks (Aim; E1), intents shown before the player's turn (F2), and press multipliers that never punish (F1: x1.25 or x1). Add `Fighter.stacks`, a foe deck that exposes its next move, `pierce` on cards, and a per-fight terrain modifier hook (`terrainAt(stand)` returning a small, approved effect). Multi-foe fights (the Storm's split) need `Combat` to hold a list of foes with a target; the 1-v-1 spar path stays as it is. Run the balance simulation on all of it before it ships.
- **World rendering.** The walk already draws zones from `lib/zone-maps.ts`; a fight is the same scene with the camera eased to a framing and integer zoom steps. In React Native that means the zone view gets a camera (scale and offset props driven by Reanimated), and fight overlays (plates, intents, numbers) are views positioned from world-to-screen math, as `toScreen` does here. Keep the canvas-free path: images with nearest-neighbour scaling on native (`Image` with `resizeMethod` and a pixel-art shader or pre-scaled sprites).
- **Native readiness.** Nothing here should go in as is: it uses `window`, `localStorage`, canvas and pointer events. Port the rules to pure TypeScript in `lib/`, the controls to touchable views (44 point targets, safe-area insets, `useWindowDimensions`), settings to the saved account, and record any web-only piece in `scripts/native-safe.json`. Timing windows should use the gesture handler's event timestamps, not wall time.
- **Data.** Encounter spots belong in the zone data (stands, where a foe may hover, which spots are which terrain), checked by the world audit like the ring arena footprint. The Glare's rules (always visible first, never chases, never during or right after a nap) belong in the spawn code with a regression test.
- **Art to draw.** The Glare's 23 frames and the Storm's knot, split and pieces; Bramble's guard (4) and a sit-down pose; the Grassling's watch, cheer and hum frames; arrow, spark, puff and sweep effect frames; four card illustrations.

## Files

- `index.html` the prototype; `src/index.src.html` its source; `tools/build_assets.py` builds `build/assets.json` (the embedded art, not kept in the repository; it draws with `tools/lib/`); `tools/assemble.py` puts them together, and without `build/assets.json` takes the art from the current `index.html`; `tools/play.py`, `tools/paths.py` and `tools/calm.py` are the Playwright runs; `shots/` the screenshots.
- Debug: `?seed=N` fixes the random rolls, `?reduced=1` forces reduced motion, `?howto=1` shows the how-to again.
