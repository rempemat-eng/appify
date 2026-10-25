# MyGame combat and animation handoff

This is a text-only handoff for Claude A's foundation and fourteen-character redraw. It contains no PNGs, engine project, production port or new dependencies. The 25 October decisions supersede the generated-frame continuation: preserve the cast and equipment in `ART_DIRECTION.md`, redraw approximately 74 px figures in four facings on the 960×540 logical grid, and use world density 3. At 1920×1080 the logical grid displays at 2×, and at 3840×2160 at 4×. West is separately drawn and relit.

The adopted target is Godot 4.7.2 with LimboAI, Phantom Camera, GdUnit4 and Python-kit/Tiled+YATI maps. These are coordination targets, not a claim that the foundation or those versions were installed or tested here. At the source check, main is `18a8bef77d79bb81163ada1df038fbb3ce6477df` and `claude-a/godot-foundation` is not remotely available. Combat porting starts after that foundation lands and file ownership is agreed on #149. No second game project is started.

## Read the data in this order

1. [Canonical ability data](canonical/abilities-v1.json) defines balance: action/release seconds, damage, range, cooldowns, resources, form timers and stateful branches. Its original unit system is preserved.
2. The [animation contract](animation/runtime-contract.md) describes the per-facing exports and events needed by the future runtime. New-art coordinates and release drawing indices must be authored against the redraw.
3. The [legacy east reference](animation/legacy-east-animation-reference.json) supplies the older prototype's actual drawing times, release indices and screen-space attachments as reference only. It is not canonical balance and must not be numerically scaled into the new art.
4. The [port regression notes](port-regressions.md) identify the behaviours that the future Godot tests must preserve.

The source hierarchy matters. The published studio in draft #241 is an east-facing 4.5.1 prototype with simplifications. Draft #242 preserves the independently hash-checked original catalogue/compiled combat engine. Later prototype descriptions are not authority where they disagree with that recovered engine. The original unpublished TypeScript source has not been recovered.

## Units and anchors

The reference simulation uses a 320×180 arena, original planar distance units, seconds, damage and radians. Density3 is a drawing/projection setting. Do not multiply simulation speed, radius, reach, damage or timers merely because a drawing has three art texels per world unit. Claude A's foundation must declare the transform between canonical combat units and its world coordinates once.

Every new facing needs its own foot pivot, release/contact attachments and phase indices. Screen-space muzzle/hand offsets are relative to that view's foot pivot; they are distinct from the simulation's planar projectile origin and any physical height. The reference's generic player-projectile seed is 9 canonical units along each projectile's launch direction, including its fan-spread offset. A south-facing barrel can project near a foot while still being high above the ground. Use a separate projection/height contract rather than treating its screenY as planar range.

A crouch becomes shorter. Cropping preserves its offset, weapons retain their source scale, and a wider canvas never shifts the world foot or collision body. The new 74 px target does not inherit the old 96/112 px body heights or192/256/448 px padding choices. Per-facing anchors are not obtained by mirroring E.

## Production boundaries

#241 remains draft and must not be merged as-is. Its generated PNG masters are reference material outside this handoff. No raw-art history rewrite or LFS migration is performed. #242's Expo scene-slot fixture is also reference-only after the engine decision. Both existing source heads remain unchanged.

Jumping and stairs must consume the foundation's actual support/elevation contract. The older pure combat reference provides Rook's vault, not a complete world-jump or authored-stair system. Do not copy prototype course dimensions or invent map stairs in this data handoff. Body, shadow and depth follow the actual ground foot/support; the fixed-camera preference remains in force unless Matt changes it.

Questions and ownership agreements belong on [#149](https://github.com/rempemat-eng/appify/issues/149). The port's agreed files, physics units, animation-facing/aim policy and exact pinned plugin/importer versions remain with the foundation owner.

## Validation scope

The accompanying checks validate the canonical reference and text/data contract only. They do not certify the new redraw, Godot 4.7.2 execution, GdUnit4 compatibility, native-device performance, map integration or a finished game. Historical4.5.1 prototype test counts are not reused as evidence for this handoff.

Tools used for this handoff are Python 3 standard-library JSON/AST/hash checks, Node.js 24 reference probes, the GitHub connector and independent source/data audits. No image generation or image editing was used in this continuation.


## Files and reproduction

The [timing table](ability-timing-summary.md) is the short animator reference. Exact effects, resources, hit shapes, state branches and timing are in `canonical/abilities-v1.json`; its `art_contract` fields deliberately leave new-art frame indices and facing anchors to Claude A. The [proposed manifest schema](animation/manifest-proposal.schema.json) defines structure; cross-field and runtime checks remain necessary. [Canonical semantic review](canonical/data-audit.json) records the resolved discrepancies.

From this handoff directory, using Node.js 24 and Python 3:

```sh
node canonical/build-ability-data.mjs
node canonical/validate-ability-data.mjs
python3 animation/build_legacy_reference.py
python3 animation/validate_reference.py
```

The canonical builder and validator need only the bundled hash-checked text references and standard Node modules. The animation extractor uses Python's standard library and the bundled published source-text fixtures under `animation/source/`; it does not import the old art renderer or open a PNG. If the existing `MyGame_All_Character_Animation_Sheets.zip` is available, pass its actual location to `animation/validate_reference.py --archive` for the additional independent archive-metadata comparison. The archive is intentionally not included.

Final local evidence: 166 canonical source-backed probes passed; 754 source-only animation checks passed; 3,243 animation checks passed with the existing archive metadata, and two corruption controls failed as expected. The archive check decoded no PNGs. These are separate scopes, not new-art or engine-compatibility passes.
