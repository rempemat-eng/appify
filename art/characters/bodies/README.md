# Body plans

There is one file per character, `<id>.json`, and each is the data a rig template needs to build that character. A body plan says:

- which template the character uses
- its height and cell
- its parts: families, layer per facing, joint, and how each part moves
- its anchors
- its signature

The plans come from the chosen design sheets (`docs/vision/characters/designs/<id>.json`, the `final` block). The rig (`scripts/art/native/`, Claude A's first screen) reads them. Per rules-system.md section 6, each character is a body plan plus a face painter.

`lib/character-bodies.test.ts` (in `check:core`) checks every file against the animation spec and the house palette.

## Schema

```json
{
  "id": "bramble",
  "kind": "folk | familiar",
  "template": "biped | smallBiped | largeBiped | wideBiped | familiar | flyer",
  "heightWorld": 24,
  "cell": "folk",
  "design": "A, capelet ranger",
  "families": ["clay", "plaster", "sky", "timber", "brass"],
  "glows": [],
  "signature": "the one thing that must read at game scale",
  "parts": [
    {
      "name": "capelet front",
      "families": ["sky"],
      "joint": "chest",
      "layer": { "S": 6, "E": 6, "W": 6, "N": 2 },
      "facings": ["S", "E", "W", "N"],
      "motion": "lags one frame in the walk; flies on hit",
      "painter": false
    }
  ],
  "anchors": {
    "perch": { "E ready": [22, 40] },
    "growth": [16, 6],
    "hand": "left"
  },
  "notes": ["..."]
}
```

### Fields

- **`joint`** is one of `foot`, `hip`, `chest`, `head`, `hand`, `back`, `tail` or `float`. The rig poses each joint, and a part moves with its joint.
- **`layer`** gives the part's z order for each facing; higher numbers are drawn in front. N is inferred where a design sheet has no N view: back parts come to the front.
- **`painter: true`** marks a part that is hand-painted per character: faces, emblems, a dial, a visor glyph. Every other part is built from rig shapes and shaded by the kit.
- **Anchors** are in cell px at density 2.
