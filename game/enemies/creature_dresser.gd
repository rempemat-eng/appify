class_name CreatureDresser
extends Node
## Put under a Camp: gives each SliceEnemy that enters the camp a CreatureLook (the drawn creature
## for its role), and sets the camp's bramble den beside it. It only adds looks; Codex's enemy
## behaviour (slice_enemy.gd) is untouched. The den is placed in the camp's parent, not in the camp,
## because a cleared camp frees its children on load; the den then shows calm.

## The bramble den and its clumps belong to the woodland's camp; a camp elsewhere (the Undercroft's
## rooms) takes only the creatures' looks.
@export var with_den := true
@export var den_offset := Vector2(0, -150)
@export var clump_offsets: Array[Vector2] = [Vector2(-170, -60), Vector2(150, -100), Vector2(120, 90)]

func _enter_tree() -> void:
	get_tree().node_added.connect(_on_node_added)

func _exit_tree() -> void:
	if get_tree().node_added.is_connected(_on_node_added):
		get_tree().node_added.disconnect(_on_node_added)

func _ready() -> void:
	var camp := get_parent() as Camp
	if not with_den or camp == null or camp.get_parent() == null:
		return
	var props: Array[Node2D] = [_prop(CampDen.DEN, camp, den_offset)]
	for off in clump_offsets:
		props.append(_prop(CampDen.CLUMP, camp, off))
	for p in props:
		camp.get_parent().add_child.call_deferred(p)

func _prop(kind: String, camp: Camp, offset: Vector2) -> CampDen:
	var d := CampDen.new()
	d.kind = kind
	d.camp = camp
	d.name = "Camp" + kind.capitalize()
	d.position = camp.position + offset
	return d

func _on_node_added(node: Node) -> void:
	if node is SliceEnemy and get_parent() != null and get_parent().is_ancestor_of(node):
		var look := CreatureLook.new()
		look.name = "Look"
		node.add_child.call_deferred(look)
