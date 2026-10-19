# C23: exported world-logic guard, first slice

Baseline: main `0798b8287dbd1a70617183b2ca1bd5f7d203121d`. This is an
engineering check over the current generated exports, not a terrain redraw or
proof that every part of the world is physically logical. It does not depend on
unmerged C22, PR29 or PR36. No navigation, save, reward or permission changes.

`npm run check:world-logic` runs negative fixtures and then inspects the actual
`lib/zone-maps.ts` exports. It is included in `check`, hence `verify`, without
changing C22's `check:world` integration point.
`node scripts/check-world-logic.cjs --json` provides structured findings and
coverage. PNG imports are opaque paths; no app or generator is executed.

## What this slice checks

It validates dimensions, all exported terrain/walk rows, objects, stands, unique
layout membership (including negative coordinates), adjacent port declarations
and spans before inspecting the data. Malformed or newly unsupported terrain
classes fail closed instead of being silently treated as ground.

The diagnostics intentionally match the current `world_lint.py` approximations:

- Ground/floating footprints on water or lava, including narrow trunk footings.
  Ground-on-water is more than 34 per cent, ground-on-lava more than 20 per cent,
  and floating-on-land less than 50 per cent water, matching the generator.
- Path components of at least 12 cells with no tile edge, named stand or nearby
  prop proxy. This does **not** prove that both ends reach meaningful nodes.
- Path, water and lava continuity across adjacent exported terrain strips:
  three cells deep, mismatches of at least four cells (16 art pixels).
  The tolerances mirror the generator; they are not pixel-perfect alignment.

Known findings live in `scripts/world-logic-known.json`, initially empty.
Exceptions require the exact zone, kind, object/seam identity, bounds and a
reason. New findings and stale exceptions fail. Do not auto-baseline a failure.
Changes to the thresholds or classification require review alongside Claude's
generator; this check never edits it.

Current main: 29 exported zones, 799 objects, 763 tested footprints, 45 path
components, 24 seams with terrain on both sides, zero findings and no waivers.
The report separately counts skipped supported (5), wet (15), overhead (15) and
off-tile (1) footprints. Those counts are omissions, not successful validation.

## What remains before C23 is complete

The requested rulebook has more meaning than today's lossy five-class export
(`~ ! ^ = .`). Keep this PR marked **taken**, not complete:

| Rule | Covered here                      | Still needed from Claude's exports/review                                      |
| ---- | --------------------------------- | ------------------------------------------------------------------------------ |
| 1/2  | Ground/floating footing proxy     | Wet banks; supported structures' drawn support/abutment geometry               |
| 5    | Not certified                     | Bridge deck/underlying water or gap, both abutments and continuing path nodes  |
| 6    | Disconnected path-component proxy | Explicit path graph, grades, nodes and both endpoint identities                |
| 7    | Port shape/adjacency only         | Frame breaks, path through each intended exit; open land is not a gate         |
| 9    | Not certified                     | Distinct bank, snow, sand, ash, crust, climate and elevation/contact semantics |
| 10   | Water/path/lava seam proxy        | Rail and frame networks, terminal identities, actual border ground tone        |
| 11   | Stand shape/bounds only           | Door/hotspot associations and reachable approaches                             |

The garden has no `zoneTerrain` export. Its four shared seams are explicitly
omitted from semantic comparison rather than inventing flat ground.
`zoneTone` is a base palette value, not the actual six-pixel ground strip, so
this slice does not claim tone continuity from it. Rails cannot be recovered
reliably from `^` or sprite names. Neither a generic supported placement nor a
nearby prop certifies a bridge, doorway or station endpoint.

Claude: please keep the current open-land direction in `world-ports.md`.
No fence, narrowing or artificial screen-sized boundary follows from a port.
For the remaining checks, expose the semantic structures above or retain a
separate explicitly reviewed generator/pixel check. C27's named circuits over
the real region walk grid and C28's navigation ownership are separate tasks.

## Validation boundaries

Negative fixtures cover ground props in water/lava, floaters on land, trunk vs
canopy footing, isolated paths, both seam orientations and final-edge runs,
threshold tolerances, malformed data and exact/stale exception handling.
The actual CLI and exported-data collector are also exercised together, including
non-zero exits for a bad map, a stale exception and a missing terrain export.
Unsupported placements are counted, never silently presented as checked.

This is not browser, phone, native runtime, rail/bridge geometry, visual-quality,
screen-reader, real backend or multiplayer validation. No existing art, UI,
movement rules or player data is changed.
