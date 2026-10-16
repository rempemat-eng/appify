# Adding art and places to NapAttack

Start with [Art direction](art-direction.md) for the shared visual rules and [World design](world-design.md) for what existing places and interactions actually do. Add content through the source generators and renderers below, rather than copying an entire screen into a new feature.

## Source and output map

| Change                                                | Edit                                                              | Generated or shared output                                   | Main consumer                                                    |
| ----------------------------------------------------- | ----------------------------------------------------------------- | ------------------------------------------------------------ | ---------------------------------------------------------------- |
| Material ramp, surface colour or shared art geometry  | `art/materials.json`                                              | `lib/art-direction.ts`, `scripts/art/materials.py`           | World generators, card art and shared UI                         |
| Garden ground, prop, placement or hotspot             | `scripts/art/garden.py`, `scripts/art/garden_decor.py`            | `assets/garden/`, `lib/garden-map.ts`                        | `components/garden-world.tsx`                                    |
| Mission ground, landmark, prop or route               | `scripts/art/worlds.py`                                           | `assets/worlds/`, `lib/world-maps.ts`, `lib/world-assets.ts` | `components/world-scene.tsx`                                     |
| Place description, postcard title or scenery resident | `lib/world-catalogue.ts`                                          | `worldCatalogue`, keyed by generated `WorldId`               | Missions, `WorldScene` and postcard art                          |
| Companion, visitor, pose or hat art                   | `scripts/art/pets.py`                                             | `lib/pet-sprites.ts`                                         | `Pet` in `components/game-ui.tsx`, `components/guardian-pet.tsx` |
| Battle backdrop or platform                           | `scripts/art/battle.py`                                           | `assets/battle/`                                             | `components/pixel-scenes.tsx`, `components/game-battle.tsx`      |
| Supporting screen vignette or its composition         | `scripts/art/vignettes.py`                                        | `assets/scenes/`, `lib/scene-assets.ts`                      | `PixelScene` in `components/pixel-scenes.tsx`                    |
| Small pixel prop or pictogram                         | `lib/scene-art.ts`                                                | `propPixels`                                                 | `PixelProp` in `components/pixel-scenes.tsx`                     |
| Habit-card illustration                               | `lib/card-art.ts`                                                 | `cardIllustrations`, typed by `CardId`                       | `CardIllustration` in `components/habit-cards.tsx`               |
| Paper, frame, button or text finish                   | `lib/cozy.ts`, `components/cozy-ui.tsx`, `components/game-ui.tsx` | Shared components and tokens                                 | Every screen                                                     |
| Content-column or dock geometry                       | `lib/layout.ts`                                                   | Shared layout helpers                                        | Screens and floating controls                                    |

`scripts/art/pixel.py` provides the Python `Canvas`, pixel primitives, upper-left shading helpers and deterministic noise. Keep reusable drawing operations here or in a clearly named art helper; they should not import game state or change rules.

For colours and native grids, import `artMaterials`/`artGrid` from `lib/art-direction.ts` in TypeScript, or the corresponding aliases from `scripts/art/materials.py` in Python. `lib/cozy.ts` applies the shared surface and geometry contract to UI. Keep a new colour local only when it is intentionally specific to that asset, rather than a second copy of wood, water or paper.

Generated TypeScript files identify their generator in the first line. Do not hand-edit those outputs. React Native needs literal image imports, so keep the generated asset tables as the route from source art to runtime images.

## Decide what kind of addition this is

- **A visual improvement:** change pixels, material, composition or presentation only. Preserve IDs, collision footprints, routes, hotspots and rewards unless there is a separately reviewed reason to change them.
- **A cosmetic interaction:** reuse the existing input, walking, feedback and activity boundaries. It has no currency, cost, progression or care duty.
- **New game content:** a new mission, card, companion or mechanic also needs rule, persistence and balance work. An illustration or scenery resident alone does not implement it.

Keep geometry separate from appearance. The look of a library belongs in its drawing function; where it stands belongs in the world object list; which cells are blocked belongs in the generated walk grid; what a mission awards belongs in game rules. One layer should not quietly alter another.

## Add or improve a garden prop

1. Choose an existing material ramp and native scale. Draw a `Canvas(w, h)` function beside similar props, reusing `garden_decor.py` for independent decorative drawings when appropriate.
2. Register the sprite in `main()` in `scripts/art/garden.py`. Add an `OBJECTS` entry only if the prop is placed in the world. Existing entries have the shape `(id, sprite_key, x, y, action_or_None)` in native coordinates.
3. Keep IDs stable and distinct from sprite keys. Several benches may share one image while retaining separate instance IDs. Anchor the sprite at its feet and inspect depth sorting by `y + h`.
4. For an existing action, use its existing hotspot and flow. A new cosmetic action also needs a deliberate handler and readable label in `components/garden-world.tsx`; adding an action string to generated data does not create behaviour.
5. Confirm its footprint leaves a reachable stopping point, a quiet companion clearing and a usable 44-screen-pixel target. A taller tree may change occlusion even if its footprint is unchanged.
6. Regenerate and review the PNGs and `lib/garden-map.ts` together. If this was only a texture or palette improvement, unexpected walk-grid or hotspot diffs need investigation.

## Add a mission prop or place

For a prop, add a drawing function and key to `SPRITES` in `scripts/art/worlds.py`. Existing trees intentionally reuse `scripts/art/garden.py`; do the same when the material and shape are shared. Put an instance in a world's object list as `(instance_id, sprite_key, x, y)`.

Each current world function returns the same five-part contract:

```python
return ground_canvas, objects, blocked_water_pixels, route_points, resident_point
```

The generator derives sprite dimensions, object footprints, shadows, the 4-pixel walk grid and runtime asset imports. A world therefore needs a coherent map, rather than a screenshot placed behind a walking pet.

To add a place:

1. Define a short identity: landmark, material emphasis, route shape, supporting story and what stays quiet. Reuse an existing lamp or tree; draw a new landmark when the place needs its own silhouette.
2. Add the world drawing function, register it in `WORLDS`, and add a matching horizon in `backdrop()`. Keep the 192 × 176 ground and 216 × 150 horizon contracts unless projection support is deliberately changed.
3. Regenerate the world data, then add its description, postcard title and scenery resident in `lib/world-catalogue.ts`. The generator derives `worldIds`, `WorldId` and `isWorldId` from `WORLDS`; `WorldScene` derives its walk-grid and resident records from those IDs. The typed catalogue requires an entry for every generated world. Missions and postcard art select a place by ID, so reordering a mission list does not change its artwork.
4. If it is a playable mission, separately add and review its mission definition in `lib/game.ts`, then audit every mission-ID whitelist and branch in rules, persistence, postcard/history copy and mission UI. Those rule boundaries are deliberately separate from the art catalogue. Follow the existing implementation rather than treating a world-art ID as permission to grant rewards.
5. Ensure every leg of the companion route, including the return to its start, is reachable. Keep the resident on reachable ground. The renderer uses the shared pathfinder and projection; do not bypass either with a screen-specific animation.
6. Extend the existing map regression tests for any new contract. Review its static Missions preview and active departure scene, in flat and tilted presentation where those views are exposed.

`worldCatalogue.previewLandmark` names an existing object whose projected silhouette frames the mission preview. `lib/world-framing.ts` centres and clamps that camera, and lets a short, wide preview grow enough to retain the landmark. Review both compact and regular heights when choosing it.

For a visual-only pass on an existing place, preserve its object IDs, dimensions, water mask, route and resident point. Material reuse and a new composition are separate choices; do not rearrange a tested route to accommodate an unnecessary decorative flourish.

## Add a supporting screen vignette

Supporting scenes use the same drawing functions as the explorable places. They are static compositions, not additional maps or game modes. `scripts/art/vignettes.py` separates `PROPS` (reusable drawing functions) from `SCENES` (composition, ground, path, pond, flowers and scene-specific details). A hut can recur without duplicating its drawing code or the entire arrangement around it.

1. Reuse a callable from `PROPS` or register a shared prop drawing function. Avoid enlarging a 16-pixel UI icon into a new building or tree.
2. Edit or add a `SCENES` entry with a deliberate arrangement. Props use `(sprite_key, x, y)` in native frame coordinates; the generator sorts them by their feet. Give the place its own landmark and edge framing rather than replacing only the colours of another entry.
3. Keep the middle clear for the live companion or screen content. The generated `sceneFrame` records a 216 × 150 canvas, feet at 111, ground depth 39 and a 160-pixel composition window. Preserve those anchors unless changing the shared renderer at the same time.
4. Extend the drawing helpers only for a detail that the composition needs. `details()` holds place-specific additions; `atmosphere()` and the sky variants provide the existing day, night and sunrise treatment. Keep light and material separation visible after a tint.
5. Generate the PNGs and `lib/scene-assets.ts`. The renderer kind is derived from the generated image registry, so a new composition does not need a second hand-maintained list. Review image selection if it needs a special atmosphere. Adding an art entry does not create navigation or a mission.
6. Inspect the result with actual children, at its intended display height. A good full image may still hide a landmark or put the companion behind an object when cropped. Miniatures should retain their focal silhouette and need no animation clock. A composition can set `focusY` for scenery-only banners; the generated `sceneFocus` metadata centres that native row in the crop. Character frames, explicit ground insets, sky-only scenes and sunrise/night alternatives keep their foot or sky anchors.

`sceneImages` contains the regular compositions; `sceneNight`, `sceneReturn` and `sceneSkies` expose their explicit alternatives, and `sceneSkyColors` supplies their backdrop fill. Treat these as presentation assets only: no collision grid, visitor unlock, reward, currency or saved progress belongs in a vignette entry.

`PixelScene` scales the bitmap by whole native pixels using `max(1, floor(measuredWidth / sceneFrame.window))`, centres it horizontally and aligns its bottom to `groundInset - sceneFrame.ground * pixel`. The default inset is the authored ground depth. WelcomeBack supplies its measured ground inset, so preserve that contract when changing scene geometry. Sky-only screens use the generated sky image rather than stretching a foreground composition. All vignette layers are passive and static; the live companion remains a separate child with its existing activity rules.

## Add a companion or variation

`scripts/art/pets.py` already supplies 32-pixel bodies, lighting, states and hat/eye anchors. Reuse those tools and keep the face clear at the smallest display size. Check open, closed, grumpy and grumpy-closed states where the species supports them; visitors use their existing open/closed contract.

Art is only one part of companion content. Identity and selection belong to `lib/companion-profiles.ts`, `lib/visitors.ts` and the existing game flows. Use `guardianPlayer` for effective rendering and `companionProfile` for descriptive attributes. Preserve the saved starter identity and shared level, currency, hats, cards and history. Only befriended visitors are selectable; a sprite entry must not unlock one.

Individual mechanical bonuses and real-world activity verification are separate future designs. Do not infer them from a family colour, animation or invitation text.

## Add or improve a card illustration

`lib/card-art.ts` owns the 16 × 16 illustrations separately from card rules. Its `illustration()` helper exposes bounded pixel and rectangle drawing operations, uses the shared material ramps and produces `CardArtPixel` records. Reuse its leaf and material vocabulary while choosing a distinct silhouette for the card's activity.

`cardIllustrations` is a `Record<CardId, readonly CardArtPixel[]>`. A new card ID therefore needs an illustration entry; it also needs an independently reviewed rule definition in `lib/cards.ts`, rule handling and reward/deck checks. Changing the picture of an existing card needs none of those mechanical changes. The shared `CardIllustration` renderer is used wherever that card appears, so inspect both collection and battle presentation rather than creating a second version for one screen.

## Add a panel or interaction

Use the existing paper/frame, button, title, body text and layout helpers. A new surface should inherit the same palette and geometry before its own content is added. Do not copy a whole screen's inline styles to get a matching card.

For motion, use the existing reduced-motion and app/screen activity hooks. Define the quiet state, active response, interruption behaviour and cleanup before adding timing. Cosmetic animation must remain separate from settlement, navigation and persistence. There is no reward for watching it finish.

An interactive object needs a label and a reachable path; decorative scenery needs neither a fake button nor a new collection counter. If a new response can open another destination, ensure an old arrival callback cannot fire after a sheet opens or the screen loses focus.

## Generate, inspect and verify

From the repository root, with the existing Node dependencies and Python Pillow available:

```sh
npm run art
git diff --stat
npm run verify
```

`npm run art` runs the checked-in art generators and formats their TypeScript outputs. It does not replace visual review. Run it a second time when a generator changes and confirm that the second run produces no further tracked changes; stable seeds and deterministic output are part of the authoring contract.

Use the existing checks for meaningful coverage:

| Check                                        | What it establishes                                                                                                               | What it does not establish                                        |
| -------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------- |
| `lib/art-direction.test.ts`                  | Canonical material/ramp contracts, bounded card pixels, world catalogue coverage, scene asset imports and exported PNG dimensions | Harmonious composition, sufficient detail or a pleasing animation |
| `lib/art-sprites.test.ts`                    | Sprite rows, dimensions, palette indices and anchors are well formed                                                              | Character, colour harmony or a readable face                      |
| `lib/world-framing.test.ts`                  | Landmark selection and preview camera bounds                                                                                      | A complete browser or phone visual review                         |
| `lib/world-maps.test.ts`                     | World routes and residents are reachable; instance IDs are unique                                                                 | Good composition or natural-looking movement                      |
| Garden, projection and Home lifecycle checks | Emitted geometry, callback guards and relevant source regressions                                                                 | Native scheduling, phone lock/resume or visual quality            |
| `npm run verify`                             | Required type, lint, rule, store, regression and web-export checks                                                                | A complete device play-test                                       |

Play-test the exact resulting build in a disposable profile. Check the target scene and its surrounding UI, normal/reduced motion, supported day/night states, overlays interrupting walks, overlapping objects, departure and return. Observe narrow layouts and large text in an actual supported viewport or device before claiming them tested.

Keep generator sources, generated PNGs, generated maps/import tables and any changed regression checks in the same review. Report the exact tested commit, preview, verification and remaining device gaps. The user merges; do not merge or enable auto-merge as part of authoring.
