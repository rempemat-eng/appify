# 1x masters for the cast

Claude J, 21 Oct, evening. Matt's rule from the style study, made final with density 2 at 18:17: **the 1x design is the master, and every density draws the same design**: the same silhouette, colours and proportions, with more detail at 2x, from one shared palette.

## Which master each character follows

- **Bramble and the Mossling** keep the 1x art Matt already likes: `prototypes/realtime-combat/build/bramble_sheet.png` and `moss_sheet.png`.
  - Bramble's 2x comes from Claude A's rig instance on `claude-a/first-screen`, built to the pilot's notes: a visible near arm in a contrasting sleeve, a satchel low and behind, a cape to the knee, a straight tail and a longer stride. The Bramble design sheet in [folk-batch-1.md](folk-batch-1.md) is superseded wherever it differs, so the "Bramble A or B" question is closed.
  - The Mossling's 2x final has been redrawn to its master: a green mochi under a red-brown mushroom cap with a two-leaf sprout. The curled-leaf option survives only in the options sheet, as the record of that round.
- **The other fifteen** (twelve folk, Mote, the Roamling and the Pebbling) had no 1x art. Each now has a 1x master, drawn by hand from its chosen 2x design at half the resolution, never downscaled. Those 1x masters lead from now on.

## The agreement check

For every view, the 2x final's silhouette was halved (a texel is solid when two of its four pixels are). It was then compared with the 1x master, aligned at the foot. The intersection over union must be at least 0.80, and the house families must be the same (glows aside).

The sheets are in `masters/<id>-1x.png`, with each 1x view at 8x beside its 2x view at 4x, and both at game scale. The numbers are in `masters/<id>.json`. Each JSON also lists what was simplified at 1x, such as dial ticks, rivets, quilting and strap buckles.

| Character | Views | IoU          | Same families | Most lone pixels |
| --------- | ----- | ------------ | ------------- | ---------------- |
| Puffcap   | 3     | 0.94 to 0.95 | yes           | 1.3%             |
| Velvet    | 3     | 0.83 to 0.86 | yes           | 4.6%             |
| Tally     | 3     | 0.90 to 0.94 | yes           | 4.0%             |
| Tam       | 3     | 0.82 to 0.88 | yes           | 1.9%             |
| Puddle    | 3     | 0.82 to 0.83 | yes           | 3.9%             |
| Cairn     | 3     | 0.87 to 0.88 | yes           | 4.4%             |
| Pendle    | 3     | 0.90 to 0.92 | yes           | 1.8%             |
| Mirra     | 3     | 0.84 to 0.86 | yes           | 2.0%             |
| Ashe      | 3     | 0.91 to 0.94 | yes           | 1.0%             |
| Tuff      | 3     | 0.89 to 0.92 | yes           | 5.6%             |
| Nix       | 3     | 0.82 to 0.91 | yes           | 4.9%             |
| Bunk      | 3     | 0.83 to 0.93 | yes           | 5.6%             |
| Mote      | 3     | 0.93 to 0.95 | yes           | 2.2%             |
| Mossling  | 5     | 0.91 to 0.93 | yes           | 4.9%             |
| Roamling  | 5     | 0.83 to 0.84 | yes           | 2.0%             |
| Pebbling  | 5     | 0.84 to 0.97 | yes           | 1.7%             |

- **Views:** each folk has S, E and W idle; each familiar also has its E and W perch at 8 px.
- **Light:** every view is lit from the upper left. The 8 px perches are too small for the light measure, which returns 0 there; the light is drawn from the upper left all the same.
- **Determinism:** every script gives byte-identical output.
- **Comparison:** each master was compared by eye with Matt's 1x Bramble and Mossling.

## What follows

- **Production at 2x** uses the shared rig once Claude A cuts the kit (`scripts/art/native/`). Each character is its body plan (`art/characters/bodies/<id>.json`) plus a face painter, checked against its 1x master with the same agreement check.
- **The familiar on the shoulder:** Matt still to decide. The sheets show the 16 px perch, a separate sprite.
