class_name RaidScreen
extends Control
## The raid's prepare screen (game-design.md 7.6, step 1; docs/vision/vertical-slice.md beat 8). It is the
## announcement too: it opens when Raids asks (core/raids.gd prepare_requested), shows what is coming and
## down which road, and the pads with what stands on them, every pad filled from the start (Hale's hurdle
## barricade), so "Ring the bell" starts the night with no other tap. A tap on a pad cycles what stands
## there through the kinds the player has, then empty. "Not tonight" puts the raid off while postponements
## are left. There is nothing to buy and no timer: the screen waits, and the player stands still behind it.
##
## Touch first: every button is at least UiStyle.TOUCH texels (44 screen px at 2x), and taller where the
## window's scale needs it for 44 logical points (`fit_screen`, as the pause menu). Keyboard and gamepad
## move the focus; the mouse and touch tap. The lane map is a placeholder diagram in the HUD's colours.

signal closed

const MIN_TOUCH_POINTS := 44.0
const MAP := Vector2(300, 64)
const ROAD := Color("#b0a080")         ## the blockout's route colour
const ROAD_EDGE := Color("#885c4b")
const LAMP := Color("#f5d49c")
const POST := Color("#5a4632")
const WOOD := Color("#806850")

var player: Node = null
var _title := UiStyle.label("", UiStyle.TITLE)
var _sub := UiStyle.label("", UiStyle.DIM)
var _text := UiStyle.label()
var _map := Control.new()
var _pads_line := UiStyle.label("", UiStyle.TEXT)
var _hint := UiStyle.label("Tap a pad to change what stands on it.", UiStyle.DIM)
var _ring: Button
var _later: Button
var _pad_buttons: Dictionary = {}      ## pad id -> Button
var _pad_x: Dictionary = {}            ## pad id -> x on the map
var _dim: ColorRect
var _panel: PanelContainer
var _row := float(UiStyle.TOUCH)

func _ready() -> void:
	add_to_group("raid_screen")
	add_to_group(&"pause_screen_layout")
	visible = false
	# the whole art grid: clicks on the world do nothing while the screen is up; the panel sits in the middle
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	mouse_filter = Control.MOUSE_FILTER_STOP
	_dim = ColorRect.new()
	_dim.color = Color(UiStyle.INK, 0.45)
	_dim.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_dim.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_dim)
	_panel = PanelContainer.new()
	_panel.name = "Panel"
	_panel.mouse_filter = Control.MOUSE_FILTER_STOP
	_panel.add_theme_stylebox_override("panel", UiStyle.panel(8))
	add_child(_panel)
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 4)
	_panel.add_child(box)
	_title.add_theme_font_size_override("font_size", UiStyle.SIZE * 2)
	for l: Label in [_title, _sub, _text, _pads_line, _hint]:
		l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_text.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_text.custom_minimum_size.x = MAP.x
	box.add_child(_title)
	box.add_child(_sub)
	box.add_child(_text)
	_map.custom_minimum_size = MAP
	_map.mouse_filter = Control.MOUSE_FILTER_PASS
	_map.draw.connect(_draw_map)
	box.add_child(_map)
	box.add_child(_pads_line)
	box.add_child(_hint)
	var row := HBoxContainer.new()
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	row.add_theme_constant_override("separation", 12)
	box.add_child(row)
	_ring = _button("Ring the bell", _on_ring)
	_ring.name = "RingTheBell"
	row.add_child(_ring)
	_later = _button("Not tonight", _on_later)
	_later.name = "NotTonight"
	row.add_child(_later)
	_panel.grow_horizontal = Control.GROW_DIRECTION_BOTH
	_panel.grow_vertical = Control.GROW_DIRECTION_BOTH
	_panel.set_anchors_and_offsets_preset(Control.PRESET_CENTER, Control.PRESET_MODE_MINSIZE)
	Raids.changed.connect(func(st: String) -> void:
		if visible and st != "announced":
			close())

func _button(text: String, action: Callable) -> Button:
	var b := Button.new()
	b.text = text
	b.add_theme_font_override("font", UiStyle.font())
	b.add_theme_font_size_override("font_size", UiStyle.SIZE)
	b.add_theme_color_override("font_color", UiStyle.TEXT)
	for st in ["font_hover_color", "font_focus_color", "font_pressed_color", "font_hover_pressed_color"]:
		b.add_theme_color_override(st, UiStyle.TITLE)
	for st in ["normal", "hover", "pressed", "focus", "hover_pressed", "disabled"]:
		var s := UiStyle.key_cap()
		s.content_margin_left = 8
		s.content_margin_right = 8
		b.add_theme_stylebox_override(st, s)
	b.custom_minimum_size = Vector2(maxf(UiStyle.TOUCH, 60.0), _row)
	b.pressed.connect(action)
	b.mouse_entered.connect(b.grab_focus)
	return b

## Opens on Raids' word, while the raid waits on the screen.
func open() -> void:
	if Raids.state() != "announced":
		return
	_fit_from_screen()
	_build_pads()
	_refresh()
	visible = true
	_panel.reset_size()
	_panel.set_anchors_and_offsets_preset(Control.PRESET_CENTER, Control.PRESET_MODE_MINSIZE)
	if player != null and "input_enabled" in player:
		player.set("input_enabled", false)
	_ring.grab_focus.call_deferred()

func close() -> void:
	if not visible:
		return
	visible = false
	var f := get_viewport().gui_get_focus_owner() if is_inside_tree() else null
	if f != null and is_ancestor_of(f):
		f.release_focus()
	if player != null and is_instance_valid(player) and "input_enabled" in player:
		player.set("input_enabled", true)
	closed.emit()

func is_open() -> bool:
	return visible

func _on_ring() -> void:
	if Raids.ring():
		close()

func _on_later() -> void:
	if Raids.postpone():
		Sound.play(&"ui_cancel")
		close()

# --- contents ---------------------------------------------------------------------------------
func _refresh() -> void:
	var def := Raids.current()
	_title.text = String(def.get("title", ""))
	var forced := Raids.postpones_left() <= 0
	_sub.text = "The shardstruck gather on the halt road, drawn by the lantern"
	_text.text = "A horn from the halt road. %s%s Ring the bell when you are ready, then hold the lantern through %d waves." % [
		"They will not wait another night. " if forced and Raids.postponed() > 0 else "", _pads_sentence(def), (def.get("waves", []) as Array).size()]
	_later.visible = not forced
	_later.text = "Not tonight (%d left)" % Raids.postpones_left()
	var names := []
	var pads: Array = Raids.pads(def)
	for i in pads.size():
		var id := String(pads[i].id)
		var kind := Raids.pad_kind(id, def)
		names.append("%d: %s" % [i + 1, String(def.get("kinds", {}).get(kind, {}).get("name", "empty")) if kind != "" else "empty"])
		if _pad_buttons.has(id):
			(_pad_buttons[id] as Button).tooltip_text = String(pads[i].why)
	_pads_line.text = "   ".join(names)
	_hint.visible = Raids.kinds_owned(def).size() > 0
	_map.queue_redraw()

## What stands on the pads, from the layout as it is now ("Hale's hurdles stand on both pads.", "Pad 2 is
## empty.", ...).
static func _pads_sentence(def: Dictionary) -> String:
	var pads: Array = Raids.pads(def)
	var empty := []
	for i in pads.size():
		if Raids.pad_kind(String(pads[i].id), def) == "":
			empty.append(i + 1)
	if empty.is_empty():
		return "Hale's hurdles stand on %s." % ("both pads" if pads.size() == 2 else "every pad")
	if empty.size() == pads.size():
		return "%s empty: nothing stands in their way." % ("Both pads are" if pads.size() == 2 else "Every pad is")
	return "Hale's hurdles stand on the road; pad %s %s empty." % [" and ".join(empty.map(func(n: int) -> String: return str(n))), "is" if empty.size() == 1 else "are"]

func _build_pads() -> void:
	for b in _pad_buttons.values():
		(b as Node).queue_free()
	_pad_buttons.clear()
	_pad_x.clear()
	var def := Raids.current()
	var lane := Raids.lane(def)
	var length := 0.0
	for i in range(lane.size() - 1):
		length += lane[i].distance_to(lane[i + 1])
	for pad: Dictionary in Raids.pads(def):
		var s := _along(lane, pad.at as Vector2)
		var x := 24.0 + (MAP.x - 64.0) * (s / maxf(length, 1.0))
		_pad_x[pad.id] = x
		var b := _button("", _on_pad.bind(String(pad.id)))
		b.name = "Pad_" + String(pad.id)
		var frame := StyleBoxFlat.new()
		frame.bg_color = Color(0, 0, 0, 0)
		frame.border_color = UiStyle.DIM
		frame.set_border_width_all(1)
		var lit := frame.duplicate() as StyleBoxFlat
		lit.border_color = UiStyle.TITLE
		for st in ["normal", "disabled"]:
			b.add_theme_stylebox_override(st, frame)
		for st in ["hover", "pressed", "focus", "hover_pressed"]:
			b.add_theme_stylebox_override(st, lit)
		b.alignment = HORIZONTAL_ALIGNMENT_CENTER
		b.vertical_icon_alignment = VERTICAL_ALIGNMENT_BOTTOM
		b.custom_minimum_size = Vector2(_row, _row)
		b.size = b.custom_minimum_size
		b.position = Vector2(x - _row / 2.0, MAP.y / 2.0 - _row / 2.0)
		_map.add_child(b)
		_pad_buttons[pad.id] = b

static func _along(lane: PackedVector2Array, at: Vector2) -> float:
	var best := INF
	var out := 0.0
	var cum := 0.0
	for i in range(lane.size() - 1):
		var ab := lane[i + 1] - lane[i]
		var t := clampf((at - lane[i]).dot(ab) / maxf(ab.length_squared(), 0.0001), 0.0, 1.0)
		var d := at.distance_to(lane[i] + ab * t)
		if d < best:
			best = d
			out = cum + ab.length() * t
		cum += ab.length()
	return out

func _on_pad(id: String) -> void:
	Raids.cycle_pad(id)
	Sound.play(&"ui_confirm")
	_refresh()

## The lane as a diagram: the road from the halt on the left to the lantern on the right, a hurdle drawn
## on each pad that has one.
func _draw_map() -> void:
	var y := MAP.y / 2.0
	_map.draw_rect(Rect2(Vector2(8, y - 6), Vector2(MAP.x - 40, 12)), ROAD_EDGE)
	_map.draw_rect(Rect2(Vector2(8, y - 4), Vector2(MAP.x - 40, 8)), ROAD)
	var font := UiStyle.font()
	_map.draw_string(font, Vector2(8, y - 14), "Halt road", HORIZONTAL_ALIGNMENT_LEFT, -1, UiStyle.SIZE, UiStyle.DIM)
	# the lantern: a post and its lit cap
	var lx := MAP.x - 24.0
	_map.draw_rect(Rect2(Vector2(lx - 2, y - 14), Vector2(4, 22)), POST)
	_map.draw_rect(Rect2(Vector2(lx - 6, y - 22), Vector2(12, 9)), LAMP)
	_map.draw_string(font, Vector2(lx - 26, y + 24), "Lantern", HORIZONTAL_ALIGNMENT_LEFT, -1, UiStyle.SIZE, UiStyle.DIM)
	var def := Raids.current()
	var n := 0
	for id: String in _pad_x:
		var x: float = _pad_x[id]
		n += 1
		_map.draw_string(font, Vector2(x - 3, y + 24), str(n), HORIZONTAL_ALIGNMENT_LEFT, -1, UiStyle.SIZE, UiStyle.DIM)
		if Raids.pad_kind(id, def) != "":
			for k in 2:
				_map.draw_rect(Rect2(Vector2(x - 7 + k * 11, y - 9), Vector2(3, 16)), POST)
			_map.draw_rect(Rect2(Vector2(x - 8, y - 6), Vector2(16, 3)), WOOD)
			_map.draw_rect(Rect2(Vector2(x - 8, y), Vector2(16, 3)), WOOD)

# --- touch ------------------------------------------------------------------------------------
## As the pause menu's (ui/pause_menu.gd): rows tall enough for 44 logical points at this window's scale.
func fit_screen(window_pixels: Vector2, art_scale: float, _offset: Vector2, ratio: float, _safe: Rect2) -> bool:
	if not is_finite(art_scale) or art_scale <= 0.0 or not is_finite(ratio) or ratio <= 0.0:
		return false
	if not window_pixels.is_finite() or window_pixels.x <= 0.0 or window_pixels.y <= 0.0:
		return false
	_row = maxf(UiStyle.TOUCH, ceilf(MIN_TOUCH_POINTS * ratio / art_scale))
	for b: Button in [_ring, _later]:
		if b != null:
			b.custom_minimum_size.y = _row
	return true

func _fit_from_screen() -> void:
	var main := get_tree().current_scene if is_inside_tree() else null
	if main == null or main.get("scale_k") == null:
		return
	var ratio := DisplayServer.screen_get_scale()
	if not is_finite(ratio) or ratio <= 0.0:
		ratio = 1.0
	fit_screen(Vector2(get_window().size), float(main.get("scale_k")), Vector2.ZERO, ratio, Rect2())

## Every button on the screen, for the touch audit and the tests.
func targets() -> Array[Button]:
	var out: Array[Button] = [_ring, _later]
	for b in _pad_buttons.values():
		out.append(b as Button)
	return out
