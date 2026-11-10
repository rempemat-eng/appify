# Eastward-style characters at 1080p: rules for the cast

Matt asked (24 Oct, 23:54) for the characters "in the eastward style but 1980". I read 1980 as 1080: native 1920x1080, art on a 960x540 grid shown at exactly 2x, and exactly 4x on a 4K Mac.

This first pass draws Bramble, Iona, Pendle and Cairn in code, with Python, Pillow, NumPy and SciPy. No image generation was used. Everything here is reproducible from `src/`.

## Files

- `lineup.png`: each character's Codex east idle next to our south, north, east and west idles, all at 4x.
- `scene_1080.png`: the four in the density-3 woodland, composed at 960x540 and scaled exactly 2x. The native frame is `src/scene_960_native.png`.
- `bramble_walk.mp4` (14.5 s) and `bramble_shot.mp4` (5.6 s, the shot twice): 1920x1080 at 60 fps, with a still camera, whole art pixels and nearest 2x. They are H.264 yuv420p. Each art pixel is a 2x2 block aligned to even coordinates, so chroma subsampling does not smear colour edges.
- `src/`:
  - `ew.py`: the rig and render rules.
  - `parts.py`: shared limbs, eyes, boots and the walk table.
  - `palette.py`: the materials.
  - One module per character, plus `anim_bramble.py`.
  - `scene.py`, `media.py` and `lineup.py`.
  - `preview.py <module> S,N,E,W`: renders a 5x review sheet.

## What we measured in Eastward

The measurements come from local screenshots only, which never go into any deliverable.

- **Height on screen.** Adults stand 14.5 to 17.6% of the screen height: John is 15.3%, a market NPC 14.5% and the big cook 17.6%. Kids are about 9%. On our 540-line grid that gives about 78 to 95 px. We use **74 px for an average adult**, crown to sole. That stays inside the brief's 60 to 80 px and keeps people in scale with our world props: the bench is 48 px tall and the oak trunk about 90 px. Bigger builds scale up (Cairn is 88 px plus his moss), and weapons may rise above the head (Iona's spear is 98 px).
- **Eastward's own pixel.** One Eastward pixel is about 4.5 screen pixels at 1080p, which is about 2.2 of our art pixels. So our grid has about twice Eastward's resolution. We keep Eastward's proportions and cluster sizes, not its pixel size: features are at least 2 px clusters, and outlines are 1 px to match our world kit.
- **Proportions.**
  - Big heads: the head (hair and face) is about a third of the height, and about as wide as the shoulders.
  - Short legs: the hip sits at about 30% of the height.
  - Chunky boots: 8 to 10 px long and 7 px tall.
  - Mitten hands: about 7 px round, with no fingers at rest.
  - Torsos are simple barrels.
  - Silhouettes are clear, with one defining item (a bow, spear, hat or moss).
- **Colour.** Each material uses 3 or 4 tones. The outline is a dark tone coloured by the material inside it, never pure black. A whole adult uses about 30 to 45 colours.
- **Shading.** Light comes from the upper left. There is a thin light rim on the upper-left edge, a flat base, and a wider shadow band on the lower right. Heads, hats and capes cast a one-tone shadow onto what is below them. Eastward has no dithering and no noise.
- **Faces.**
  - Eyes are dark bars, 1 Eastward pixel wide and 2 tall (2x3 or 2x4 of ours), often with a pale glint.
  - Brows, a nose dot and a blush mark complete the face. Mouths are mostly absent.
  - Expression comes from brows and eye height, not detail.
- **Motion.** Poses read in silhouette. A walk bobs the body 1 px down on the contact-to-down drawings and 1 px up on the up drawings. Arms swing against the legs. Hair and cloth trail a little.

## The rules (`ew.py`), the same for every character

1. **Parts, not pixels.** A character is a list of parts. Each part has:
   - a mask, built from ellipses, tapered capsules, polygons and two-segment limbs;
   - a material, a depth `z` and a few shading settings.

   Faces, glints, buttons and the bowstring are explicit pixels placed last.

2. **Four tones per material**: deep, shadow, base and light, plus an optional shine kept for metal glints and lamps. The outline tone is the deep tone pulled 62% toward the world ink `#1E1917`. Shadows lean violet and lights lean warm, like `art/materials.json`. All 32 ramps are in `palette.py`. Reuse them for shared materials (skin, leather, gold, steel, brass) and add a ramp only for a new identity colour.
3. **Form light.** Each part is shaded from its own silhouette. A dome built from the distance field is lit from the upper left:
   - `rl` (1.2 to 2 px) sets the light rim;
   - `rs` (2 to 4 px) sets the shadow band;
   - `vgrad` darkens the lower part of long pieces (coats, trousers, beards).

   Because the light is computed after mirroring, west is lit upper left too.

4. **Cast shadows** (`cast=(dx, dy, strength)`). Heads, hat brims, capes, scarves and near arms drop one tone onto the parts under them, 1 to 2 px down and right.
5. **Clean clusters.** A tone island of 1 px (2 px for light and deep) inside a part is merged into its neighbours. There is no speckle and no dithering.
6. **Lines.**
   - Outer outline: 1 px and 4-connected, so diagonals stay single, in the edge tone of the material it wraps.
   - Inner lines where a part overlaps another: `hard` (edge tone) for limbs, hands, heads and gear; `soft` (deep tone) for cloth over cloth; `shade` (shadow tone) for hair clumps and moss.
   - Thin things that must not be outlined (bowstrings) use `noout`.
7. **Depth.** Far limbs are drawn one tone darker (`dim=1`). Draw order runs from back to front: back gear, far arm, far leg, near leg, torso, belt, strap, cape, near arm, hands, scarf, face, beard, hair, hat.
8. **Faces.** Each face is drawn from these stamps:

   | Feature    | How it is drawn                                                                                              |
   | ---------- | ------------------------------------------------------------------------------------------------------------ |
   | Eyes       | 2 px wide and 3 px tall (4 for younger faces), ink `#1E1917`, with a `#FFFDF5` glint at the upper-left pixel |
   | Brows      | 4x1 in the hair's shadow tone                                                                                |
   | Nose       | 2x1 light over 2x1 shadow (front), or a 2 px bump past the profile (side)                                    |
   | Blush      | 2x1                                                                                                          |
   | Mouth      | 2x1 in the deep skin tone, only on unbearded faces                                                           |
   | Robot eyes | 2x3 lamps (core, rim, warm bottom pixel)                                                                     |
   | Golem eyes | 4x2 amber slits                                                                                              |

   A blink is the bottom row of the eye only.

9. **Facings.**
   - S and N are drawn front and back.
   - E is drawn in profile, with the head turned (one eye, nose bump, ear).
   - W uses the E geometry on a mirrored x axis (`Fig(flip=True)`), with the light recomputed. Gear that really sits on one side of the body changes side. Bramble's bow (left hand), quiver strap and billhook move. Iona's spear moves to her far hand. Pendle's holster and sling move. Cairn's sprout moves. So W is never a plain mirror.
10. **Ground pivot.** The feet centre sits at (W/2, H-6) of the cell. A crouch gets shorter; nothing is stretched back to height.

## Timing

| Clip     | Drawings | Timing                                                                                                                                                                                                                                                                                                                        |
| -------- | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Idle     | 4        | 420, 260, 420, 260 ms. The upper body (chest, head, arms) lifts 1 px on drawings 1 and 2. A 120 ms blink every 3.4 to 5 s, staggered per character.                                                                                                                                                                           |
| Walk     | 8        | 100 ms each: contact, down, passing, up, then the other foot (`parts.WALK`). The planted foot moves back 3.5 px a drawing and the body steps 3.5 px with each drawing, so there is no foot slide; the cost is a 10 Hz step. The bob is 1 px down on "down" and 1 px up on "up". Arms swing at 0.55 of the near foot's offset. |
| Bow shot | 9        | 140, 120, 110, 90, 80, 300, 60, 90, 220 ms (see below)                                                                                                                                                                                                                                                                        |

The bow shot runs:

1. Ready.
2. Reach back to the quiver (anticipation). The near arm passes in front of the head.
3. Nock with the bow rising.
4. Raise and aim.
5. Half draw.
6. Full draw, held 300 ms: the anchor at the jaw, the bow limbs bent, a slight lean back.
7. Release, 60 ms: the string straight, the hand thrown back, the bow tipping forward.
8. Follow-through.
9. Settle.

The arrow travels at 760 art px/s.

## Adding the other ten characters

1. Read their identity row in Codex's `ART_DIRECTION.md`. Pick ramps from `palette.py` first, and add only the identity colours.
2. Copy the shape of `iona.py`. Write `south`, `north` and `side(west)`, and give `draw()` the same signature. Keep 74 px for an average adult, scaled by build (Clack broad, Mote slim, kids smaller). Make the head a third of the height.
3. Put every asymmetric item on its real side, and move it in `side(west=True)`. Nix's laser arm is anatomically left in every view.
4. Run `python3 preview.py <module> S,N,E,W`. Check the 5x sheet and the 2x strip, then put the character into `lineup.py` and `media.py`.
5. Before handing on, check for these faults:
   - lone pixels in fills;
   - the light on the right in W;
   - gear on the wrong side;
   - a face hidden by hair;
   - a weapon held by a hand that is behind the body.

## Honest notes: what still falls short

- **Chunkiness.** At the same screen height, Eastward's people are wider: thicker torsos and limbs, heads at least as wide as the shoulders. Eastward's outline is also about twice our weight, because its pixel is 2.2 of ours. Ours read slightly slim and fine-lined beside it. The next pass should widen bodies by about 10 to 15% and grow heads about 1 px each side. Keeping 1 px outlines is deliberate, to match the world kit.
- **Procedural shapes.** Bodies are built from ellipses and capsules, so elbows, knees and coat hems are smooth but generic. Hands are mittens in every frame. A hand-drawn pass on hands, folds and the face in profile would lift the charm most. Diagonal inner lines leave some 1 px stair steps; they are lines, not speckle, but an artist would tidy them.
- **Hair.** Bramble's curls are shaded clumps; they read as curly but a bit like cauliflower. Iona's sheen is faint and her bangs barely swept.
- **Cairn** is blockier than Codex's round boulders, and Codex's floating pebbles are left out. The slabs have rounded corners and lit facets, but they still read more as cut stone than weathered granite.
- **Pendle's revolver** shows only as a grip in the holster. The rifle is a simple barrel and stock.
- **Bramble's bow (east facing).** The bow is in his left hand, which is the far hand facing east. It sits ahead of the body and is partly overlapped. Codex shows it in the near hand.
- **Walk.** The walk is only drawn facing east (west renders from the same table, but is not reviewed). It has no heel-to-toe roll and a simple arm swing. The mantle and quiver lag is small. The 10 Hz body step is the price of no foot slide.
- **Shot.** No smear frames or release effects. The string and arrow shaft are 1 px lines, so they are faint at 2x.
- **Not tested** in the game engine, on a phone or on a real 4K display. The 4x claim is arithmetic: 960x540 times 4 is 3840x2160, with nearest scaling.

## Pass 2 (25 Oct): what changed

- **One pose-driven build per character.** `parts.Rig` projects body-space points `(fwd, up, lat)` into each facing and solves limbs in 3D, so S, N, E and W come from the same pose. A step toward the camera drops `K = 0.35` px per px. Depth decides what covers what: a hand behind the back goes under the torso, and back gear in N goes over it. The animation contract is in CONTRACT.md.
- **Cell and pivot.** Cell 160 x 144, pivot (80, 136), and the sole outline on row 135, so the packed bounds end at the pivot as in Codex's frames.
- **Bramble.**
  - He is a left-handed archer: the bow is in his right hand, which is the near hand facing east, as in Codex's art. He draws with the left, and the quiver is over the left shoulder.
  - The folding buckler is the bracer on the bow arm. It is always visible and opens for the guard.
  - The bow is visibly slung across his back for the billhook and the guard, and comes back to his hand afterwards.
  - His body is 12% wider and his head is 1 px wider each side.
  - Hands that hold something show a finger crease across the shaft.
- **Pendle.**
  - Head: cattleman hat with a pinched crown and a concho, round 3x3 lamp eyes, and a bandana over the lower face.
  - Duster: fuller, with a capelet and a back vent.
  - Body: exposed brass arms on dark ball joints, a brass chest plate, knee caps, shin guards and toe caps.
  - Gear: the revolver grip and cylinder show in the holster on his right hip. The rifle has a brass scope and is slung with its barrel up past his left shoulder. It reads in every facing: above the shoulder in S, across the back in N, and behind the head in E and W.
- **Cairn** is rebuilt from rounded boulders:
  - two great round shoulder boulders capped with moss;
  - a deep chest boulder over a belly stone and the pelvis;
  - big round fists that hang to the knees;
  - thick thigh stones on flat feet;
  - a small wedge head set low and forward, with amber slits;
  - the sprout on his left shoulder and two floating pebbles over his right.

  He is 87 px tall in idle, against 74 for an average adult. In profile he hunches forward, his head ahead of his chest.

## Honest notes after pass 2

- **The other cast members are not ported.** Iona and the ten designers' characters are still per-facing builds (pass 1 structure). They render idles but cannot be animated until they are ported to the rig.
- **Bramble's front and back actions are less clear than his profile.**
  - Facing S, the aimed bow is seen nearly edge-on in front of his chest, and the arrow points at the camera as a short stub.
  - Facing N, the body hides the bow. That is logical, but less legible.
  - Hand-drawn front aims, with the bow canted more, would read better.
- **Cairn's profile** is narrower than Codex's (about 45 px against 70). Codex's three-quarter boulders overlap more.
- **The Briarshot vine** is a chain of 1 px-outlined beads with leaves. It makes most of the lone-pixel warnings (9 to 11 in a few drawings).
- **Walk speed.** Feet stay planted only at 68 px/s. Codex's runtime moves at 92 px/s, so it needs the manifest's `walk_speed` (see CONTRACT.md).
- **Not tested** in Godot, on a phone or on a 4K display. The frames.tres resource has not been opened in Godot.
