# Art style

The target is a clean, modern top-down pixel style with clear outlines and confident shading: the "cosy RPG tileset" look of the references below. Detail comes from form and light, not from noise.

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
- **Asset sources Matt linked for inspiration:**
  - [CraftPix](https://craftpix.net/), its top-down tilesets (grassland, forest, farm, swamp, tavern).
  - The [Top-Down Farm with Animals](https://www.behance.net/gallery/227432629/Top-Down-Farm-with-Animals-Pixel-Art-Asset-Pack) pack on Behance.
  - Adobe Stock top-down nature and snowy village tilesets.

  Use them to understand style; do not copy or ship their art.

- **Technique guides:**
  - Raymond Schlitter's [Pixelblog 20: Top Down Tiles](https://slynyrd.com/blog/2019/8/27/pixelblog-20-top-down-tiles) and [Pixelblog 21: Top Down Objects](https://www.slynyrd.com/blog/2019/9/18/pixelblog-21-top-down-objects): few colours per texture, staggered leaf clusters, subtle hard shadows, one consistent projection.
  - Lospec's [outlines article](https://lospec.com/articles/pixel-art-outlines-part-2-using-color).

## Detail target (Matt, 18 Oct 16:33)

Matt pointed at Cainos' *Pixel Art Top Down - Village* (Unity Asset Store and itch.io) as "the exact sort of art style i want, in terms of detail". It is a reference, not a source: our art stays generated, on our palette and light. What its detail means for the generators, at the same 32 px scale:

- **Stone in courses:** every wall, tower and cliff face laid as blocks of slightly different tone with mortar lines, chipped corners and moss in the lower joints; cliffs are stacked blocks with dark crevices, not bands.
- **Roofs in shingles or slates:** rows that overlap, each row's lower edge lit, ridge caps, a darker eave shadow on the wall below.
- **Timber with grain:** planks with a lit edge, knots and nail heads; posts with a cap.
- **Foliage in clusters:** crowns built from many small leaf clumps, three or four greens plus a yellow-green rim on the lit side, gaps showing the dark interior; birches and autumn trees add pale trunks and golden leaves.
- **Ground that is never flat:** grass tufts, small flowers, pebbles and worn dirt patches where feet go; paths edged with grass breaking over them.
- **Soft outlines:** a dark, hue-shifted outline (not black) on props, broken where the light hits.
- **Pilot first:** one zone redrawn to this level and compared side by side with the reference before the rest follow.

**Eastward too (Matt, 18 Oct 16:55):** "i also really like eastwards art style … but stuff needs to fit mobile, so be careful". What we take from Eastward: warm, lived-in places crowded with small story props; light as a material (lamp and window pools, warm light against cool shade, colour in the shadows); soft, chunky shapes with dark hue-shifted outlines; weather and air (haze, drifting motes). What a phone sets as limits:

- **Readable at 1.3 to 2 screen pixels per art pixel.** Detail comes in clusters of two or more pixels, never single-pixel noise that turns to grey; walkable ground stays calmer and lighter than what blocks the way; every interactive prop keeps a clear silhouette and a 44 px target.
- **Quiet where you walk.** Clutter gathers at the edges of a place, against walls and under trees; paths, doors and the space round the companion stay open (world-rules.md, "a mostly empty node").
- **Light baked in, few live layers.** Pools of light are drawn into the ground and props; at most a handful of live glows per screen, finite and still with reduced motion (AGENTS.md).
- **Memory.** A zone's ground is one image; more detail must not mean more layers or larger files per zone. (The images are saved at 4x for crisp native scaling; a 1x save with nearest-neighbour scaling on the web would cut decoded memory sixteenfold, and is worth a test.)

## The rules

1. **Outlines.** Every object gets a 1 px outline in `outline` from `art/materials.json` (`#1E1917`, a warm near-black). Do not outline ground textures such as grass and dirt.
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

   The deep-shade band stays quiet. Never fill foliage with random speckle.

5. **Stone.** Use `style.facet_stone()`:
   - a lit top plane, a mid front and a dark right flank;
   - a bright rim along the top edge and a dark base;
   - a crack or two, and optionally moss caps with drips.
6. **Buildings.** Show the 3/4 top-down roof as two planes:
   - the left plane is lit, the right plane shaded;
   - shingle rows with dark under-lines;
   - timber ridge and fascia, plaster or timber walls with corner posts, a dark band under the eaves and a stone foundation.

   See `nap_hut()`.

7. **Ground.**
   - Grass is two close tones in broad, clean patches, plus tufts: dark roots, light tips (`style.tuft()`).
   - Paths sit lower than the turf. The turf edge above a path is a dark lip, with a shadow line on the dirt and occasional one-pixel scallops. The turf edge below a path catches the light.
   - Water has a dark band under its top bank and short, flowing highlights.
8. **Cast shadows.** Shadows are hard-edged and multiply the ground (`style.cast_shadow()`, `SHADOW_MUL`). They sit under each object, offset slightly right and down. They live in the ground image so they work on grass, dirt and sand alike.
9. **Forest shade.** Where the canopy closes in, the ground goes to `FOREST_DARK` through checker dithering (`style.dither_dark()`).
10. **Clean over busy.** If a texture makes an area noisy, remove it. Leave negative space in the clearing where the companion walks.
11. **The companion stays readable.** Tall things may stand in front of the companion (it walks behind roofs, trees and the forge), but when one hides at least 40% of its body, a faint copy (42% opacity) shows through, under the night tint (`lib/occlusion.ts`, `Ghost` in `components/atlas-walk.tsx`). It fades in and never takes taps. A low fence across the feet does not count.

## Where the code lives

| File                                            | What it draws                                                                                                |
| ----------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| `scripts/art/style.py`                          | The rules above as functions: `leafy`, `trunk`, `facet_stone`, `cast_shadow`, `dither_dark`, `tuft`          |
| `scripts/art/garden.py`                         | The garden map, its objects and ground (192×384 native, plus a 32 px forest band above y = 0)                |
| `scripts/art/garden_meadow.py`                  | The stream, bridge, meadow beds, orchard and growth-stage sprites                                            |
| `scripts/art/pets.py`, `battle.py`, `worlds.py` | Companions, battle backdrops and mission worlds. **These still use the older style and need the same pass.** |

## Review checklist

- [ ] Squint: does the object read as a 3D form, with a clear lit side and shaded side?
- [ ] Is there a hard cast shadow, and does the object sit on the ground?
- [ ] Is the outline continuous, and is it the shared outline colour?
- [ ] Are there four or five tones, all from one ramp, with no stray colours?
- [ ] Is the texture there to explain the surface (leaves, planks, stone), not random noise?
- [ ] Put it next to the hut, a tree and the companion: does the light agree?
- [ ] Check it in the app at 402×874 at noon and at night (the night tint changes everything).
