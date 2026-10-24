# MyGame: engine and art workflow

Earlier Character Studio investigation. For the current Cairn room, animation dimensions and validation, use `README.md`, `COMBAT_RESEARCH.md` and `VALIDATION.md`; the measurements below describe the preceding Nix rebuild.

Research checked against official engine documentation and original tool documentation on 24 October 2026. This is an engineering and art-direction assessment for a small prototype, not evidence of production readiness.

## What failed in the first attempt

The previous scene used an 80-pixel frame, a 0.5 sprite scale, a 2.1 camera zoom and a 2× window enlargement. The combined enlargement was **2.1 screen pixels per source pixel**. A source pixel therefore could not consistently occupy a whole number of screen pixels. The sprite already requested nearest-neighbour filtering, so another filter toggle would not have repaired the missing character detail.

The camera also continually eased towards a position influenced by Nix's movement. The background moved even during ordinary walking. This was an unnecessary comfort risk in a small training arena. Its reduced-motion switch then froze idle and walking frames, removing useful movement feedback.

The more general mistake was treating a working engine export and numerous logic assertions as sufficient evidence of visual quality. Those checks could establish that actions triggered and collisions worked. They could not establish that a face was readable, a walk was convincing or the camera was comfortable.

## Engine choice

**Continue this experiment in Godot.** Its existing 2D nodes cover the work needed here: character movement and collisions, sprite-sheet animation, reusable actor scenes, tile layers and export. Its text resources and command-line interface also allow both human and agent editing without inventing a replacement scene editor.[1–4]

| Tool | Best use for this project | Trade-off |
|---|---|---|
| Godot | Desktop-first 2D action RPG with editable scenes and an eventual native build | Existing Expo gameplay and application services would need a planned port or integration. This sample does not demonstrate that migration. |
| Phaser | Browser-first game retaining JavaScript/TypeScript skills | Its pixel-art settings address sampling and pixel placement, but detailed source art and good animation remain separate work.[5] |
| Defold | Compact cross-platform game with strong editor/runtime automation | Its official agent interfaces are unusually useful, but changing to Lua and new resources is another port. There is no immediate reason to do that before judging the Godot rebuild.[6] |
| Pixelorama | Free, editable pixel-art and animation source | It complements the engine. It does not replace movement, combat or scene logic.[7–8] |

Eastward is a visual reference, not a reason to copy an engine choice. Its official FAQ identifies a custom C++/Lua engine based on MOAI; its publisher describes original detailed pixel art combined with lighting.[9–10] The practical lesson is to budget for artwork and animation, rather than expect engine settings to produce that appearance.

## Rendering and camera decisions

For strict pixel art, Godot recommends a fixed design viewport, `viewport` stretching and integer scaling. A **960×540** design becomes **1920×1080 at exactly 2×**. A 640×360 design instead becomes FHD at 3×, with less source space for the same composition. Neither choice adds drawn information to a small sprite. Higher design resolutions need artwork appropriate to them.[11]

This rebuild uses a 960×540 `viewport` with integer stretching. It retains a **fixed 2× camera zoom** to preserve the small world's existing coordinate system. Nix's 0.5 sprite scale cancels that zoom: each source pixel occupies one internal pixel and exactly two screen pixels at FHD. The camera stays at `(160, 91)`. New frames use 128-pixel cells with an approximately 96-pixel drawn character, giving roughly 192 screen pixels of height at FHD. The physics body moves continuously; the visual child rounds the feet to half a world unit, corresponding to one internal pixel. The background's 0.5 scale gives the same 2× final enlargement; the dummy's 0.75 scale gives a 3× final enlargement.

Use lossless texture imports and nearest filtering for the pixel layers. Godot 4 controls filtering through CanvasItem properties or a project default, not through an old Godot 3 import switch.[12]

Use one fixed camera for the training scene. Remove camera shake, tracking drift, camera rotation and unsolicited zoom. Keep weapon animation, walking and local hit feedback. A later large world may need scrolling, but that should be prototyped independently with deliberate room framing and a comfort option. Game Accessibility Guidelines specifically identify shake, tilting, blur and unexpected camera movement as possible barriers to play.[13] This is a design response to the reported discomfort, not a claim that any configuration guarantees comfort for everyone.

## Art pipeline

1. Establish a front, side and back character design with a stable silhouette, palette and equipment. Approve it **at gameplay size**, not only as a large portrait.
2. Allocate real source pixels to the face, hair planes, hands, clothing seams, weapon and boots. Draw that information. A larger canvas filled by the same enlarged small drawing is not additional detail.
3. Keep an editable layered source in Pixelorama. Use separate character, shadow and effect layers, and animation tags for idle, walk, fire, guard and other actions. Its saved project preserves layers and tags; exported PNGs are engine assets, not the sole master.[7–8]
4. Export sprite sheets and frame metadata consistently. Pixelorama exposes frame ranges, sheet exports, layer splitting and JSON through its CLI.[8] Keep this export step reproducible so a source edit does not require manually rebuilding every animation resource.
5. Preserve a common foot pivot across frames. Store muzzle and effect attachment anchors separately from the image bounds. Cropping or packing must preserve those offsets. Verify directional frames against the same ground contact line.
6. Inspect contact sheets and slow playback. Check foot sliding, shape wobble, equipment switching sides, unintended size changes and frame seams. A contact sheet should show coherent poses, not merely many distinct images.

The first five steps create a repeatable workflow; the final step still needs visual judgement. Automated assertions can catch wrong dimensions or missing anchors, but cannot certify attractive anatomy or convincing motion.

### What Eastward's in-game characters actually do

The comparison here uses **gameplay characters**, not the larger promotional cast portraits. Three official 1920×1080 images were inspected: the stairway city scene, an indoor shop scene and the warm-lit village scene.[16] Crops were enlarged with nearest-neighbour sampling only for inspection. These are published JPEG screenshots, some visibly resampled; they do not establish original sprite dimensions, palette counts or exact source-pixel allocations.

Two additional sprite copies from the player-maintained Eastward Wiki were downloaded and measured independently.[19] Every aligned 3×3 RGBA block in each file is exactly constant. Taking one pixel per block and enlarging with nearest-neighbour sampling reconstructs each downloaded image with byte-for-byte identical pixel data:

| Downloaded sprite copy | PNG dimensions | Losslessly recoverable pixel grid | Non-uniform 3×3 blocks | Distinct visible colours |
|---|---:|---:|---:|---:|
| John | 93×162 | 31×54 | 0 of 1,674 | 20 |
| Sam | 78×108 | 26×36 | 0 of 936 | 12 |

These are measurements of **these two distributed files**, not an assertion about every sprite, animation frame, rendering resolution or original internal game asset. The wiki copies are secondary distribution evidence, while the exact grid and colour counts above come from the downloaded pixels. Transparent colours are excluded from the visible-colour count.

This materially qualifies the earlier resolution diagnosis. Original Nix's south-facing idle frame has a drawn bounding box of **24×52 pixels**; the east-facing one is **19×52**, with 37 and 39 visible colours respectively. Nix was therefore already similar in source height to the recoverable John grid. Its narrow silhouette, small facial allocation, weaker shapes and fractional display scaling are stronger explanations of poor readability than height alone. A taller redraw may help MyGame's chosen presentation, but simply doubling the resolution is not a demonstrated requirement for Eastward-like clarity.

The following observations are visual analysis of those images, not statements made by Pixpil:

| Visible feature | Practical implication for MyGame |
|---|---|
| John reads through dark spiked hair, a beard, broad shoulders and an orange vest. Sam reads through a much smaller body, a large white-hair silhouette, a dark dress and red footwear. | Give each established character two or three identifying features that survive a small thumbnail. Equipment should change the outline, not just add markings inside it. |
| Heads and hair occupy substantial space. Adults and children use noticeably different proportions; the NPCs include narrow faces, large noses, broad jaws and squat bodies. | Preserve the roster's identity and vary body/head shapes. Avoid giving everyone the same heroic mannequin with different colours. |
| Faces are economical: clear eye marks, a nose or mouth indication, with hair, beard or glasses doing much of the identification. | Allocate space for a legible expression. Do not attempt portrait-level eyelashes, tiny teeth or facial gradients that disappear at play size. |
| Clothing is organised into large colour masses with selected borders, cuffs, pockets or folds. Hair is grouped into clumps. | Use deliberate connected pixel clusters and quiet interior areas. More texture is not automatically more detail. |
| Dark contours separate limbs, clothing and faces; restrained highlights describe form. Strong environmental light shifts the entire scene's colours. | Establish readable base colours and value separation before adding a restrained lighting pass. Avoid relying on glow to explain the anatomy. |
| In the side-view village pose, hands, bent legs, clothing and the hair profile are readable without a particle trail. | Pose and articulation should explain the action. Keep feet, elbows and weapon direction legible without camera movement or excessive effects. |

This points towards **greater clarity and stronger design**, rather than merely a denser sprite. The new 128-pixel cell is a MyGame production choice, not an alleged Eastward specification. For each character, check a normal-size silhouette, a greyscale view and the actual arena view before approving additional detail.

Pixpil's own workflow supports that emphasis: the developer interview describes Aseprite assets separated into natural structural parts and individually prepared for lighting.[17] In another interview, artist Hong Moran stresses a memorable distinctive feature in each character and environment, while the team describes tools that automate asset handling.[18] Neither interview supplies a universal sprite size or a recipe for imitating its characters.

## Animation and scene structure

Use `AnimatedSprite2D` with `SpriteFrames` for discrete, authored frame animation. Godot also supports animating sprite-sheet frames with `AnimationPlayer`.[2] Keep gameplay state authoritative: idle, locomotion, attack, guard and recovery should have explicit entry and exit rules. A visual animation should not accidentally reset every frame because movement input is still held.

Attack timing needs a single clear contract: anticipation, release, recovery and completion. Emit a shot once at the release event, and use the same declared timing in tests. Keep muzzle anchors directional and action-specific. Use `AnimationPlayer` when a sequence must coordinate frames, sound and attachment properties. Introduce `AnimationTree` when layered transitions or blend spaces justify it; it uses an AnimationPlayer's animations rather than replacing their source.[14]

Suggested production organisation:

```text
actors/nix/       actor scene, controller, frame resources and anchors
combat/           reusable projectiles, hit effects and target logic
world/            room scenes, tile layers, props and entrances
ui/               CanvasLayer interface and input hints
art-source/       editable layered masters and palettes
tools/            deterministic export and validation scripts
tests/            movement, action timing and scene smoke checks
```

Keep the collision body at the feet and animate the visual child. Move a CharacterBody2D through its movement methods in the physics callback; use floating motion mode for top-down behaviour.[1] Keep the interface outside the world camera's transform.

## Building the world

The existing painted courtyard can remain a prototype backdrop. It is quick to load and useful for a contained visual comparison. Its weakness is that painted boundaries, visible depth and collision geometry can diverge.

For expanding production levels, use `TileMapLayer` for terrain and repeatable ground structure. Godot's tile workflow supports collision, navigation and occlusion information as well as painting large layouts efficiently.[3] Use reusable prop scenes for interactive machinery, doors and animated objects. Put foreground occluders on an intentional separate layer and test them against actor depth sorting. Avoid rebuilding the entire world as a single image when parts need independent behaviour.

## Collaboration and verification

Agree on one owner for runtime controllers and another for art resources during a change. Exchange explicit contracts: frame dimensions, names, foot pivot, muzzle coordinates, action durations and effect layers. An art change should not silently alter gameplay reach or save data. Work on isolated branches and integrate a small reviewed scene before a broad migration.

Godot supports headless runs, scripted execution, exports and deterministic movie capture from its CLI.[4] Use those interfaces for repeatable checks, then inspect the actual rendered result. For this sample, the meaningful checks are fixed camera transforms throughout play, movement and wall collisions, once-only shot release, correct anchors, readable UI and crisp output at FHD. Also inspect a short idle/walk/fire capture and still crops at native size.

Keep browser testing as a convenient access route. Godot's documented web configuration is GDScript with the Compatibility renderer; single-threaded export is the preferred default and avoids cross-origin-isolation requirements. Native builds remain a separate validation target.[15] Software-rendered browser tests cannot establish performance on the player's computer.

### Applied in this retry versus subsequent work

The retry targets a steady camera, an intentional FHD scaling path, clearer character artwork, maintained locomotion animation and local combat feedback. Consult `VALIDATION.md` for what was actually checked in the delivered build.

The layered art pipeline, a proper tile-based world, broader animation authoring, larger level transitions, native device performance and integration with the main game are **subsequent production work**. A successful training-yard scene is evidence about the workflow, not completion of those tasks.

## Sources

1. [Godot 4.5: CharacterBody2D movement](https://docs.godotengine.org/en/4.5/tutorials/physics/using_character_body_2d.html)
2. [Godot 4.5: 2D sprite animation](https://docs.godotengine.org/en/4.5/tutorials/2d/2d_sprite_animation.html)
3. [Godot 4.5: TileSets and TileMapLayer](https://docs.godotengine.org/en/4.5/tutorials/2d/using_tilesets.html)
4. [Godot 4.5: command-line interface](https://docs.godotengine.org/en/4.5/tutorials/editor/command_line_tutorial.html)
5. [Phaser: rendering configuration](https://docs.phaser.io/api-documentation/typedef/types-core)
6. [Defold: using coding agents](https://defold.com/manuals/ai-agents/)
7. [Pixelorama: saving editable projects and exporting](https://pixelorama.org/user_manual/save_and_export/)
8. [Pixelorama: command-line exports](https://pixelorama.org/user_manual/cli/)
9. [Eastward: official FAQ](https://eastwardgame.com/faqs/)
10. [Chucklefish: Eastward's original art and development](https://chucklefish.org/blog/introducing-eastward-by-pixpil/)
11. [Godot 4.5: multiple resolutions and integer scaling](https://docs.godotengine.org/en/4.5/tutorials/rendering/multiple_resolutions.html)
12. [Godot 4.5: image imports and filtering](https://docs.godotengine.org/en/4.5/tutorials/assets_pipeline/importing_images.html)
13. [Game Accessibility Guidelines: camera movement and comfort](https://gameaccessibilityguidelines.com/avoid-or-provide-option-to-disable-any-difference-between-controller-movement-and-camera-movement/)
14. [Godot 4.5: AnimationPlayer and AnimationTree](https://docs.godotengine.org/en/4.5/tutorials/animation/animation_tree.html)
15. [Godot 4.5: exporting for the web](https://docs.godotengine.org/en/4.5/tutorials/export/exporting_for_web.html)
16. [Eastward official gameplay image gallery](https://eastwardgame.com/media/): [city stairway](https://eastwardgame.com/wp-content/uploads/2023/10/eastward-features-1.jpg), [shop](https://eastwardgame.com/wp-content/uploads/2023/10/eastward-features-3.jpg), [village](https://eastwardgame.com/wp-content/uploads/2023/10/f4-small-town-life.jpg)
17. [Pixpil developer interview: Eastward's creators share insights on making pixel art adventures](https://www.gamedeveloper.com/art/eastward-s-creators-share-insights-on-making-pixel-art-adventures)
18. [Pixpil artist and developer interview: Road to the IGF](https://www.gamedeveloper.com/business/road-to-the-igf-pixpil-s-i-eastward-i-)
19. Downloaded sprite copies measured directly: [John file record](https://eastwardwiki.com/File:John.png), [John PNG](https://eastwardwiki.com/mediawiki/images/8/82/John.png), [Sam file record](https://eastwardwiki.com/File:Sam.png), [Sam PNG](https://eastwardwiki.com/mediawiki/images/9/94/Sam.png). These are player-maintained wiki copies, not an official specification. Eastward artwork remains Pixpil's work and is used only as a research reference, not as MyGame artwork.
