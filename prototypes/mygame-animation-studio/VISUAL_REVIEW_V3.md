# Independent visual review: v3

Review begun 24 October 2026. This review is independent of the agents drawing the extensions and of the runtime implementation. It records visual observations, not approval based on image hashes or frame counts. Final import/runtime evidence belongs in VALIDATION.md.

## Review method

Inspect each available source master against the preceding exported idle, then inspect the selected packed drawings at their gameplay density. Review weapon ownership, anatomical side, the preparation/contact/recovery order, return-to-loop seam, foot support, airborne registration and powered equipment. A new sheet with the correct number of cells can still contain an incoherent sequence or a missing body.

The raw tool preview includes low-alpha colour fringes. Those are not automatically an exported defect: the established importer thresholds alpha. Morel, Clack and Bramble extensions had no vivid red pixels at alpha >=128 in the first diagnostic. Colour-keying or repainting was not requested on that basis. Actual packed edges still need inspection.

## Defects caught before final selection

| Source | Independent finding | Required action / state |
|---|---|---|
| Ashe extension64, primary | Current row order contains an overhead strike followed by multiple thrust peaks; it does not read as one sixteen-pose strike | Sent to art owner/root for a coherent reorder or targeted sixteen-pose replacement. Re-review selected order |
| Morel extension64, primary | The visible flask alternates between hands while another arm extends; potential phantom retained flask during release | Art owner producing a targeted primary16 with one throwing hand and the other hand fixed |
| Velvet extension64, primary | Only seven independent bodies appear in the first primary row; extractor confirms missing row3/col8 | Hard rejection of that primary row. Art owner asked for a complete targeted primary16; do not pad or duplicate a body |
| Mirra extension64, primary | Two short gesture cycles and repeated outward peaks interrupt one long release | Candidate reorder sent to owner; selected order requires re-review |
| Cairn and other jump source rows | Source rows include whole-character vertical displacement as well as tucked limbs | Root will use per-frame supported-bottom registration before the simulation supplies the airborne arc. This is pivot registration, not new pose generation |
| Rook extension64, primary | Source release frame includes a muzzle flash | Align release to that frame and do not layer a contradictory second authored muzzle. Projectile should leave the actual barrel |
| Nix cycles32, primary3 | A flesh palm replaces the mechanical emitter in a load pose | Single-frame generated replacement now restores the metal left arm; checked independently |
| Velvet powered40, primary4 | Three arms: sword arm, lantern arm and an extra fist at the shoulder | Hard rejection of this cell. Detail crop retained under captures/visual-v3; art owner asked to repair |
| Velvet powered40, exit0–5 | Both hands operate the lantern while the sabre disappears without a readable stow | Requested exit drawings that keep sabre and lantern in their own hands |
| Morel powered40, primary/exit | Mask disappears during throw and turns into a different round apparatus on removal | Art owner identified the same issue and is drawing primary/exit repairs |
| Runtime jump selection | Contact-compression drawing5 was selected before support contact, then skipped on actual landing | Runtime owner asked to keep airborne poses2–4 and select5–7 only after support; landing effect also needs the current support position |

## First visual observations

Bramble's replacement bow sequence keeps the bow visible through draw, release and recovery. The quiver and mantle remain attached. Its primary release appears at local frame8 in the supplied sixteen-pose sequence.

Clack's sixteen-pose primary has a plausible supported aim/load and restrained recoil/recovery. His harness and shoulder launcher remain recognisable rather than becoming a stationary turret. Rook's primary similarly stages its visible release at frame8 and returns to the carried carbine. Mote's glass gesture needs the chosen ordering checked for an idle-like pause near the middle, but its body remains distinct from a robot.

Cairn's new movement retains recessed amber eyes, moss and the same broad stone construction. The knee/arm changes provide a readable crouch, lift and landing. It must not inherit both the source sheet's vertical offset and the engine's arc. Stair drawings should remain supported rather than bounce like repeated jumps.

The new silhouettes mostly match the preceding base art at the source-model level. This does not yet certify registration, loop seams or full artistic polish at runtime.

## Repaired and later source checks

The selected `morel-primary16-v2.png` resolves the throwing-hand ownership issue: the visible arm retains the flask through preparation and is empty on release; the opposing fist no longer contradicts that motion. The first `morel-primary16.png` repair did not resolve it and should not be selected. A preparatory-pose reorder was suggested to make the raise/backswing continuous.

`velvet-primary16.png` supplies all sixteen independent bodies, retaining one sabre and one lantern. A preparatory-pose reorder was suggested to avoid an idle-like reset in the middle. The initial missing-body extension row is not approved as a fallback.

The fresh Iona, Tam, Brine, Pendle and Mirra extension masters were inspected after their owners rejected the first attempts. They now provide raised-foot stair cycles, a dodge returning to standing and much clearer single-action primary staging. Tam's preparatory palm order needs the owner's explicit reorder. Pendle's visible flash is at primary8, so the runtime release and muzzle treatment must agree. Brine keeps the gun, reel and helmet air connection; no swimming claim follows from that costume.

The single Nix primary3 replacement restores the same mechanical emitter and organic opposing arm. The raw Ashe repair's apparent red gradient was checked by the root against alpha: its background is transparent under the importer threshold. It is not a confirmed opaque-background defect. Its idle-like primary7 must be moved out of the windup before selection.

Ashe's powered master retains one worn helmet through idle, walk, primary and guard, and removes/stows it during exit. Clack's loader remains attached and unfolded through the held form, then folds back. Neither master introduces a second helmet or a stationary body turret. Cairn's powered master keeps root braces around the same slabs; his visible ground contact is primary5 and must define the release event accordingly.

The independent two-times-size Cairn jump contact board (`captures/visual-v3/cairn-jump-registration.png`) uses a single body scale and per-frame support-bottom registration. Anticipation remains short, extension and tuck remain articulated, landing remains compressed, and the sheet's whole-body arc is removed before the runtime supplies height. No pixels were repainted. The actual engine trajectory and contact timing still require rendered review.

## Selected packed-pose review

All fourteen selected packed sets were compared in `captures/visual-v3/packed-continuity-01.png` through `-03.png`: base idle, primary/secondary release, powered idle, powered primary, powered guard and the final exit drawing. These are inspection panels at the native logical pixel density, not gameplay screenshots. The panels crop a portion of wider cells for their fixed layout; truncated Ashe/Iona tips in a panel are not evidence that the original engine frame is clipped.

The selected replacements resolve the hard equipment defects found above. Nix's emitter is mechanical at the repaired load pose; Rook's selected powered guard has one worn helmet and an empty hip; Velvet's selected single-pose primary repair has two arms, one sabre and one lantern, and its selected exit retains the weapons. The bad top row of the combined Velvet primary/exit repair is excluded by the importer. Morel's selected powered release retains the fitted mask and its exit removes the same mask. Iona's separate primary strips remove the merged neighbouring body/head and keep one spear shaft. Tam's ice remains around the existing limbs with readable palms, Pendle keeps the rifle in Longshot, and Mote keeps the same exposed core until exit. Source-level body-volume and acting cleanup remains appropriate before production art approval.

The final selected order, alpha registration and event metadata must remain coupled to those repairs. The review did not add duplicate drawings to reach a headline number. Velvet's exit may contain fewer selected drawings when an exact duplicate is rejected; use the manifest's actual count.

Pendle's new reload source visibly stages opening, loading and closing the same revolver. The enlarged cylinder art does not reliably depict exactly six individually countable cartridges. Runtime six-round ammunition and visible reload staging are separate claims; the latter does not prove a mechanically exact cylinder illustration.

## Contact and support findings

Independent Bramble/Cairn release measurements are retained in `art-source/animated/v3/ranger-anchors.json`. They use the actual packed foot pivot and visible bow exit, billhook tip, stone fist contact and throwing hand. Cairn's powered contact has a shorter visible forward reach than the base slam, so the target review must use the correct spacing rather than enlarge an invisible hit range.

Rook's eight secondary drawings were inspected separately. Their contract is ready0, compression1, rising load2, airborne extension3, tucked apex4, descent5, physical contact compression6 and supported stand7. The selected source lift must be normalized before adding a simulated vault arc. Only the near backpack nozzle is clearly visible in the east-facing launch drawing. `rook-thrusters.json` supplies that one visible nozzle at offset(-26,-59); the far unit is occluded. The orange/black hip sphere is a helmet and must never emit thrust.

The runtime owner applied the independent findings about jump contact pose5, current support-height landing effects, and footstep suppression when motion is blocked. Those source changes still require the final rebuilt rendered/playback verification reported in VALIDATION.md.

At this point no new hard equipment blocker was found in the selected packed comparison poses. Static inspection alone does not certify playback quality.

## Actual native render review

The final native Godot showcase was sampled at 2, 5, 8, 12, 25, 40, 55 and 61 seconds (`captures/native-v3/frame-01.png` through `frame-08.png`). These are rendered scene frames from the 61.5-second recording, with the selected 2,135 drawings. Additional Rook Q launch frames were extracted at 54.3–54.5 seconds from `roster-v3-final.avi` for nozzle/gear inspection.

In these scene samples, Cairn's moss and recessed eyes remain below the HUD on the stair route. Supported feet, shadow position and the course's elevated surfaces agree; the stair poses do not read as a floating body translated up a flat floor. The large model remains readable without camera movement. Rook's selected descent/contact/stand sequence has visible separation from its ground shadow and a supported landing. The sampled human/robot equipment states retain their established body construction and repaired arm/helmet ownership. No new character-canvas clipping or forehead/HUD overlap was observed in these samples. This is a scoped sampling result, not approval of every possible world placement.

Two final rendered presentation corrections were reported to the root:

- The character/state/pose/hit status row at about y=150 uses pale text directly over the pale top-wall strip. Its contrast is insufficient in every supplied scene sample. Give it a solid dark backplate or place it on the dark header.
- Rook's short launch pulse originates at the correct visible backpack nozzle, but its straight-down direction runs into the carried helmet below. Angle the same brief jet down/back-left to clear that equipment; preserve its measured origin and the far-nozzle occlusion. Do not turn the helmet into an emitter.

The rebuilt actual Web captures for Cairn, Rook and Bramble (`captures/roster-browser/`) were then inspected at 1920×1080. The dark status backplate resolves the contrast issue. Its compact lower edge leaves the earlier stair-route moss clearance intact; no button/status overlap or forehead clipping was observed. Nearest presentation keeps the faces, amber eye slits, equipment and deliberate pixel clusters readable at the intended size. This resolves the UI correction in those rebuilt captures.

The matching final native recheck then passed using `captures/native-v3-final/stairs.png` and `rook-jet-1.png` through `rook-jet-3.png`. The stair status row is readable, with Cairn's moss and eyes clear below it. The first two Rook samples remain in preparation without premature exhaust. The takeoff sample shows a brief pulse angled down/back-left from the measured backpack nozzle, clearing the carried hip helmet. The far nozzle remains occluded. An enlarged inspection crop is retained at `captures/visual-v3/rook-final-jet-detail.png`.

Both reported presentation corrections are resolved in these rebuilt native/Web captures. No further presentation change is requested by this audit. The supplied stills alone do not establish normal-speed smoothness, performance on the user's device, complete powered traversal, or production-world integration. Final browser playback and native regression results belong in VALIDATION.md.

## Scope limits

The supplied masters are east-facing three-quarter studies. This review does not approve north/south/west acting, complete directional world traversal, moving platforms, ladders, swimming, powered traversal or production map integration. Powered idle/walk/primary/guard/exit can establish held equipment continuity only for those supplied states. A pose count is not an Eastward-quality certification.
