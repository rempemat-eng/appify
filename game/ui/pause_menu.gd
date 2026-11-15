extends PanelContainer
## The pause menu (lane R, 25 Oct: reduced motion could only be set by editing the save). It shows while
## the tree is paused (Esc or Start toggles that in game.gd) and offers Resume, Reduced motion, Pixel
## scale (fill or whole) and Quit. Beside it, on a panel of its own, the controls as they are bound now
## (ui/controls_panel.gd: text only, so the menu keeps its four rows): at its right, or at its left when
## the Sound panel stands at the right, or below it where the window shows too little of the grid; where
## no place is free of the menu and the Sound panel, the controls are not shown. Keyboard and gamepad move the
## focus (ui_up / ui_down, ui_accept);
## the mouse and touch tap. PixelScreen supplies the actual screen projection so
## rows retain at least 44 logical display points without changing world scale.
## Settings are written to the save at once; nothing here touches game rules.

var _buttons: Array[Button] = []
var _motion: Button
var _scale: Button
var _dim: ColorRect
var _controls: ControlsPanel
var _screen_scale := 0.0
var _screen_offset := Vector2.ZERO
var _safe_pixels := Rect2()

const MIN_TOUCH_POINTS := 44.0
const CONTROLS_GAP := 6.0            ## texels between the menu and the controls panel beside it

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
	# the controls: a sibling panel to the menu's right (top-level, so this container does not lay it
	# out and the menu's own size and rows stay as they are)
	_controls = ControlsPanel.new()
	_controls.name = "Controls"
	_controls.top_level = true
	add_child(_controls)
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
		if visible:
			_place_controls()
		return
	visible = paused
	if paused:
		_refresh()
		_controls.refresh()
		_place_controls.call_deferred()
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
	# Where the window shows too little of the grid for the controls beside the menu, the two stand one
	# above the other, and the menu moves up by just enough for the pair to sit centred in what is shown.
	var seen := visible_grid()
	var want := _controls.get_combined_minimum_size() if _controls != null else Vector2.ZERO
	if stacked(Rect2(position, size), want, seen, CONTROLS_GAP, _beside(Rect2(position, size))):
		position.y = seen.position.y + floorf((seen.size.y - (size.y + CONTROLS_GAP + want.y)) / 2.0)
	queue_redraw()

## The part of the art grid the window shows, inside its safe area, in art texels: the whole grid until
## PixelScreen has said otherwise (fit_screen). A window narrower than the grid at its scale (a phone
## held upright with pixel scale "whole") shows only the grid's middle.
func visible_grid() -> Rect2:
	var grid := Rect2(Vector2.ZERO, UiStyle.GRID)
	if _screen_scale <= 0.0:
		return grid
	var seen := Rect2((_safe_pixels.position - _screen_offset) / _screen_scale, _safe_pixels.size / _screen_scale)
	seen = seen.intersection(grid)
	return seen if seen.has_area() else grid

## The panels that stand beside this menu (the Sound panel, ui/sound_menu.gd: at the menu's right, top to
## top, its own GAP away), as they stand with the menu at `own`. The controls keep clear of them.
func _beside(own: Rect2) -> Array[Rect2]:
	var out: Array[Rect2] = []
	if get_parent() == null:
		return out
	for other in get_parent().get_children():
		if other is Control and other != self and other.get("beside") == self:
			var gap := float(other.get("GAP")) if other.get("GAP") != null else CONTROLS_GAP
			out.append(Rect2(Vector2(own.end.x + gap, own.position.y), (other as Control).get_combined_minimum_size()))
	return out

## The places the controls panel of size `want` may take beside a menu at `own`, best first: at the
## menu's right, top edges level; at its left; right of whatever already stands at its right; below
## the menu; above it.
static func _places(own: Rect2, want: Vector2, gap: float, taken: Array[Rect2]) -> Array[Vector2]:
	var far := own.end.x
	for t: Rect2 in taken:
		far = maxf(far, t.end.x)
	return [
		Vector2(own.end.x + gap, own.position.y),
		Vector2(own.position.x - gap - want.x, own.position.y),
		Vector2(far + gap, own.position.y),
		Vector2(own.get_center().x - want.x / 2.0, own.end.y + gap),
		Vector2(own.get_center().x - want.x / 2.0, own.position.y - gap - want.y),
	]

static func _free(at: Vector2, want: Vector2, seen: Rect2, own: Rect2, taken: Array[Rect2]) -> bool:
	var r := Rect2(at, want)
	if not seen.grow(0.01).encloses(r) or r.intersects(own):
		return false
	for t: Rect2 in taken:
		if r.intersects(t):
			return false
	return true

## True when the controls fit at neither side of the menu (nor past the panel at its right) but the two
## fit one above the other in `seen`: then the menu moves up to make the room.
static func stacked(own: Rect2, want: Vector2, seen: Rect2, gap: float, taken: Array[Rect2] = []) -> bool:
	if want == Vector2.ZERO:
		return false
	var places := _places(own, want, gap, taken)
	for i in 3:
		if _free(places[i], want, seen, own, taken):
			return false
	return own.size.y + gap + want.y <= seen.size.y

## Where the controls panel goes: the first of `_places` that lies inside `seen` (the rectangle the window
## shows, not the whole art grid) and touches neither the menu nor a panel beside it. Vector2.INF when
## there is no such place: the panel is then not shown, rather than laid over something.
static func controls_place(own: Rect2, want: Vector2, seen: Rect2, gap: float, taken: Array[Rect2] = []) -> Vector2:
	for at: Vector2 in _places(own, want, gap, taken):
		if _free(at, want, seen, own, taken):
			return at.round()
	return Vector2.INF

func _place_controls() -> void:
	var want := _controls.get_combined_minimum_size()
	var own := Rect2(global_position, size)
	var at := controls_place(own, want, visible_grid(), CONTROLS_GAP, _beside(own))
	_controls.visible = at.is_finite()
	if at.is_finite():
		_controls.size = want
		_controls.global_position = at

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
	Sound.play(&"ui_confirm")
	_refresh()

func _quit() -> void:
	# through the game, so the save holds the hearts as they are now (game.gd autosave)
	if get_tree().get_nodes_in_group("game").is_empty():
		SaveGame.save()
	else:
		get_tree().call_group("game", "autosave")
	get_tree().quit()
