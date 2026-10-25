extends Control
## A placeholder HUD on the art grid (game-design.md 11.6): health and roll charges top left, Glint top
## right, the tracked quest bottom left, and the interact prompt bottom right with the last device's key.
## Real HUD art replaces the labels later; the layout and what it reads stay.

var player: Player

@onready var _status := _label(Vector2(12, 8), HORIZONTAL_ALIGNMENT_LEFT)
@onready var _glint := _label(Vector2(-212, 8), HORIZONTAL_ALIGNMENT_RIGHT, true)
@onready var _quest := _label(Vector2(12, -26), HORIZONTAL_ALIGNMENT_LEFT, false, true)
@onready var _prompt := _label(Vector2(-212, -26), HORIZONTAL_ALIGNMENT_RIGHT, true, true)

func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE

func _label(at: Vector2, align: HorizontalAlignment, right := false, bottom := false) -> Label:
	var l := Label.new()
	l.horizontal_alignment = align
	l.add_theme_font_size_override("font_size", 12)
	l.add_theme_constant_override("outline_size", 4)
	l.add_theme_color_override("font_outline_color", Color(0.1, 0.08, 0.1))
	l.anchor_left = 1.0 if right else 0.0
	l.anchor_right = l.anchor_left
	l.anchor_top = 1.0 if bottom else 0.0
	l.anchor_bottom = l.anchor_top
	l.position = at
	l.size = Vector2(200 if right else 600, 18)
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(l)
	return l

func _process(_delta: float) -> void:
	if player == null or not is_instance_valid(player):
		return
	var hearts := "#".repeat(player.hp) + ".".repeat(player.max_hp - player.hp)
	_status.text = "HP %s   roll %s" % [hearts, "o".repeat(player.roll_charges) + "-".repeat(Player.ROLL_CHARGES - player.roll_charges)]
	_glint.text = "Glint %d" % int(SaveGame.data.glint)
	_quest.text = Quests.tracked_text()
	var f: Node = player.focus
	_prompt.visible = f != null and is_instance_valid(f) and not Dialogue.busy
	if _prompt.visible:
		_prompt.text = "%s  %s" % ["Y" if Inputs.last_device == &"gamepad" else "E", f.verb]
