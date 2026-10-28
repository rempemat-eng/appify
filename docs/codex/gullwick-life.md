# Gullwick settlement-life planning

X3-gullwick/r1, slot=editor-data. Base: continent-v53 `911edac6173ebf4398bcbf54b6171e4e68e62e13`.
Claude A opened X3 in issue 149 comment 6467789932. This is one town's first planning packet, not whole X3 completion.

The existing town format already supplies residents/routines and `x3_notes`. Gullwick has eight occupied buildings,
one district, six streets, no square and no workplace buildings. Its authored households are farming, fishing,
carting and craft households. Those roles, all geometry, themes, purposes and the original notes remain unchanged.
`game/world/villager.gd` already presents idle/work/talk; this packet changes no runtime or clock code.

Each occupied home receives one provisional representative with a placeholder name. This is coverage of authored
households, not eight inhabitants or eight simultaneously visible NPCs. Workplace stays null/deferred because the
source supplies no matching work building. Morning/day/evening/night are proposed ordering labels only. The day
destination is the home's existing frontage street; other phases refer to home. No off-street destination,
commute route, duration, production clock phase, named cast identity or new story is asserted.

Animal and working-prop instance lists remain empty and explicitly deferred: Gullwick has no specific authored
species/count/placement or approved kit IDs. The general coastal habitat brief does not establish those inputs.
The source geometry itself reports one dead end; planning references do not prove path connectivity, walkability,
clear doors, wildlife habitat or a lively camera view. The packet cannot be activated as production data.

## Checks

From the repository root:

```sh
git show 911edac6173ebf4398bcbf54b6171e4e68e62e13:docs/vision/research/blockout/towns/gullwick.json > /tmp/gullwick-source.json
python3 -m scripts.settlement_life.check docs/vision/research/blockout/towns/gullwick.json --source /tmp/gullwick-source.json
python3 -m unittest scripts.settlement_life.test_check
python3 scripts/review/town_plan.py --town gullwick
```

The life checker rejects missing/duplicate residents/phases, unknown places, cross-home destinations, changed layout,
role/district drift, invented workplaces, population claims, production timing and activation. It is standalone,
not wired into the shared package/check list. Its tests use the genuine pinned Git source, not a regenerated layout.
The original town checker remains unchanged. Malformed input exits 2; valid planning exits 0; findings exit 1.

Claude A next: review the household coverage, supply names and work sites or approve explicit non-building work
destinations, set animal/prop inputs and production phase mapping, then coordinate scene/routine integration with
the runtime owners. Source refreshes must explicitly preserve this life block: the upstream layout generator still
initialises residents/routines empty. No generator edit or regeneration guarantee is included here.
