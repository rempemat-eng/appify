# Pause touch layout (Y9-ui/r1)

This extends the existing four-button MyGame pause menu. It does not change the
world's 960 × 540 art viewport, `PixelScreen.choose_scale`, actions, focus order,
settings or game rules. Claim: [6477481283](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6477481283).

`PixelScreen.fit` sends its actual art scale and centred offset to the pause menu.
The menu's minimum row height is `ceil(44 * display_ratio / art_scale)` art texels,
with the existing 22-texel minimum retained. The panel centres inside the supplied
safe rectangle. The dimmer covers the physical window, including letterbox regions.
The existing `SubViewportContainer` remains responsible for projecting input.

All projection arguments use physical window pixels; `display_ratio` is physical
pixels per logical display point. Runtime obtains it from
[`DisplayServer.screen_get_scale`](https://docs.godotengine.org/en/stable/classes/class_displayserver.html#class-displayserver-method-screen-get-scale),
falling back to one for an invalid value. Mobile runtime intersects the window with
[`get_display_safe_area`](https://docs.godotengine.org/en/stable/classes/class_displayserver.html#class-displayserver-method-get-display-safe-area).
The desktop safe rectangle is the complete window. Platform reporting accuracy and
input on physical devices still need device evidence; a fallback ratio of one is
not a measured phone density.

The new focused suite instantiates the actual controls, then reuses the existing
`touch_audit.gd` projection oracle. Declared test inputs are 1920×1080@1,
960×540@1, 874×402@1, 2622×1206@3 and 667×375@1, each in fill and whole modes.
It also checks explicit asymmetric safe insets, non-overlapping controls, unchanged
action connections and cyclic focus neighbours, and invalid projection refusal.
These are synthetic engine geometry/input contracts, not rendered phone acceptance.
Whole mode may still crop the world in small windows; that existing policy remains.
The standalone audit CLI deliberately retains its original default-row baseline.

Arbitrarily small safe areas cannot fit this four-button menu. The tested matrix
does not establish a new minimum supported screen size or approval for every ratio,
orientation, accessibility setting or native platform. No physical-device,
multiplayer or final visual acceptance is claimed here.
