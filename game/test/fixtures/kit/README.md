# Terrain rendering parity (W7)

These are Python reference renders at one pixel per terrain texel, using
`scripts.art.kit.compose.render`. They cover the kit lab (including piece shadows and
edge dressing), a lawn/path/water corner, and a deliberately wrong edge-profile hash.
They are test fixtures, not baked ground or shipping art.

Regenerate from the repository root, then review the resulting pixel changes:

```sh
python3 game/test/fixtures/kit/generate.py
python3 game/test/fixtures/kit/generate.py --check
```

The generator requires the same Pillow, NumPy and SciPy dependencies as `check:kit`.
`references.json` records input and decoded-pixel hashes. The GdUnit suite checks these
hashes without a Python dependency, so changing the Python renderer, kit textures,
prop shadow metadata or source plans makes the references stale until regenerated.
The lab must contain visible shadow and dressing pixels.

`test_terrain.gd` launches a real OpenGL child process, even when the parent suite uses
Godot's dummy headless driver. On Linux without `DISPLAY`, it requires `xvfb-run`,
`xauth` and working OpenGL (Mesa software rendering is sufficient). A missing renderer,
empty image, missing comparison result or different image extent fails the check.
The deliberately shifted reference must produce a completed comparison with differing
pixels, not an unrelated process error. No tolerance, resizing or colour correction is used.

For a standalone capture after the normal Godot import:

```sh
xvfb-run -a "$GODOT" --display-driver x11 --rendering-method gl_compatibility \
  --rendering-driver opengl3 --audio-driver Dummy --path game \
  --script res://tools/kit_shot.gd -- \
  --scene=res://zones/kitlab/kitlab.tscn --out=/tmp/kitlab.png \
  --compare=res://test/fixtures/kit/kitlab.png
```

`--plan=res://test/fixtures/kit/three_materials.json` also works. Scene inputs use the
generated kit-zone layout: an identity-transform `Ground`, and direct `KitPiece`
children under `Props`. The tool draws live terrain and shadows/dressing only; baked
textures, prop sprites, actors, cameras and UI are excluded. It emits a
`KIT_SHOT_RESULT` JSON comparison and returns nonzero on any mismatch or capture error.
