class_name CampSettle
extends Node2D
## The beat when a camp's last creature is freed (15 Nov): a few motes of the fallen light lift off the
## ground where the camp stood and go out, while the HUD says the place is quiet (game.gd, data/leads.json
## "beats"). Finite: gone after LIFE seconds. Under reduced motion the motes stand still where they
## start and go out together at the end, with no rise and no fade. Looks only: no collisions, rewards
## or saves, and nothing waits on it.

const LIFE := 1.6
const RISE := 36.0       ## texels a mote lifts over its life
const TEXEL := 3.0       ## one world px: motes are drawn on the world's grid
const GOLD := Color("#F8DD8F")
const PALE := Color("#F3E9D2")
const INK := Color("#1E1917")
## Where the motes start, in texels from the camp's middle, and when each sets off (a share of LIFE).
## A fixed table: the beat looks the same every time and needs no random numbers.
const MOTES := [
	[Vector2(-96, 18), 0.00], [Vector2(-54, -30), 0.10], [Vector2(-18, 36), 0.04], [Vector2(12, -12), 0.16],
	[Vector2(48, 30), 0.08], [Vector2(84, -24), 0.20], [Vector2(-72, 54), 0.24], [Vector2(30, 66), 0.14],
	[Vector2(108, 42), 0.28], [Vector2(-30, -60), 0.30],
]

var _t := 0.0

func _ready() -> void:
	z_index = 1

## What shows `t` seconds in: [{at: Vector2 (texels from the middle), alpha: float, big: bool}].
## Empty once it is over. Reduced motion: every mote at its start, full, for the whole life.
static func parts(t: float, reduced: bool) -> Array:
	var out := []
	if t < 0.0 or t >= LIFE:
		return out
	for i in MOTES.size():
		var from: Vector2 = MOTES[i][0]
		if reduced:
			out.append({"at": from, "alpha": 1.0, "big": i % 3 == 0})
			continue
		var k := (t / LIFE - float(MOTES[i][1])) / (1.0 - float(MOTES[i][1]))
		if k < 0.0:
			continue
		var lift := RISE * (1.0 - (1.0 - k) * (1.0 - k))        # quick off the ground, settling at the top
		var at := from + Vector2(0, -lift)
		out.append({"at": (at / TEXEL).round() * TEXEL, "alpha": clampf((1.0 - k) * 2.0, 0.0, 1.0), "big": i % 3 == 0})
	return out

func _process(delta: float) -> void:
	_t += delta
	if _t >= LIFE:
		queue_free()
		return
	queue_redraw()

func _draw() -> void:
	for p: Dictionary in parts(_t, bool(SaveGame.setting("reduced_motion", false))):
		var side := TEXEL * (2.0 if p.big else 1.0)
		var at: Vector2 = p.at
		var a: float = p.alpha
		draw_rect(Rect2(at + Vector2(TEXEL, TEXEL), Vector2(side, side)), Color(INK, 0.35 * a))
		draw_rect(Rect2(at, Vector2(side, side)), Color(GOLD if p.big else PALE, a))
