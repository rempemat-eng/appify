# World editor dock (W3)

Enable **World editor** in Project Settings → Plugins, open a kit zone, and select
its `Ground` or another node in that zone. The World dock follows that selection.
It reads complete source definitions under `game/kit/pieces/`; the built manifest
and prop index supply the preview swatches and scenes.

- Choose a terrain swatch, then Brush (1–3 cells), Rectangle, or Route (2–3 cells).
  Drag in the 2D canvas. One completed gesture is one undo action. Escape or a lost
  left button cancels the pending gesture. Surface variants have a separate brush.
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

Terrain and placement transactions preserve cell/variant/baked state, node
ownership, ordinary gameplay nodes and W2's plan metadata. Undo remains bound to
the original scene after selection changes. Accepted edits refresh W4's derived
walk/collision child; selecting a scene alone does not install it.

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

`operations.gd` exposes `paint_cells`, `preview_piece`, `place_piece`, `validate`
and `export_plan`. The EditorPlugin delegates its corresponding non-UI API to the
same object. Operations accept the real `EditorUndoRedoManager` or a test
`UndoRedo`; injected library/factory/provider options are confined to each
configured operations instance.

## Reproduce acceptance

```sh
GODOT=/path/to/Godot_v4.7.2-stable npm run check:godot
```

The three `test_world_editor*.gd` suites cover transaction rollback/redo, approval
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
