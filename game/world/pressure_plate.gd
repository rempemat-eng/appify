class_name PressurePlate
extends Area2D
## The Undercroft puzzle's first step: step on the plate and it stays down. Sets `flag` in the save and
## tells the zone (Village.changed, as a restore does), so the Conditionals swap their pictures (the plate
## sinks, the channel to the sealed slab lights) and the game autosaves. Nothing is paid or rewarded.

signal pressed

@export var flag := "undercroft_plate"

func _ready() -> void:
	collision_layer = 0
	collision_mask = 2  # player
	body_entered.connect(_on_body)

func is_pressed() -> bool:
	return SaveGame.has_flag(flag)

func press() -> void:
	if is_pressed():
		return
	SaveGame.set_flag(flag)
	Village.changed.emit(flag)
	pressed.emit()

func _on_body(body: Node) -> void:
	if body.is_in_group("player"):
		press()
