# Working on NapAttack

The source of truth is `rempemat-eng/appify` on GitHub. The Bilt editor and its preview are outdated. Real multiplayer is a later phase; finish the existing art, motion, HUD and local interactions before adding more content or mechanics.

## Read the vision first

`docs/vision/` holds Matt's direction and the shared design rules (art style, the full-screen interface, garden growth, roadmap). Read it before any design, art or interface work, follow it over older docs, and update it when the direction changes.

## Coordinate before editing

- Read the current `main` and the active pull request head before starting. Check the working tree for other people's changes.
- Use an isolated branch for a task, with one integration owner. Claude and Codex must not independently push to the same task branch at the same time. When agents share a checkout, agree which files or component regions each one owns before writing. If two tasks need the same files, integrate one before starting the other.
- Do not overwrite concurrent changes. If `main` advances, inspect its changes and incorporate them before marking your work ready. Preserve the other agent's fixes and verify the resulting source.
- Never force-push shared work. Push with an expected-head check when using the GitHub connector. Do not push locally reconstructed Git history over the repository's real history.
- The user merges pull requests. Do not merge, change branch protection or enable auto-merge unless asked.

## Keep the design coherent

- Keep the native pixel grid, upper-left lighting, material-specific shading and a quiet companion clearing. Edit the source art generators and regenerate PNGs and the map together.
- Garden props must remain reachable. Keep the companion inside the scene and keep small prop hit areas usable when it stands nearby. Touch targets are at least 44 screen pixels.
- Decorative interactions do not add rewards, costs or chores. Do not change existing game rules as part of an art or HUD pass.
- Motion should anticipate, act and settle. Effects are finite, respect reduced motion and stop when their screen is inactive. Interrupted walks must not trigger stale navigation or naps.

## Verify the exact result

- Run `npm run verify` on the final source and check the matching GitHub Actions result before marking the PR ready. It checks TypeScript, lint, core rules, the game store, companion profiles, garden regressions and the web export. Keep lint clean. Claude removed the earlier inherited warnings.
- The garden harness substitutes React, timers, platform and animation boundaries. It verifies emitted plans and source geometry, not real React scheduling, native lifecycle or visual quality.
- Play-test the current PR preview in a disposable local profile. Keep the same preview origin when testing saved progress. Check normal and reduced motion, day/night, interrupted walks, overlapping props and HUD actions.
- Do not claim phone, native, multiplayer or device-usage testing from a desktop browser or a source harness. Record any missing coverage plainly.

## Companion identity

- Use `guardianPlayer` for effective rendering/combat identity and `companionProfile` for attributes. Keep the canonical starter name/species in the saved account. Only befriended visitors are selectable.
- Personality descriptions and real-world invitations do not add mechanical stats. Explain existing family effects accurately, and label later individual bonuses as proposals until implemented and balanced.
- Switching must preserve shared level, currency, hats, cards, history and collection. Do not switch during a mission, nap or battle.

## Handoff

Provide the PR link, exact tested head, preview URL, validation results and remaining limitations. Check whether the previous PR has already merged before updating it; open a new PR for subsequent work. Keep durable regression checks and artwork instructions in the repository.
