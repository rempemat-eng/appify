# Cast audit (independent, 25 Oct, about 11:45)

Scope: all fourteen characters in `out/<id>/` as they stood in the working tree at 11:45. **Cairn and Pendle were being re-exported by the lead (uncommitted changes in out/cairn, out/pendle)**, so their findings apply to that snapshot and must be re-checked after the lead commits. No source was edited.

Method: automated passes over every drawing (packed bounds, opaque area, per-clip equipment pixel counts, foot anchors, loop seams, release anchors against drawn pixels, clip end against the rest pose, light direction per facing, `Rig.limb` reach ratios per pose), then enlarged crops of every flagged drawing and the key drawings (wind-up, release, recovery, end) of primary, secondary, special, guard, powered_primary, powered_guard and powered_exit in S, N, E, W for every character, plus a 2x game-size sheet. Tools: `scratchpad/audit/` (metrics.py, reach2.py, cont.py, light.py, keys.py, strip.py, crop.py). Evidence crops: `review/audit/`.

Severity: **blocker** = breaks a stated logic rule every time the action plays; **clear fault** = visible logic or anatomy error a player can see at 2x; **polish** = worth fixing, not wrong.

## Counts

| Character    | Blocker | Clear fault | Polish |
| ------------ | ------- | ----------- | ------ |
| Ashe         | 0       | 2           | 3      |
| Bramble      | 0       | 1           | 4      |
| Brine        | 1       | 1           | 2      |
| Cairn (WIP)  | 1       | 3           | 3      |
| Clack        | 0       | 5           | 2      |
| Iona         | 0       | 2           | 2      |
| Mirra        | 0       | 0           | 3      |
| Morel        | 0       | 0           | 2      |
| Mote         | 0       | 0           | 2      |
| Nix          | 0       | 0           | 3      |
| Pendle (WIP) | 0       | 0           | 2      |
| Rook         | 0       | 1           | 3      |
| Tam          | 0       | 3           | 1      |
| Velvet       | 0       | 1           | 2      |
| Cast-wide    | 1       | 1           | 2      |
| **Total**    | **3**   | **20**      | **36** |

What passed everywhere: 0 checks.py errors; every release anchor lies on drawn pixels of the right emitter (arrow_tip, muzzle, palm, flask, spear_tip, blade_tip, fist, lantern, nozzle) at the release drawing or the one before; one-sided gear is on the correct side in all four facings for all 14 (Nix's laser arm anatomical left, right arm natural; Bramble's bow in the right hand, drawn with the left; Velvet sabre left, lantern right; Morel flask right, catalyst left; Rook helmet right back hip; Iona spear right; Ashe sword right, helm under the left arm; Mirra gem right, tail left; Pendle rifle over the left shoulder; Clack launcher on the right shoulder, rack front left; Cairn sprout left); W is relit (light measured from the upper left in all four facings for all 14); idle never pops in height (1 px breath; Cairn 3 px); no walk loop pops at the seam; planted feet in walks travel at the manifest `walk_speed`; powered state tags (Tam ice, Iona storm, Cairn growth, Ashe helm, Morel mask, Rook helmet, Clack loader) persist through every powered clip and are cleared by powered_exit; special's last drawing matches powered_idle and powered_exit's last matches idle. Decided items are honoured: Tam male monk in orange; Bramble left-handed; Clack goggles pushed up; Cairn round with big arms.

## Cast-wide

1. **Blocker (runtime + art): the powered state has no hit, dodge, jump, stair or secondary drawings.** While powered, the runtime can only play the base clips for these, which drop the powered look for their duration: Ashe's helm returns under her arm, Tam's ice vanishes, Rook's helmet jumps to the hip, Morel's mask returns to the chest, Pendle's rifle is replaced by the revolver and slung rifle, Clack's loader folds, Brine's glow, Cairn's splints, Iona's storm blade, Bramble's vine bow, Nix's open casing, Mote's open coat and Velvet's open lantern all disappear. Fix: until powered variants exist, follow runtime rule 5 below; for production, export `powered_hit`, `powered_dodge`, `powered_jump`, `powered_stair_up/down` (and `powered_secondary` where the secondary is allowed while powered) with the same tables and the powered state flag.
2. **Clear fault (shared rig, `parts.Rig.zarm`): in N a hand reaching across the body near the body plane is drawn over the back.** `zarm` puts an arm in front of the torso whenever the hand depth is within 3.5 px of the body plane, so a cross-body reach (hand on the other side of the midline, in front of the chest) is painted over the back in the N view. Seen in Ashe, Clack and Velvet (entries below; survey crop `review/audit/N_cross_body_arms_survey.png`). Brine, Rook, Iona, Pendle and Mirra cross-body reaches are correctly hidden. Fix (lead): in N, when the hand's lateral position crosses the midline or the elbow is in front of the chest, use the far depth for the forearm and upper arm.
3. Polish: **stance snaps without a lifted in-between.** Many guard and attack wind-ups move both feet 4 to 8 px apart in one drawing with both soles on the ground (feet skate). Worst: Tam secondary 3 and 7 (7 to 8 px), Iona secondary 1 (7.5 px), Velvet primary 9 (7 px), Cairn secondary 9 (7 px), Clack primary/secondary/special/powered_primary 1 and the return (6.5 px); 6 px in Mirra, Morel, Nix, Rook, Tam and Velvet guards. Fix: when a foot moves more than 3 px, lift it 2 to 3 px in that drawing (or add a 40 ms in-between) and plant it in the next. Tam, Iona and Cairn are listed as clear faults below.
4. Polish: **jump drawing 7 and dodge drawing 7 do not match idle 0** (stance width and arm pose; 30 to 50 % of pixels change for jump, 15 to 35 % for dodge, all 14). The runtime cut to idle shows a small stance pop. Fix: make recover (jump 7) and dodge 7 the idle stance, or have the runtime leave jump into walk when moving.

## Ashe

1. **Clear fault: left arm drawn over the back in N.** powered_guard N 0 to 7, powered_primary N 0 to 10: the free left hand joining the grip is painted across the cape. Fix: cast-wide item 2. Crop `ashe_powered_leftarm_stretch.png`.
2. **Clear fault: left arm over-stretched in the two-handed powered grip.** powered_primary 0 to 10 and powered_guard 0 to 6, all facings: reach 1.2 to 1.62 (forearm drawn up to 60 % too long, visible in S as a long bar across the chest). Fix: bring the sword grip toward the body midline and twist the shoulders (`twist`), or let the left hand join only at the contact drawings (5 to 7) and rest on the pommel otherwise.
3. Polish: the helm is narrower than her hair; in special 3 to 4 the hair visibly vanishes into a smaller shell (all facings). Widen the helm by 2 px or flatten the hair volume as it seats.
4. Polish: secondary E/W 3 and 7, guard W 1 and 6: foot moves 3 to 4.5 px on the ground (cast-wide item 3).
5. Polish: dodge W 1: the sword vanishes for one drawing (hidden behind the body); keep 4 px of the blade visible.

## Bramble

1. **Clear fault: the bow pops back into the hand after a guard.** Guard hold (4) has the bow slung on the back; idle has it in the right hand. The current runtime clamps to 4 and cuts to idle, so the bow teleports. Also guard 7 is not idle 0 (bow 7 to 16 % pixel difference). Fix: runtime rule 4 (play 5 to 7), and make guard 7 equal idle 0. Crop `bramble_guard_hold_vs_idle.png`.
2. Polish: primary S 4 to 7 and special S 3 to 6: the bow and arrow cross his face toward the camera, hiding the face at 2x. Offset the bow 2 to 3 px to his right (viewer left) in S.
3. Polish (decision for Matt): the billhook is drawn and used by the RIGHT hand (documented in bramble.py). A left-handed ranger would normally wield it left; confirm or move it to the left hip and left hand.
4. Polish: walk W 1 and 9: the bow in the far hand disappears completely behind the body; keep the lower limb visible.
5. Polish: secondary E/W 3 and 8: 2.5 px stance shift on the ground.

## Brine

1. **Blocker: harpoon continuity.** primary ends (drawings 7 to 11) and powered_primary ends (3 to 7) with the harpoon gone; idle, walk, guard and powered_idle show it loaded. Every shot followed by idle or walk pops the harpoon back into the muzzle while the tether entity still exists. Ruling: the harpoon is a state. Art: export unloaded variants (`idle_empty`, `walk_empty`, `guard_empty`, `hit_empty`, and powered equivalents; the same tables with `loaded=False`). Runtime: rule 6. Without the art, the runtime must play secondary (reel) automatically before returning to idle and block movement until then, which is worse for play. Crop `brine_harpoon_continuity.png`.
2. **Clear fault: the gun has no legible grip during Pressure Brace.** special 1 to 5 and powered_exit 1 to 5, E and W: the right hand is at the regulator and the left arm's target (the fore grip) is at reach 1.89 (also 1.52 through every powered clip), so the gun hangs barrel-down at the hip with no clear hand on it (E: no hand at all; W: the near hand only touches the stock). Fix: move the held point to the gun's balance near the hip (reach under 1.0) and draw the left glove closed on the fore grip, or sling the gun on a strap while the right hand works the valve. Crops `brine_special_EW_gun_no_grip.png`, `brine_special_floating_gun.png`.
3. Polish: primary N: gun fully hidden by the body; the shot is unreadable from behind until the runtime's tether appears. Let the muzzle clear the right shoulder by 3 px.
4. Polish: in S the gun aimed at the camera is a short stack of rings (known).

## Cairn (WIP snapshot)

1. **Blocker: two rocks at the release.** secondary S/E/W drawing 6 (the release drawing) still contains the whole boulder (244 px); the runtime spawns the projectile at drawing 6, so two rocks are on screen for that drawing. Fix: remove the rock from drawing 6 (hands open, follow-through) and keep it in 4 to 5 only, or move the release to the first rock-less drawing while keeping Codex's release time. Crop `cairn_secondary_rock_at_release_and_second_head.png`.
2. **Clear fault: the carried boulder reads as a second head.** secondary E/W 4 to 5 (and S/N): a round stone above the shoulders with a dark horizontal slit and green mouth-like moss sits right where a head would be; at 2x Cairn seems to have two heads. Fix: no slit; irregular slab shape with a torn root-ball underside and dirt crumbs, and hold it forward of the head.
3. **Clear fault: heavy feet skate 6 to 7 px in one drawing.** secondary E/W 9 (both feet), special E/W 6, guard and powered_guard E/W 6 (5 px). For a golem this reads as sliding. Fix: lift then plant each foot over two drawings, with a ground puff on the plant.
4. **Clear fault: rim speckle.** 448 lone-pixel warnings (up to 49 per drawing; e.g. idle S 0 at (91,79), (109,79)): single cream rim pixels and outline breaks along the boulder edges. Fix: group rim light into 2 to 3 px runs on the upper-left edges only, keep the outline continuous. Crop `cairn_rim_speckle.png`.
5. Polish: the two floating pebbles over the right shoulder (all 588 drawings) are not in the identity table; they read as dust. Confirm with Matt or drop.
6. Polish: Old Growth splints read as small stools on the fists at 2x, and the root band in S 3 to 7 runs across both legs as one bar. Make the splints follow the forearm curve and band each leg separately.
7. Polish: idle height 85 to 87 px against the "about 90" target.

## Clack

1. **Clear fault: left arm over-stretched in the reload.** primary 10 reach 2.07 (the arm twice its length reaching the muzzle), primary 2 to 7 and powered_primary 1 to 6 reach 1.54 to 1.62, secondary 2 to 5 reach 1.7. Visible in E/W 9 to 11 as a long straight arm along the tube. Fix: tip the tube muzzle down toward the rack for the load (or load at the breech like the powered loader), and keep the fore grip within 12 px of the trigger grip.
2. **Clear fault: left arm drawn over the back in N.** primary N 1 to 10, secondary N 1 to 5, powered_primary N 1 to 6. Fix: cast-wide item 2. Crop `clack_N_arm_over_back.png`.
3. **Clear fault: harness straps drawn over the launcher in W.** Every W drawing: the tube on the far (right) shoulder is painted over the torso but under the X straps. Fix: in W draw the tube behind the torso and near shoulder (only the parts clearing the silhouette show), or above the straps if it is meant to be in front. Crop `clack_W_strap_over_tube_and_reload_reach.png`.
4. **Clear fault: the launcher reads backwards in E/W.** The rear bell is a closed dark dome (looks like a warhead) and the muzzle is a small yellow cap; Codex's launcher has a large open orange muzzle. Fix: draw the bell open (dark interior ellipse, flared rim) and the muzzle as an open ring the rocket nose sits in. Crop `clack_E_bell_reads_as_nose.png`.
5. **Clear fault: rocket count changes off-screen.** After primary the rack shows one rocket; idle shows two (refilled with no drawn action). Ruling: make the rack stateless: the reload draws from a closed ammo case behind the rack (as Morel's reagent case) so the visible rack always shows two; or runtime rule 7 with `idle_rack1/0` variants. Crop `clack_rack_continuity.png`.
6. Polish: in S the tube is end-on and reads as a club over the shoulder (known).
7. Polish: 6.5 px stance snaps at primary/secondary/special/powered_primary 1 and the return drawing.

## Iona

1. **Clear fault: the upright spear passes behind her head in E although it is in the near (right) hand.** idle, walk, special, guard rest, powered_idle, powered_walk, powered_exit, every E drawing with the spear upright: the head is painted over the shaft. In W (far hand) behind is correct. Fix: in E draw the shaft over the head, or hold the spear 3 px forward of the face so it does not cross the head (as W does). Crop `iona_E_spear_behind_head.png`.
2. **Clear fault: lunge step skates.** secondary E/W 1: the front foot moves 7.5 px and the back foot 6.5 px with both soles down. Fix: lift the front foot in drawing 1 and plant in 2.
3. Polish: S/N thrusts angle the spearhead down and sideways (known projection limit); at 2x the S thrust reads as a low sweep.
4. Polish: E is lit more weakly from the left than the other facings (light bias +0.4 against +2 to +3); check the coat shading on the far half in E.

## Mirra

1. Polish: primary and secondary read only as hand gestures at 2x; the water effects must carry them (separate scene effects, as the identity requires). Make sure the runtime spawns them at `palm_R` on the release drawing.
2. Polish: the gem above the right ear is not shown in N (visible ear side); add 2 px of gem at the head's right edge.
3. Polish: 6 to 6.5 px stance snaps (primary 8, powered_primary 6, guard W 1/6).

## Morel

1. Polish: in W the flask is hidden in the far hand at rest (idle, walk), so his key item is invisible facing west. Let 4 px of flask show below the apron.
2. Polish: guard and powered_guard 1 and 6: 6 px stance snaps.

## Mote

1. Polish: dodge S barely changes from idle (no lean toward the dodge); add a 2 px lean and hem lag.
2. Polish: primary W 3 to 4: the forming shard is hidden behind the head; the wind-up loses its glint facing west.

## Nix

1. Polish: E jacket rim speckle, 9 to 15 lone pixels per drawing (38 warnings).
2. Polish: idle height S 75, N 71, E/W 72: the hair spike is taller in S; trim 2 px or add it in N/E/W.
3. Polish: primary and powered_primary 1/7/9: 6 px stance snaps.

## Pendle (WIP snapshot)

1. Polish: the open cylinder in reload is about 5 px; at 2x the six-round reload reads only as fiddling (known).
2. Polish: special S 4 to 8 holds the rifle horizontally across the hips pointing to his left; a low-ready diagonal reads better facing the camera.

## Rook

1. **Clear fault: Thruster Vault does not settle.** secondary ends at drawing 7 crouched with the carbine aimed (51 to 58 % of pixels differ from idle 0), so the cut to idle pops. Fix: add a settle drawing (or make 7 the idle pose) within the existing duration. Crop `rook_secondary_end_vs_idle.png`.
2. Polish: special 5 to 6 fires a thruster puff while the helmet seats; not part of Orbital Rig in the identity table and it can read as a vault. Confirm or remove.
3. Polish: special W 2 to 4: the helmet travels hip to head entirely hidden behind the body (far hand), so it appears on the head without a visible move. Let it clear the head's back edge in drawing 4.
4. Polish: 6.4 px stance snaps at primary and powered_primary 1/9.

## Tam

1. **Clear fault: far arm drawn over the chest in W.** primary W 4 to 5 and powered_primary W 3: the right (far) arm's ochre sleeve lies across the near side of the chest. Fix: in W hide the far upper arm behind the torso until the forearm clears the chest front. Crops `tam_W_far_arm_over_chest_primary_powered.png`, `tam_W4_far_arm_over_chest_and_secondary_reach.png`.
2. **Clear fault: right arm over-stretched in Frost Ridge.** secondary 4 to 6 reach 1.56 (forearm visibly longer than the left in E/W). Fix: lower the hips and lean further (or place the palm 4 px nearer the feet).
3. **Clear fault: secondary stance snap of 7 to 8 px.** secondary E/W 3 and 7: both feet jump apart and back in one drawing. Fix as cast-wide item 3. Crop `tam_secondary_stance_snap.png`.
4. Polish: 6 to 7 px snaps in guard, powered_guard and primary 8.

## Velvet

1. **Clear fault: left arm drawn over the back in N.** primary N 5 to 6, powered_primary N 3 to 4: the sabre arm crosses the coat. Fix: cast-wide item 2. Crop `velvet_N_arm_over_back.png`.
2. Polish: primary 9: 7 px stance snap; guard 1/6: 6 px.
3. Polish: special W 5 to 7 and W idle: the lantern (far hand) is fully hidden; let its bottom show below the coat tail.

## Rulings on the known continuity issues

- **Brine's harpoon after primary versus idle:** a fault, not acceptable as is (blocker above). The harpoon is out until secondary reels it in, so the art needs unloaded variants and the runtime a `harpoon_out` state (rule 6).
- **Clack's rocket count after primary versus idle:** a fault (clear fault above). Prefer the art fix (stateless rack fed from a closed case); otherwise rule 7.
- **Bramble's bow after guard:** a fault in the current runtime (clear fault above). Rule 4 fixes it once guard 7 equals idle 0.

## Runtime rules the game must follow

1. **Speed:** move the body at the manifest `walk_speed` and `stair_speed` (Cairn 30 px/s, Pendle 50, others 57 to 68). Codex's fixed 92 px/s makes Cairn's feet slide at three times their stride.
2. **Facing:** pick the facing set (`<clip>_S/N/E/W`) from movement or aim; on a facing change mid-clip keep the drawing index (all facings share timing). Emit releases in the facing's direction from that facing's `release_anchor`, never `Vector2.RIGHT`.
3. **Projectiles and effects:** spawn on the release drawing at the named anchor; they are separate entities (Brine's tether from `muzzle`, Nix's decoy at `origin`, Rook's two turrets at the manifest `effects` offsets, Mote's orbit shards, Mirra's seals and currents). A carried item that becomes a projectile must not also be drawn in that drawing (fix Cairn first). Re-run `anim_<id>.py` after any export so `effects` survive.
4. **Guard:** clamp to drawing 4 while held; on release play 5 to 7, then idle. Never cut from 4 to idle.
5. **Powered state:** special always ends in powered_idle; while powered, use only powered_idle, powered_walk, powered_primary and powered_guard. Any other action (hit, dodge, jump, stairs, secondary, defeat) first plays powered_exit or, for hit and defeat, is allowed to drop the state with powered_exit's first drawings, until powered variants exist. powered_exit always returns to idle.
6. **Brine:** track `harpoon_out` from primary's release until secondary's drawing 6; while out, play the unloaded variants; if the tether ends without a reel, play secondary 5 to 8 before idle.
7. **Clack (only if the rack stays stateful):** track rack count 2/1/0 and choose the matching idle and walk variants; reload only from a non-empty rack.
8. **Jump:** select drawings by role from vertical velocity (0 load, 1 push, 2 rise, 3 apex, 4 fall, 5 land only after support, 6 absorb, 7 recover); the runtime lifts the sprite (no height is baked; Rook's vault likewise).
9. **Dodge and lunges:** drawn in place; the runtime supplies all translation once (Iona's lunge steps the feet but keeps the pivot).
10. **Stows and draws are atomic:** do not interrupt between a stow and its retrieve (Bramble secondary and guard bow, Pendle Longshot holster and rifle draw, Ashe's helm path, Rook's helmet path, Morel's mask path) except by hit or defeat, and then resolve to the state the hit clip shows; otherwise the item teleports.
11. **Cut to idle only after the last drawing** of a non-loop clip (every primary, secondary, special and exit ends on its rest pose, except Rook's secondary until fixed).
