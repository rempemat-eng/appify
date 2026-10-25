extends GdUnitTestSuite

func _resources(id: String) -> AbilityResources:
	var r := AbilityResources.new()
	assert_bool(r.configure(id)).is_true()
	return r

func test_all_kits_start_with_canonical_resources_and_special_available() -> void:
	for id in AbilityCatalogue.IDS:
		var r := _resources(id)
		assert_bool(r.eligible("primary", false)).is_true()
		assert_bool(r.eligible("secondary", false)).is_true()
		assert_bool(r.eligible("special", false)).is_true()
		assert_bool(r.eligible("unknown", false)).is_false()

func test_pendle_six_shots_then_exact_reload_boundary() -> void:
	var r := _resources("pendle")
	for i in 6:
		assert_bool(r.eligible("primary", false)).is_true()
		assert_int(r.release("primary", false)).is_equal(1)
	assert_int(r.ammo).is_equal(0)
	assert_bool(r.eligible("secondary", false)).is_false()
	r.advance(1.3499, "", false)
	assert_bool(r.eligible("primary", false)).is_false()
	r.advance(0.0001, "", false)
	assert_int(r.ammo).is_equal(6)
	assert_bool(r.eligible("primary", false)).is_true()

func test_pendle_partial_fan_and_powered_stock_preserve_reload() -> void:
	var r := _resources("pendle")
	for i in 4:
		r.release("primary", false)
	assert_int(r.release("secondary", false)).is_equal(2)
	assert_float(r.reload_remaining).is_equal(1.4)
	r.release("special", false)
	assert_int(r.ammo).is_equal(0)
	assert_float(r.reload_remaining).is_equal(1.4)
	assert_bool(r.eligible("primary", true)).is_true()
	assert_bool(r.eligible("secondary", true)).is_true()
	assert_int(r.release("secondary", true)).is_equal(0)
	assert_int(r.release("primary", true)).is_equal(1)
	assert_int(r.ammo).is_equal(0)
	assert_float(r.reload_remaining).is_equal(1.4)

func test_brine_and_clack_reload_and_activation_rules() -> void:
	for id in ["brine", "clack"]:
		var r := _resources(id)
		r.release("primary", false)
		assert_bool(r.eligible("primary", false)).is_false()
		assert_bool(r.eligible("secondary", false)).is_true()
		var pending := r.reload_remaining
		r.release("secondary", false)
		assert_float(r.reload_remaining).is_equal(pending)
		r.release("special", false)
		assert_int(r.ammo).is_equal(1)
		assert_float(r.reload_remaining).is_equal(0.0)
		assert_int(r.release("primary", true)).is_equal(3 if id == "clack" else 1)
		assert_float(r.reload_remaining).is_equal(0.7 if id == "clack" else 0.52)
		r.advance(5.0, "", false)
		assert_int(r.ammo).is_equal(1)

func test_nix_threshold_and_three_passive_rates() -> void:
	var r := _resources("nix")
	r.heat = 92.0
	assert_bool(r.eligible("primary", false)).is_false()
	assert_bool(r.eligible("secondary", false)).is_true()
	r.release("secondary", false)
	assert_float(r.heat).is_equal(92.0)
	r.advance(0.1, "primary", false)
	assert_float(r.heat).is_equal_approx(91.6, 0.000001)
	assert_bool(r.eligible("primary", false)).is_true()
	r.release("primary", false)
	assert_float(r.heat).is_equal(100.0)
	r.advance(1.0, "secondary", true)
	assert_float(r.heat).is_equal(93.0)
	r.advance(1.0, "secondary", false)
	assert_float(r.heat).is_equal(78.0)
	r.release("special", false)
	assert_float(r.heat).is_equal(45.0)
	r.release("primary", true)
	assert_float(r.heat).is_equal(57.0)
	r.advance(100.0, "", false)
	assert_float(r.heat).is_equal(0.0)

func test_inactive_time_freezes_reload_heat_and_reconfigure_resets() -> void:
	var r := _resources("clack")
	r.release("primary", false)
	r.advance(100.0, "", false, false)
	assert_float(r.reload_remaining).is_equal(1.15)
	r.configure("nix")
	r.heat = 80.0
	r.advance(100.0, "", true, false)
	assert_float(r.heat).is_equal(80.0)
	assert_float(r.reload_remaining).is_equal(0.0)

func test_resource_rejection_cannot_consume_clock_cooldown_or_token() -> void:
	var r := _resources("nix")
	var c := AbilityClock.new()
	c.configure("nix")
	c.can_commit = r.eligible
	r.heat = 92.0
	assert_bool(c.commit("primary")).is_false()
	assert_float(c.cooldowns.primary).is_equal(0.0)
	assert_int(c.instance).is_equal(0)
	assert_int(c.drain_events().size()).is_equal(0)
	r.advance(0.1, "", false)
	assert_bool(c.commit("primary")).is_true()
	# Preparation cancellation consumes neither ammo nor heat: only release() mutates them.
	c.cancel()
	assert_float(r.heat).is_equal(90.5)
