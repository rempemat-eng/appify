# MyGame character bridge and existing-world fixture

This additive bridge exports the animation studio’s drawings for Expo and renders them through the existing `AtlasWalk.scene` slot. It also provides an inspectable browser fixture on the real Snowy Ridge world tile, with the repository’s actual prop sprites, foot sorting, terrain and walk cells. It does **not** replace the production playable companion or implement the planned action RPG.

The inspected integration target is `main` at `18a8bef77d79bb81163ada1df038fbb3ce6477df`. The animation studio source is the isolated draft PR #241. Existing `AtlasWalk`, maps, save data and world art generators are unchanged. Claude A remains the renderer and map integration owner.

## Reproduce

```sh
node --import tsx scripts/export-mygame-world.ts --studio /absolute/path/to/mygame-animation-studio
node --import tsx lib/mygame-character.test.ts
python3 -m http.server 8774 --directory prototypes/mygame-world-preview
```

Open `http://localhost:8774/preview.html`. Select any of the 14 characters and an authored clip/view. Arrow keys or WASD walk over the **existing** map’s open cells. The fixture reports missing requested directions and retains the selected drawn view; it never mirrors art. A walk-cell overlay makes collision inspectable. Stair poses can be inspected as drawings; the fixture does not claim that a stair exists in this tile.

The exporter verifies each source frame’s decoded RGBA SHA-256 against the studio manifest, retains weighted durations and authored event frames/anchors, and packs cropped PNGs into per-clip atlas pages, with each side at most 4096 pixels. A view retains its own virtual frame size/foot pivot; cropped frames retain their stored size and crop offset. Both stored RGBA and reconstructed virtual RGBA hashes are verified when supplied. `provenance.json` records source manifest hashes and the exact world-source hash. `registry.ts` provides static Metro image imports; only the displayed clip needs decoding. `character-runtime.mjs` is generated from the **same** pure TypeScript bridge used by Expo, so the browser fixture does not maintain a separate animation sampler.

## Existing renderer connection

`components/MyGameWorldCharacter.tsx` exports:

- `MyGameWorldCharacter`, an independently positioned node for the existing `AtlasWalk.scene` slot.
- `MyGameAtlasWalk`, an additive wrapper accepting `guests`, plus existing `AtlasWalk` props. It supplies guest nodes through that slot. The legacy playable companion is still drawn by `AtlasWalk`.

Each guest supplies its exact character, view, clip, shared-clock elapsed time, **region-local ground foot**, explicit support and airborne height, world unit, asset density, DPR and static image resolver. Example asset imports:

```tsx
import {
  myGameCharacterAssets,
  myGameCharacterImages,
} from '@/prototypes/mygame-world-preview/registry';
import { MyGameAtlasWalk } from '@/components/MyGameWorldCharacter';

// The owner supplies elapsed from the scene's active-time clock, and worldUnit
// from the same pixelScale(screen.width, DPR) used by AtlasWalk.
<MyGameAtlasWalk
  region="valley"
  width={width}
  height={height}
  active={active}
  guests={[
    {
      key: 'cairn-preview',
      asset: myGameCharacterAssets.cairn,
      view: 'E',
      clip: 'idle',
      elapsed,
      foot: regionFoot,
      supportHeight: 0,
      airborneHeight: 0,
      worldUnit,
      assetPixelsPerWorldPixel: 2,
      devicePixelRatio: dpr,
      reducedMotion,
      resolveImage: (key) => myGameCharacterImages[key],
    },
  ]}
/>;
```

The opt-in landscape fixture uses **960×540 logical texels / 480×270 world pixels at density 2**. The existing terrain and new character source texels share that scale. Its `?fhd=1` mode fills a 1920×1080 viewport with exactly 2×2 screen pixels per source texel. This changes no production screen framing; the pending landscape-framing work remains with its owner. `projectMyGameCharacter(...).crisp` reports whether source texels occupy whole device pixels on the caller’s grid; production density and final character proportions still need art/renderer-owner acceptance. No implicit `96 source pixels = 96 world pixels` conversion or silent density-four rescale occurs.

The character’s full composite is snapped once, its weapon anchor uses that same transform, its shadow stays on the support surface, and z-depth follows the unraised, **unscaled region-coordinate** ground foot, matching the renderer’s prop zIndex (not screen pixels). If a caller uses a deck, it must pass AtlasWalk’s explicit level depth offset. A jumping character cannot jump in front of a tree merely because its picture moved upward. This bridge has no private animation timer; inactive/reduced-motion policy remains with the scene owner, and reduced motion displays a static meaningful action/guard pose without changing combat time.

## Verified world contract and remaining production blockers

`makeMyGameWorldSupport` reads the actual `worldTiles` RLE walk/material fields across all four planes. Unknown and negative-outside points are blocked. Current generated `worldDecks` and legacy `zoneDecks` are both empty, and generated tiles have no `tiers`. The current source consequently has no authored stair/ramp/lift placement or numeric terrace-height contract. If a future tile contains tiers/decks, this adapter explicitly requests a height resolver instead of silently flattening it.

The current playable renderer accepts an old `GuardianPet`/NAP companion and left/right movement. The proposed new character animation document is not wired to gameplay, and the action RPG world/ability API has not landed on main. `WORLD_CANVAS` defaults off. Therefore these remain external integration tasks:

- An owner-approved optional actor renderer replacing the legacy playable companion and receiving the actual movement/action/aim clock.
- Authoritative active-gameplay collision, airborne hit policy, landings and ability events. `crossedRelease` is only a presentation crossing helper and does not apply damage.
- Authored stairs, ramps, deck connectors, elevations and transitions in the real map contract.
- Approved per-view art, scale/density and final style acceptance.

The bridge reports absent clips/views rather than substituting a base ability or mirrored facing. Completing those contracts is necessary before saying the new roster is integrated into the full production game. The actual-map fixture is a concrete asset/render/collision integration test, not that claim.

### Proposed owner-reviewed playable hook

The smallest player replacement hook is an **optional** `actor` render callback on `AtlasWalk`, defaulting to its existing companion. It should replace both `pet(true)` and `pet(false)` calls so the hidden-behind-props ghost uses the same frame. The owner should pass local box dimensions/foot pivot, actual facing and walking state, active/reduced-motion state, and whether the call requests a ground shadow or ghost. The callback must render **inside the existing positioned player wrapper**, preserving its shared-value movement, camera, ground-foot zIndex, landing transform and deck handling. It must not insert an independently positioned guest inside that wrapper. New combat ownership can later provide an actual animation/action clock through the callback; a renderer hook alone is not a four-action game API. No hook is applied in this branch because `AtlasWalk` is another lane’s owned file.

## Canonical ability recovery

The earlier published playtest artifact `NapAttack_Desktop_Playtest.zip` was recovered read-only from its existing Library identity `libfile_a8686f8b8cfc8191b71d7f2712de1cd8`. Its ZIP SHA-256 is `0b0374b323d4525317b32deb57560a85c947e37fa1801a0835249f76cc05cd1c`; archive CRC passed. The latest Web entry is `entry-6fdd0ef25567acc156c4a1e86a9a36fe.js`, SHA-256 `94f8b4e105ea17d635f2fe7ae6a23d33b4f2fe1cc764761d64a4423b8d1ef82c`. Metro module 3501 has no dependencies and exports the original 14-character catalogue; module 3500 depends only on 3501 and exports the pure combat engine (`createCombatState`, `stepCombat`, `samplePose`, etc.). These modules were evaluated in an isolated Node VM with only their exact dependency, recovering executable reference rules as well as descriptions. The original unpublished TypeScript commit `6413b8b1f094cb0acd5f104ca51264c9689a92f7` is not present on the remote; this recovery is **compiled reference code**, not a claim to have recovered its original TypeScript source.

Critical recovered rules were handed to the art/runtime lanes before further authoring:

- Pendle’s normal secondary fans **up to three remaining revolver rounds**, then reloads. Longshot primary draws the western marksman rifle, while **Longshot secondary is rifle-stock melee**, not a rifle fan.
- Rook’s Thruster Vault keeps carbine aiming/fire available while airborne. It avoids ground melee, but projectiles/explosions still hit. A blanket prohibition on airborne attacks would change the canonical kit.
- Clack’s separate concussive vent works while the launcher reloads; Siege Breaker fires three-rocket salvos and stays mobile.
- Ashe’s Cinderhelm ends in an aimed fire finisher; Nix’s Afterimage stays at its activation origin and lasts until its first hit or three seconds; Rook’s Orbital Rig creates exactly two finite turrets.

The exact catalogue and bounded original modules are preserved in `prototypes/mygame-world-preview/reference/`. The catalogue module SHA-256 is `8b2dc37132bc29f9e9f184b42abc209933a2ba98f35ef46e9c1061838492ad6f`, and the engine module SHA-256 is `21aa782577f3d2fc51389efdd80c4c61a1a7ddd48d128e01eb318daa75d6bc10`. `adapter.mjs` checks these hashes and evaluates only those two modules with their exact dependencies. Its opt-in reference-helper mode exposes original pure release functions for extraction; it is Node-only and is never imported into Expo. `runtime-constants.json` records all 14 base/powered duration and release times, direct release snapshots, cooldowns, movement, form, guard and vault values. No source evaluation or runtime download occurs in the shipped character component.

The full recovered catalogue/engine was supplied directly to the runtime owner so powered-secondary art and effects are based on the established rules rather than inferred names.

## Tools and validation

This lane used read-only Git/GitHub inspection, isolated Git worktrees, Node/TypeScript (`tsx`, `tsc`), Python/Pillow for deterministic pixel-preserving atlas packing, the existing Library connector/materialization helper for the earlier reference artifact, and Playwright/Chromium for visual browser checks. It introduces no image-generation model or new service dependency. New images are derived exactly from the existing authored frame PNGs; the art lanes own new drawings and their source provenance.

`lib/mygame-character.test.ts` checks weighted timing, one-shot terminal frames, guard holds, a skipped-render release crossing, stale-clock rejection, exact facing/ability lookup, reduced-motion poses, device snapping, airborne body/weapon alignment, support shadows, ground-depth sorting, every exported atlas rectangle and all 573,440 current real-world cells. TypeScript checks include the new native component; generated preview modules remain outside production discovery. Browser validation exercised all 14 baseline selectors and all 239 original E clips with zero page errors, confirmed 960×540 logical pixels display at exactly 1920×1080 in FHD mode, and then checked real cropped v4 art. Keyboard input stopped at world foot (376,1602), remained there under continued west input, and the next west cell was verified closed. A south movement to (378,1682) crosses an existing pine’s ground foot; north/south captures and measured results are preserved under `prototypes/mygame-world-preview/qa/`. This is direct collision-rejection/depth evidence, separate from the 48 open-route samples. The exporter also passed a synthetic 320×320 crop/pivot reconstruction and v4-over-legacy-E selection case; synthetic art was never included in the shipped preview. The initial export under `assets/mygame-characters` correctly failed `check:assets` because these new images had not been graded in the owned asset ledger. The final layout deliberately relocates all character/fixture exports under `prototypes/mygame-world-preview`, which is review/comparison-only and excluded by the existing ledger checker. No asset-ledger rule, grade or production sprite is changed. Materializing production images requires explicit art/ledger acceptance; copied current-world fixture images do not become approved rebuilt-region art through this preview. Full repository verification and hosted CI remain the final integration owner’s gate.
