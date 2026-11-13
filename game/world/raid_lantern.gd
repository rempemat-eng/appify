class_name RaidLantern
extends Node2D
## The shard lantern's health during a raid (game-design.md 7.6: "the lantern has its own health bar").
## A node at the lantern's foot that only counts and draws: the lantern's picture and its solid are the
## zone's own. Creatures that reach the lane's end batter it (enemies/raid_creature.gd); at no health it
## `fell`, and the night is lost (world/raid_night.gd). The bar is a placeholder in the HUD's colours,
## drawn over the lantern's top; it never moves or blinks.

signal fell

const BAR := Vector2(60, 6)
const ABOVE := 166.0                  ## texels above the post's foot (936, 936): just over the lit cap, as seen in play
const FILL := Color("#f5d49c")
const LOW := Color("#d98a7a")
const BACK := Color("#1E1917")

var max_hp := 12
var hp := 12

func _ready() -> void:
	add_to_group("raid_lantern")
	hp = max_hp
	z_index = 1                        # over the lantern's own picture

func standing() -> bool:
	return hp > 0

func batter(amount: int, _dir: Vector2 = Vector2.ZERO) -> bool:
	if hp <= 0 or amount <= 0:
		return false
	hp = maxi(hp - amount, 0)
	queue_redraw()
	if hp == 0:
		fell.emit()
		return true
	return false

func _draw() -> void:
	var at := Vector2(-BAR.x / 2.0, -ABOVE)
	draw_rect(Rect2(at - Vector2(1, 1), BAR + Vector2(2, 2)), BACK)
	var share := float(hp) / float(maxi(max_hp, 1))
	draw_rect(Rect2(at, Vector2(roundf(BAR.x * share), BAR.y)), FILL if share > 0.34 else LOW)
