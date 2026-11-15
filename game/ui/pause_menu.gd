extends PanelContainer
## The pause menu (lane R, 25 Oct: reduced motion could only be set by editing the save). It shows while
## the tree is paused (Esc or Start toggles that in game.gd) and offers Resume, Reduced motion, Pixel
## scale (fill or whole) and Quit. Beside it, on a panel of its own, the controls as they are bound now
## (ui/controls_panel.gd: text only, so the menu keeps its four rows): at its right, or at its left when
## the Sound panel stands at the right, or below it where the window shows too little of the grid; where
## no place is free of the menu and the Sound panel, the controls are not shown. The menu and the Sound
## panel always stay inside what the window shows: side by side, moved over together where the window is
## narrow, or one above the other where it is narrower than the two (`menu_place`, `side_place`).
## Keyboard and gamepad move the focus (ui_up / ui_down on the arrows, the d-pad and the left stick) and
## press the focused row (ui_accept: Enter, Space, and the pad's A, which core/inputs.gd adds);
## the mouse and touch tap. PixelScreen supplies the actual screen projection so
## rows retain at least 44 logical display points without changing world scale.
## Settings are written to the save at once; nothing here touches game rules.
## Quit asks first, inside the menu ("Quit the game?", Quit or Stay, the focus on Stay): Quit is one row
## from Resume and a tap away. Stay goes back to the rows with the focus on Quit (Esc and Start still end
## the pause, as everywhere in the menu, and the menu opens on its rows again).
## Closing hands the focus back to the control that had it before the pause (the raid's prepare screen),
## or to none when none had it (play: the pad's A rolls and presses nothing).

var _buttons: Array[Button] = []
var _motion: Button
var _scale: Button
var _dim: ColorRect
var _dim_rect := Rect2(Vector2.ZERO, UiStyle.GRID)     ## what the dim covers, in the canvas's own texels
var _controls: ControlsPanel
var _screen_scale := 0.0
var _screen_offset := Vector2.ZERO
var _safe_pixels := Rect2()
var _box: VBoxContainer
var _confirm: Array[Control] = []       ## the question and its two rows while Quit asks; empty otherwise
var _confirm_buttons: Array[Button] = []
var _return_to: Object                  ## what had the focus when the pause began (a Control)

const MIN_TOUCH_POINTS := 44.0
const CONTROLS_GAP := 6.0            ## texels between the menu and the controls panel beside it

func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	add_to_group(&"pause_screen_layout")
	visible = false
	mouse_filter = Control.MOUSE_FILTER_STOP
	add_theme_stylebox_override("panel", UiStyle.panel(6))
	# The world dimmed behind the menu. It stops the mouse, so clicks on the world do nothing while paused,
	# and it must be asked after the rows: the engine asks every top-level control before the rest of the
	# screen, so a top-level dim took each click and tap meant for a row (15 Nov: Resume could not be
	# clicked). It is an ordinary child now, the first, in a plain holder that this container may lay out
	# as it likes; the dim inside the holder keeps the rectangle `_place_dim` gives it.
	var back := Control.new()
	back.name = "Back"
	back.show_behind_parent = true
	back.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(back)
	var dim := ColorRect.new()
	_dim = dim
	dim.name = "Dim"
	dim.color = Color(UiStyle.INK, 0.55)
	dim.size = UiStyle.GRID
	dim.mouse_filter = Control.MOUSE_FILTER_STOP
	back.add_child(dim)
	item_rect_changed.connect(_place_dim)
	visibility_changed.connect(_place_dim)
	# the controls: a sibling panel to the menu's right (top-level, so this container does not lay it
	# out and the menu's own size and rows stay as they are)
	_controls = ControlsPanel.new()
	_controls.name = "Controls"
	_controls.top_level = true
	add_child(_controls)
	var box := VBoxContainer.new()
	_box = box
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
	_ring(_buttons)
	for b in _buttons:         # sideways nowhere, until the Sound panel links its rows to these (sound_menu.gd)
		b.focus_neighbor_left = b.get_path_to(b)
		b.focus_neighbor_right = b.get_path_to(b)
	_refresh()
	grow_horizontal = Control.GROW_DIRECTION_BOTH
	grow_vertical = Control.GROW_DIRECTION_BOTH
	set_anchors_and_offsets_preset(Control.PRESET_CENTER, Control.PRESET_MODE_MINSIZE)

## Wraps the focus top to bottom through `rows`.
static func _ring(rows: Array[Button]) -> void:
	for i in rows.size():
		var b := rows[i]
		b.focus_neighbor_top = b.get_path_to(rows[i - 1])
		b.focus_neighbor_bottom = b.get_path_to(rows[(i + 1) % rows.size()])

func _add(box: VBoxContainer, text: String, action: Callable) -> Button:
	var b := _row(text, action)
	box.add_child(b)
	_buttons.append(b)
	return b

func _row(text: String, action: Callable) -> Button:
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
	return b

func _process(_delta: float) -> void:
	if _screen_scale > 0.0:
		_position_in_safe_area()
	var paused := get_tree().paused
	if paused == visible:
		if visible:
			_place_dim()
			_place_controls()
		return
	visible = paused
	if paused:
		# what had the focus (the raid's prepare screen has it on a button): it gets it back on closing
		var had := get_viewport().gui_get_focus_owner()
		_return_to = had if had != null and not is_ancestor_of(had) and not _beside_has(had) else null
		_refresh()
		_controls.refresh()
		_place_controls.call_deferred()
		_buttons[0].grab_focus.call_deferred()
	else:
		_end_asking()
		var f := get_viewport().gui_get_focus_owner()
		if f != null and is_ancestor_of(f):
			f.release_focus()
		_hand_back_focus()

## On closing: the focus goes back to what had it when the pause began, if that is still there and shown;
## otherwise to nothing, as before the pause (15 Nov, the audit of #494: Resume left no control focused,
## so on the raid's prepare screen the d-pad and A did nothing more).
func _hand_back_focus() -> void:
	var kept := _return_to
	_return_to = null
	if not is_instance_valid(kept):
		return
	var back := kept as Control
	if back == null or not back.is_inside_tree() or not back.is_visible_in_tree():
		return
	if back.focus_mode == Control.FOCUS_NONE or is_ancestor_of(back) or _beside_has(back):
		return
	back.grab_focus()

## True when `node` is in a panel beside this menu (the Sound panel).
func _beside_has(node: Node) -> bool:
	for panel: Control in _side_panels():
		if panel.is_ancestor_of(node):
			return true
	return false

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
	for button in _buttons + _confirm_buttons:
		button.custom_minimum_size.y = maxf(UiStyle.TOUCH, row_height)
	if not _confirm.is_empty():
		_confirm[0].custom_minimum_size.y = 2.0 * _buttons[0].custom_minimum_size.y
	# The dimmer also covers letterbox/cropped-window regions while paused.
	_dim_rect = Rect2(-offset / art_scale, window_pixels / art_scale)
	_place_dim()
	_position_in_safe_area.call_deferred()
	return true

func _position_in_safe_area() -> void:
	if _screen_scale <= 0.0:
		return
	size = get_combined_minimum_size()
	var seen := _seen_here()
	var side := _side()
	var centred := (_safe_pixels.get_center() - _screen_offset) / _screen_scale - size / 2.0
	position = menu_place(centred, size, side.size, seen, side.position.x)
	# Where the window shows too little of the grid for the controls beside the menu, the two stand one
	# above the other, and the menu (with the panel at its side) moves up by just enough for all of it to
	# sit centred in what is shown.
	var want := _controls.get_combined_minimum_size() if _controls != null else Vector2.ZERO
	var own := Rect2(position, size)
	var taken := _beside(own, seen)
	if stacked(own, want, seen, CONTROLS_GAP, taken):
		var group := own
		for t: Rect2 in taken:
			group = group.merge(t)
		position.y += seen.position.y + floorf((seen.size.y - (group.size.y + CONTROLS_GAP + want.y)) / 2.0) - group.position.y
	_place_dim()
	queue_redraw()

## The dim keeps its rectangle on the screen wherever the menu stands.
func _place_dim() -> void:
	if _dim == null or not is_inside_tree():
		return
	_dim.global_position = _dim_rect.position
	_dim.size = _dim_rect.size

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

## `visible_grid` in the coordinates this menu's `position` is in (its parent's).
func _seen_here() -> Rect2:
	var seen := visible_grid()
	var parent := get_parent() as Control
	if parent != null:
		seen.position -= parent.global_position
	return seen

## The panels that stand beside this menu: the siblings whose `beside` is this menu (the Sound panel,
## ui/sound_menu.gd).
func _side_panels() -> Array[Control]:
	var out: Array[Control] = []
	if get_parent() == null:
		return out
	for other in get_parent().get_children():
		if other is Control and other != self and other.get("beside") == self:
			out.append(other as Control)
	return out

static func _gap_of(panel: Control) -> float:
	return float(panel.get("GAP")) if panel.get("GAP") != null else CONTROLS_GAP

## The first panel beside this menu as a rectangle: its smallest size, with its gap as `position.x`.
## No area when there is none.
func _side() -> Rect2:
	for panel: Control in _side_panels():
		return Rect2(Vector2(_gap_of(panel), 0.0), panel.get_combined_minimum_size())
	return Rect2()

## The panels beside this menu as they stand with the menu at `own`, in the coordinates of `own` and
## `seen`. The controls keep clear of them.
func _beside(own: Rect2, seen: Rect2) -> Array[Rect2]:
	var out: Array[Rect2] = []
	for panel: Control in _side_panels():
		var want := panel.get_combined_minimum_size()
		out.append(Rect2(side_place(own, want, seen, _gap_of(panel)), want))
	return out

## Where a panel of size `want` beside this menu stands now, `gap` texels from it (the Sound panel asks
## each frame): a `position` beside this menu's own.
func place_beside(want: Vector2, gap: float) -> Vector2:
	return side_place(Rect2(position, size), want, _seen_here(), gap)

## True when the window shows too little width for a menu `own` wide and a panel `side` wide next to each
## other: the panel then stands below the menu.
static func side_below(own: Vector2, side: Vector2, seen: Rect2, gap: float) -> bool:
	return own.x + gap + side.x > seen.size.x + 0.01

## Where a panel of size `side` stands beside a menu at `own`: at its right, top edges level, or below
## it, centred on it, where `seen` is too narrow for the two (`side_below`).
static func side_place(own: Rect2, side: Vector2, seen: Rect2, gap: float) -> Vector2:
	if side_below(own.size, side, seen, gap):
		return Vector2(own.position.x + floorf((own.size.x - side.x) / 2.0), own.end.y + gap)
	return Vector2(own.end.x + gap, own.position.y)

## Where the menu of size `own` stands so that it and the panel beside it (`side`, zero for none) lie
## inside `seen`: at `centred` (the middle of the window) when the panel then fits at its right; else
## moved left by just enough for the two to sit centred side by side; else, in a window narrower than the
## two, in the middle with the panel below it, the two centred top to bottom (from the top edge when
## even that is too tall).
static func menu_place(centred: Vector2, own: Vector2, side: Vector2, seen: Rect2, gap: float) -> Vector2:
	var at := centred
	if side == Vector2.ZERO:
		return at
	if side_below(own, side, seen, gap):
		at.y = seen.position.y + maxf(0.0, floorf((seen.size.y - (own.y + gap + side.y)) / 2.0))
	elif at.x + own.x + gap + side.x > seen.end.x + 0.01:
		at.x = seen.position.x + floorf((seen.size.x - (own.x + gap + side.x)) / 2.0)
	return at

## The places the controls panel of size `want` may take beside a menu at `own`, best first: at the
## menu's right, top edges level; at its left; right of whatever already stands at its right; below
## the menu and whatever stands beside or below it; above them. The last two are centred on the menu
## together with the panels beside it that `seen` shows whole, and pushed sideways into `seen` where
## that centre would leave it.
static func _places(own: Rect2, want: Vector2, gap: float, taken: Array[Rect2], seen: Rect2) -> Array[Vector2]:
	var far := own.end.x
	var low := own.end.y
	var high := own.position.y
	var group := own
	for t: Rect2 in taken:
		far = maxf(far, t.end.x)
		low = maxf(low, t.end.y)
		high = minf(high, t.position.y)
		if seen.grow(0.01).encloses(t):
			group = group.merge(t)
	var x := clampf(group.get_center().x - want.x / 2.0, seen.position.x, maxf(seen.position.x, seen.end.x - want.x))
	return [
		Vector2(own.end.x + gap, own.position.y),
		Vector2(own.position.x - gap - want.x, own.position.y),
		Vector2(far + gap, own.position.y),
		Vector2(x, low + gap),
		Vector2(x, high - gap - want.y),
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
	var places := _places(own, want, gap, taken, seen)
	for i in 3:
		if _free(places[i], want, seen, own, taken):
			return false
	var tall := own.size.y           # the menu and what stands beside or below it, top to bottom
	for t: Rect2 in taken:
		tall = maxf(tall, t.end.y - own.position.y)
	return tall + gap + want.y <= seen.size.y

## Where the controls panel goes: the first of `_places` that lies inside `seen` (the rectangle the window
## shows, not the whole art grid) and touches neither the menu nor a panel beside it. Vector2.INF when
## there is no such place: the panel is then not shown, rather than laid over something.
static func controls_place(own: Rect2, want: Vector2, seen: Rect2, gap: float, taken: Array[Rect2] = []) -> Vector2:
	for at: Vector2 in _places(own, want, gap, taken, seen):
		if _free(at, want, seen, own, taken):
			return at.round()
	return Vector2.INF

func _place_controls() -> void:
	var want := _controls.get_combined_minimum_size()
	var own := Rect2(global_position, size)
	var seen := visible_grid()
	var at := controls_place(own, want, seen, CONTROLS_GAP, _beside(own, seen))
	_controls.visible = at.is_finite() and not asking()
	if _controls.visible:
		_controls.size = want
		_controls.global_position = at

## The rows, top to bottom (the Sound panel joins its focus ring to them where it stands below).
func rows() -> Array[Button]:
	return _buttons

## The focus mark: a small gold chevron left of the focused row.
func _draw() -> void:
	for b in _buttons + _confirm_buttons:
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

## True while Quit asks (the Sound panel and the controls stand aside meanwhile).
func asking() -> bool:
	return not _confirm.is_empty()

## Quit, pressed: the four rows give way to the question and its two rows, in the same place and the same
## size, so the Sound panel's room and every other row stay where they were, and Stay stands where Quit did
## (a second tap on Quit lands on Stay). The focus starts on Stay.
func ask_quit() -> void:
	if asking():
		return
	var row_height := _buttons[0].custom_minimum_size.y
	var question := UiStyle.label("Quit the game?", UiStyle.TEXT)
	question.name = "QuitQuestion"
	question.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	question.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	question.custom_minimum_size = Vector2(150, 2.0 * row_height)
	var leave := _row("Quit", _quit_now)
	leave.name = "QuitConfirm"
	var stay := _row("Stay", stay_here)
	stay.name = "Stay"
	for b: Button in [leave, stay]:
		b.custom_minimum_size.y = row_height
		b.focus_exited.connect(queue_redraw)
	_confirm_buttons = [leave, stay]
	for b in _buttons:
		b.visible = false
	_confirm = [question, leave, stay]
	for c: Control in _confirm:
		_box.add_child(c)
	_ring(_confirm_buttons)
	for b: Button in _confirm_buttons:
		b.focus_neighbor_left = b.get_path_to(b)
		b.focus_neighbor_right = b.get_path_to(b)
	stay.grab_focus()
	Sound.play(&"ui_confirm")
	queue_redraw()

## Stay: back to the rows, the focus on Quit.
func stay_here() -> void:
	if not asking():
		return
	_end_asking()
	_buttons[-1].grab_focus()
	Sound.play(&"ui_cancel")

## Puts the four rows back (on Stay, and when the pause ends while Quit asks).
func _end_asking() -> void:
	if not asking():
		return
	for c: Control in _confirm:
		c.visible = false
		c.queue_free()
	_confirm.clear()
	_confirm_buttons.clear()
	for b in _buttons:
		b.visible = true
	queue_redraw()

## The Quit row: asks first (`ask_quit`).
func _quit() -> void:
	ask_quit()

## Quit, confirmed.
func _quit_now() -> void:
	# through the game, so the save holds the hearts as they are now (game.gd autosave)
	if get_tree().get_nodes_in_group("game").is_empty():
		SaveGame.save()
	else:
		get_tree().call_group("game", "autosave")
	get_tree().quit()
