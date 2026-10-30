# MyGame / Character Animation Studio

Fourteen east-facing character sets, with 152 selected body drawings for twelve characters, 151 for Velvet and 160 for Pendle including his revolver reload. Total: 2,135 distinct exported drawings. The allocation is 112 base/combat/traversal drawings plus 40 powered-state review drawings (39 for Velvet, whose exit uses seven valid poses without padding). Unequal timing preserves decisive attacks; the added ordinary primary breakdowns keep the previous release and total recovery time.

## Play

Unzip this folder, open Terminal there and run:

```bash
python3 play.py
```

The downloadable studio includes a ready browser build. A Git source checkout first needs `python3 -m pip install -r requirements-art.txt`, then `python3 tools/build_animation_roster.py`, a Godot import and Web export as documented in TOOLCHAIN.md.

The included browser build opens locally. Godot is not needed to play it. Open `project.godot` in Godot 4.5.1 to edit the source. The launcher serves the included build; it does not rebuild it.

| Input | Action |
|---|---|
| [ / ] or character selector | Change character |
| 1–8 | Idle, walk, primary, secondary, special activation, guard, hit or defeat studies |
| N or clip selector | Next clip, including traversal, powered review and Pendle reload |
| J / Q | Primary / secondary in target practice |
| E | Enter a held powered equipment review; press again for the authored return |
| WASD / arrows | Move in base and powered flat practice |
| Hold Space | Guard |
| K | Jump |
| Shift | Dodge |
| T | Terrain course / target practice |
| B | Pose study / target practice |
| P | Pause / resume |
| Comma / period | Step a paused drawing |
| V | Normal / half speed |
| Loop button | Repeat the selected clip |
| C | Pose inspector |
| Tab | Demonstrate the roster clips |
| H / L | Hit / defeat study |
| M | Quiet / fuller local effects |
| R | Reset |
| F / Escape | Enter / leave full screen |

The terrain course contains stairs up and down, a raised landing, a low ledge, a bridge over a pit and tagged water, mud, wood and ice contact surfaces. Jump height is separate from the supporting floor height. A missed landing returns to the course checkpoint without adding fall damage. Combat is unavailable in the terrain course. These are isolated character test fixtures, not production map placements or new main-game traversal rules.

Powered review holds equipment until an explicit exit. It supplies idle, walk, primary, guard and exit drawings, without inventing production buff values, durations or cooldowns. Base secondaries, jumping and the terrain course are unavailable during that review because matching powered variants are not supplied. Exit the form before returning to base practice.

## Sheets and editable source

`animation-sheets/` contains fourteen transparent PNG atlases, matching JSON frame coordinates/timing/pivots and GIF motion reviews. GIFs show exported source drawings; the native preview shows the real engine course and effects.

Every set has seventeen clips: idle, walk, primary, secondary, special activation, guard, hit, defeat, jump, stair ascent, stair descent, dodge, powered idle, powered walk, powered primary, powered guard and powered exit. Pendle has an eighteenth reload clip. Ordinary walk and primary actions contain sixteen drawings. Cairn also retains his sixteen-drawing boulder throw and four-drawing hit/defeat reactions. Atlas coordinates are explicit in JSON rather than implied by one action per row.

Ordinary cells are192×192 with foot pivot(96,172). Iona uses224×192 with the same pivot to retain her spear without shrinking her body. Ashe uses 256×192 and pivot (132,172) to retain broad sword and fallen poses at the same body density. Human standing bodies target 96 logical pixels; Cairn targets 112. Full HD uses a fixed 960×540 logical viewport at exact 2× presentation. The camera never follows, tilts, shakes or pulses.

`assets/animated/<id>/frames.tres` is the native Godot resource. Its adjacent manifest records durations, release/contact frames, anchors, source selections and registration. `art-source/animated/` retains selected flattened masters and explicit retakes. Source prompts and review decisions are retained in the v3 provenance JSON. These are flattened raster masters, not layered Aseprite projects. Rebuild with `tools/build_animation_roster.py`, reimport in Godot, then export Web again. Run `tools/animation_review.py` to refresh contact boards, GIFs and the overview.

The artwork faces east in three-quarter view. North, south and west directions, powered traversal, powered secondaries, swimming, climbing and moving-platform integration remain production work. No asymmetric anatomy is mirrored to imply a completed direction. Fine contour and body-volume cleanup remains subject to art review; test counts do not certify artistic quality.

`VALIDATION.md` records the actual final checks. `ABILITY_TRAVERSAL_AUDIT.md` and `VISUAL_REVIEW_V3.md` distinguish starting defects, retakes and remaining limits. `WORLD_ANIMATION_CONTEXT.md` covers world locations and integration requirements. `COMBAT_RESEARCH.md` retains the animation/VFX reference sources. This studio does not edit the main game, saves, economy or map work.
