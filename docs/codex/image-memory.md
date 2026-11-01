# Imported PNG memory report (C7)

`npm run check:images` prints a Markdown report and appends it to the GitHub Actions job summary when `GITHUB_STEP_SUMMARY` is present. The Verify workflow runs it on PRs and main. `node scripts/check-images.cjs --json` produces machine-readable output (with the same CI summary). No new dependencies, art edits, runtime changes or production budget thresholds.

For each repository-owned PNG imported by runtime code under `app/`, `components/` or `lib/`, the report reads its PNG IHDR dimensions and estimates **width × height × 4 bytes**, independent of compressed file size. A MiB is 1,048,576 bytes. It lists every path, importer, dimensions, exact byte count and category. Inventory totals deduplicate by path, not by content hash; two separately named files may have separate decode/cache entries.

It now also reads each PNG's on-disk file bytes. The hub and world route summaries list that static PNG upper bound and their ten largest reachable PNGs. The hub row sits beside lane R's measured **7–9 MB fetched within four seconds**. They are intentionally different measurements: the static source closure includes all imported catalogue branches and Metro platform variants even when the first render does not request them, while the review number is transferred data affected by cache state and may include non-PNG resources. Neither number is measured resident or GPU memory.

Category totals distinguish garden ground, water animation frames, night lights, props, growth sprites, each mission world and shared world props, battle, and vignettes. New paths fall into an explicit Other category instead of disappearing. Current companions and icons use generated vector/pixel rows, not imported PNGs: their PNG contact sheets are deliberately not counted.

## What screen totals mean

Every Expo route is discovered automatically and includes its ancestor layouts. Additional entries describe the existing global onboarding/nap/welcome-back module, menu/companions, battle and mission-world surfaces. The source graph follows local static imports, re-exports, literal require/import calls, directory index modules and all Metro platform variants. Type-only imports/exports, tests, declarations, comments and strings not used as imports do not contribute.

Each screen is a **conservative static import envelope**, not a measurement of what it draws or keeps decoded. All catalogue entries, day/night images and animation frames reachable through a module count. Shared global overlays/layouts count on every screen but only once within that screen. Do **not** add screen totals together. A shared module may expose multiple screens without drawing all of them; no tree-shaking or conditional-render analysis is claimed. Identical totals are possible and useful evidence of import coupling, not proof of equivalent rendering cost.

Excluded: external package images, app-config/splash/favicons, remote/data URI assets, SVG/vector allocation, non-PNG formats, screen pixel buffers, GPU copies, mipmaps, runtime caching or a native allocator's overhead. Header checks reject missing files, malformed headers, zero/unsafe dimensions, unresolved local imports, dynamic module paths and source symlinks; they are not a PNG decoder or CRC validator. No app module is executed and no save is read or written.

## Initial baseline and feedback for Claude

On main `365942e25e72a8ddfd81b4ebc0290f338e312222`, the imported inventory is **108 PNGs / 94,753,472 bytes / 90.364 MiB**. Garden ground is 13,271,040 bytes; its eight water frames are another 4,489,216 bytes. Vignettes are 26,956,800 bytes; battle is 16,699,392 bytes. The report recomputes these numbers on every run: they are observations, not enforced limits. Claude's latest building redraw and seven night-light PNGs are preserved unchanged.

Current routes and overlay surfaces all reach the same inventory through shared modules (notably the global overlays and multi-screen modules). Category, per-file and ten-largest tables make that coupling inspectable. A later approved import split or a runtime decode trace could distinguish actually active assets; this task deliberately does not refactor visual components. `lib/budgets.ts` has no `firstLoad` budget, so hub size remains report-only. The test can inject a budget and proves an over-budget fixture route fails; production gating begins only when Claude adds the real budget. No recommendation here authorises art changes or hidden game-rule changes.

## Verification and limits

`npm run check:images-test` covers on-disk and RGBA arithmetic, deduplication, shared/ancestor layouts, cycles, type-only imports, re-exports, literal/dynamic imports, Metro variants, orphan imports, malformed/missing assets, stable ordering, largest-file ordering, an injected over-budget route and the real CLI's JSON/CI-summary output. It runs inside `npm run verify`. Without an injected or future production `firstLoad` budget, the report command fails only on invalid or uninspectable inputs, never on size.

This is source analysis, not a phone memory profile, native device test, frame-rate measurement, visual approval or new play-test. Screenshot and normal Verify workflows remain unchanged apart from the additive report step. C6's separate generator repair remains on PR #16; this independent C7 branch does not copy or waive it.
