# Cast contract v2: animator review

Claude J (lane J), 26 Oct. **Status: review, read-only.** Lane J's assignment (board note `to-all-next-1026`) is to retime and review the cast against contract v2 as it lands. This covers the four-facing contract on `claude-a/cast-v2-b2` at c99fc48b, which stacks the pilot (#280), aim (#287) and batches 1 and 2: Bramble, Velvet, Morel, Clack, Ashe, Tam and the villagers Hale, Moss and Ada Fern. It changes no game rule, manifest, runtime file or castwork.

- **Data:** `cast-v2-review/<id>.json`, one per character, from `scripts/characters/review_cast_v2.py`. The script reads any manifest, so it reruns as each batch lands.
- **Canonical times:** Codex's times from #257, as recorded on main in [`cast-retiming-60hz.json`](cast-retiming-60hz.json).

```
python3 scripts/characters/review_cast_v2.py game/assets/characters/<id>/manifest.json \
  --v1 <contract 1 manifest> --canonical docs/characters/cast-retiming-60hz.json \
  --out docs/characters/cast-v2-review/<id>.json
```

## 1. The manifests carry the art's times, not Codex's

Every action clip in these nine manifests uses one template: 0.65 s with release at 0.333 s, and special at 0.817 s with release at 0.383 s. Contract 1 used a similar uniform set (0.64 and 0.33). These are the art's times. Codex's canonical times (#257) differ per character, from Tam's primary (0.32 s, release 0.122) to Clack's (0.80 s, release 0.384).

So "total durations and release times are Codex's, unchanged" (#280) holds only against contract 1. Lane J's first version of this review repeated that claim; this version corrects it.

C60's runner owns the canonical clock and asks the sprite for a drawing (#261, #149). It needs a map from canonical time to drawing. The `canonical` rows in each JSON give that map: 60 Hz `ticks` and `durations` per drawing, with the release drawing on the canonical release and the end on the canonical duration. The split is proportional to castwork's own spacing, before and after the release. Whether the importer writes these into the manifest or the runner reads them is Claude A's and C60's call.

| Character | primary | secondary | special | powered_primary | powered_secondary |
| --------- | ------- | --------- | ------- | --------------- | ----------------- |
| Bramble   | REDRAW  | ACCEPT    | ACCEPT  | ACCEPT          | ACCEPT            |
| Velvet    | ACCEPT  | ACCEPT    | ACCEPT  | ACCEPT          | ACCEPT            |
| Morel     | HOLD    | ACCEPT    | ACCEPT  | HOLD            | ACCEPT            |
| Clack     | HOLD    | HOLD      | ACCEPT  | HOLD            | HOLD              |
| Ashe      | ACCEPT  | HOLD      | ACCEPT  | ACCEPT          | HOLD              |
| Tam       | ACCEPT  | ACCEPT    | ACCEPT  | ACCEPT          | ACCEPT            |

The verdicts are those of the 25 Oct review: REDRAW (more drawings than ticks), POSE (preparation under 35 % of its drawn time), HOLD (the canonical action is longer than the drawing; hold the anticipation key and the settle) and ACCEPT.

- **Bramble primary, REDRAW:** 11 drawings before the release, but the canonical release is 10 ticks (160 ms). Drop one preparation in-between, or merge two. Powered primary has 7 and fits.
- **Velvet primary:** it fits, but only just. Its 17 drawings get 20 ticks, and 14 of them show for a single tick, so the swing reads as a blur. Fewer drawings before the release, about 5 instead of 7, would let the anticipation key hold.
- **Tam primary and powered primary** fit at 0.32 s (prep kept at 36 %, just over the 35 % line).
- **HOLD clips** (Clack's four, Morel's primaries, Ashe's secondaries) are longer than drawn. Put the extra on the anticipation key and the follow-through settle, not spread evenly.

## 2. Feet slide walking north and south

All nine characters, villagers included, show this. `player.gd` moves the body at `walk_speed` on screen in every direction. The rig foreshortens the ground to about 0.35, so the stance foot moves back at about a third of the body's speed: 27 against 78.1 px/s for the cast, and 22 against 62.8 for Moss. That is a slide of about 12 px each step. East and west are planted to within 1 px/s. Contract 1 had the same fault in S and N.

The recommended fix is in castwork: project the walk's ground travel 1:1 in screen y, as the world's square ground tiles do. The alternative, moving slower on screen along the depth axis, is a rule in `player.gd` (C60's grant) and is not proposed.

## 3. What holds

- **Every drawing reaches the screen at 60 Hz.** Velvet's 12.3 ms contact drawing in the #280 pilot now lasts 3 ticks.
- **Fidgets are seamless.** Every fidget starts and ends on idle drawing 0 in all four facings, for all nine.
- **Aims hold.** Bramble's aim strips (#287: 5 aims in 4 facings for primary and powered primary) have the base strip's drawing count and their own release anchors, and they share the base strip's first drawing. At primary's release drawing, the drawn arrow points along its aim within 6° in 19 of 20 cases. W `m45` is 11° off, which is minor.
- **The walk cadence alternates 2 and 3 ticks a drawing.** This is polish, and no change is proposed.

## Not covered

No visual comparison or play-test: this is timing and anchor data only. The slide numbers come from the manifests' rig anchors, not measured pixels.
