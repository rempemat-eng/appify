# Kit relations and physical validation

W5/W6 engineering implementation, based on `claude-a/world-editor` at
`04228475cbd9fb76e0a0a9af52240d7e40a5d858`. Claude retains design and art review.
The shared cases are engineering fixtures. They do not replace the first thirty
authored cases promised in `docs/world-editor.md`, or approve any library piece.

## Placement API

`scripts.art.kit.relations` and `game/world/terrain/relations.gd` expose
`check_zone(plan, library, materials)` and `check_placement(plan, candidate,
library, materials)` (`evaluate` is an alias). Omitted registries load the source
piece files and material manifest. Explicit empty registries remain empty.
Both return ordered `{check, message, at}` findings in the input coordinate units.
They do not mutate their inputs.

`check_zone` validates the completed plan, including minimum counts.
`check_placement` previews insertion or same-ID replacement. It reports the
candidate's faults, newly broken constraints on other pieces, and worsening
maximum counts. Unrelated existing faults and missing minimum counts do not
prevent incremental construction. It is a preview, not a placement action.

All twelve schema relation names and ground, tier, orientation, stage, clearance,
snap and count constraints use `game/kit/schema/relations.cases.json`. Explicit
`piece:`, `role:`, `material:`, `surface:` and `anchor:` targets avoid ambiguous
names. Unknown targets and malformed plan data fail closed.

Two source-backed interpretations remain proposals for Claude's review:

- `not_on`, `not_near` and `not_overlap` express bans in either constraint list.
  Existing rocks use `forbids: not_overlap`; double negation would allow overlap.
- `under` a material or surface requires the footprint's complete north boundary
  below that terrain. Existing waterfall records explicitly require water above
  the entire fall. `under` a piece or role instead tests its authored overhang.

Proximity uses cell distance; directional requirements use the authored cardinal
facing. Facing does not rotate geometry because current `KitPiece` does not
rotate its collision or art. Footprint offsets are anchored at the foot's cell;
an absent footprint uses the foot cell. No sprite-sized solid is invented.

## Physical validation

`scripts.review.kit_scene.check_zone` combines placement, cell-native checks and
`ground_rules.check_plan`. Findings add `severity` and use world pixels for
review. `to_ground_plan` preserves route and water masks as exact `cell_regions`;
it does not infer polylines from an arbitrary tile-mask lab. Existing authored
paths and routes retain their original painted-plan checks.

The physical checks include water ends, tier crossings and falls, decks, precise
solids and bounds, spawn/door access, fire on a hearth, broken-stage debris,
clutter, flow direction and uphill flow. Scale uses the existing
`audit.size_class` binding to the size guide. Unclassified pieces remain explicit
advisories rather than being described as scale-audited. Concepts and retired or
rejected records are faults; candidate/gated records retain the prototype's
advisory policy unless `ship` is true. This validator does not grant editor
placement permission or promote approvals.

Piece/spawn/anchor coordinates default to texels; `coordinate_space: cells`
normalises them at ingress. One cell is 24 texels or 8 world pixels. Door
rectangles always use cells. Source collision/deck metadata uses world pixels;
sprite dimensions use density-three texels. Normalisation here does not change
the Python bake/walk consumers, which still need their own cell-coordinate intake
before a cell-authored plan can ship.

```sh
python3 -m unittest scripts.art.kit.test_relations scripts.review.test_kit_scene
python3 -m scripts.review.kit_scene kitlab --check --json
npm run review:scene -- game/kit/zones/kitlab.json --no-render
npm run check:godot
```

An explicit exported JSON target receives a data review, including malformed
input failures. A registered zone retains its normal visual review and gains kit
findings from its authoritative plan, or the explicit `--plan` export. Export
scene edits before review. `check:kit-scene` reports all stored kit plans; other
prototype plans can expose pre-existing metadata/placement faults and require
their owners' corrections. No findings are suppressed to make those plans pass.

The GdUnit suite checks shared relation verdicts/messages, the physical fixture
cases through the production Python validator, and a real Godot scene export
through its CLI. The Python bridge needs only the standard library. The pinned
editor base's pre-W2 exporter requires a destination template; that bridge test
retains the actual lab template. PR #305 separately covers fresh-path lossless
exports. Rendered dock interactions, artwork quality, devices and combined
W1/W2/W3/W4/W7 integration require their own evidence.
