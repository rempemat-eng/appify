class_name RaidBarricade
extends StaticBody2D
## A defence piece on a raid pad (game-design.md 7.6): Hale's hurdle barricade, the forge's kind. It
## stands across the lane, a low solid (layer 17, docs/physics.md): feet stop at it and arrows fly over,
## so the player shoots across it. Marching creatures stop short of it and batter it (world/raid_night.gd
## blocker_ahead, enemies/raid_creature.gd); at no health it breaks, its body goes, and the lane is open.
##
## Across an east-west road it is drawn from its pictures (scripts/art/kit/hurdles.py; Matt, 13 Nov: "what
## are those brown things on the track?"): a zigzag of woven wattle hurdles from wall to wall, standing,
## then battered (from half its health down: leaning, the weave burst), then broken (stumps and rods flat on
## the road, under everyone). Its contact shadow is laid by the one sun from the picture's sheet. Any other
## way round (no pad asks for it yet) keeps the blockout's placeholder. A hit tints it for HIT_TINT seconds
## (a colour, not a movement, so reduced motion keeps it); nothing about it loops.

signal broke

const DENSITY := 3.0
const HIT_TINT := 0.12
const WOOD := Color("#a88a64")         ## the blockout's building wood, one step lit
const INK := Color("#1E1917")
const POST := Color("#5a4632")
const LIT := Color("#d8c0a0")
const SHADE := Color(0.06, 0.08, 0.04, 0.24)   ## the creatures' contact shadow (enemies/creature_look.gd)
const PIP := Color("#f5d49c")
const PIP_EMPTY := Color("#3a3030")
const ART := "res://kit/props/art/raid/"
const HIT_LIT := Color(1.28, 1.22, 1.12)   ## the struck picture, a step towards the light
static var _sheet: Dictionary = {}         ## hurdle.json, read once
const STUMP := 8.0                       ## texels: a broken panel's post stumps stand this high
const LYING := 4.0                       ## texels: a fallen rail's highest end off the road (its contact shadow)

var pad_id := ""
var kind: Dictionary = {}
var span := 0.0                          ## world px across the lane, from the pad (0: the kind's own `span`)
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
	var wide := (span if span > 0.0 else float(kind.get("span", 22))) * DENSITY
	return Vector2(depth, wide) if absf(across.x) >= absf(across.y) else Vector2(wide, depth)

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
	if pictured():
		# its wreckage lies flat on the road: over the ground and its shadows, under everyone (as the zone's debris)
		z_as_relative = false
		z_index = -8
	_shape.set_deferred("disabled", true)
	collision_layer = 0
	broke.emit()
	return true

func _process(delta: float) -> void:
	if _hit > 0.0:
		_hit = maxf(_hit - delta, 0.0)
		if _hit == 0.0:
			queue_redraw()

## A flat rectangle with a one-texel ink outline (UiStyle.INK, the house outline colour).
func _ink_rect(r: Rect2, colour: Color) -> void:
	draw_rect(r.grow(1.0), INK)
	draw_rect(r, colour)

## The ground contact shadow of an upright piece standing on `foot` (texels), `width` wide and `h` high: the
## one sun (data/sun.json via TerrainGround.sun(): a texel h up lands cast.x h east, cast.y h south).
func _cast(foot: Vector2, width: float, h: float) -> void:
	var c := TerrainGround.sun() * h
	draw_colored_polygon(PackedVector2Array([foot, foot + Vector2(width, 0), foot + Vector2(width, 0) + c, foot + c]), SHADE)

## The contact shadow of a piece lying on the road (`r`, texels, drawn by `_ink_rect`), raised `h` off it at
## its highest: its outlined box moved by the one sun, drawn under the piece so only a sliver shows east and
## south of it.
func _cast_lying(r: Rect2, h: float) -> void:
	var box := r.grow(1.0)
	draw_rect(Rect2(box.position + TerrainGround.sun() * h, box.size), SHADE)

## The panels' feet on the ground, down the span (texels): one panel per 16 world px.
func _panel_feet(r: Rect2) -> Array[float]:
	var out: Array[float] = []
	var panels := maxi(1, roundi(r.size.y / 48.0))
	var step := r.size.y / panels
	for i in panels:
		out.append(r.position.y + step * (i + 1))
	return out

## The picture's sheet: frame, foot and each state's ground line and rise (scripts/art/kit/hurdles.py).
static func sheet() -> Dictionary:
	if _sheet.is_empty():
		var parsed: Variant = JSON.parse_string(FileAccess.get_file_as_string(ART + "hurdle.json"))
		_sheet = parsed if parsed is Dictionary else {"span": -1}
	return _sheet

## Which picture shows: "standing", "battered" from half its health down, "broken" at none.
func look() -> String:
	return "broken" if hp <= 0 else ("battered" if hp * 2 <= max_hp else "standing")

## True when its pictures fit: across an east-west road, on a pad as wide as they were drawn for.
func pictured() -> bool:
	var s := _size()
	return s.y >= s.x and is_equal_approx(s.y, float(sheet().get("span", -1)) * DENSITY)

func _draw_pictured() -> void:
	var st: Dictionary = sheet().states[look()]
	var foot: Array = sheet().foot
	var ground: Array = st.ground
	var cast := TerrainGround.sun() * float(st.rise)
	for i in range(ground.size() - 1):
		var a := Vector2(float(ground[i][0]), float(ground[i][1]))
		var b := Vector2(float(ground[i + 1][0]), float(ground[i + 1][1]))
		draw_colored_polygon(PackedVector2Array([a, b, b + cast, a + cast]), SHADE)
	draw_texture(load(ART + String(st.png)), -Vector2(float(foot[0]), float(foot[1])), HIT_LIT if _hit > 0.0 else Color.WHITE)

func _draw() -> void:
	if pictured():
		_draw_pictured()
		return
	var s := _size()
	var r := Rect2(-s / 2.0, s)
	var vertical := s.y >= s.x
	var rise := 24.0                    # the rails stand this high above the ground (texels)
	if hp <= 0:
		# broken: per panel, the two post stumps still standing and the rails down on the road, split in two
		# with a gap and their ends knocked askew, in ink outline so the open road reads as open. Each piece
		# keeps a small contact shadow by the one sun, as the standing hurdle's do: the stumps cast from their
		# feet, the fallen rails a sliver (all shadows first, so none falls across a piece)
		if vertical:
			var feet := _panel_feet(r)
			for fy in feet:
				for x: float in [-11.0, 5.0]:
					_cast(Vector2(x, fy), 6.0, STUMP)
				_cast_lying(Rect2(Vector2(-16, fy - 3.0), Vector2(13, 4)), LYING)
				_cast_lying(Rect2(Vector2(0, fy - 6.0), Vector2(15, 4)), LYING)
				_cast_lying(Rect2(Vector2(-9, fy + 4.0), Vector2(20, 4)), LYING)
			for fy in feet:
				for x: float in [-11.0, 5.0]:
					_ink_rect(Rect2(Vector2(x, fy - STUMP), Vector2(6, STUMP)), POST)
				_ink_rect(Rect2(Vector2(-16, fy - 3.0), Vector2(13, 4)), WOOD)
				_ink_rect(Rect2(Vector2(0, fy - 6.0), Vector2(15, 4)), WOOD)
				_ink_rect(Rect2(Vector2(-9, fy + 4.0), Vector2(20, 4)), POST)
		else:
			var left := Rect2(Vector2(r.position.x, -4), Vector2(s.x * 0.45, 4))
			var right := Rect2(Vector2(r.position.x + s.x * 0.55, -1), Vector2(s.x * 0.45, 4))
			_cast_lying(left, LYING)
			_cast_lying(right, LYING)
			_ink_rect(left, WOOD)
			_ink_rect(right, WOOD)
		return
	var wood := LIT if _hit > 0.0 else WOOD
	if vertical:
		# across an east-west road: hurdle panels down the span, each two posts and two rails, outlined in
		# the house ink so the placeholder reads on the brown road; each post and rail casts a contact shadow
		for fy in _panel_feet(r):
			for x: float in [-11.0, 5.0]:
				_cast(Vector2(x, fy), 6.0, rise + 4.0)
			for k in 2:
				var h := rise - k * 9.0
				var c := TerrainGround.sun() * h
				draw_rect(Rect2(Vector2(-13, fy) + c, Vector2(26, 2)), SHADE)
			for k in 2:
				_ink_rect(Rect2(Vector2(-13, fy - rise + k * 9), Vector2(26, 5)), wood)
			for x: float in [-11.0, 5.0]:
				_ink_rect(Rect2(Vector2(x, fy - rise - 4.0), Vector2(6, rise + 4)), POST)
	else:
		for i in 3:
			var x := r.position.x + (s.x - 6.0) * float(i) / 2.0
			_cast(Vector2(x, 0), 6.0, rise + 6.0)
			_ink_rect(Rect2(Vector2(x, -rise), Vector2(6, rise + 6)), POST)
		for k in 2:
			_ink_rect(Rect2(Vector2(r.position.x, -rise + 4 + k * 9), Vector2(s.x, 5)), wood)
	# its health as pips over it, once it has been hit
	if hp < max_hp:
		var w := 5.0
		var x0 := -(w + 1.0) * max_hp / 2.0
		var top := minf(r.position.y, -rise) - 14.0
		for i in max_hp:
			draw_rect(Rect2(Vector2(x0 + i * (w + 1.0), top), Vector2(w, 4)), PIP if i < hp else PIP_EMPTY)
