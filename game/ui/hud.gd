extends Control
## The HUD on the 960 x 540 art grid (game-design.md 11.6, lane R's 25 Oct findings): hearts and roll
## charges top left with the tracked quest on its own panel below them, Glint top right, and the interact
## prompt bottom right as a key cap with the last device's key. Pixel font and icons from UiStyle and
## ui/art (gen_hud.py), one texel per image pixel. It reads the player and the save; it changes nothing.
## Esc's pause menu (ui/pause_menu.gd) is a child, shown while the tree is paused.

const MARGIN := 8

var player: Player

var _hearts := HBoxContainer.new()
var _rolls := HBoxContainer.new()
var _quest := PanelContainer.new()
var _quest_title := UiStyle.label("", UiStyle.TITLE)
var _quest_step := UiStyle.label()
var _glint := UiStyle.label()
var _prompt := HBoxContainer.new()
var _prompt_key := UiStyle.label("E", UiStyle.INK)
var _prompt_verb := UiStyle.label()
var _shown := {}                     ## what each part last showed, so nodes change only on change

func _ready() -> void:
	set_anchors_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	var top_left := VBoxContainer.new()
	top_left.position = Vector2(MARGIN, MARGIN)
	top_left.add_theme_constant_override("separation", 3)
	top_left.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(top_left)
	for row: HBoxContainer in [_hearts, _rolls]:
		row.add_theme_constant_override("separation", 1)
		row.mouse_filter = Control.MOUSE_FILTER_IGNORE
		top_left.add_child(row)
	# the quest tracker: its own row under the meters, never shared with another line
	_quest.add_theme_stylebox_override("panel", UiStyle.panel(2))
	_quest.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var lines := VBoxContainer.new()
	lines.add_theme_constant_override("separation", 1)
	lines.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_quest_step.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_quest_step.custom_minimum_size.x = 220
	lines.add_child(_quest_title)
	lines.add_child(_quest_step)
	_quest.add_child(lines)
	top_left.add_child(_quest)
	# Glint, top right: the number then its mark
	var glint := HBoxContainer.new()
	glint.add_theme_constant_override("separation", 3)
	glint.mouse_filter = Control.MOUSE_FILTER_IGNORE
	glint.set_anchors_and_offsets_preset(Control.PRESET_TOP_RIGHT, Control.PRESET_MODE_KEEP_SIZE, MARGIN)
	glint.grow_horizontal = Control.GROW_DIRECTION_BEGIN
	_glint.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	glint.add_child(_glint)
	glint.add_child(UiStyle.icon("glint"))
	add_child(glint)
	# the interact prompt, bottom right
	_prompt.add_theme_constant_override("separation", 4)
	_prompt.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_prompt.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_RIGHT, Control.PRESET_MODE_KEEP_SIZE, MARGIN)
	_prompt.grow_horizontal = Control.GROW_DIRECTION_BEGIN
	_prompt.grow_vertical = Control.GROW_DIRECTION_BEGIN
	var cap := PanelContainer.new()
	cap.add_theme_stylebox_override("panel", UiStyle.key_cap())
	cap.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_prompt_key.remove_theme_color_override("font_shadow_color")
	_prompt_key.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	cap.add_child(_prompt_key)
	_prompt.add_child(cap)
	_prompt.add_child(_prompt_verb)
	_prompt.visible = false
	add_child(_prompt)
	add_child(preload("res://ui/pause_menu.gd").new())

func _process(_delta: float) -> void:
	if player == null or not is_instance_valid(player):
		return
	_meter(_hearts, "hearts", player.hp, player.max_hp, "heart")
	_meter(_rolls, "rolls", player.roll_charges, Player.ROLL_CHARGES, "roll")
	var g := str(int(SaveGame.data.glint))
	if _shown.get("glint") != g:
		_shown.glint = g
		_glint.text = g
	_show_quest(Quests.tracked_text())
	var f: Node = player.focus
	var prompt := f != null and is_instance_valid(f) and not Dialogue.busy
	_prompt.visible = prompt
	if prompt:
		_prompt_key.text = "Y" if Inputs.last_device == &"gamepad" else "E"
		_prompt_verb.text = str(f.verb)

## A row of `total` icons, the first `full` of them filled.
func _meter(row: HBoxContainer, key: String, full: int, total: int, art: String) -> void:
	var now := Vector2i(clampi(full, 0, total), total)
	if _shown.get(key) == now:
		return
	_shown[key] = now
	while row.get_child_count() < total:
		row.add_child(UiStyle.icon(art + "_full"))
	while row.get_child_count() > total:
		var last := row.get_child(row.get_child_count() - 1)
		row.remove_child(last)
		last.queue_free()
	for i in total:
		(row.get_child(i) as TextureRect).texture = load("res://ui/art/%s_%s.png" % [art, "full" if i < now.x else "empty"])

## "Title: step" from Quests.tracked_text(), as a gold title over the step.
func _show_quest(text: String) -> void:
	if _shown.get("quest") == text:
		return
	_shown.quest = text
	_quest.visible = text != ""
	var cut := text.find(": ")
	_quest_title.text = text.substr(0, cut) if cut >= 0 else text
	_quest_step.text = text.substr(cut + 2) if cut >= 0 else ""
	_quest_step.visible = _quest_step.text != ""
