# Crossroads trees and shrubs: the approved woodland copies (10 Nov)

The independent audit of draft PR #460 (`claude-a/crossroads-trees`). The PR replaces the 24 queued Crossroads trees and shrubs with byte copies of the woodland pictures approved in round 9 of `2026-11-09-woodland-assets.md`, moves four trees, and re-lays the lawn and shadows around them.

## Round 1 (PR #460 head cba98f46, 10 Nov)

Reviewed by a detail-auditor that drew none of it. Base main ba0244a6.

**Result: 26 of 27 pass, and oak_13 fails on its placement.** All 24 copies are the approved bytes, unmirrored, with their feet on the drawn foot. oak_13's move puts its crown over the arrival from the woodland. The woodland spawn is 100 % hidden and the to_woodland door 57 % (XT1). The new `detail.repetition` fault does not block. It counts the lit leaf highlights of identical approved copies across the whole zone, the ground has none, and no screen-sized view comes near the bar (ruling 1).

### What was reviewed and how (round 1)

- Fresh worktrees at cba98f46 and main ba0244a6. Since main, only the files listed in the PR body change: the 24 PNGs and their records, `ground.png`, the two beds shadow overlays and their records, the plan, `kit.json`, `crossroads.tscn`, the three Crossroads kit pieces with their prop scenes and index, the golden manifest's `inputs`, the kit fixture hash, the intake pin, `town.py` and `screen.py`. No woodland record or picture changed.
- **Identity.** Each copy's sha256 equals its record's and the round-9-approved woodland record's. The decoded RGBA arrays are equal pixel for pixel, and none equals its source mirrored. `crossroads.tscn` has no `flip_h` and no negative scale.
- **Asset gate.** `python3 -m scripts.review.assets` on the 27 ids (no record) reproduces every record: the 24 copies 0/0/1 (`detail.bar` polish, as their sources), and ground and both overlays 0/0/0.
- **Composite.** `sha256(scene.composite(load_zone('crossroads')))` is 3f481ce8… at head, which matches the new pin in `test_kit_scene_intake.py`, and cc2fa5e3… on main. Of 395,339 changed texels, 373,991 fall inside the swapped boxes and 21,348 outside, as the painter says.
- **Scene gate.** `npm run review:scene -- crossroads` with renders gives main 88 / 54 / 4 and head 88 / 33 / 4. The PR says 32. The difference is one `logic.stray_line` at [5,5,67,18] in a rendered view's corner. It sat in the hut view on main and is in the halt view at head, and both runs have 4. That box is a render-corner mark, not art.
  - Gone: the 3 `logic.crown_cut` and 16 `detail.flat`.
  - New: `detail.repetition` on the zone composite (1.14). The other new lines are the same flat-object boxes reported in a different picture or shifted by 1 px.
  - `--no-render` gives main 88 / 25 / 4 and head 88 / 20 / 4.
- Also run: `grid_snap --check` (ok), `placement_audit --check` (ok) and `python3 -m unittest scripts.review.test_review` (178 OK).
- **Own scripts** (auditor scratch `audit460r1_tools/`, not committed; detectors and thresholds untouched):
  - `feet.py`: the origin against the drawn base;
  - `clear.py`: foot distances to routes, faces, doors, spawns and targets;
  - `occ.py` and `targets.py`: how much of a 74 × 36 texel companion box at each spawn, door and touch target is covered by a swapped sprite drawn in front;
  - `gdiff.py` and `cdiff.py`: the confined diff;
  - `rep.py` and `repwin.py`: the repetition detector's count, attributed to its owner, with duplicates masked, and per screen-sized window;
  - `ewdup.py`: template matching for reused Eastward sprites.
- **By eye** (auditor scratch `audit460r1_crops/`):
  - the full composite at 1x;
  - main beside head for the top band at 1x, the top left and top right at 2x, and the park at 1x and 2x;
  - the house rows at 6x;
  - Eastward 13 at ×1.37 nearest beside the park at matched character height (ours 74, Eastward 54), and five crops of Eastward 13's conifer at 4x.
- The Eastward shots stay local.

### Verdicts (round 1)

| Record | Source | Verdict | Notes |
| --- | --- | --- | --- |
| oak_6 | hollow_tree | **pass** | moved to 184,56; XT6 polish |
| oak_13 | oak | **fail** | XT1: crown over the woodland spawn and door |
| oak_21 | oak | **pass** | moved to 616,104 |
| oak_40 | oak | **pass** | moved to 328,552 |
| oak_42, oak_43 | oak | **pass** | |
| oak_41, oak_44, oak_45, oak_46 | beech | **pass** | |
| bush_7, bush_14, bush_16, bush_22, bush_49, bush_50 | bush | **pass** | XT4 polish; W9-P1 carried |
| bush_8, bush_15, bush_17, bush_23, bush_47 | bush_b | **pass** | |
| bush_18, bush_48, bush_51 | bush_c | **pass** | |
| ground | | **pass** | confined; XT3 polish. If oak_13 moves, ground changes and returns to pending |
| beds_dug_shadow, beds_scorched_shadow | | **pass** | 12 and 11 texels, consistent with the ground |

For each copy the verdict is an identity check, as woodland round 9 ruling 3 allows. The detail audit of these bytes is round 9's.

### Measurements

**Feet and y-sort.** Every origin is on the drawn bottom row (dy 0).

| Picture | Origin to drawn base centre (texels) | Offset |
| --- | --- | --- |
| oak, beech, hollow_tree | +0.5 | (-106,-247), (-96,-264), (-122,-227) |
| bush_c | 0 | |
| bush_b | +1.5 | |
| bush | −5 (1.7 world px, XT4) | |

The trees' offsets equal the woodland kit pieces'. Solids are unchanged: 8 × 4 for the oaks, 16 × 6 or none for the bushes.

**Soft grid.** Every foot has x on a multiple of 4 and y on a multiple of 8. `grid_snap` is ok.

**The moved trees (world px).**

- **oak_6 at 184,56.** Its foot is 4 px above the garden walk's edge. The crown box runs from y −20, so 74 % of the crown is in the zone and there is no crown_cut. At 2x the hollow trunk with its creature's hole stands on the lawn above the walk, and its contact shade reaches the walk's top lip, east and down. Anyone on the walk has feet below 56, so they are drawn in front of it.
- **oak_13 at 16,112.** The foot is inside the plan's `lane_face` rect (y 100 to 150), which is drawn as a lawn bank with bushes, not a wall, so the foot reads. The crown, though, covers the woodland arrival (XT1).
- **oak_21 at 616,104.** It stands on the hay slope's foot (`terrace_bank_e`), 140 px from the smithy. It covers no spawn, door or target, and its crown is whole.
- **oak_40 at 328,552.** It is 68 px from the green lane. Its crown is clear of oak_41's (a gap of about 20 texels at 2x).
- **Cover.** `targets.py` checks every spawn, door, building door, thing, person, restore site and raid pad. Against main, which covers none, the only new cover is oak_13 over `spawn:woodland` (1.00) and `door:to_woodland` (0.57).

**Neighbours.**

- No tree's or shrub's nearest neighbour uses the same picture (0 of 10 trees and 0 of 14 bushes).
- The closest same-picture pairs are bush 111, bush_b 118, beech 208 and oak 279 world px apart. The PR's ≥ 110 for bushes holds.
- There is one hollow_tree.
- In any 877 × 493 texel window (one Eastward screen at ×1.37), at most 2 identical trees and 3 identical bushes appear. Eastward 13 shows one conifer sprite at least 5 times in a single screen, unmirrored, with neighbours 57 to 79 native px apart (78 to 108 texels at ×1.37) (`ew13_trees_4x.png`).

**Ground diff.** 83,127 texels of `ground.png` change:

- 61,190 inside the swapped sprites' old or new boxes;
- 19,794 within 72 texels of an old, new or `lawn_at` foot;
- the rest are the tree casts thrown further east and down (oak_6, oak_13's old spot, oak_40, oak_41, oak_44 and oak_45, each 73 to 104 texels east of its foot), plus 400 texels on house lawn rows.

188 of those 400 show in the composite, which confirms the painter: hut front 42, below the hut 64, library corner 22 and bakery foot row 60. `ground.png` alone scores 0.00 on `detail.repetition`.

**Beds shadow overlays.** 12 (dug) and 11 (scorched) texels change, at overlay x 251 to 263 and y 8 to 13. Each moves from a step over the old, larger bush_8 cast to the same step over plain lawn (ground #86a458 → overlay #648445). That is the overlay's one-step ratio everywhere else, so the overlay agrees with the new ground.

### Ruling 1: `detail.repetition` 1.14 does not block

1. **It is the copies, not the ground.** Of the 671 repeating blades, 487 lie inside the oak, beech and hollow copies and 176 inside the bushes. The other 7 (hut 3, library 4) are on main too. With every second and later copy of an identical sprite masked, the zone scores 0.01, main's value. `ground.png` alone scores 0.00. The detector reads lit leaf highlights as "tuft blades", because foliage falls in its green family.
2. **It is a whole-zone count.** Repeats are pooled over 1920 × 1680 texels, about seven screens. Over 25 screen-sized windows of the head composite, the highest density is 0.16 and the median 0.00. That is inside Eastward's 0.0 to 0.7, and none of the rendered views fires.
3. **Eastward reuses identical tree sprites more densely than we do.** Eastward 13 at ×1.37 has at least 5 copies of one conifer on one screen; ours has at most 2 per screen. On the reference shots the detector measures 0.00 to 0.16. That is because JPEG breaks exact blob masks, not because Eastward avoids copies, so its 0.0 to 0.7 band undercounts sprite reuse.
4. **Precedent.** The approved woodland composite scores 2.78, all of it from identical copies (15 of one oak). Round 9 ruling 3 asked for exactly this reuse.
5. **No change asked.** The fault is recorded as a false positive in kind for this PR. Clearing it would need more approved variants, not ground grain, and the detector and threshold stay as they are. A later detector owner may want to leave sprite pixels out, or count per screen. That is not this audit's call.

### Findings (round 1)

**XT1 (F, blocking; oak_13).** The crown covers the arrival from the woodland.

- At 16,112 the oak's crown (box x −19 to 51, y 30 to 112 world) hides the woodland spawn (30,70) 100 % and the to_woodland door 57 % (78 % of the door rect). The first 30 px of the garden walk are 93 % covered.
- The companion arrives already behind a crown, as a 42 % ghost, at a door. AGENTS.md says paths, doors and the space round the companion stay open; art-style "Quiet where you walk" says the same.
- No tree on main covers any spawn or door.
- **Fix:** move oak_13 so that:
  - the woodland spawn and the to_woodland door are each under 40 % covered (ideally 0), and the walk's first two cells are open;
  - the foot stays on the soft grid, off routes, with no crown_cut and no same-picture nearest neighbour.
- Then re-lay the lawn, re-pin the composite, and send ground and oak_13 back to pending.

**XT2 (P; zone).** `detail.repetition` 1.14 is a false positive in kind (ruling 1). Nothing to fix in this PR.

**XT3 (P; ground; XR3-G1 residue).** 188 visible texels on the hut, library and bakery lawn rows are reshuffled scatter.

- At 6x they are the same kind of marks at the same density: pebbles and crumbs.
- This is acceptable, as in round 3 of `2026-11-08-crossroads-placed.md`. XR3-G1 (make the scatter local) stays open.

**XT4 (P; the 6 `bush` copies).** The y-sort origin is 5 texels (1.7 world px) west of the drawn base centre.

- It follows the woodland's foot-at-bottom-middle convention, and y is exact. It is harmless at 1x.
- If the bush is redrawn (W9-P1), centre the mass on its foot.

**XT5 (P; PR body).** Three statements in the PR body are stale or wrong:

- "The pin is now e88b83aa…" is left over from the first pass; the pin is 3f481ce8….
- The beds overlays lose the old bush_8 cast; they do not "take in bush_8's new cast".
- The head scene count is 33 faults, not 32 (one extra `logic.stray_line` on a render corner).

Correct them when the PR is next edited.

**XT6 (P; oak_6).** The hollow tree's drawn trunk base is 28 world px wide against its 8 × 4 solid, as the painter notes. A companion can stand inside the flare's edge. Widen the solid to about 20 × 6 if the gate allows.

**Carried:** W9-P1. The bush's mirrored upper gaps now appear 6 times in the zone. They are still polish, and they read as a cleft at 1x.

### Eastward comparison

- **1x:** `ew13_vs_park_1x.png` puts Eastward 13 and the park side by side.
- **2x:** `ew13_vs_park_2x.png`, plus `park_2x.png` and `top_left_2x.png` against main.
- **On valley ground:** the copies read as the round-9 crowns. They have lobes with shade under their edges, light from the upper left, and their trunks seated in the lawn with an east cast. They hold the same detail as at the woodland, and the old, smooth Crossroads crowns are gone.
- **Neighbours:** neighbouring trees alternate oak and beech, and at 1x the eye does not pair the identical copies, which are at least 279 px apart.

### Gate (round 1)

- This round sets the reviewer block of all 27 records: 26 pass, oak_13 fail, with XT1 as its `fix_list`.
- `python3 -m scripts.review.gate --check` then prints `[review gate] 7 zones, fix queue 24 assets: 1 refused`. The refusal is oak_13: its queue entry holds the old bytes.
- It also prints **23 ADVISORY lines**, one for each copy except oak_13. Removing those entries is Claude A's call. oak_13's entry stays until XT1 is fixed and re-audited. Merging with oak_13 failing would fail `check:kit`.
- This round edits only the 27 records and this file: no art, queue, detector, threshold, generator or game file.

### Not checked (round 1)

- A device or in-app play-test, night tint, reduced motion, and the 402 × 874 phone view.
- `npm run verify`, `check:art-repro` and CI. I did not regenerate the zone, so the painter's byte-for-byte claims for `town.py` and `screen.py` (the woodland unchanged) were checked only through the unchanged woodland records and pin.
- Kit pieces, prop scenes and index were read from the diff, not audited.
