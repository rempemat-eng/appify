class_name RaidRepair
extends Node2D
## A brief repair after a lost raid (docs/vision/vertical-slice.md beat 8: boards on a window, a cart on
## its side), shown until the next walk into town (core/raids.gd clears `repairs`). Nothing is destroyed
## and nothing costs anything: it is only a sight. The node stands at the thing's foot, so it sorts with
## the building or the actors in front of it; `spec.at` is where it is drawn.
##
## No picture yet: drawn in the blockout's placeholder style (flat rectangles in its wood colours), an art
## follow-up. Still; it never moves.

const DENSITY := 3.0
const PLANK := Color("#806850")
const DARK := Color("#5a4632")
const WHEEL := Color("#3c3a34")
const SHADOW := Color(0.0, 0.0, 0.0, 0.25)

var spec: Dictionary = {}

func _ready() -> void:
	add_to_group("raid_repair")

func _draw() -> void:
	var at: Array = spec.get("at", [0, 0])
	var size: Array = spec.get("size", [12, 12])
	var foot := float(spec.get("foot", at[1]))
	var centre := Vector2(0.0, (float(at[1]) - foot) * DENSITY)
	var s := Vector2(float(size[0]), float(size[1])) * DENSITY
	var r := Rect2(centre - s / 2.0, s)
	match String(spec.get("kind", "")):
		"boards":
			# three planks nailed across a window
			for i in 3:
				var y := r.position.y + 3.0 + (s.y - 12.0) * float(i) / 2.0
				draw_rect(Rect2(Vector2(r.position.x - 3, y), Vector2(s.x + 6, 6)), PLANK if i != 1 else DARK)
		"cart":
			# a handcart on its side: its bed standing on edge, one wheel up
			draw_rect(Rect2(r.position + Vector2(4, s.y - 4), Vector2(s.x, 8)), SHADOW)
			draw_rect(r, PLANK)
			draw_rect(Rect2(r.position, Vector2(s.x, 5)), DARK)
			draw_circle(r.position + Vector2(s.x * 0.3, -6), 9.0, WHEEL)
			draw_circle(r.position + Vector2(s.x * 0.3, -6), 4.0, DARK)
		_:
			draw_rect(r, PLANK)
