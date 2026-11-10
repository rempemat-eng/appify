# Cast audit, round 2 (HEAD bdd06fe6)

I re-audited all fourteen characters at bdd06fe6 (23 clips each; Brine 31, Pendle 23 with reload and no powered_secondary) to the same standard as AUDIT.md, using the same scripts in `scratchpad/audit/`: metrics2.py, reach2.py (now including the generated powered tables), cont2.py and cont3.py (clip starts and ends), light.py and grid.py. I spent the detailed looks on the changed and new clips. New evidence crops are in `review/audit2/`. No source was edited.

## Counts (open after this round)

| Character  | Blocker | Clear fault | Polish |
| ---------- | ------- | ----------- | ------ |
| Ashe       | 0       | 0           | 1      |
| Bramble    | 0       | 0           | 0      |
| Brine      | 1       | 0           | 0      |
| Cairn      | 0       | 0           | 1      |
| Clack      | 0       | 1           | 0      |
| Iona       | 0       | 1           | 1      |
| Mirra      | 0       | 1           | 1      |
| Morel      | 0       | 0           | 0      |
| Mote       | 0       | 0           | 0      |
| Nix        | 0       | 0           | 1      |
| Pendle     | 0       | 0           | 0      |
| Rook       | 0       | 0           | 2      |
| Tam        | 0       | 2           | 0      |
| Velvet     | 0       | 0           | 1      |
| Whole cast | 0       | 1           | 1      |
| **Total**  | **1**   | **6**       | **9**  |

There are also five CONTRACT.md corrections (last section). The polish items from round 1 that are not listed here were not re-checked in detail.

## Blocker

1. **Brine: harpoon continuity, partly fixed.** idle, walk, guard and hit now have `_empty` variants, and so do their powered versions. Primary and powered_primary end matching idle_empty and powered_idle_empty; secondary and powered_secondary start empty and reload at drawing 6. Crop: `review/audit2/brine_harpoon_sets.png`. Still open:
   - jump, dodge, stair_up, stair_down, special and defeat (and their powered versions) have no empty variant, so a dodge or jump while the tether is out pops the harpoon back into the gun.
   - The designer's suggestion (NOTES: play secondary 5 to 8 first) delays a dodge by about 0.25 s, which is not acceptable for a defensive move.
   - Primary while the harpoon is out is not specified.

   **Fix:** export `jump_empty`, `dodge_empty`, `stair_up_empty`, `stair_down_empty` and `defeat_empty` (plus the powered versions) with `loaded=False`. Block primary while `harpoon_out`. Decide whether special clears the tether (play special_empty) or is blocked.

## Clear faults

1. **Whole cast, a regression at bdd06fe6: the `effects` blocks were dropped from the Rook, Nix and Mote manifests.** The last re-export rewrote the manifests and nobody re-ran `anim_<id>.py`. The turret, decoy and shard sprites are still in `out/<id>/fx/`, but the runtime has lost Rook's two turret offsets (-45,-8 and 36,14 at special drawing 5), Nix's decoy spawn data and Mote's shard data. **Fix:** run `python3 anim_rook.py`, `anim_nix.py` and `anim_mote.py` and commit. Better, have `export.py` call `write_effects()` itself so the blocks cannot be lost again.
2. **Clack: in N the reloading launcher is drawn over his back.** This is new with the tipped-tube reload: primary N 8 to 9 (and any powered reload that uses the same pose). The tube runs from the right shoulder down to the left hand at the front of the belt, so in a back view the muzzle half should be hidden by the torso. Instead the whole tube, muzzle included, is painted across the back. S is correct. **Fix:** in N give the tube's front half the far depth, so only the bell end above the right shoulder shows. Crop: `review/audit2/clack_N_reload_tube_over_back.png`.
3. **Tam: Frost Ridge palms no longer touch the ground.** The reach fix raised the release palms from 7 px to 17 px above the ground (secondary and powered_secondary, drawings 4 to 5, all facings), so the ridge appears to start from mid-air. **Fix:** kneel or drop the hips further (bend the knees, lean further) until the palms are within 2 px of the ground, keeping reach at or below 1.0. Crop: `review/audit2/tam_frost_ridge_palms_off_ground.png`.
4. **Tam: the powered variants start in the base pose.** powered_secondary, powered_guard, powered_hit and powered_primary drawing 0 have the base arms; powered_idle has the palms raised forward. Entering from powered_idle makes both arms jump (pixel change 19 to 47 points above the same base transition). **Fix:** apply `powered_from` easing at the start of the generated clips as well (drawing 0 equals powered_idle 0), not only at the end.
5. **Mirra: the same entry pop, but worse.** powered_primary, powered_secondary, powered_guard and powered_hit drawing 0 use the base narrow stance with the hands in; powered_idle is the wide, low, palms-out stance. Legs and hands snap on every powered action (+33 to +51 points). Same fix. Crop: `review/audit2/mirra_powered_entry_pop.png`.
6. **Iona: powered_primary rotates the spear 90° in one drawing.** powered_idle holds the spear upright; powered_primary drawing 0 already holds it horizontal. The base primary has a tilted in-between at drawing 0, but the powered table has none. **Fix:** start powered_primary with the base tilt drawing. Crop: `review/audit2/iona_powered_primary_entry_pop.png`.

## Polish

1. **Whole cast: attack drawing 0 is a ready pose, not the idle pose.** For example, Ashe's sword hangs down in idle and points forward in primary 0 and guard 0, and Iona's spear is upright in idle and horizontal in secondary 0. The weapon snaps on entry. This is acceptable for responsiveness. If wanted, add a 40 ms entry drawing taken from idle and take it out of the anticipation hold, so the timing is unchanged.
2. Ashe: special 3, the hair still spills around the descending helm (all facings). Better than before, but it still reads as larger than the helm.
3. Rook: powered_primary 0 raises the carbine away from powered_idle (+26 points). Same treatment as clear fault 4.
4. Rook: stair_down and powered_stair_down 4, left arm reach 1.12 (the designer noted it).
5. Nix: powered_primary 0 differs from powered_idle (+26 points). Same treatment.
6. Velvet: powered_guard 0 lowers the sabre from powered_idle (+26 points). Same treatment.
7. Iona: 194 lone-pixel warnings (round 1: 87). They are mostly storm sparks in the powered clips, which is intentional, but cap them at 8 isolated pixels per drawing.
8. Mirra: 191 lone-pixel warnings (round 1: 145), from the studs and trim.
9. Cairn: powered_primary lasts 0.94 s against the base 1.165 s and the contract table's 0.64 s. Record Cairn's figure in the table.

## Round-1 findings: status

All three blockers and 19 of the 20 clear faults are fixed. The one exception is Tam's Frost Ridge reach: it is fixed, but the fix broke the ground contact (now a clear fault above).

| Round-1 finding                                           | Status                                                                                                                                                                                          | Evidence                                 |
| --------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------- |
| Blocker: no powered hit, dodge, jump, stairs or secondary | **Fixed.** Every character has them (Pendle skips secondary by design via `POWERED_SKIP`). The powered state tags hold through every powered clip, and every powered clip ends on powered_idle. | 2x sheets of all 14 characters; cont2.py |
| Blocker: Brine's harpoon pops back in                     | **Partly fixed** (blocker above)                                                                                                                                                                | brine_harpoon_sets.png                   |
| Blocker: Cairn shows two rocks at the release             | **Fixed.** The release moved to drawing 7, where the rock is gone; the release anchor sits at the drawing-6 rock.                                                                               | metrics2 rock counts                     |
| Whole cast: arms over the back in N (`zarm`)              | **Fixed** (Ashe, Clack and Velvet checked)                                                                                                                                                      | grids                                    |
| Ashe: arm over the back in N                              | **Fixed**                                                                                                                                                                                       |                                          |
| Ashe: two-handed over-stretch                             | **Fixed.** The powered attacks are one-handed; reach is clean.                                                                                                                                  | reach2                                   |
| Bramble: bow pops after guard                             | **Fixed.** Guard 6 puts the bow back in the hand and guard 7 equals idle 0. Rule 4 is in the contract.                                                                                          |                                          |
| Brine: no grip on the gun in the special                  | **Fixed.** The left hand holds the gun in E and W.                                                                                                                                              |                                          |
| Cairn: rock reads as a second head                        | **Fixed.** It is now a turf-topped slab with roots.                                                                                                                                             |                                          |
| Cairn: feet skate 5 to 7 px                               | **Fixed.** No foot moves more than 3.3 px with both soles down anywhere in the cast.                                                                                                            | metrics2                                 |
| Cairn: rim speckle                                        | **Fixed** (0 lone-pixel warnings)                                                                                                                                                               |                                          |
| Clack: reload over-stretch                                | **Fixed** (reach clean), but see clear fault 2                                                                                                                                                  |                                          |
| Clack: arm over the back in N                             | **Fixed**                                                                                                                                                                                       |                                          |
| Clack: straps over the tube in W                          | **Fixed.** The tube is now drawn over the straps.                                                                                                                                               |                                          |
| Clack: launcher reads backwards                           | **Fixed.** Open flared bell; open orange muzzle.                                                                                                                                                |                                          |
| Clack: rocket count changes                               | **Fixed.** The rack always shows two; the reload comes from a closed case.                                                                                                                      | rack pixel counts are constant           |
| Iona: spear behind the head in E                          | **Fixed**                                                                                                                                                                                       |                                          |
| Iona: lunge skate                                         | **Fixed.** The back foot lifts.                                                                                                                                                                 |                                          |
| Rook: vault does not settle                               | **Fixed.** secondary 7 equals idle 0.                                                                                                                                                           |                                          |
| Tam: far arm over the chest in W                          | **Fixed**                                                                                                                                                                                       |                                          |
| Tam: Frost Ridge over-stretch                             | **Fixed, with a regression** (clear fault 3)                                                                                                                                                    |                                          |
| Tam: stance snap                                          | **Fixed**                                                                                                                                                                                       |                                          |
| Velvet: arm over the back in N                            | **Fixed**                                                                                                                                                                                       |                                          |
| Cast-wide polish: jump 7 and dodge 7 differ from idle     | **Fixed for all 14** (no difference above 11 %)                                                                                                                                                 | cont2                                    |

Cast-wide checks that pass at bdd06fe6:

- **Checks:** 0 checks.py errors.
- **Arm reach:** clean in every table, including the powered ones (one 1.12, noted above).
- **Clip shape:** every jump has 8 drawings with roles, every guard has 8 drawings and holds at 4, and every dodge lasts 0.495 s. Primary and powered_primary keep 0.64 s with the release at 0.33 s (Cairn at its own timing).
- **Light:** comes from the upper left in every facing (Iona's E improved from +0.4 to +1.0).
- **One-sided gear:** still on the correct side.

## CONTRACT.md runtime rules: corrections needed

1. **Rule 6 (Brine) is incomplete.** Add: primary is blocked while `harpoon_out`. jump, dodge, stairs and defeat use their `_empty` variants once exported (blocker above). Until then the runtime plays the loaded clip, which is a visible pop, and must not delay a dodge. State what special does while the harpoon is out. Also adopt the designer's wording: the flag is set at the primary or powered_primary release and cleared at secondary or powered_secondary drawing 6.
2. **Rule 7 (Clack) is obsolete.** The rack is stateless now (always two). Delete the rule, or say "no rack state; the reload draws from the closed case".
3. **Rule 11 is out of date.** jump 7 and dodge 7 now equal idle 0 for all 14 characters, and powered_jump 7 and powered_dodge 7 equal powered_idle 0. Replace "Bramble, Iona, Pendle and Cairn; the others as they are fixed" with "all characters".
4. **Rule 5 leaves two cases open.** Defeat while powered: say "play powered_exit 0 to 3, then defeat" or "defeat drops the gear in its first drawing (accepted pop)". Special while already powered: blocked. Also add: generated powered clips start on powered_idle 0 (clear faults 4 to 6).
5. **Rule 3 and the clip table.**
   - Rule 3 assumes an `effects` block that bdd06fe6 removed (clear fault 1). Make the exporter write it.
   - The table says Cairn's hit is 4 drawings; it is now 8 drawings at 0.455 s, so update the table.
   - Record Cairn's powered_primary at 0.94 s.
