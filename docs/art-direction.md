# NapAttack art direction

NapAttack is a small, handmade world that welcomes its companion home after time away. Its visual identity combines soft organic shapes, useful little buildings, warm paper and timber, and deliberate pixel clusters. A player should recognise the same place in the garden, a mission, a card, a shop panel and a return screen.

This is the production guide for new artwork. The companion and the player's next action remain more prominent than decorative detail. More detail means more material, shape and story, rather than more noise or more things to collect.

## The common DNA

| Element   | Rule                                                                                                                                                  | A useful check                                                                                                             |
| --------- | ----------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| Pixels    | Draw at the asset's native resolution. Use whole-pixel clusters and nearest-neighbour export.                                                         | Inspect the native image as well as its enlarged version. A single rock must not look smoother than the surrounding grass. |
| Shape     | Friendly, rounded silhouettes built from stepped edges; timber, stone and foliage have different shapes.                                              | Read the silhouette before adding texture. A roof, tree and companion should remain distinct without their colours.        |
| Light     | Daylight comes from the upper left. Light upper and left faces; reserve deeper tones for undersides, joints and lower-right faces.                    | Put a new asset beside the hut, a tree and a companion. Its brightest face should agree with theirs.                       |
| Outline   | Use material-coloured shadows and restrained dark contours. Small characters and props need stronger separation than distant scenery.                 | Keep outlines readable without turning every internal leaf or plank into a black grid.                                     |
| Materials | Shade with a small ordered ramp. Wood has grain and joints; stone has broad facets; foliage has leaf clusters; water has banks and short reflections. | Texture should explain the surface, rather than fill every empty pixel.                                                    |
| Colour    | Moss, warm cream and timber are the base; lavender, amber, water blue and terracotta are accents.                                                     | A whole new biome may change the balance, but a random fluorescent prop needs a reason to exist.                           |
| Depth     | Separate far scenery, walking ground, feet-anchored props and foreground edges.                                                                       | The companion stands on the ground and can pass behind the correct objects in both flat and tilted views.                  |
| Interface | Paper and timber belong to the same handmade world. Keep dark ink, consistent borders and hard lower shadows.                                         | Compare a shop, mission, Journal and return panel side by side. Different jobs do not require different frame languages.   |

The pixel art is deliberately crisp. Text and controls still use normal responsive layout and readable type; do not rasterise body copy or shrink a control to its decorative icon's size.

## Shared materials and finishes

`art/materials.json` is the canonical contract for world material ramps, surface colours, interface geometry and native grids. TypeScript reads it through `lib/art-direction.ts` (`artMaterials`, `artSurface`, `artGeometry`, `artGrid`, `artOutline`); Python generators read it through `scripts/art/materials.py`. Reuse these values rather than copying hex colours into the next generator or miniature illustration. `scripts/art/garden.py` keeps its familiar ramp aliases for existing drawing code.

Ramps run from dark to light. Choose the appropriate material and use a few adjacent tones for each plane; do not apply the entire ramp as stripes. Character-specific ramps in `scripts/art/pets.py` can retain their identity while following the same lighting and cluster rules. A new biome-specific material is a deliberate extension to this vocabulary, not a reason to recolour every shared prop.

Interface geometry is equally shared: panels use a 12-pixel radius, controls 8, tags 6, opaque 2-pixel borders and a 3-pixel hard lower depth. These are screen-layout values, separate from native sprite pixels. `panelStyle`, `PaperFinish` and `PixelButton` provide the finish, including upper-edge light; consume the tokens when creating an appropriate new variant.

## Native scale and perspective

| Asset                       | Native format                                         | Source and renderer                                                     |
| --------------------------- | ----------------------------------------------------- | ----------------------------------------------------------------------- |
| Companion and visitor       | 32 × 32 pixel body; hats have their own anchored rows | `scripts/art/pets.py` → `lib/pet-sprites.ts`; `Pet` and `GuardianPet`   |
| Small world/UI prop         | 16 × 16 pixel motif                                   | `lib/scene-art.ts`; `PixelProp` in `components/pixel-scenes.tsx`        |
| Habit-card illustration     | 16 × 16 pixels; rendered at 48 × 48                   | `lib/card-art.ts`; `CardIllustration` in `components/habit-cards.tsx`   |
| Garden and mission ground   | 192 × 176 pixels, 4-pixel walk cells                  | `scripts/art/garden.py` and `scripts/art/worlds.py`; generated map data |
| Battle and horizon backdrop | 216 × 150 pixels                                      | `scripts/art/battle.py` and `scripts/art/worlds.py`                     |
| Supporting screen vignette  | 216 × 150 pixels; feet line at 111                    | `scripts/art/vignettes.py` → `lib/scene-assets.ts`                      |

World PNGs are exported at 6× and supporting vignettes at 4× with nearest-neighbour sampling. The native dimensions, not that larger file size, govern object positions, walk grids and apparent detail. Do not increase one object's resolution to make it richer. Improve its silhouette, clusters, shading and material instead.

`lib/garden-projection.ts` owns the flat and 2.5D projection. Props remain upright billboards anchored at their feet, while the ground plane tilts. Keep drawing coordinates and collision geometry in native world space; do not fix a visual misalignment with a one-off screen-space offset that only works at one width.

## Detail has a hierarchy

1. **Companion and action:** a clear face, readable pose, an obvious path and a legible primary button.
2. **Landmark:** one place-defining silhouette, such as the garden hut, park fountain, Book Club library or mountain cabin and ridge.
3. **Supporting scene:** a few related objects that explain who uses the place. Books belong near reading seats; tools belong near beds or planters.
4. **Surface detail:** grain, roof courses, stones, leaf clusters and water reflections. Group detail near edges and landmarks, leaving the walking clearing quieter.
5. **Small discoveries:** a resident, keepsake or finite response that is pleasant to notice and safe to miss.

Do not fill a quiet area merely because it looks empty in an enlarged screenshot. Check at the actual display size. When everything has equally strong texture, the world becomes harder to read and the companion loses focus.

## Reuse a material family, not an entire scene

Shared trees, lamps, benches, paper, roof shingles and tools make the places feel connected. They do not require the same placement, density or focal point.

| Place            | Existing identity                     | Reuse that supports it                                          | Variation that keeps it distinct                                                                 |
| ---------------- | ------------------------------------- | --------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ |
| Home garden      | A sheltered, personal clearing        | Trees, timber, lavender fabric, water and tiny domestic objects | Asymmetrical paths, a clear companion area, personal kept memories and a few useful destinations |
| Park Patrol      | A cared-for public green              | Trees, benches, lamps, flower beds                              | Fountain plaza, open paths and pond-side life                                                    |
| Book Club        | A small town gathering around stories | Timber, lamps, trees, planters                                  | Library silhouette, cobbled street, book cart and outdoor tables                                 |
| Mountain Retreat | An open alpine walk                   | Pine shapes, timber, stones and water                           | Snow ridge, winding trail, stream crossing, cabin and cairn                                      |
| Battle           | A clearing where companions meet      | Garden trees and grass materials                                | Clear fighter platforms, quieter central backdrop and space for action feedback                  |

For a new place, choose its landmark, route shape, material emphasis and small story before adding props. Two scenes using the same bench can feel different; two scenes with copied layouts and differently coloured benches usually will not.

Use stable seeds for procedural texture. Variation should feel authored and should regenerate identically. Do not introduce random asset selection at every render or time-based texture seeds that make reviews and save-state comparisons unreliable.

## A living world that lets the player leave

Movement should describe life: a glance, a settled breath, a leaf stirring, a resident looking around, a short walk followed by a pause. Vary the subject and timing rather than making every prop pulse together. A place may remain alive through composition and small story details even when all animation is off.

- A decorative response anticipates, acts and settles. Leave a stable final state; do not create an endless celebration.
- Pass the screen's activity gate to animated children. Stop timers, walking and callbacks when the screen loses focus, the app is inactive or an overlay takes control.
- Respect reduced motion. Keep the same meaning, silhouette and available actions in a static state. Quiet view must be able to remove scenery without changing the break.
- Keep walk routes clear, cancel interrupted arrivals and reject stale callbacks. Opening a sheet must not let an old walk start a nap behind it.
- Decorative interactions earn no currency, cost nothing and create no care obligation. New ambient life must not become a reason to keep checking the phone.
- A mission resident is scenery until a separate implemented meeting flow says otherwise. Art must not imply an earned visitor, tracked activity or reward that the game does not provide.

## Interface discipline

Reuse `lib/cozy.ts`, `components/cozy-ui.tsx`, `PixelButton`, `PixelText`, `BodyText` and `lib/layout.ts`. Build a variant of an existing control before adding another frame, font, border or shadow convention.

Use pixel display type for short titles and labels; use the existing readable body type for explanations. Wrap labels and action rows naturally. Keep primary, secondary, selected and disabled states recognisable across every screen, with meaning conveyed by text or shape as well as colour.

Small icons use the shared pixel vocabulary where the picture represents an in-world object. Accessibility labels and 44-screen-pixel touch targets remain independent of the native icon size. Decorative image layers must not intercept taps or add duplicate screen-reader announcements.

## Review an addition in context

- Review the asset at native size, its intended display size and enlarged size. Check silhouette, upper-left light, material ramp and edge sharpness.
- Put it beside an existing garden prop and a companion, then inspect the actual target screen. A technically valid sprite may still feel foreign.
- Inspect Home, Missions, Cards, Shop, Journal, Arena, departure and return together. An improvement is incomplete if a secondary panel still uses a visibly different finish.
- Check flat and tilted scenes, day and night where supported, overlapping props, a walking companion and static/reduced-motion presentation.
- Check long labels, large text and narrow layouts on a real supported viewport or device. Desktop geometry tests do not establish phone coverage.
- Run the authoring and verification steps in [Content authoring](content-authoring.md). Keep source generators, generated assets and generated maps together.

The reference games named for this direction suggest useful questions rather than assets to copy: is the landmark readable, does the material feel tactile, does movement have character, and can the player understand a place at a glance? NapAttack's own answer stays centred on its companions, personal clearing and time away.
