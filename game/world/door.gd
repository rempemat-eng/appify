class_name Door
extends Area2D
## Walk into it to go to `target_zone` at `target_spawn`. Doors arm a moment after the zone loads, so
## arriving on top of one never bounces the player straight back. `only_if` (a quest condition as JSON,
## core/quests.gd) keeps the door shut until it holds: the Undercroft's hatch opens with the quest.

@export var target_zone := ""
@export var target_spawn := "start"
@export var only_if := ""

var _armed := false

func _ready() -> void:
	collision_layer = 0
	collision_mask = 2  # player
	body_entered.connect(_on_body)
	get_tree().create_timer(0.4).timeout.connect(func() -> void: _armed = true)

func _on_body(body: Node) -> void:
	if _armed and body.is_in_group("player") and is_open():
		Zones.go_to.call_deferred(target_zone, target_spawn)

func is_open() -> bool:
	return only_if == "" or Quests.check(JSON.parse_string(only_if))
