extends Node
## The input map, registered in code so it stays diffable (game-design.md 11.5): keyboard and mouse
## first, gamepad equivalents second. Remapping later edits these same actions at runtime.
## Also tracks which device was used last, so prompts can show the matching glyph.

signal device_changed(device: StringName)

var last_device: StringName = &"keyboard"

func _enter_tree() -> void:
	_axis(&"move_left", [KEY_A, KEY_LEFT], JOY_AXIS_LEFT_X, -1.0)
	_axis(&"move_right", [KEY_D, KEY_RIGHT], JOY_AXIS_LEFT_X, 1.0)
	_axis(&"move_up", [KEY_W, KEY_UP], JOY_AXIS_LEFT_Y, -1.0)
	_axis(&"move_down", [KEY_S, KEY_DOWN], JOY_AXIS_LEFT_Y, 1.0)
	_action(&"attack", [], [JOY_BUTTON_X], [MOUSE_BUTTON_LEFT])
	_action(&"ranged", [], [], [MOUSE_BUTTON_RIGHT], JOY_AXIS_TRIGGER_RIGHT)
	_action(&"dodge", [KEY_SPACE], [JOY_BUTTON_A])
	_action(&"special", [KEY_Q], [JOY_BUTTON_RIGHT_SHOULDER])
	_action(&"familiar", [KEY_F], [], [], JOY_AXIS_TRIGGER_LEFT)
	_action(&"tonic", [KEY_R], [JOY_BUTTON_LEFT_SHOULDER])
	_action(&"interact", [KEY_E], [JOY_BUTTON_Y])
	_action(&"menu", [KEY_ESCAPE], [JOY_BUTTON_START])
	_action(&"map", [KEY_M], [JOY_BUTTON_BACK])
	_action(&"gear", [KEY_TAB], [])
	# dialogue: advance with E, Enter or the gamepad's A/Y; never Space or click (dodge and attack)
	_action(&"ui_advance", [KEY_E, KEY_ENTER], [JOY_BUTTON_A, JOY_BUTTON_Y])

func _input(event: InputEvent) -> void:
	var dev := last_device
	if event is InputEventJoypadButton or (event is InputEventJoypadMotion and absf(event.axis_value) > 0.4):
		dev = &"gamepad"
	elif event is InputEventKey or event is InputEventMouseButton:
		dev = &"keyboard"
	if dev != last_device:
		last_device = dev
		device_changed.emit(dev)

## The right stick's aim, or zero when it rests.
func stick_aim() -> Vector2:
	var v := Vector2(Input.get_joy_axis(0, JOY_AXIS_RIGHT_X), Input.get_joy_axis(0, JOY_AXIS_RIGHT_Y))
	return v.normalized() if v.length() > 0.35 else Vector2.ZERO

func _ensure(action: StringName) -> void:
	if InputMap.has_action(action):
		InputMap.action_erase_events(action)
	else:
		InputMap.add_action(action, 0.3)

func _axis(action: StringName, keys: Array, axis: JoyAxis, dir: float) -> void:
	_ensure(action)
	_keys(action, keys)
	var j := InputEventJoypadMotion.new()
	j.axis = axis
	j.axis_value = dir
	InputMap.action_add_event(action, j)

func _action(action: StringName, keys: Array, buttons: Array, mouse: Array = [], trigger: int = -1) -> void:
	_ensure(action)
	_keys(action, keys)
	for b in buttons:
		var j := InputEventJoypadButton.new()
		j.button_index = b
		InputMap.action_add_event(action, j)
	for m in mouse:
		var mb := InputEventMouseButton.new()
		mb.button_index = m
		InputMap.action_add_event(action, mb)
	if trigger >= 0:
		var t := InputEventJoypadMotion.new()
		t.axis = trigger as JoyAxis
		t.axis_value = 1.0
		InputMap.action_add_event(action, t)

func _keys(action: StringName, keys: Array) -> void:
	for k in keys:
		var e := InputEventKey.new()
		e.physical_keycode = k
		InputMap.action_add_event(action, e)
