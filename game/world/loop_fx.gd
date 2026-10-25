class_name LoopFx
extends Sprite2D
## A small looping effect drawn as a strip (tools/gen_village_fx.py): the forge fire, chimney
## smoke. It only animates while it is on screen and the screen is active, and shows one still
## drawing under reduced motion (game-design 11: effects are finite and respect reduced motion).

@export var fps := 8.0

var _t := 0.0
var _on_screen := false

func _ready() -> void:
	var vis := VisibleOnScreenNotifier2D.new()
	if texture != null and hframes > 0:
		var w := texture.get_width() / hframes
		var h := texture.get_height()
		vis.rect = Rect2(offset if not centered else Vector2(-w / 2.0, -h / 2.0), Vector2(w, h))
	vis.screen_entered.connect(func() -> void: _on_screen = true)
	vis.screen_exited.connect(func() -> void: _on_screen = false)
	add_child(vis)
	frame = 0

func _process(delta: float) -> void:
	if SaveGame.setting("reduced_motion", false):
		frame = 0
		return
	if not _on_screen or not is_visible_in_tree():
		return
	_t += delta
	frame = int(_t * fps) % hframes
