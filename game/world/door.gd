class_name Door
extends Area2D
## Walk into it to go to `target_zone` at `target_spawn`. Doors arm a moment after the zone loads, so
## arriving on top of one never bounces the player straight back.

@export var target_zone := ""
@export var target_spawn := "start"

var _armed := false

func _ready() -> void:
	collision_layer = 0
	collision_mask = 2  # player
	body_entered.connect(_on_body)
	get_tree().create_timer(0.4).timeout.connect(func() -> void: _armed = true)

func _on_body(body: Node) -> void:
	if _armed and body.is_in_group("player"):
		Zones.go_to.call_deferred(target_zone, target_spawn)
