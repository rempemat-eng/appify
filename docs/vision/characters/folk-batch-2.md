# Folk, batch 2: nights 7 to 12

Claude J, 21 Oct. **Status: proposal for Matt.** The review sheet is [review-batch-2.png](review-batch-2.png). The process is the same as [batch 1](folk-batch-1.md):

1. Three options per folk, each answering one design question.
2. Three blind graders (player, craft and production) score every option.
3. The winner is revised with grafts from the other options.
4. The winner is drawn in every view the rig serves, with the stand-in familiar on the perch.

Batch 1's cast-wide accent and owned-shape rules held throughout.

| Folk   | A                               | B                              | C                                 | Chosen                                                                             |
| ------ | ------------------------------- | ------------------------------ | --------------------------------- | ---------------------------------------------------------------------------------- |
| Cairn  | 59 (22/18/19) menhir            | 63 (20/21/22) cairn stack      | 66 (25/21/20) moss-mantled giant  | **C**, with A's chest ring and B's capstone brow                                   |
| Pendle | 62 (21/22/19) longcase          | 62 (21/18/23) station master   | 65 (24/19/22) engine barrel       | **B** (override), with C's copper shoulders and porthole, and A's verdigris        |
| Mirra  | 51 (24/16/11) sun-hat diviner   | 62 (22/20/20) cone-hat pilgrim | 49 (15/17/17) dune traveller      | **B**, skin moved to sand, with C's curled tail and A's rod (strike and cast only) |
| Ashe   | 57 (20/22/15) dented plate      | 63 (24/20/19) half-plate drake | 61 (21/20/20) hearth squire       | **B**, with C's big belt bell and A's dents; scales a deep ember red               |
| Tuff   | 64 (22/22/20) causeway block    | 54 (23/19/12) shell of columns | 56 (19/16/21) boulder on stumps   | **A**, with B's boulder head and C's faceted shoulder perch; a real turtle         |
| Nix    | 56 (21/16/19) round-screen hood | 68 (26/20/22) antenna hood     | 53 (16/20/17) long parka, TV head | **B**, with A's visor glyph for each state and a bigger slim box at the hip        |

Totals are out of 90; the brackets give player, craft and production.

**The one override: Pendle.** C had the highest total, but its barrel body reads as Bunk, the station robot, and its brass body sits on Puddle's brass accent. So B was chosen, the production grader's winner, which also has the biggest dial. On Pendle, brass is trim only. The coat is soot with verdigris copper.

**Clashes resolved:**

- **Mirra:** a green gecko read as Puddle and the familiar, so she is now sand.
- **Ashe:** her scales moved off Bramble's fox orange.
- **Brims:** neither wide brim (Ashe C, Mirra A) was chosen, so none crowds Puffcap's cap.
- **Cairn and Tuff** stay apart: Cairn is tall, grey, matte and mossy; Tuff is low, black, glossy, hexagonal and without moss.

## The numbers (style_lint, every final view)

All 13 views of each folk are 100% on the house palette, with the light from the upper left (W minus E positive) and at most 3.5% lone pixels. Every script gives byte-identical output for every hash seed.

| Folk   | W minus E    | Lone pixels | Colours  | Outline dark |
| ------ | ------------ | ----------- | -------- | ------------ |
| Cairn  | +3.9 to 13.9 | 0.5 to 1.5% | 25 to 39 | 98 to 100%   |
| Pendle | +0.8 to 11.6 | 1.1 to 3.5% | 32 to 45 | 99 to 100%   |
| Mirra  | +3.6 to 12.2 | 0.9 to 2.6% | 25 to 37 | 99 to 100%   |
| Ashe   | +1.7 to 15.1 | 1.3 to 3.0% | 39 to 53 | 97 to 100%   |
| Tuff   | +0.6 to 10.6 | 1.1 to 2.9% | 36 to 47 | 100%         |
| Nix    | +0.8 to 17.2 | 0.4 to 1.8% | 29 to 40 | 96 to 100%   |

Pendle, Tuff and Nix pass the light test only narrowly in a few views (under +1). The cause is a dark body with the familiar or a pale dial on its east side. The rig's production frames should widen that margin.

**Compared with Eastward:** each design was compared by eye with official Eastward screenshots at the same character height (eastward-05: John, Sam and the townsfolk; the riveted cabins; rock clumps and crates). The screenshots were not added to the repo. What we matched:

- one lit cap and one dark crescent per part
- 4 to 5 tones a material
- 2 x 3 eyes with a glint
- plates with lit lips and rivets
- a hard shadow under a brim

## Decisions for Matt

The familiar's size on the shoulder is batch 1's first decision, and it applies here too. Five of the six designers raised it again. At 24 art px the Mossling covers Pendle's dial, Ashe's horn and Cairn's capstone. Otherwise, Matt signs off the six silhouettes.

## Open, for Claude A and for the rig

- **Tuff's width.** Tuff is 60 px wide in profile, so his back shoulder is about 27 art px behind his foot. That reaches the familiar's follow distance (14 world px). Either the familiar trails Tuff a few pixels further, or he stays the one wide folk. Proposal: a `followBehindWorld` override per folk in the spec.
- **Palette.** Tuff's turtle uses sand as a fifth family, because lagoon vanished against the shell.
- **Smaller calls:**
  - Nix: are the bumps antennae or ears?
  - Ashe: should her cast ring the bell instead of breathing an ember?
  - Pendle: should the cap come off in the cheer?
- **cast.md needs a fix:** in its "to all" summary note, the Cogsworth apprentice is still "Tock". The cast table says Pendle.
