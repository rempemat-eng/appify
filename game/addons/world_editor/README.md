# World editor dock (W3)

Enable **World editor** in Project Settings → Plugins, open a kit zone, and select
its `Ground` or another node in that zone. The World dock follows that selection.
It reads complete source definitions under `game/kit/pieces/`; the built manifest
and prop index supply the preview swatches and scenes.

What it can and cannot do today, and how that was checked, is the status section at
the top of `docs/world-editor.md`.

## Building a whole zone (10 Nov)

1. **Start a zone.** `$GODOT --headless --path game -s tools/kit_zone.gd -- --new=<zone>
--size=40x23 --ground=lawn --lab=1` writes an empty plan and its scene. Open the
   scene. Nothing in the library is approved yet, so only a lab zone has a palette.
2. **The status line** is pinned at the top of the dock. Every refusal, result and
   validation is shown there, faults before advice.
3. **Paint and place** as described below. **Select / move** (or Escape with no stroke
   under way) puts the brush down: clicks on the canvas go to Godot's own select, move
   and delete tools again. A second identical piece on one spot is refused.
4. **Godot's own tools are safe to use on pieces.** Moving a piece on the canvas or in
   the inspector, deleting or duplicating it in the scene tree, and undoing any of
   that, all refresh the walk mask, the shadows, the previews and the baked-ground
   flag (the plugin follows the editor's undo history).
5. **Gameplay.** Choose a kind (spawn point, door, talk or read area, villager, restore
   site, enemy camp), give it a name and its one detail (a door's target `zone` or
   `zone/spawn`, a speaker id, a character id, a restore id, a camp id), press _Place on
   the next click_ and click the canvas. It is one undo action. The new node is
   selected, so the rest (a verb, a talk radius, a door's condition, a camp's enemies)
   is set in Godot's inspector or by moving and duplicating its children. A spawn or an
   actor is refused on ground nobody can stand on. A door on the zone's edge is laid
   along that edge, three cells long.
6. **Validate zone**, then **Save and export plan**: it saves the scene and writes
   `game/kit/zones/<zone>.json`. Commit both. Anything under `Actors` that a plan
   cannot hold is named in both messages.
7. **Bake ground** when the layout is settled (about 20 seconds a screen; the editor
   waits while it runs).

`game/kit/zones/editor_glade.json` and its scene were built this way and are kept as a
fixture (`game/test/test_world_editor_authoring.gd`).

- Choose a terrain swatch, then Brush (1–3 cells), Rectangle, or Route (2–3 cells).
  Drag in the 2D canvas. One completed gesture is one undo action. Escape or a lost
  left button cancels the pending gesture; Escape with no gesture under way puts the
  brush down. Surface variants have a separate brush.
- Choose a piece and click to place its foot. Snapping follows `placement.snap`.
  Q/E or the Facing selector changes its authored facing metadata; sprites are
  never rotated or mirrored. The canvas shows footprint, facing and relation range;
  the status area retains the shared engine's refusal message.
- Hover or select a palette entry to read its size, placement rules, function,
  story and gameplay metadata. Use Validate zone for the full physical validator.
- Only approved definitions are eligible in ordinary zones. Explicit labs also
  accept candidate/gated definitions. Concepts, rejected and retired pieces are
  refused everywhere, including direct non-UI calls and validation of existing
  scene content. This tool never changes approval records.

Building places from the kit (round 3, 3 Nov):

- **Search and category.** Above the pieces list, a search box (every word must
  appear in the piece's id, name, role or purpose) and a category (fences, farm,
  commons, village, woodland, water) narrow the palette (226 pieces in a lab); filtering does
  not reload the library.
- **Fence runs.** Select any fence cell piece (`fence_<style>_*`) and drag along the
  run: each cell's piece is chosen by its neighbours (straights, corners, Ts, ends),
  the run's ends join a gate's ends, and existing cells of that style it meets are
  re-joined (an end becomes a corner or a T). One undo action; a refused cell refuses
  the run. Gates and stiles are still placed one at a time on their path.
  While you drag, the canvas draws the arms of the piece each cell will get.
- **Group copy and paste.** Select placed pieces (a pen, its gate and what it holds)
  and press Copy selected pieces; Paste group, then click: the group lands with its
  top-left cell under the pointer, every piece at its place relative to the others
  (fences stay on their lines, contents inside them). Each piece is checked by the
  shared relation engine against the zone with the rest of the group in it; all are
  placed in one undo action, or none.
- **Gates and stiles on runs** (round 7). With a gate or a stile selected, click a
  run: the piece replaces the straight cells it spans (a gate three, a stile one),
  snapping to the nearest straight span within two cells of the click; the cells
  either side keep their joins, now to the gate's or stile's ends. A stile goes only
  on a drystone or post-and-rail run, and its relation keeps it on a path. When no
  span fits, the status says why. One undo action.
- **Live fault overlay** (round 7). While a piece is placed, the ghost is green,
  amber (advice) or red (fault), with the failing rule's short name beside it. The
  relation engine answers at once; the full validator (kit_rules, relations,
  enclosures, check_plan, as Validate) runs on a worker thread on a crop of the zone
  8 cells round the ghost, keeping only the findings about the ghost. Crops and
  verdicts are cached and cleared whenever the scene changes.
- **Variants and the scatter brush** (round 7). V or Next variant cycles the
  selected piece's variants (sprites are never mirrored: a flip is a variant drawn
  for it). With Scatter brush on and a small piece selected (two cells or less, not
  a fence), drag over the ground: each cell decides by its own seed (the zone's name)
  whether it takes a piece and which variant, keeps a cell of clearance from every
  other piece, and is checked by the relation engine with the stroke's earlier
  pieces in place, so forbids hold. One undo a stroke; the same stroke repainted
  lands the same pieces.
- **Validate zone** now also runs `scripts/art/kit/enclosures.py` (closed loops,
  what each pen holds and needs, every stretch keeping its stock) and
  `placement_audit.check_plan` (needs a hearth or home, faces a feature, avoids wild
  woods, a fingerpost's arms along its junction), and lists every finding by its
  check.
- **Doors, paths and gates** (4 Nov, Matt's review of the farm study). Validate and
  the live overlay also run `scripts/art/kit/thresholds.py` through `check_plan`: a
  door's path is centred on its opening and straight for a cell (`door_path`), its
  threshold and swing stay clear (`door_clear`), a gate is centred on the path
  through it (`gate_path`), a path crosses a fence only at a gate or a stile
  (`path_through_fence`), and a fence meets a building at a front corner or along
  its wall foot, never in front of the façade (`fence_wall`). Doors are each
  building's `geometry.doors`. Painting a route from a door snaps the stroke's
  first two rows onto the door's centre line (one cell wider when the door's centre
  needs the other parity), and a gate clicked onto a run takes the span centred on
  the path crossing it. Both stay one undo.

Terrain and placement transactions preserve cell/variant/baked state, node
ownership, ordinary gameplay nodes and W2's plan metadata. Undo remains bound to
the original scene after selection changes. Accepted edits, and Godot's own edits
to placed pieces, refresh W4's derived walk/collision child; selecting a scene
alone does not install it. Before a save the plugin removes the walk node's
process-local owner mark from the ground, so nothing of one editor session reaches
the scene file.

Bake ground validates, saves the active zone scene, exports it through W2 and
invokes the existing painter CLI. Open the zone as its own scene before baking.
Reentrant bakes/imports and cell-coordinate plans are refused before saving: the
current painter CLI still assumes texels. Painting, placement and full validation
support either W2 coordinate space. The Python executable is `PYTHON` or `python3`.

## Interfaces and dependency pins

W3 owns this addon and `test_world_editor*.gd`. Its branch starts at
`claude-a/world-editor@04228475cbd9fb76e0a0a9af52240d7e40a5d858` and preserves these
unmodified dependency commits for combined-source acceptance:

| Dependency | PR   | Pin                                        | Used interface                                                                    |
| ---------- | ---- | ------------------------------------------ | --------------------------------------------------------------------------------- |
| W2         | #305 | `ef4bd6234c36b0e5ce4e9595286c7bea424a7276` | Static `kit_zone.gd.plan_from_scene`, `kit_zone_plan` / `kit_zone_entry` metadata |
| W4         | #304 | `2d637747ffe874f350045dfa2c5412f5723e8165` | `KitWalk.rebuild` / `write_walk`                                                  |
| W5/W6      | #311 | `c8c1a1ed63a902bb85f729fe699bf377d1033a17` | `KitRelations.check_placement`, Python `kit_scene.check_zone`                     |

Integrate/review those PRs before the W3 commit. W1/W7 and their artwork/runtime
changes are not included. `rules_adapter.gd` transports findings; it does not
implement placement predicates or physical rules. Missing/malformed providers
refuse the operation. Their design semantics and outstanding prototype findings
remain documented in `docs/codex/editor-rules.md`.

`operations.gd` exposes `paint_cells`, `preview_piece`, `place_piece`,
`place_gameplay`, `validate`, `export_plan`, `export_plan_file`, `refresh_derived`,
`sync_native_edits` and `prepare_save`. The EditorPlugin delegates its corresponding non-UI API to the
same object. Operations accept the real `EditorUndoRedoManager` or a test
`UndoRedo`; injected library/factory/provider options are confined to each
configured operations instance.

## Reproduce acceptance

```sh
GODOT=/path/to/Godot_v4.7.2-stable npm run check:godot
```

`test_world_editor_authoring.gd` holds the faults found by building a zone end to end
(10 Nov) and the fixture zone. The three older `test_world_editor*.gd` suites cover transaction rollback/redo, approval
gates, coordinate/metadata preservation, geometry and actual shared-rule
integration. The ordinary-node identity fixture guards against Godot renaming a
placed node while its plan keeps a colliding id. The real Solid/KitWalk fixture
also covers placement, collision rebuild, undo, redo, cleanup and an active-mask
PackedScene disk save/reload preserving the original collision layer. The W4
successor uses serialization-safe ownership; the W2 successor rejects malformed
plans before node allocation; W6 preserves equal-tier bridge landings.

For actual editor history and dock construction, run a disposable editor:

```sh
"$GODOT" --headless --editor --audio-driver Dummy --path game \
  res://zones/kitlab/kitlab.tscn -- --we-smoke-report=/absolute/report.json
```

This opt-in acceptance runner exercises editor transactions and restores the
scene without saving it, writes its report and exits. With a real display, omit
`--headless` and add `--we-capture=/absolute/editor.png` for a rendered screenshot.
Headless success does not establish the dock's rendered appearance.
