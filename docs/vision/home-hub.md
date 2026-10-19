# The home hub: one screen for the garden and the world

Matt, 19 Oct: "you need to fix the popping in and out of the main house hub. think of a better way to implement the main house hub."

The home garden is a place in the one world. You walk out of the gate into Crossroads Town and back in again on one screen, with one camera, one companion and one HUD. This file says what popped and why, the options, the design we chose and its phases.

## What popped, and why

Until phase 1 the home was two screens that took turns.

| Screen     | Route                                        | Renderer                                                         | Camera                                               | HUD                                                         |
| ---------- | -------------------------------------------- | ---------------------------------------------------------------- | ---------------------------------------------------- | ----------------------------------------------------------- |
| The garden | the Home tab, `app/(tabs)/index.tsx`         | `GardenWorld` (`components/garden-world.tsx`), the garden only   | its own, clamped to the garden's 320×576 map         | the floating HUD and the tab bar (`app/(tabs)/_layout.tsx`) |
| The world  | a stack route over the tabs, `app/world.tsx` | `AtlasWalk` (`components/atlas-walk.tsx`), a region zone by zone | its own, clamped to the region's land, `focusY` 0.55 | a header ("◀ GARDEN", region and zone, MAP) and place cards |

Both drew the garden: `GardenWorld` from its own pictures, and `AtlasWalk` as the valley's `garden` tile (`tileDrawables`, `t.id === 'garden'`), with still water at slightly different places and no beds, orchard, keepsakes or night pools.

The handoff:

1. **Out.** Walking to a garden exit (`gardenExitToward`, `atGardenExit` in `lib/garden-path.ts`) ends in `leave()` (garden-world.tsx), which sets `useUi.worldLink` and calls `router.push('/world')`. The world reads the link once, starts at the same spot in the valley's copy of the garden (`exitWalk`) and walks on through the gap.
2. **Back.** Every step in the world runs `homeward()` (app/world.tsx). When the companion is inside the garden's yard (`inGardenYard`), it sets `useUi.homeArrival` and calls `router.replace('/')`. The garden puts the companion there and fades up from black (`veil`).

What the player saw at each crossing:

- **The screen swapped.** The stack push or replace, then a 320 ms fade from black in each direction (`FadeIn` on the world's scene, `veil` on the garden).
- **The HUD swapped.** The tab bar and the floating HUD went, the world's header and a "HOME GARDEN / BACK TO THE GARDEN" card came (and the reverse).
- **The camera jumped.** The garden's camera keeps the companion at 0.55 of the part above the hotbar and clamps to the garden; the world's keeps it at 0.55 of the whole window (0.3 with a card) and clamps to the region. The same spot sat in a different place on screen.
- **The art changed.** Water moved by a few pixels, the beds, the orchard, the keepsakes and the lantern's pool appeared or vanished.
- **It ping-ponged at the edge.** The world only waited until the companion had left the yard once (`outside` ref) or walked 24 px from where it arrived. Walking along the yard's edge, or tapping just outside it, crossed back and forth and swapped screens each time.

The world screen has two smaller pops of its own, which the hub would inherit:

- The camera jumps when a place card opens or closes (`focusY` and `padBottom` change in one frame).
- Mounted zones follow the zone the companion stands in (`here`, which flips at a tile edge), and taps used a different camera clamp from the one drawn, so taps near the region's top edge landed off by up to 96 px.

## Options

**A. One walk screen.** The Home tab shows the valley through `AtlasWalk`. The garden's interactions (hotspots and their actions, the bed and the nap, reactions, ambient life, keepsakes and decorating, guide bubbles, journeys home) become a home layer that `AtlasWalk` mounts in the garden tile's coordinates. The tab bar and HUD never change; a place's name shows as a small label.

- For: nothing to hand off, so nothing can pop or ping-pong. One renderer, one camera, one companion, one copy of the garden's art. It is where the world atlas already points ("seamless travel"), and the other tabs can become places later.
- Against: the largest change. Two kinds of scene state meet (the garden's journeys and actions, the world's zones and cards). Memory: the Home tab now mounts the zones round the companion, not one garden picture, so mounting must be tight.

**B. The garden screen embeds `AtlasWalk`.** As A, but entered from the garden's side: `GardenWorld` keeps its journeys, actions and props, and uses `AtlasWalk` as its stage instead of its own camera and ground.

- For: every garden rule stays in the code that has its harness (`scripts/check-garden.cjs`), so no rule is rewritten. Smaller first step.
- Against: on its own it leaves the world's places (cards, stations) on the other screen.

**C. Keep two screens, make the handoff invisible.** No fade, matched camera framing, the same HUD on both, hysteresis at the edge.

- For: smallest change.
- Against: two renderers drawing the same garden must agree pixel for pixel, and two camera models must agree at every window size. The stack transition, remounting the scene and reloading its pictures remain. It hides the seam rather than removing it, and every later feature has to keep both screens in step.

## The design: one walk screen (A, built as B first)

- **One stage.** `AtlasWalk` owns the camera, the ground, the props, the companion's sprite and its outline through tall props, the night tint and the lamps, everywhere, the garden included.
- **The home layer.** The garden's interactions keep their logic in `GardenWorld`: its journeys (`walkTo`, `arrived`, `act`), its guards (interrupted walks never arrive, nothing runs while inactive or napping), its effects. In hub mode `GardenWorld` keeps the companion's position in garden pixels that simply run on past the garden's edges, walks on the valley's grid moved into those pixels, and hands the position to `AtlasWalk` (`follow`). Its art (water, flagstones, beds, orchard, keepsakes, visitors, light pools, ambient life, reactions, the guide's "!") mounts inside `AtlasWalk`'s camera at the garden tile's origin, each thing at its own depth among the props (`scene`); its hit areas and bubbles mount in a layer above the tap layer (`hits`).
- **No exits.** The gate, the trail and the meadow's sides are ordinary ground. A tap in the town walks there. Nothing navigates when the companion crosses the yard's edge.
- **The HUD stays put.** The floating HUD and the tab bar stay on screen everywhere in the valley. A zone's name shows for a moment as a small label under the HUD, with hysteresis so walking along an edge does not flicker it.
- **Places.** Outside the garden the valley's places work as they did on the world screen: small pins, and a card above the hotbar when the companion stands at the stall, the ring, a mission place, the halt or the jetty, or beside a resident. The card logic is shared (`lib/world-cards.ts`, `components/place-card.tsx`). The camera eases when a card opens or closes.
- **Doors and journeys are the only cuts.** Going into the hut and travelling to another region are real changes of place; they keep a short fade. A journey back to the valley lands in the hub at the station.
- **Rules unchanged.** No game rule, reward or cost changes. Decorative interactions stay free. Motion anticipates, acts and settles, is finite, respects reduced motion (walks are instant) and stops when the screen is inactive. Touch targets stay at least 44 px.

## Phases

**Phase 1 (this PR): no more popping.**

- `GardenWorld` has a hub mode (the Home tab: a camera window, not napping). The nap screen's small window keeps the old scene for now.
- `AtlasWalk` gains the follow mode, the `scene` and `hits` slots, companion details (emote, pose, grumpy, sleepy), an `active` switch, one camera function shared by drawing and taps, eased `focusY` and `padBottom`, instant walks with reduced motion, zone mounting by what the camera can see (with hysteresis), and a zone name with hysteresis.
- The world screen (`app/world.tsx`) remains for the hut's inside and the other regions. When it would open in the valley (a place link from the Shop or Missions tab, a saved spot), it hands over to the hub at that spot. Journeys from the halt or the jetty play on the world screen and land back in the hub.
- Checks: `lib/home-hub.test.ts` (the moved grid, the handoff routing, hysteresis, view mounting) and a hub block in `scripts/check-garden.cjs` (no navigation across the yard's edge, hotspot actions, the hut door, interrupted walks).

**Phase 2: one world screen.** The hut's inside and the other regions open in the same hub, so the world screen and its header go. The world map opens from the HUD or the ☰ menu. Callers (Shop, Missions, decorating) set the hub's arrival directly instead of going through `/world`.

**Phase 3: the garden scene retires.** The nap screen draws its window with `AtlasWalk` too, and the garden's art that `AtlasWalk` does not yet draw (beds, orchard, night pools) becomes ordinary scene data, so `GardenWorld` keeps only the home's interactions. The source harness follows the layer.

**Phase 4: places, not tabs.** The stall and the ring become places you walk into in the hub (coherence plan step 10), and the Missions tab's map shows the same valley.
