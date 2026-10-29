# Character animation/runtime handoff

Source review: draft PR #241, commit `4d7efc7085786c897fc0c50f7151a0ae7e62f0c2`. This is a reference contract for Claude A's replacement art and Godot foundation. It does not change `game/`, add an engine project or establish Godot 4.7.2 compatibility. No generated PNGs are included in these deliverables.

## Published source versus forward requirements

The published actor is an **E-only study runtime**. `scripts/roster_actor.gd` loads `assets/animated/<id>/{manifest.json,frames.tres}`, requires 17 common clips plus Pendle's reload, reads the manifest's foot pivot and never mirrors the sprite. It emits the release signal with `Vector2.RIGHT`. Its power is a manual visual hold; powered secondary/jump/dodge are blocked, and its finite-form/canonical balance is not the recovered original engine. `WORLD_ANIMATION_CONTEXT.md` explicitly discloses those limits. Later v4 tests/fixes discussed in chat are not present at this published head and must not be described as merged source.

`legacy-east-animation-reference.json` reconstructs all 14 E authoring timelines and stored attachment fields from the published importer/anchor sources:239 clips and 2,135 reference drawings. It contains no frame PNGs. Those numbers and old 96/112 px body targets are **not requirements** for the new 74 px art. The original canonical engine and ability data provided in the sibling handoff is authoritative for simulation seconds, cooldowns, damage and special rules. Do not copy the old studio's `contact_reach` into production balance; it described presentation geometry.

## Minimal manifest shape

Retain the existing fields for each authored facing: `id`, `name`, `view`, `frame_size`, `foot_pivot`, `clips`; each clip has `frame_count`, `durations`, `duration`, `loop`, `release_frame`, `release_time`, `hold_frame` and `frames`. A frame has a bundled `path`; a tight crop additionally needs `crop_offset` and `stored_size`. A full-canvas PNG does not need crop fields. Existing `SpriteFrames` resources are generated presentation data and must agree with the manifest.

Keep source texels separate from world units. `frame_size` is padding and `foot_pivot` is registration, not the figure height or collision body. Both are explicit per-view data; no hardcoded 96 px target, fixed 192/448 px canvas or 96-frame minimum belongs in the new runtime. Source texels display at 2× on 1920×1080 and4× on 3840×2160 under Claude A's960×540 project settings. World art density 3 is a separate import/world-unit contract.

The old per-character file has `view:"E"`. For four facings, the importer/loader must agree how to select S/N/E/W manifests or subrecords. A per-view file with the same inner shape is sufficient; an exact directory layout should be agreed with the foundation owner. Never derive W by flipping E anatomy or lighting.

### Clip requirements

| Group | Clips | Presentation rule |
|---|---|---|
| Ground/rest | `idle`, `walk`, `stair_up`, `stair_down` | Loop. Genuine alternating support and continuous loop; stairs retain grounded support height. |
| Actions | `primary`, `secondary`, `special` | One-shot. Prepare, visible release/contact, recovery. `special` is the base-to-powered entry. |
| Defence/reactions | `guard`, `hit`, `defeat` | Guard advances to `hold_frame` while held; hit recovers; defeat holds its terminal drawing until authoritative reset. |
| Movement | `jump`, `dodge` | One-shot, with semantic phase indices. Physical support/air time controls the visible phase. |
| Powered | `powered_idle`, `powered_walk`, `powered_primary`, `powered_secondary`, `powered_guard`, `powered_hit`, `powered_defeat`, `powered_jump`, `powered_stair_up`, `powered_stair_down`, `powered_dodge`, `powered_exit` | Keep the transformed model throughout all applicable states. Exit is explicit and carries no generic extra damage event. |
| Character variants | Brine `secondary_empty`, `powered_secondary_empty`; Rook `air_primary`, `powered_air_primary`; Pendle `reload`; Velvet counter mapped to `powered_counter`; Ashe expiry attack mapped to `powered_finisher` | Separate body choreography where the kit changes the actual action. Variant selection must follow canonical state, not just the current form bit. |

No separate idle-aim clip is required by the recovered contract. Rook does require a firing body pose while airborne. The aim vector should be an explicit action input, captured for release. Whether the foundation permits only four cardinal aims or continuous aim with a nearest-facing body is a controller decision; anchors must belong to the actual selected view in either case.

## Events, timing and lifecycle

The old signal names are `action_released`, `action_finished`, `action_cancelled`, `footfall`, `landed`, `void_fall`. Keep the meaning or map them explicitly to the foundation event bus. The old `action_released(character_id, clip, origin, direction)` parameter named `clip` actually carries the semantic action (`primary`, `secondary`, `special`), so the forward payload must separate **action** from **selected visual clip** and include the facing.

A release payload needs character ID, action, selected clip/view, cast/action instance ID, canonical simulation time, authored contact index, ground origin, visual attachment point, height and aim direction. One attack instance releases once, even if a slow frame crosses several drawings. Multi-projectile attacks can create several projectiles from that one release. Do not emit damage by polling `sprite.frame==N` every render frame.

Canonical action duration and release seconds stay authoritative. Drawing weights choreograph preparation/recovery around those boundaries; adding drawings must not extend cooldowns, damage windows or input lock. At the release event, the real sprite must display the authored contact drawing before downstream effects sample its attachment. Test exact boundaries, tiny float differences, 60 Hz steps, variable steps and overshoot. The published tests check a narrow release crossing; they do not establish the later discussed floating-boundary fix.

Power duration, expiry, counter windows, ammo, reload, heat and decoys belong to simulation state, not art loops. In particular, use the canonical handoff rather than earlier v4 summaries for Nix Q heat (no reset), Mote orbit mechanics (no autonomous idle damage) and Velvet's prepared counter window (can survive form expiry). Ashe has no separate delayed finisher action in the recovered engine. Its damage releases at exact natural expiry using the current aim. Art can pre-anticipate or display that contact/recovery, but starting a new preparation/lock and waiting for its release would change the mechanics. Overlap with an existing action needs a foundation presentation-priority rule. Mote's straight-angle shard fan must not be described or implemented as homing/converging simulation merely because older art prose used those words.

Pause/inactive/focus loss freezes the shared simulation/animation clock and clears stale held/buffered input. Cancellation must invalidate a pending release and its action-instance ID. Reset clears old projectiles/props/height/decoy/input state. Finite effects expire; idle/study playback never applies damage or moves the actor.

## Attachments and geometry

All image anchors are signed **source-texel offsets from the foot pivot**, positive X right and positive Y down. Re-author them on the new 74 px drawings for every facing; do not multiply old E values by74/96 and treat them as reviewed contacts. No mirrored/rotated E anchor is a replacement for an N/S/W measurement.

| Field | When needed |
|---|---|
| `release_anchor:[x,y]` | Each damaging/casting action and variant; measured at its actual `release_frame`. It may be a fist, blade contact, palm or muzzle rather than a hand joint. |
| `hand_anchors:[point-or-null,...]` | Per-frame attachment track when a tether or persistent effect must stay on a moving emitter. Brine needs the actual harpoon-gun tip through relevant locomotion/reaction/action clips. Track length equals frame count. |
| `held_prop_anchors:[point-or-null,...]`, `held_prop`, `held_prop_baked` | Cairn's separately rendered held boulder. Null hides it; release removes the held copy as the projectile is created. `held_prop_baked` prevents drawing the same object twice. These must replace old hardcoded frame 2–7 positions. |
| `thruster_anchors`, `thruster_direction` (or explicit per-frame equivalents) | Rook's actual backpack nozzle(s), with occluded nozzles omitted. A carried helmet never emits exhaust. The old source hardcodes plume direction, so the forward contract must provide view-specific direction too. |
| `release_ground_anchor:[x,y]`, `release_height` | Separate planar projectile seed/height from its drawn muzzle. A north muzzle drawn high in the image must not move collision far behind the actor. These are simulation/world-unit metadata, not interchangeable with screen anchors. |
| `traversal_frames` | Named load/rise/apex/fall/land indices, or an equivalent phase map, so animation art may change count/order without changing physics. Rook vault has its own map; air-primary runs alongside it. |
| `baked_effects` | Only if an unavoidable baked flash/effect is already in a frame; prevents doubling it. Prefer separate VFX for the new art. |

A tight crop must reconstruct the same virtual frame exactly: draw stored pixels at `crop_offset` within `frame_size`, and subtract the unchanged `foot_pivot` once. The published v3 runtime uses full-canvas PNGs; tight-crop/AtlasTexture margin support is a forward requirement, not implemented v3 behaviour. Native texture bounds and pixel filtering must be checked in Godot 4.7.2 before claiming drop-in compatibility.

The actor's world position is its **ground footprint**. Support elevation and airborne height are separate. The body and weapon move together above the footprint; shadow and depth sorting use ground/support coordinates. The engine owns the full jump arc. Source drawings show articulation and landing compression, never a second baked whole-body trajectory. Terrain/material/height/deck IDs come from the agreed map importer, not guessed body poses. Ladders, deep water and moving platforms need separate gameplay/art contracts if introduced; stairs are not climbing.

## Proposed handoff validations

- Four actual facings and required state/variant coverage, with deliberate missing assets reported rather than mirrored/fallback gear.
- Positive finite frame times, consistent resource/manifest counts, valid release/guard/phase indices and complete attachment tracks.
- Actual release drawing and once-only event under variable simulation steps; canonical seconds unaffected by drawing count.
- Per-view muzzle/contact visible in the actual action, planar first-hit sweeps, no wall/elevation bypass.
- Grounded stairs, physical jump/vault, one landing event, support shadow and unraised-foot depth; Rook fires in air without removing worn/carried equipment.
- Form expiry and counter/finisher/reload/heat edge cases against canonical data; terminal defeat, inactive/pause/reset and bounded effects.

## Reproduce the reference audit

The `source/` folder contains only the 11 exact text sources listed in `source-provenance.json`, each checked against its published Git blob SHA. No character PNG is needed to extract the authoring contract.

```sh
python3 build_legacy_reference.py
python3 validate_reference.py --report validation-source-only.json
python3 validate_reference.py --archive /path/to/MyGame_All_Character_Animation_Sheets.zip
```

The source-only run passed 754 checks. With the existing delivered ZIP explicitly supplied, 3,243 checks passed, covering all 14 sheet metadata files, 239 clips and 2,135 drawing records plus ZIP identity/CRC. The validator does not decode any PNG. These are source/data checks, not a new Godot/gameplay/art acceptance claim. The proposed JSON schema is not formally validated because the optional `jsonschema` package is unavailable here.

## Questions for #149

1. Confirm per-view manifest/resource layout and the foundation's source-texel/world-unit conversion at density 3. The74 px figure height alone is not that conversion.
2. Confirm the controller's cardinal/continuous aim and action-instance event API, ground/support/airborne-height units and presentation priority when Ashe's exact expiry overlaps another action. Do not assume an automatic 3× canonical-to-world conversion.
3. Supply agreed owned `game/` paths once the foundation PR lands, then port this contract and canonical tests there. Until then, no separate project or broad source migration.

References are exact source paths under `prototypes/mygame-animation-studio/` at the commit above: `scripts/roster_actor.gd`, `scripts/animation_yard.gd`, `tools/build_animation_roster.py`, `tests/roster_animation_test.gd`, `WORLD_ANIMATION_CONTEXT.md`, and the five selected JSON attachment files in `art-source/animated/v3/`. `build_legacy_reference.py` shows the data extraction and checks; it never opens or generates a character PNG.
