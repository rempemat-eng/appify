# Final animation validation

Final revision checked 24 October 2026: **2,135 distinct drawings**, fourteen characters, **239 clips**. Twelve sets have 152 drawings; Velvet has 151 because her exit uses seven valid poses rather than duplicate padding; Pendle has 160 including reload. Every set has112 base/combat/traversal drawings plus its supplied powered review drawings.

| Check | Final result | Evidence |
|---|---|---|
| Asset integrity | All 14 sets; 2,135 unique packed drawings, strict binary alpha, no canvas clipping, fit factor 1.0 throughout, correct atlas rectangles/timing/anchors | `validation/asset-integrity-v3.json` |
| Fresh source rebuild | Selected masters alone reproduce **2,192 runtime/atlas files byte for byte**, including all 2,135 body PNGs and 14 native resources | `validation/git-source-repro-v3.json`, `git-source-assets.json`, `git-source-rebuild.log` |
| Native Godot integration | **1,681 passed,0 failed, skipped[]**; every authored frame and 239 clips visited | `validation/roster-native-v3.log`, `roster-import-v3.log` |
| Actual Web clip playback | **274 passed**, all **239/239** clips; one uninterrupted run; no runtime errors | `validation/animation-browser-results-v3.json`, `animation-browser-v3.log` |
| Actual Web interactions | **171 passed** across all 14 characters; one uninterrupted run; no runtime errors | `validation/traversal-browser-results-v3.json`, `traversal-browser-v3.log` |
| Fixed camera | **7,452 unchanged browser camera samples**, plus native course/showcase checks | Both browser result files and native log |
| Native showcase | Actual physical course and all 14 jump/powered reviews complete after 61.467 simulation seconds; Rook physical vault included | `validation/native-capture-v3.log` |

The two completed browser runs served the exact same final PCK:

```text
5678a71d372b47ea46527696e4d4238d3d56045e705db67ee4d65c93e7ab130a
```

`validation/runtime-source-v3.json` records runtime/test/log hashes and manifest identity. The browser result files independently record the PCK they actually served. Earlier 801/112 results, partial character passes, interrupted runs and preliminary harness-route failures are not counted as current final evidence.

## What was exercised

Native and real keyboard browser checks cover every base primary/secondary/special activation, powered idle/walk/primary/guard/exit, one-shot completion, looping, pause/stepping/speed, character selection, actual canvas blur/refocus, reset and bounded effects. Pendle reload closes before restoring six-round capacity; powered rifle shots use the rifle without silently consuming revolver ammunition. Brine has an attached harpoon/reel state and 136 per-frame muzzle anchors, with empty-reel and reset controls. Nix's non-damaging Afterimage retains its activation origin. Iona's lunge moves before contact, stops at blockers and cancels its contact window on guard.

All fourteen characters perform physical jumps with separate support and airborne height. Stair ascent/descent are supported continuous elevation transitions; blocking side faces, a 32-pixel upper landing, the 16-pixel ledge, bridge support, materials, missed landings and checkpoint reset are checked. Rook's secondary now has a real height arc, about 60 pixels of planar travel, one supported landing, a positive ledge case and an over-wide-gap negative case. Airborne actions, held input after focus loss, old queued releases and duplicated landing events are rejected or cleared consistently.

The camera never follows, tilts, shakes or pulses. Collision/support uses the ground footprint; body/effect projection uses the same rounded foot position. Material contacts and projectiles remain local and bounded. The study does not add production damage, swimming, fall-damage, economy or save rules.

## Visual review and scope

`VISUAL_REVIEW_V3.md` records independent source, packed-pose and actual renderer review. Retakes repair merged/missing bodies, flask hand swaps, flesh replacing the laser emitter, duplicate lanterns/helmets, a third arm, attack restarts and inconsistent equipment exits. Registration prevents a painted jump arc from being added twice; actual support contact chooses the landing compression pose. Final presentation corrections put the status text on a compact dark strip and angle Rook's one visible nozzle jet away from the carried hip helmet. The far nozzle is correctly occluded in this view.

Image uniqueness and automated assertions do not establish artistic perfection. Final contour/body-volume and tiny equipment details still benefit from pixel-artist cleanup. Pendle's reload staging is supplied and runtime capacity is six, but enlarged microscopic cylinder markings are not certified as six individually countable cartridges.

These are east-facing three-quarter studies. Additional directions, powered secondaries/jump/stair/dodge variants, layered authoring masters and production-world integration are unfinished. Powered review therefore permits flat walking, primary and guard, with an explicit exit before base traversal or secondary use. Ladders, climbing, deep water, moving platforms, arbitrary ceilings/occlusion and production height-combat layers are requirements in `WORLD_ANIMATION_CONTEXT.md`, not features silently claimed as complete.

Testing used Linux software rendering, Chromium and native Godot in a headless environment. It does not establish Mac/native-device/controller performance, mobile runtime behaviour, sound output, main-game integration or Eastward-quality acceptance. Hosted repository CI has not validated this draft Godot handoff.
