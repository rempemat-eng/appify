class_name RaidLantern
extends Node2D
## The shard lantern's health during a raid (game-design.md 7.6: "the lantern has its own health bar").
## A node at the lantern's foot that only counts and draws: the lantern's picture and its solid are the
## zone's own. Creatures that reach the lane's end batter it (enemies/raid_creature.gd); at no health it
## `fell`, and the night is lost (world/raid_night.gd).
##
## Unhurt, it shows nothing (Matt, 13 Nov: "why does the lantern have a health bar?"). From the first
## blow its health stands over its roof as a row of lights, the HUD's own kind of meter (hearts for
## Bramble, lights for the lantern: ui/art/shard_*.png, one light for two blows). Each blow shows on the
## lantern itself: its glass (the pane under its arched head, `pane`) goes dark and comes back, twice, in
## FLICKER seconds; under reduced motion it is dark once for that long, with no flicker. When a wave comes
## its light pools once on the setts at its foot (`swell`): three hard-edged rings on the shard's own ramp
## that spread and go, drawn on the ground under everyone; under reduced motion the pool stands still for
## that long. Both are finite, and nothing here loops.

signal fell

const PIP := Vector2(7, 10)           ## a light's picture
const PIPS_ABOVE := 190.0             ## texels above the plinth's foot: just over the roof's finial
const GLASS := Rect2(-16, -122, 32, 60)   ## the housing's glass, from the foot (village.p_shard_lantern)
const FLICKER := 0.3
const SWELL := 0.9
const ARCH := 9.0                     ## how far the head's arch drops from its crown to the posts
const DARK := Color(0.106, 0.063, 0.2, 0.62)      ## the palette's void over the glass
## The pool of light at its foot, outermost first: a half-width in texels and its colour (dusk 2, 3, 4).
const POOL: Array = [[60.0, Color("#584187")], [42.0, Color("#7262a4")], [24.0, Color("#927bb2")]]
const POOL_FLAT := 0.46               ## the pool lies on the ground: this much of its width deep
const POOL_ALPHA := 0.4

var max_hp := 12
var hp := 12
var _struck := 0.0
var _swell := 0.0
var _pool: Node2D

func _ready() -> void:
	add_to_group("raid_lantern")
	hp = max_hp
	z_index = 1                        # over the lantern's own picture
	_pool = Node2D.new()               # the light on the setts: under the lantern and everyone in the square
	_pool.name = "Pool"
	_pool.z_as_relative = false
	_pool.z_index = -8
	_pool.draw.connect(_draw_pool)
	add_child(_pool)
	set_process(false)

func standing() -> bool:
	return hp > 0

func hurt() -> bool:
	return hp < max_hp

func batter(amount: int, _dir: Vector2 = Vector2.ZERO) -> bool:
	if hp <= 0 or amount <= 0:
		return false
	hp = maxi(hp - amount, 0)
	_struck = FLICKER
	set_process(true)
	queue_redraw()
	if hp == 0:
		fell.emit()
		return true
	return false

## A wave has come for it: its light pools once at its foot.
func swell() -> void:
	_swell = SWELL
	set_process(true)
	_pool.queue_redraw()

func _process(delta: float) -> void:
	_struck = maxf(_struck - delta, 0.0)
	_swell = maxf(_swell - delta, 0.0)
	queue_redraw()
	_pool.queue_redraw()
	if _struck == 0.0 and _swell == 0.0:
		set_process(false)

## How dark the glass is `left` seconds before a blow's flicker ends: dark, back, dark, back.
static func dim(left: float, still: bool) -> float:
	if left <= 0.0:
		return 0.0
	if still:
		return 1.0
	var t := 1.0 - left / FLICKER
	return 1.0 if t < 0.3 or (t >= 0.5 and t < 0.75) else 0.0

## Each light's picture, left to right: "full", "half" or "empty" (one light for two health).
static func lights(now: int, total: int) -> Array[String]:
	var out: Array[String] = []
	for i in ceili(total / 2.0):
		out.append("full" if now >= i * 2 + 2 else ("half" if now == i * 2 + 1 else "empty"))
	return out

## The glass under its arched head, in texels from the foot: the housing's pane as the painter cuts it
## (village.p_shard_lantern: the head drops ARCH texels from its crown to the posts), in whole texels.
static func pane() -> PackedVector2Array:
	var out := PackedVector2Array()
	var half := GLASS.size.x / 2.0
	var x := GLASS.position.x
	while x < GLASS.end.x:
		var mid := x + 0.5 - GLASS.get_center().x
		var top := GLASS.position.y + ceilf(ARCH * pow(absf(mid) / half, 2.2))
		for corner: Vector2 in [Vector2(x, top), Vector2(x + 1.0, top)]:
			if out.is_empty() or out[out.size() - 1] != corner:
				out.append(corner)
		x += 1.0
	out.append(GLASS.end)
	out.append(Vector2(GLASS.position.x, GLASS.end.y))
	return out

## How many of the pool's rings show `left` seconds before the swell ends: they come from the foot
## outwards and go the same way (the innermost first), in whole steps; all of them when `still`.
static func rings(left: float, still: bool) -> Array[int]:
	var out: Array[int] = []
	if left <= 0.0:
		return out
	var n := POOL.size()
	if still:
		for i in n:
			out.append(i)
		return out
	var t := 1.0 - left / SWELL                    # 0 to 1 through the swell
	var steps := 2 * n - 1
	var step := mini(int(t * steps), steps - 1)
	for i in n:
		var from_foot := n - 1 - i                 # 0 for the innermost ring
		if from_foot <= step and from_foot > step - n:
			out.append(i)
	return out

func _draw_pool() -> void:
	var still: bool = SaveGame.setting("reduced_motion", false)
	for i: int in rings(_swell, still):
		var half: float = POOL[i][0]
		var pts := PackedVector2Array()
		for k in 24:
			var a := TAU * k / 24.0
			pts.append(Vector2(roundf(cos(a) * half), roundf(sin(a) * half * POOL_FLAT)))
		_pool.draw_colored_polygon(pts, Color(POOL[i][1], POOL_ALPHA))

func _draw() -> void:
	var still: bool = SaveGame.setting("reduced_motion", false)
	var d := dim(_struck, still)
	if d > 0.0:
		draw_colored_polygon(pane(), Color(DARK, DARK.a * d))
	if not hurt():
		return
	var row := lights(hp, max_hp)
	var at := Vector2(-(PIP.x + 1.0) * row.size() / 2.0, -PIPS_ABOVE)
	for i in row.size():
		draw_texture(load("res://ui/art/shard_%s.png" % row[i]), at + Vector2(i * (PIP.x + 1.0), 0))
