extends GdUnitTestSuite
## The interface (ui/): the pixel font draws without antialiasing or ligatures, the HUD's pictures sit on
## the art grid at their drawn sizes, and the pause menu follows the pause, sets reduced motion and the
## pixel scale in the save, and keeps every row at least 44 screen px tall at 2x.

func before_test() -> void:
	SaveGame.reset()

func after_test() -> void:
	get_tree().paused = false
	SaveGame.reset()

func test_pixel_font_is_crisp() -> void:
	var v := UiStyle.font() as FontVariation
	assert_object(v).is_not_null()
	var f := v.base_font as FontFile
	assert_int(f.antialiasing).is_equal(TextServer.FONT_ANTIALIASING_NONE)
	assert_int(f.hinting).is_equal(TextServer.HINTING_NONE)
	assert_int(f.subpixel_positioning).is_equal(TextServer.SUBPIXEL_POSITIONING_DISABLED)
	var liga := TextServerManager.get_primary_interface().name_to_tag("liga")
	assert_int(int(v.opentype_features.get(liga, 1))).is_equal(0)

func test_hud_pictures_on_the_grid() -> void:
	var sizes := {"heart_full": Vector2i(11, 10), "heart_empty": Vector2i(11, 10), "roll_full": Vector2i(9, 9),
		"roll_empty": Vector2i(9, 9), "glint": Vector2i(9, 11), "panel": Vector2i(12, 12), "key": Vector2i(9, 9)}
	for n in sizes:
		var t: Texture2D = load("res://ui/art/%s.png" % n)
		assert_object(t).is_not_null()
		assert_vector(Vector2(t.get_size())).is_equal(Vector2(sizes[n]))

func test_pause_menu_follows_the_pause_and_sets_settings() -> void:
	var menu: PanelContainer = auto_free(preload("res://ui/pause_menu.gd").new())
	add_child(menu)
	await await_idle_frame()
	assert_bool(menu.visible).is_false()
	get_tree().paused = true
	await await_idle_frame()
	assert_bool(menu.visible).is_true()
	var buttons := menu.find_children("*", "Button", true, false)
	assert_int(buttons.size()).is_equal(4)
	for b: Button in buttons:
		assert_float(b.size.y).is_greater_equal(UiStyle.TOUCH)
	(buttons[1] as Button).pressed.emit()
	assert_bool(SaveGame.setting("reduced_motion", false)).is_true()
	(buttons[2] as Button).pressed.emit()
	assert_str(str(SaveGame.setting("pixel_scale", "fill"))).is_equal("whole")
	(buttons[0] as Button).pressed.emit()
	assert_bool(get_tree().paused).is_false()
	await await_idle_frame()
	assert_bool(menu.visible).is_false()

# --- pressing a row: the mouse, a touch, a gamepad (15 Nov) ---------------------------------------
## The HUD as the game has it (ui/hud.gd adds the pause menu and the Sound panel), paused.
func _paused_hud() -> Control:
	var host: Control = auto_free(Control.new())
	add_child(host)
	var hud: Control = load("res://ui/hud.gd").new()
	host.add_child(hud)
	get_tree().paused = true
	for i in 4:
		await get_tree().process_frame
	return host

func _row(host: Node, text: String) -> Button:
	for b: Button in host.find_children("*", "Button", true, false):
		if b.text.begins_with(text) and b.is_visible_in_tree():
			return b
	return null

## Brings `row` under the middle of the test runner's window: that window is 64 pixels square, and a
## press outside it finds nothing.
func _bring(host: Control, row: Button) -> Vector2:
	var middle := get_viewport().get_visible_rect().get_center()
	host.position += middle - row.get_global_rect().get_center()
	for i in 3:
		await get_tree().process_frame
	assert_bool(row.get_global_rect().has_point(middle)).is_true()
	return middle

func _dim_of(host: Node) -> ColorRect:
	for c: ColorRect in host.find_children("*", "ColorRect", true, false):
		if c.mouse_filter == Control.MOUSE_FILTER_STOP:
			return c
	return null

func _click(at: Vector2) -> void:
	for down: bool in [true, false]:
		var e := InputEventMouseButton.new()
		e.button_index = MOUSE_BUTTON_LEFT
		e.pressed = down
		e.position = at
		e.global_position = at
		get_viewport().push_input(e, true)

## A mouse click with the dim there. On main no click reached a row: the dim was a top-level control that
## stops the mouse, and the engine asks top-level controls first (a click on Resume left the game paused).
func test_a_mouse_click_presses_a_pause_row_and_a_sound_row_with_the_dim_behind_them() -> void:
	var host := await _paused_hud()
	var dim := _dim_of(host)
	assert_object(dim).is_not_null()                 # the dim is there and stops the mouse: the world takes no click
	assert_bool(dim.is_visible_in_tree()).is_true()
	for spec: Array in [["Reduced motion", "reduced_motion", false], ["Gentle sound", "gentle_sound", false],
			["Ambience", "ambience", true]]:
		var row := _row(host, spec[0])
		assert_object(row).is_not_null()
		var at := await _bring(host, row)
		assert_bool(dim.get_global_rect().has_point(at)).override_failure_message("the dim is not under %s" % spec[0]).is_true()
		_click(at)
		assert_bool(bool(SaveGame.setting(spec[1], spec[2]))).override_failure_message(
			"a click on '%s' did nothing" % spec[0]).is_equal(not spec[2])
	# and Resume resumes
	var resume := _row(host, "Resume")
	_click(await _bring(host, resume))
	assert_bool(get_tree().paused).override_failure_message("a click on Resume left the game paused").is_false()

## A finger: a screen touch given to the engine as a phone gives it (Input.parse_input_event), which makes
## the mouse press of it that a Button answers (the project setting for that is on).
func test_a_screen_touch_presses_a_pause_row_and_a_sound_row_with_the_dim_behind_them() -> void:
	assert_bool(bool(ProjectSettings.get_setting("input_devices/pointing/emulate_mouse_from_touch"))).is_true()
	var host := await _paused_hud()
	assert_object(_dim_of(host)).is_not_null()
	for spec: Array in [["Reduced motion", "reduced_motion", false], ["Sound effects", "sound_effects", true]]:
		var row := _row(host, spec[0])
		var at := await _bring(host, row)
		for down: bool in [true, false]:
			var t := InputEventScreenTouch.new()
			t.index = 0
			t.pressed = down
			t.position = at
			Input.parse_input_event(t)
			for i in 3:
				await get_tree().process_frame
		assert_bool(bool(SaveGame.setting(spec[1], spec[2]))).override_failure_message(
			"a tap on '%s' did nothing" % spec[0]).is_equal(not spec[2])

func _pad_press(button: JoyButton, device := 0) -> void:
	for down: bool in [true, false]:
		var e := InputEventJoypadButton.new()
		e.button_index = button
		e.device = device
		e.pressed = down
		e.pressure = 1.0 if down else 0.0
		get_viewport().push_input(e, true)

func _has_pad_button(action: StringName, button: JoyButton) -> bool:
	for e: InputEvent in InputMap.action_get_events(action):
		if e is InputEventJoypadButton and e.button_index == button:
			return true
	return false

func _has_stick(action: StringName, axis: JoyAxis, dir: float) -> bool:
	for e: InputEvent in InputMap.action_get_events(action):
		if e is InputEventJoypadMotion and e.axis == axis and signf(e.axis_value) == dir:
			return true
	return false

## A gamepad. On main the d-pad and the stick moved the focus and no button pressed the row: the engine's
## ui_accept holds Enter and Space only. core/inputs.gd adds A.
func test_a_gamepad_moves_the_focus_and_its_a_button_presses_the_focused_row() -> void:
	# the map: A accepts and the engine's keys are still there; Start pauses; the d-pad and the left stick move
	assert_bool(_has_pad_button(&"ui_accept", JOY_BUTTON_A)).override_failure_message("ui_accept has no pad button").is_true()
	var keys := []
	for e: InputEvent in InputMap.action_get_events(&"ui_accept"):
		if e is InputEventKey:
			keys.append(e.physical_keycode if e.physical_keycode != KEY_NONE else e.keycode)
	assert_array(keys).contains([KEY_ENTER, KEY_KP_ENTER, KEY_SPACE])
	assert_bool(_has_pad_button(&"menu", JOY_BUTTON_START)).is_true()
	for spec: Array in [[&"ui_up", JOY_BUTTON_DPAD_UP, JOY_AXIS_LEFT_Y, -1.0], [&"ui_down", JOY_BUTTON_DPAD_DOWN, JOY_AXIS_LEFT_Y, 1.0],
			[&"ui_left", JOY_BUTTON_DPAD_LEFT, JOY_AXIS_LEFT_X, -1.0], [&"ui_right", JOY_BUTTON_DPAD_RIGHT, JOY_AXIS_LEFT_X, 1.0]]:
		assert_bool(_has_pad_button(spec[0], spec[1])).override_failure_message("%s has no d-pad button" % spec[0]).is_true()
		assert_bool(_has_stick(spec[0], spec[2], spec[3])).override_failure_message("%s has no stick" % spec[0]).is_true()
	# the events: the menu opens on Resume; d-pad down, then A
	var host := await _paused_hud()
	var resume := _row(host, "Resume")
	var motion := _row(host, "Reduced motion")
	var scale := _row(host, "Pixel scale")
	assert_object(get_viewport().gui_get_focus_owner()).is_same(resume)
	_pad_press(JOY_BUTTON_DPAD_DOWN)
	assert_object(get_viewport().gui_get_focus_owner()).is_same(motion)
	_pad_press(JOY_BUTTON_A)
	assert_bool(bool(SaveGame.setting("reduced_motion", false))).override_failure_message("A did not press the focused row").is_true()
	assert_bool(get_tree().paused).is_true()
	# the left stick moves the focus too, and a second pad's A counts as the first's
	# (through Input, as a pad's does: for a stick the engine asks Input whether the action was just pressed)
	for value: float in [1.0, 0.0]:
		var stick := InputEventJoypadMotion.new()
		stick.axis = JOY_AXIS_LEFT_Y
		stick.axis_value = value
		Input.parse_input_event(stick)
		for i in 2:
			await get_tree().process_frame
	assert_object(get_viewport().gui_get_focus_owner()).is_same(scale)
	_pad_press(JOY_BUTTON_A, 1)
	assert_str(str(SaveGame.setting("pixel_scale", "fill"))).is_equal("whole")
	# across to the Sound panel and A there
	_pad_press(JOY_BUTTON_DPAD_RIGHT)
	var sound_row := get_viewport().gui_get_focus_owner() as Button
	assert_object(sound_row).is_not_null()
	assert_bool(sound_row.get_parent().get_parent() is SoundMenu).is_true()
	var was: bool = SaveGame.setting(sound_row.name)
	_pad_press(JOY_BUTTON_A)
	assert_bool(bool(SaveGame.setting(sound_row.name))).is_equal(not was)
	# A on Resume resumes
	resume.grab_focus()
	_pad_press(JOY_BUTTON_A)
	assert_bool(get_tree().paused).is_false()

# --- the controls beside the pause menu (15 Nov) ------------------------------------------------
## Every action the game's own code reads, found in the source: `Input.is_action...("x")`,
## `event.is_action...("x")` and the four names of `Input.get_vector`.
func _actions_read_by_the_game() -> Array:
	var found := {}
	var re := RegEx.new()
	re.compile("(?:is_action_just_pressed|is_action_pressed|is_action_just_released|get_action_strength)\\(\\s*&?\"([a-z_]+)\"")
	var vec := RegEx.new()
	vec.compile("get_vector\\(\\s*&?\"([a-z_]+)\",\\s*&?\"([a-z_]+)\",\\s*&?\"([a-z_]+)\",\\s*&?\"([a-z_]+)\"")
	var dirs := ["res://"]
	while not dirs.is_empty():
		var dir: String = dirs.pop_back()
		for sub in DirAccess.get_directories_at(dir):
			if not sub in ["addons", "test", "tools", ".godot", "reports"]:
				dirs.append(dir.path_join(sub))
		for f in DirAccess.get_files_at(dir):
			if f.ends_with(".gd"):
				var text := FileAccess.get_file_as_string(dir.path_join(f))
				for m in re.search_all(text):
					found[m.get_string(1)] = true
				for m in vec.search_all(text):
					for i in range(1, 5):
						found[m.get_string(i)] = true
	var out := found.keys()
	out.sort()
	return out

func test_the_controls_panel_lists_what_the_game_reads_and_nothing_unbuilt() -> void:
	var listed := []
	for entry: Dictionary in ControlsPanel.BUILT:
		listed.append_array(entry.actions)
	listed.sort()
	# the code is the list: an action somebody starts to read has to be added, one nobody reads comes out
	var read := _actions_read_by_the_game()
	assert_array(read).contains(["attack", "dodge", "interact", "menu", "move_left", "ui_advance"])
	assert_array(listed).is_equal(read)
	var text := "\n".join(ControlsPanel.rows().map(func(r: Dictionary) -> String: return "%s: %s | %s" % [r.label, r.keys, r.pad]))
	# bound in core/inputs.gd, read by nothing yet: neither the action's row nor its key shows
	for action: String in ["ranged", "special", "familiar", "tonic", "map", "gear"]:
		assert_bool(InputMap.has_action(action)).is_true()
		assert_bool(listed.has(action)).override_failure_message("%s is listed but nothing reads it" % action).is_false()
		for e: InputEvent in InputMap.action_get_events(action):
			var n := ControlsPanel.name_of(e)
			assert_bool(n in ["Q", "F", "R", "M", "Tab", "Right click", "RT", "LT", "RB", "LB", "Back"]).is_true()
			var whole := RegEx.new()      # the name as a whole word: "R" is not in "Roll"
			whole.compile("(^|[^A-Za-z])%s($|[^A-Za-z])" % n)
			assert_bool(whole.search(text) != null).override_failure_message("the controls show %s, which is bound to the unbuilt %s:\n%s" % [n, action, text]).is_false()

func test_the_controls_panel_shows_the_real_bindings_from_the_input_map() -> void:
	var rows := {}
	for r: Dictionary in ControlsPanel.rows():
		rows[r.label] = r
	assert_str(rows["Move"].keys).is_equal("W A S D / Arrows")
	assert_str(rows["Move"].pad).is_equal("Left stick")
	assert_str(rows["Aim"].keys).is_equal("Mouse")
	assert_str(rows["Aim"].pad).is_equal("Right stick")
	assert_str(rows["Shoot"].keys).is_equal("Left click")
	assert_str(rows["Shoot"].pad).is_equal("X")
	assert_str(rows["Roll"].keys).is_equal("Space")
	assert_str(rows["Roll"].pad).is_equal("A")
	assert_str(rows["Talk, use"].keys).is_equal("E")
	assert_str(rows["Talk, use"].pad).is_equal("Y")
	assert_str(rows["Next line"].keys).is_equal("E / Enter")
	assert_str(rows["Next line"].pad).is_equal("A / Y")
	assert_str(rows["Pause"].keys).is_equal("Escape")
	assert_str(rows["Pause"].pad).is_equal("Start")
	# every name comes from the map itself: rebind the roll and the row follows
	var kept := InputMap.action_get_events("dodge")
	InputMap.action_erase_events("dodge")
	var c := InputEventKey.new()
	c.physical_keycode = KEY_C
	InputMap.action_add_event("dodge", c)
	var roll := ""
	for r: Dictionary in ControlsPanel.rows():
		if r.label == "Roll":
			roll = "%s | %s" % [r.keys, r.pad]
	InputMap.action_erase_events("dodge")
	for e: InputEvent in kept:
		InputMap.action_add_event("dodge", e)
	assert_str(roll).is_equal("C | -")

func test_the_controls_stand_beside_the_pause_menu_and_add_no_row_to_it() -> void:
	var screen: Control = auto_free(Control.new())     # the art grid, as the HUD is in the game
	screen.size = UiStyle.GRID
	add_child(screen)
	var menu: PanelContainer = preload("res://ui/pause_menu.gd").new()
	screen.add_child(menu)
	await await_idle_frame()
	var controls := menu.get_node("Controls") as ControlsPanel
	assert_bool(controls.is_visible_in_tree()).is_false()
	get_tree().paused = true
	for i in 4:
		await get_tree().process_frame
	assert_bool(controls.is_visible_in_tree()).is_true()
	assert_int(menu.find_children("*", "Button", true, false).size()).is_equal(4)
	assert_int(controls.find_children("*", "Button", true, false).size()).is_equal(0)
	assert_str(controls.shown_text()).contains("Roll: Space | A")
	assert_str(controls.shown_text()).contains("Pause: Escape | Start")
	var own := menu.get_global_rect()
	var beside := controls.get_global_rect()
	assert_bool(own.intersects(beside)).override_failure_message("%s over %s" % [beside, own]).is_false()
	assert_bool(Rect2(Vector2.ZERO, UiStyle.GRID).encloses(beside)).override_failure_message("%s leaves the art grid" % beside).is_true()
	assert_float(beside.position.y).is_equal(own.position.y)
	# nothing on it takes a tap or the focus: the menu's four rows stay the only targets
	assert_int(controls.mouse_filter).is_equal(Control.MOUSE_FILTER_IGNORE)
	for l: Node in controls.find_children("*", "Label", true, false):
		assert_int((l as Label).focus_mode).is_equal(Control.FOCUS_NONE)
	get_tree().paused = false
	await await_idle_frame()
	assert_bool(controls.is_visible_in_tree()).is_false()

## The audit of #491: on a phone held upright (402 x 874) with pixel scale "whole" the window shows only
## the grid's middle (x 279 to 681), and the panel, kept inside the whole grid, stood at x 571 to 807,
## cut off. It is placed inside what the window shows and clear of the menu and of the Sound panel at
## the menu's right (ui/sound_menu.gd): at the menu's left, else past the Sound panel, else below or
## above. Where no such place exists (480 x 270 at "whole") it is not shown, rather than laid over
## something. With and without the Sound panel.
## The menu and the Sound panel themselves (15 Nov): on main the Sound panel stood at the menu's right
## wherever that was, so at 402 x 874, 375 x 667 and 480 x 270 with "whole" it was cut off at the window's
## edge. The two stay inside what the window shows at every size here, never one over the other, and
## every row of both lies inside it. 320 x 720 "whole" is narrower than the two side by side: the Sound
## panel stands below the menu there, and the focus runs through both in one ring.
func test_the_controls_panel_stays_inside_what_the_window_shows_and_clear_of_the_other_panels() -> void:
	const Screen := preload("res://main/pixel_screen.gd")
	var shown_somewhere := 0
	for with_sound: bool in [true, false]:
		for spec: Array in [[402, 874, "whole"], [402, 874, "fill"], [480, 270, "whole"], [480, 270, "fill"], [375, 667, "whole"],
				[1920, 1080, "fill"], [960, 540, "whole"], [874, 402, "fill"], [874, 402, "whole"], [2622, 1206, "fill"],
					[320, 720, "whole"]]:
			var screen: Control = auto_free(Control.new())
			screen.size = UiStyle.GRID
			add_child(screen)
			var menu: PanelContainer = preload("res://ui/pause_menu.gd").new()
			screen.add_child(menu)
			var sound: SoundMenu = null
			if with_sound:
				sound = SoundMenu.new()
				sound.beside = menu
				screen.add_child(sound)
			var window := Vector2(spec[0], spec[1])
			var k: float = Screen.choose_scale(window, spec[2])
			var offset := ((window - Screen.ART * k) / 2.0).floor()
			get_tree().call_group(&"pause_screen_layout", &"fit_screen", window, k, offset, 1.0, Rect2(Vector2.ZERO, window))
			get_tree().paused = true
			for i in 6:
				await get_tree().process_frame
			var controls := menu.get_node("Controls") as ControlsPanel
			var seen: Rect2 = menu.visible_grid()
			var own := menu.get_global_rect()
			var beside := controls.get_global_rect()
			var what := "%s %s, sound %s: controls %s, menu %s, sound %s, the window shows %s" % [window, spec[2], with_sound, beside,
				own, sound.get_global_rect() if sound != null else Rect2(), seen]
			# the menu and the Sound panel: inside what the window shows, apart, every row inside too
			assert_bool(seen.grow(0.5).encloses(own)).override_failure_message("the menu is cut off. " + what).is_true()
			for b: Button in menu.find_children("*", "Button", true, false):
				assert_bool(seen.grow(0.5).encloses(b.get_global_rect())).override_failure_message("a menu row is cut off. " + what).is_true()
			if sound != null:
				var beside_it := sound.get_global_rect()
				assert_bool(sound.is_visible_in_tree()).override_failure_message(what).is_true()
				assert_bool(seen.grow(0.5).encloses(beside_it)).override_failure_message("the Sound panel is cut off. " + what).is_true()
				assert_bool(own.intersects(beside_it)).override_failure_message("the Sound panel is over the menu. " + what).is_false()
				var rows := sound.find_children("*", "Button", true, false)
				var menu_rows := menu.find_children("*", "Button", true, false)
				assert_int(rows.size()).is_equal(3)
				for b: Button in rows:
					assert_bool(seen.grow(0.5).encloses(b.get_global_rect())).override_failure_message("a Sound row is cut off. " + what).is_true()
				if window == Vector2(320, 720):
					# one above the other, centred on the menu, and one focus ring through both
					assert_float(beside_it.position.y).is_equal(own.end.y + SoundMenu.GAP)
					assert_float(beside_it.get_center().x).is_equal(own.get_center().x)
					assert_object((menu_rows[-1] as Button).find_valid_focus_neighbor(SIDE_BOTTOM)).is_same(rows[0])
					assert_object((rows[0] as Button).find_valid_focus_neighbor(SIDE_TOP)).is_same(menu_rows[-1])
					assert_object((rows[-1] as Button).find_valid_focus_neighbor(SIDE_BOTTOM)).is_same(menu_rows[0])
					assert_object((menu_rows[0] as Button).find_valid_focus_neighbor(SIDE_TOP)).is_same(rows[-1])
				else:
					# side by side, tops level, each panel wrapping on its own, sideways crossing over
					assert_float(beside_it.position.y).is_equal(own.position.y)
					assert_float(beside_it.position.x).is_equal(own.end.x + SoundMenu.GAP)
					assert_object((menu_rows[-1] as Button).find_valid_focus_neighbor(SIDE_BOTTOM)).is_same(menu_rows[0])
					assert_object((rows[-1] as Button).find_valid_focus_neighbor(SIDE_BOTTOM)).is_same(rows[0])
					assert_bool(rows.has((menu_rows[1] as Button).find_valid_focus_neighbor(SIDE_RIGHT))).override_failure_message(what).is_true()
			if controls.is_visible_in_tree():
				shown_somewhere += 1
				assert_bool(seen.grow(0.5).encloses(beside)).override_failure_message("cut off. " + what).is_true()
				assert_bool(own.intersects(beside)).override_failure_message("over the menu. " + what).is_false()
				if sound != null:
					assert_bool(sound.get_global_rect().intersects(beside)).override_failure_message("over the Sound panel. " + what).is_false()
					assert_float(sound.position.x).is_equal(menu.position.x + menu.size.x + SoundMenu.GAP)     # the Sound panel is where it was
			else:
				# hidden only where nothing is free: no place inside what is shown clear of the menu and the Sound panel
				var taken: Array[Rect2] = []
				if sound != null:
					taken.append(sound.get_global_rect())
				assert_vector(menu.controls_place(own, beside.size if beside.size.x > 0 else controls.get_combined_minimum_size(), seen, 6.0, taken)).override_failure_message(
					"hidden though a place is free. " + what).is_equal(Vector2.INF)
			if window == Vector2(402, 874) and spec[2] == "whole":
				assert_bool(controls.is_visible_in_tree()).override_failure_message(what).is_true()     # the audit's size: shown, below the menu
				assert_float(beside.position.y).is_greater_equal(own.end.y)
			if window == Vector2(1920, 1080):
				assert_bool(controls.is_visible_in_tree()).override_failure_message(what).is_true()
				# the whole grid: beside the menu, tops level; at its left when the Sound panel has the right
				assert_float(beside.position.y).is_equal(own.position.y)
				assert_bool(beside.end.x <= own.position.x if with_sound else beside.position.x >= own.end.x).override_failure_message(what).is_true()
			get_tree().paused = false
			await get_tree().process_frame
			screen.remove_child(menu)
			menu.free()
			if sound != null:
				screen.remove_child(sound)
				sound.free()
	assert_int(shown_somewhere).is_greater(10)

func test_where_the_controls_panel_goes() -> void:
	const Menu := preload("res://ui/pause_menu.gd")
	var want := Vector2(236, 150)
	var grid := Rect2(0, 0, 960, 540)
	# room on the right: beside the menu, tops level
	assert_vector(Menu.controls_place(Rect2(395, 170, 170, 200), want, grid, 6.0)).is_equal(Vector2(571, 170))
	# no room on the right, room on the left
	assert_vector(Menu.controls_place(Rect2(700, 170, 170, 200), want, grid, 6.0)).is_equal(Vector2(458, 170))
	# the audit's case: the window shows x 279 to 681 only: below the menu, centred on it
	var seen := Rect2(279, 0, 402, 540)
	var at := Menu.controls_place(Rect2(395, 150, 170, 200), want, seen, 6.0)
	assert_vector(at).is_equal(Vector2(362, 356))
	assert_bool(seen.encloses(Rect2(at, want))).is_true()
	# no room below either: above
	assert_vector(Menu.controls_place(Rect2(395, 330, 170, 200), want, seen, 6.0)).is_equal(Vector2(362, 174))

func test_the_controls_keep_clear_of_a_panel_at_the_menu_s_right() -> void:
	const Menu := preload("res://ui/pause_menu.gd")
	var want := Vector2(236, 181)
	var grid := Rect2(0, 0, 960, 540)
	var own := Rect2(395, 164, 170, 212)
	var sound: Array[Rect2] = [Rect2(571, 164, 170, 168)]
	# the Sound panel has the right: the controls go to the menu's left, tops level
	assert_vector(Menu.controls_place(own, want, grid, 6.0, sound)).is_equal(Vector2(153, 164))
	assert_bool(Menu.stacked(own, want, grid, 6.0, sound)).is_false()
	# the audit's window (x 279 to 681): no side is free, the two stack and the menu makes room
	var seen := Rect2(279, 0, 402, 540)
	assert_bool(Menu.stacked(own, want, seen, 6.0, sound)).is_true()
	var up := Rect2(395, 70, 170, 212)
	var moved: Array[Rect2] = [Rect2(571, 70, 170, 168)]
	var at := Menu.controls_place(up, want, seen, 6.0, moved)
	assert_vector(at).is_equal(Vector2(362, 288))
	assert_bool(Rect2(at, want).intersects(moved[0])).is_false()
	# 480 x 270 at "whole" shows 480 x 270 texels: nothing is free, so no place (the panel is not shown)
	var small := Rect2(240, 135, 480, 270)
	assert_bool(Menu.stacked(own, want, small, 6.0, sound)).is_false()
	assert_vector(Menu.controls_place(own, want, small, 6.0, sound)).is_equal(Vector2.INF)

## Where the menu and the panel beside it stand (ui/pause_menu.gd menu_place, side_place).
func test_where_the_menu_and_the_panel_beside_it_go() -> void:
	const Menu := preload("res://ui/pause_menu.gd")
	var own := Vector2(170, 212)
	var side := Vector2(170, 168)
	var grid := Rect2(0, 0, 960, 540)
	var centred := grid.get_center() - own / 2.0
	# the whole grid: the menu in the middle, the panel at its right, tops level (as before)
	assert_vector(Menu.menu_place(centred, own, side, grid, 6.0)).is_equal(centred)
	assert_vector(Menu.side_place(Rect2(centred, own), side, grid, 6.0)).is_equal(Vector2(571, 164))
	# no panel: the middle
	assert_vector(Menu.menu_place(centred, own, Vector2.ZERO, Rect2(279, 0, 402, 540), 6.0)).is_equal(centred)
	# a phone upright at "whole" (x 279 to 681): the two move over together and sit centred
	var seen := Rect2(279, 0, 402, 540)
	var at: Vector2 = Menu.menu_place(centred, own, side, seen, 6.0)
	assert_vector(at).is_equal(Vector2(307, 164))
	var beside := Rect2(Menu.side_place(Rect2(at, own), side, seen, 6.0), side)
	assert_vector(beside.position).is_equal(Vector2(483, 164))
	assert_bool(seen.encloses(beside)).is_true()
	# the controls below them: centred under the two (x 307 to 653), not under the menu alone
	var taken: Array[Rect2] = [Rect2(483, 70, 170, 168)]
	assert_vector(Menu.controls_place(Rect2(307, 70, 170, 212), Vector2(236, 181), seen, 6.0, taken)).is_equal(Vector2(362, 288))
	# and pushed inside what is shown where that centre would leave it
	assert_vector(Menu.controls_place(Rect2(279, 70, 170, 212), Vector2(236, 181), Rect2(279, 0, 240, 540), 6.0)).is_equal(Vector2(279, 288))
	# narrower than the two: the panel below the menu, the two centred top to bottom
	var narrow := Rect2(320, 0, 320, 540)
	assert_bool(Menu.side_below(own, side, narrow, 6.0)).is_true()
	at = Menu.menu_place(centred, own, side, narrow, 6.0)
	assert_vector(at).is_equal(Vector2(395, 77))
	beside = Rect2(Menu.side_place(Rect2(at, own), side, narrow, 6.0), side)
	assert_vector(beside.position).is_equal(Vector2(395, 295))
	assert_bool(narrow.encloses(beside)).is_true()
	# too short for the two as well: from the top edge, never above it
	var tiny := Rect2(320, 100, 320, 300)
	assert_float(Menu.menu_place(centred, own, side, tiny, 6.0).y).is_equal(100.0)

# --- the audit of #494: focus after a pause, the pause button, Quit asks, the title card (15 Nov) ------
## The HUD as the game has it, running under the pause as game.tscn's Game does, not paused.
func _hud_host() -> Control:
	var host: Control = auto_free(Control.new())
	host.process_mode = Node.PROCESS_MODE_ALWAYS
	host.size = UiStyle.GRID
	add_child(host)
	var hud: Control = load("res://ui/hud.gd").new()
	hud.name = "HUD"
	host.add_child(hud)
	for i in 3:
		await get_tree().process_frame
	return host

func _frames(n: int) -> void:
	for i in n:
		await get_tree().process_frame

func _key_press(code: Key) -> void:
	for down: bool in [true, false]:
		var e := InputEventKey.new()
		e.keycode = code
		e.physical_keycode = code
		e.pressed = down
		get_viewport().push_input(e, true)

## A stand-in for the raid's prepare screen (the raid files belong to another stream): a focused button.
## On main, Resume left no control focused, so the d-pad and A did nothing on that screen any more.
func test_resume_hands_the_focus_back_to_the_control_that_had_it() -> void:
	var host := await _hud_host()
	var stand_in := Button.new()
	stand_in.name = "StandIn"
	stand_in.text = "Sound the anvil"
	host.add_child(stand_in)
	var presses := [0]
	stand_in.pressed.connect(func() -> void: presses[0] += 1)
	stand_in.grab_focus()
	await _frames(2)
	get_tree().paused = true
	await _frames(3)
	var resume := _row(host, "Resume")
	assert_object(get_viewport().gui_get_focus_owner()).is_same(resume)
	_pad_press(JOY_BUTTON_A)                         # A on Resume
	assert_bool(get_tree().paused).is_false()
	await _frames(3)
	assert_object(get_viewport().gui_get_focus_owner()).override_failure_message("no focus after Resume").is_same(stand_in)
	_pad_press(JOY_BUTTON_A)
	assert_int(presses[0]).override_failure_message("A did nothing after the pause").is_equal(1)
	# by Esc's way too (the tree unpaused from outside the menu), and with the focus moved to the Sound panel
	get_tree().paused = true
	await _frames(3)
	_row(host, "Pixel scale").grab_focus()
	_pad_press(JOY_BUTTON_DPAD_RIGHT)
	var crossed := get_viewport().gui_get_focus_owner()
	assert_bool(crossed != null and crossed.get_parent().get_parent() is SoundMenu).override_failure_message(
		"right from Pixel scale went to %s" % (crossed.get_path() if crossed != null else "nothing")).is_true()
	get_tree().paused = false
	await _frames(3)
	assert_object(get_viewport().gui_get_focus_owner()).is_same(stand_in)
	# a control that went away or was hidden meanwhile gets nothing; nothing else is focused either
	get_tree().paused = true
	await _frames(3)
	stand_in.visible = false
	get_tree().paused = false
	await _frames(3)
	assert_object(get_viewport().gui_get_focus_owner()).is_null()
	stand_in.visible = true
	stand_in.grab_focus()
	get_tree().paused = true
	await _frames(3)
	stand_in.free()
	get_tree().paused = false
	await _frames(3)
	assert_object(get_viewport().gui_get_focus_owner()).is_null()

## In play nothing has the focus before the pause, and nothing has it after: the pad's A rolls and presses
## no row, no setting changes.
func test_with_no_focus_before_the_pause_there_is_none_after_it() -> void:
	var host := await _hud_host()
	var vp := get_viewport()
	if vp.gui_get_focus_owner() != null:
		vp.gui_get_focus_owner().release_focus()
	var presses := [0]
	for b: Button in host.find_children("*", "Button", true, false):
		b.pressed.connect(func() -> void: presses[0] += 1)
	for way: String in ["resume", "outside"]:
		get_tree().paused = true
		await _frames(3)
		if way == "resume":
			_pad_press(JOY_BUTTON_A)
			presses[0] -= 1                             # that press was Resume's
		else:
			get_tree().paused = false
		await _frames(3)
		assert_bool(get_tree().paused).is_false()
		assert_object(vp.gui_get_focus_owner()).override_failure_message("focus after %s" % way).is_null()
		var before := SaveGame.data.duplicate(true)
		_pad_press(JOY_BUTTON_A)
		_key_press(KEY_ENTER)
		await _frames(2)
		assert_int(presses[0]).override_failure_message("a row was pressed after %s" % way).is_equal(0)
		assert_dict(SaveGame.data).is_equal(before)
		assert_bool(get_tree().paused).is_false()

func _pause_button(host: Node) -> Button:
	return host.find_child("PauseButton", true, false) as Button

## The pause button opens the menu, as Esc and Start do; it is hidden while the menu shows, never takes the
## focus, and stands aside while the raid's prepare screen (here a stand-in in its group) covers the HUD.
func test_the_pause_button_opens_the_menu_and_hides_while_it_cannot() -> void:
	var host := await _hud_host()
	var button := _pause_button(host)
	assert_object(button).override_failure_message("the HUD has no pause button").is_not_null()
	assert_bool(button.is_visible_in_tree()).is_true()
	assert_int(button.focus_mode).is_equal(Control.FOCUS_NONE)
	assert_int(button.action_mode).is_equal(BaseButton.ACTION_MODE_BUTTON_PRESS)
	var at := await _bring(host, button)
	_click(at)
	assert_bool(get_tree().paused).override_failure_message("a click on the pause button did not pause").is_true()
	await _frames(3)
	assert_bool(button.is_visible_in_tree()).is_false()
	assert_bool(_row(host, "Resume").is_visible_in_tree()).is_true()
	_click(at)                                       # the dim takes a press where the button was
	assert_bool(get_tree().paused).is_true()
	(_row(host, "Resume") as Button).pressed.emit()
	await _frames(3)
	assert_bool(button.is_visible_in_tree()).is_true()
	# a finger
	for down: bool in [true, false]:
		var t := InputEventScreenTouch.new()
		t.index = 0
		t.pressed = down
		t.position = at
		Input.parse_input_event(t)
		await _frames(2)
	assert_bool(get_tree().paused).override_failure_message("a tap on the pause button did not pause").is_true()
	get_tree().paused = false
	await _frames(3)
	# the prepare screen up: no pause button (the screen would take its taps)
	var screen := Control.new()
	screen.add_to_group("raid_screen")
	host.add_child(screen)
	await _frames(2)
	assert_bool(button.is_visible_in_tree()).is_false()
	screen.visible = false
	await _frames(2)
	assert_bool(button.is_visible_in_tree()).is_true()

## A press on the pause button reaches no one else: the game reads the left mouse button as a shot
## (Input.is_action_just_pressed in actors/player.gd), and the button pauses on the press itself, before
## the player's next physics step. The same press elsewhere shoots: the probe works.
func test_a_press_on_the_pause_button_does_not_shoot() -> void:
	var host := await _hud_host()
	var p: Player = auto_free(load("res://actors/player.tscn").instantiate())
	p.process_mode = Node.PROCESS_MODE_PAUSABLE      # as under the game's ZoneRoot
	add_child(p)
	p.use_mouse_aim = false
	for i in 3:
		await get_tree().physics_frame
	var button := _pause_button(host)
	var at := await _bring(host, button)
	for down: bool in [true, false]:
		var e := InputEventMouseButton.new()
		e.button_index = MOUSE_BUTTON_LEFT
		e.pressed = down
		e.button_mask = MOUSE_BUTTON_MASK_LEFT if down else 0
		e.position = at
		e.global_position = at
		Input.parse_input_event(e)
		for i in 2:
			await get_tree().physics_frame
	assert_bool(get_tree().paused).is_true()
	get_tree().paused = false
	for i in 4:
		await get_tree().physics_frame
	assert_bool(p.is_shooting()).override_failure_message("the press on the pause button shot an arrow").is_false()
	# the probe: the same press where there is no button shoots
	host.position += Vector2(0, 400)
	await _frames(2)
	for down: bool in [true, false]:
		var e := InputEventMouseButton.new()
		e.button_index = MOUSE_BUTTON_LEFT
		e.pressed = down
		e.button_mask = MOUSE_BUTTON_MASK_LEFT if down else 0
		e.position = at
		e.global_position = at
		Input.parse_input_event(e)
		for i in 2:
			await get_tree().physics_frame
	assert_bool(p.is_shooting()).override_failure_message("the probe: a press on the world did not shoot").is_true()

## Where the pause button stands: inside what the window shows, at least 44 screen pixels (logical points
## at ratio 1), clear of every HUD piece (the hearts, the rolls, the tracker with the lantern's lights, the
## Glint count, the prompt, and a title card), at every window of the layout test above (its eleven
## sizes are eight windows), each in both scale modes.
func test_the_pause_button_stays_inside_the_window_and_clear_of_the_hud() -> void:
	const Screen := preload("res://main/pixel_screen.gd")
	var host := await _hud_host()
	var hud := host.get_node("HUD") as Control
	var button := _pause_button(host)
	# every piece filled as wide as it gets: five hearts, three rolls, a long tracker with the lights row,
	# a five-digit Glint count, the "Look" prompt, a title card
	hud.call("_meter", hud.get("_hearts"), "hearts", 5, 5, "heart")
	hud.call("_meter", hud.get("_rolls"), "rolls", 2, 3, "roll")
	hud.call("_show_quest", "The first night: Hold the shard lantern (wave 1 of 3), and keep the hurdles standing")
	var lights := hud.get("_lantern") as HBoxContainer
	for i in 5:
		lights.add_child(UiStyle.icon("shard_full"))
	lights.visible = true
	(hud.get("_glint") as Label).text = "99999"
	(hud.get("_prompt") as Control).visible = true
	(hud.get("_prompt_verb") as Label).text = "Look"
	SaveGame.data.settings.reduced_motion = true
	hud.call("show_card", "The Starfall", "Act one", "A long line of text under the title, as the opening card has.", 600.0)
	var menu := hud.get("_pause_menu") as Control
	var pieces := ["_hearts", "_rolls", "_quest", "_glint_box", "_prompt", "_card"]
	for spec: Array in [[402, 874], [480, 270], [375, 667], [1920, 1080], [960, 540], [874, 402], [2622, 1206], [320, 720]]:
		for mode: String in ["fill", "whole"]:
			var window := Vector2(spec[0], spec[1])
			var k: float = Screen.choose_scale(window, mode)
			var offset := ((window - Screen.ART * k) / 2.0).floor()
			get_tree().call_group(&"pause_screen_layout", &"fit_screen", window, k, offset, 1.0, Rect2(Vector2.ZERO, window))
			await _frames(3)
			var seen: Rect2 = menu.call(&"visible_grid")
			var own := button.get_global_rect()
			var what := "%s %s: the button %s, the window shows %s" % [window, mode, own, seen]
			assert_bool(button.is_visible_in_tree()).override_failure_message(what).is_true()
			assert_bool(seen.encloses(own)).override_failure_message("cut off. " + what).is_true()
			assert_float(own.size.y * k).override_failure_message("under 44 screen px. " + what).is_greater_equal(44.0)
			assert_float(own.size.x).is_equal(own.size.y)
			for name: String in pieces:
				var piece := hud.get(name) as Control
				assert_bool(piece.is_visible_in_tree()).override_failure_message("%s hidden. %s" % [name, what]).is_true()
				assert_bool(own.intersects(piece.get_global_rect())).override_failure_message(
					"over %s %s. %s" % [name, piece.get_global_rect(), what]).is_false()
	# the same with a phone's safe area (a notch at the top and a rounded right edge)
	var phone := Vector2(1206, 2622)
	var kp: float = Screen.choose_scale(phone, "fill")
	var off := ((phone - Screen.ART * kp) / 2.0).floor()
	get_tree().call_group(&"pause_screen_layout", &"fit_screen", phone, kp, off, 3.0, Rect2(40, 140, 1126, 2400))
	await _frames(3)
	var safe: Rect2 = menu.call(&"visible_grid")
	assert_bool(safe.encloses(button.get_global_rect())).is_true()
	assert_float(button.size.y * kp).is_greater_equal(44.0 * 3.0)

## Quit asks first, in the menu: Quit or Stay, the focus on Stay, and Stay stands where Quit did. Stay goes
## back with the focus on Quit. By the keyboard, the mouse and the pad. On main the press quit at once.
func test_quit_asks_first_and_stay_goes_back_to_the_quit_row() -> void:
	var host := await _paused_hud()
	var menu := _row(host, "Resume").get_parent().get_parent() as Control
	var sound := host.find_children("*", "SoundMenu", true, false)[0] as Control
	var quit := _row(host, "Quit")
	var quit_rect := quit.get_global_rect()
	var size := menu.size
	for way: String in ["keyboard", "mouse", "pad"]:
		quit.grab_focus()
		await _frames(1)
		var quit_rel := quit.get_global_rect().position - menu.global_position
		match way:
			"keyboard": _key_press(KEY_ENTER)
			"mouse": _click(await _bring(host, quit))
			"pad": _pad_press(JOY_BUTTON_A)
		await _frames(3)
		assert_bool(get_tree().paused).is_true()
		var stay := _row(host, "Stay")
		var leave := host.find_child("QuitConfirm", true, false) as Button
		assert_object(stay).override_failure_message("%s: Quit did not ask" % way).is_not_null()
		assert_object(leave).is_not_null()
		assert_str((host.find_child("QuitQuestion", true, false) as Label).text).is_equal("Quit the game?")
		assert_object(get_viewport().gui_get_focus_owner()).override_failure_message("%s: the focus is not on Stay" % way).is_same(stay)
		assert_bool(quit.is_visible_in_tree()).is_false()
		assert_bool(_row(host, "Resume") == null).is_true()
		assert_bool(sound.is_visible_in_tree()).override_failure_message("the Sound panel stays beside the question").is_false()
		assert_vector(menu.size).is_equal(size)
		var stay_rect := stay.get_global_rect()
		assert_vector(stay_rect.position - menu.global_position).override_failure_message("Stay is not where Quit was").is_equal(quit_rel)
		assert_vector(stay_rect.size).is_equal(quit_rect.size)
		assert_float(stay_rect.size.y).is_greater_equal(float(UiStyle.TOUCH))
		# up and down run between the two
		_pad_press(JOY_BUTTON_DPAD_UP)
		assert_object(get_viewport().gui_get_focus_owner()).is_same(leave)
		_pad_press(JOY_BUTTON_DPAD_DOWN)
		assert_object(get_viewport().gui_get_focus_owner()).is_same(stay)
		match way:
			"keyboard": _key_press(KEY_ENTER)
			"mouse": _click(await _bring(host, stay))
			"pad": _pad_press(JOY_BUTTON_A)
		await _frames(3)
		assert_bool(get_tree().paused).is_true()
		assert_object(_row(host, "Stay")).override_failure_message("%s: Stay did not go back" % way).is_null()
		assert_object(get_viewport().gui_get_focus_owner()).override_failure_message("%s: the focus is not on Quit" % way).is_same(quit)
		assert_bool(sound.is_visible_in_tree()).is_true()
		assert_int(menu.find_children("*", "Button", true, false).size()).is_equal(4)
	# the pause ending while it asks (Esc, Start) puts the rows back for the next time
	quit.grab_focus()
	_key_press(KEY_ENTER)
	await _frames(2)
	assert_object(_row(host, "Stay")).is_not_null()
	get_tree().paused = false
	await _frames(3)
	assert_object(_row(host, "Stay")).is_null()
	get_tree().paused = true
	await _frames(3)
	assert_object(_row(host, "Stay")).is_null()
	assert_bool(_row(host, "Resume").is_visible_in_tree()).is_true()
	assert_bool(sound.is_visible_in_tree()).is_true()

## The title card stands aside while paused (on a fresh game it showed through the pause panels at
## 402 x 874 and 320 x 720) and comes back on resume while it is still due; a card that ran out meanwhile
## does not.
func test_the_title_card_hides_while_paused_and_comes_back() -> void:
	var host := await _hud_host()
	var hud := host.get_node("HUD") as Control
	var card := hud.get("_card") as Control
	SaveGame.data.settings.reduced_motion = true
	hud.call("show_card", "The Starfall", "", "Morning.", 30.0)
	await _frames(2)
	assert_bool(card.is_visible_in_tree()).is_true()
	get_tree().paused = true
	await _frames(2)
	assert_bool(card.is_visible_in_tree()).override_failure_message("the card shows behind the pause menu").is_false()
	assert_str(hud.shown_text().banner).is_equal("The Starfall")      # still due: game.gd waits on it
	get_tree().paused = false
	await _frames(2)
	assert_bool(card.is_visible_in_tree()).is_true()
	get_tree().paused = true
	await _frames(2)
	hud.set("_card_left", 0.0)
	get_tree().paused = false
	await _frames(2)
	assert_bool(card.is_visible_in_tree()).is_false()

# --- the audit of #496 (15 Nov) -----------------------------------------------------------------------
## Picture modes (--shot, --demo, --lineup and the rest) set the HUD's guidance off: no pause button there,
## where it covered art the review pictures look at.
func test_no_pause_button_where_guidance_is_off() -> void:
	var host := await _hud_host()
	var hud := host.get_node("HUD") as Control
	var button := _pause_button(host)
	assert_bool(button.is_visible_in_tree()).is_true()
	hud.set("guidance", false)
	await _frames(2)
	assert_bool(button.is_visible_in_tree()).override_failure_message("the pause button shows in a picture mode").is_false()
	hud.set("guidance", true)
	await _frames(2)
	assert_bool(button.is_visible_in_tree()).is_true()

## The HUD and a real prepare screen after it, as game.gd adds them, the night announced.
func _hud_and_prepare_screen() -> Array:
	for q: String in ["woodland_stones", "road_to_crossroads", "cold_forge", "under_the_stones", "home_again"]:
		SaveGame.data.quests[q] = {"state": "done", "step": Quests.defs[q].steps.size()}
	for f: String in ["shard_home:woodland", "hale_walked_home", "visited:crossroads", "visited:woodland"]:
		SaveGame.set_flag(f)
	SaveGame.data.village.restored = {"forge": 1, "fern_cottage": 1}
	var host := await _hud_host()
	var screen := RaidScreen.new()
	host.add_child(screen)
	Raids.arrive("crossroads", "woodland")
	assert_str(Raids.state()).is_equal("announced")
	screen.open()
	await _frames(3)
	return [host, screen]

## On main the prepare screen (added after the HUD) was drawn over the pause menu and kept running under
## the pause: Tab reached "Sound the anvil" and Enter sounded it while paused (the audit's probe). Now the
## screen stands aside while paused, still open, and comes back on resume with the focus on its button.
func test_the_prepare_screen_stands_aside_under_the_pause_and_comes_back() -> void:
	var made := await _hud_and_prepare_screen()
	var host: Control = made[0]
	var screen: RaidScreen = made[1]
	var anvil := screen.get_node("Panel").find_child("SoundTheAnvil", true, false) as Button
	assert_object(get_viewport().gui_get_focus_owner()).is_same(anvil)
	assert_bool(_pause_button(host).is_visible_in_tree()).is_false()      # the screen takes the taps there
	get_tree().paused = true
	await _frames(3)
	var menu := _row(host, "Resume").get_parent().get_parent() as Control
	# drawn: the menu over the world, nothing of the screen over the menu
	assert_bool(menu.is_visible_in_tree()).is_true()
	assert_bool(screen.is_visible_in_tree()).override_failure_message("the prepare screen is drawn over the pause menu").is_false()
	assert_bool(anvil.is_visible_in_tree()).is_false()
	assert_bool(screen.is_open()).is_true()
	assert_bool(_pause_button(host).is_visible_in_tree()).is_false()
	# Tab and Enter, again and again: the focus stays in the menu and its Sound panel, the anvil stays silent
	var sound := host.find_children("*", "SoundMenu", true, false)[0] as Control
	for i in 9:
		_key_press(KEY_TAB)
		await _frames(1)
		var f := get_viewport().gui_get_focus_owner()
		assert_bool(f != null and (menu.is_ancestor_of(f) or sound.is_ancestor_of(f))).override_failure_message(
			"Tab took the focus to %s" % (f.get_path() if f != null else "nothing")).is_true()
		if f != null and String(f.name) != "Resume" and String(f.name) != "Quit":
			_key_press(KEY_ENTER)
			await _frames(1)
	assert_str(Raids.state()).override_failure_message("the anvil sounded while paused").is_equal("announced")
	assert_bool(get_tree().paused).is_true()
	# back: the screen as it was, the focus on its button, which works
	(_row(host, "Resume") as Button).pressed.emit()
	await _frames(3)
	assert_bool(screen.is_visible_in_tree()).is_true()
	assert_object(get_viewport().gui_get_focus_owner()).override_failure_message("the focus did not come back to the anvil").is_same(anvil)
	assert_bool(_pause_button(host).is_visible_in_tree()).is_false()
	_key_press(KEY_ENTER)
	await _frames(2)
	assert_str(Raids.state()).is_equal("running")
	assert_bool(screen.is_open()).is_false()
	await _frames(2)
	assert_bool(_pause_button(host).is_visible_in_tree()).is_true()
