extends PanelContainer
## The dialogue box, in the HUD's pixel font on its wood panel (ui/ui_style.gd): listens to Dialogue.opened, shows one line at a time with a short type-on
## (instant under reduced motion), advances on E / Enter / gamepad A or Y or a tap on the box, and
## emits Dialogue.closed after the last line. Space and left click stay free for roll and attack.

const CHARS_PER_SEC := 60.0

var _lines := PackedStringArray()
var _i := 0
var _shown := 0.0
var _opened_frame := -1
var _held_until := -1                ## the last frame the pause menu still owns the keys
var _name := Label.new()
var _text := Label.new()

func _ready() -> void:
	add_to_group("dialogue_box")
	visible = false
	anchor_left = 0.5
	anchor_right = 0.5
	anchor_top = 1.0
	anchor_bottom = 1.0
	offset_left = -300
	offset_right = 300
	offset_top = -128
	offset_bottom = -44
	add_theme_stylebox_override("panel", UiStyle.panel(6))   # the HUD's wood panel and pixel font
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 3)
	add_child(box)
	UiStyle.style_label(_name, UiStyle.TITLE)
	UiStyle.style_label(_text)
	_text.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_text.custom_minimum_size = Vector2(570, UiStyle.LINE * 3)
	box.add_child(_name)
	box.add_child(_text)
	Dialogue.opened.connect(_open)

func _open(speaker: String, lines: PackedStringArray) -> void:
	_lines = lines
	_i = 0
	_name.text = speaker
	_show_line()
	visible = true
	_opened_frame = Engine.get_process_frames()  # the E that opened the box must not also skip its first line

## The line on the box right now ("" when it is closed), for the play driver and the tests.
func shown_line() -> String:
	return _text.text if visible else ""

func _show_line() -> void:
	_text.text = _lines[_i]
	_shown = float(_text.text.length()) if SaveGame.setting("reduced_motion", false) else 0.0
	_text.visible_characters = int(_shown)

func _process(delta: float) -> void:
	if not visible:
		return
	# This box keeps running under the pause menu (it is drawn there too), but the menu owns the keys:
	# Enter on Resume must not also turn the page, on that frame or the next.
	if get_tree().paused:
		_held_until = Engine.get_process_frames() + 1
		return
	_shown = minf(_shown + CHARS_PER_SEC * delta, _text.text.length())
	_text.visible_characters = int(_shown)
	if Input.is_action_just_pressed("ui_advance") and Engine.get_process_frames() != _opened_frame \
			and Engine.get_process_frames() > _held_until:
		advance()

func _gui_input(event: InputEvent) -> void:
	if get_tree().paused:
		return
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		advance()
		accept_event()

## Finishes the current line, or moves to the next, or closes after the last.
func advance() -> void:
	if _shown < _text.text.length():
		_shown = _text.text.length()
		return
	_i += 1
	if _i < _lines.size():
		_show_line()
	else:
		visible = false
		Dialogue.closed.emit()
