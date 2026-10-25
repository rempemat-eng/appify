class_name Conditional
extends Node2D
## Shows its children only while `only_if` (a quest condition as JSON, core/quests.gd) holds, and
## re-checks whenever a quest moves or a building is restored. Hidden means disabled too: the walls,
## doors and talk areas inside stop colliding, so one zone scene holds the broken and the restored town
## (data/plans/*.json items with "if"; tools/gen_blockout.py wraps them in one of these).

@export var only_if := ""

var _cond: Variant = null

func _ready() -> void:
	y_sort_enabled = true
	_cond = JSON.parse_string(only_if) if only_if != "" else null
	Quests.started.connect(func(_id: String) -> void: refresh())
	Quests.advanced.connect(func(_id: String, _s: int) -> void: refresh())
	Quests.completed.connect(func(_id: String) -> void: refresh())
	Village.changed.connect(func(_id: String) -> void: refresh())
	refresh()

func shown() -> bool:
	return Quests.check(_cond)

func refresh() -> void:
	var on := shown()
	visible = on
	process_mode = Node.PROCESS_MODE_INHERIT if on else Node.PROCESS_MODE_DISABLED
	if not on:
		# a talk area switched off does not report body_exited: let go of the player's focus here
		var player := get_tree().get_first_node_in_group("player") if is_inside_tree() else null
		if player != null and player.get("focus") is Node and is_ancestor_of(player.focus):
			player.focus = null
