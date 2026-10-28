# Combined editor proposal: E2/r1

MyGame · slot=mortar · [claim and scope](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6483540277).

This assembles the delivered editor work on a new Codex branch from the real PR302 head. It is a draft integration proposal. It grants no piece approval, map approval, production rollout or main merge. The original source branches remain unchanged.

## Exact inputs

| Input | Commit                                     | Contribution                                                 |
| ----- | ------------------------------------------ | ------------------------------------------------------------ |
| 302   | `04228475cbd9fb76e0a0a9af52240d7e40a5d858` | Unchanged editor/woodland proposal baseline                  |
| main  | `7f83ee03781752f6c4db068185142040c8a2c319` | Current reviewed engineering, classifier and check commands  |
| 341   | `af563582b2f95e43f03dad0133754aa46b072186` | W0 catalogue + W1 source metadata + malformed concept intake |
| 312   | `fb375325aa1641084a15e26c4a692bc42694afa8` | W3 dock; includes current W4 and W5/W6 predecessors          |
| 305   | `64c212fc91027020600297b5258de7301968d46d` | Latest literal logical-ID and round-trip repair              |
| 317   | `47ac43542bd02d85b906b206faa0a41ec67855f4` | W7 cell-coordinate intake; includes W7 pixel fixtures        |
| 315   | `36af9a5b1cbb038f5c1515a93156b2a496f943ca` | Python walk cell-coordinate normalization                    |
| 347   | `fd4cf36dbff7ff3c672678a559c885acbe0655e1` | Baked scene/piece review intake and structured failures      |

The [machine-readable input manifest](editor-integration-inputs.json) records the actual source trees and every changed path/blob/mode. PR341 already contains unchanged W0/306 and W1/307. PR312 already contains W4/304 and W5–W6/311. PR317 already contains W7/308. Those ancestors are not merged again. The latest W2/305 repair is selected over the old W2 ancestor retained by earlier stacks. Current main is a genuine integration parent, bringing its reviewed models, classifier and current checks into the combined proposal.

## Integration decisions

Only two files have textual merge conflicts:

- `package.json`: retain the complete current-main `check` chain, including `check:quests`; retain the editor's complete `check:kit` chain, which extends main's three checks; retain `check:kit-scene`; union the existing six `check:review` modules without dropping either main's PR-sheet tests or W1/W5/W6/walk tests. All non-script package fields and the dependency lock remain unchanged. Both dedicated concept and scene-intake workflows remain present.
- `scripts/review/run.py`: keep W6's exported JSON-plan intake, physical findings and JSON-only route. In the normal zone route, retain PR347's `SceneIntakeError` handling, incomplete/error report and exit1. Existing plan validation and explicit intake failure handling both execute; neither implementation replaces the other.

The initial package-side audit stopped before a write when it also detected the existing `check:kit` value difference. The final union preserves that entire editor command rather than selecting main's shorter value. This was a source-resolution guard, not a successful validation invocation.

## Combined-interface regression

The first combined run of the two existing physical/intake modules executed42 methods and failed one unchanged W6 CLI test. Its route fixture relied on an old guessed solid collider for the woodland lab bench. W1's selected source metadata instead declares `collision: null` and an empty footprint for that bench. The invalid plan still exited1 with `rules.seating`, but it could not produce the specifically asserted `rules.route_clear` from that non-solid object.

Under the [lead's narrow fixture extension](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6483718766), only that test fixture is adjusted. The valid real lab control is unchanged. Its invalid copy adds the already existing lab family `woodland_boulder` at the bench's existing foot, then applies the same route-cell mutation. That family's unchanged solid rectangle overlaps the mutated route cell. The exact CLI exit1, positive fault count and `rules.route_clear` assertion remain; a `rules.seating` assertion is added so the bench refusal is also retained. No collider, library metadata, checker rule or threshold is changed.

The same42-method combined command then passed, EXIT0, with every10920 tracked source file's bytes and modes unchanged across execution. The original red log/result is retained separately; it is not relabelled as a pass. These focused tests ran on the assembled production source before these two review documents were added. Existing Python ResourceWarnings remain visible; no full lint result is claimed by this focused run.

## Source invariants and freshness

- Every changed source file except the package composition, review-runner composition and authorised test fixture matches an exact input blob/mode. The complete source delta is338 paths; these two new review documents make340 changed paths in the submitted proposal.
- `game/actors/player.gd` remains exactly blob `0dd01672a14fda097b3db2e0da8643c5eca6307b`, shared by PR302 and current main.
- All106 live piece JSONs remain candidates, and all129 W0 concepts remain concepts. Their blobs are unchanged from the selected PR341 input. No approval is promoted and no new piece is authored here.
- No production raster changes. The only added raster paths are the five existing W7 test-fixture PNGs copied unchanged from their reviewed input.
- All53 recorded W7 producer-input hashes match the assembled source. No reference image or reference metadata is regenerated. A matching input hash is not a new cross-engine render comparison.
- No map/town/NPC authoring data or gameplay rule is edited. Current-main model data and save-migration source are consumed unchanged as existing inputs, not activated as a new slice feature.

## Validation and acceptance still required

| Evidence                                                                     | This proposal's result                      |
| ---------------------------------------------------------------------------- | ------------------------------------------- |
| Exact input ancestry, copied blobs, package union and Player/approval guards | Pass                                        |
| Existing W7 committed input-hash audit                                       | 53 match; no regeneration                   |
| Existing W6 physical + PR347 intake focused methods                          | 42 pass, EXIT0; original red retained       |
| Full combined Godot and kit checks                                           | Not run                                     |
| Full combined verify, zero-warning lint and ordinary art reproduction        | Not run                                     |
| Current combined editor smoke, rendered dock and cross-engine parity         | Not run                                     |
| Current E2 Y12/scene acceptance packet                                       | Not run                                     |
| Matching hosted CI                                                           | Pending draft; skips/filters are not passes |
| Matt's approval on the applicable PR                                         | Not granted                                 |

The full serial validation slot belongs to the lead's currently allocated task. This proposal starts no competing heavy chain and stays draft until its own exact frozen checks pass. Each input's earlier green checks remain evidence for that input, not proof that this combination passes.

The accessible PR344 sheet remains its original PR302 baseline with31 passing and44 failing PNG rows and incomplete kit-scene coverage. It is not rewritten as a green result because this assembly includes a scene-intake repair. Fresh combined review evidence and the written Eastward/art gates are still required. Matt's explicit PR-specific OK is required before an art/editor merge. X5 and the first playable slice retain actual W1–W3 main inclusion and approved Crossroads-kit prerequisites.
