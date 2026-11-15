class_name ControlsPanel
extends PanelContainer
## The controls, on a panel of their own beside the pause menu (ui/pause_menu.gd shows it while the game
## is paused). Every binding is read from the input map as it is at that moment (core/inputs.gd
## registers it; a later remap edits the same actions), so the panel cannot drift from the keys.
## It lists only what the game reads today. An action that is bound but that nothing reads yet (ranged,
## special, familiar, tonic, map, gear) is left out until it is built: test/test_ui.gd holds BUILT
## against the code. Text only: no buttons, no focus, nothing to press.

## What the game reads, in the order shown: the row's name and the actions it stands for.
const BUILT := [
	{"label": "Move", "actions": ["move_up", "move_left", "move_down", "move_right"]},
	{"label": "Shoot", "actions": ["attack"]},
	{"label": "Roll", "actions": ["dodge"]},
	{"label": "Talk, use", "actions": ["interact"]},
	{"label": "Next line", "actions": ["ui_advance"]},
	{"label": "Pause", "actions": ["menu"]},
]
## Aiming is no action in the input map: the bow follows the mouse pointer, or the right stick
## (actors/player.gd, core/inputs.gd stick_aim). Shown after Move.
const AIM := {"label": "Aim", "keys": "Mouse", "pad": "Right stick"}
const ARROWS := ["Up", "Left", "Down", "Right"]
const PAD_BUTTONS := {
	JOY_BUTTON_A: "A", JOY_BUTTON_B: "B", JOY_BUTTON_X: "X", JOY_BUTTON_Y: "Y",
	JOY_BUTTON_BACK: "Back", JOY_BUTTON_START: "Start",
	JOY_BUTTON_LEFT_SHOULDER: "LB", JOY_BUTTON_RIGHT_SHOULDER: "RB",
}
const PAD_AXES := {
	JOY_AXIS_LEFT_X: "Left stick", JOY_AXIS_LEFT_Y: "Left stick",
	JOY_AXIS_RIGHT_X: "Right stick", JOY_AXIS_RIGHT_Y: "Right stick",
	JOY_AXIS_TRIGGER_LEFT: "LT", JOY_AXIS_TRIGGER_RIGHT: "RT",
}
const MOUSE_BUTTONS := {MOUSE_BUTTON_LEFT: "Left click", MOUSE_BUTTON_RIGHT: "Right click", MOUSE_BUTTON_MIDDLE: "Middle click"}

var _grid: GridContainer
var _shown := []

func _ready() -> void:
	process_mode = Node.PROCESS_MODE_ALWAYS
	mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_theme_stylebox_override("panel", UiStyle.panel(6))
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 4)
	box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(box)
	var title := UiStyle.label("Controls", UiStyle.TITLE)
	title.custom_minimum_size.y = 16
	box.add_child(title)
	_grid = GridContainer.new()
	_grid.columns = 3
	_grid.add_theme_constant_override("h_separation", 10)
	_grid.add_theme_constant_override("v_separation", 3)
	_grid.mouse_filter = Control.MOUSE_FILTER_IGNORE
	box.add_child(_grid)
	refresh()

## Reads the input map again (the pause menu calls this each time it opens).
func refresh() -> void:
	var now := rows()
	if now == _shown or _grid == null:
		return
	_shown = now
	for c in _grid.get_children():
		_grid.remove_child(c)
		c.queue_free()
	for cell: String in ["", "Keyboard", "Gamepad"]:
		_grid.add_child(UiStyle.label(cell, UiStyle.DIM))
	for row: Dictionary in now:
		_grid.add_child(UiStyle.label(row.label, UiStyle.DIM))
		_grid.add_child(UiStyle.label(row.keys))
		_grid.add_child(UiStyle.label(row.pad))
	reset_size()

## The panel as text, a row a line (the tests and the play driver read the screen through this).
func shown_text() -> String:
	return "\n".join(_shown.map(func(r: Dictionary) -> String: return "%s: %s | %s" % [r.label, r.keys, r.pad]))

## The rows to show: [{label, keys, pad}], from the input map as it is now.
static func rows() -> Array:
	var out := []
	for entry: Dictionary in BUILT:
		var keys := []      # one list of names for each action of the row
		var pads := []
		for action: String in entry.actions:
			var k := []
			var p := []
			if InputMap.has_action(action):
				for e: InputEvent in InputMap.action_get_events(action):
					var n := name_of(e)
					if n == "":
						continue
					if e is InputEventJoypadButton or e is InputEventJoypadMotion:
						p.append(n)
					else:
						k.append(n)
			keys.append(k)
			pads.append(p)
		out.append({"label": entry.label, "keys": _join(keys), "pad": _join(pads)})
		if entry.label == "Move":
			out.append(AIM.duplicate())
	return out

## A binding's name as a player would say it: "W", "Space", "Left click", "Start", "Left stick".
static func name_of(e: InputEvent) -> String:
	if e is InputEventKey:
		var code: int = e.physical_keycode if e.physical_keycode != KEY_NONE else e.keycode
		return OS.get_keycode_string(code as Key)
	if e is InputEventMouseButton:
		return String(MOUSE_BUTTONS.get(e.button_index, "Mouse %d" % e.button_index))
	if e is InputEventJoypadButton:
		return String(PAD_BUTTONS.get(e.button_index, "Button %d" % e.button_index))
	if e is InputEventJoypadMotion:
		return String(PAD_AXES.get(e.axis, "Axis %d" % e.axis))
	return ""

## One row's bindings on a line. The first binding of each of the row's actions makes one group, the
## second the next: "W A S D / Arrows" for the four directions, "E / Enter" for one action with two keys.
static func _join(per_action: Array) -> String:
	var groups := []
	var depth := 0
	for names: Array in per_action:
		depth = maxi(depth, names.size())
	for i in depth:
		var group := []
		for names: Array in per_action:
			if i < names.size() and not group.has(names[i]):
				group.append(names[i])
		var arrows := group.size() == ARROWS.size()
		for a: String in ARROWS:
			arrows = arrows and group.has(a)
		var text := "Arrows" if arrows else " ".join(group)
		if text != "" and not groups.has(text):
			groups.append(text)
	return " / ".join(groups) if not groups.is_empty() else "-"
