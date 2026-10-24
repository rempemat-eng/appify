# Toolchain and reproducible handoff

This file records tools actually used for this animation revision. It distinguishes original source generation, deterministic export and actual runtime validation. No new service, credential or production backend is required to play the downloadable build.

| Tool | Version observed | Purpose and evidence |
|---|---|---|
| Built-in image generation | Model/version not exposed by the tool | New original raster animation masters and targeted equipment/anatomy retakes. Exact v3 prompts, grid selections, rejected cells and hashes are retained in `art-source/animated/v3/*provenance*.json` and `elements-art-review.json`. |
| Python | 3.12.14 | Import/build/review scripts and local launcher. |
| Pillow | 12.3.0 | Nearest-neighbour packing, strict binary alpha, PNG atlases, GIF contact studies and integrity checks. |
| NumPy | 2.3.5 | Pixel masks, bounds, alpha and frame comparisons. |
| SciPy | 1.17.0 | Connected-component extraction, with hard rejection of missing or merged bodies. |
| Godot | 4.5.1 stable | Character state, collisions, support/elevation, attacks, actual native tests and Web export. |
| Node.js | 24.22.1 | Browser harness runner. |
| Playwright | 1.62.1 | Real keyboard, pause, focus and camera checks against the exported Godot Web build. |
| Chromium | 153 headless Linux | Actual desktop WebGL playback through software rendering. Browser emulation is not physical-device evidence. |
| Xvfb / software OpenGL | Local Linux environment | Display for real native Godot movie capture in this headless environment. |
| FFmpeg | 6.1.1 | Encode the actual native capture for the downloadable preview. |
| GitHub connector | Session integration | Read current coordination/main/PRs; publish the isolated source handoff and exact test/tool notes. |
| ChatGPT Library connector | Session integration | Preserve the downloadable studio, sheets and preview with versioned identity. |
| Parallel agents | Session workflow | Three art owners, one runtime owner, independent logical/browser and visual auditors, with root integration. Findings led to real retakes and regressions; agent agreement is not artistic certification. |

## What reproduces exactly

Stored PNG masters are the source of truth. Re-running image generation is not a deterministic rebuild and is not required. The importer selects those stored pixels, thresholds their existing alpha, applies one calibrated source scale, registers their pivot and exports native resources and atlases. It never creates missing poses through duplicate padding or frame interpolation. The final JSON records selected source slots, source and packed bounds, pivots, timing and release/contact anchors. PNG outputs are replaced atomically so an interrupted save cannot publish half an atlas.

Jump/stair/dodge registration removes whole-body source translation before the engine supplies world height. Rook's vault uses the same physical support model, its own secondary drawings and one visible attached nozzle in this east-facing view; the far nozzle is occluded. Brine's gun has per-frame muzzle anchors so the tether stays attached while the body changes pose. More drawings preserve the ordinary attack release and recovery times rather than doubling control latency.

## Rebuild from a Git checkout

The repository stores selected raw masters, source, timing/anchor contracts and validation evidence. Engine binaries, caches, temporary/rejected studies, generated body PNGs, packaged downloads and exported Web binaries are excluded. The ready downloadable ZIP additionally contains generated resources and a playable Web build.

From this directory:

```bash
python3 -m pip install -r requirements-art.txt
python3 tools/build_animation_roster.py
python3 tests/animation_assets.py
python3 tools/animation_review.py
```

Import with Godot 4.5.1, then run the native suite and export Web using its matching official templates:

```bash
godot --headless --editor --path . --import
godot --headless --path . --script tests/roster_animation_test.gd
mkdir -p web
godot --headless --path . --export-release Web web/index.html
```

The `godot` executable name varies by installation. The contact-board renderer uses the DejaVu Sans path near the top of `animation_review.py`; on another OS, point it to an installed DejaVu Sans font. Review-label rendering is separate from the runtime sprite pixels. Web uses the non-threaded compatibility export; `export_presets.cfg` includes runtime JSON. The Python launcher serves existing `web/` files and does not export the project.

Run the browser harness with Playwright and a compatible Chromium installed:

```bash
node tests/animation_browser.cjs
node tests/traversal_browser.cjs
```

`CHROMIUM_PATH` and `PLAYWRIGHT_MODULE` can select installed executable/module paths. Those variables identify local tools, not credentials. The harness creates and closes its own local HTTP server. No live player session or saved account is used.

For a real native showcase, use Godot's movie mode on a display (or a configured Xvfb display):

```bash
godot --path . --rendering-method gl_compatibility --audio-driver Dummy --resolution 960x540 --write-movie showcase.avi --fixed-fps 30 -- --traversal-showcase --quit-on-showcase
```

The showcase runs the actual course/jump/vault/powered action code and exits when the sequence completes. The delivered MP4 is a nearest-neighbour 2× encoding of that logical viewport, not fabricated gameplay from a GIF sheet.

## Review and remaining limits

`VALIDATION.md` names final test results and exact evidence. `ABILITY_TRAVERSAL_AUDIT.md`, `VISUAL_REVIEW_V3.md` and `WORLD_ANIMATION_CONTEXT.md` record starting defects, actual repairs and remaining integration work. A source uniqueness check does not prove expressive motion or pixel-art quality. The working masters are flattened PNGs; layered authoring projects, all directions, powered secondary/traversal combinations, deep-water/climbing/moving-platform integration and production game balance remain outside this handoff.

Pendle's reload has readable open/eject/load/close body staging and a six-round runtime capacity. Enlarged microscopic cylinder markings still need artist cleanup; a targeted correction was rejected by the image service and did not overwrite the selected strip. No claim is made that six individual cartridges are visibly countable in every drawing.

The source lives only in `prototypes/mygame-animation-studio/` on its isolated handoff branch. It is not imported by the production app, does not replace the CI/map lane, and does not modify player saves, maps or economy. Claude A remains the integration owner.
