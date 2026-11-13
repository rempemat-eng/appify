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
## lantern itself: its glass goes dark and comes back, twice, in FLICKER seconds; under reduced motion it
## is dark once for that long, with no flicker. When a wave comes its light swells once (`swell`; a still
## halo under reduced motion). Both are finite, and nothing here loops.

signal fell

const PIP := Vector2(7, 10)           ## a light's picture
const PIPS_ABOVE := 190.0             ## texels above the plinth's foot: just over the roof's finial
const GLASS := Rect2(-16, -122, 32, 60)   ## the housing's glass, from the foot (village.p_shard_lantern)
const FLICKER := 0.3
const SWELL := 0.9
const DARK := Color(0.106, 0.063, 0.2, 0.62)      ## the palette's void over the glass
const GLOW := Color("#af93b4")                    ## the shard's light (dusk 5)

var max_hp := 12
var hp := 12
var _struck := 0.0
var _swell := 0.0

func _ready() -> void:
	add_to_group("raid_lantern")
	hp = max_hp
	z_index = 1                        # over the lantern's own picture
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

## A wave has come for it: its light swells once.
func swell() -> void:
	_swell = SWELL
	set_process(true)
	queue_redraw()

func _process(delta: float) -> void:
	_struck = maxf(_struck - delta, 0.0)
	_swell = maxf(_swell - delta, 0.0)
	queue_redraw()
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

func _draw() -> void:
	var still: bool = SaveGame.setting("reduced_motion", false)
	if _swell > 0.0:
		var k := 1.0 if still else sin(PI * (1.0 - _swell / SWELL))
		var mid := GLASS.get_center()
		draw_circle(mid, 34.0 + 10.0 * k, Color(GLOW, 0.16 * k))
		draw_circle(mid, 22.0 + 6.0 * k, Color(GLOW, 0.2 * k))
	var d := dim(_struck, still)
	if d > 0.0:
		draw_rect(GLASS, Color(DARK, DARK.a * d))
	if not hurt():
		return
	var row := lights(hp, max_hp)
	var at := Vector2(-(PIP.x + 1.0) * row.size() / 2.0, -PIPS_ABOVE)
	for i in row.size():
		draw_texture(load("res://ui/art/shard_%s.png" % row[i]), at + Vector2(i * (PIP.x + 1.0), 0))
