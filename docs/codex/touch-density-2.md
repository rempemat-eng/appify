# C47: touch targets at density 2

Assignment: Claude A's #149 comment 6322623299, retained by pivot 6325893482 and coordinator 6327658464. Base: `18a8bef77d79bb81163ada1df038fbb3ce6477df`, with #198 and #212 included. This changes only the target-geometry section of `scripts/check-garden.cjs`; component fixes belong to Claude B.

## Reproduce

```sh
npm run check:garden
```

The original 320, 390, 430 and 640 CSS-pixel widths remain at the live default. The matrix additionally covers 320×568@2 and 375×667@2 at explicit densities 1 and 2, in flat/tilt views and web/iOS platform plans. It changes the evaluated density-setting export locally, so the actual `GardenWorld` and `pixelScale` read the requested grid, and restores it afterwards. No app flag/default or shared harness stub changes.

These are source-geometry checks. The standalone garden uses its natural scene height; the phone height identifies the requested screen, but does not simulate viewport clipping, safe areas or a phone. Passing `viewportHeight` would select the hub renderer instead of the standalone geometry under audit. React, clocks and native boundaries remain substituted by the existing harness. No browser screenshots, real native runtime, memory, frame-time or physical hit-testing claims follow from this check.

## Findings for Claude B

The existing actionable `gardenObjects` and pond checks pass, including 44×44 minimums, scene bounds, artwork projection and split-target layering. With a real callback and four kept-memory fixtures, the four keepsakes become actual `Pressable` nodes. Their web boxes are undersized at both grids. React Native Web 0.21.2's `Pressable` does not implement the emitted `hitSlop`; the audit counts the emitted CSS box on web. On iOS it checks the **planned** box plus numeric hitSlop, giving 44–45.5 points. Native clipping, overlap and gesture behaviour still need a device check.

Every size below is width×height in CSS pixels. Each row represents four explicit registry entries, one per target ID. The complete key is `<view>/web/<screen>/density<density>/<target ID>`; no wildcard is accepted by the code.

| Screen    | Density | View | `keepsake-rest` | `keepsake-read` | `keepsake-move` | `keepsake-create` |
| --------- | ------- | ---- | --------------- | --------------- | --------------- | ----------------- |
| 320×568@2 | 1       | flat | 16×16           | 16×16           | 16×16           | 16×16             |
| 320×568@2 | 1       | tilt | 12.5×12.5       | 12×12           | 13×13           | 12.5×12.5         |
| 320×568@2 | 2       | flat | 16×16           | 16×16           | 16×16           | 16×16             |
| 320×568@2 | 2       | tilt | 12.5×12.5       | 12×12           | 13×13           | 12.5×12.5         |
| 375×667@2 | 1       | flat | 24×24           | 24×24           | 24×24           | 24×24             |
| 375×667@2 | 1       | tilt | 18.5×18.5       | 18×18           | 19.5×19.5       | 19×19             |
| 375×667@2 | 2       | flat | 16×16           | 16×16           | 16×16           | 16×16             |
| 375×667@2 | 2       | tilt | 12.5×12.5       | 12×12           | 13×13           | 12.5×12.5         |

There are 32 exact known findings. Density 2 reduces the 375-wide phone's flat keepsake box from 24 to 16 pixels. At 320 wide, both densities already use a world unit of one CSS pixel, so sizes match. Claude B's next step is to give these web interactions a real minimum 44×44 target while preserving their artwork/projection and avoiding overlap. Remove each repaired entry together with its component fix; this task does not change the component.

Decoration mode's actual “Tap where the keepsake goes” pressable is the whole scene and passes the size check in all 16 phone/density/view/platform cases. Placed decor is passive art (`DecorSprite` emits a `pointerEvents: 'none'` view), rather than a separate small button. This is not a decor-placement/collision audit: the existing harness substitutes those model boundaries. Companion/visitor targets fixed by #212 are outside this standalone garden section; C47 does not retest their real UI.

## Registry controls

The real measurements are compared against `knownTargetFindings` by exact case/target ID and exact size. A new undersized target fails. Any change to a known size fails for review. A repaired or missing target leaves a stale finding and fails until its entry is removed. Invalid/nonfinite dimensions also fail.

The harness exercises that same validator with a removed real entry, an injected new 43×44 target, a repaired 44×44 target still registered, and changed 15×16 geometry. Each must throw the corresponding error. An external scratch mutation removing the first registry entry must also make the full harness exit nonzero with `Unregistered undersized target`; restore the source before final validation.

## Validation

Final source checks and exact tested head are recorded on the task PR. Required: `npm run check:garden`, the external missing-entry mutation, `npm run verify` (including web and iOS exports), `npm run check:art-repro`, and matching CI. Source checks do not settle C34's separate physical-device measurement gate.
