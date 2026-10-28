# Kit scene intake

W6-kit-review-intake/r1 fixes the source-picture adapter used by `review:scene`.
The claim is [6477002375](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6477002375),
with the lead's bounded runner/workflow extension recorded in
[6477117727](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6477117727).
The branch starts at the actual, unapproved
[PR302 head 04228475](https://github.com/rempemat-eng/appify/tree/04228475cbd9fb76e0a0a9af52240d7e40a5d858).
It targets that editor proposal. This engineering change does not approve its art or permit
its ancestry to enter main.

## The failure and repair

The old adapter understood `Sprite2D` ground pictures and `Vector2` positions. The four
registered kit zones instead have a `TerrainGround` `Node2D`, with a `Vector2i` grid and a
baked texture. All four previously loaded at size `(0, 0)` and produced an empty RGBA
composite. The runner then failed while saving that empty image.

The adapter now reads the ground that the runtime displays:

- `grid_size`, including the script default when omitted, gives the extent in cells. The
  supported manifest uses 24 texels per cell.
- `baked` identifies the existing ground PNG. The adapter reads that image; it neither
  invokes a painter nor substitutes the live shader/Python preview.
- The existing `ground_baked.json` stamp must match `bake.input_hash`. The digest includes
  the same three producer files, plan fields and used library records as the producer.
- That stamp is insufficient by itself: the serialized scene's materials, tiers, surface
  variants, kit piece identities/positions/variants and authored spawn positions must also
  match the stamped plan. Editing a scene without exporting and baking cannot silently
  reuse an old stamp. The PNG extent must match `grid_size × 24`.
- Packed cell data is read as Godot 4 `TileMapLayer` format 0: a two-byte version followed
  by 12 bytes per cell. Unknown versions, alternative tiles, sources, extents and duplicate
  cells fail closed.

Scene instances retain their source resource tables and receive the outer scene's actual
overrides. The adapter applies `KitPiece.variant` through the runtime index, including the
selected PNG and foot offset, and preserves the piece's sort origin, inherited z, parent
transforms and visibility. It hides exactly the `Sprite` of an index entry marked `painted`
when baked ground is present, as `KitPiece.set_ground_baked` does. That prevents falls,
steps and painted bridge details from being drawn twice.

Integer axis-aligned scale, reflection, quarter-turn rotation, offsets and ordinary sprite
frames are represented. Arbitrary rotation, skew, explicit transform matrices, `top_level`,
custom materials/modulation on a sprite or any ancestor, sprite region rendering and unknown textures are unsupported
and produce an intake failure. A kit piece transform absent from its bake plan is stale,
even when the sprite transform alone can be represented: its baked shadows cannot be
assumed to match.

The baked producer writes opaque RGB. Other image modes fail closed rather than losing
their alpha. The ground must sort below every visible source sprite; a changed layer that
would put it above a sprite is unsupported by this ground-first adapter. Missing scene
instances and registry/parse errors also become explicit intake failures, including errors
in the runner's initial registry read before it can select a zone.

Kit sprites retain scene order when z and sort Y tie. Legacy sprites retain their existing
X tiebreak, preserving both legacy hashes below. A synthetic overlap regression checks the
kit contract separately. No dedicated Godot capture of a same-Y overlap was taken; the
existing real-capture comparison below does not establish that additional tie case.

`SceneIntakeError` marks these cases as incomplete coverage. The runner writes
`complete: false`, the diagnostic, no source picture and exit status 1. It does not turn a
missing or unsupported input into a blank passing picture. Existing detector thresholds,
rendering commands and art approval states are unchanged.

## Actual source checks

| Registered zone | Extent | Sprites hidden because already painted into ground |
| --- | --- | --- |
| `kitlab` | 960 × 552 | 0 |
| `kitlab_tiers` | 960 × 552 | 2 |
| `kitlab_widths` | 960 × 552 | 2 |
| `woodland_kit` | 960 × 1728 | 2 |

The focused suite loads all four actual registered scenes, compares the ground to the
existing baked PNG and checks nonempty composites. It compares the freshness digest with
the authoritative producer function. A real boulder variant exercises an instanced sprite
whose selected PNG and foot differ from its default. A negative control unhides a painted
piece and requires the resulting composite to differ.

Synthetic fixtures exercise missing/unbaked/stale ground, a changed producer source,
scene changes behind an unchanged plan stamp, grid extent, packed materials/tiers,
surface variants, spawn changes, piece inventory, unknown variants/index records,
parent transforms, foot offsets, painted visibility and the runner's incomplete report.
The legacy woodland and Crossroads composites retain their recorded pre-change byte hashes:

- Woodland: `df4bade2c300319709c35a1b491ed3922e61502761312e10b045d3c68ca07934`.
- Crossroads: `f90ca3ebcdd13319346922b5bd83fe03311c110437d69b604800332230a5bdbd`.

Run the dedicated suite with:

```sh
python3 -m unittest scripts.review.test_kit_scene_intake -v
```

The dedicated `Kit scene intake` workflow runs this suite without editing the shared
`test_review` module or package commands. Drafts wait for readiness. Its execution and
matching general CI must be reported separately from local checks.

## Comparison with real Godot captures

[Palette's PR344 evidence](https://github.com/rempemat-eng/appify/tree/bc9672a5a63dc15dede557b45e922c8412bb3a1c/docs/reviews/editor-takeover/captures)
contains actual Godot 4.7.2/Mesa captures of the unchanged PR302 subject, with engine exits,
source guards and PNG hashes in `provenance.json`. The adapter's static source composites
were compared against those exact files; these are existing captures, not newly claimed
engine runs. No Palette files, engine configuration or system Xvfb setup were changed.

Each 1920 × 1080 capture is sampled at every second pixel to recover the game's
960 × 540 native viewport. The matching source crop has the following world origin.
Whole-viewport numbers include HUD and dynamic characters, which the static source
picture intentionally excludes.

| Capture | Crop origin | Whole viewport matching pixels / 518,400 | Match | Static pixels compared | Static mismatches |
| --- | --- | --- | --- | --- | --- |
| `kitlab_tiers-start` | (0, 12) | 515,298 | 99.401620% | 432,210 | 0 |
| `woodland_kit-start` | (0, 452) | 515,909 | 99.519483% | 432,210 | 0 |
| `woodland_kit-undercroft` | (0, 779) | 513,060 | 98.969907% | 372,830 | 0 |

The static comparison excludes the top 36 and bottom 28 native rows for HUD, and rectangles
around authored player/NPC/enemy positions: 75 texels either side, 125 above and 40 below.
Those envelopes are declared from source positions rather than derived from mismatching
pixels. They are deliberately broader than individual sprites. Zero residual mismatches
apply only to the remaining counted pixels, not those excluded regions or every viewport.

The exact capture SHA-256 hashes are:

- Tiers: `123c5c38c65455ac3f7164736d5f04d7e21528fa0a47e40d47ffcff8359f51d1`.
- Woodland start: `973325b0ad5c8bb12ecd6471e9a837545381c15f9c5f3080687c4faa356a58ab`.
- Woodland undercroft: `20d68684fe986a1d319de06601a526067afb6ee11a278a07db8df74c31343e49`.

The fourth zone and second lab have source/fixture coverage, but no matching Palette
runtime capture. These comparisons do not establish dynamic actor frames, animation,
quest-state visibility, a live unbaked shader, arbitrary transforms, device rendering or
whole-editor acceptance. The source stamp is the producer's existing input-freshness
contract, not a new cryptographic checksum of the PNG contents. Ordinary art
reproduction remains a separate required check.

Palette's existing Y12 failure/incomplete result and its detector findings remain evidence.
This adapter enables the missing source-scene producer; it does not erase those results,
waive the Eastward comparison, approve any candidate piece or change the written art bar.
