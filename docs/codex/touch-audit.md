# Y9 first step: viewport and target geometry audit

slot=rivet. This is a read-only audit of existing Godot UI geometry, not a touch
controller, camera change, rendering fix or physical-device result.

The existing `main/pixel_screen.gd` scales the entire 960 × 540 art viewport.
`ui/pause_menu.gd` makes four buttons at `UiStyle.TOUCH = 22` art texels high.
`game/test/test_camera_frame.gd` already checks zone-load camera placement and
black-frame rejection. None of those production files is changed here.

## Reproduce

After importing the project, run Godot 4.7.2:

```sh
$GODOT --headless --audio-driver Dummy --path game -s res://tools/touch_audit.gd
```

The tool instantiates the real pause menu, waits for container layout, measures
its four actual button rectangles and applies the real `choose_scale` function.
It emits one JSON document containing the declared input samples, scale, target
dimensions, clipping and findings. No save or setting is written. Runtime loading
of the screen script is intentional: `-s` scripts parse before autoload names exist.

Window dimensions are **physical pixels** and `dpr` means physical pixels per
logical point. Safe insets, when supplied to the API, are logical left/top/right/
bottom points. These are explicit assumptions, not measured phone properties.
The built-in matrix uses zero safe insets and synthetic window sizes. A production
caller must obtain the real window, ratio, safe area and input coordinate mapping.

| Physical window | Ratio | Mode         | Actual button height, logical points | Art viewport clipped |
| --------------- | ----: | ------------ | -----------------------------------: | -------------------- |
| 1920 × 1080     |     1 | fill / whole |                               44.000 | no                   |
| 960 × 540       |     1 | fill / whole |                               22.000 | no                   |
| 874 × 402       |     1 | fill         |                               16.378 | no                   |
| 874 × 402       |     1 | whole        |                               22.000 | yes                  |
| 2622 × 1206     |     3 | fill         |                               16.378 | no                   |
| 2622 × 1206     |     3 | whole        |                               14.667 | no                   |
| 667 × 375       |     1 | fill         |                               15.278 | no                   |
| 667 × 375       |     1 | whole        |                               22.000 | yes                  |

All four buttons have the same height. The two equivalent fill-mode samples
(874 × 402 at ratio 1 and 2622 × 1206 at ratio 3) show why meeting 44 **physical
pixels** does not establish a 44-point target. Whole mode clamps scale to at least
1, so a window smaller than the art viewport can crop the world even when the
centrally placed pause buttons remain inside it. This does not establish a camera
tracking defect or a rendered black frame.

## API and evidence interpretation

`measure_controls(node)` returns current Button IDs/Rect2 bounds in the node's
viewport coordinate space. The caller must measure in the art viewport; the CLI
sets its measurement viewport to the actual art dimensions. This is a button
inventory only, not coverage of every interactive Godot class or input action.

`audit(window_pixels, dpr, mode, targets, insets)` checks explicit ART-space
rectangles. `touch.minimum` means either dimension is under 44 logical points;
`touch.clipped` means the target is not fully inside the declared safe area.
Both full and visible dimensions are reported. The world-clipped flag is separate.
The checker does not enlarge targets or assume overlapping padding is usable.

`ok` means the audit input is valid. `passes` requires a nonempty target inventory
and zero target findings. A valid report with findings is not an input failure.
The CLI exits zero when all requested samples were measured completely, even if
the current UI has findings; it is report-only. Missing targets or invalid samples
make `complete` false and exit nonzero. Consumers must read those explicit fields,
and still reject engine script errors even when Godot exits zero.

Malformed sizes/ratios/modes/insets/IDs/rectangles and projection overflow are
rejected. The tests include 44-point passing controls, smaller controls, one fully
offscreen control, safe-area clipping independent of minimum size, ratio equivalence,
empty inventories, invalid/overflow inputs, detached output and actual menu layout.
They verify the detector, not that today's phone UI meets the standard.

## Receiving action

Claude A should decide how phone controls and menus retain at least 44 logical
points while the world viewport scales, then grant a narrow renderer/input/UI
follow-up. Simply increasing the art-space row height for every window would
also enlarge desktop rows and does not settle safe-area or input transforms.
Keep Tempo's Y7 menu model separate from that presentation decision.

The audit is the measurement/target-check step of Y9. Touch bindings, simultaneous
touches, capture/cancellation, camera interaction with safe areas, final layout,
rendered accessibility and physical iOS/Android evidence remain unimplemented or
untested. Existing C34 device and C54 approval blockers are unaffected. No new
game rules, art, Player, camera or production menu behavior are introduced.
