class_name Camp
extends Node2D
## A group of enemies that counts as one fight. Its child enemies report `died`; when the last one falls
## the camp sets the flag "camp_cleared:<camp_id>" and reports "camp:<camp_id>" to the quests. A cleared
## camp stays cleared: on load it removes its enemies.

signal cleared

@export var camp_id := ""

var _left := 0

func _ready() -> void:
	y_sort_enabled = true
	if SaveGame.has_flag("camp_cleared:" + camp_id):
		for c in get_children():
			c.queue_free()
		return
	for c in get_children():
		if c.has_signal("died"):
			_left += 1
			c.died.connect(_on_died)

func is_cleared() -> bool:
	return SaveGame.has_flag("camp_cleared:" + camp_id)

func _on_died() -> void:
	_left -= 1
	if _left <= 0:
		SaveGame.set_flag("camp_cleared:" + camp_id)
		Quests.notify("camp:" + camp_id)
		cleared.emit()
