# C6: reproducible artwork

Run `npm run check:art-repro` with Node dependencies installed, Python 3.12
and Pillow 12.3.0 (`python3 -m pip install 'Pillow==12.3.0'`). `PYTHON` may
select another Python executable. CI pins Pillow and the action revisions.

The check copies the current tracked source into a private temporary Git index.
It does not change the caller's working files, staging area, artwork or saves,
including when the caller has uncommitted work. The temporary copy is removed
after success or failure. Supported diagnostic preview overrides are redirected
inside that owned workspace, outside the snapshot being compared. In particular,
inherited `MAP_PREVIEW`, `ZONE_PREVIEW` and `JOURNEY_PREVIEW` cannot write to caller destinations.

It runs nine production entry points: garden, pets, battle, worlds,
vignettes, icons, mission_map, zones and journey. The other Python modules supply shared
drawing functions. Standalone prop contact sheets, including cyber_props and
steampunk_props, are helpers, not additional production generators; zones imports
them in its own process. Each entry point gets a separate Python process.

It formats eleven generated TypeScript modules, including `lib/mission-map.ts`,
`lib/zone-maps.ts`, `lib/zone-assets.ts` and `lib/journey-assets.ts`,
with the installed oxfmt, rejects changed/deleted tracked bytes and new
uncommitted generated files, then checks regenerated sprite outlines.
The destination map, every zone ground and prop, and all journey layers and
vehicles are covered by the whole-tree byte comparison, not inappropriate
per-sprite outline tests. Zones now exports both walk/layout and asset modules;
journey exports its layer/vehicle module.
A failed generator never skips the remaining generators, formatting or sprite
diagnostics, and cannot produce a passing result.

`npm run check:art-repro-test` tests isolation and failure detection with real
Git/filesystem boundaries and substituted generator processes. It requires no
Python and also runs in `npm run verify`. It covers mission-map TypeScript drift,
zone PNG drift, unexpected zone output, failures of map, zone and journey entry points and
preview overrides that actually write into the owned temporary directory.
The atlas generators invoke `npx oxfmt` themselves, so the check links the
installed toolchain into its disposable copy after staging source and before
running generators. npm subprocesses run offline. Only that exact, intact
`node_modules` symlink is omitted from unexpected-output reporting; replacing it
or creating similarly named files fails. Dependencies are never staged.
Tests cover those boundaries, the new module/PNG drift and journey failures.
These checks do not prove artwork quality.

The **Art reproducibility** workflow runs the actual Python pipeline on PRs,
main pushes and manual dispatch. Main is not changed by the workflow.
The existing `npm run art` omits icons, mission_map, zones and journey; this dedicated
guard explicitly covers all four as well as the older entry points.
C7's image report and regression checks remain intact in `package.json`.

## Integrated source and evidence

Claude repaired the vignette prop API on main
`e2f4057b48724f070f4645bc5eb260b4f34d13a7` (17 October 2026).
The original `AttributeError` from the retired `garden.pine` API was a real
failure, not an exception to waive. No generator, asset or visual component is
authored in C6, and no baselines or failure handling are relaxed.

This follow-up incorporates main
`dee30c7ac009627bf6d099cb6e82d800bf8eeafb`, including the atlas prototype,
its generated zone layouts and props, journey layers, and the Snowy Ridge trail.
Claude's `check:region-walk` package entry and all generated output are preserved.
The guard's explicit entry-point list must grow when another production
generator or generated TypeScript module is introduced.

Exact-source local checks, matching CI, screenshot artifacts and preview links
are recorded on PR #16. Regeneration proves source/output agreement, not native
performance, resident memory, device behaviour, animation scheduling or visual
polish. Screenshot and native-generation jobs do not establish physical-device
or multiplayer testing.
