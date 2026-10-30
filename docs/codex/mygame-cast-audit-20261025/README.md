# Landed cast compatibility review, 25 October 2026

The new cast has four-facing animation metadata for all fourteen characters, but its clocks and some state variants do not yet match the recovered combat contract. This review gives Claude A and C60 a concrete reconciliation input. It adds no production code, art or alternate runner.

Reviewed main: `2f88ca5381388affc1e5f457678cf09a9e481749`. Canonical ability source: draft #245 at `1820a07c5ae8b745e239aa2aaa25e0c5ef483d42`, Git blob `03ba3bd1e0b71a1b31719cb3899459069f27b4b4`. #244 remains a separate original-source audit supplement. Claude A owns cast/actors/integration; C60 stays with the economy slot. This is a new audit branch, not an update or takeover of their branches. #241 and #242 stay reference-only.

## Findings for the owners

1. **Retiming:** all 69 supplied primary/secondary/special action clips differ from canonical release or completion times. The [timing table](timing-summary.md) and [proposed frame schedules](retiming.json) fit preparation and recovery separately while preserving each current contact index. They are review inputs, not imported art. Nix's ordinary laser contact is 0.3300 s in the art versus 0.0798 s canonically; his decoy is 0.3299 versus 0.0500. Rook's vault begins at 0.2200 versus 0.0500. Simply increasing the whole clip speed will not generally match both release and end.
2. **Variant coverage:** every character lacks an explicit `powered_defeat`; Pendle additionally lacks `powered_secondary` for the rifle-stock strike. No explicit clip/mapping is present for Brine's ordinary/powered empty-tether strike, Rook's ordinary/powered airborne primary, Velvet's counter or Ashe's natural-expiry contact/recovery. An explicitly reviewed equivalent or layered composition can satisfy a variant; this report does not require multiplying files where the choreography can be shared safely. Brine already has nineteen extra empty-equipment movement/reaction clips; those do not identify the missing secondary action.
3. **Live-state switching:** `Player.set_character` can replace defeat with idle while retaining zero HP, and can leave roll/swing state active beneath idle artwork. [Runtime findings](runtime-findings.md) provide the narrow owner fix and proposed regressions. These are source findings, not a claim that the game has been patched.
4. **Release presentation:** `CastSprite.advance` synchronises the final drawing before returning crossed indices. A coarse step can therefore emit a release index while a later drawing is actually displayed. Full loop crossings are lost when the final frame equals the starting frame. Frame-zero release is a forward-contract gap, not a current-asset failure. See the runtime findings for precise scope.
5. **Facing attachments:** use `clips.<clip>.facings.<facing>.frames[i].anchors`, with a named emitter/contact and explicit validity. The clip-level `release_anchor` is a single unqualified pair. It cannot stand in for all four facings. Bramble intentionally falls back to the preceding frame's arrow tip when the release drawing no longer contains the arrow. Both sets of anchors are retained in the snapshot.

The existing C60 request for canonical-unit conversion and a player/action-driver integration agreement remains on #149 (comment 6396874102, escalation 6399868256). No conversion or actor edit authority is inferred here. The actual cast resource layout is now established; it need not be re-requested. Support-height, action lifecycle, wall/line-of-sight policy and Ashe expiry presentation still need a coherent integration decision.

## What was checked

`audit_cast.py` verified the exact Git blob identity of the canonical JSON and every landed manifest. Across 14 characters, 341 clips, 11,656 frame records and 67,376 declared anchor points, it checked four-facing coverage, duration/count consistency, positive finite timing, release/hold indices and onset times, role counts, atlas rectangle/sheet metadata, declared bounds and anchor coordinates. It derived 69 contact-preserving schedules and the missing-variant list. `report.json` is the result; `source-snapshot.json` is a compact metadata extract with source identities, not a copy of the PNGs.

All metadata checks passed. The report still contains the timing and coverage gaps above. Passing metadata is not art acceptance: PNG pixels, face readability, anatomy, equipment continuity and light are not certified. The [fourteen-character world criteria](character-world-acceptance.md) define the necessary rendered/interaction checks without inventing terrain access, map dimensions or balance.

Repeated extraction produced identical report and retiming files. A changed-byte control failed the Git identity check; a zero-duration control, with its fixture hash deliberately updated, failed the duration check. The scripts use only Python's standard library and do not download anything.

Seven source-method probes were also executed with Godot 4.7.2 against fake boundary objects; their log and extractor are included. They demonstrate the source behaviours in the runtime findings, not whole-Player or integrated gameplay validation.

No full `npm run verify`, art reproduction, GdUnit suite, whole-game Godot run, gameplay recording or device test was run for this documentation/data branch. It stays draft for Claude A/C60 review. Historical prototype results are not reused as current evidence.

## Reproduction

To repeat the calculations from the bundled metadata:

```sh
python3 audit_cast.py --snapshot source-snapshot.json --out /tmp/cast-review-repeat
cmp report.json /tmp/cast-review-repeat/report.json
cmp retiming.json /tmp/cast-review-repeat/retiming.json
```

For a fresh source audit, check out main at the exact reviewed SHA and #245 at its pinned SHA. Make a temporary input directory containing `pins.json` from `source-snapshot.json`'s `pins` object and `canonical.json` copied byte for byte from #245's `canonical/abilities-v1.json`. Then:

```sh
python3 audit_cast.py --inputs /tmp/cast-review-inputs \
  --cast-dir /path/to/pinned-main/game/assets/characters --out /tmp/cast-review-fresh
```

The extractor rejects different source blobs. It reads JSON only; it does not import the legacy painters or open any images. Tooling used: GitHub connector for exact source reads/publication, Python for extraction/checks, and independent read-only source review. All source changes in this PR are confined to this directory.

## Cleanup

No old generated PNG enters this handoff. Temporary raw manifest copies and repeated output can be removed after the source-hashed extract is published. The remote #241 art is preserved as the agreed reference branch; removing it from history or changing LFS is not part of this audit. Existing user downloads, saves, the Expo app and other workers' files are outside cleanup scope.
