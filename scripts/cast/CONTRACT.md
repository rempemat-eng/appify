# Animation contract (cast, v2)

**v2 (25 Oct, after Matt watched a fight: "more animated frames and possibly facing more directions (like in eastward: idle movements, the weapons facing in more then 4 directions...)", "a touch too slow", "make the bow a bit more interesting/ bigger", "make sure you get the 3d effect right every time").** Piloted on Bramble (bow) and Velvet (sabre); the other twelve stay on v1 (four facings) until Matt approves, and the runtime falls back for them. What changes from pass 2 is in this section; everything below still holds unless it says otherwise.

### V2.1 Facings: four body facings ship, eight are stored

**Matt, 26 Oct 08:11: "store the animations but honestly 4 directions if its smooth enough is probably fine (like eastward). the weapon might need to move in more directions however."** The shipped contract has the four body facings **S, N, E, W** for every clip; the weapon clips also turn to **aims within the facing** (V2.8). The three-quarter facings (SE, NE, SW, NW) stay stored and exportable: `python3 export.py <id> --facings 8`.

- Every facing is drawn from the one 3D pose by `parts.proj`. W (and SW, NW) is drawn on a mirrored grid from the E (SE, NE) geometry with the lateral axis negated, relit upper left: never a flipped image.
- Stored 3/4 machinery: `parts.ANG`/`MIRROR`/`Rig.diag`/`Rig.back`, `surf.py` (cylinder and sphere surfaces, 3/4 boots), `turn.Warp` (turns a build's flat S and N drawings onto the body), the pilots' and the folk's 3/4 torsos and heads.

### V2.2 Manifest and frames.tres

- `contract: 2`, `directions` (S, N, E, W; eight only with `--facings 8`), `facing_vectors`, `facing_rule`, `idle_fidgets`, and for weapon clips `aim_clips`, `aim_degrees`, `aim_tags`, `aim_rule` (V2.8). Per clip `facings{F}` has `frames` and, for actions, `release_anchor`; a weapon clip's facing also has `aims{tag}` each with `deg`, `screen` (the aim's unit screen vector), `frames` and `release_anchor`. The facing's own `frames` are its straight-ahead aim (`0`).
- frames.tres: `<clip>_<F>`, `<clip>_<F>_<tag>` for each aim (`primary_E_p22`), and `<clip>` = E.

### V2.3 More drawings, same gameplay timing

- **Walk 12 drawings a stride** (`anim.WALK_N2`), stairs 8 (unchanged), idle 12.
- Actions get in-betweens for **anticipation** (a dip or wind-up before the move), a **smear or whip** in-between before contact, **overshoot** and **settle** drawings after it (`anim.densify` inserts mid-poses; or write them out, as anim_bramble.py does). Bramble's primary is 18 drawings (was 12), secondary 16 (12), hit 10 (8), dodge 10 (8); Velvet's primary 17 (11), secondary 13 (9), hit 10, dodge 10.
- **Secondary motion** (`anim.follow`): cloth (`lag`: mantle, coat tails, quiver), hair and beard (`hair`, Bramble) and hanging gear (`lsw`, Velvet's lantern) trail the shoulders' motion through a damped spring, overshoot and settle. The last drawing of a non-loop clip is untouched, so it still equals the rest pose.
- Timing: `anim.fit_timing` still refits every action to Codex's total duration and release time; only the release drawing's index moves (Bramble primary 11, secondary 7, powered_primary 7; Velvet primary 7, secondary 6, powered_primary 5). Jump (8, roles by index) and guard (8, hold 4) keep their counts.

### V2.4 Facing selection (runtime)

- The runtime picks the body facing **from the aim** while standing or acting and **from the movement** while walking: the nearest of S, N, E, W with about 10 degrees of hysteresis. On a facing change mid-clip keep the drawing index.
- A weapon clip then picks its aim within the facing (V2.8). A facing change shows a three-quarter in-between for a short beat (V2.9). Melee swings stay per facing (Eastward's John swings his pan in his four facings).

### V2.5 Idle life (fidgets)

- The idle is a 12-drawing breathing loop. Each character also has **2 to 3 fidgets** (`FIDGETS` in its anim module, `idle_fidgets` in the manifest): Bramble `fidget_string` (plucks and listens to the bowstring), `fidget_beard` (scratches his beard), `fidget_quiver` (half draws an arrow to count them and pats the quiver); Velvet `fidget_glass` (taps the lantern's glass with the knuckle-bow), `fidget_flourish` (a small sabre flourish), `fidget_shoulders` (rolls her shoulders, the tails swing). They are drawn in every body facing (and the stored eight with `--facings 8`), authored timing (`authored: True`, not refitted), and **start and end on idle 0** (checks.py verifies the sha).
- **Trigger rule** (`idle_fidgets.after` 4.0 s, `every` [6, 10] s): when idle has shown continuously for 4 s, play one fidget, chosen at random but never the same twice running, starting when idle reaches drawing 0; then return to idle; the next comes after a random 6 to 10 s more of idle. Any other clip (walk, an action, a hit) cancels the fidget at once and resets the clock; a facing change while a fidget plays cancels it too (it returns to idle in the new facing). No fidgets while powered. The game's `CastSprite` implements this.

### V2.8 Weapon aim within the facing (26 Oct)

What Eastward does (local screenshots 02 and 22, and the Steam thread below): John's body is in one of four facings (profile while he walks and fires to the side); his gun is held across the body in that facing, and the shots in the same frames fly at angles between the cardinals. On keyboard the movement keys give "8 major directions" and the mouse points freely (https://steamcommunity.com/app/977880/discussions/0/3038230013018479783/). The web sources found do not describe the sprite set further; this design meets the brief (at least 8 aim directions) and goes finer.

- Weapon clips (`AIM_CLIPS` in the anim module; Bramble: primary and powered_primary) are drawn at **`AIM_DEGS` = -45, -22.5, 0, +22.5, +45 degrees** within each body facing (screen degrees, + clockwise: for E + is down the screen, for S + is toward the screen left). With four facings that is **16 aim directions, every 22.5 degrees**; the body stays in its facing and only the arms, the weapon and the shoulders' twist turn.
- Each aim is drawn from the rig, not rotated as an image: `anim.aim_body(F, deg)` gives the body-space aim whose projection draws **exactly along the screen direction the projectile flies** (the map is the picture plane), with a lateral part for depth: aiming toward the camera brings the arms and weapon in front of the body, away puts them behind. E and W: up/down the screen is the weapon's pitch, with a little turn toward or away from the camera. S: lateral plus a drop (the forward part is foreshortened by K). N: raised 45 degrees so the weapon clears the head. The bow is canted about the arrow line in N and S toward the side where it stands clear of his head (measured per aim).
- `orient` (anim_bramble) turns the drawn draw about the chest from straight ahead to the aim, drawing by drawing (the reach to the quiver does not turn; the raise turns part way; nock to follow-through fully; the lowering eases back), so the hands stay on the bow and string in every aim, and the release drawing and timing are the same in all aims.
- Each aim has its own `release_anchor` (the arrow tip). **The runtime** picks the facing (V2.4), then the aim nearest the exact angle, plays `<clip>_<F>_<tag>`, spawns the projectile at that aim's anchor and flies it along the exact aim.

### V2.9 Smooth turns: three-quarter in-betweens (26 Oct)

Matt, after Eastward's gameplay (https://youtu.be/dWEOOrbw3Ug): "the body turns in 4 directions but with somewhat smooth transitions in between". The stored three-quarter drawings are exported as **turn in-betweens**, not as playable facings.

- Clips `anim.TURN_BASE_CLIPS` (idle, walk, powered*idle, powered_walk) and the weapon clips (`AIM_CLIPS`, their straight-ahead drawing) get `turns{SE, NE, SW, NW}` in the manifest, each with one drawing per drawing of the clip (same count, same timing); frames.tres `<clip>*<D>`. A module may list its own `TURN_CLIPS`. The manifest's `turn_inbetweens`gives the facings, the clips,`hold`(0.07 s),`hold_180`(0.055 s),`aim_step` (0.04 s) and the rule.
- **Runtime rule** (CastSprite): when the body facing changes between S N E W in such a clip, show the diagonal between the two facings for `hold`, **keeping the drawing index and the clip time** (a walk does not stutter: the in-between is the same stride drawing turned). A 180-degree turn passes through one side: diagonal, the cardinal between, diagonal, `hold_180` each, on the side the input rotates toward (movement, else aim); an exact reversal goes by the S side (E/W) or by E (N/S). Gameplay (anchors, release) already uses the new facing.
- Within a facing, a weapon clip whose aim changes mid-clip steps one aim (22.5 degrees) per `aim_step` toward the new aim instead of jumping; a new shot starts at its aim (its first drawings do not turn yet, V2.8).
- Every character in the rollout ships these in-betweens; checks.py checks them like a facing (ground, palette, equipment) and that each set has the clip's drawing count.

### V2.10 Polish: spacing, arcs, weight, clean pixels (26 Oct)

Matt, 26 Oct 10:15: "the new animations are definitely getting there (a bit more polish and its perfect)", "remember the soft grid and pixel style (at our current resolution)". Screen size and pixel density stay.

- **Spacing and easing** (`anim.space`, inside `fit_timing`): every drawing of every clip except the walks (whose planted foot sets the cadence) is held a whole number of 60 fps frames, so none flashes past in under a frame or alternates one and two frames. Key poses are held: the release or contact drawing and the one after it at least 3 frames, the longest-authored drawing on each side of the release (the anticipation peak, the settle) and the last drawing at least 3, the module's `HOLDS` (Bramble's anchor at full draw, Morel's load) at least 3. Other drawings get at least 2; when a clip has more drawings than frames, its shortest in-betweens drop to 1 frame (the fast part of the move). The rest of the frames follow the authored proportions, so slow-in and slow-out stay uneven. Each side of the release keeps its length to the frame (0.333 s, so gameplay timing moves by under a frame); authored fidgets are rounded to frames.
- **Arcs** (`anim.arc_lerp`, used by `densify`): an in-between swings a hand round its shoulder (same distance, the angle between) and turns a weapon or held thing through its angle (slerp, same length), instead of a straight-line midpoint that cuts the corner and shrinks the bow, sabre, hammer or flask.
- **Weight and overlap**: the gait's down beat a drawing after each contact (1 px); actions end on settle drawings into rest; `anim.follow` makes cloth, hair, beard, quiver, lantern and the hanging flask trail by one to two drawings with a damped overshoot.
- **Clean pixels**: the soft grid and edge rules of `docs/vision/eastward-edges.md` for the character's outline, which stays one clean pixel wide (silhouette doubled corners measured at 0 to 2 per drawing). `anim.deflicker` removes one- and two-pixel specks that blink on for a single drawing, using the value both neighbouring drawings show, and only where that value already fills at least three of the pixel's own neighbours. It never leaves a stray and never changes idle drawing 0, which the fidgets share. checks.py warns on any flicker that is left (`anim.flicker`).

### V2.11 Release anchors on the item, and the second batch's fixes (26 Oct)

- **Anchor on the item** (Matt's #289 note on Morel's throw): every release anchor lies within 2 px of its held item's visible pixels (`anim.anchor_gaps`, the manifest's per-frame `anchor_gap`, a checks.py error), in every facing and aim; the item may be out of sight only from behind (N). From behind, gear on the back that is nearer the camera than the item may cover it, and the anchor may sit on that gear when the module names it in `ANCHOR_COVER` (Clack: the loader frame over the muzzle).
- **The strike is never hidden** (26 Oct review of Ashe's cut): at the release the held weapon shows at least `RELEASE_MIN_PX` (12) pixels in every facing and aim, N included (checks.py error). The weapon is the module's `WEAPON_TAG[clip]` (Bramble: the bow, since the arrow has left), else the release anchor's item. Where the body would cover the strike from behind, a module poses that clip per facing with `facing_table(clip, fc)` (same drawing count and timing; the exporter uses it when present): Ashe cuts down on her right side in N, Velvet's cut and lantern flare and Morel's catalyst go out beside the body.
- **Batch 3 (Iona, Nix, Brine, Pendle)**: `ANCHOR_WITH[anchor]` names parts that belong to the item in some states and count with it in every facing (Iona's storm rim on the blade, Pendle's rifle for the muzzle in Longshot); `WEAPON_WITH[clip]` adds the shot's own effect to the weapon's visible pixels at the release (Pendle's muzzle flash, where the revolver points at the camera). Aims: Nix's laser arm swings about its shoulder (anim.aim_body); Brine's harpoon gun and Pendle's rifle turn about the stock (level in S, anim.aim_level) and, from behind, are held out past the shoulder on the aim's side; Pendle's revolver arm swings about the shoulder and, aimed across from behind, is raised at his right past the hat. Brine's harpoon-out clips (`*_empty`) get the turn in-betweens too (`TURN_CLIPS`).
- **Clack**: the launcher stays level in S and N (`anim.aim_level`) and pitches in E and W; aimed up it rides forward and up on the shoulder pad (`SLIDE_UP` 12 px, `RAISE_UP` 3 px at 45 degrees) and in E and W he leans his head back (`hback`, 3 px), so the muzzle clears his face; the vent's puff and the backblast blowing away from the camera are drawn behind him.
- **Ashe**: a one-handed diagonal cut that stays outside her silhouette (back low, load behind the right shoulder, swing up ahead of her face, contact forward and down, follow-through low across her front); the blade continues the forearm line from the fist in every drawing.
- **Tam** (v3 design, Matt 26 Oct): shaved head, heavy dark brows, a short squared chin beard, a deep maroon under-robe under the saffron, a slate-blue sash; a slimmer profile with a flared hem; arms long enough that the palm strike reaches clear of his face.
- Ashe, Tam and Clack have three-quarter builds for the turn in-betweens (turn.Warp of the S/N torso, a three-quarter head, the shared three-quarter boot).

### V2.12 No face from behind (26 Oct review of Pendle's N aims)

- In N and in the NE / NW turn drawings (and every N aim) no face part shows. Face parts carry the tag `face`: the eye ink (`parts.EYE`, tagged automatically by `ew.Fig.detail`), eye glints, Pendle's lamp eyes and the bandana's front, Mote's lamp eyes, Cairn's eye slits, Brine's faceplate window. checks.py fails a back drawing with any `face` pixels, or with any pixel in a colour that only the face uses (`checks.face_colours`: the colours under the `face` tag of the S, E and SE idle drawings that appear nowhere else in them).
- The back of a head must also not _read_ as a face at game size: no back view may share the front view's face layout (a dark band over a coloured patch, paired lights at eye height, a notch that reads as a mouth). Look at it at 1x and 2x and as a blurred thumbnail (`python3 src/squint.py out.png <ids>`, the squint test) for every back view. Pendle from behind reads as a gunslinger's back: the duster's collar turned up high, the hat's back brim low, only a narrow band of the steel back plate between them (with its seam), the bandana only as a small knot off-centre at his right with both tails hanging to that side, the hat's crown dent and band tie showing from behind. Clack from behind: the grey fringe covers the back of the skull from just under a thin mid-tone strap to the nape, with a few combed strands.
- Ashe: her worn helm's visor is tagged `face`, and turned away (NE, NW) the helm, worn or carried, shows its plain rear; the helm shell has lit and dark planes (mirrored on the flipped grid).
- **Scale (26 Oct audit, `docs/vision/size-guide.md`, main's `logic.scale`)**: Cairn is 1.2x the hero, about 89 px of body (`SCALE` 1.063; 25 Oct's 1.2 x the old 87 px rig measured 101); Morel is drawn at `SCALE` 1.05 so his stoop measures 72 to 73 (adults 70 to 78). A module's `SCALE` multiplies its walk speed too.
- `anim.deflicker` no longer strands lone pixels: after its fixes, a pixel that became lone where its four neighbours agree takes their colour (Cairn's scaled boulders had up to 16 such specks a drawing). Exported with it on 26 Oct: Ashe, Pendle, Cairn, Morel; the other characters' exports predate it and a re-export may despeckle a few pixels.
- **Batch 4 (Mirra, Mote, Cairn)**: Mirra's headwrap folds are 4-connected lines (no dotted folds); Mote's skull has three light planes, mirrored on the flipped grid; Cairn has a three-quarter build (the wedge head turned toward the facing, the far eye foreshortened; the far arm behind the body), a 12-drawing idle and walk, the fidgets `fidget_knuckles` and `fidget_pebbles`, and 2 px moss tuft strokes.

### V2.13 Batch 5: Rook C, Tam v4, Cairn's hands (Matt, 26 Oct 19:19)

- **Rook** is design C, the observatory moon-walker (`rook_opts.use('lantern')` is applied by rook.py): a quilted beige suit with midnight-blue pads and brass trim, chest lanterns, a star chart on the pack, a glass bubble helmet in a brass ring.
  - With the helmet worn, the hair is cut to the glass's inner volume (`rook._in_helmet`) in every facing, aim and clip; the glass, rim and highlight draw over it.
  - Designs A (Cogsworth brass) and B (shard defector) stay in rook_opts.py and are recorded as proposal outfits in `game/data/progression/rook.json` (unlock TBD).
  - Rook has a three-quarter build (the S or N pack and torso turned with turn.Warp, `head_3q`), a v2 idle, walk and fidgets (`fidget_stars`, `fidget_check`), and the carbine aims within the facing about his shoulder.
- **Tam v4** has a real neck (`tam._neck`: the throat shaded under the jaw, the nape behind, trapezius slopes into the robe's neckline) and the head set 1.2 px lower, from every facing.
  - His weight is on the right leg (P0: the left foot relaxed ahead, heel light; the idle settles his hips). He is drawn at `SCALE` 1.05 (body 73 px; the neck set the head lower).
  - Fidgets: `fidget_beads`, `fidget_shoulders`.
  - The frost ridge kneel is redone: the right foot ahead, the left knee down, the back long, and the saffron drapes forward over the thighs (`_skirt(kneel=)`).
- **Cairn's hands** (`cairn.golem_hand`, `HAND_K` 1.3): about 30 % smaller than the round fists, blocky stone with three stubby fingers, a separate thumb stone, a knuckle ridge and moss in the joints.
  - `gripR` / `gripL` run from 0 (open, in idle) to 1 (a fist with three knuckle stones, in the slam and guard).
  - The slam's contact comes down 1 px so the knuckles still strike the ground.
- **Cairn's hands, big blocks (26 Oct, after the 22:30 reference; construction only)**: each hand is five big faceted stones (`cairn._block`): a back-of-hand slab, three thick blunt finger wedges and a separate thumb wedge.
  - The fist is four blocks bunched: the slab, two knuckle blocks and the thumb wedge across them.
  - The stones are in the arms' value: the face in the mid tone, a thin lit top facet one step up toward the light (upper left, mirrored on the flipped grid), and broad shaded side facets one step down.
  - A dark gap shows only between blocks, never inside one. A bit of moss sits in one joint.
  - `HAND_K` is 1.4. The slam's contact keys are 1 px lower than the round fists'. The defeat's fists rest 3.5 px higher.
  - The thrown slab has flat facets too (`_slab_facets`).
- **Cairn stands more upright (27 Oct, Matt: "a bit less hunched and a touch more upright, not completely")**. `cairn.UPRIGHT` holds the changes, in every clip and facing:
  - The torso leans forward about half as far (2.25 px off every key's `lean`), and the shoulder line sits 1.5 px higher.
  - The head is 4.5 px higher and sits on the chest, not in front of it: 8 px forward of the shoulders from the side (was 17), 8 in three-quarter (was 12).
  - The chest stone sits 4.5 px forward of the belly from the side (was 6.5).
  - The back boulder sits under the shoulders (-13, -11), not over them. From behind, it shows bare stone with a thin moss band, so the head is the only mossy mass on top.
  - The stance, round body, hands and the slam keys are unchanged.
- **Cairn's torso depth, equal arms and golem proportions (27 Oct, Matt 11:03 and 11:05)**. Proportions and construction only come from the reference, not its design.
  - Torso depth (`cairn.DEPTH`): the chest stone is about 20 % shallower front to back. It is 35 px deep in profile (was 44); the chest, belly, pelvis and back boulder together are 44 px (was 55). In the three-quarter turns the chest's projected width is 21 -> 18.9. The width across the shoulders and the heights stay. The shoulder sockets sit 2 px further forward, and the head follows them in (6 px ahead from the side, 7 in three-quarter).
  - Equal arms: both arms use one set of segments (`cairn.ARM`: upper 19, fore 18.5). The rest hands now hang the same distance from their shoulders, and the shoulders turn less (P0 `turn` 2, was 6). Before, the right hand rested 26 px ahead of the left, so in S the right arm drew 72 px and the left 68. Now they draw 69 and 68.
  - `checks.arm_symmetry` runs for any character whose module declares `ARM`. Both arms' rig segments must equal `ARM`'s in every idle drawing and facing, and the drawn arms in S and N (top of the shoulder stone to the lowest hand pixel) must be within 1 px.
  - Golem proportions (`cairn.LEGS`): the hips are 3 px lower, the thigh and foot stones squatter, and the stance 1 px narrower. The rest hands come down with them.
  - Measured over S idle: head 0.21 of the height (target about 0.2), legs to the hip joint 0.30 (was 0.32), shoulders 1.67 times the hips' span across the thighs (target 1.6 to 2, was 1.59), and the hands hang 6 px below the knee.
  - The legs stay above a quarter on purpose. Below that, the hip joint drops inside the foot stones.
  - The far moss caps are drawn `deep` when dimmed, so their tufts survive the dim. In NE and NW the far shoulder cap now shows whole, and without this it is a flat patch.

### V2.6 Speed

- Walk speed **+15 %**: `walk_speed` 78.1 px/s (was 67.9). The stride stays 4 x 9.5 = 38 px (a longer one stretches the legs past 1.03 of their length), so the cadence rises: one stride in 0.487 s (12 drawings of 40.5 ms). Planted feet travel exactly the body's distance, so nothing skates (the 3 px rule and `anim.unskate` hold for the actions).

### V2.7 Bramble's bow

A 52 px carved recurve (was 42): a thick riser with a leather-wrapped grip and two gold wrap bands, limbs that taper, a carved light ridge and notches along their backs, recurved tips with horn caps, a 1 px string with a brass nock point. He holds it a little higher at rest so the lower tip clears the ground. The quiver over his left shoulder bounces with the walk and he draws from it in the shot and in `fidget_quiver`.

This is how every character is animated so that the sprites can replace Codex's in its Godot studio (`mygame-animation-studio`, `scripts/roster_actor.gd`). The code is `src/anim.py` (contract, pose tools, export), `src/parts.py` (the 3D pose rig), `src/checks.py` (checks and review sheets) and one `src/anim_<id>.py` per character. Bramble (`src/anim_bramble.py`) is the template.

## Cell, pivot and facings

- Cell **160 x 144** for every character, foot pivot **(80, 136)**. The sole outline is row 135, so a standing drawing's packed bounds end at y = 136, as in Codex's frames (their pivot is (96, 172) in a 192 cell; the runtime reads `foot_pivot` from the manifest, so the smaller cell needs no runtime change).
- The figure is drawn at our scale (average adult 74 px, Cairn about 90), not Codex's 96. In Codex's 960 x 540 studio they will look smaller than its current sprites; that is the agreed Eastward scale (STYLE.md).
- v1: four facings **S, N, E, W** (v2: eight, above). W is drawn from the same pose on a mirrored grid with the light recomputed and one-sided gear on its real side, never a flipped E image.
- Draws pass `gy = anim.FIG_GY` (135) to `Fig`.

## Files per character

`out/<id>/<clip>_<F>_NN.png`, `out/<id>/manifest.json`, `out/<id>/frames.tres`.

- **manifest.json** keeps Codex's shape: `id, name, view, frame_size, foot_pivot, body_height_target, clips{...}, pose_count`. Each clip has `frame_count, durations, duration, loop, release_frame, release_time, hold_frame, frames` (the E facing, so the current runtime works unchanged) and `release_anchor` (E). New fields: `directions`, `default_direction`, `walk_speed`, `stair_speed`, per clip `roles` (jump and guard) and `facings{S,N,E,W}` each with `frames` and `release_anchor`. Every frame lists `path, file, packed_bounds, anchors, equipment, sha256`.
- **Anchors** are pixels relative to the foot pivot, in screen orientation (x right, y down; a W anchor already has the mirrored x). Every frame has `hand_R`, `hand_L`, `foot_R`, `foot_L`; weapons add their own (`arrow_tip`, `strike`, `muzzle`, `fist_R` ...). A clip's `release_anchor` is the named anchor at the release drawing (or the drawing before it, when the projectile has already left).
- **frames.tres** (Godot 4 SpriteFrames): animation `<clip>` is the E facing (what `RosterStudyActor` plays today), and `<clip>_S`, `<clip>_N`, `<clip>_E`, `<clip>_W` are the four facings. Paths are `res://assets/animated/<id>/<file>`; copy `out/<id>/` to `assets/animated/<id>/` to drop it in.

## Clips

Order and names follow `RosterStudyActor.CLIPS`; Pendle adds `reload`. Timings are authored in ms per drawing and then refitted (`anim.fit_timing`) so each clip keeps **Codex's total duration and release time** for that character (gameplay timing is unchanged). Loops are not refitted.

| Clip                                                                                              | Drawings         | Duration (Codex)     | Release / hold              | Ground rule   | Notes                                                        |
| ------------------------------------------------------------------------------------------------- | ---------------- | -------------------- | --------------------------- | ------------- | ------------------------------------------------------------ |
| idle                                                                                              | 8                | 1.6 s loop           |                             | exact         | breath (upper body 1 px), cloth sway, one blink              |
| walk                                                                                              | 10               | stride loop 0.56 s   |                             | stance        | `anim.gait`: planted foot travels 2A per step, no foot slide |
| primary                                                                                           | 10 to 12         | 0.64 s (Cairn 1.165) | release 0.33 s (Cairn 0.56) | exact         | anticipation, contact, follow-through, settle                |
| secondary                                                                                         | 8 to 12          | 0.64 s (Cairn 1.165) | release 0.33 s              | exact         |                                                              |
| special                                                                                           | 8 to 10          | 0.82 s               | release 0.38 s              | exact         | activation into the powered state                            |
| guard                                                                                             | 8                | 0.70 s               | hold drawing 4              | exact         | roles: raise 0-3, hold 4, lower 5-6, rest 7                  |
| hit                                                                                               | 8                | 0.93 s (Cairn 0.455) |                             | exact         | Cairn: 8 drawings in Codex's 0.455 s                         |
| defeat                                                                                            | 8 to 10          | 1.27 s               |                             | none          | last drawing is the held end pose                            |
| jump                                                                                              | 8                | 0.70 s               |                             | none          | fixed roles by index, below                                  |
| stair_up, stair_down                                                                              | 8                | 0.72 s loop          |                             | none          |                                                              |
| dodge                                                                                             | 8                | 0.495 s              |                             | none          | in place: the runtime moves the body                         |
| powered_idle, powered_walk                                                                        | 8, 10            | as idle, walk        |                             | exact, stance |                                                              |
| powered_primary                                                                                   | 8 to 12          | 0.64 s (Cairn 0.94)  | release 0.33 s (Cairn 0.56) | exact         | starts on powered_idle 0 (or one in-between from it)         |
| powered_guard                                                                                     | 8                | 0.70 s               | hold 4                      | exact         |                                                              |
| powered_exit                                                                                      | 8                | 0.86 s               |                             | exact         | return to the base state                                     |
| powered_hit, powered_dodge, powered_jump, powered_stair_up, powered_stair_down, powered_secondary | as the base clip | as base              | as base                     | as base       | generated: the base table with the powered state (below)     |

**Extra clips.** Pendle adds `reload` (1.11 s). Brine adds the harpoon-out set (`anim.EXTRA_CLIPS['brine']`): `<clip>_empty` for idle, walk, guard, hit, jump, dodge, stair*up, stair_down, special and defeat, and `powered*<clip>\_empty`for idle, walk, guard, hit, jump, dodge, stair_up, stair_down and exit, each the base table with the harpoon out (rule 6). Every clip whose name contains`jump`or`guard` carries the jump or guard roles.

**Powered variants.** A powered character must keep its powered gear in every clip it can play. The anim module sets `POWERED` (pose overrides, e.g. `dict(briar=1.0)`, or a function `(pose, index) -> pose`) and, optionally, `POWERED_SKIP` (base clips the powered state does not allow, e.g. Pendle's revolver fan fire). `anim.add_powered` (run by the exporter) then renders `powered_<clip>` from the same table with the base clip's timing, release frame and release anchor. A table the module writes itself under that name wins.

**Jump roles** (the runtime picks drawings by index from the vertical velocity): 0 load, 1 push, 2 rise, 3 apex, 4 fall, 5 land (contact compression; only after support), 6 absorb, 7 recover. Do not bake height into jump drawings: the runtime lifts the sprite.

**Guard**: the runtime clamps to drawing 4 while guard is held and returns straight to idle on release, so drawings 5 to 7 only show in study mode. _Runtime request:_ play guard 5 to 7 on release, because characters that stow gear for the guard (Bramble's bow) otherwise pop back to the idle pose.

**Walk speed.** Our figures are 74 px, so a foot-planted stride is 4 x 9.5 = 38 px. At 0.56 s per stride that is **68 px/s**, written to the manifest as `walk_speed` (Bramble). Codex's runtime moves at 92 px/s, which would slide the feet by about a quarter. _Runtime request:_ use the manifest's `walk_speed` (and `stair_speed`) when present.

**Release direction.** The runtime emits `action_released` with `Vector2.RIGHT`. With four facings, use the facing's direction and that facing's `release_anchor`.

## Timing rules

- 8 to 12 drawings for loops and attacks. Unequal holds: the anticipation and the contact drawing short, the load and the settle long.
- Every action has: anticipation, a held load, a short contact or release drawing, a follow-through and a settle that ends on the idle pose (so the runtime's cut back to idle does not pop).
- A body bob is whole pixels; the walk bobs 1 px down after contact and 1 px up at passing.

## Pose-key tooling (how to animate a character)

1. Make the character pose-driven: `P0(**k)` returns the default pose and `build(f, facing, P)` places everything from it through `parts.Rig` (see `bramble.py`, `pendle.py`, `cairn.py`). Body space is `(fwd, up, lat)` in art pixels from the ground pivot, `lat` positive toward the character's **right**. `Rig.p()` projects a point for the facing; `Rig.limb()` solves a two-bone limb in 3D (knee or elbow toward a pole) and returns masks; `Rig.zarm()`/`Rig.zleg()` choose depth; `Rig.far()` says which side is dimmed. In S a step toward the camera drops `K = 0.35` px per px.
2. Write `src/anim_<id>.py` with `TABLE = {clip: [(pose, ms), ...]}`, `RELEASE = {clip: drawing}`, `RELEASE_ANCHOR = {clip: anchor}`, and `EQUIP` (below). Poses list only what differs from `P0`. Helpers: `anim.gait(n, A, lift)` for walks and stairs, `anim.lerp(a, b, t)` and `anim.ease()` for in-betweens.
3. Record anchors in `build` with `f.anchor(name, x, y)` and tag gear parts with `tag='bow'` etc. in `f.add()`.
4. `python3 export.py <id>`, then `python3 checks.py <id>`, then look at `review/<id>/<clip>_<F>.png` enlarged.

## Equipment and checks

`EQUIP = {tag: dict(always=True, may_hide={facings}) | dict(clips={clip: [drawings]})}` says where each tagged item must have at least 4 visible pixels. `checks.py` also checks: palette (only ramp, outline and face colours; no blends), colour count (64 max per frame), hard alpha, lone pixels (more than 8 is a warning), nothing touching the cell border, the ground rule (E/W exact; S/N may sit up to 4 px lower because feet toward the camera project lower), the idle height band per character, and writes a 4x contact sheet per clip and facing with the pivot row, the release anchor and the timings.

## Runtime rules (from the 25 Oct audit; the game must follow them)

1. **Speed.** Move the body at the manifest's `walk_speed` and `stair_speed` (Cairn 30 px/s, Pendle 50, the others 57 to 68). A fixed 92 px/s makes the feet slide (Cairn's at three times their stride).
2. **Facing.** Pick the facing set (`<clip>_S/N/E/W`) from movement or aim. On a facing change mid-clip keep the drawing index (all facings share timing). Emit releases in the facing's direction from that facing's `release_anchor`, never `Vector2.RIGHT`.
3. **Projectiles and effects.** Spawn them on the release drawing at the named anchor. They are separate entities (Brine's tether from `muzzle`, Nix's decoy at `origin`, Rook's two turrets at the manifest `effects` offsets, Mote's orbit shards, Mirra's seals and currents). A carried item that becomes a projectile is never drawn on the release drawing (Cairn's rock leaves on drawing 7). The manifest's `effects` block (sprites in `out/<id>/fx/`) is written by the exporter: from the anim module's `effects()` hook when it has one, otherwise kept from the previous manifest, so a re-export never drops it.
4. **Guard.** Clamp to drawing 4 while held; on release play 5 to 7, then idle. Never cut from 4 to idle. Drawing 7 equals idle 0.
5. **Powered state.** Special always ends in powered*idle. While powered, play the `powered*` clip of every action that has one (idle, walk, primary, guard, hit, dodge, jump, stair_up, stair_down, secondary). Every powered clip starts on powered_idle 0, or one in-between from it, and ends on powered_idle 0, so entering and leaving it from the powered rest does not pop (generated clips included). An action without a powered clip (Pendle's revolver fan fire) first plays powered_exit, then the base action. **Special while powered is blocked** (the form is already on). **Defeat while powered** plays powered_exit 0 to 3, then defeat (the gear is put away before the fall; hit does not need this, it has powered_hit). powered_exit always returns to idle.
6. **Brine (harpoon_out).** `harpoon_out` is set at the release drawing of primary or powered_primary and cleared at drawing 6 of secondary or powered_secondary, when the reel brings the harpoon home. While it is set, every clip X plays as `X_empty` (powered: `powered_X_empty`): idle, walk, guard, hit, jump, dodge, stair_up, stair_down, special, defeat and powered_exit, so a dodge, jump or defeat starts at once with no delay. **Primary reels in:** while the harpoon is out, the primary input plays secondary (powered: powered_secondary), and the next primary fires normally. Special plays `special_empty` (its release stays at drawing 4, `hand_R`). The tether is a scene line from the frame's `muzzle` anchor to the harpoon entity; if it ends without a reel (the target dies or the line breaks), the runtime clears `harpoon_out` and the next clip uses the loaded set (the one place the harpoon returns without a drawn reel).
7. **Clack.** No rack state: the rack always shows two rockets and the reload draws from the closed ammo case.
8. **Jump.** Select drawings by role from the vertical velocity (0 load, 1 push, 2 rise, 3 apex, 4 fall, 5 land only after support, 6 absorb, 7 recover). The runtime lifts the sprite; no height is baked (Rook's vault likewise).
9. **Dodge and lunges** are drawn in place; the runtime supplies the translation, once (Iona's lunge steps the feet but keeps the pivot).
10. **Stows and draws are atomic.** Do not interrupt between a stow and its retrieve (Bramble's secondary and guard bow, Pendle's Longshot holster and rifle draw, Ashe's helm path, Rook's helmet path, Morel's mask path) except by hit or defeat, and then resolve to the state the hit clip shows; otherwise the item teleports.
11. **Cut to idle only after the last drawing** of a non-loop clip. Every primary, secondary, special and exit ends on its rest pose; for all characters jump 7 and dodge 7 equal idle 0, and powered_jump 7 and powered_dodge 7 equal powered_idle 0.

## Feet

A foot that moves more than 3 px between drawings with both soles down skates. `anim.unskate(keys, P0)` lifts the moving foot 2.5 px in the drawing where it moves, lets one foot move per drawing (the other follows in the next) and appends a lifted in-between if the clip ends mid-step. Run it over the non-loop clips at the end of `anim_<id>.py` (see anim_bramble.py). For a guard, which must stay 8 drawings, bring one foot home in drawing 5 and the other in 6 so nothing is appended.
