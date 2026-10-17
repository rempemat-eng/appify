# C6: reproducible artwork

Run `npm run check:art-repro` with Node dependencies installed, Python 3.12
and Pillow 12.3.0 (`python3 -m pip install 'Pillow==12.3.0'`). `PYTHON` may
select another Python executable. CI pins Pillow and the action revisions.

The check copies the current tracked source into a private temporary Git index.
It does not change the caller's working files, staging area, artwork or saves,
including when the caller has uncommitted work. The temporary copy is removed
after success or failure. Supported diagnostic preview overrides are redirected
inside that owned workspace, outside the snapshot being compared. In particular,
inherited `MAP_PREVIEW` and `ZONE_PREVIEW` cannot write to caller destinations.

It runs eight production entry points: garden, pets, battle, worlds,
vignettes, icons, mission_map and zones. The other Python modules supply shared
drawing functions. Standalone prop contact sheets, including cyber_props and
steampunk_props, are helpers, not additional production generators; zones imports
them in its own process. Each entry point gets a separate Python process.

It formats eight generated TypeScript modules, including `lib/mission-map.ts`,
with the installed oxfmt, rejects changed/deleted tracked bytes and new
uncommitted generated files, then checks regenerated sprite outlines.
The destination map composite and town, junction and neon zone grounds are
covered by the whole-tree byte comparison, not inappropriate per-sprite outline
tests. Zones currently generates PNGs only, not another TypeScript module.
A failed generator never skips the remaining generators, formatting or sprite
diagnostics, and cannot produce a passing result.

`npm run check:art-repro-test` tests isolation and failure detection with real
Git/filesystem boundaries and substituted generator processes. It requires no
Python and also runs in `npm run verify`. It covers mission-map TypeScript drift,
zone PNG drift, unexpected zone output, failures of both new entry points and
preview overrides that actually write into the owned temporary directory.
These checks do not prove artwork quality.

The **Art reproducibility** workflow runs the actual Python pipeline on PRs,
main pushes and manual dispatch. Main is not changed by the workflow.
The existing `npm run art` omits icons, mission_map and zones; this dedicated
guard explicitly covers all three as well as the older entry points.
C7's image report and regression checks remain intact in `package.json`.

## Integrated source and evidence

Claude repaired the vignette prop API on main
`e2f4057b48724f070f4645bc5eb260b4f34d13a7` (17 October 2026).
The original `AttributeError` from the retired `garden.pine` API was a real
failure, not an exception to waive. No generator, asset or visual component is
authored in C6, and no baselines or failure handling are relaxed.

This follow-up incorporates main
`7d60250be5e2ccf36326f03f6e7cbf81d9918b61`, including L1's destination map,
its terrain grid, the seamless garden border and the three zone concepts.
The guard's explicit entry-point list must grow when another production
generator or generated TypeScript module is introduced.

Exact-source local checks, matching CI, screenshot artifacts and preview links
are recorded on PR #16. Regeneration proves source/output agreement, not native
performance, resident memory, device behaviour, animation scheduling or visual
polish. Screenshot and native-generation jobs do not establish physical-device
or multiplayer testing.
