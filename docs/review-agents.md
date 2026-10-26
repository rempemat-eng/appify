# Review agents: the asset gate and the scene gate

Matt, 25 Oct 19:18: "try to build really sophisticated agents that catch logic errors and others that catch detailling errors", and 19:19: check art "after the props or background is first drawn ... before it gets placed and left in the world". He had been finding the faults himself. Two reviewers now find them first, backed by detectors calibrated on his flagged screenshots.

- **logic-auditor** (`.claude/agents/logic-auditor.md`): what holds things up, what touches what, scale against a person, water, shadows, paths and reach, occlusion, biome, quest and door wiring.
- **detail-auditor** (`.claude/agents/detail-auditor.md`): flatness, volume, material texture, outlines, mesh and speckle, repetition, light, water depth, and the per-object detail bar against Eastward at the same character height.

Both are independent: an agent never reviews work made in its own session. Both visit every region of every picture (a fixed grid of 3x crops), ask a fixed checklist of every object, compare with Eastward, list every finding with location, crop, severity and fix, count the detector findings they reject as false positives, and never pass what they did not look at.

## The required step for every lane

Before you hand art to Claude A or Matt:

1. **Asset gate**, for every asset you drew or changed (prop, building, plant, rock, water piece, ground or background):
   `npm run review:asset -- <zone>/<name>` (or `<png> --kind <kind> --biome <biome>`; `kit/<name>` for the kit's ground props). Open the sheet in `artifacts/review/assets/`: the asset at 4x with every finding boxed, then at 1x and 2x on neutral grey and on its biome's ground, beside Bramble for scale and beside its approved siblings. Fix until it passes, then `--record` it and have a **detail-auditor** run its checklist on it (from another chat or a subagent that did not draw it) and set the record's `reviewer` verdict.
2. **Scene gate**, for every zone you placed it in: `npm run review:scene -- <zone>` renders the zone headless at 1920 x 1080 at every spawn (Xvfb, `docs/godot.md`), composes the whole zone from its scene and runs both detector sets. Then run a **logic-auditor** and a **detail-auditor** on the result. Their reports go in `docs/reviews/<date>-<subject>.md`.
3. Say in the PR what was reviewed, by which agent, the counts, and what was fixed.

**The placement gate.** `npm run check:kit` (and so `npm run verify` and CI) runs `python3 -m scripts.review.gate --check`: every picture a zone places from `game/zones/<zone>/art/` needs `art/catalogue/<zone>/<name>.json` with a matching sha256 and a pass. The generators (`game/tools/gen_village.py`, `gen_zone.py`) call the same check before they write a scene and refuse otherwise. The art already in the world on 25 Oct was seeded into `art/catalogue/fix-queue.json` (most of it fails): a queued asset may stay placed, and be redrawn and re-recorded, while it climbs out of the queue; a new asset must pass. Remove an entry from the queue when its asset passes.

## The detectors

`scripts/review/` (Python with PIL, numpy and scipy). Every size is a fraction of the character height H in the picture's own art pixels (the game 74, the 2x pilot 50, Eastward 54), so one threshold serves every density. `core.to_native` brings any picture to its art grid first (it measures the pixel scale from the edge spectrum, so a 3.14x Retina screenshot of the 2x game comes back at 960 x 540).

| Module | Gate | Detectors |
| --- | --- | --- |
| `water.py` | scene, ground assets | `logic.water_staircase`, `logic.water_straight`, `detail.fall_flat`, `logic.fall_face`, `logic.water_source`, `logic.bridge_span` |
| `screen.py` | scene, ground assets | `logic.stray_line`, `detail.repetition` (stamped tufts), `detail.flat` (one-tone areas and flat objects), `detail.flat_line`, `detail.no_falloff` (interiors), `detail.debug_overlay` |
| `scene.py` | scene (Godot data) | `logic.occlusion`, `logic.intersect`, `logic.crown_cut`, `logic.reach`, `logic.shadow_orphan`, `logic.prop_row`, `logic.wiring` |
| `detail.py` | asset | `detail.flat`, `detail.volume`, `detail.texture`, `detail.light`, `detail.mesh`, `detail.water_flat` |
| `construct.py` | asset | `logic.floating_part`, `logic.stilts`, `logic.dotted_line`, `logic.scale` (size guide), mushrooms (`logic.scale`, `logic.prop_row`), `logic.biome`, `detail.mesh` (see-through crowns), `detail.water_flat` (half discs, flat troughs), `detail.light`, `detail.repetition`, `detail.glyph` (UI-like marks), `logic.construction` (a well needs a crank), `detail.volume` (cylinder shading) |
| `cast.py` | characters | `cast.foot_slide`, `cast.walk_speed`, `cast.seam`, `cast.equipment`, `cast.end_pose`, `cast.light` (ported from the 25 Oct cast audits; `python3 -m scripts.review.cast [ids]`) |
| `bands.py` | asset, scene | `detail.bar`: tones and shapes a patch against Eastward's prop, stone and foliage bands, both through the same JPEG pipe (`eastward_bands.json`, numbers only); `ground_plane`: a calm ground plane against Eastward's ground band (below) |

Commands: `npm run review:asset`, `npm run review:scene`, `npm run check:review` (unit tests on synthetic pictures), `python3 -m scripts.review.calibrate --flagged <Matt's folder> --eastward <Eastward folder>` (recall and false positives; the pictures stay local).

## Calibration (25 Oct)

`scripts/review/calibration_set.json` holds Matt's flagged faults: the woodland at 1080p (14), the Crossroads close-ups (15) and the Undercroft boss room (9), with the asset versions he saw pinned to their commits. Every fault is caught by at least one route: **38 of 38**. False positives, counted as every fault-level finding on art that is approved or is the reference: **5 on 6 clean screens** (the pilot golden and Eastward 08, 12, 13, 17 and 37: 0.8 a screen) and **20 on 22 clean prop crops** (the golden's and Eastward's, 0.9 a prop, mostly `detail.volume` on parts cut from JPEG or the golden's fence rails; checks that need a real alpha channel are not counted on cut crops). `calibration_results.json` has the table. The image-only shadow and canopy-mesh guesses (`screen.shadows`, `screen.mesh`) are kept behind `experimental=True`: they fired on Eastward as often as on our art, so shadows are checked from the zone's data and crowns from their sprites instead.

What the detectors cannot see, the agents must: whether a waystone reads as a waystone, whether a room has wall faces, where a door leads, whether a placement makes sense for its owner. The detectors are leads; the agents' checklists are the review.

## Ground planes (26 Oct)

`detail.flat` (`screen.flat_objects` and `screen.flats`) was written for things: a prop painted in four tones or fewer, or a one-tone patch inside one. A calm floor that is not the screen's ground palette (an indoor floor beside walls and void, as in the Undercroft) met the same rule, and the Undercroft's round 3 answered it the wrong way, with a glossy diagonal stripe on every flag. Eastward's dungeon floors are calm, dark fields; they would fail the prop rule too.

So a **ground plane** (an area off the ground palette at least 1 H² and 0.5 H across) is now judged by Eastward's **ground band** instead (`bands.ground_plane`, `screen.calm_ground`; a flag inside such a plane is skipped by `flats`). The band (`eastward_bands.json`, `groups.ground`) is measured on six calm ground boxes in shots 06 (the dungeon floor in shade), 13 and 17 (lawn, path, a yard's dirt), listed in `calibrate_boxes.EW_GROUND` and rebuilt with `python3 -m scripts.review.bands --ground <Eastward folder>`. A plane passes when it is both:

- **drawn**: tones and shapes a 0.25 H patch (through the same JPEG pipe) at least 0.9 x the band's least (Eastward 7.5 tones, 23 shapes; band means 11.8 and 39.9);
- **calm**: the contrast between its pieces (the luminance spread after a 0.12 H median, which keeps flag against flag and drops joints and grain) at most 1.15 x the band's most (Eastward 15.9 L).

A flat fill (2 to 3 tones, 4 to 5 shapes a patch) still trips, and so does a bright floor of contrasting slabs: Matt's terrazzo floor (U1) measures 28 to 33 L between its pieces against Eastward's 5 to 16. The round 4 Undercroft floor measures 9.5 to 11 tones, 27 to 29 shapes and 13 to 16 L. `npm run check:review` holds one picture of each (`GroundPlane`: a calm Eastward-like floor that passes, a flat one and a bright contrasting one that trip).

The zone faults (W7, W8, W12 and the other woodland zone routes) are now pinned to the commit Matt saw (`woodland@2f88ca53` in `calibration_set.json`; `calibrate.pinned_game` extracts the zone's data and the files its scenes reach), as the asset routes already were. Before that, a fixed woodland made the calibration lose the faults it was built on (35 of 38 on 26 Oct). With the pin and the ground band: **38 of 38**; the false positives are in `calibration_results.json`.

## Adding a detector

1. Write it as a function returning `core.Finding`s (detector id `logic.<name>` or `detail.<name>`, severity, box in art px, a one-sentence message, a concrete fix, the measured score and its threshold). Put image checks in `screen.py` or `water.py`, scene-data checks in `scene.py`, per-asset checks in `construct.py` or `detail.py`, and wire it into `screen.review_screen`, `scene.review_zone` or `assets.review_rgba`.
2. Express sizes as fractions of H and measure luminance in L units, so it works at every density and on JPEG.
3. Add a test to `test_review.py` with one synthetic picture that must trip it and one that must not.
4. If it answers a fault Matt found, add the fault to `calibration_set.json` (his screenshot stays local; pin the asset to its commit), run `calibrate`, and keep recall at 100 % with the false positives no higher than before. Note the new numbers here.
5. List it in both agents' checklists if it changes what they must look for.

## The dry run (25 Oct)

`docs/reviews/2026-10-25-world.md`: the full procedure on the woodland and Crossroads at 86e52500. 39 findings (1 blocker: the camera shows the void for the first two seconds of a fresh start), 85 detector findings of which 14 were rejected as false positives (16 %), and 5 faults the checklist caught that no detector did (the waystone rune, roof grilles, tarps, the choked well's ring, puddles): leads for the next detectors.
