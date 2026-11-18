extends GdUnitTestSuite
## Tall landmarks framed whole near them (world/camera_framing.gd): the library's bell cupola in Crossroads
## (Matt, 13 Nov: "bell tower optional, cupola drawn") was above the top of the picture from everywhere in
## the square. The hint math first (fit, the player's safe insets, the zone limits, the ease, reduced
## motion, no effect outside the area or while blocked), then the real game in a 960 x 540 SubViewport.

const SCREEN := Vector2(960, 540)
const LIMITS := Rect2(0, 0, 1920, 1680)            # Crossroads' bounds
const CUPOLA := Rect2(717, 235, 54, 138)           # CupolaEmpty as the zone scene places it
const AREA := Rect2(568, 300, 352, 396)
const FEATHERS := [128.0, 128.0, 128.0, 128.0]     # west, north, east, south
const TRACKER := Rect2(8, 33, 231, 58)            # the quest tracker panel as the #523 audit measured it
const HEARTS := Rect2(8, 8, 60, 20)
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

func test_the_game_reads_a_fight_from_the_zone_enemies_with_or_without_a_dead_flag() -> void:
	# found by check:godot: the Thornback has no `dead`, and bool(null) failed every frame in the Undercroft
	var zone: Zone = auto_free(Zone.new())
	var actors := Node2D.new()
	actors.name = "Actors"
	zone.add_child(actors)
	add_child(zone)
	var was: Zone = Zones.current
	Zones.current = zone
	var player := Node2D.new()
	zone.add_child(player)
	assert_str(CameraFraming.game_block_reason(player)).is_equal("")
	var plain := Node2D.new()                         # in the group, no state at all: not a fight
	plain.add_to_group("enemy")
	zone.add_child(plain)
	var awake := Node2D.new()
	awake.set_script(_Stand)
	awake.add_to_group("enemy")
	zone.add_child(awake)
	assert_str(CameraFraming.game_block_reason(player)).is_equal("")      # idle, no `dead`
	awake.set("state", &"chase")
	assert_str(CameraFraming.game_block_reason(player)).is_equal("fight")
	var outside: Node2D = auto_free(Node2D.new())     # an awake enemy outside the current zone does not count
	add_child(outside)
	awake.reparent(outside)
	assert_str(CameraFraming.game_block_reason(player)).is_equal("")
	Zones.current = was if is_instance_valid(was) else null

## A stand-in enemy with a `state` and no `dead`, as bosses/thornback.gd.
class _Stand extends Node2D:
	var state: StringName = &"idle"

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
	f.hints = [{"id": "t", "area": AREA, "feather": FEATHERS, "nodes": [s]}]
	return f

func _step(f: CameraFraming, feet: Vector2, dt := 1.0 / 60.0, reduced := false, blocked := "") -> Dictionary:
	return f.step(dt, feet, feet + LIFT, SCREEN, LIMITS, reduced, blocked)

func test_it_eases_in_and_out_over_half_a_second() -> void:
	var f := _framing()
	var feet := Vector2(744, 650)
	var full := CameraFraming.fit_centre(feet + LIFT, feet, CUPOLA, SCREEN, LIMITS) - (feet + LIFT)
	var r := _step(f, feet, 0.25)
	assert_bool(r.cut).is_false()
	assert_vector(r.offset).is_equal_approx(full * 0.5, Vector2(0.01, 0.01))   # half the weight, half the offset
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
	for feet: Vector2 in [Vector2(744, 900), Vector2(420, 650), Vector2(1060, 650), Vector2(744, 830)]:
		for i in 60:
			var r := _step(f, feet)
			assert_vector(r.offset).is_equal(Vector2.ZERO)

func test_no_effect_while_the_landmark_is_hidden() -> void:
	var f := _framing(false)
	for i in 60:
		assert_vector(_step(f, Vector2(744, 650)).offset).is_equal(Vector2.ZERO)

func test_no_effect_while_blocked_and_a_block_eases_it_out() -> void:
	for reason: String in ["input off", "downed", "raid", "fight"]:
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

func test_a_talk_holds_the_weight_where_it_is() -> void:
	# the bell tower's mark and the notice board are talked to in front of the library: no swing, no cut
	for reduced: bool in [false, true]:
		var f := _framing()
		var feet := Vector2(744, 650)
		assert_vector(_step(f, feet, 1.0 / 60.0, reduced, "talk").offset).is_equal(Vector2.ZERO)   # held at 0
		for i in 60:
			_step(f, feet, 1.0 / 60.0, reduced)
		var framed: Vector2 = _step(f, feet, 1.0 / 60.0, reduced).offset
		for i in 120:
			var r := _step(f, feet, 1.0 / 60.0, reduced, "talk")
			assert_bool(r.cut).is_false()
			assert_vector(r.offset).is_equal_approx(framed, Vector2(0.01, 0.01))
		assert_float(f.weight).is_equal(1.0)
		var r2 := _step(f, feet, 1.0 / 60.0, reduced)          # the talk ends: still framed, no cut
		assert_bool(r2.cut).is_false()
		assert_vector(r2.offset).is_equal_approx(framed, Vector2(0.01, 0.01))

func test_the_feather_round_the_area() -> void:
	# 1 inside, falling linearly to 0 over the feather outside each side (the south one 128 texels)
	assert_float(CameraFraming.feather(AREA, Vector2(744, AREA.end.y), FEATHERS)).is_equal(1.0)
	assert_float(CameraFraming.feather(AREA, Vector2(744, AREA.end.y + 64.0), FEATHERS)).is_equal_approx(0.5, 0.001)
	assert_float(CameraFraming.feather(AREA, Vector2(744, AREA.end.y + 128.0), FEATHERS)).is_equal(0.0)
	assert_float(CameraFraming.feather(AREA, Vector2(AREA.end.x + 14.0, 650), FEATHERS)).is_equal_approx(114.0 / 128.0, 0.001)
	assert_float(CameraFraming.feather(AREA, Vector2(AREA.end.x + 128.0, 650), FEATHERS)).is_equal(0.0)
	assert_float(CameraFraming.feather(AREA, Vector2(AREA.end.x + 14.0, 650))).is_equal_approx(50.0 / 64.0, 0.001)   # the default 64
	var f := _framing()
	for y: float in [600.0, 650.0, 696.0]:
		assert_float(f.hint_at(Vector2(744, y)).get("w", 0.0)).is_equal(1.0)
	for y: float in [824.0, 900.0]:
		assert_bool(f.hint_at(Vector2(744, y)).is_empty()).is_true()
	for x: float in [568.0, 744.0, 906.0, 920.0]:
		assert_float(f.hint_at(Vector2(x, 650)).get("w", 0.0)).is_equal(1.0)

func _walk(f: CameraFraming, reduced: bool, from: Vector2, to: Vector2, look := Vector2.ZERO, speed := 150.0,
		avoid: Array = []) -> Dictionary:
	# feet walk from `from` to `to` at `speed` texels a second, 60 steps a second, settled first; the largest
	# change of the camera's target centre in one step, as a multiple of the feet's step, and the cuts
	var feet := from
	for i in 90:
		f.step(1.0 / 60.0, feet, feet + LIFT + look, SCREEN, LIMITS, reduced, "", avoid)
	var last: Vector2 = feet + LIFT + look + f.step(1.0 / 60.0, feet, feet + LIFT + look, SCREEN, LIMITS, reduced, "", avoid).offset
	var most := 0.0
	var cuts := 0
	var dir := (to - from).normalized()
	var stride := speed / 60.0
	while feet.distance_to(to) > 0.5:
		feet += dir * minf(stride, feet.distance_to(to))
		var r := f.step(1.0 / 60.0, feet, feet + LIFT + look, SCREEN, LIMITS, reduced, "", avoid)
		var c: Vector2 = feet + LIFT + look + r.offset
		most = maxf(most, c.distance_to(last) / stride)
		cuts += 1 if r.cut else 0
		last = c
	return {"most": most, "cuts": cuts}

func test_crossing_the_edges_moves_the_camera_at_most_two_and_a_half_times_the_feet() -> void:
	# the #523 audits: one step moved the camera up to 186 texels; with the 32-texel feather and a smoothstep,
	# 11 a step under reduced motion; with 128-texel feathers and the weight applied linearly the target
	# centre (the feet's own step included) keeps within 2.5 times the feet
	for reduced: bool in [false, true]:
		for leg: Array in [[Vector2(744, 650), Vector2(744, 900)], [Vector2(744, 900), Vector2(744, 650)],
				[Vector2(860, 680), Vector2(1080, 680)], [Vector2(1080, 680), Vector2(860, 680)],
				[Vector2(640, 650), Vector2(420, 650)]]:
			var m := _walk(_framing(), reduced, leg[0], leg[1])
			print("CROSS reduced=%s %s -> %s: the target centre moved at most %.2f times the feet's step, %d cuts" % [
				reduced, leg[0], leg[1], m.most, m.cuts])
			assert_float(float(m.most)).is_less_equal(2.5)
			assert_int(int(m.cuts)).is_equal(0)

func test_walking_in_from_the_lane_looking_east_brings_the_hud_bound_in_without_a_jump() -> void:
	# the bound comes in with the weight (full from CAP_FULL), so entering the east feather with the look fully
	# east moves the target centre at most 5 times the feet's step (about 12 texels at a run), not the bound's
	# whole width (up to about 250 texels) at once. The fastest the camera moves in this patch: the cost of
	# the cupola being clear of the tracker from weight 0.5 up.
	var avoid := [TRACKER, HEARTS]
	for reduced: bool in [false, true]:
		for y: float in [600.0, 640.0]:
			var m := _walk(_framing(), reduced, Vector2(1080, y), Vector2(880, y), Vector2(144, 0), 150.0, avoid)
			print("ENTER reduced=%s y %s: the target centre moved at most %.2f times the feet's step" % [reduced, y, m.most])
			assert_float(float(m.most)).is_less_equal(5.0)

func test_a_block_that_starts_or_ends_while_framed_cuts_under_reduced_motion() -> void:
	var f := _framing()
	var feet := Vector2(744, 650)
	_step(f, feet, 1.0 / 60.0, true)
	assert_bool(_step(f, feet, 1.0 / 60.0, true).cut).is_false()
	for reason: String in ["input off", "downed", "raid", "fight"]:
		assert_bool(_step(f, feet, 1.0 / 60.0, true, reason).cut).override_failure_message(reason).is_true()
		assert_bool(_step(f, feet, 1.0 / 60.0, true, reason).cut).is_false()      # once
		assert_bool(_step(f, feet, 1.0 / 60.0, true).cut).is_true()                  # and once back
	# at the feather's south end the weight is small: a block there cuts too (weight above 0)
	var g := _framing()
	var low := Vector2(744, AREA.end.y + 120.0)
	_step(g, low, 1.0 / 60.0, true)
	assert_float(g.weight).is_greater(0.0)
	assert_float(g.weight).is_less(CameraFraming.CUT_STEP)
	assert_bool(_step(g, low, 1.0 / 60.0, true, "fight").cut).is_true()
	# out of the area a block changes nothing and cuts nothing
	var h := _framing()
	assert_bool(_step(h, Vector2(744, 900), 1.0 / 60.0, true, "fight").cut).is_false()
	assert_bool(_step(h, Vector2(744, 900), 1.0 / 60.0, true).cut).is_false()

func _cupola_at(c: Vector2) -> Rect2:
	return Rect2(CUPOLA.position - (c - SCREEN / 2.0), CUPOLA.size)

func _sweep(feet: Vector2, avoid: Array) -> Dictionary:
	# framed and settled at `feet`, the aim swings east from none to the full look-ahead (game.gd LOOK_MAX,
	# 144 texels) over 60 steps; the centre each step, with and without the HUD bound
	var f := _framing()
	for i in 90:
		f.step(1.0 / 60.0, feet, feet + LIFT, SCREEN, LIMITS, false, "", avoid)
	var centres: Array = []
	var plain: Array = []
	var g := _framing()
	for i in 90:
		g.step(1.0 / 60.0, feet, feet + LIFT, SCREEN, LIMITS, false, "")
	for i in 61:
		var look := Vector2(144.0 * i / 60.0, 0)
		var c0 := feet + LIFT + look
		centres.append(c0 + f.step(1.0 / 60.0, feet, c0, SCREEN, LIMITS, false, "", avoid).offset)
		plain.append(c0 + g.step(1.0 / 60.0, feet, c0, SCREEN, LIMITS, false, "").offset)
	return {"centres": centres, "plain": plain, "weight": f.weight}

func test_the_aim_swung_east_moves_the_centre_steadily_and_keeps_the_cupola_clear() -> void:
	# the #523 round-2 audit: at feet (934, 599) the choice between beside and below flipped as the look
	# grew, 93 texels in x and 92 in y within 0.2 s
	var avoid := [TRACKER, HEARTS]
	var spots: Array = [Vector2(934, 599)]
	for y in range(440, 611, 10):
		spots.append(Vector2(930, y))
	for feet: Vector2 in spots:
		var sw := _sweep(feet, avoid)
		var cs: Array = sw.centres
		var most := 0.0
		for i in range(1, cs.size()):
			var dx: float = cs[i].x - cs[i - 1].x
			assert_float(dx).override_failure_message("feet %s step %d: x went back %.2f" % [feet, i, dx]).is_greater_equal(-0.001)
			most = maxf(most, dx)
			# the bound moves nothing in y
			assert_float(cs[i].y).is_equal_approx(sw.plain[i].y, 0.001)
		assert_float(most).is_less_equal(144.0 / 60.0 + 0.001)      # never faster than the look itself
		if feet == spots[0]:
			print("SWEEP feet %s weight %.2f: centre x %.1f -> %.1f, most %.2f a step; cupola at the end %s" % [
				feet, sw.weight, cs[0].x, cs[-1].x, most, _cupola_at(cs[-1])])
		# wherever the weight is at least CAP_FULL, the cupola is MARGIN clear of the tracker all the way
		if sw.weight >= CameraFraming.CAP_FULL:
			for c: Vector2 in cs:
				for r: Rect2 in avoid:
					assert_bool(_cupola_at(c).intersects(r.grow(CameraFraming.MARGIN - 0.01))).override_failure_message(
						"feet %s: the cupola at %s is under %s" % [feet, _cupola_at(c), r]).is_false()

func test_at_partial_weight_the_cupola_stays_clear_of_the_tracker() -> void:
	# the round-2 audit: at partial weight the blend let the vane under the tracker. Weights 0.5 and 0.78
	# held (a step of no time), the aim fully east, at the library's door and at the lane's mouth
	var avoid := [TRACKER, HEARTS]
	for w: float in [0.5, 0.78]:
		for feet: Vector2 in [Vector2(744, 650), Vector2(906, 660), Vector2(920, 620)]:
			var f := _framing()
			f.rect = CUPOLA
			f.weight = w
			var c0 := feet + LIFT + Vector2(144, 0)
			var r := f.step(0.0, feet, c0, SCREEN, LIMITS, false, "talk", avoid)    # a talk holds the weight
			var c: Vector2 = c0 + r.offset
			for p: Rect2 in avoid:
				assert_bool(_cupola_at(c).intersects(p.grow(CameraFraming.MARGIN - 0.01))).override_failure_message(
					"w %s feet %s: the cupola at %s is under %s" % [w, feet, _cupola_at(c), p]).is_false()
			assert_bool(_feet_safe(c, feet)).is_true()

func test_the_bound_follows_the_tracker_width_a_texel_at_a_time() -> void:
	var c1 := CameraFraming.hud_cap_x(CUPOLA, SCREEN, [Rect2(8, 33, 231, 58)])
	var c2 := CameraFraming.hud_cap_x(CUPOLA, SCREEN, [Rect2(8, 33, 232, 80)])    # one texel wider, wrapped taller
	assert_float(c1 - c2).is_equal_approx(1.0, 0.001)
	assert_float(c1).is_equal_approx(717.0 + 480.0 - (239.0 + CameraFraming.MARGIN), 0.001)
	# pieces on the right half (the Glint count, the pause button) set no bound
	assert_float(CameraFraming.hud_cap_x(CUPOLA, SCREEN, [Rect2(930, 27, 22, 22)])).is_equal(INF)

func test_the_crossroads_hint_names_both_cupola_pictures() -> void:
	var defs := CameraFraming.load_defs()
	var hs: Array = defs.get("crossroads", [])
	assert_int(hs.size()).is_equal(1)
	assert_array(hs[0].frame).contains_exactly(["Props/If_cupola_empty/CupolaEmpty", "Props/If_cupola_hung/CupolaHung"])
	var area: Array = hs[0].area
	assert_vector(Vector2(area[0], area[1])).is_equal(AREA.position)
	assert_vector(Vector2(area[2], area[3])).is_equal(AREA.size)
	assert_array(hs[0].feather.map(func(v: Variant) -> float: return float(v))).is_equal(FEATHERS)

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
	# a talk opens: the framing holds (the look-ahead is held at zero for a talk as before)
	Dialogue.busy = true
	await _settle(g, Vector2(744, 650))
	assert_float(g.framing.weight).is_equal(1.0)
	assert_bool(Rect2(Vector2.ZERO, SCREEN).encloses(_cupola_on_screen(path))).is_true()
	Dialogue.busy = false
	# the input off (the raid's prepare screen): it eases out
	g.player.input_enabled = false
	await _settle(g, Vector2(744, 650))
	g.player.input_enabled = true
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

func test_in_crossroads_looking_east_at_the_lane_keeps_the_cupola_clear_of_the_tracker() -> void:
	SaveGame.reset()
	var g := _game()
	Zones.go_to("crossroads", "start")
	g.player.use_mouse_aim = false
	g.player.aim = Vector2.RIGHT
	await _settle(g, Vector2(906, 660), 120)
	var panels: Array[Rect2] = g.hud.top_panels()
	assert_bool(panels.is_empty()).is_false()
	var on := _cupola_on_screen("Props/If_cupola_empty/CupolaEmpty")
	print("EAST cupola at %s, panels %s, camera centre %s" % [on, panels, (g.get_node("Camera2D") as Camera2D).get_screen_center_position()])
	assert_bool(Rect2(Vector2.ZERO, SCREEN).grow(-4.0).encloses(on)).is_true()
	for r: Rect2 in panels:
		assert_bool(on.intersects(r)).override_failure_message("the cupola at %s is under %s" % [on, r]).is_false()
	Zones.current = null

func test_in_crossroads_walking_across_the_south_edge_moves_the_drawn_camera_smoothly() -> void:
	# the drawn Camera2D, frame by frame, as Bramble runs (150 texels a second) from the door to the square and back:
	# within 2.5 times the feet's step and a texel of rounding
	for reduced: bool in [false, true]:
		SaveGame.reset()
		SaveGame.data.settings.reduced_motion = reduced
		var g := _game()
		Zones.go_to("crossroads", "start")
		var cam := g.get_node("Camera2D") as Camera2D
		g.player.use_mouse_aim = false
		g.player.aim = Vector2.ZERO
		await _settle(g, Vector2(744, 650), 90)
		var most := 0.0
		var last := cam.get_screen_center_position()
		for leg: Array in [[650.0, 900.0], [900.0, 650.0]]:
			var y: float = leg[0]
			var dy := 2.5 if leg[1] > leg[0] else -2.5
			while absf(y - leg[1]) > 1.0:
				y += dy
				g.player.global_position = Vector2(744, y)
				await get_tree().physics_frame
				await get_tree().process_frame
				var c := cam.get_screen_center_position()
				most = maxf(most, absf(c.y - last.y))
				last = c
		print("DRAWN reduced=%s: the camera's centre moved at most %.1f texels in one frame (the feet 2.5)" % [reduced, most])
		assert_float(most).is_less_equal(2.5 * 2.5 + 1.0)
		SaveGame.data.settings.reduced_motion = false
		Zones.current = null
