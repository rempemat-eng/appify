# NapAttack vision

This folder is the shared brief for anyone building NapAttack: Matt, Claude and Codex. Read it before any design, art or interface work, and update it when the direction changes. When this folder and an older doc disagree, this folder wins.

| File                                         | What it covers                                                                                                                                                                                                                                                                                                   |
| -------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [art-style.md](art-style.md)                 | How the world art should look, the techniques the generators use, references and a review checklist                                                                                                                                                                                                              |
| [interface.md](interface.md)                 | The full-screen game layout: HUD, hotbar, sheets, pixel frames and the pixel font                                                                                                                                                                                                                                |
| [garden-growth.md](garden-growth.md)         | How the meadow grows from time away, and its limits                                                                                                                                                                                                                                                              |
| [sound.md](sound.md)                         | The generated sound palette, where each cue plays, and the rules for new sounds                                                                                                                                                                                                                                  |
| [coherence-plan.md](coherence-plan.md)       | **The current plan:** Matt's 17 Oct review, the audit, targets and the ordered steps                                                                                                                                                                                                                             |
| [living-world-plan.md](living-world-plan.md) | **The approved new work (17 Oct):** currency and care, decay, atmosphere, menus, people, decorating, world memory, biomes, and their order                                                                                                                                                                       |
| [roadmap.md](roadmap.md)                     | What comes next, open questions and ideas we have not built                                                                                                                                                                                                                                                      |
| [home-hub.md](home-hub.md)                   | **The home hub (19 Oct):** the garden as a place in the one world, on one screen with the valley; why the old handoff popped, the design and its phases                                                                                                                                                          |
| [world-rules.md](world-rules.md)             | **The world's rulebook (18 Oct):** what each kind of ground means, what may stand on it, how neighbouring places join, corridors, detail derived from logic, and the bug protocol                                                                                                                                |
| [world-plan.md](world-plan.md)               | **The world plan (v2, 20 Oct, for review):** sizes from the scale table (plots, streets, squares, farms, harbours, towns, castles, city blocks) in px and walk-seconds, what the phone shows, region canvases instead of zone tiles, every region resized, where the ways stand, the order of work and decisions |

## Matt's direction (October 2026)

- **One game, not an app with a game in it.** The world fills the phone. Controls sit on top of it (a HUD, a hotbar, a menu) or live inside it (tap the signpost, the mailbox, the bed). Home does not scroll.
- **Pixel everything.** Buttons, panels and indicators use hard-edged pixel frames, not rounded web controls. All text uses one pixel font.
- **Clean, detailed art with real shading.** "Shading is super important. I like it clean." Outlines stay. Objects should feel 3D: a lit side, a shaded side, cast shadows. The bar is the references in art-style.md.
- **Cosy tone.** Gentle, warm, never shaming. The companion encourages; it does not nag.
- **The garden grows.** Time away visibly changes the world.
- **Intuitive and immersive.** Show, do not explain. Guidance appears in the world (a "!" over the next place, the companion speaking) rather than as cards of text.
- **Content after polish.** Once the look and feel are right, add more places, visitors and things to do.
- **A living world (17 Oct).** Matt approved the merged plan and Codex's living-world ideas: a safe currency earned away from the phone, gentle reversible decay, seasons and weather as scenery, people with routines, decorating and interiors, lasting story changes and new biomes. Order and rules: [living-world-plan.md](living-world-plan.md).

**World rules** (Matt, 18 Oct): the world must make sense: water has a source and a sink and only floating or supported things stand on it, paths lead to places, gates sit in fences, neighbouring places are built together with corridors between them, and detail follows from these rules. The research is [../research/2d-world-design.md](../research/2d-world-design.md); the rules are [world-rules.md](world-rules.md).

**World atlas** (Matt, 17 Oct): the regions beyond the valley (Driftwood Harbour, Hearthold Castle, steampunk Cogsworth Junction, the western Dust Gulch, the Ember Caldera, cyberpunk Neon Harbour, Halcyon Station and the moon Lumen), the theme that ties them together (a journey from rest to screens and back to sleep), seamless travel and a world that feels alive: [world-atlas.md](world-atlas.md).

## Working agreements

- Edit the generators in `scripts/art/` and rerun `npm run art`; never hand-edit generated PNGs or `lib/garden-map.ts`.
- New colours go into `art/materials.json` (shared ramps), not into individual files.
- Keep the source-level harnesses in `scripts/check-*.cjs` meaningful: derive expectations from generated data (the map, the ramps) rather than hard-coding coordinates.
- Play-test in a browser at phone size (402×874) and look at screenshots before calling art or layout done.
