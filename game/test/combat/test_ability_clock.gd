extends GdUnitTestSuite

func _clock(id: String) -> AbilityClock:
	var clock := AbilityClock.new()
	assert_bool(clock.configure(id)).is_true()
	return clock

func _events(events: Array[Dictionary], kind: String) -> Array[Dictionary]:
	return events.filter(func(event: Dictionary) -> bool: return event.kind == kind)

func _release_case(id: String) -> void:
	for name in ["primary", "secondary", "special"]:
		var clock := _clock(id)
		var spec := AbilityCatalogue.action(id, name)
		assert_bool(clock.commit(name)).is_true()
		clock.drain_events()
		clock.advance(float(spec.release_seconds) - 0.0001)
		assert_int(_events(clock.drain_events(), "release").size()).is_equal(0)
		clock.advance(0.0001)
		var released := _events(clock.drain_events(), "release")
		assert_int(released.size()).is_equal(1)
		assert_float(released[0].elapsed).is_equal_approx(float(spec.release_seconds), 0.000001)
		clock.advance(0.01)
		assert_int(_events(clock.drain_events(), "release").size()).is_equal(0)
		# A single overshoot delivers exactly one event, including after animation would finish.
		var coarse := _clock(id)
		coarse.commit(name)
		coarse.advance(float(spec.duration_seconds) + 0.1)
		assert_int(_events(coarse.drain_events(), "release").size()).is_equal(1)
		var powered := _clock(id)
		powered.commit("special")
		powered.advance(0.65)
		if name == "special":
			continue # the same canonical special remains on its 25 s cooldown
		powered.drain_events()
		assert_bool(powered.commit(name)).is_true()
		var powered_spec := AbilityCatalogue.action(id, name, true)
		powered.advance(float(powered_spec.duration_seconds) + 0.01)
		var powered_events := _events(powered.drain_events(), "release")
		assert_int(powered_events.size()).is_equal(1)
		assert_bool(powered_events[0].powered_at_commit).is_true()
		assert_float(powered_events[0].elapsed).is_equal_approx(float(powered_spec.release_seconds), 0.000001)

func test_mixed_steps_and_overshoot_preserve_event_order() -> void:
	var fine := _clock("nix")
	var coarse := _clock("nix")
	fine.input(true, false, false, false)
	coarse.input(true, false, false, false)
	for i in 120:
		fine.advance(1.0 / 60.0)
	coarse.advance(2.0)
	var a := fine.drain_events()
	var b := coarse.drain_events()
	assert_int(a.size()).is_equal(b.size())
	for i in a.size():
		assert_str(a[i].kind).is_equal(b[i].kind)
		assert_int(a[i].instance).is_equal(b[i].instance)

func test_special_starts_cooldown_at_commit_and_form_at_release() -> void:
	var c := _clock("rook")
	c.commit("special")
	assert_float(c.cooldowns.special).is_equal(25.0)
	assert_bool(c.is_powered()).is_false()
	c.advance(0.28)
	assert_bool(c.is_powered()).is_true()
	assert_float(c.powered_remaining).is_equal_approx(10.0, 0.000001)
	c.advance(1.0)
	assert_float(c.powered_remaining).is_equal_approx(9.0, 0.000001)
	assert_float(c.cooldowns.special).is_equal_approx(23.72, 0.000001)

func test_overshoot_does_not_charge_form_for_time_before_its_release() -> void:
	var c := _clock("nix")
	c.commit("special")
	c.advance(0.8)
	assert_float(c.powered_remaining).is_equal_approx(6.48, 0.000001)
	assert_bool(c.commit("special")).is_false()

func test_cancel_before_release_and_restart_never_emits_old_contact() -> void:
	var c := _clock("bramble")
	c.commit("primary")
	c.advance(0.15)
	c.cancel()
	c.advance(0.3)
	assert_int(_events(c.drain_events(), "release").size()).is_equal(0)
	assert_bool(c.commit("primary")).is_true()
	c.advance(0.2)
	var events := _events(c.drain_events(), "release")
	assert_int(events.size()).is_equal(1)
	assert_int(events[0].instance).is_equal(2)

func test_inactive_time_freezes_action_cooldown_queue_and_form() -> void:
	var c := _clock("tam")
	c.commit("special")
	c.advance(0.3)
	var elapsed := c.elapsed
	var form := c.powered_remaining
	var cooldown := float(c.cooldowns.special)
	c.advance(500.0, false)
	assert_float(c.elapsed).is_equal(elapsed)
	assert_float(c.powered_remaining).is_equal(form)
	assert_float(c.cooldowns.special).is_equal(cooldown)

func test_special_wins_simultaneous_edges_and_hold_does_not_requeue() -> void:
	var c := _clock("brine")
	c.input(false, true, true, false)
	assert_str(c.action).is_equal("special")
	c.advance(0.65)
	c.input(false, true, true, false)
	assert_str(c.action).is_equal("")
	c.input(false, false, false, false)
	c.input(false, true, false, false)
	assert_str(c.action).is_equal("secondary")

func test_guard_clears_queue_and_suppresses_held_primary() -> void:
	var c := _clock("clack")
	c.commit("primary")
	c.input(true, true, false, false)
	c.input(true, false, false, true)
	c.advance(1.0)
	assert_str(c.action).is_equal("")
	assert_int(_events(c.drain_events(), "release").size()).is_equal(1)

func test_queued_action_expires_while_current_action_is_busy() -> void:
	var c := _clock("clack")
	c.commit("primary")
	c.input(false, true, false, false)
	c.advance(0.81)
	assert_str(c.action).is_equal("")

func test_natural_and_interrupted_form_end_remain_distinguishable() -> void:
	var c := _clock("ashe")
	c.commit("special")
	c.advance(8.28)
	var natural := _events(c.drain_events(), "powered_off")
	assert_int(natural.size()).is_equal(1)
	assert_str(natural[0].action).is_equal("natural")
	var interrupted := _clock("ashe")
	interrupted.commit("special")
	interrupted.advance(0.3)
	interrupted.end_form("defeat")
	interrupted.advance(10.0)
	var stopped := _events(interrupted.drain_events(), "powered_off")
	assert_int(stopped.size()).is_equal(1)
	assert_str(stopped[0].action).is_equal("defeat")

func test_bramble_canonical_release_boundaries() -> void:
	_release_case("bramble")

func test_morel_canonical_release_boundaries() -> void:
	_release_case("morel")

func test_velvet_canonical_release_boundaries() -> void:
	_release_case("velvet")

func test_cairn_canonical_release_boundaries() -> void:
	_release_case("cairn")

func test_iona_canonical_release_boundaries() -> void:
	_release_case("iona")

func test_tam_canonical_release_boundaries() -> void:
	_release_case("tam")

func test_brine_canonical_release_boundaries() -> void:
	_release_case("brine")

func test_pendle_canonical_release_boundaries() -> void:
	_release_case("pendle")

func test_mirra_canonical_release_boundaries() -> void:
	_release_case("mirra")

func test_ashe_canonical_release_boundaries() -> void:
	_release_case("ashe")

func test_clack_canonical_release_boundaries() -> void:
	_release_case("clack")

func test_nix_canonical_release_boundaries() -> void:
	_release_case("nix")

func test_rook_canonical_release_boundaries() -> void:
	_release_case("rook")

func test_mote_canonical_release_boundaries() -> void:
	_release_case("mote")
