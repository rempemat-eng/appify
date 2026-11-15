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
## cut off. It is placed inside what the window shows: beside the menu where that fits, else below it.
func test_the_controls_panel_stays_inside_what_the_window_shows() -> void:
	const Screen := preload("res://main/pixel_screen.gd")
	for spec: Array in [[402, 874, "whole"], [402, 874, "fill"], [375, 667, "whole"], [1920, 1080, "fill"], [960, 540, "whole"], [874, 402, "fill"]]:
		var screen: Control = auto_free(Control.new())
		screen.size = UiStyle.GRID
		add_child(screen)
		var menu: PanelContainer = preload("res://ui/pause_menu.gd").new()
		screen.add_child(menu)
		var window := Vector2(spec[0], spec[1])
		var k: float = Screen.choose_scale(window, spec[2])
		var offset := ((window - Screen.ART * k) / 2.0).floor()
		assert_bool(menu.fit_screen(window, k, offset, 1.0, Rect2(Vector2.ZERO, window))).is_true()
		get_tree().paused = true
		for i in 5:
			await get_tree().process_frame
		var controls := menu.get_node("Controls") as ControlsPanel
		var seen: Rect2 = menu.visible_grid()
		var own := menu.get_global_rect()
		var beside := controls.get_global_rect()
		var what := "%s %s: panel %s, menu %s, the window shows %s" % [window, spec[2], beside, own, seen]
		assert_bool(controls.is_visible_in_tree()).is_true()
		if beside.size.x <= seen.size.x and beside.size.y <= seen.size.y:
			assert_bool(seen.grow(0.5).encloses(beside)).override_failure_message("cut off. " + what).is_true()
		else:
			# a window too small for the panel at this scale: as much of it as fits, from its top left
			assert_vector(beside.position).override_failure_message(what).is_equal(seen.position.round())
		if own.size.y + beside.size.y + 6.0 <= seen.size.y or own.size.x + beside.size.x + 6.0 <= seen.size.x:
			assert_bool(own.intersects(beside)).override_failure_message("over the menu. " + what).is_false()
		get_tree().paused = false
		await get_tree().process_frame
		screen.remove_child(menu)
		menu.free()

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
