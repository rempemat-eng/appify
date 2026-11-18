extends Control
## The HUD on the 960 x 540 art grid (game-design.md 11.6, lane R's 25 Oct findings): hearts and roll
## charges top left with the tracked quest on its own panel below them, Glint top right, and the interact
## prompt bottom right as a key cap with the last device's key. Pixel font and icons from UiStyle and
## ui/art (gen_hud.py), one texel per image pixel. It reads the player and the save; it changes nothing.
## Esc's pause menu (ui/pause_menu.gd) is a child, shown while the tree is paused, and so is its Sound
## panel (ui/sound_menu.gd).
## With no quest active the tracker shows the story's lead (Quests.lead: where to go on), and
## `show_card` puts a title card top centre for a few seconds (the opening and the build's closing
## beat, data/leads.json). The card never stops play; it fades unless reduced motion is on. It is hidden
## while the game is paused (it showed through the pause panels on a phone) and comes back on resume if it
## was still showing.
## The pause button, top right inside what the window shows (and its safe area), opens the same menu as
## Esc and Start, for a player with only a touch screen (15 Nov, the audit of #494). It is a square as tall
## as a pause row (at least 44 logical points), the dark panel with two cream bars drawn in code, as the
## pause menu draws its focus mark: the HUD's icons are generated pictures (ui/art/gen_hud.py), and a new
## one would be new art. It stands clear of the Glint count, the meters, the tracker, the prompt and a title
## card (and is not shown at all where guidance is off: the picture modes), presses on the touch itself (so the pause begins before the game can read the same press as a
## shot), takes no focus (the pad's A never presses it), and is hidden while paused and while the raid's
## prepare screen covers it.

const MARGIN := 8
const CARD_FADE := 0.4

var player: Player
var guidance := true                 ## false for screenshots and demos: no lead, no title card

var _hearts := HBoxContainer.new()
var _rolls := HBoxContainer.new()
var _quest := PanelContainer.new()
var _quest_title := UiStyle.label("", UiStyle.TITLE)
var _quest_step := UiStyle.label()
var _lantern := HBoxContainer.new()   ## the shard lantern's lights while a raid runs (world/raid_lantern.gd)
var _glint := UiStyle.label()
var _prompt := HBoxContainer.new()
var _prompt_key := UiStyle.label("E", UiStyle.INK)
var _prompt_verb := UiStyle.label()
var _shown := {}                     ## what each part last showed, so nodes change only on change
var _card := PanelContainer.new()
var _card_title := UiStyle.label("", UiStyle.TITLE)
var _card_sub := UiStyle.label("", UiStyle.DIM)
var _card_text := UiStyle.label()
var _card_left := 0.0                ## seconds the card still shows
var _card_tween: Tween
var _card_paused := false            ## the card was hidden by the pause and comes back on resume
var _glint_box: HBoxContainer
var _pause_menu: Control
var _pause_button: PauseButton

const PAUSE_GAP := 4                 ## texels between the pause button and a HUD piece above it

## The on-screen pause button: the HUD's panel and two upright bars, cream on an ink shadow.
class PauseButton extends Button:
	func _init() -> void:
		name = "PauseButton"
		focus_mode = Control.FOCUS_NONE
		action_mode = BaseButton.ACTION_MODE_BUTTON_PRESS
		mouse_filter = Control.MOUSE_FILTER_STOP
		tooltip_text = ""
		for state in ["normal", "hover", "pressed", "hover_pressed", "disabled"]:
			add_theme_stylebox_override(state, UiStyle.panel(0))
		add_theme_stylebox_override("focus", StyleBoxEmpty.new())

	func _draw() -> void:
		var side := minf(size.x, size.y)
		var bar := Vector2(maxf(2.0, roundf(side * 0.12)), maxf(6.0, roundf(side * 0.4)))
		var gap := bar.x
		var at := ((size - Vector2(bar.x * 2.0 + gap, bar.y)) / 2.0).floor()
		for i in 2:
			var r := Rect2(at + Vector2(i * (bar.x + gap), 0.0), bar)
			draw_rect(Rect2(r.position + Vector2.ONE, r.size), UiStyle.INK)
			draw_rect(r, UiStyle.TITLE if is_pressed() else UiStyle.TEXT)

func _ready() -> void:
	add_to_group("hud")
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
	_lantern.add_theme_constant_override("separation", 1)
	_lantern.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_lantern.visible = false
	lines.add_child(_lantern)
	_quest.add_child(lines)
	top_left.add_child(_quest)
	# Glint, top right: the number then its mark
	var glint := HBoxContainer.new()
	_glint_box = glint
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
	# the title card, top centre: a gold title at twice the text size, a dim line, the cream text
	_card.add_theme_stylebox_override("panel", UiStyle.panel(8))
	_card.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_card.set_anchors_and_offsets_preset(Control.PRESET_CENTER_TOP, Control.PRESET_MODE_MINSIZE, 44)
	_card.grow_horizontal = Control.GROW_DIRECTION_BOTH
	var card_lines := VBoxContainer.new()
	card_lines.add_theme_constant_override("separation", 4)
	card_lines.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_card_title.add_theme_font_size_override("font_size", UiStyle.SIZE * 2)
	_card_title.add_theme_constant_override("shadow_offset_x", 2)
	_card_title.add_theme_constant_override("shadow_offset_y", 2)
	_card_text.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_card_text.custom_minimum_size.x = 330
	for l: Label in [_card_title, _card_sub, _card_text]:
		l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		card_lines.add_child(l)
	_card.add_child(card_lines)
	_card.visible = false
	add_child(_card)
	# the pause button, under the menu (hidden while it shows anyway)
	_pause_button = PauseButton.new()
	_pause_button.custom_minimum_size = Vector2(UiStyle.TOUCH, UiStyle.TOUCH)
	_pause_button.pressed.connect(_open_pause)
	add_child(_pause_button)
	var pause_menu: Control = preload("res://ui/pause_menu.gd").new()
	_pause_menu = pause_menu
	add_child(pause_menu)
	var sound_menu := SoundMenu.new()    # the Sound panel, beside the pause menu (ui/sound_menu.gd)
	sound_menu.beside = pause_menu
	add_child(sound_menu)

## Shows a title card for `secs` seconds: a title, a small line under it and a sentence or two.
func show_card(title: String, subtitle: String, text: String, secs := 9.0) -> void:
	if not guidance:
		return
	_card_title.text = title
	_card_sub.text = subtitle
	_card_sub.visible = subtitle != ""
	_card_text.text = text
	_card_text.visible = text != ""
	_card_left = secs
	_card.visible = true
	_card.reset_size()
	if _card_tween != null:
		_card_tween.kill()
	_card.modulate.a = 1.0
	if not SaveGame.setting("reduced_motion", false):
		_card.modulate.a = 0.0
		_card_tween = create_tween()
		_card_tween.tween_property(_card, "modulate:a", 1.0, CARD_FADE)

func _hide_card() -> void:
	_card_left = 0.0
	if _card_tween != null:
		_card_tween.kill()
	if SaveGame.setting("reduced_motion", false):
		_card.visible = false
		return
	_card_tween = create_tween()
	_card_tween.tween_property(_card, "modulate:a", 0.0, CARD_FADE)
	_card_tween.tween_callback(func() -> void: _card.visible = false)

func _process(delta: float) -> void:
	_pause_card(get_tree().paused)
	_place_pause_button()
	if _card_left > 0.0 and not get_tree().paused:
		_card_left -= delta
		if _card_left <= 0.0:
			_hide_card()
	if player == null or not is_instance_valid(player):
		return
	_meter(_hearts, "hearts", player.hp, player.max_hp, "heart")
	_meter(_rolls, "rolls", player.roll_charges, Player.ROLL_CHARGES, "roll")
	var g := str(int(SaveGame.data.glint))
	if _shown.get("glint") != g:
		_glint_changed(int(_shown.get("glint", g)), int(g))
		_shown.glint = g
		_glint.text = g
	# a lab zone is not part of the story: no quest and no lead pointing somewhere it cannot lead
	# a raid under way takes the tracker (core/raids.gd: "The first night: Hold the shard lantern (wave 1 of 3)", and
	# "(the shardstruck are coming)" until wave 1 comes)
	var raid := Raids.tracker_text()
	_show_quest("" if Zones.in_lab() else (raid if raid != "" else Quests.tracked_text(guidance)))
	_show_lantern(get_tree().get_first_node_in_group("raid_lantern") as RaidLantern if raid != "" else null)
	var f: Node = player.focus
	var prompt := f != null and is_instance_valid(f) and not Dialogue.busy
	_prompt.visible = prompt
	if prompt:
		_prompt_key.text = "Y" if Inputs.last_device == &"gamepad" else "E"
		_prompt_verb.text = str(f.verb)

## The pause button: what Esc and Start do (game.gd), the menu shows itself while the tree is paused.
func _open_pause() -> void:
	if not get_tree().paused:
		get_tree().paused = true

## The title card stands aside while the game is paused, and comes back on resume if it is still due.
func _pause_card(paused: bool) -> void:
	if paused and _card.visible:
		_card.visible = false
		_card_paused = true
	elif not paused and _card_paused:
		_card_paused = false
		if _card_left > 0.0:
			_card.visible = true

## The HUD's pieces the pause button keeps clear of (a title card only while it shows).
func pause_button_clear_of() -> Array[Control]:
	var out: Array[Control] = [_hearts, _rolls, _quest, _glint_box, _prompt]
	if _card.visible:
		out.append(_card)
	return out

## The HUD's lasting pieces in the top half of the picture (art-grid texels): the hearts and rolls, the
## quest tracker (it grows when its text wraps), the Glint count and the pause button. The camera keeps a
## framed landmark clear of them (world/camera_framing.gd), and the play driver's `expect framed` fails
## when one covers the picture. A title card is left out: it shows for seconds over the middle of the
## picture, and moving the camera for it would swing it twice.
func top_panels() -> Array[Rect2]:
	var out: Array[Rect2] = []
	var pieces: Array[Control] = [_hearts, _rolls, _quest, _glint_box, _pause_button]
	for piece: Control in pieces:
		if piece == null or not piece.is_visible_in_tree():
			continue
		var r := piece.get_global_rect()
		if r.has_area() and r.position.y < UiStyle.GRID.y / 2.0:
			out.append(r)
	return out

## Shows the pause button where the menu can be opened from it and places it: a square as tall as a pause
## row, MARGIN in from the top right of what the window shows, moved down below any piece it would touch.
func _place_pause_button() -> void:
	# not in picture modes (guidance off: --shot, --demo and the rest), where it would cover the art the
	# review pictures look at; not while paused; not while the raid's prepare screen is open (it takes the taps)
	var raid := get_tree().get_first_node_in_group("raid_screen") as Control
	var raid_open := raid != null and (bool(raid.call(&"is_open")) if raid.has_method(&"is_open") else raid.is_visible_in_tree())
	_pause_button.visible = guidance and not get_tree().paused and not raid_open
	if not _pause_button.visible or _pause_menu == null:
		return
	var rows: Array = _pause_menu.call(&"rows")
	var side := maxf(UiStyle.TOUCH, (rows[0] as Control).custom_minimum_size.y)
	var seen: Rect2 = _pause_menu.call(&"visible_grid")   # the HUD covers the art grid: its coordinates
	var at := Vector2(seen.end.x - MARGIN - side, seen.position.y + MARGIN)
	var pieces := pause_button_clear_of()
	for i in pieces.size() + 1:
		var moved := false
		for piece: Control in pieces:
			var r := Rect2(piece.global_position - global_position, piece.size)
			if r.has_area() and Rect2(at, Vector2(side, side)).intersects(r.grow(PAUSE_GAP - 1)):
				at.y = r.end.y + PAUSE_GAP
				moved = true
		if not moved:
			break
	_pause_button.position = at
	if _pause_button.size != Vector2(side, side):
		_pause_button.size = Vector2(side, side)
		_pause_button.queue_redraw()      # the bars follow the size; a press redraws the button itself

## The count changed: it shows the new number at once, tinted for GLINT_FLASH seconds (lamp gold for a
## gain, a muted red for a loss). One finite tween; under reduced motion only the number changes.
const GLINT_FLASH := 0.5
func _glint_changed(from: int, to: int) -> void:
	if to > from:
		Sound.play(&"glint")             # before the reduced-motion return: that switch is not sound's
	if from == to or SaveGame.setting("reduced_motion", false) or not is_inside_tree():
		return
	_glint.modulate = Color("#f5d49c") if to > from else Color("#d98a7a")
	create_tween().tween_property(_glint, "modulate", Color.WHITE, GLINT_FLASH)

## What the HUD shows right now, as text (the play driver and the tests read the screen through this).
func shown_text() -> Dictionary:
	return {
		"quest_title": _quest_title.text if _quest.visible else "",
		"quest_step": _quest_step.text if _quest.visible and _quest_step.visible else "",
		"prompt": _prompt_verb.text if _prompt.visible else "",
		"glint": _glint.text,
		"banner": _card_title.text if (_card.visible or _card_paused) and _card_left > 0.0 else "",
		"banner_text": _card_text.text if (_card.visible or _card_paused) and _card_left > 0.0 else "",
		"lantern": "%d/%d" % [_shown.lantern.x, _shown.lantern.y] if _lantern.visible else "",
	}

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

## The shard lantern's lights under the raid's line, from the anvil on: what to protect, before the first
## blow (the lantern itself shows them only once it is hurt). Hidden when no raid runs.
func _show_lantern(lantern: RaidLantern) -> void:
	var now := Vector2i(lantern.hp, lantern.max_hp) if lantern != null else Vector2i(-1, -1)
	if _shown.get("lantern") == now:
		return
	_shown.lantern = now
	_lantern.visible = lantern != null
	if lantern == null:
		return
	var row := RaidLantern.lights(lantern.hp, lantern.max_hp)
	while _lantern.get_child_count() < row.size():
		_lantern.add_child(UiStyle.icon("shard_full"))
	while _lantern.get_child_count() > row.size():
		var last := _lantern.get_child(_lantern.get_child_count() - 1)
		_lantern.remove_child(last)
		last.queue_free()
	for i in row.size():
		(_lantern.get_child(i) as TextureRect).texture = load("res://ui/art/shard_%s.png" % row[i])

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
