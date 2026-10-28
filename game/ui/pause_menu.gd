extends PanelContainer
## The pause menu (lane R, 25 Oct: reduced motion could only be set by editing the save). It shows while
## the tree is paused (Esc or Start toggles that in game.gd) and offers Resume, Reduced motion, Pixel
## scale (fill or whole) and Quit. Keyboard and gamepad move the focus (ui_up / ui_down, ui_accept);
## the mouse and touch tap. PixelScreen supplies the actual screen projection so
## rows retain at least 44 logical display points without changing world scale.
## Settings are written to the save at once; nothing here touches game rules.

var _buttons: Array[Button] = []
var _motion: Button
var _scale: Button
var _dim: ColorRect
var _screen_scale := 0.0
var _screen_offset := Vector2.ZERO
var _safe_pixels := Rect2()

const MIN_TOUCH_POINTS := 44.0

func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	add_to_group(&"pause_screen_layout")
	visible = false
	mouse_filter = Control.MOUSE_FILTER_STOP
	add_theme_stylebox_override("panel", UiStyle.panel(6))
	var dim := ColorRect.new()          # the world dimmed behind the menu; containers skip top-level children
	_dim = dim
	dim.top_level = true
	dim.show_behind_parent = true
	dim.color = Color(UiStyle.INK, 0.55)
	dim.size = UiStyle.GRID
	dim.mouse_filter = Control.MOUSE_FILTER_STOP     # clicks on the world do nothing while paused
	add_child(dim)
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 0)
	add_child(box)
	var title := UiStyle.label("Paused", UiStyle.TITLE)
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	title.custom_minimum_size.y = 16
	box.add_child(title)
	_add(box, "Resume", _resume)
	_motion = _add(box, "", _toggle_motion)
	_scale = _add(box, "", _toggle_scale)
	_add(box, "Quit", _quit)
	for i in _buttons.size():  # wrap the focus top to bottom
		var b := _buttons[i]
		b.focus_neighbor_top = b.get_path_to(_buttons[i - 1])
		b.focus_neighbor_bottom = b.get_path_to(_buttons[(i + 1) % _buttons.size()])
	_refresh()
	grow_horizontal = Control.GROW_DIRECTION_BOTH
	grow_vertical = Control.GROW_DIRECTION_BOTH
	set_anchors_and_offsets_preset(Control.PRESET_CENTER, Control.PRESET_MODE_MINSIZE)

func _add(box: VBoxContainer, text: String, action: Callable) -> Button:
	var b := Button.new()
	b.text = text
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
	b.pressed.connect(action)
	b.mouse_entered.connect(b.grab_focus)                       # one highlight, wherever it came from
	b.focus_entered.connect(queue_redraw)
	box.add_child(b)
	_buttons.append(b)
	return b

func _process(_delta: float) -> void:
	if _screen_scale > 0.0:
		_position_in_safe_area()
	var paused := get_tree().paused
	if paused == visible:
		return
	visible = paused
	if paused:
		_refresh()
		_buttons[0].grab_focus.call_deferred()
	else:
		var f := get_viewport().gui_get_focus_owner()
		if f != null and is_ancestor_of(f):
			f.release_focus()

## Inputs are physical window pixels, physical pixels per ART texel, and physical
## pixels per logical point. The safe rectangle is window-relative physical pixels.
## No save, action, focus order, world scale or art viewport setting changes here.
func fit_screen(window_pixels: Vector2, art_scale: float, offset: Vector2, ratio: float, safe_pixels: Rect2) -> bool:
	if not window_pixels.is_finite() or window_pixels.x <= 0.0 or window_pixels.y <= 0.0:
		return false
	if not is_finite(art_scale) or art_scale <= 0.0 or not is_finite(ratio) or ratio <= 0.0 or not offset.is_finite():
		return false
	if not safe_pixels.position.is_finite() or not safe_pixels.end.is_finite() or not safe_pixels.has_area():
		return false
	if not Rect2(Vector2.ZERO, window_pixels).encloses(safe_pixels) or _buttons.is_empty():
		return false
	var row_height := ceilf(MIN_TOUCH_POINTS * ratio / art_scale)
	if not is_finite(row_height):
		return false
	_screen_scale = art_scale
	_screen_offset = offset
	_safe_pixels = safe_pixels
	for button in _buttons:
		button.custom_minimum_size.y = maxf(UiStyle.TOUCH, row_height)
	# The dimmer also covers letterbox/cropped-window regions while paused.
	_dim.position = -offset / art_scale
	_dim.size = window_pixels / art_scale
	_position_in_safe_area.call_deferred()
	return true

func _position_in_safe_area() -> void:
	if _screen_scale <= 0.0:
		return
	size = get_combined_minimum_size()
	position = (_safe_pixels.get_center() - _screen_offset) / _screen_scale - size / 2.0
	queue_redraw()

## The focus mark: a small gold chevron left of the focused row.
func _draw() -> void:
	for b in _buttons:
		if b.has_focus():
			var r := b.get_global_rect()
			var at := r.position - get_global_position() + Vector2(3, floorf(r.size.y / 2.0) - 2)
			for i in 3:
				draw_rect(Rect2(at + Vector2(i, i), Vector2(1, 5 - 2 * i)), UiStyle.TITLE)

func _refresh() -> void:
	_motion.text = "Reduced motion: %s" % ("on" if SaveGame.setting("reduced_motion", false) else "off")
	_scale.text = "Pixel scale: %s" % ("whole" if str(SaveGame.setting("pixel_scale", "fill")) == "whole" else "fill")
	queue_redraw()

func _resume() -> void:
	get_tree().paused = false

func _toggle_motion() -> void:
	_write("reduced_motion", not SaveGame.setting("reduced_motion", false))

func _toggle_scale() -> void:
	_write("pixel_scale", "fill" if str(SaveGame.setting("pixel_scale", "fill")) == "whole" else "whole")
	get_window().size_changed.emit()   # main/pixel_screen.gd refits on this signal

func _write(key: String, value: Variant) -> void:
	SaveGame.data.settings[key] = value
	SaveGame.save()
	_refresh()

func _quit() -> void:
	SaveGame.save()
	get_tree().quit()
