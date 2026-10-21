# The lawn measure

This is the measure every round of the perfected scene used (pilot2x `perfect/MEASURE.md`). It now lives in the kit as `measure.py`, and `npm run check:kit` runs it on the golden scene.

## The mask

The mask is `measure.lawn_mask`:

- the open lawn from the terrain codes (the grass families, so no path, herb bed, water, face or stair);
- minus every prop's `box` in the plan, grown by 2 world px;
- minus a box round each walker;
- eroded by one world px.

The dressing (flowers and tufts) is lawn texture and stays in.

## The measures

The measures are `measure.lawn`:

- **Edge share:** the share of right and down neighbour pairs inside the mask whose colours differ by more than 20 (Euclidean RGB distance).
- **Lone px:** pixels unlike all four neighbours, as a mean over 16 x 16 boxes that are at least 90 % lawn.

## The band

The band is data: `lawn.measure` in `scripts/art/biomes/meadow.json`.

On 21 Oct Matt asked for more grass, the amount the 1.5x level had, so Claude A moved the band at 2x from 0.17–0.21 to 0.20–0.24. Lone px stay under the house ceiling. The golden's own values are recorded in `art/golden/pilot/manifest.json`.

| Round | Edge share at 2x | Lone px at 2x |
| --- | --- | --- |
| r5 | 0.173 | 0.5 % |
| r6 (the golden) | 0.226 | 0.6 % |

Another biome is measured against its own swatch's band (rules-system.md 4), never pushed towards these numbers.
