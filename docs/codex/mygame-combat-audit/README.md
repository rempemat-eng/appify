# MyGame combat and animation handoff

Matt's 25 October 2026 decisions govern this handoff. Claude A owns the code-drawn redraw, foundation and integration. This is an audit/data supplement for the existing CHARACTER-CONTRACT owner to consolidate, not a competing runtime or foundation. Existing handoff branches and their files remain with their owners. New AI frame/direction generation for #241 has stopped. #241 remains a draft reference prototype; its raw generated PNGs must not merge as-is.

## Sources and authority

- Canonical combat: the exact desktop playtest bundle `entry-6fdd0ef25567acc156c4a1e86a9a36fe.js`, recovered catalogue module 3501 and engine module 3500. The recovered source strings are checked against the saved ZIP and bundle. Their hashes and extraction commands accompany the data. This preserves the tested rules; it does not declare their balance final.
- Studio animation reference: [#241 at 4d7efc7](https://github.com/rempemat-eng/appify/tree/4d7efc7085786c897fc0c50f7151a0ae7e62f0c2/prototypes/mygame-animation-studio). All fourteen manifests, the exporter and runtime were inspected. This is the published v3 east-facing study. Later comments describe local v4 fixes, but no supplied source substantiates those fixes, so this handoff does not claim them implemented.
- Identity and continuity: [ART_DIRECTION.md](https://github.com/rempemat-eng/appify/blob/4d7efc7085786c897fc0c50f7151a0ae7e62f0c2/prototypes/mygame-animation-studio/ART_DIRECTION.md). Its old canvas dimensions and review-mode restrictions are superseded by Matt's current direction and canonical combat rules.
- Coordination: [#149](https://github.com/rempemat-eng/appify/issues/149). No existing task, branch ownership, save schema or persistent continuation is reassigned here.

## Target

Use Claude A's `game/` foundation after it lands and combat file ownership is agreed. The adopted target is Godot 4.7.2 with LimboAI, Phantom Camera and GdUnit4; map inputs are the Python art kit or Tiled through YATI. These are requested integration targets, not a claim that these versions have been installed or tested in this handoff.

The logical viewport is 960×540. Figures are approximately 74 logical pixels tall, displayed at 2× for 1080p and 4× for 4K, with nearest filtering and a consistent support origin. Draw S/N/E/W separately; west must be relit and asymmetric anatomy/equipment preserved. World art uses `--density 3`. This density is not a character, anchor or combat-distance multiplier.

Canonical combat currently uses a 320×180 simulation arena; the studio uses 960×540 and much larger source figures. Preserve these units in the references. Agree an explicit simulation-to-world transform in the foundation; do not silently reinterpret ranges, speed or damage areas as new-world pixels. Reauthor art anchors for 74 px bodies rather than uniformly shrinking old anchors.

## What the published studio actually consumes

Each character needs both `assets/animated/<id>/manifest.json` and a `frames.tres` SpriteFrames resource. A manifest alone cannot play. Required clips are `idle`, `walk`, `primary`, `secondary`, `special`, `guard`, `hit`, `defeat`, `jump`, `stair_up`, `stair_down`, `dodge`, `powered_idle`, `powered_walk`, `powered_primary`, `powered_guard`, `powered_exit`. Pendle also has `reload`.

| Item | Existing meaning |
| --- | --- |
| Frame timing | SpriteFrames per-frame duration divided by animation speed. Exporter speed is 1.0, so frame durations are seconds. The actor does not read JSON timing arrays for playback. |
| `release_time` | Action clock in seconds; takes precedence over `release_frame`. |
| `release_frame` | Zero-based release/contact pose. Its onset is the sum of all preceding frame durations. One gameplay release per action. |
| `hold_frame` | Zero-based guard pose held while input remains down. |
| `foot_pivot` | Ground-foot position within the untrimmed logical frame canvas. Independent of crop bounds. |
| `release_anchor`, `hand_anchors` | Offsets from the visual foot, +x right and +y down. Hand anchors are per-frame; they are not atlas/screen coordinates. |
| `contact_reach` | Studio melee reach override, in studio units. Not canonical balance data. |
| `thruster_anchors` | Rook's separate attached nozzle offsets, relative to the foot. |
| `baked_effects` | A `muzzle_flash` entry suppresses a second procedural flash. |
| Bounds and provenance | Export/audit metadata. Packed bounds are left/top/right/bottom, with exclusive maximum edges; the actor does not interpret these as hitboxes. |

The concrete field list and pending extensions are also in `animation-contract.json`. Frame counts are drawing choices. Preserve event times and pose roles when changing them; do not slow the mechanics to fit a larger drawing count.

## Required port work beyond the old manifest

1. **Four-facing resources and anchors.** The old actor hard-codes east, disables flipping, and releases/dashes to the right. Add a facing selector and per-facing pivots, release, hand/held-object and nozzle tracks. Keep clip names and the current manifest shape within each facing. Agree the wrapping/resource layout with Claude A before implementing an importer. Do not label nonexistent S/N/W anchors as completed.
2. **Continuous gameplay aim.** The canonical engine supports a continuous aim vector with four dominant-axis body facings. Keep simulation aim separate from body-art facing and visual muzzle position. No additional AI directions are requested. If a drawn clip needs distinct high/low aim poses, expose named tags in the agreed importer instead of changing gameplay aim to cardinal-only.
3. **Release pose before event.** The published studio emits `action_released` before updating the visible pose. The port must commit the authored release/contact pose first, then publish the event exactly once. Test exact boundaries, large delta steps, cancellation and repeated actions. Damage remains simulation-owned and cannot depend on rendering completion.
4. **Traversal roles.** Existing jump indices are load 0–1, rise 2, apex 3, descend 4, landing 5–7. Rook's old secondary uses rise 3, apex 4, descend 5 and landing 6–7. Replace these hard-coded assumptions with explicit pose roles if drawings change. Physics owns elevation, collision and actual landing; source poses remain registered to their support baseline.
5. **Attachment and contact events.** Cairn's separate held boulder is hard-coded to secondary frames 2–7; supply an authored per-facing attachment track. Footfalls currently come from a half-cycle timer; export foot-contact event times/poses if the redraw needs exact contact synchronisation. Existing signals are `action_released`, `action_finished`, `action_cancelled`, `footfall`, `landed`, `void_fall`.
6. **Equipment through all allowed states.** The old powered review supports only idle/walk/primary/guard/exit. It rejects powered secondary/jump/dodge and has no powered reaction/stair coverage. Draw or layer the relevant equipment consistently through allowed secondary, movement, reaction and defeat states. Missing variants must remain explicit; do not gate canonical actions merely to hide missing artwork.

Keep Brine's tether/reel, Nix's stationary decoy, Mirra's seals/currents, Rook's exactly two turrets and Mote's orbiting shards as scene entities. Do not paint extra entities into the body and then create duplicates at runtime. Pendle's rifle/revolver, Ashe's helmet and Nix's anatomical left laser arm must retain identity in every facing.

## Canonical rules that override study restrictions

- Brine's untethered secondary is a gun-butt sweep; a valid tether instead reels a light target or winches toward a heavy anchor.
- Morel's secondary may burst at close range without a prepared patch. Prepared patches support the catalyst reaction.
- Pendle's powered secondary uses the rifle stock. Base fan fire consumes up to three remaining revolver rounds and reloads.
- Rook can aim and fire his carbine while vaulting. Height avoids ground melee/fields, not projectiles/explosions. The body/weapon presentation may need layering rather than one mutually exclusive clip.
- Specials release at 0.28 s during a 0.65 s action and start a finite form. Nix lasts 7 s, Rook 10 s, the other twelve 8 s. The special cooldown is 25 s. Equipment ends through canonical expiry/defeat behavior, not the studio's manually toggled indefinite review state.
- Attack durations and release times in the canonical data govern the port. Old studio frame timings and release anchors are drawing references, not replacement combat constants.

## Integration boundary and validation

No `game/` source, plugins, CI wiring, player saves or existing task branch has changed. Main was inspected at `18a8bef77d79bb81163ada1df038fbb3ce6477df`; no Godot foundation branch was visible at inspection, which does not establish the state of Claude A's local checkout. This data-only handoff remains draft. Recovered-module checks and extraction validation are distinct from running the Godot game, full npm verification, hosted CI or physical-device measurements.

| File | Use |
| --- | --- |
| `data/canonical.json` | All fourteen identities, source-derived numeric rules, base/powered action/release clocks, executed projectile/contact probes and explicit units. New art release-frame indices are null until authored. |
| `data/studio-reference.json` | All 239 old studio clips, exact source-manifest hashes, timing/hold frames, release/hand/nozzle anchors and 56 action-timing discrepancies. All new facing anchors remain pending. |
| `animation-contract.json` | Machine-readable existing field semantics and separately labelled importer requirements. This file is not installed as a runtime schema. |
| `reference/` | Hash-pinned recovered compiled modules, bounded reference adapter and labelled source-derived annotations. Original TypeScript recovery is not claimed. |
| `tools/` | Reproducible archive/module extraction, data generation and the focused checker. |

Validation: the saved archive, JS bundle and both original module byte strings match their pinned SHA-256 hashes. All 21 downloaded studio source files, including fourteen manifests, were matched to the published Git blob identities before extraction. The two data JSON files reproduce byte for byte. The focused checker passes 967 checks over fourteen characters and 239 clips, including guard direction, canonical fallbacks, reload/vault/decoy behavior, finite forms and rejected corrupt-data controls. This identifies 56 canonical-versus-study action-timing mismatches; it does not certify new sprites or production integration.

Run `python3 tools/extract-reference.py` with the pinned desktop ZIP and `--check`; run `node tools/extract-data.mjs` with `--studio-root` pointing to the exact #241 prototype directory and `--check`; then run `node tools/verify-handoff.mjs`. Each command is relative to this directory. The checker runs from the committed text references without an engine or network connection. The saved desktop build is [the source archive](https://chatgpt.com/library?file_id=libfile_a8686f8b8cfc8191b71d7f2712de1cd8&account_id=personal); no build bundle or PNG is copied into this supplement.

Claude A: please agree (a) the four-facing resource wrapper and anchor units, (b) the explicit simulation-to-world transform, and (c) combat/simulation/test owned paths and player/input/save APIs once the foundation PR lands. The character lane can then port the simulation, restore the canonical behaviors above, implement the importer and run GdUnit4 tests against the pinned engine. No parallel foundation is needed.
