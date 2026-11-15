class_name SoundMenu
extends PanelContainer
## The pause menu's Sound panel (docs/vision/sound.md): three switches beside the pause menu, shown with
## it while the tree is paused. Sound effects and Ambience are on by default; Gentle sound is off by
## default (confirms and moments only, and no two effects within 400 ms: core/sound_rules.gd). Each is
## written to the save at once, like the pause menu's own settings, and none of them touches a game rule.
## Gentle sound and Reduced motion are separate switches: neither reads the other.
##
## It is a panel of its own, to the right of the pause menu (`beside`, set by the HUD), with rows the same
## height as the pause menu's: at least 44 logical display points, from the same `fit_screen` call
## (main/pixel_screen.gd). The pause menu says where it stands (`place_beside`), so the two stay inside
## what the window shows: in a window narrower than the two side by side, this panel stands below the
## menu. Side by side, up and down wrap inside each panel and left and right cross between the two (the
## engine's nearest-neighbour focus); one above the other, up and down run through both panels in one
## ring (`_link`). The mouse and touch tap; Enter, Space and the pad's A press the focused row.
## While the pause menu's Quit asks (Quit or Stay), this panel stands aside, its room kept.

const ROWS := [
	["sound_effects", "Sound effects", true],
	["ambience", "Ambience", true],
	["gentle_sound", "Gentle sound", false],
]
const GAP := 6.0                     ## texels between the pause menu and this panel
const MIN_TOUCH_POINTS := 44.0

var beside: Control                  ## the pause menu: this panel stands at its right, top to top

var _buttons: Array[Button] = []
var _below := false                  ## standing below the pause menu, not at its right (a narrow window)
var _linked := false                 ## `_link` has run once

func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	add_to_group(&"pause_screen_layout")
	visible = false
	mouse_filter = Control.MOUSE_FILTER_STOP
	add_theme_stylebox_override("panel", UiStyle.panel(6))
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 0)
	add_child(box)
	var title := UiStyle.label("Sound", UiStyle.TITLE)
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	title.custom_minimum_size.y = 16
	box.add_child(title)
	for row: Array in ROWS:
		_add(box, String(row[0]))
	for i in _buttons.size():        # wrap the focus top to bottom
		var b := _buttons[i]
		b.focus_neighbor_top = b.get_path_to(_buttons[i - 1])
		b.focus_neighbor_bottom = b.get_path_to(_buttons[(i + 1) % _buttons.size()])
	_refresh()

func _add(box: VBoxContainer, key: String) -> void:
	var b := Button.new()
	b.name = key
	b.flat = true
	b.alignment = HORIZONTAL_ALIGNMENT_LEFT
	b.custom_minimum_size = Vector2(150, UiStyle.TOUCH)
	b.add_theme_font_override("font", UiStyle.font())
	b.add_theme_font_size_override("font_size", UiStyle.SIZE)
	b.add_theme_color_override("font_color", UiStyle.DIM)
	for state in ["font_hover_color", "font_focus_color", "font_pressed_color", "font_hover_pressed_color"]:
		b.add_theme_color_override(state, UiStyle.TITLE)
	var empty := StyleBoxEmpty.new()
	empty.content_margin_left = 10                              # room for the focus mark
	for state in ["normal", "hover", "pressed", "focus", "hover_pressed", "disabled"]:
		b.add_theme_stylebox_override(state, empty)
	b.pressed.connect(toggle.bind(key))
	b.mouse_entered.connect(b.grab_focus)
	b.focus_entered.connect(queue_redraw)
	b.focus_exited.connect(queue_redraw)
	box.add_child(b)
	_buttons.append(b)

func _process(_delta: float) -> void:
	# shown while paused, except while the pause menu's Quit asks (ui/pause_menu.gd asking)
	var paused := get_tree().paused and not (beside != null and is_instance_valid(beside)
		and beside.has_method(&"asking") and bool(beside.call(&"asking")))
	if paused != visible:
		visible = paused
		if paused:
			_refresh()
		else:
			var f := get_viewport().gui_get_focus_owner()
			if f != null and is_ancestor_of(f):
				f.release_focus()
	if visible:
		_stand_beside()

## Rows as tall as the pause menu's: 44 logical points at this window's scale (the same inputs).
func fit_screen(window_pixels: Vector2, art_scale: float, _offset: Vector2, ratio: float, _safe_pixels: Rect2) -> bool:
	if not window_pixels.is_finite() or window_pixels.x <= 0.0 or window_pixels.y <= 0.0:
		return false
	if not is_finite(art_scale) or art_scale <= 0.0 or not is_finite(ratio) or ratio <= 0.0:
		return false
	var row_height := ceilf(MIN_TOUCH_POINTS * ratio / art_scale)
	if not is_finite(row_height):
		return false
	for button in _buttons:
		button.custom_minimum_size.y = maxf(UiStyle.TOUCH, row_height)
	_stand_beside.call_deferred()
	return true

func _stand_beside() -> void:
	size = get_combined_minimum_size()
	if beside != null and is_instance_valid(beside):
		if beside.has_method(&"place_beside"):
			position = beside.call(&"place_beside", size, GAP)
		else:
			position = beside.position + Vector2(beside.size.x + GAP, 0.0)
		var below := position.y >= beside.position.y + beside.size.y
		if below != _below or not _linked:
			_below = below
			_link()
	queue_redraw()

## Up and down at the ends of the two panels. Side by side each panel wraps on its own. One above the
## other, sideways finds nothing, so the two make one ring: down from the menu's last row comes to this
## panel's first, and down from this panel's last to the menu's first.
func _link() -> void:
	var theirs: Array = beside.call(&"rows") if beside.has_method(&"rows") else []
	if theirs.is_empty() or _buttons.is_empty():
		return
	var mine_first := _buttons[0]
	var mine_last := _buttons[-1]
	var their_first: Button = theirs[0]
	var their_last: Button = theirs[-1]
	their_last.focus_neighbor_bottom = their_last.get_path_to(mine_first if _below else their_first)
	their_first.focus_neighbor_top = their_first.get_path_to(mine_last if _below else their_last)
	mine_first.focus_neighbor_top = mine_first.get_path_to(their_last if _below else mine_last)
	mine_last.focus_neighbor_bottom = mine_last.get_path_to(their_first if _below else mine_first)
	# Sideways, by row: side by side, left and right cross between the two panels row for row (the menu's
	# Pixel scale and Quit both to Gentle sound); one above the other, they stay. Never to a control
	# outside the two: the raid's prepare screen keeps running under the pause, and the engine's nearest
	# neighbour reached its buttons from here (15 Nov).
	for i in theirs.size():
		var row: Button = theirs[i]
		row.focus_neighbor_right = row.get_path_to(row if _below else _buttons[mini(i, _buttons.size() - 1)])
		row.focus_neighbor_left = row.get_path_to(row)
	for i in _buttons.size():
		var row := _buttons[i]
		row.focus_neighbor_left = row.get_path_to(row if _below else theirs[mini(i, theirs.size() - 1)])
		row.focus_neighbor_right = row.get_path_to(row)
	_linked = true

## The focus mark: the pause menu's small gold chevron, left of the focused row.
func _draw() -> void:
	for b in _buttons:
		if b.has_focus():
			var r := b.get_global_rect()
			var at := r.position - get_global_position() + Vector2(3, floorf(r.size.y / 2.0) - 2)
			for i in 3:
				draw_rect(Rect2(at + Vector2(i, i), Vector2(1, 5 - 2 * i)), UiStyle.TITLE)

func is_on(key: String) -> bool:
	for row: Array in ROWS:
		if row[0] == key:
			return bool(SaveGame.setting(key, row[2]))
	return false

func _refresh() -> void:
	for i in _buttons.size():
		_buttons[i].text = "%s: %s" % [ROWS[i][1], "on" if is_on(String(ROWS[i][0])) else "off"]
	queue_redraw()

## Flips one switch, saves, and tells the sound at once (effects switched off stop mid-note).
func toggle(key: String) -> void:
	SaveGame.data.settings[key] = not is_on(key)
	SaveGame.save()
	Sound.settings_changed()
	Sound.play(&"ui_confirm")
	_refresh()
