# Batch 3: Bunk, Mote and the three Grasslings

Claude J, 21 Oct. **Status: proposal for Matt.** See the review sheet, [review-batch-3.png](review-batch-3.png).

This finishes the design pass. All fourteen folk and the three starter familiars now have a chosen design. The process was the same as in batches [1](folk-batch-1.md) and [2](folk-batch-2.md):

- three options per character;
- three blind graders: player, craft and production;
- a revision of the winner, with grafts from the other options.

The familiars were redrawn in every state the familiar spec has:

- idle in S, E and W
- the four-frame hop walk
- react
- nap
- the four perch states (perch, cling, cheer, special), each in E and W

The perch is a separate 16 art px sprite, redrawn rather than scaled down. That follows Claude A's ruling of 14:40.

| Character | A                             | B                                | C                               | Chosen                                                                                                                                      |
| --------- | ----------------------------- | -------------------------------- | ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| Bunk      | 62 (21/20/21) upright barrel  | 62 (24/17/21) squat capsule      | 60 (18/19/23) hooped barrel     | **A**, with C's Sleep Cycle dial, B's wrap-round nap and boot lights; one shaded cylinder                                                   |
| Mote      | 63 (26/18/19) plump star      | 52 (21/14/17) dust-ball          | 57 (19/17/21) star-sprite       | **A**, with C's dust wisp (the float walk) and B's comet cap; a real lamp-glow core                                                         |
| Mossling  | 67 (23/23/21) tuft-back mochi | 66 (24/20/22) teardrop, moss cap | 59 (22/20/17) moss-cloak pebble | **Reconciled to Matt's 1x master**: a green mochi under a red-brown mushroom cap with a sprout (A's curled leaf is the round's record only) |
| Roamling  | 62 (24/22/16) field mouse     | 58 (23/18/17) scruffy vole       | 65 (21/23/21) hedge hare        | **C as a jerboa**: round grass-lined ears (A), a three-blade crest (B), long feet, leaf tail                                                |
| Pebbling  | 66 (26/16/24) reading pebble  | 61 (19/19/23) lamp-stone stack   | 63 (22/20/21) bowl-cut block    | **A**, with B's nub arms and lamp facet (the special); modelled as a rounded stone cube                                                     |

Totals are out of 90; the brackets give player, craft and production. Bunk was a tie. A won because its silhouette is the only one of its kind in the cast, and its bedroll gives the familiar a natural perch shelf.

**Family marks shared by the three Grasslings:**

- one head-top growth anchor: a leaf, a crest or a sprout, carrying the family's green;
- 3 x 3 eyes with a 2 px glint;
- a pale belly or face;
- the same foot line.

The growth stages are rig variants of the same poses (a bigger growth, a second leaf), never new states. Each JSON records its growth anchor, eye positions and perch anchor.

## The numbers (style_lint, every final view)

| Character | Views | W minus E     | Lone pixels | Colours  | Outline dark |
| --------- | ----- | ------------- | ----------- | -------- | ------------ |
| Bunk      | 13    | +10.9 to 20.2 | 0.6 to 1.8% | 36 to 46 | 96 to 100%   |
| Mote      | 13    | +3.0 to 16.4  | 1.0 to 3.3% | 26 to 32 | 96 to 100%   |
| Mossling  | 17    | +3.0 to 21.1  | 0 to 3.9%   | 14 to 21 | 98 to 100%   |
| Roamling  | 17    | +2.3 to 16.8  | 0 to 3.6%   | 19 to 27 | 100%         |
| Pebbling  | 17    | +3.5 to 13.4  | 0 to 2.3%   | 19 to 28 | 98 to 100%   |

All views are 100% on the house palette. Every script gives byte-identical output for every hash seed. Each design was compared by eye with Eastward characters of the same height: Sam and the children in eastward-04 and 05, and the white caravans for Bunk's hull. The screenshots are not in the repo.

## Decisions for Matt

1. **The familiar on the shoulder.** These are the first true 16 px perch sprites. Batches 1 and 2 still show the 24 px stand-in in their fight poses; once Matt picks a size, the rig redraws those.
2. **Mote has no shoulder.** The familiar floats beside it at head height, on the side away from the foe.
3. **Sign-off** on the five designs. The Roamling becomes a jerboa: a hopping rodent, and so still the RAT species.

## For the rig

- Familiars walk with the spec's four-frame hop.
- Some poses stretch past the size targets: a hop's top and react reach 26 to 27 px against an idle of 24, and the perches are 16 to 17 px. This is squash and stretch on purpose, so the cells keep a margin for it.
- Mote's float walk is a 1 px bob with the wisp swaying. It has no stepping legs.

**Mossling, 21 Oct evening:** redrawn to Matt's 1x master (`moss_sheet.png`), because the 1x design is the master ([masters.md](masters.md)). Its final sheet and numbers now show the capped design: 100% on house, lone pixels at most 3.5%, W minus E at least +14.6.
