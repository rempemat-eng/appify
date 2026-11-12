class_name Camp
extends Node2D
## A group of enemies that counts as one fight. Its child enemies report `died`; when the last one falls
## the camp sets the flag "camp_cleared:<camp_id>" and reports "camp:<camp_id>" to the quests. A cleared
## camp stays cleared: on load it removes its enemies. Each creature freed pays its Glint once for the life
## of the save (core/glint_cache.gd): a camp that is back after a zone reload or a defeat pays nothing again.

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
			c.died.connect(_on_died.bind(c))

func is_cleared() -> bool:
	return SaveGame.has_flag("camp_cleared:" + camp_id)

static func kind_of(creature: Node) -> String:
	return "boss" if creature is Thornback else ("creature" if creature is SliceEnemy else "mossling")

func _on_died(who: Node) -> void:
	GlintCache.pay_once("%s/%s" % [camp_id, who.name], kind_of(who))
	_left -= 1
	if _left <= 0:
		SaveGame.set_flag("camp_cleared:" + camp_id)
		Quests.notify("camp:" + camp_id)
		cleared.emit()
