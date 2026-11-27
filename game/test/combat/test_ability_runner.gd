extends GdUnitTestSuite

func _runner(id: String) -> AbilityRunner:
	var r := AbilityRunner.new()
	assert_bool(r.configure(id)).is_true()
	return r

func test_each_kit_release_once_and_cancel_before_contact_costs_nothing() -> void:
	for id in AbilityCatalogue.IDS:
		var r := _runner(id)
		var ammo := r.resources.ammo
		r.commit("primary")
		r.advance(0.001)
		r.cancel()
		r.advance(3.0)
		assert_int(r.drain_release_commands().size()).is_equal(0)
		assert_int(r.resources.ammo).is_equal(ammo)
		r.commit("primary")
		r.advance(3.0)
		assert_int(r.drain_release_commands().size()).is_equal(1)
		r.advance(3.0)
		assert_int(r.drain_release_commands().size()).is_equal(0)

func test_pendle_held_fire_coarse_and_fine_agree_across_reload() -> void:
	var coarse := _runner("pendle")
	var fine := _runner("pendle")
	coarse.input(true, false, false, false)
	fine.input(true, false, false, false)
	coarse.advance(7.123)
	for i in 7123:
		fine.advance(0.001)
	var a := coarse.drain_release_commands()
	var b := fine.drain_release_commands()
	assert_int(a.size()).is_equal(b.size())
	assert_bool(a.size() > 6).is_true()
	assert_int(coarse.resources.ammo).is_equal(fine.resources.ammo)
	assert_float(coarse.resources.reload_remaining).is_equal_approx(fine.resources.reload_remaining, 0.00001)
	for i in a.size():
		assert_int(a[i].instance).is_equal(b[i].instance)
		assert_int(a[i].rounds).is_equal(1)

func test_partial_fan_consumes_available_rounds_at_contact_only() -> void:
	var r := _runner("pendle")
	r.resources.ammo = 2
	r.commit("secondary")
	assert_int(r.resources.ammo).is_equal(2)
	r.advance(float(AbilityCatalogue.action("pendle", "secondary").release_seconds))
	var commands := r.drain_release_commands()
	assert_int(commands.size()).is_equal(1)
	assert_int(commands[0].rounds).is_equal(2)
	assert_int(r.resources.ammo).is_equal(0)
	assert_float(r.resources.reload_remaining).is_equal_approx(1.4, 0.000001)

func test_form_expiry_during_preparation_uses_live_release_state() -> void:
	var r := _runner("pendle")
	r.clock.powered_remaining = 0.01
	r.resources.ammo = 2
	r.commit("primary")
	r.advance(0.4)
	var commands := r.drain_release_commands()
	assert_int(commands.size()).is_equal(1)
	assert_bool(commands[0].powered_at_commit).is_true()
	assert_bool(commands[0].powered_at_release).is_false()
	assert_int(r.resources.ammo).is_equal(1)

func test_nix_idle_cooling_boundary_retries_held_input_without_frame_delay() -> void:
	var coarse := _runner("nix")
	var fine := _runner("nix")
	for r in [coarse, fine]:
		r.resources.heat = 100.0
		r.input(true, false, false, false)
		assert_int(r.clock.instance).is_equal(0)
	coarse.advance(2.123)
	for i in 2123:
		fine.advance(0.001)
	var a := coarse.drain_release_commands()
	var b := fine.drain_release_commands()
	assert_bool(a.size() > 0).is_true()
	assert_int(a.size()).is_equal(b.size())
	assert_float(coarse.resources.heat).is_equal_approx(fine.resources.heat, 0.00001)
	assert_int(coarse.clock.instance).is_equal(fine.clock.instance)

func test_special_caps_heat_at_contact_and_cools_using_each_interval_state() -> void:
	var r := _runner("nix")
	r.resources.heat = 100.0
	r.commit("special")
	r.advance(0.8)
	# 0.28s ordinary cooling precedes contact, then cap45 and 0.52s powered cooling7.
	assert_float(r.resources.heat).is_equal_approx(41.36, 0.000001)
	assert_float(r.clock.powered_remaining).is_equal_approx(6.48, 0.000001)
	assert_int(r.drain_release_commands().size()).is_equal(1)

func test_inactive_time_freezes_both_components_and_reconfigure_clears_commands() -> void:
	var r := _runner("clack")
	r.commit("primary")
	r.advance(0.4)
	var pending := r.resources.reload_remaining
	var elapsed := r.clock.elapsed
	r.advance(100.0, false)
	assert_float(r.resources.reload_remaining).is_equal(pending)
	assert_float(r.clock.elapsed).is_equal(elapsed)
	assert_bool(r.configure("nix")).is_true()
	assert_int(r.drain_release_commands().size()).is_equal(0)
	assert_float(r.resources.heat).is_equal(0.0)
	assert_bool(r.commit("primary")).is_true()
	r.advance(0.4)
	assert_int(r.drain_release_commands().size()).is_equal(1)
