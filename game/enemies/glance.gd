class_name Glance
extends RefCounted
## The mark for an arrow that does no harm: a creature that cannot come for the archer (it is walking
## home, or the archer stands outside the ground it keeps to) cannot be hurt from there, so nobody can
## stand out of reach and shoot it down. The arrow glances off: a small pale chevron over the creature
## for TIME seconds. One still drawing, finite, no blinking and no movement, so it is the same under
## reduced motion. No sound (the build has none).

const TIME := 0.22
const INK := Color("#2a1c1a")
const PALE := Color("#e4e0da")

## Draws the mark on `ci` centred on `at` (texels, local); `left` is the seconds it still shows.
static func draw(ci: CanvasItem, at: Vector2, left: float) -> void:
	if left <= 0.0:
		return
	var p := (at / 3.0).round() * 3.0
	for pass_ in 2:
		var c := INK if pass_ == 0 else PALE
		var w := 5.0 if pass_ == 0 else 3.0
		ci.draw_line(p + Vector2(-9, 3), p + Vector2(0, -6), c, w)
		ci.draw_line(p + Vector2(0, -6), p + Vector2(9, 3), c, w)
