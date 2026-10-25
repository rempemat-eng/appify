extends Node2D
## The Thornback at rest beside the shard once it has been freed and the zone is entered again (the camp
## removes the fighting Thornback when its camp is cleared). Hidden while a live Thornback is in the zone,
## so the freeing seen in the same visit is not doubled. Draws the calm loop's first drawing, facing west
## towards the chamber's door (a still picture: nothing moves while it sleeps).

const ART := "res://bosses/thornback/art/"

func _ready() -> void:
	visible = false
	var man: Variant = JSON.parse_string(FileAccess.get_file_as_string(ART + "manifest.json"))
	if typeof(man) != TYPE_DICTIONARY:
		return
	var spr := Sprite2D.new()
	spr.texture = load(ART + "sheets/calm_W.png")
	spr.hframes = int(man.clips.calm.frames)
	spr.centered = false
	spr.offset = -Vector2(man.foot_pivot[0], man.foot_pivot[1])
	add_child(spr)
	Quests.advanced.connect(func(_id: String, _s: int) -> void: refresh())
	Quests.completed.connect(func(_id: String) -> void: refresh())
	refresh.call_deferred()

func refresh() -> void:
	if not is_inside_tree():
		return
	var live := false
	for n in get_tree().get_nodes_in_group("thornback_live"):
		if is_instance_valid(n) and not n.is_queued_for_deletion():
			live = true
	visible = SaveGame.has_flag("camp_cleared:thornback") and not live
