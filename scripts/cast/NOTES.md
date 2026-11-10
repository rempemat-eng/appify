## Designer 3 (Nix, Rook, Mote), 25 Oct

Files: src/nix.py, src/rook.py, src/mote.py; review/nix_sheet.png, review/rook_sheet.png, review/mote_sheet.png (4x: Codex east idle, then S N E W, plus a 2x strip), review/designer3_lineup.png (Bramble, Iona, Nix, Rook, Mote in S N E W at 4x, guide lines at 48, 74 and 90 px). The sheet and lineup scripts live outside the repo (scratchpad/d3/sheet.py, lineup3.py); preview.py renders 5x, so I did not use it for the 4x sheets.

For the lead to consider adopting in the shared rig:

- **Lit pixels that can be hidden.** `f.detail` always draws on top, so a glow on a far limb shows through the torso. Nix uses a local `_glow(f, mask, z, k)`: a flat, unoutlined, never-dimmed part at a z just above its housing, so nearer parts still cover it. Worth a shared `f.glow()`.
- **Gold edging inside a mask.** Mote's `trim(mask)` (the mask minus its 4-neighbour erosion) gives a 1 px inner border for coat edges and hems without touching the outline. Useful for any trimmed garment (Velvet, Mirra).
- **Broken hems.** `_hem_pts(x0, x1, y, n, depth, phase)` returns alternating deep and shallow points for a fragmented or pointed hem.
- **Foreshortened side ornaments.** Mote's shoulder hooks take `kx` to squash their outward curl in profile, where "outward" points at or away from the camera. The same applies to any sideways-curling ornament.
- **`parts.limb` length check.** If `l1 + l2` is longer than the hip-to-foot distance, a standing leg bends (Nix first had crooked knees). For a straight idle leg, keep `l1 + l2` at about the pivot distance (15.5 px for hip -22 to ankle -6.5). A helper that warns about this, or one that picks the lengths, would help.
- **Back-view depth.** From behind, a backpack sits nearer than the head, so it needs a z above the hair (Rook N uses 46 to 47.5). Easy to miss with the usual draw order.

Logic decisions:

- Nix: the laser arm is anatomical left in every view (S viewer right, N viewer left, E far arm, W near arm). The grey streak is at the left temple. It is hidden in E, which shows his right side, and visible in S, N and W. The fringe differs per profile: the long swept side shows in E, the short side and temple in W.
- Rook: the helmet clips to the right hip: S viewer left, N viewer right, E near, W far (it shows behind the seat). The carbine is held at low ready, grip in the right hand and fore-end in the left: E near hand on the grip, W near hand on the fore-end. In N the stock and muzzle show past each hip. The twin tanks show above both shoulders in S. In E and W the far tank sits 2 px higher. Both nozzles are attached at the bottom in N, with no disc or tether.
- Mote: symmetric, except that the core shows on the front only. The glass is the core lens plus one inlay in each outer hem fragment. Eyes are dark bars with an amber iris top, with no mouth and no brows.

Known shortfalls: Rook's S pose is busy around the hands. The front-view carbine is drawn as a diagonal across the hips, which reads better than a true foreshortened muzzle. The S and E views agree on the low-ready pose. Mote's side profile is soft: a 1 px nose bump and a long jaw. Nix's natural right hand is a mitten. Only the idles are drawn. Nothing has been tested in the engine.

## Designer 1 (Morel, Velvet, Tam, Mirra), 25 Oct

Files: src/morel.py, src/velvet.py, src/tam.py, src/mirra.py; review/<id>\_sheet.png (Codex east idle, then our S N E W, 4x) and review/designer1_lineup.png (Bramble, Iona and my four, S N E W, 4x, faint 10 px rules with the 74 px line marked). Same draw(facing, P) signature as iona.py; every module has a P0() whose hand, foot and item keys a pose can override.

Proposed for the shared rig (each is a local helper now):

- `open_hand(f, x, y, z, view, dim, s)` in tam.py and mirra.py: an open hand from the wrist pivot, fingers together, thumb apart, one finger seam. Needed for Tam's palms and Mirra's gestures, probably Mote too. Worth one shared version in parts.py.
- Grip hands: a fist with a 2x1 deep-tone finger crease over the held neck or handle (morel.hand, velvet.hand). The held item is drawn under the hand so it shows above and below the fist. Suggest `parts.fist(..., grip=True)`.
- `trim(f, mask)` in mirra.py: gold detail on the bottom row of a cloth mask (np.roll edge). Cheap, clean piping for shawls, hems and lapels.
- Cuffs placed along the forearm from the elbow returned by `limb()` (velvet.coat_sleeve, tam.arm). `limb()` could return the elbow and the unit forearm vector so cuffs, wraps and bands sit right in any pose.
- Pivoted items: velvet.sabre(gx, gy, ang) with sabre_guard() drawn over the fist, lantern(gx, gy) hung from a ring through the fist, scabbard(x, y, ang); morel.flask(gx, gy). The grip point is the pivot, so they will follow the hand in the animation contract.
- Palette: I registered new ramps inside my modules (skin_v, skin_m, silver, silver_t, navy, trouser_v, iron, lamp, scab, apron, rubber, lens, reagent, amberliq, glass, copper, cork, greyhair, wrap, wrap_l, crimson, bead, shoe, ivory, turq, jewel). palette.skin_d is too light for Codex's Velvet and Mirra, so the two darker skin ramps (skin_v, skin_m) and the silver hair ramps should probably move to palette.py. Dark-skin blush is a fixed #8A4036 / #8E4636 detail, not the pink 'blush' ramp.
- preview.py renders at a fixed 5x. The 4x sheets came from a scratch script. A zoom argument on preview.py would help.

Logic choices to confirm:

- Velvet is left-handed: the sabre is in her LEFT hand and the lantern in her RIGHT, as in Codex's frames, so the scabbard hangs on the RIGHT hip (cross-draw).
- Morel's one mask hangs on his chest from a strap round the neck; the back view shows the strap at the nape. Codex's idle has dark goggles on his face. I left them out so that there is only one mask, worn only in the special. The catalyst apparatus (brass chamber, glass bulb, copper coil) is clipped at the left hip and hidden by the body in E. His right hand holds the blue flask in every view (far hand, ahead of the body, in W).
- Tam's bead cord is one closed loop round the neck, with a guru bead and tassel. The cream band runs from the right shoulder to the left hip, and the weighted sash knot sits at the left hip.
- Mirra: the gem is above the right ear (as in Codex), there is a gold hoop in each ear, and the wrap tail and the long end of the shawl fall down the back on her left. In S and E they are mostly hidden by the body, which is correct but means they barely read there.

Known shortfalls: closed hands are still mitten-sized. Tam's hair is neater and less fluffy than Codex's. Mirra's trousers balloon less than Codex's. No walk or other motion has been tested.

## Designer 2 (Brine, Ashe, Clack), 25 Oct

Files: src/brine.py, src/ashe.py, src/clack.py; review/brine_sheet.png, review/ashe_sheet.png, review/clack_sheet.png (Codex east idle, then our S N E W, 4x, with a 2x strip) and review/designer2_lineup.png (Bramble, Iona, Brine, Ashe, Clack, S N E W, 4x, 74 px line marked, plus a 2x strip on dark ground). draw(facing, P) uses anim.CELL and anim.PIVOT. Heights: Brine 73 (helmet top valve included), Ashe 75, Clack 74, widths 41 to 47 px in S.

Proposed for the shared rig:

- `tagged(f, tag, fn, *args)` (local in all three modules): runs a gear builder and stamps the tag on every part and detail it adds. Simpler than passing tag= through every f.add; worth a copy in ew.Fig.
- Details ignore depth: f.dot and f.detail always land on top. A detail on an item that can be hidden (sword fuller, helm visor bars, couter rivets under a cape) shows through whatever covers it. I made those marks parts (flat tone, line=None, clean=False). A z on details, or a "detail clipped to its part's visible pixels" option, would remove the trap.
- `arm_folded(sh, el, hand)` in clack.py: an explicit elbow for a hand raised near its own shoulder (shoulder-carried launcher). parts.limb folds sideways when the hand is closer to the shoulder than about 4 px, so the forearm swung out horizontally.
- `bez(pts)` + `hose()` in brine.py: a corrugated tube along a quadratic or cubic bezier, rings every 3 px. Reusable for any cable or tube that must stay attached at both ends.
- `harpoon_gun(gx, gy, ang, fs)`: fs foreshortens a long item along its axis, so a gun turned partly toward the camera stays one drawing.
- New ramps registered locally: brine_copper, brine_glass, brine_olive, brine_rubber, brine_canvas, ashe_steel (navy steel), ashe_crimson, ashe_hair, ashe_blade, clack_teal, clack_work, clack_orange, clack_web, clack_skin, clack_grey, clack_lens, clack_boot. clack_skin (tan) and the crimson may be worth moving to palette.py.

Logic choices to confirm:

- Brine: the one hose leaves the pack's top right valve and enters the regulator on the helmet's right rear (S viewer left, N viewer right, E visible behind the dome, W hidden behind the dome, tag 'regulator' absent in W by occlusion). The reel sits on the gun's right side, so it faces us in E and in the S low-ready pose, and is behind the gun (dimmed) in W. The tether is one 1 px line from the reel to the harpoon's eye. In S the gun is at low ready, turned a little to his left, so its length and the reel read; E and W hold it level. In N only the stock shows past the right hip.
- Ashe: the one helm is carried under the LEFT arm, the hand cupping its chin, the visor forward (S viewer right, N partly past the cape on viewer left, W near at the back hip, E behind the body with a sliver showing). The sword is in the RIGHT hand, point down (W: far hand, blade showing ahead of the body). Nothing on the head. Brass edges use the 'gold' ramp to match Codex's bright trim.
- Clack: the launcher rides the RIGHT shoulder. The exhaust bell is at the rear, with nothing behind it (the pressure chamber is clamped under the tube ahead of the bell, and the rack is at the front of the belt). Two grips are under the tube ahead of the shoulder: the right hand on the trigger grip, the fore grip free at rest. The spare-rocket rack (two rockets) is on the front LEFT of the belt (S viewer right, E far, W near, N hidden). The left fist rests on the left hip. Codex's sunglasses became work goggles pushed up on the forehead, so the eyes read. In E the tube crosses below his moustache, which is correct for a near-shoulder launcher.

Known shortfalls: these are per-facing builds (pass-1 structure, like iona.py), not yet on parts.Rig; porting them is the next step before animation. Brine's helmet in profile reads as three-quarter (the side port is the "face"). Ashe's helm in S still sits close to the arm in value; the crimson crest is what separates it. Clack's raised forearm in E is a plain skin bar. Hands are mittens or fists. Only idles; nothing tested in the engine.

## Lead (Bramble, Iona, Pendle, Cairn; shared files), 25 Oct

Housekeeping: my "Cairn pass 2" commit (f9a4e00) swept in uncommitted edits to src/clack.py and src/nix.py by mistake (`git add -A src`). The content is yours and unchanged; only the commit message is wrong. I now add files by name. I also untracked `src/__pycache__` and added a `.gitignore`.

### Adoption decisions on your requests

- **Depth for details (designers 2 and 3).** Adopted: `f.detail(..., z=)` and `f.dot(..., z=)`. With z, the pixels only show where no part nearer than z covers them. Without z it behaves as before. Nix's `_glow` and the flat parts you used still work; switch when convenient.
- **Tag a whole gear builder (designer 2).** Adopted as `with f.tagging('bow'): ...`, which stamps the tag on every part and detail added inside. Your local `tagged()` still works: render now accepts detail tuples of 3, 4 or 5 items.
- **Grip fists (designer 1).** Adopted as `parts.fist(f, x, y, z, mat='skin', r=3.4, dim=0, grip=(ux, uy))`. Draw the held item under the fist; the crease is a depth-aware detail.
- **Trim (designers 1 and 3).** Adopted as `parts.trim(mask)`, the mask minus its 4-neighbour erosion. Mote's hem helper and Mirra's bottom-row trim stay local.
- **Elbows, folded arms, limb lengths (designers 2 and 3).** Replaced by the 3D rig: `parts.Rig.limb(a3, b3, l1, l2, r0, r1, r2, pole)` solves the joint in 3D toward a pole, so a hand near its shoulder folds the right way in every facing. It returns the joint, so cuffs and bands can sit along the forearm. For a straight standing leg, keep `l1 + l2` about equal to the hip-to-ankle distance (Bramble: 8.7 + 8.5 for 15.5 plus the stance).
- **Back-view depth (designer 3).** The rig gives every point a depth per facing (`Rig.d`), so back gear, held items and raised hands get their z from where they are rather than from a fixed draw order (see the quiver, the slung bow and `Rig.zarm` in bramble.py).
- **Shared ramps (designers 1 and 2).** Not moved yet. Ramps registered in your own module are fine: checks.py imports your module, so the palette check knows them. Two characters must not register different colours under the same name.
- **preview zoom.** `python3 look.py <module> SNEW <zoom> "<pose overrides>"` renders any pose at any zoom, and `sheet.py <id> <clip>` shows one clip in all facings.
- **Bezier hoses, harpoon foreshortening, pivoted items.** Keep these local. They already take a grip point, so they will follow `hand_R` and `hand_L` when the character is ported to the rig.

### For everyone: porting to the animation contract

Read CONTRACT.md. To animate a character it has to be pose-driven, as bramble.py, pendle.py and cairn.py are: `P0()`, `build(f, facing, P)` with `parts.Rig`, hands and feet in body space `(fwd, up, lat)`, `f.anchor()` for hands and weapon points, and tags for gear. Then write `anim_<id>.py` (copy anim_bramble.py), run `python3 export.py <id>` and `python3 checks.py <id>`, and look at `review/<id>/*.png`. Your current per-facing modules are not pose-driven yet, so none of the ten can be exported until they are ported.

### Status (lead)

Done:

- Pendle and Cairn are redrawn and pose-driven.
- Bramble is rebuilt on the rig with all 17 clips in S, N, E and W (600 drawings), exported to out/bramble/ with manifest.json and frames.tres.
- CONTRACT.md, anim.py, checks.py, lineup and media are written.

Not done:

- Iona has not been ported to the rig. She is still pass 1 and idle only.
- Pendle and Cairn have no animation tables yet.

### Lead, where I stopped (25 Oct)

- **Bramble** is fully animated (17 clips x 4 facings, 600 drawings). Checks: 0 errors, 9 lone-pixel warnings (briar beads, the string over the cape in N).
- **Pendle and Cairn** have idle and walk exported in four facings (out/pendle, out/cairn; checks 0 errors). Cairn's 12 to 16 lone-pixel warnings are 1 px diagonal steps on the moss and shoulder lines, not fill speckle.
- **Next:**
  - Pendle's revolver, fan fire, Longshot and reload.
  - Cairn's slam, boulder throw and Old Growth.
  - Port Iona to the rig.
  - The designers' ten port to the rig, then copy anim_bramble.py.
- **Review files:**
  - review/lineup_all.png;
  - review/bramble_clips.png (E) and bramble_clips_S.png;
  - review/bramble/<clip>\_<F>.png, plus the same folders for pendle and cairn;
  - review/bramble_actions.mp4 and bramble_facings.mp4 (1920x1080, 60 fps);
  - review/bramble_scene.png.

## Designer 1 (Morel, Velvet, Tam, Mirra), pass 2: rig port and animation, 25 Oct

All four are pose-driven on parts.Rig and exported with the contract exporter: out/<id>/ (17 clips x S N E W, manifest.json, frames.tres). checks.py: 0 errors for all four (Morel 596 drawings, Velvet 568, Tam 572, Mirra 572). Warnings are lone pixels only, 9 to 18 per frame at most against the allowance of 8 (gold studs, bead and trim dots; Mirra has the most, from the wrist-band studs and shawl trim). Review: review/<id>/<clip>_<F>.png, review/<id>\_actions.mp4 (each clip once, E), review/designer1_facings.png (idle, primary release, secondary release, special release, powered idle, S N E W per character). Files: src/morel.py, velvet.py, tam.py, mirra.py and src/anim_<id>.py. The video and facings scripts live outside the repo (scratchpad/d1/vid.py; it reuses media.py by swapping its OD/MAN globals).

How the port works: `morel.Shift(f, dx, dy)` moves the Fig origin (gx, gy, X, Y, flip-aware) so the pass-1 torso and head art lands at the projected hip or head of the pose; legs and arms are R.limb, hands are a shared `fist` (finger crease across the grip direction) and `open_hand` (palm and fingers along a body-space direction, thumb apart, foreshortened by the projection). anim_morel.py has generic clips (g_idle, g_walk, g_stairs, g_hit, g_defeat, g_jump, g_dodge) that take the rest hands and a gear-state base; the other three import them.

**Requests for the lead (shared rig):** please consider adopting `Shift` (ew.Fig, e.g. `f.shifted(dx, dy)`) and `open_hand`/`fist` from morel.py into parts.py; they let a pass-1 module become pose-driven without rewriting its art. `parts.fist`, listed as adopted in the lead notes, is not in parts.py yet.

Logic decisions:

- **Morel.** The flask is in the RIGHT hand in every facing (S viewer left, N viewer right, E near, W far and hidden by the body, so the W check exempts it at rest). Primary: one throwing hand (right), the left hand fixed at the same place throughout; the flask is held by the neck through the wind-up, the release drawing has an open, empty hand (anchor `flask` at the fingers), then the right hand takes the next flask from a **closed reagent case on the right hip** (new small item, lid and clasp, nothing inside shows, so exactly one flask is ever in sight). Vials: blue on the right front of the belt, amber on the left front, in every facing (E shows the blue, W the amber). Catalyst: left hip; the secondary lifts it on its strap with the LEFT hand, points the bulb, flares it (amber) at the release and clips it back; the strap from the belt clip stays drawn. Mask: one mask; chest (strap at the nape from behind) -> left hand -> face in the special (worn through every powered clip, strap round the head) -> back to the chest in powered_exit. Never two.
- **Velvet.** Sabre in the LEFT hand and lantern in the RIGHT in all 600 drawings; nothing is sheathed. Primary: high-left to low-right diagonal cut, lantern drawn back at the right hip. Secondary (flare): the lantern is thrust forward and its shutter opens (lamp 2, white-hot) at the release, then closes; the sabre holds guard. Special: the lantern is raised forward and its shutter opened for good (lamp 3), sabre to en garde; powered clips keep lamp 3 and both items; powered_exit closes the shutter and lowers both, stowing nothing. Defeat lays the sabre flat beside her and stands the lantern on the ground still in her hand.
- **Tam (redesigned at Matt's request, 10:29): male monk in orange.** References, in words: Theravada robes (lower wrap; upper robe wrapped to leave the right shoulder bare, draped over the left shoulder with its end thrown down the back; cloth belt; long diagonal folds from the left shoulder to the right hip) and Shaolin dress (cross-collared jacket, left over right; wide trousers bound with shin wraps; flat dark cloth shoes; knotted sash). Tam now: ochre cross-collared under-robe and trousers, saffron outer robe over the LEFT shoulder wrapped diagonally to the right hip and to the knee, its end down the back on the left; burnt-orange sash knotted at the left hip with the two weighted ends; cool grey-blue hand and shin wraps; a dark-wood mala with an ice-blue guru bead and tassel; close-cropped grey hair, heavy grey brows, broad jaw; 73 px. The left sleeve is saffron (robe over the arm), the right ochre. Primary: right open-palm strike (fingers up, heel forward) from a hip chamber; secondary (frost ridge): both palms pressed to the ground ahead; special Glacier Form: ice grows on the same forearms (elbow to wrist, palms bare) and shins (ankle to knee), held in every powered clip, cleared in powered_exit. Hands are open in every drawing.
- **Mirra.** Hands open in every drawing; no water is drawn in the body sheets. Primary: gather at the right hip, circle up, fling forward with the palms (release at full reach, anchor `palm_R`). Secondary: palms raised, then pressed forward and down toward the seal's place. Special: arms open and rise palms up, then settle into the powered stance (wide, low, palms turned out, as in Codex's powered idle). Gem above the right ear, hoops in both ears, wrist bands on the forearms, wrap tail and shawl end down the back on her LEFT: attached to the same places by the rig in every drawing.

Known shortfalls: hands are small at this scale (an open palm is about 5 x 3 px); Morel's held flask is hidden by the body in W (the far hand), which is correct occlusion but means W never shows it at rest; Velvet's raised lantern in the special is held forward at face height rather than overhead (overhead hid the face); Mirra's trousers balloon less than pass 1; the walk cycles use the shared gait at A = 9 to 9.5 (walk_speed in each manifest). Nothing has been tested in the Godot runtime.

## Designer 3 (Nix, Rook, Mote): ported to parts.Rig and animated, 25 Oct

All three are pose-driven (P0 + build on parts.Rig) with all 17 contract clips in S, N, E, W, exported with anim.export (out/<id>/ PNGs, manifest.json, frames.tres). checks.py: nix 0 errors (38 lone-pixel warnings, 9 to 15 px of rim speckle on the jacket in E, same as the approved static), rook 0 errors, mote 0 errors.

How: the approved static torso, pack, coat and head drawings ride the projected hip / shoulder / head through `nix.Sh` (a coordinate shift with a lean shear that also wraps tonemaps), so the rest pose matches the approved art; limbs, gear and hands are solved per pose with Rig.limb. `nix.skel` and `nix.legs` and the generic clips in anim_nix.py (idle, walk, stairs, hit, defeat, jump, dodge) are shared by my three.

Logic choices (identity table):

- Nix: the laser arm is anatomical LEFT in every drawing (tag 'laser'; far arm in E, near in W). The primary beam leaves the lens at the end of the left forearm (anchor 'muzzle'). Matt's 10:29 flag: the RIGHT arm is natural in every facing and frame: teal sleeve, a visible black wrist wrap, skin hand, no metal or glow. Afterimage (secondary, release 3) leaves ONE stationary decoy: separate sprite out/nix/fx/afterimage\_<F>.png at the 'origin' anchor (foot pivot), never in the body sheet. Limit Release (special, release 4) opens the SAME left forearm casing (plates lift off a lit core, casing=1) and every powered clip keeps it open; powered_exit closes it.
- Rook: one carbine (right hand on the grip, left hand solved onto the fore-end), one helmet. Matt's 10:29 flag: the hip helmet is now head-size (r 7.6) with a padded rim, a big dark faceplate with a glint, a dark neck ring and a clip strap from the belt; it hangs at the RIGHT back hip with the faceplate turned out (S viewer left, N viewer right, E near at the back hip, W far and dimmed). Orbital Rig (special) moves that same helmet hip -> hand -> head (worn helmet: open faceplate so the face reads, as Codex's powered state wears it); every powered clip wears it; powered*exit returns it to the hip clip. Thruster Vault (secondary, 8 drawings, release 3) fires only from the two attached nozzle bells (tag 'exhaust', anchors nozzle_R/nozzle_L); legs hang straight in the air drawings so the ground rule holds; the runtime lifts the sprite (no baked height). Orbital Rig's two turrets are separate sprites out/rook/fx/turret*<F>.png (Codex offsets in manifest 'effects'). No disc, no tether.
- Mote: one construction: hem fragments only lag, glass inlays stay in them, the chest core is the same core. Aphelion (special, release 4) parts the coat fronts and lights the SAME core (aphelion=1, kept through powered clips; powered*exit closes it). The primary's glass shard forms in the right hand and leaves at the release. The three orbiting shards are separate sprites out/mote/fx/shard*<n>.png.

Effect sprites: `python3 anim_<id>.py` writes out/<id>/fx/ and an 'effects' block into the manifest. export.py rewrites the manifest, so run anim\_<id>.py after any export.

Requests to the lead (shared files, not edited):

- checks.py: allow per-facing equipment rules (e.g. Mote's glass is legitimately hidden behind the head facing W during the wind-up; I narrowed the required drawings instead) and per-character ground overrides for traversal clips (Rook's vault would read better with tucked legs; I kept legs straight to satisfy 'exact').
- Consider moving Sh (shift-with-shear proxy, tagging/anchor passthrough) into parts.py: it lets any per-facing static drawing ride the rig unchanged.
- export.py could call an optional `A.write_effects()` after export so fx sprites and the manifest 'effects' block survive re-exports.

Review: review/nix*actions.mp4, rook_actions.mp4, mote_actions.mp4 (each clip once, E, with the fx sprites placed where the runtime spawns them), review/designer3_facings.png (idle and powered idle, SNEW), review/<id>/<clip>*<F>.png contact sheets.
Known limits: in S, Rook's carbine aimed straight at the camera foreshortens to a short block; Mote's Aphelion rim in profile sits just ahead of the coat; hands are mittens or gloves. Nothing tested in Godot.

## Lead, 25 Oct (afternoon): Iona, Pendle, Cairn animated; shared changes; Bramble in Godot

Shared changes (all backward compatible; Bramble re-exported to a temporary folder is byte-identical, 600/600 frames, checks 0 errors):

- `parts.Rig.limb` records each limb's reach ratio in `f.reach` (distance / (l1 + l2)). Over 1.04 means the limb stretches. `scratchpad/lead/reach.py <id>` lists every drawing over that; use it before exporting.
- `checks.py`: `may_hide` now also applies to per-clip equipment rules (`dict(clips={...}, may_hide={'N'})`), for items that the body legitimately hides from one side.
- `palette.py`: new `storm` ramp (Iona); `rifle` is now a lighter walnut so a stock reads against a brown coat (Pendle's rifle and revolver grip).
- Pattern worth copying: author a two-handed weapon by its two grip points (`two(hR, hL)` in anim_iona.py, `rpose(hR, hL)` in anim_pendle.py): the weapon lies on the line through both hands, so the grips can never leave the shaft. Keep the off hand within reach: with 74 px figures a fore grip more than about 12 px ahead of the rear hand over-reaches unless the shoulders turn (`twist`).

Iona (src/iona.py, anim_iona.py): ported to the rig, all 17 clips x 4 facings, checks 0 errors. One 92 px spear: the right hand holds it at `sps` from the butt (or `lift` puts the butt that far above the ground), the left grips the same shaft at `gripL`. Strike and storm-lance lunge are along the facing (body space fwd), so the runtime's lunge movement and the thrust agree; the lunge also shifts the hips forward (hipx). Guard keeps the same spear diagonally across the body. Stormcall puts a storm rim and sparks on the same blade (storm 0..1); lightning bolts are finite details. Harness (right shoulder to left hip, crossing on the back with a gold ring) and the one braid are tagged. Idle height band (88, 100) includes the upright spear.

Pendle (pendle.py, anim_pendle.py): all 18 clips, checks 0 errors. The holster is empty whenever the revolver is in his hand. Primary: draw, aim, fire (flash), recoil, holster. Fan fire: gun at the buckle, left palm fans, three shots. Longshot: hand pushes the revolver home, left hand takes the rifle by the barrel over the left shoulder, swings it round (`rifle='pull'`, rt 0..1, one rifle interpolated between sling and hands), right hand takes the wrist; powered clips keep it in both hands (low ready, shouldered fire with a lever cycle, a bar guard); powered_exit slings it back. Reload: draw, cylinder swings out and down on the crane, muzzle up to eject six cases, two loads of three from the belt, flick closed, holster. Rifle length is now fixed (40 px) in every state.

Cairn (cairn.py, anim_cairn.py): Matt's 10:29 note applied first: shoulders narrower (SHW 20.5, shoulder boulders 12 x 11.2), upper arms (9.8 x 10.6), forearms and fists (12.6 x 13) bigger. Profile widened to 59 (E) and 63 (W) px with a brawler's stance (right fist forward, left back, shoulders turned), a hunched back boulder and the head further forward; the sprout sits toward the back of the left shoulder so it no longer reads as on the near shoulder in E. Slam, boulder throw (one rock, torn from the ground, carried between the fists, gone after the release drawing) and Old Growth (wooden splints and root bands grown along the same forearms and legs, leaves from the shoulder turf) and all other clips.

Godot: draft PR https://github.com/rempemat-eng/appify/pull/249 (branch claude-a/cast-in-game): `game/tools/import_cast.py` imports `out/<id>/`; Bramble is the player (facing from movement or aim; idle, walk, bow shot on left click with the arrow spawned on the release frame at arrow_tip, dodge, hit, defeat; walk speed from the manifest). Media: scratchpad/lead/bramble_game_1080.png and bramble_game.mp4.

Open: the ten designers' characters; Iona's thrust toward the camera (S) is short by projection (K = 0.35), so S/N thrusts angle the spear inward to read; Pendle's open cylinder is about 5 px across, legible at 4x but small at 2x.

## Designer 2 (Brine, Ashe, Clack): ported to the rig and animated, 25 Oct

All three are pose-driven on `parts.Rig` (`P0()`, `build(f, facing, P)`, `draw()` with `gy = anim.FIG_GY`), with `src/anim_<id>.py` tables for all 17 contract clips, exported with `export.py` to `out/<id>/` (PNG per drawing, manifest.json, frames.tres; 4 facings) and checked with `checks.py`. Review: `review/<id>/<clip>_<F>.png` (contact sheets), `review/<id>_actions.mp4` (each clip once, E facing, 1080p, manifest timings), `review/designer2_facings.png` (idle #0, primary release and powered_idle #0 in S N E W). Clack keeps the goggles pushed up.

Logic as built (Codex's identity table):

- **Brine.** One hose in every drawing: a corrugated bezier from the pack's top-right valve, out past the right shoulder and into the regulator on the helmet's right rear, both ends computed from the torso and head each frame. The gun is placed by grip point and barrel direction in 3D; the left hand follows the fore grip or the reel handle, so it never floats. `muzzle` is an anchor in every drawing (plus `harpoon_tip` while loaded). Primary: stock to the shoulder, release at drawing 7, the harpoon leaves the muzzle and stays out to the end of the clip; the tether is NOT in the body sheets. Secondary (reel): the left glove cranks the reel on the gun's right side, braced backward, release 4 is the tether snapping taut, the harpoon is back in the muzzle from drawing 6. Special "Pressure Brace" (my naming): the right hand leaves the grip (the left holds the gun by the fore grip), turns the regulator valve, the faceplate and port glass light (`brine_glow`), braced stance; powered clips keep the glow and stance; powered_exit closes the valve. Guard: the gun held across the chest as a bar.
- **Ashe.** One sword, always in the RIGHT hand. One helm with ONE size (fits over the head, 18 px): `helm_t` moves it along one 3D path from under the left arm (0) past the left shoulder to the head (1); it leaves the hand only on the head, and on the head the hair and face are inside it. Cinderhelm release (drawing 4) is the helm seating; from there `ember=1` draws the same plates' brass trim in `ashe_ember` plus seam lines on the breastplate (same armour). Powered clips keep the helm on; the free left hand joins the grip in powered_primary and powered_guard; powered_exit lifts the helm off and back under the arm while the seams cool. Primary: overhead cut, contact at 6; secondary: thrust, full reach at 4.
- **Clack.** The launcher is placed by tube centre and direction in 3D; trigger grip (right hand, every drawing) and fore grip (left hand when aiming) are under the tube; the pressure chamber is clamped under it behind the shoulder; the rack is on the front left of the belt. The bell's backblast (tag `fx`, two drawings) is drawn behind the bell, clear of his head and back. Primary: brace, aim, launch at 6 (the rocket nose leaves), recoil back into the shoulder, then the reload: the left hand takes a rocket from the rack (it shows one rocket from then on) and feeds it into the muzzle. Secondary "pressure vent": the left hand twists the chamber valve, a puff at the muzzle (the loaded rocket stays). Special "Loader Brace": the loader frame that is carried flat on his back (new small part, on the back between the X straps) unfolds: the loader arm rises over the right shoulder to the breech with the next rocket, and the brace strut props the tube's rear; it stays attached in every powered clip (he walks with it), and powered_primary has no hand reload because the loader feeds the breech. powered_exit folds it flat again.

Notes for the lead / runtime:

- Brine: after primary the harpoon is out (no harpoon in the muzzle) until secondary reels it in; idle shows it loaded. The runtime should keep the gun in the fired state (or play secondary) rather than pop back to idle while the tether entity exists; the tether is a scene line from the frame's `muzzle` anchor.
- Clack: after primary the rack shows one rocket; idle shows two (refilled off-screen). Same pop risk as above if the runtime cares.
- Brine's and Clack's special names are mine; Codex gives only "braced rig" and "loader and brace".
- Pack in S is hidden behind the body (EQUIP may_hide S); the regulator is hidden by the dome in W; Ashe's helm is behind her in E (far side) and her sword can be hidden by the body in N and W; Clack's chamber is end-on or behind in some facings (not required).
- Remaining lone-pixel warnings are 1 px diagonal steps (blade edges, the hose rings, loader struts), not fill speckle.

Known shortfalls: in S, end-on items (Brine's gun aimed at the camera, Clack's tube) read as short stacks of rings; kneeling poses in S show little leg; hands are mittens or fists. Nothing tested in the Godot runtime. Scratch tools I used (not committed): scratchpad/d2/rv.py (quick multi-frame review), pre.py (fast ground/border/equipment check without export), vid.py (actions video with the Brine tether effect), fac.py (facings sheet).

## Lead to all designers, 25 Oct (audit fix pass): what changed in the shared rig and what to do

1. **Arms in N (parts.Rig.zarm).** From behind, a hand in front of the chest and within the torso's width (`R.body_half`, default 9.5 px of lat) now takes the far depth, so a cross-body reach or a two-handed grip is hidden by the back instead of painted over it (audit: Ashe, Clack, Velvet). Raised hands (up over 50) are unchanged. If your torso is wider or narrower, set `R.body_half` after `R = Rig(f, facing)`. If you pass an explicit `zR`/`zL`, you bypass this. I re-exported all fourteen characters with it and re-ran the checks (results below).
2. **Powered variants (the whole-cast blocker).** The contract now has powered*hit, powered_dodge, powered_jump, powered_stair_up, powered_stair_down and powered_secondary. How to get them cheaply: in `anim*<id>.py`, after TABLE, add
   ```python
   POWERED = dict(ice=1.0)                 # the pose fields that put on your powered gear
   # or, when the gear needs more than flags:
   def POWERED(P, i):
       return dict(P, ice=1.0, fx=i)
   POWERED_SKIP = ('secondary',)           # only if the powered state does not allow that action
   ```
   The exporter (`anim.add_powered`) renders each `powered_<clip>` from the base table with that state, keeping the base timing, release frame and release anchor. Write a table yourself under the same name to override one. Examples: anim_bramble.py (dict), anim_iona.py (function), anim_pendle.py (function that puts the rifle in both hands, and SKIP for fan fire). Then `python3 export.py <id>` and `python3 checks.py <id>`.
3. **Feet skating.** `anim.unskate(keys, P0)` lifts a foot that moves more than 3 px in the drawing where it moves and spreads a two-foot change over two drawings. Copy the loop at the end of anim_bramble.py. Guards must stay 8 drawings: bring one foot home in drawing 5 and the other in 6, or unskate appends a drawing.
4. **Lone pixels.** `f.despeckle = True` in your `draw()` merges single pixels whose four neighbours share one colour (opt-in; Cairn uses it).
5. **Clip ends.** Make guard 7, jump 7 and dodge 7 equal your idle drawing 0 (usually `K()`), so the runtime's cut to idle does not pop (CONTRACT.md, runtime rules 4 and 11).
6. **Reach.** `python3 ../../audit/reach2.py <id>` lists limbs stretched over 1.10; fix them (twist the shoulders or move the hand in).
7. CONTRACT.md now carries the eleven runtime rules from AUDIT.md.

Lead's own characters in this pass:

- Bramble: guard 7 = idle 0; jump and dodge end on idle; reach fixes. The right-handed billhook is deliberate: the right is his bow hand, so stowing the bow over the left shoulder frees exactly the hand that draws the billhook from the right hip, while the left (draw) hand stays free.
- Iona: the upright spear in the near hand is drawn in front of the head in E. The hand moved 2 px back, so the shaft crosses the cheek between ear and eye.
- Pendle: the low-ready rifle is a diagonal from the front.
- Cairn: the thrown rock is never on the release drawing. The release moved to drawing 7, and drawing 6 holds the rock at the release point. The rock is now an angular slab with a torn root-ball, held on top of the fists and ahead of the head, so it no longer reads as a second head. Feet no longer skate, and the rim speckle is merged.
- Still open: Cairn's pebbles and splint shape (polish, waiting on Matt).

## Designer 3 audit pass (Nix, Rook, Mote), 25 Oct

Re-exported on the lead's zarm fix (R.body_half: Nix 10.5, Rook 12, Mote default). checks: nix 772 frames 0 errors 0 warnings (despeckle on); rook 772 frames 0/0; mote 776 frames 0 errors, 5 lone-pixel warnings (hem fragments in dodge E, special E 6). audit cont.py: clean for all three; reach2.py: clean except two 1.12 stair_down reaches (Rook's left hand, the step down), left as is.

- Rook: Thruster Vault drawing 7 is the idle pose (no pop to idle). Primary steps one lifted foot at a time (1, 2, 8, 9); the aim holds the gun nearer the centre line so the left hand reaches the fore-end; fore-end grip 4.5 px from the grip. Orbital Rig 4: the helmet is lifted above and behind the head so a cap of it clears the head facing W. Defeat: the left hand leaves the fore-end for the knee. The thruster puff while the helmet seats (special 5 to 6) is unchanged pending Matt.
- Nix: primary steps one lifted foot at a time; S hair spike trimmed 2 px (idle heights S 73, N 71, E/W 72); despeckle on.
- Mote: the wind-up shard is held behind the head, so it shows in W and N. Not done (polish): dodge S has no sideways lean (the rig's lean is forward only, which barely shows facing the camera).
- All three: powered_hit, powered_dodge, powered_jump, powered_stair_up/down and powered_secondary via POWERED (Nix casing=1, Rook helmet='head', Mote aphelion=1); guards are 8 drawings with lifted steps out (0, 1) and home (5, 6), 7 = idle; jump 7 and dodge 7 = idle 0; unskate on the other actions (Rook's vault excluded: its air drawings are runtime-driven). fx sprites and manifest 'effects' re-written after export.

## Designer 2, audit fixes (Brine, Ashe, Clack), 25 Oct

Re-exported after the lead's fix pass, using the powered variants (`POWERED` in each anim file), `anim.unskate`, and clip ends equal to idle 0. My three builds set their arm depths themselves, so the new `Rig.zarm` doesn't apply to them; the same N rule is in my builds instead. From behind, a hand in front of the chest or across the body, and an elbow in front of it, are drawn behind the back. `reach2.py` is clean (nothing over 1.10). Arms now come from `brine.shoulders()`, which turns the shoulders about the vertical (up to 40°) only as far as needed to keep both hands within arm's length. The arm joints are a little narrower and the arms a little longer than before (Brine 11 / 18 px, Ashe 10.5 / 17.6, Clack 12 / 19.1).

- **Brine (blocker): harpoon-out variants.** `idle_empty`, `walk_empty`, `guard_empty`, `hit_empty`, `powered_idle_empty`, `powered_walk_empty`, `powered_guard_empty` and `powered_hit_empty` are the same tables with the harpoon out. They are registered for brine in `anim.EXTRA_CLIPS` from anim_brine.py at import, so export.py and checks.py pick them up. **Lead: please adopt these in anim.py.** One detail: `guard_empty` / `powered_guard_empty` get no `roles` in the manifest, because export only gives roles to names ending in "guard"; their hold drawing is still 4.
  - **Pressure Brace:** during the special and powered_exit, the left hand alone holds the gun upright in front of the belly by the fore grip (gun mode `left`), so it is visibly held in E and W while the right hand turns the regulator valve.
  - **Defeat:** the gun lies across his lap with both hands on it.
- **Runtime rule to add to CONTRACT.md (request; harpoon_out).** `harpoon_out` is set at the release drawing of primary or powered_primary and cleared at secondary (or powered_secondary) drawing 6. While it is set, play `<clip>_empty` in place of idle, walk, guard and hit (and their powered versions). jump, stairs, dodge and defeat have no empty variant; if they are needed while the harpoon is out, play secondary 5 to 8 first, as AUDIT rule 6 says. The tether is a scene line from the frame's `muzzle` anchor.
- **Ashe.**
  - The two-handed powered grip is gone: powered_primary and powered_guard are one-handed. The free left hand is a fist at her side, because a two-handed grip at this arm length stretches the forearm.
  - The helm is 2 px wider (radius 10), so the hair no longer pokes out of it as it seats.
  - The carried helm sits 3 px higher, so the cupping hand is within reach.
- **Clack.**
  - The rear bell is a flat-ended flared cone with an open dark throat. The muzzle is a wide orange collar with a brass-edged open bore, and the rocket nose in it is steel.
  - The reload tips the tube muzzle-down toward his left hand. The rocket comes from a new closed ammo case on the left hip (tag `rack`), so the rack always shows two rockets and there is no rack state.
  - The pressure vent is now worked by a lever at the fore grip; reaching the chamber behind the shoulder was beyond arm's length.
  - In W, the harness straps are clipped to the torso, so they no longer cross the far-shoulder tube.
  - The fore grip sits 1.5 px closer to the trigger grip.
  - The stance changes step one foot at a time, and the right foot no longer steps back. A foot behind the pivot lifted the lowest row by 1 px in S and N.

Result: checks.py 0 errors for all three (brine 1052 drawings incl. the 8 harpoon-out clips, ashe 796, clack 784; only lone-pixel warnings, 1 px diagonal steps); reach2.py clean; cont.py silent for my three. Re-exported out/<id>/, review sheets, review/<id>\_actions.mp4 and review/designer2_facings.png.

## Designer 1, audit fix pass, 25 Oct

Re-exported Morel, Velvet, Tam and Mirra with the lead's zarm fix and the powered variants: 23 clips x S N E W each. Morel's powered_hit, dodge, jump, stairs and secondary come from `POWERED = dict(mask='face')`. Velvet, Tam and Mirra write them with `anim_morel.powered_from`, because their powered rest pose differs from the base one: each non-looping variant eases over its last three drawings into powered_idle 0, so the runtime's cut does not pop. checks.py: 0 errors for all four (Morel 796 drawings, Velvet 772, Tam 768, Mirra 768); warnings are lone pixels only. audit/reach2.py: nothing over 1.10. No planted foot moves more than 3 px between drawings in any non-loop clip.

- **Arms.** A pose's `zR`/`zL` is now only a hint for S, E and W: in N `morel.arm_z` always uses `Rig.zarm`, so the lead's cross-body rule applies (Velvet's cut is hidden by her back in N; the sabre may hide in N). In profile the far upper arm stays behind the torso and only the forearm comes round in front (`morel.up_z`), which fixes Tam's W strike (the far ochre sleeve no longer lies across the chest). Every hand is kept within its arm's reach (`morel.reach`), so audit/reach2.py lists nothing over 1.10 for the four.
- **Tam's frost ridge** is laid from a deep crouch with both palms driven down toward the ground ahead at full reach (no stretched arm); the ridge itself is the scene effect.
- **Feet.** I tried `anim.unskate`, but a lifted foot in S or N leaves only the planted foot, and a planted foot behind the body (S) or in front of it (N) projects 1 px above the pivot row, so checks.py fails those drawings (Bramble passes only because its lifted drawings happen to plant a foot near fwd 0). Instead `anim_morel.spread_feet` lets a planted foot move at most 3 px per drawing and spreads a larger stance change over the neighbouring drawings (both soles stay down; first and last drawings unchanged). Guards bring one foot home in 5 and the other in 6 and stay 8 drawings. A clip that lifts a foot on purpose (dodge push-off) is spread only after its last lifted step. **Request for the lead:** if lifted steps are preferred, let the S/N ground check accept a lowest row up to ceil(K x |fwd of the planted foot|) above the pivot row.
- **Clip ends.** guard 7, jump 7 and dodge 7 equal idle 0.
- **Polish taken:** Velvet's lantern hangs 2 px lower so its base shows below the tails in W, and the powered lantern is carried forward (visible in W through the special and powered clips); Mirra's gem shows at the right edge of the wrap in N; Velvet's powered_primary and powered_exit are back at contract length (8).
- **Polish not taken:** Morel's flask in W stays hidden by the apron (far hand); showing it would need a pose that looks wrong in E. Mirra's primary and secondary read as gestures only; the water is the runtime's effect at `palm_R` on the release drawing (rule 3).

Lead, re-export after the zarm change (25 Oct, evening): all fourteen re-exported from the working tree as it stood (designers' uncommitted source included) and checked: 0 errors for every character. Ashe's and Clack's cross-body arms in N are now behind the back. Commit "Re-export the ten after the zarm fix" holds only out/ and review/, not your source.

## Designer 2, re-audit (AUDIT-2.md), 25 Oct

- **Brine, harpoon continuity complete.** Every clip that can play while the harpoon is out now has an `_empty` version, so nothing pops the harpoon back in:
  - base clips: `idle_empty`, `walk_empty`, `guard_empty`, `hit_empty`, `jump_empty`, `dodge_empty`, `stair_up_empty`, `stair_down_empty`, `special_empty`, `defeat_empty`;
  - powered clips: `powered_idle_empty`, `powered_walk_empty`, `powered_guard_empty`, `powered_hit_empty`, `powered_jump_empty`, `powered_dodge_empty`, `powered_stair_up_empty`, `powered_stair_down_empty`, `powered_exit_empty`.
  - Each is the same table with the harpoon out; the powered ones also have the glass lit. `special_empty` keeps the special's release drawing (4, `hand_R`).
  - They are registered for brine in `anim.EXTRA_CLIPS` from anim_brine.py.
  - **Lead:** please adopt them in anim.py. Also give `jump_empty` / `powered_jump_empty` the jump roles and `guard_empty` / `powered_guard_empty` the guard roles: the exporter assigns roles by exact name, so these get none.
- **Proposed runtime rule (for CONTRACT.md, replacing "secondary 5 to 8 first" in rule 6):** `harpoon_out` is set at the release drawing of primary or powered_primary and cleared at drawing 6 of secondary or powered_secondary. While it is set:
  - every clip X plays as `X_empty` (powered: `powered_X_empty`), so dodge, jump and defeat start at once with no delay;
  - **primary reels in:** the primary input plays secondary (powered: powered_secondary), so the same button recalls the harpoon, and the next primary fires normally. I prefer this to blocking primary: the button always does something visible, and it uses drawings that already exist.
  - If the tether entity ends without a reel (the target dies or the line breaks), the runtime clears `harpoon_out` and the next clip uses the loaded set; that is the one place the harpoon appears without a drawn reel. I can draw a 3-drawing "rewind" if you want it covered.
- **Clack, N reload:** when the tube is tipped below shoulder height in N, its front half (muzzle, collar, front band, grips) is drawn behind his back; only the rear half (bell, chamber, rear band) shows over the right shoulder. primary N 8 to 9 now show the bell end only. The launcher's rear half takes its own depth (`launcher(..., zr=)`).

## Lead, 25 Oct (late): AUDIT-2 items done on the shared side; please report when your fixes are exported

- **Effects survive re-exports.** `anim.export` now keeps the previous manifest's `effects` block, or rebuilds it from an optional hook in your anim module: `def effects(): return sprites, meta` (sprites: {file: RGBA array} saved to out/<id>/fx/, meta: the block). Designer 3: please move the three `__main__` blocks of anim_rook/nix/mote into `effects()` hooks. I re-ran the three scripts, so the blocks are back in the manifests now.
- **CONTRACT.md:** rule 3 (effects), rule 5 (every powered clip starts and ends on powered_idle 0; special while powered is blocked; defeat while powered plays powered_exit 0 to 3 first), rule 6 (Brine's harpoon_out in full, using designer 2's wording, with `_empty` for idle, walk, guard, hit, jump, dodge, stairs and defeat; primary and special blocked while the harpoon is out; a dodge is never delayed), rule 7 (Clack: no rack state), rule 11 (all characters), and the Cairn timings in the table.
- **Iona:** powered_primary now enters from the upright spear through the tilt drawing (release frame 4, still at 0.33 s).
- **Next (lead):** when all three of you have reported, I run checks.py and the audit scripts across the 14 and import the whole cast into the game (branch claude-a/cast-all), with a character-select key. Please append "designer N: done, exported at <commit>" here when you are ready.

## Designer 1, re-audit (AUDIT-2), 25 Oct

- Tam's Frost Ridge (secondary and powered_secondary 4 to 5) now kneels on the left knee and leans in, so both palms rest on the ground ahead: the fingertips are 4 px above the ground row and the wrists 6 px, with reach under 1.0 and every facing on the ground rule. The robe hem is clamped to the ground when he kneels.
- Velvet, Tam and Mirra: every powered action (primary, guard, hit, secondary, dodge, jump) now starts on the powered_idle pose and eases out of it over three drawings (`anim_morel.powered_entry`), so entering from powered_idle no longer pops (Mirra keeps her wide, low stance into the action; Velvet's powered_guard keeps the raised sabre).
- Mirra uses `f.despeckle = True`: 0 lone-pixel warnings (was 191); gem and hoops intact.
- Re-exported Velvet, Tam and Mirra: checks.py 0 errors each; audit/reach2.py clean; no planted foot moves more than 3 px a drawing.

## Lead, 25 Oct (late): final check and the whole cast in the game

- Adopted: Brine's `_empty` set is now in `anim.EXTRA_CLIPS`; any clip whose name contains jump or guard gets the roles (out/brine manifest patched in place, metadata only); CONTRACT rule 6 uses designer 2's "primary reels in"; CONTRACT lists the extra clips.
- Final check at b67eea81: checks.py 0 errors for all 14; audit reach2 clean; effects blocks present for Rook, Nix and Mote. Remaining from metrics2: foot moves of 2.6 to 3 px in some designer-1 guards and in Ashe primary 10, under the audit's 3.3 px line; attack drawing 0 being a ready pose (accepted polish).
- Game: draft PR https://github.com/rempemat-eng/appify/pull/251 (claude-a/cast-all) imports all 14 with a debug character select (1 to 0, Shift+1 to 4).

## Lead, 25 Oct 16:xx: Cairn larger

Matt asked for a larger, taller Cairn. `ew.Fig(scale=)` draws a build larger at the same pixel density (default 1, so every other character is unchanged; Bramble re-renders byte-identical). Cairn is drawn at `cairn.SCALE = 1.2`: about 104 px standing instead of 87, same proportions. His walk speed is 36 px/s and his breath stays 1 px. The cell is unchanged (it fits; defeat fists moved in). Checks 0 errors; reach, feet and clip ends clean. Game: draft PR on claude-a/cairn-larger.

## Lead, 25 Oct (evening): village folk

Hale, Moss and Ada Fern on `src/folk.py` (a shared villager builder on parts.Rig), one module each (hale.py, moss.py, ada.py) with idle, walk, talk and work (anim.EXTRA_CLIPS), drawn with `Fig(scale=)` to 74, 73 and 71 px. Checks 0 errors, reach clean. In the game on claude-a/villagers.
