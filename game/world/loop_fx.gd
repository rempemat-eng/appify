class_name LoopFx
extends Sprite2D
## A small looping effect drawn as a strip (tools/gen_village_fx.py): the forge fire, chimney
## smoke. It only animates while it is on screen and the screen is active, and shows one still
## drawing under reduced motion (game-design 11: effects are finite and respect reduced motion).

@export var fps := 8.0

var _t := 0.0
var _on_screen := false
var _phase := 0

func _ready() -> void:
	var vis := VisibleOnScreenNotifier2D.new()
	if texture != null and hframes > 0:
		var w := texture.get_width() / hframes
		var h := texture.get_height()
		vis.rect = Rect2(offset if not centered else Vector2(-w / 2.0, -h / 2.0), Vector2(w, h))
	vis.screen_entered.connect(func() -> void: _on_screen = true)
	vis.screen_exited.connect(func() -> void: _on_screen = false)
	add_child(vis)
	_phase = _placement_phase()
	frame = 0 if SaveGame.setting("reduced_motion", false) else _phase

func _process(delta: float) -> void:
	if SaveGame.setting("reduced_motion", false):
		frame = 0
		return
	if not _on_screen or not is_visible_in_tree():
		return
	_t += delta
	frame = (int(_t * fps) + _phase) % hframes

## Identity comes from the authored placement, never its runtime instance ID or global RNG.
## Read metadata by name so the runtime does not depend on the editor's KitPiece classes.
func _placement_phase() -> int:
	if hframes <= 1:
		return 0
	var placement: Node = get_parent()
	while placement != null and not placement.has_meta("kit_zone_entry"):
		placement = placement.get_parent()
	if placement == null:
		return 0
	var entry: Variant = placement.get_meta("kit_zone_entry")
	if not entry is Dictionary:
		return 0
	var placement_id: Variant = entry.get("id")
	if not placement_id is String or placement_id.strip_edges().is_empty():
		return 0
	var zone := ""
	var ancestor: Node = placement
	while ancestor != null:
		var plan: Variant = ancestor.get_meta("kit_zone_plan", {})
		if plan is Dictionary:
			var zone_id: Variant = plan.get("zone")
			if zone_id is String and not zone_id.strip_edges().is_empty():
				zone = zone_id
				break
		ancestor = ancestor.get_parent()
	var effect_path := String(placement.get_path_to(self))
	# Length prefixes keep distinct component tuples distinct before hashing.
	var identity := "%d:%s%d:%s%d:%s" % [zone.length(), zone, placement_id.length(), placement_id, effect_path.length(), effect_path]
	# Fixed positive integer hash; the modulus bounds every multiply within int64.
	var value: int = 5381
	for i in identity.length():
		value = (value * 33 + identity.unicode_at(i)) % 2147483647
	return value % hframes
