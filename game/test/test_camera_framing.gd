extends GdUnitTestSuite
## Tall landmarks framed whole near them (world/camera_framing.gd): the library's bell cupola in Crossroads
## (Matt, 13 Nov: "bell tower optional, cupola drawn") was above the top of the picture from everywhere in
## the square. The hint math first (fit, the player's safe insets, the zone limits, the ease, reduced
## motion, no effect outside the area or while blocked), then the real game in a 960 x 540 SubViewport.

const SCREEN := Vector2(960, 540)
const LIMITS := Rect2(0, 0, 1920, 1680)            # Crossroads' bounds
const CUPOLA := Rect2(717, 235, 54, 138)           # CupolaEmpty as the zone scene places it
const AREA := Rect2(568, 604, 352, 156)
const LIFT := Vector2(0, -24)                      # game.gd: the plain follow is 8 world px above the feet

func _frame_at(c: Vector2) -> Rect2:
	return Rect2(c - SCREEN / 2.0, SCREEN)

func _feet_safe(c: Vector2, feet: Vector2) -> bool:
	var on := feet - (c - SCREEN / 2.0)
	return on.x >= CameraFraming.SAFE_LT.x - 0.01 and on.y >= CameraFraming.SAFE_LT.y - 0.01 \
		and on.x <= SCREEN.x - CameraFraming.SAFE_RB.x + 0.01 and on.y <= SCREEN.y - CameraFraming.SAFE_RB.y + 0.01

# --- the hint math ------------------------------------------------------------------------------------------
func test_the_plain_follow_cuts_the_cupola_off() -> void:
	# the fault as it was: at the library's door the top of the picture is 294 texels above the feet
	var feet := Vector2(744, 640)
	assert_bool(_frame_at(feet + LIFT).encloses(CUPOLA)).is_false()

func test_the_cupola_fits_whole_near_the_door() -> void:
	for feet: Vector2 in [Vector2(744, 616), Vector2(744, 650), Vector2(640, 690), Vector2(860, 700)]:
		var c := CameraFraming.fit_centre(feet + LIFT, feet, CUPOLA, SCREEN, LIMITS)
		assert_bool(_frame_at(c).grow(-CameraFraming.MARGIN + 0.01).encloses(CUPOLA)).override_failure_message(
			"feet %s: the frame %s does not hold %s" % [feet, _frame_at(c), CUPOLA]).is_true()
		assert_bool(_feet_safe(c, feet)).override_failure_message("feet %s off the safe insets at centre %s" % [feet, c]).is_true()
		# the nearest centre that fits: the picture's top exactly MARGIN above the cupola, x untouched
		assert_float(c.y).is_equal_approx(CUPOLA.position.y - CameraFraming.MARGIN + SCREEN.y / 2.0, 0.01)
		assert_float(c.x).is_equal_approx(feet.x, 0.01)

func test_the_player_wins_over_the_landmark() -> void:
	# further south the feet would leave the bottom inset: the camera stops there, the cupola is cut
	for y: float in [704.0, 730.0, 760.0]:
		var feet := Vector2(744, y)
		var c := CameraFraming.fit_centre(feet + LIFT, feet, CUPOLA, SCREEN, LIMITS)
		assert_bool(_feet_safe(c, feet)).is_true()
		assert_float(feet.y - (c.y - SCREEN.y / 2.0)).is_equal_approx(SCREEN.y - CameraFraming.SAFE_RB.y, 0.01)
		assert_bool(_frame_at(c).grow(-CameraFraming.MARGIN + 0.01).encloses(CUPOLA)).is_false()
	# and the last feet that still frame it whole: y 703
	var last := Vector2(744, 703)
	var c2 := CameraFraming.fit_centre(last + LIFT, last, CUPOLA, SCREEN, LIMITS)
	assert_bool(_frame_at(c2).grow(-CameraFraming.MARGIN + 0.01).encloses(CUPOLA)).is_true()

func test_the_frame_stays_inside_the_zone_limits() -> void:
	# a landmark at the zone's top edge: the centre is never above limits.top + 270
	var tall := Rect2(300, 10, 40, 200)
	var feet := Vector2(320, 400)
	var c := CameraFraming.fit_centre(feet + LIFT, feet, tall, SCREEN, LIMITS)
	assert_bool(LIMITS.encloses(_frame_at(c))).is_true()
	# limits that forbid the fit: they win, as the phantom camera's own clamp would
	var tight := Rect2(0, 300, 1920, 1380)
	var feet2 := Vector2(744, 650)
	var c2 := CameraFraming.fit_centre(feet2 + LIFT, feet2, CUPOLA, SCREEN, tight)
	assert_float(c2.y).is_equal_approx(300.0 + SCREEN.y / 2.0, 0.01)
	assert_bool(tight.encloses(_frame_at(c2))).is_true()
	# sideways too: a landmark past the east limit pulls the frame no further than the limit
	var east := Rect2(1880, 500, 30, 60)
	var feet3 := Vector2(1700, 700)
	var c3 := CameraFraming.fit_centre(feet3 + LIFT, feet3, east, SCREEN, LIMITS)
	assert_float(c3.x).is_equal_approx(LIMITS.end.x - SCREEN.x / 2.0, 0.01)

func test_a_landmark_bigger_than_the_screen_is_centred_within_the_safe_insets() -> void:
	var huge := Rect2(0, 0, 400, 900)
	var feet := Vector2(200, 600)
	var c := CameraFraming.fit_centre(feet + LIFT, feet, huge, SCREEN, Rect2(-2000, -2000, 6000, 6000))
	assert_bool(_feet_safe(c, feet)).is_true()

func test_block_reasons() -> void:
	assert_str(CameraFraming.block_reason(false, true, false, false, [])).is_equal("")
	assert_str(CameraFraming.block_reason(false, true, false, false, ["idle", "leash", "dormant"])).is_equal("")
	assert_str(CameraFraming.block_reason(true, true, false, false, [])).is_equal("talk")
	assert_str(CameraFraming.block_reason(false, false, false, false, [])).is_equal("input off")
	assert_str(CameraFraming.block_reason(false, true, true, false, [])).is_equal("downed")
	assert_str(CameraFraming.block_reason(false, true, false, true, [])).is_equal("raid")
	for st: String in ["chase", "approach", "windup", "attack", "lunge", "recover"]:
		assert_str(CameraFraming.block_reason(false, true, false, false, ["idle", st])).is_equal("fight")

# --- the ease, reduced motion, the area and the blocks (a stand-in for the zone's cupola picture) ----------
func _framing(visible := true) -> CameraFraming:
	var host: Node2D = auto_free(Node2D.new())
	add_child(host)
	var s := Sprite2D.new()
	s.centered = false
	s.texture = ImageTexture.create_from_image(Image.create(int(CUPOLA.size.x), int(CUPOLA.size.y), false, Image.FORMAT_RGBA8))
	s.position = CUPOLA.position
	s.visible = visible
	host.add_child(s)
	var f := CameraFraming.new()
	f.hints = [{"id": "t", "area": AREA, "nodes": [s]}]
	return f

func _step(f: CameraFraming, feet: Vector2, dt := 1.0 / 60.0, reduced := false, blocked := "") -> Dictionary:
	return f.step(dt, feet, feet + LIFT, SCREEN, LIMITS, reduced, blocked)

func test_it_eases_in_and_out_over_half_a_second() -> void:
	var f := _framing()
	var feet := Vector2(744, 650)
	var full := CameraFraming.fit_centre(feet + LIFT, feet, CUPOLA, SCREEN, LIMITS) - (feet + LIFT)
	var r := _step(f, feet, 0.25)
	assert_bool(r.cut).is_false()
	assert_vector(r.offset).is_equal_approx(full * 0.5, Vector2(0.01, 0.01))   # smoothstep(0.5) = 0.5
	r = _step(f, feet, 0.25)
	assert_vector(r.offset).is_equal_approx(full, Vector2(0.01, 0.01))
	r = _step(f, feet, 1.0)                                                   # and stays, no drift
	assert_vector(r.offset).is_equal_approx(full, Vector2(0.01, 0.01))
	# out of the area: back to the plain follow in 0.5 s, every step between the two
	var out := Vector2(744, 900)
	var prev := 1.0
	var t := 0.0
	while true:
		r = _step(f, out, 0.05)
		t += 0.05
		assert_float(float(r.weight)).is_less_equal(prev)
		prev = float(r.weight)
		if r.offset == Vector2.ZERO:
			break
		assert_float(t).is_less(0.6)
	assert_float(t).is_equal_approx(0.5, 0.06)
	assert_str(f.hint_id).is_equal("")

func test_the_ease_keeps_the_feet_in_the_safe_insets() -> void:
	# walking south out of the area while it eases out: the camera's centre is between the plain one and the
	# framed one, so the feet stay inside the insets on every step
	var f := _framing()
	var feet := Vector2(744, 640)
	for i in 40:
		_step(f, feet)
	for i in 60:
		feet.y += 4.0          # 240 texels a second: faster than Bramble runs
		var r := _step(f, feet)
		assert_bool(_feet_safe(feet + LIFT + r.offset, feet)).override_failure_message("feet %s" % feet).is_true()

func test_reduced_motion_cuts_in_and_out() -> void:
	var f := _framing()
	var feet := Vector2(744, 650)
	var full := CameraFraming.fit_centre(feet + LIFT, feet, CUPOLA, SCREEN, LIMITS) - (feet + LIFT)
	var r := _step(f, feet, 1.0 / 60.0, true)
	assert_bool(r.cut).is_true()
	assert_vector(r.offset).is_equal_approx(full, Vector2(0.01, 0.01))
	r = _step(f, feet, 1.0 / 60.0, true)
	assert_bool(r.cut).is_false()                                   # one cut, not one every frame
	r = _step(f, Vector2(744, 900), 1.0 / 60.0, true)
	assert_bool(r.cut).is_true()
	assert_vector(r.offset).is_equal(Vector2.ZERO)

func test_no_effect_outside_the_area() -> void:
	var f := _framing()
	for feet: Vector2 in [Vector2(744, 900), Vector2(400, 650), Vector2(1000, 650), Vector2(744, 770)]:
		for i in 60:
			var r := _step(f, feet)
			assert_vector(r.offset).is_equal(Vector2.ZERO)

func test_no_effect_while_the_landmark_is_hidden() -> void:
	var f := _framing(false)
	for i in 60:
		assert_vector(_step(f, Vector2(744, 650)).offset).is_equal(Vector2.ZERO)

func test_no_effect_while_blocked_and_a_block_eases_it_out() -> void:
	for reason: String in ["talk", "input off", "downed", "raid", "fight"]:
		var f := _framing()
		for i in 60:
			assert_vector(_step(f, Vector2(744, 650), 1.0 / 60.0, false, reason).offset).is_equal(Vector2.ZERO)
		for i in 60:
			_step(f, Vector2(744, 650))
		assert_float(f.weight).is_equal(1.0)
		var t := 0.0
		while f.weight > 0.0:
			_step(f, Vector2(744, 650), 0.05, false, reason)
			t += 0.05
		assert_float(t).is_equal_approx(0.5, 0.06)

func test_the_crossroads_hint_names_both_cupola_pictures() -> void:
	var defs := CameraFraming.load_defs()
	var hs: Array = defs.get("crossroads", [])
	assert_int(hs.size()).is_equal(1)
	assert_array(hs[0].frame).contains_exactly(["Props/If_cupola_empty/CupolaEmpty", "Props/If_cupola_hung/CupolaHung"])
	var area: Array = hs[0].area
	assert_vector(Vector2(area[0], area[1])).is_equal(AREA.position)
	assert_vector(Vector2(area[2], area[3])).is_equal(AREA.size)

# --- the real game, drawn in a 960 x 540 SubViewport as main.tscn draws it --------------------------------
func _game() -> Node2D:
	var world: SubViewport = auto_free(SubViewport.new())
	world.size = Vector2i(SCREEN)
	add_child(world)
	var g: Node2D = load("res://game.tscn").instantiate()
	world.add_child(g)
	get_tree().root.get_node("PhantomCameraManager").screen_size = Vector2i(SCREEN)
	return g

func _cupola_on_screen(path: String) -> Rect2:
	var s := Zones.current.get_node(path) as Sprite2D
	return s.get_global_transform_with_canvas() * s.get_rect()

func _settle(g: Node2D, at: Vector2, frames := 90) -> void:
	g.player.global_position = at
	for i in frames:
		await get_tree().physics_frame

func test_in_crossroads_the_empty_cupola_is_framed_and_bramble_stays_on_screen() -> void:
	SaveGame.reset()
	var g := _game()
	Zones.go_to("crossroads", "start")
	var path := "Props/If_cupola_empty/CupolaEmpty"
	await _settle(g, Vector2(744, 900))
	assert_bool(Rect2(Vector2.ZERO, SCREEN).encloses(_cupola_on_screen(path))).is_false()   # in the square: cut off
	await _settle(g, Vector2(744, 650))
	var on := _cupola_on_screen(path)
	assert_bool(Rect2(Vector2.ZERO, SCREEN).grow(-8.0).encloses(on)).override_failure_message(
		"the cupola is at %s on the picture" % on).is_true()
	var feet: Vector2 = g.player.get_global_transform_with_canvas().origin
	assert_bool(Rect2(CameraFraming.SAFE_LT, SCREEN - CameraFraming.SAFE_LT - CameraFraming.SAFE_RB).grow(2.0).has_point(feet)) \
		.override_failure_message("the player is at %s on the picture" % feet).is_true()
	# a talk opens: the framing eases out (the look-ahead is held at zero for a talk as before)
	Dialogue.busy = true
	await _settle(g, Vector2(744, 650))
	Dialogue.busy = false
	assert_bool(Rect2(Vector2.ZERO, SCREEN).encloses(_cupola_on_screen(path))).is_false()
	# back to the square: the plain follow
	await _settle(g, Vector2(744, 650))
	await _settle(g, Vector2(744, 900))
	assert_float(g.framing.weight).is_equal(0.0)
	Zones.current = null

func test_in_crossroads_the_hung_cupola_is_framed_too_and_reduced_motion_cuts() -> void:
	SaveGame.reset()
	SaveGame.data.village.restored = {"bell_tower": 1}
	SaveGame.data.settings.reduced_motion = true
	var g := _game()
	Zones.go_to("crossroads", "start")
	await _settle(g, Vector2(744, 900))
	g.player.global_position = Vector2(744, 650)
	# two frames: the cut needs no ease (the phantom camera's own damping is skipped by the teleport)
	await get_tree().process_frame
	await get_tree().physics_frame
	await get_tree().process_frame
	await get_tree().physics_frame
	assert_float(g.framing.weight).is_equal(1.0)
	var cam := g.get_node("Camera2D") as Camera2D
	var top := cam.get_screen_center_position().y - SCREEN.y / 2.0
	assert_float(top).is_less_equal(CUPOLA.position.y - CameraFraming.MARGIN + 1.0)
	assert_bool(Rect2(Vector2.ZERO, SCREEN).encloses(_cupola_on_screen("Props/If_cupola_hung/CupolaHung"))).is_true()
	SaveGame.data.settings.reduced_motion = false
	Zones.current = null
