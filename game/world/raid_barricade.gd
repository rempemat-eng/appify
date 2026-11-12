class_name RaidBarricade
extends StaticBody2D
## A defence piece on a raid pad (game-design.md 7.6): Hale's hurdle barricade, the forge's kind. It
## stands across the lane, a low solid (layer 17, docs/physics.md): feet stop at it and arrows fly over,
## so the player shoots across it. Marching creatures stop short of it and batter it (world/raid_night.gd
## blocker_ahead, enemies/raid_creature.gd); at no health it breaks, its body goes, and the lane is open.
##
## No picture yet: it is drawn in the blockout's placeholder style (flat rectangles in the blockout's wood
## colours, game/tools/gen_blockout.py), an art follow-up. A hit tints it for HIT_TINT seconds (a colour,
## not a movement, so reduced motion keeps it); nothing about it loops.

signal broke

const DENSITY := 3.0
const HIT_TINT := 0.12
const WOOD := Color("#806850")         ## the blockout's building wood
const POST := Color("#5a4632")
const LIT := Color("#a88a64")
const SHADOW := Color(0.0, 0.0, 0.0, 0.25)
const PIP := Color("#f5d49c")
const PIP_EMPTY := Color("#3a3030")

var pad_id := ""
var kind: Dictionary = {}
var lane_s := 0.0                       ## how far along the lane it stands (texels)
var across := Vector2.RIGHT             ## the lane's direction where it stands
var hp := 10
var max_hp := 10
var _hit := 0.0
var _shape: CollisionShape2D

func _ready() -> void:
	add_to_group("raid_defence")
	max_hp = int(kind.get("hp", 10))
	hp = max_hp
	collision_layer = 17                # walls + low: stops feet, not shots
	collision_mask = 0
	_shape = CollisionShape2D.new()
	_shape.name = "Shape"
	var rect := RectangleShape2D.new()
	rect.size = _size()
	_shape.shape = rect
	add_child(_shape)

## The footprint in texels: `depth` along the lane, `span` across it, turned to the nearer axis (the
## placeholder is drawn on the pixel grid, never rotated).
func _size() -> Vector2:
	var depth := float(kind.get("depth", 6)) * DENSITY
	var span := float(kind.get("span", 22)) * DENSITY
	return Vector2(depth, span) if absf(across.x) >= absf(across.y) else Vector2(span, depth)

func standing() -> bool:
	return hp > 0

## A creature's blow. Returns true when this one broke it.
func batter(amount: int, _dir: Vector2 = Vector2.ZERO) -> bool:
	if hp <= 0 or amount <= 0:
		return false
	hp = maxi(hp - amount, 0)
	_hit = HIT_TINT
	queue_redraw()
	if hp > 0:
		return false
	_shape.set_deferred("disabled", true)
	collision_layer = 0
	broke.emit()
	return true

func _process(delta: float) -> void:
	if _hit > 0.0:
		_hit = maxf(_hit - delta, 0.0)
		if _hit == 0.0:
			queue_redraw()

func _draw() -> void:
	var s := _size()
	var r := Rect2(-s / 2.0, s)
	if hp <= 0:
		# broken: two rails lying on the road
		draw_rect(Rect2(r.position + Vector2(0, s.y * 0.3), Vector2(s.x, 6)), POST)
		draw_rect(Rect2(r.position + Vector2(s.x * 0.2, s.y * 0.7), Vector2(s.x * 0.8, 6)), WOOD)
		return
	var wood := LIT if _hit > 0.0 else WOOD
	draw_rect(Rect2(r.position + Vector2(3, 3), s), SHADOW)
	var vertical := s.y >= s.x
	var rise := 24.0                    # the rails stand this high above the ground (texels)
	if vertical:
		# across an east-west road: three hurdle panels down the span, each two posts and two rails
		var panels := 3
		var step := s.y / panels
		for i in panels:
			var y := r.position.y + step * (i + 1) - 4.0
			for x: float in [-10.0, 6.0]:
				draw_rect(Rect2(Vector2(x, y - rise), Vector2(4, rise + 4)), POST)
			for k in 2:
				draw_rect(Rect2(Vector2(-12, y - rise + 4 + k * 9), Vector2(24, 5)), wood)
	else:
		for i in 3:
			var x := r.position.x + (s.x - 6.0) * float(i) / 2.0
			draw_rect(Rect2(Vector2(x, -rise), Vector2(6, rise + 6)), POST)
		for k in 2:
			draw_rect(Rect2(Vector2(r.position.x, -rise + 4 + k * 9), Vector2(s.x, 5)), wood)
	# its health as pips over it, once it has been hit
	if hp < max_hp:
		var w := 5.0
		var x0 := -(w + 1.0) * max_hp / 2.0
		var top := minf(r.position.y, -rise) - 14.0
		for i in max_hp:
			draw_rect(Rect2(Vector2(x0 + i * (w + 1.0), top), Vector2(w, 4)), PIP if i < hp else PIP_EMPTY)
