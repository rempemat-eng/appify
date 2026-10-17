# C6: reproducible artwork

Run `npm run check:art-repro` with Node dependencies installed, Python 3.12
and Pillow 12.3.0 (`python3 -m pip install 'Pillow==12.3.0'`). `PYTHON` may
select another Python executable. CI pins Pillow and the action revisions.

The check copies the current tracked source into a private temporary Git index.
It does not change the caller's working files, staging area, artwork or saves,
including when the caller has uncommitted work. The temporary copy is removed
after success or failure. Existing generators may also write their usual
diagnostic previews under `/tmp`; supported preview overrides are redirected
inside the disposable workspace.

It runs all six production entry points: garden, pets, battle, worlds,
vignettes and icons. The other Python modules supply their shared drawing
functions; the standalone prop contact sheets are not production generators.
It formats all seven generated TypeScript modules with the installed oxfmt,
rejects any changed/deleted tracked bytes or new uncommitted generated files,
then checks the regenerated sprite outlines. A failed generator never skips
the remaining generators, formatting or the sprite diagnostics, and cannot
produce a passing result.

`npm run check:art-repro-test` tests isolation and failure detection with real
Git/filesystem boundaries and substituted generator processes. It requires no
Python and also runs in `npm run verify`. It does not prove artwork quality.
The **Art reproducibility** workflow runs the actual Python pipeline on PRs,
main pushes and manual dispatch. Main is not changed by the workflow.

## Resolved feedback: vignette regeneration

Claude repaired `scripts/art/vignettes.py` on main
`e2f4057b48724f070f4645bc5eb260b4f34d13a7` (17 October 2026), using the
current `garden_props` and `world_props` APIs. C6 integrates that source and
all merged C5/C7 work unchanged; it does not modify a generator, an asset or
a visual component.

On the integrated source, Python 3.12.14 and Pillow 12.3.0 regenerate all six
production entry points without tracked drift or new generated files.
Formatting all seven generated TypeScript modules preserves their bytes,
and all 102 regenerated sprite outline checks pass. The repaired vignettes
use a 432 by 300 art frame exported at 2x; checking reproducibility is not
visual approval or a phone-memory measurement.

The original report on `abc09449132f27348129dbdc5ac75561933a5808` caught an
`AttributeError` from the retired `garden.pine` API. That was a real failure,
not a guard exception to waive. Its repair is now checked by the same guard;
no baselines or failure handling were relaxed. The existing `npm run art`
still omits icons; this dedicated guard explicitly covers them.

C7's image report and regression checks remain intact in `package.json`.
`npm run verify` runs both the image-report tests and the 267 guard boundary
assertions; the separate Art reproducibility CI job runs the real Python
pipeline. Matching CI and screenshot evidence is recorded on PR #16.
Regeneration proves source/output agreement, not native performance, device
behaviour, animation scheduling or visual polish.
