# Current animation sources

The current roster has 912 selected drawings from the flattened PNG masters and explicit replacement strips in `art-source/animated/`. The deterministic importer records each selected source frame, applies common body density and foot registration, then produces PNG cells, native SpriteFrames and atlas metadata. It does not create interpolated or duplicated poses to reach a quota.

Thirteen sets have 64drawings. Cairn has 80, including sixteen-frame walk, primary and secondary clips. Every set covers idle, walk, primary, secondary, special activation, guard, hit and defeat in an east-facing three-quarter view.

The common frame is 192×192, pivot (96,172). Ashe uses 256×192, pivot (132,172), so long sword and fallen poses fit without shrinking the figure. Human body density targets 96 logical pixels; Cairn 112. Full HD presentation is exact 2×.

Most primary/secondary releases occur at zero-based frame 4. Cairn's long attacks release at 8; Mote's core opens at special frame 2; Rook's vault begins at secondary frame 3 and contains its vertical motion already. The held Cairn guard uses frame 3. Exact durations and events are in each manifest.

These sources are not layered Pixelorama/Aseprite masters or complete directional/powered libraries. Some contour and volume cleanup remains. `animation-sheets/README.md` explains the delivered layout, and `VALIDATION.md` records tests and recovery.
