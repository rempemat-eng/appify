# NapAttack vision

This folder is the shared brief for anyone building NapAttack: Matt, Claude and Codex. Read it before any design, art or interface work, and update it when the direction changes. When this folder and an older doc disagree, this folder wins.

| File                                 | What it covers                                                                                      |
| ------------------------------------ | --------------------------------------------------------------------------------------------------- |
| [art-style.md](art-style.md)         | How the world art should look, the techniques the generators use, references and a review checklist |
| [interface.md](interface.md)         | The full-screen game layout: HUD, hotbar, sheets, pixel frames and the pixel font                   |
| [garden-growth.md](garden-growth.md) | How the meadow grows from time away, and its limits                                                 |
| [roadmap.md](roadmap.md)             | What comes next, open questions and ideas we have not built                                         |

## Matt's direction (October 2026)

- **One game, not an app with a game in it.** The world fills the phone. Controls sit on top of it (a HUD, a hotbar, a menu) or live inside it (tap the signpost, the mailbox, the bed). Home does not scroll.
- **Pixel everything.** Buttons, panels and indicators use hard-edged pixel frames, not rounded web controls. All text uses one pixel font.
- **Clean, detailed art with real shading.** "Shading is super important. I like it clean." Outlines stay. Objects should feel 3D: a lit side, a shaded side, cast shadows. The bar is the references in art-style.md.
- **Cosy tone.** Gentle, warm, never shaming. The companion encourages; it does not nag.
- **The garden grows.** Time away visibly changes the world.
- **Intuitive and immersive.** Show, do not explain. Guidance appears in the world (a "!" over the next place, the companion speaking) rather than as cards of text.
- **Content after polish.** Once the look and feel are right, add more places, visitors and things to do.

## Working agreements

- Edit the generators in `scripts/art/` and rerun `npm run art`; never hand-edit generated PNGs or `lib/garden-map.ts`.
- New colours go into `art/materials.json` (shared ramps), not into individual files.
- Keep the source-level harnesses in `scripts/check-*.cjs` meaningful: derive expectations from generated data (the map, the ramps) rather than hard-coding coordinates.
- Play-test in a browser at phone size (402×874) and look at screenshots before calling art or layout done.
