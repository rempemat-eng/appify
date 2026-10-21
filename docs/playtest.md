# Play-testing at phone size

`npm run playtest` plays the game's main flows in a browser at three phone sizes and at art densities 1 and 2, saves a screenshot of every step and writes a short report. Lane R runs it twice a day; anyone can run it before marking a PR ready.

**It is a desktop browser, not a phone.** Chromium emulates each phone's viewport, pixel ratio and touch. It says nothing about a phone's GPU, memory, frame rate, audio output, notch and home indicator, the software keyboard or the native app. Say so in any review that uses it, and never report its results as phone testing.

## What it plays

Each flow runs on 402x874 @3 (iPhone 17 Pro), 412x915 @2.625 (Pixel 9) and 375x667 @2 (iPhone SE), each at `?density=1` and `?density=2`: 42 runs.

| Flow               | What it does and checks                                                                                        |
| ------------------ | -------------------------------------------------------------------------------------------------------------- |
| `onboarding`       | A fresh profile: picks a seed, names the player and the Grassling, and lands in the garden                     |
| `hub`              | The saved garden fixture; measures the HUD and hotbar; opens the menu                                          |
| `walk-interrupted` | Taps the bed (a walk that would offer a nap), then changes course mid-walk: no nap sheet and no nap may follow |
| `nap`              | Opens the nap sheet, starts a nap, wakes up                                                                    |
| `spar`             | Opens the arena and starts the spar with Dave                                                                  |
| `night`            | The garden at 22:00                                                                                            |
| `reduced-motion`   | The app's and the browser's reduced motion on; a walk                                                          |

Clocks are faked (14:00 UTC by day, 22:00 at night) and `Math.random` is seeded, so runs are repeatable. Every request outside the local export is blocked and reported.

## Running it

```bash
npm run playtest                      # builds the web export first (about 3 minutes), then about 4 minutes of play
npm run playtest -- --no-build        # reuse .expo/screens-export
npm run playtest -- --no-build --project=402x874@3-d2 --grep nap
```

If the Playwright browser is missing, point it at an installed Chromium with `PLAYTEST_BROWSER_PATH=/path/to/chrome`.

## The report

`artifacts/playtest/REPORT.md` (not committed) has:

- pass or fail for each flow on each screen and density (a browser error fails a flow);
- the interface's measured size: hotbar tabs, the nap and menu buttons, controls under 44 px (named), whether 2x icons drew, and horizontal overflow. The HUD and hotbar must be the same size at density 1 and 2 (`interfaceGrid`, docs/vision/interface.md); the report lists any difference;
- links to every screenshot (`artifacts/playtest/images/<screen>/<flow>-<step>.png`).

Look at the screenshots, not just the table: the harness proves the flows run and the interface keeps its size, not that a screen looks right.
