# Folk, batch 1: the first six designs

Claude J, 21 Oct. **Status: proposal for Matt.** The review sheet is [review-batch-1.png](review-batch-1.png): the six chosen designs, each in every view the rig must serve, and the batch side by side at game scale.

These are design sheets, not production frames. The frames will come from the shared rig (rig parts plus a few hand painters per character) once Claude A's first-screen PR lands. The sheets fix:

- the silhouette
- the rig's parts list
- the palette on the house ramps
- personality in the pose
- where the familiar perches

## How it was decided

1. **Three options per character.** A designer drew three options (A, B, C), each a different answer to that character's main design question. The script for each character is `scripts/art/characters/designs/<id>.py`, built on `sheetkit.py`. Its outputs are `designs/<id>-options.png` and `designs/<id>.json`.
2. **Three independent graders** scored all 18 options, blind to the designers' picks, each on three criteria out of 10:
   - **player:** reads on a phone; appeal; fits the story.
   - **craft:** house style; Eastward-level detail at this height; drawing quality.
   - **production:** rig-ability; fits the cell and the familiar; cost.
3. **Revision.** The highest total won, with the best grafts from the losing options and the fixes the graders shared. It was then redrawn with:
   - the nap
   - eight fight key poses with a stand-in Mossling on the perch
   - perch anchors

   The results are `designs/<id>-final.png` and the `final` block in `designs/<id>.json`.

| Folk    | A                                     | B                                       | C                                       | Chosen                                                         |
| ------- | ------------------------------------- | --------------------------------------- | --------------------------------------- | -------------------------------------------------------------- |
| Bramble | 60 (19/17/24) capelet ranger          | 60 (24/20/16) hooded traveller          | 54 (21/18/15) fox scout                 | **A**, with B's fuller capelet and C's taller brush            |
| Puffcap | 54 (19/16/19) the cap is the nightcap | 58 (18/20/20) button head in a sock cap | 60 (25/18/17) mat cap                   | **C**, with B's bigger face and arm nubs                       |
| Velvet  | 59 (20/17/22) hooded wing-cloak       | 57 (26/19/12) eye-spot capelet, crook   | 62 (22/18/22) ruff and swallowtail coat | **C**, with A's closed-wing nap and B's eye-spots on the tails |
| Tally   | 53 (20/17/16) crook-staff drover      | 68 (23/21/24) collar-bell puffball      | 58 (23/16/19) big-cardigan clerk        | **B**, with C's stick behind the ear and a longer cardigan     |
| Tam     | 53 (26/17/10) bothy pack              | 58 (19/21/18) kettle cap                | 60 (19/17/24) scarf and kettle at hip   | **C**, as "Bothy Keeper", with A's low mat roll and kettle     |
| Puddle  | 58 (23/18/17) sou'wester, long coat   | 65 (23/19/23) short smock, net          | 55 (20/17/18) waders, bucket            | **B**, with A's pushed-back sou'wester and C's braces          |

Totals are out of 90; the brackets give player, craft and production. Bramble was a tie. A won because it keeps the limbs free for the walk and fight rig, and because hoods belong to Nix.

## Cast-wide rules this batch set

- **One signature accent per folk:**
  - Bramble: sky
  - Puffcap: light dusk
  - Velvet: deep dusk with a snow ruff
  - Tally: berry knit
  - Tam: leaf-green knit
  - Puddle: brass oilskin with berry wellies
- **Shapes owned by one folk each:**
  - Only one staff with something hanging from it (none in this batch: Velvet's lamp hangs at her hip).
  - No hoods: Nix owns the hood.
  - No floppy nightcap with a pompom: Mote owns it.
- **Drawing rules:**
  - Profiles are drawn as forms: a brow, a cheek and a snout step, lit from the upper left.
  - W is drawn, not mirrored. Every prop keeps one anchor and one layer, so it stays on the same side of the body in every facing.
  - Fur and knit are directional clusters (tufts that follow the form; rib columns), never mottled dots or checker.

## The numbers (style_lint, every final view)

All 13 views of each folk are 100% on the house palette, with light from the upper left (W minus E positive) and at most 4% lone pixels.

| Folk    | W minus E    | Lone pixels | Colours  | Outline dark |
| ------- | ------------ | ----------- | -------- | ------------ |
| Bramble | +2.4 to 13.9 | 0.5 to 2.3% | 26 to 38 | 100%         |
| Puffcap | +4.8 to 13.6 | 0.3 to 2.2% | 29 to 49 | 96 to 100%   |
| Velvet  | +1.3 to 13.5 | 0.5 to 2.3% | 35 to 46 | 100%         |
| Tally   | +2.4 to 13.0 | 1.1 to 3.8% | 32 to 42 | 100%         |
| Tam     | +3.8 to 12.7 | 0.7 to 2.4% | 33 to 48 | 98 to 100%   |
| Puddle  | +2.0 to 9.1  | 0.4 to 2.1% | 28 to 37 | 100%         |

**Compared with Eastward:** each designer compared their character by eye with official Eastward screenshots (`scripts/refs/fetch_references.py`, kept out of the repo). They used people at the same character height: John, Sam, Masao, the fishmonger and the stall keepers in the market shots, and the townsfolk in eastward-05. What they matched:

- the head is a third to two fifths of the height
- 2 to 3 px eyes with a glint
- 4 to 5 tones per garment
- a hard shadow under a brim
- hair and fleece as lobes, each with a lit cap and a dark crescent

## Decisions for Matt

1. **The familiar's size on the shoulder.** At 24 art px, the Mossling is two thirds of Puddle's height and dominates small folk in fights (every designer raised this). Options:
   - (a) keep 24 px and accept it;
   - (b) a perched familiar drawn at about 16 art px, a separate shoulder sprite (fights.md already gives it its own six poses);
   - (c) the familiar stands beside the folk in fights instead of on the shoulder.

   Claude J recommends (b).

2. **Is this the right six?** Sign-off on the silhouettes before production from the rig. Anything that reads wrong at game scale goes back now, while it is cheap.
3. **Bramble: A or B.** This was the one tie. B's long hooded cape scored best with the player grader. A was chosen for animation, and because Nix owns the hood.

## Open, for Claude A

- Puffcap's familiar perches on the flat cap top. Her cell is therefore 28 x 36 world px (`folkSmallTall` in the animation spec), not 28 x 30.
- The stand-in Mossling is drawn in grass in some sheets: leaf failed W minus E on a round form. The real familiar comes from the rig.
- Not yet shown: the walk cycle, and the W versions of cast, hit, sit and cheer. They come from the rig.
