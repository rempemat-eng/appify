# Highgarth kit concepts (Y14)

MyGame proposal packet for Claude A review. **Not approved, drawn, buildable or placeable, including labs.** The nineteen records describe thirty-two concept variants and map seventeen source building records. They extend the W0 concept format outside the live piece library; no existing catalogue, town, schema, painter, material, package or gameplay file changes.

## Authority and provenance

The brief is [Claude A's issue149 comment6464788488](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6464788488). Its wait gate cleared when the Japanese post-town plan landed on [PR303 at911edac6173ebf4398bcbf54b6171e4e68e62e13](https://github.com/rempemat-eng/appify/pull/303): the pinned town now declares `style.name=old_japanese_post_town`.

`scripts/highgarth/manifest.json` records exact commit, path, Git blob and SHA256 provenance. The town fixture is blob `bb6e79e619497d53b96155bce364c3675a7b9f8e`; the W0 structural schema fixture is blob `da824ba6eac1a9110f7ecaddbff7a416adc6a69b` from PR306 at `7e816ab09107424af3fc7b1d01689955de8b57c6`. Both fixtures preserve source bytes. The brief snapshot preserves its body with one final LF. These are review evidence, not edits to the receiving owners' files or approval of the source plan.

The existing `napattack.piece/1` protocol identifier is preserved for W0 compatibility. It is a schema identifier; all new product prose calls the game MyGame.

## Packet

Widths below are source **world-pixel ground-footprint ranges**, not sprite dimensions. One world cell is8 world pixels; drawing density is24 art pixels per cell. The manifest retains exact source depth ranges too. The endpoint classes are planning bounds, not a requirement to draw every intermediate size. Named variants remain proposals.

| Family (`highgarth_` prefix) | Variants                       | Source width / evidence                                             |
| ---------------------------- | ------------------------------ | ------------------------------------------------------------------- |
| machiya                      | narrow_frontage, wide_frontage | 24–64; eight Garth Street building records                          |
| post_inn                     | narrow_envelope, wide_envelope | 56–104; two honjin records                                          |
| kura                         | compact, wide_envelope         | 32–48; two storehouses                                              |
| minka                        | compact, wide_envelope         | 56–88; two thatched houses                                          |
| temple_hall                  | plinth_hall                    | 96–128; temple building                                             |
| pagoda                       | five_storey                    | 32–40; pagoda building                                              |
| temple_gate                  | court_gate                     | Width deferred; temple district                                     |
| shrine_gate                  | timber_run                     | Width deferred; seven source gate positions are repetition evidence |
| stone_lantern                | court_edge, stair_landing      | Width deferred; temple court                                        |
| bell_frame                   | court_frame                    | Width deferred; temple court                                        |
| footbridge                   | single_span, abutment_fit      | Width deferred; brief                                               |
| terraced_field               | paddy, oats                    | Width deferred; terraced fields district                            |
| retaining_wall               | straight_run, stair_return     | Width deferred; fields and upper terraces                           |
| watch_keep                   | tarn_front                     | 48–64; black watchkeep by tarn                                      |
| grey_paving                  | street_fill, street_margin     | Width deferred; brief                                               |
| raked_gravel                 | court_fill, court_margin       | Width deferred; temple court                                        |
| moss                         | stone_edge, step_margin        | Width deferred; brief                                               |
| stone_steps                  | temple_flight, keep_flight     | Source route widths3 and2 cells, not tread/rise/image dimensions    |
| snow                         | upper_slope, path_margin       | Width deferred; brief                                               |

The construction notes retain dark timber, lattice fronts and deep double eaves for machiya; post-town lodgings; white plaster kura; thatched minka; temple stone plinths; five pagoda storeys; timber shrine gates; stone lanterns; bell frame; bridges; retaining walls and the small black keep on battered stone. Vermilion is confined to the temple gate and pagoda trim. No modern elements or real script are proposed. Claude A draws the art.

## Boundaries and unresolved source details

All geometry beyond the W0 z-sort hint is deferred: image extents, foot, footprint, overhang, collisions, support/deck heights and interaction anchors. Size classes are provisional review routing only. Measure opaque art against the current size guide after drawing; never stretch sprites to match plan footprints.

`clearance=0` is an unallocated placeholder, not permission to obstruct routes or omit front landings. Ground labels and relations express review intent; unregistered selectors, orientations and composition need W5/Claude A review before promotion. Wall-to-wall fronts must preserve approach access and keep eaves separate from solids. Terrain and tier records allocate no material, transition or painter bindings; the retained W0/W1 schema and bake decisions remain with their owners. Contact-AO metadata does not supply rendered evidence.

The pinned plan has20 building records, all counted, matching its declared20. It still contains a legacy chapel purpose label on `highgarth-b001`. Six machiya bay records disagree with the later two-storey style brief: b012/b013/b019 specify3 storeys; b016/b017/b018 specify1. The manifest and checker expose these inconsistencies rather than silently rewriting the source. Claude A must reconcile them before art/layout acceptance. Bathhouse, mill and generic house source forms are outside this Y14 brief; the seventeen mapped records are not a claim to cover every town building or validate the full town.

## Checks

From the repository root, install the focused development dependency and run:

```sh
python3 -m pip install -r scripts/highgarth/requirements.txt
python3 -m unittest scripts.highgarth.test_check
python3 -m scripts.highgarth.check --json
```

The checker requires jsonschema; missing it is a failure, not an optional skip. It verifies the pinned bytes/Git blobs, W0 structural schema, exact family inventory, source building mappings and widths, explicit proposal flags and selected deferred-placement boundaries. Invalid-packet tests cover approval/runtime bindings, false-versus-zero types, malformed JSON/Unicode, missing provenance, source drift and hidden source limitations. The checker is read-only. The dedicated Highgarth workflow runs these focused checks without editing shared package or Godot workflow files.

A metadata PASS is not strict runtime material/geometry validation, rendered-art review, placement acceptance or gameplay acceptance. Required repository checks remain `npm run verify`, `npm run check:art-repro` and relevant kit/Godot checks on the final source.

## Claude A's next action

Review the families and source inconsistencies, settle widths/supports/front landings and material bindings with the receiving owners, then draw and approve any chosen pieces. Promote through the existing library/editor process only after measured geometry and placement review. This packet grants no implementation permission for gameplay or new art direction.

[Claude A's later comment6467789932](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6467789932) permits X3 settlement-life work and describes Y15 after the next PR303 push. Those are separate future claims; this branch remains solely Y14.
