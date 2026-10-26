# Art style

The target is a clean, modern top-down pixel style with clear outlines and confident shading: the "cosy RPG tileset" look of the references below. Detail comes from form and light, not from noise.

**House style (20 Oct, proposed):** [house-style.md](house-style.md) makes every region one game at Eastward's level of detail: one palette made by one rule (warm lamplight, dusk-violet shade), the outline in each material's own edge tone, light from the upper left, parts and clusters instead of noise, shadows as ramp steps, a recipe per material, and what each setting may change. Once Matt approves it, it wins where it and this file differ.

## Density 2 (Matt, 21 Oct 18:17)

"let's go with 2x. final decision." **All new art is drawn at density 2:** an adult is 50 art px tall, a soft-grid cell is 16 art px, and 600 art px span the screen (`ART_ACROSS_AT[2]` in `lib/pixel-scale.ts`). The world logic stays in world units: an adult is 25 world px and a cell 8, and every size in [size-guide.md](size-guide.md) is in world px, so multiply by 2 for art px. The engine is `lib/art-density.ts` (#183): the density is a render parameter, a picture's density is measured from its pixels (`npm run check:art-density`), and the reasons for exactly 2 (2 device px a texel on every phone now sold, an adult of 50 against Eastward's 54) are in its header and in #183's description, which summarise the density research. At 2x, k = 50 / 54 = 0.93, so Eastward's measurements in [eastward-edges.md](eastward-edges.md) apply almost one to one in art px.

**The style reference** is Matt's old 1x scene, recreated and perfected at 2x (Claude A is finishing it now). Its lessons are rules for all new art:

- **One design per object, at every density.** A tree, a rock or a house has one design; the 2x drawing is that design drawn finer, never a different object.
- **Foliage in Eastward-style leaf stamps:** crowns built from stamped leaf clusters, lit at the top left, with dark gaps between them, not a smooth sphere with speckle.
- **Grass is tufts on a calm base:** one main field tone with a few large soft patches, and clumped tufts on top (eastward-edges.md 5.5).
- **Rock is pixel art:** form shading (a lit crown, a body, a dark underside) and cluster texture, never vector facets.
- **Everything on the soft grid,** with masses that step in and out along cell lines (eastward-edges.md 1.6), never a smooth curve.
- **Shadows fall east and down,** in two ramp steps, sized in world units so they match at every density.

The rules below still hold. Where one names a pixel size drawn at 1x, its 2x equivalent is noted beside it.

## Density 3: foliage, water and the woodland (Matt, 25 Oct 19:16)

"Especially the trees look really strange." The 2x foliage algorithm (leaf stamps, crease pockets) does not scale: at density 3 it drew a mesh of thin dark contours round many small cells. From density 3 the kit paints foliage as Eastward does: a few large clumps per crown, each a dome lit from the upper left (lit top, mid-tone body, shaded lower right, dark under-shade where it tucks under the clump in front), tones meeting in leaf-shaped scallops whose lit tips point down, sparse leaf marks and glints, leaf tips breaking the silhouette only, and an outline on the silhouette only. Bushes sit on the ground with no stems. Trunks have bark (plates, smooth beech, birch dashes), flare into roots, and reach up under the crown so it always covers them. Water at density 3 has curved banks on the soft grid (no stair steps), a wet edge, a bank lip with stones and grass hanging over it, depth from the bank to the middle and one-texel ripple lines; a fall has a lip, volume, streaks, foam, spray and rings. Size and colour choices per kind are data (the biome recipe's `crown` and `bark`). From 26 Oct (Matt: "the lamp and bench are exactly the style i'm going for" and paths should "adhere to the soft grid more"): every organic edge at density 3 (paths, worn earth, puddles, lots, rings, craters, the talus) runs smooth on the soft grid with no one-texel teeth, the surface dark under the turf's north lip and the turf lit south of it, and calm inside (a few large patches, clods in drifts); structures and props stand on the 8 world px cell (`scripts/art/native/softedge.py`, `scripts/art/grid_snap.py`, review-agents.md).

## References

Matt shared these as the bar ("it should be at least like this"). The images are third-party art, so they are described here rather than copied into the repo.

- **Stone circle in a forest clearing.** About 218 native px across, close to our 192-wide garden, so this level of detail fits our scale. It has:
  - muted grass (around `#86A755`) and a reddish dirt ring (around `#AE7E64`);
  - grey-purple standing stones with moss caps and drips;
  - pines with lit left flanks and cool purple shade at their bases;
  - the forest edge dissolving into near-black (`#2F2D2D`) through checker dithering.
- **Village tiles.** It has:
  - near-black outlines on everything;
  - round bushes built from leaf clumps, each with a light cap and a dark scalloped lower edge;
  - a gabled house with lit and shaded roof planes, a ridge beam, timber framing and a stone foundation;
  - turf with a dark lip where it drops onto the path;
  - hard shadows under every object.
- **Games Matt named:**
  - [Eastward](https://store.steampowered.com/app/977880/Eastward/): lighting and interiors.
  - [Moonlighter](https://store.steampowered.com/app/606150/Moonlighter/): shops and props.
  - [Owlboy](https://store.steampowered.com/app/115800/Owlboy/): foliage and colour.
  - Soulbound.
  - [Chef RPG](https://store.steampowered.com/app/1796790/Chef_RPG/) by World 2 Studio (Matt, 19 Oct 00:59: "in terms of art style i really like Chef RPG as well"). Take three things from it: a port town and its interiors built with real height (walls with thickness, wainscot and shelving), dense small story props (crockery, produce, signage) in one consistent three-quarter view, and warm light. Look at its store page and official trailers before drawing interiors (H1), towns (N1) and the harbour.
- **Asset sources Matt linked for inspiration:**
  - [CraftPix](https://craftpix.net/), its top-down tilesets (grassland, forest, farm, swamp, tavern).
  - The [Top-Down Farm with Animals](https://www.behance.net/gallery/227432629/Top-Down-Farm-with-Animals-Pixel-Art-Asset-Pack) pack on Behance.
  - Adobe Stock top-down nature and snowy village tilesets.

  Use them to understand style; do not copy or ship their art.

- **Technique guides:**
  - Raymond Schlitter's [Pixelblog 20: Top Down Tiles](https://slynyrd.com/blog/2019/8/27/pixelblog-20-top-down-tiles) and [Pixelblog 21: Top Down Objects](https://www.slynyrd.com/blog/2019/9/18/pixelblog-21-top-down-objects): few colours per texture, staggered leaf clusters, subtle hard shadows, one consistent projection.
  - Lospec's [outlines article](https://lospec.com/articles/pixel-art-outlines-part-2-using-color).

## Detail target (Matt, 18 Oct 16:33)

Matt pointed at Cainos' _Pixel Art Top Down - Village_ (Unity Asset Store and itch.io) as "the exact sort of art style i want, in terms of detail". It is a reference, not a source: our art stays generated, on our palette and light. What its detail means for the generators, at the same 32 px scale:

- **Stone in courses:** every wall, tower and cliff face laid as blocks of slightly different tone with mortar lines, chipped corners and moss in the lower joints; cliffs are stacked blocks with dark crevices, not bands.
- **Roofs in shingles or slates:** rows that overlap, each row's lower edge lit, ridge caps, a darker eave shadow on the wall below.
- **Timber with grain:** planks with a lit edge, knots and nail heads; posts with a cap.
- **Foliage in clusters:** crowns built from many small leaf clumps, three or four greens plus a yellow-green rim on the lit side, gaps showing the dark interior; birches and autumn trees add pale trunks and golden leaves.
- **Ground that is never flat:** grass tufts, small flowers, pebbles and worn dirt patches where feet go; paths edged with grass breaking over them.
- **Soft outlines:** a dark, hue-shifted outline (not black) on props, broken where the light hits.
- **Pilot first:** one zone redrawn to this level and compared side by side with the reference before the rest follow.

**Eastward too (Matt, 18 Oct 16:55):** "i also really like eastwards art style … but stuff needs to fit mobile, so be careful". What we take from Eastward: warm, lived-in places crowded with small story props; light as a material (lamp and window pools, warm light against cool shade, colour in the shadows); soft, chunky shapes with dark hue-shifted outlines; weather and air (haze, drifting motes). What a phone sets as limits:

- **Readable at 1.3 to 2 screen pixels per art pixel** (at 1x; at density 2 an art pixel is 2 device px, about 0.67 CSS px on a 3x phone, so a cluster of two 1x pixels is 4 art px across). Detail comes in clusters of two or more pixels, never single-pixel noise that turns to grey; walkable ground stays calmer and lighter than what blocks the way; every interactive prop keeps a clear silhouette and a 44 px target.
- **Quiet where you walk.** Clutter gathers at the edges of a place, against walls and under trees; paths, doors and the space round the companion stay open (world-rules.md, "a mostly empty node").
- **Light baked in, few live layers.** Pools of light are drawn into the ground and props; at most a handful of live glows per screen, finite and still with reduced motion (AGENTS.md).
- **Memory.** A zone's ground is one image; more detail must not mean more layers or larger files per zone. (The images are saved at 4x for crisp native scaling; a 1x save with nearest-neighbour scaling on the web would cut decoded memory sixteenfold, and is worth a test.)

## Eastward's level of detail is required (Matt, 20 Oct 01:19 and 01:24)

"eastward level of detail is what you should be aiming for", then: "Eastward level of detail should not just ne a nice to have but it has to be reached". This is an acceptance bar, not a direction:

- **Nothing new is drawn below it.** Every prop, building, face, edge and patch of ground that is drawn or redrawn is compared side by side with official Eastward screenshots at the same character height before it is handed on. **Edges and the soft grid follow Eastward only** (Matt, 21 Oct 09:23: "can you use only eastward as the example on how to draw edges and the soft grid"): rims, lips, faces, feet, sides, corners, outlines, transitions between grounds, water's edge, stairs and cast shadows are drawn to the measured rules in [eastward-edges.md](eastward-edges.md), never to Sea of Stars, CrossCode or Chained Echoes. Their geometry and value structure only, not Eastward's muted colours (Matt, 21 Oct 09:31): each terrain keeps its own house ramp. The references are fetched with `scripts/refs/fetch_references.py` (research/world-references.md); they never go into the repository.
- **Measured, not felt.** The comparison counts, per 16 x 16 px patch at the same character height, the distinct tones, the distinct shapes (lumps, stones, tufts, planks, leaves) and the dressing pieces, in ours and in the reference. Ours must reach the reference's count for that kind of surface; the soft-grid toolkit (`scripts/art/terrace.py`) reports these numbers and a check will enforce them once the baselines are set.
- **Every PR that changes art says what it was compared with**, shows the side-by-side crop, and gives the counts. Claude A does not merge art that misses the bar; it goes back with the crops that fall short.
- **Phone limits still hold** (above): detail in clusters of two or more pixels, quiet ground where you walk, few live layers. Eastward manages its density on a 640 x 360 screen; at density 2 ours is 600 art px across, about the same width, so the bar is reachable.

## Eastward sets the detail, the setting sets the style (Matt, 20 Oct 10:15)

"the level of detail here is fairly good but don't let eastward guide all of the stylistic parts (you have to consider the setting eastward is set in vs mine)". Eastward is the bar for craft: how much detail per patch, clean clusters, light and shade, lived-in density. It is not the source of forms, materials or palette. Eastward is a post-apocalyptic, worn, earthbound world; ours runs from a cosy valley through a steampunk junction, a frontier desert town, a castle and a fire country, a neon city and a space station to the moon. Each place takes its forms from its own setting, from real-world and genre references:

- **The valley and the isles:** a cosy rural and coastal setting: dry stone, thatch and slate, hedgerows, clean, cared-for, bright.
- **Cogsworth:** Victorian industry: brick, cast iron, rivets, glass roofs, soot, steam.
- **Sunstone Reach:** a frontier town in the desert: sun-bleached timber, false fronts, adobe, corrugated iron, dust; Hearthold is a castle in dressed stone; the fire country is basalt, ash and glowing seams.
- **Neon Harbour:** a dense harbour city at night: concrete, glass, signage, cables, steam from vents, wet reflections.
- **Halcyon Station and Lumen (the moon):** engineered for vacuum: pressure shells and modules with panel seams, airlocks with frames, radiators, antennas, cable runs and footings; no brick or timber. The moon's ground is regolith (grey to brown-grey, no plants, no water), craters of every size with raised rims and lit and shadowed walls, ejecta and boulders, bootprints and rover tracks, hard-edged black shadows with no ambient fill, and a black sky past the horizon.

And in every place, the drawing itself must make sense (Matt's 10:15 review of the first detail passes): a lit window is a window lit from inside, never a coloured slab laid over a facade; a doorway exists only where something meets it; banners hang where they read whole, not behind a roof that cuts them; posts and beams run unbroken and windows sit between them; a structure reads at a glance as what it is.

## The rules

1. **Outlines.** Every object gets a 1 px outline (1 art px at every density: at 2x that is half a world px, as Eastward's one-pixel lines stay one pixel) in `outline` from `art/materials.json` (`#1E1917`, a warm near-black). Do not outline ground textures such as grass and dirt.
2. **Light.** Light always comes from the upper left. Each material uses four or five tones from its ramp:
   - the lit top-left face is the light tones;
   - the body is the mid tone;
   - the lower-right and the underside are the dark tones;
   - a highlight sits only on the most lit edges.
3. **Hue-shifted ramps.** Shadows lean cool (blue or purple), highlights lean warm (yellow). The shared ramps in `art/materials.json` already do this. Keep the palette muted and earthy; avoid pastel or neon.
4. **Foliage.** Use `style.leafy()`:
   - a sphere-shaded mass in four clean bands;
   - spaced leaf clumps, each one tone lighter than the band under it, with a light cap and a dark U-shaped lower rim;
   - a silhouette that is a run of bumps.

   The deep-shade band stays quiet. Never fill foliage with random speckle. At 2x, crowns are built from Eastward-style leaf stamps (Density 2, above).

5. **Stone.** Use `style.facet_stone()`:
   - a lit top plane, a mid front and a dark right flank;
   - a bright rim along the top edge and a dark base;
   - a crack or two, and optionally moss caps with drips.

   At 2x, rock is form shading and cluster texture, never vector facets (Density 2, above; eastward-edges.md 2.3).

6. **Buildings.** Show the 3/4 top-down roof as two planes:
   - the left plane is lit, the right plane shaded;
   - shingle rows with dark under-lines;
   - timber ridge and fascia, plaster or timber walls with corner posts, a dark band under the eaves and a stone foundation.

   See `nap_hut()`.

7. **Ground.**
   - Grass is two close tones in broad, clean patches, plus tufts: dark roots, light tips (`style.tuft()`).
   - Paths sit lower than the turf. The turf edge above a path is a dark lip, with a shadow line on the dirt and occasional one-pixel scallops. The turf edge below a path catches the light.
   - Water has a dark band under its top bank and short, flowing highlights.
8. **Cast shadows.** Shadows are hard-edged and multiply the ground (`style.cast_shadow()`, `SHADOW_MUL`). They sit under each object, offset slightly right and down (east and down, two ramp steps, offsets in world units so 1 world px is 2 art px at 2x). They live in the ground image so they work on grass, dirt and sand alike.
9. **Forest shade.** Where the canopy closes in, the ground goes to `FOREST_DARK` through checker dithering (`style.dither_dark()`).
10. **Clean over busy.** If a texture makes an area noisy, remove it. Leave negative space in the clearing where the companion walks.
11. **The companion stays readable.** Tall things may stand in front of the companion (it walks behind roofs, trees and the forge), but when one hides at least 40% of its body, a faint copy (42% opacity) shows through, under the night tint (`lib/occlusion.ts`; `Ghost` in `components/atlas-walk.tsx`, and the same in `components/garden-world.tsx`, never while napping). It fades in and never takes taps. A low fence across the feet does not count.

## Where the code lives

| File                                            | What it draws                                                                                                       |
| ----------------------------------------------- | ------------------------------------------------------------------------------------------------------------------- |
| `scripts/art/style.py`                          | The rules above as functions: `leafy`, `trunk`, `facet_stone`, `cast_shadow`, `dither_dark`, `tuft`                 |
| `scripts/art/garden.py`                         | The garden map, its objects and ground (192×384 native, plus a 32 px forest band above y = 0; 384×768 and 64 at 2x) |
| `scripts/art/garden_meadow.py`                  | The stream, bridge, meadow beds, orchard and growth-stage sprites                                                   |
| `scripts/art/pets.py`, `battle.py`, `worlds.py` | Companions, battle backdrops and mission worlds. **These still use the older style and need the same pass.**        |

## Review checklist

- [ ] Squint: does the object read as a 3D form, with a clear lit side and shaded side?
- [ ] Is there a hard cast shadow, and does the object sit on the ground?
- [ ] Is the outline continuous, and is it the shared outline colour?
- [ ] Are there four or five tones, all from one ramp, with no stray colours?
- [ ] Is the texture there to explain the surface (leaves, planks, stone), not random noise?
- [ ] Put it next to the hut, a tree and the companion: does the light agree?
- [ ] Check it in the app at 402×874 at noon and at night (the night tint changes everything).
