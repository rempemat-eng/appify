# C26: keepsakes and historical world layouts

Baseline: `0798b8287dbd1a70617183b2ca1bd5f7d203121d`, 19 October 2026.
Tests and synthetic fixtures only. No model, save format, art or gameplay changes.

The fixtures use literal historical inputs, independently of the current store's
defaults and layout migration functions. The approved layout-3 expectations pin:

- An explicit layout-1 `lava` spot and an unversioned predecessor both move into
  `west`, preserving the exact fractional point inside the caldera.
- A layout-2 town spot stays in town and moves down 1152 region pixels when the
  Frostline grows the valley north. Reload does not apply the shift twice.
- One valid hut placement and one garden placement survive together, globally
  deduplicated by item. An undiscovered item is dropped even at a geometrically
  valid point; a discovered item at a now-invalid footprint is dropped separately.

`check:saves` loads these through the actual game store, migrates them, writes
the real save codec and reloads. It checks idempotence, fractional GRASS and
opaque account/decor field preservation. `check:game` independently checks the
resulting zone-local point and exercises actual `placeDecor` and `storeDecor`:
unfound refusal, moving within the hut, moving to the garden, one copy only,
and repeated putting-away without loss of discovery, ownership or progress.

All native/storage/network boundaries remain the existing test substitutes.
No real account, player save or backend is read or mutated. This supplements
the pure `world-save.test.ts` checks; it does not duplicate C22's mapSeen/hutLook
integration. C22's unmerged tests should be preserved when merging these files.

Lane handoff: C25's `lib/sound.ts` and visual component fixes remain Claude-owned;
this PR does not change those files. C23's richer semantic exports and C24's
runtime corrections are still separate handoffs. Review-only PR #41's visual
findings are not certified or fixed by these persistence tests.

Not tested: new hut artwork in PR #38, physical world routes or art, real React
or device storage lifecycle, browser/phone/native runtime, multiplayer or backend.
