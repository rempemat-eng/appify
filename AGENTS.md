# Working on NapAttack

The source of truth is `rempemat-eng/appify` on GitHub. The Bilt editor and its preview are outdated. Real multiplayer is a later phase; finish the existing art, motion, HUD and local interactions before adding more content or mechanics.

## Read the vision first

`docs/vision/` holds Matt's direction and the shared design rules (art style, the full-screen interface, garden growth, roadmap). Read it before any design, art or interface work, follow it over older docs, and update it when the direction changes.

## Coordinate before editing

- Read the current `main` and the active pull request head before starting. Check the working tree for other people's changes.
- Use an isolated branch for a task, with one integration owner. Claude and Codex must not independently push to the same task branch at the same time. When agents share a checkout, agree which files or component regions each one owns before writing. If two tasks need the same files, integrate one before starting the other.
- Do not overwrite concurrent changes. If `main` advances, inspect its changes and incorporate them before marking your work ready. Preserve the other agent's fixes and verify the resulting source.
- Keep CI minutes down without lowering the bar (Matt, 19 Oct). Every push to an open, non-draft PR re-runs CI, so: keep a PR as a draft while you iterate (drafts run no CI) and mark it ready once, after your local `npm run verify` and `npm run check:art-repro` pass; push a branch once per finished step rather than after every commit; and do not merge main into an open PR just to keep it current (Claude A merges it on top of main and regenerates). Update a PR only when it conflicts or a reviewer asks for changes.
- Name chats and scheduled tasks `NapAttack <lane> · <what>` (Matt, 19 Oct), with the lane as A, B, C, D, E or R (the world review): for example `NapAttack C · Isles, Cogsworth & city`, `NapAttack A · Coordination round`, `NapAttack R · Check PR #66`. A one-off check names its PR.
- Never force-push shared work. Push with an expected-head check when using the GitHub connector. Do not push locally reconstructed Git history over the repository's real history.
- The user merges pull requests, except that Claude A verifies and merges the lanes' and Codex's PRs (Matt, 18 Oct) and its own (Matt, 20 Oct 22:40: "You merge them"). Nobody else merges, changes branch protection or enables auto-merge unless asked.
- Four Codex chats (20 Oct): before claiming or editing C29–C34, read `docs/codex/coordination.md` and the live handoff thread https://github.com/rempemat-eng/appify/issues/149. Preserve the existing C29→C30 and C32→C31 assignments and start conditions; register C33/C34 separately. Check other claims and agree shared save/manifest ownership before writing. This does not expand Claude-lane permissions.
- Continuous work: Codex takes tasks from the Codex queue in `docs/vision/coherence-plan.md` and answers the Feedback written there; Claude keeps that queue stocked and, as Matt asked, verifies and merges quiet Codex PRs.
- Two Claude chats may work at once (Matt, 18 Oct). The first (Claude A) builds the world and merges; a second (Claude B) takes Claude B's queue in `docs/vision/coherence-plan.md`, "Who does what", on a `claude-b/` branch with a PR, and edits only the files that table gives it. Both Claude chats keep the crew board (https://claude.ai/artifact/Mn6cKNmqLxKWDQwyhsMhmE) current with the ArtifactData tool: their lane in `lanes/<claude-a|claude-b>`, task states in `tasks/<id>`, and notes addressed to them in `notes` (read before each step, mark `done` when handled). Codex, which cannot open the board, keeps using Feedback in the plan. A third chat (Claude C) owns the Tidebloom Isles on a `claude-c/` branch and a fourth (Claude D) owns Sunstone Reach on a `claude-d/` branch, as the same table says. A fifth (Claude E) owns the home valley's places on a `claude-e/` branch (Matt, 19 Oct: "feel free to add more agents if it makes sense").

## Keep the design coherent

- Eastward's level of detail is required, not a nice to have (Matt, 20 Oct). Compare every art change side by side with the official references at the same character height and meet the counts in `docs/vision/art-style.md` ("Eastward's level of detail is required") before handing it on; say in the PR what you compared.
- No old asset is reused unless it fits the newest standard (Matt, 20 Oct 20:16: "make sure no old assets are reused that dont fit the soft grid, level of detail etc. established for the newest version"). A sprite, ground piece or scenery picture may go into a rebuilt region only when the asset ledger grades it KEEP, or its REWORK fix is done (`docs/vision/asset-ledger.md`, `scripts/art/asset_ledger.json`, `npm run check:assets`, being built on `claude-a/asset-ledger`; until it lands, check each asset by hand against the points that follow): on the soft grid, at Eastward's level of detail, in the house style and palette, at the size guide's scale, and logical. Everything else is redrawn or retired, never patched into the new world. Old zones stay playable until their region is rebuilt, but polish goes into the new kits, not into old ground.
- Keep the native pixel grid, upper-left lighting, material-specific shading and a quiet companion clearing. Edit the source art generators and regenerate PNGs and the map together.
- Garden props must remain reachable. Keep the companion inside the scene and keep small prop hit areas usable when it stands nearby. Touch targets are at least 44 screen pixels.
- Decorative interactions do not add rewards, costs or chores. Do not change existing game rules as part of an art or HUD pass.
- Motion should anticipate, act and settle. Effects are finite, respect reduced motion and stop when their screen is inactive. Interrupted walks must not trigger stale navigation or naps.

## Keep it portable to iOS and Android

NapAttack is a web app now and is meant to become a phone app later (Matt, 19 Oct: not yet, but nothing should stand in the way). Follow `docs/native-readiness.md`:

- **Browser objects** (`window.*`, `document.*`, `navigator.*`, `localStorage`) go only behind `Platform.OS === 'web'`, or in a `.web.tsx` file with a native sibling. `typeof window` is not a guard, because React Native defines `window`. Record each new use in `scripts/native-safe.json`; `npm run check:native` enforces it.
- **Packages:** add them with `npx expo install`, and don't use DOM-based libraries outside `.web` files.
- **Assets:** bundle art and sound with `import`. `public/` exists only on the web.
- **Interaction and layout:** touch first (taps, 44-point targets, nothing hover-only), and layout from `useWindowDimensions` and safe-area insets.

## Verify the exact result

- Run `npm run verify` on the final source and check the matching GitHub Actions result before marking the PR ready. It checks TypeScript, lint, core rules, the game store, companion profiles, garden regressions, native readiness, the web export and the iOS bundle. Keep lint clean. Claude removed the earlier inherited warnings.
- The garden harness substitutes React, timers, platform and animation boundaries. It verifies emitted plans and source geometry, not real React scheduling, native lifecycle or visual quality.
- Play-test the current PR preview in a disposable local profile. Keep the same preview origin when testing saved progress. Check normal and reduced motion, day/night, interrupted walks, overlapping props and HUD actions.
- Do not claim phone, native, multiplayer or device-usage testing from a desktop browser or a source harness. Record any missing coverage plainly.

## Companion identity

- Use `guardianPlayer` for effective rendering/combat identity and `companionProfile` for attributes. Keep the canonical starter name/species in the saved account. Only befriended visitors are selectable.
- Personality descriptions and real-world invitations do not add mechanical stats. Explain existing family effects accurately, and label later individual bonuses as proposals until implemented and balanced.
- Switching must preserve shared level, currency, hats, cards, history and collection. Do not switch during a mission, nap or battle.

## Handoff

Provide the PR link, exact tested head, preview URL, validation results and remaining limitations. Check whether the previous PR has already merged before updating it; open a new PR for subsequent work. Keep durable regression checks and artwork instructions in the repository.
