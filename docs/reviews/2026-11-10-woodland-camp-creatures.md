# Asset gate: woodland camp creatures (independent verdicts), 10 Nov 2026

Reviewed by the detail-auditor (a session that did not draw this art) at main 2f3335cd: `art/cast/{boarlet,toad,tortoise,den}/` (724 drawings; the game's sheets in `game/assets/characters/<id>/sheets/` and `game/assets/enemies/` hold the same pixels, checked frame by frame). The thornback (264 records, also pending) was not in the brief and has no verdict.

**Result: no creature may be placed.** 291 drawings pass and 433 fail (boarlet 86 / 154, toad 77 / 163, tortoise 128 / 108, den and clumps 0 / 8). Every creature has failing clips, so a pass on a drawing does not place the creature.

Commands: `python3 -m scripts.review.assets art/cast/<id>/*.png --biome woodland --record` (all 724; today's detectors add `detail.cluster_noise`, at fault level on 32 drawings, so 32 records now have status `fail`), `python3 -m scripts.review.cast boarlet toad tortoise`, and the auditor's own measurements (colours, outline, light, mirror test, shard light side, foot anchors against ground-contact pixels, tones and shapes a patch). Compared with Eastward shot 17 (Octopia farm yard, the two pigs, the third pig and the cow, interior boxes at native 640 x 360 scaled 1.37 to H 74, same JPEG pipe) and with Bramble, in a 1080p game frame with `--camp` on the meadow.

## Verdicts by clip and facing (drawings failing / drawings, fix codes x drawings)

| creature | clip | S | N | E | W |
| --- | --- | --- | --- | --- | --- |
| boarlet | idle | pass 8/8 | FAIL 8/8 (B2x8) | pass 8/8 | FAIL 8/8 (C1x8) |
| boarlet | move | FAIL 2/8 (N1x2) | FAIL 8/8 (B2x8) | FAIL 8/8 (B3x8) | FAIL 8/8 (C1x8 B3x8) |
| boarlet | telegraph | FAIL 6/8 (N1x1 B4x5) | FAIL 8/8 (B2x8 B4x5) | FAIL 5/8 (B4x5) | FAIL 8/8 (C1x8 B4x5) |
| boarlet | attack | FAIL 4/4 (B4x4) | FAIL 4/4 (B2x4 B4x4) | FAIL 4/4 (B4x4) | FAIL 4/4 (C1x4 B4x4) |
| boarlet | hurt | pass 4/4 | FAIL 4/4 (B2x4) | pass 4/4 | FAIL 4/4 (C1x4) |
| boarlet | stagger | pass 7/7 | FAIL 7/7 (B2x7) | pass 7/7 | FAIL 7/7 (C1x7) |
| boarlet | freed | FAIL 6/13 (N1x6) | FAIL 13/13 (B2x13) | pass 13/13 | FAIL 2/13 (C1x2) |
| boarlet | freed_move | FAIL 2/8 (N1x2) | FAIL 8/8 (B2x8) | FAIL 8/8 (B3x8) | FAIL 8/8 (B3x8) |
| toad | idle | pass 8/8 | pass 8/8 | FAIL 8/8 (T5x8) | FAIL 8/8 (C1x8 T5x8) |
| toad | move | FAIL 8/8 (T4x8) | FAIL 8/8 (T4x8) | FAIL 8/8 (T4x8 T5x8) | FAIL 8/8 (C1x8 T4x8 T5x8) |
| toad | telegraph | FAIL 6/8 (T2x6) | pass 8/8 | FAIL 8/8 (T5x8 T2x6) | FAIL 8/8 (C1x8 T5x8 T2x6) |
| toad | attack | pass 5/5 | pass 5/5 | FAIL 5/5 (T5x5) | FAIL 5/5 (C1x5 T5x5) |
| toad | hurt | pass 4/4 | pass 4/4 | FAIL 4/4 (T5x4) | FAIL 4/4 (C1x4 T5x4) |
| toad | stagger | pass 7/7 | FAIL 5/7 (T3x5) | FAIL 7/7 (T5x7 T3x5) | FAIL 7/7 (C1x7 T5x7 T3x5) |
| toad | freed | pass 12/12 | pass 12/12 | FAIL 12/12 (T5x12) | FAIL 12/12 (C1x2 T5x12) |
| toad | freed_move | FAIL 8/8 (T4x8) | FAIL 8/8 (T4x8) | FAIL 8/8 (T4x8 T5x8) | FAIL 8/8 (T4x8 T5x8) |
| tortoise | idle | FAIL 4/8 (N1x4) | pass 8/8 | pass 8/8 | FAIL 8/8 (C1x8) |
| tortoise | move | FAIL 1/8 (N1x1) | pass 8/8 | FAIL 8/8 (K3x8) | FAIL 8/8 (C1x8 K3x8) |
| tortoise | telegraph | FAIL 6/8 (N1x6) | pass 8/8 | pass 8/8 | FAIL 8/8 (C1x8) |
| tortoise | attack | FAIL 4/4 (K1x4) | FAIL 4/4 (K1x4) | FAIL 4/4 (K1x4) | FAIL 4/4 (C1x4 K1x4) |
| tortoise | hurt | FAIL 1/4 (N1x1) | pass 4/4 | pass 4/4 | FAIL 4/4 (C1x4) |
| tortoise | stagger | FAIL 7/7 (N1x2 K2x5) | FAIL 5/7 (K2x5) | FAIL 5/7 (K2x5) | FAIL 7/7 (C1x7 K2x5) |
| tortoise | freed | FAIL 2/12 (N1x2) | pass 12/12 | pass 12/12 | FAIL 2/12 (C1x2) |
| tortoise | freed_move | pass 8/8 | pass 8/8 | FAIL 8/8 (K3x8) | FAIL 8/8 (K3x8) |
| den | clump_calm | FAIL 1/1 (L1x1) | | | |
| den | clump_lit | FAIL 3/3 (L1x3) | | | |
| den | den_calm | FAIL 1/1 (D1x1 D2x1) | | | |
| den | den_lit | FAIL 3/3 (D1x3 D2x3) | | | |

## Findings and fixes

- **C1 (fault, 124 drawings): the shard is mirrored in every west facing.** Shard left minus right luminance is -70 to -120 L in W against +44 to +120 in S, N and E, on all three creatures. The bodies were relit (W minus E body luminance is positive in W), the shard was not. Redraw the W shard with the pale facet and glint on the left.
- **B2 (fault, boarlet, all 60 N drawings):** the spine from behind is a black stitched line (a zip); E and W show a bristle mane. Draw the mane as 5 to 7 dark tufts with lit left edges.
- **B3, K3, T4 (fault, move and freed_move):** stride against speed. Planted-foot speed from the anchors, confirmed on ground-contact pixels: boarlet 51.4 px/s (manifest 37.1), tortoise 37.1 (manifest 26.1), toad 8.6 (manifest 25.9; its hind foot never moves and it never leaves the ground). `slice_enemy.gd` moves every role at 102 art px/s on approach, so the slide is 28, 36 and 52 px a 0.56 s cycle. Fix the manifests' walk_speed to the stride, play the clip at velocity / walk_speed in `creature_look.gd`, and draw the toad a hop.
- **T2 (fault, toad telegraph S, E, W, drawings 2 to 7):** a flat orange plus sign at the lips, the calibration set's flat glyph. **T3, K2 (fault, stagger drawings 1 to 5):** flat dark plus signs as dizzy marks. **K1 (fault, tortoise attack, all 16):** the stomp is a flat khaki hoop over the feet. **B4 (fault, boarlet telegraph 3 to 7 and attack):** dust as outlined cream blobs that read as bones. Replace each with unoutlined dust or a lamp-toned glint (the records hold the drawable instruction).
- **T5 (fault, toad, all E and W):** the side view measures 11.3 tones and 14.3 to 18.3 shapes a patch against Eastward's animals at 14.0 and 27.6 (0.81 and 0.52 to 0.66), and has no folded hind leg.
- **N1 (fault, 27 S drawings of boarlet and tortoise):** `detail.cluster_noise` at fault level, not overturned. Other drawings of the same facing sit just under the line, so calm the texture across the facing.
- **D1, D2 (fault, den):** mouth 22 x 17 px and mound 42 px tall against creatures 40 to 45 px tall; the weave reads as brick courses. **L1 (fault, clumps):** a three-tone mound with a flat V of twigs.
- Polish: the boarlet's E facing has no west-to-east falloff (W minus E -3.2 to 0.4 L against +11 to +14 in W); the toad has two leaves in N and one elsewhere; telegraph and attack end 25 to 46 % away from idle (`cast.end_pose`), covered in play by the stagger clip.

What passes: outlines are closed in each family's dark tone (96 to 100 % of the silhouette, no stray semi-transparent pixels), 14 to 30 colours a drawing, lone pixels 1 to 5 % (limit 6), volume holds within a clip (1 to 8 % area change outside poses that add dust or a ring), feet stay planted outside walks (at most 4 px, 6.5 in the boarlet's charge), light is upper left on every body. Boarlet (15.8 to 16.8 tones, 39 to 41 shapes) and tortoise (20 to 24, 35 to 38) meet Eastward's animals; against the gate's prop band they are 0.50 to 0.75, which is the wrong band for an animal.

## In code, not in the pictures (game/enemies is reserved; reported only)

`creature_look.gd` scales the sprite 1.06 x 0.93 during a wind-up and turns the toad up to 0.2 rad: both leave the pixel grid. The contact shadow and the scuff marks are alpha circles and rectangles, not ramp steps.

## False positives

0 rejected. `detail.light` on the boarlet's E facing is kept as polish.

## Not checked

The thornback; the seed and shard effect pictures (no records); night tint; reduced motion; phone scale; the slide and the wind-up scaling in captured game frames (derived from the clips and the code); frame-by-frame eye review of every one of the 724 drawings at 8x (each clip sheet was opened at 4x, measurements cover every drawing).

No fix-queue entry was added: the queue holds only art placed before the gate's seed, and these are not placed. The fix lists are in each record's `reviewer.note`.
