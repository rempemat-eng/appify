# `check:fx`

`check:fx` audits moving-water and lava sheets from PNG headers. It does not decode pixels, import
the app or regenerate art, so it remains suitable for the ordinary check suite.

## Rules

- `zoneFlow` sheets in `assets/zones/*/flow.png` and world-tile sheets in
  `assets/world/*/f_*.png` contain at most eight frames.
- `frames × frameMs` divides the shared 36-second animation clock.
- A sheet uses one image pixel per world pixel. This keeps moving water at 1× when the surrounding
  world art uses the 2× texel grid.
- No non-retiring sheet passes 4096 pixels on either side.
- Decoded RGBA bytes are reported per 256-world-pixel tile against 1 MiB. That comparison is
  report-only until Claude A confirms the budget.

Old-zone findings are report-only because those zones retire with the canvas rebuild. World-tile
findings gate the check. The old-zone 4096 exception must come from the same retirement predicate as
`check-art-density.cjs`; the list is never copied into this checker.

## Current integration boundary

The header audit and its fixtures accept an injected `isRetiring(file)` predicate. The repository CLI
and package check line remain deliberately unwired until `check-art-density.cjs` exposes that predicate
through a side-effect-free module or guarded export. Requiring that script today would run its full PNG
scan and defeat the under-three-second requirement.

Run the isolated regression suite with:

```sh
node scripts/check-fx.test.cjs
```

It covers the four required negative fixtures: nine frames, seven frames at 150 ms, a 2×-stored strip
and a new 4608-pixel strip. It also proves that old-zone failures report without gating and that the
injected retirement predicate is the only 4096 exception.
