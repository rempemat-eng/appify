# Cast contract v2: animator review (Bramble and Velvet pilot)

Claude J (lane J), 26 Oct. **Status: review, read-only.** Lane J's assignment (board note `to-all-next-1026`) is to retime and review the cast against contract v2 as it lands. This reviews the pilot in draft #280 (`claude-a/cast-v2` at 13074172, castwork e6672fa8) against the contract 1 manifests on main. It changes no game rule, manifest, runtime file or castwork.

- Data: [`cast-v2-review/bramble.json`](cast-v2-review/bramble.json) and [`velvet.json`](cast-v2-review/velvet.json), from `scripts/characters/review_cast_v2.py`. The script reads any manifest, including the four-facing ones expected on `claude-a/cast-v2-aim`, so it reruns as each character lands.

```
python3 scripts/characters/review_cast_v2.py game/assets/characters/<id>/manifest.json \
  --v1 <contract 1 manifest> --out docs/characters/cast-v2-review/<id>.json
```

## What holds

- **Canonical times are unchanged.** Across all 26 clips per character, each total duration and release time is within 0.3 ms of contract 1. Every release drawing starts on its release time (offset 0.0 ms).
- **Every drawing reaches the screen at 60 Hz** when the clip starts on a tick, except the two drawings in finding 2.
- **Fidgets are seamless.** All six fidgets start and end on idle drawing 0, in all 8 facings.
- **East and west walks are planted.** The stance foot travels back at 79 px/s against the body's 78.1, so the feet don't slide.
- **The cadence rise is right.** The walk cycle shortens from 0.56 s to 0.486 s with the stride unchanged, so +15 % speed comes from steps, not stretched legs.

## Findings

1. **Feet slide in every facing with a north or south component (skating, pre-existing, larger in v2).** `player.gd` moves the body at `walk_speed` on screen in every direction (`velocity = move * walk_speed`). In the drawings, the planted foot moves back only as far as the rig's foreshortened ground plane allows:

   | Facing         | Planted foot (px/s) | Body (px/s) | Slide (px/s) | Over one stance |
   | -------------- | ------------------: | ----------: | -----------: | --------------: |
   | E, W           |                  79 |        78.1 |            0 |            0 px |
   | SE, SW, NE, NW |                  52 |        78.1 |           26 |      about 6 px |
   | S, N           |                  27 |        78.1 |           51 |     about 12 px |

   Contract 1 has the same fault in S and N (23 against 68 px/s); the v2 pilot adds the four diagonals. The ground tiles are drawn square on screen, so the world does not foreshorten depth. The rig foreshortens it to about 0.35, so a step toward or away from the camera covers a third of the distance the body travels.

   Options, for Claude A and Matt:
   - **(a), recommended:** castwork projects the walk's ground travel 1:1 in screen y, as the world does. The stance foot then travels the body's distance in every facing. Legs, bob and body foreshortening stay as drawn; only the foot path along the depth axis lengthens.
   - **(b):** move slower on screen along the depth axis. That changes how the player moves, which is a rule in `player.gd` (C60's grant), so it is not proposed here.
   - **(c):** accept the slide as a convention of the view. The script then keeps E and W as the only checked facings.

2. **Velvet's primary contact drawing lasts less than one tick.** Drawings 7 (the release drawing) and 8 last 12.3 ms each. On a steady 60 Hz clock each is shown for one tick, but one late frame skips the contact drawing entirely, and C60's runner releases on it. Recommendation: give drawing 7 at least 2 ticks (33 ms), taken from the smear in-betweens before it (drawings 4 to 6). The release time and total stay where they are. Bramble's shortest drawing is 23 ms, and his contact drawings hold 2 ticks.

3. **Polish: the walk cadence alternates 2 and 3 ticks.** A 40.5 ms drawing is 2.43 ticks, so the 12 walk drawings show for 2, 2, 3, 2, 3, … ticks. The steps pulse slightly while the body glides. Contract 1 alternated 3 and 4. No change is needed for the pilot. With 12 drawings and the stride kept, an even step needs a 0.4 s cycle (+40 % speed) or a 0.6 s cycle (−7 %), so this stays as it is unless Matt picks a speed for other reasons.

## Not covered

No visual comparison or play-test: this is timing and anchor data only. The pilot's art and 3D review is in #280 itself. The skate numbers come from the manifest's foot anchors, which the importer writes from the rig, not from measuring pixels.
