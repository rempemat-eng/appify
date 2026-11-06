extends GdUnitTestSuite

func test_launches_match_pinned_original_engine_across_all_kits_and_forms() -> void:
	var fixture := AbilityCatalogue.read_json("res://test/combat/projectile-oracle.json")
	assert_int(fixture.cases.size()).is_equal(68)
	for case in fixture.cases:
		var release := {"action": case.action, "powered_at_release": case.powered, "rounds": case.rounds}
		var actual := AbilityProjectiles.plan(case.id, release, Vector2(86, 98),
			Vector2.from_angle(case.angle), Vector2(86 + case.distance, 98), case.height)
		assert_int(actual.size()).override_failure_message(str(case)).is_equal(case.expected.size())
		for i in actual.size():
			for key in case.expected[i]:
				var expected = case.expected[i][key]
				if key in ["position", "velocity"]:
					assert_vector(actual[i][key]).is_equal_approx(Vector2(expected[0], expected[1]), Vector2(0.0001, 0.0001))
				elif expected is float:
					assert_float(float(actual[i][key])).is_equal_approx(expected, 0.0001)
				else:
					assert_that(actual[i][key]).is_equal(expected)

func test_launch_uses_live_release_form_and_keeps_it_after_form_ends() -> void:
	var runner := AbilityRunner.new()
	runner.configure("bramble")
	runner.clock.powered_remaining = 0.2
	runner.commit("primary")
	runner.advance(0.1596)
	var commands := runner.drain_release_commands()
	var shots := AbilityProjectiles.plan("bramble", commands[0], Vector2.ZERO, Vector2.RIGHT, Vector2(100, 0))
	runner.advance(1.0)
	assert_bool(runner.clock.is_powered()).is_false()
	assert_bool(shots[0].powered).is_true()
	assert_int(shots[0].pierce).is_equal(3)
	# Returned mutable state must not be shared with another launch or the catalogue.
	shots[0].hit_ids.append(9)
	var again := AbilityProjectiles.plan("bramble", commands[0], Vector2.ZERO, Vector2.RIGHT, Vector2(100, 0))
	assert_int(again[0].hit_ids.size()).is_equal(0)

func test_actual_partial_fan_release_keeps_two_centred_shots_without_double_consumption() -> void:
	var runner := AbilityRunner.new()
	runner.configure("pendle")
	runner.resources.ammo = 2
	runner.commit("secondary")
	runner.advance(0.1824)
	var shots := AbilityProjectiles.plan("pendle", runner.drain_release_commands()[0], Vector2.ZERO,
		Vector2.RIGHT, Vector2(100, 0))
	assert_int(shots.size()).is_equal(2)
	assert_float(shots[0].velocity.y).is_equal_approx(-shots[1].velocity.y, 0.0001)
	assert_int(runner.resources.ammo).is_equal(0)
	assert_float(runner.resources.reload_remaining).is_equal_approx(1.4, 0.000001)

func test_mote_powered_idle_and_special_create_no_autonomous_shards() -> void:
	for action in ["idle", "special", "secondary"]:
		assert_int(AbilityProjectiles.plan("mote", {"action": action, "powered_at_release": true},
			Vector2.ZERO, Vector2.RIGHT, Vector2.ONE).size()).is_equal(0)
	var shots := AbilityProjectiles.plan("mote", {"action": "primary", "powered_at_release": true},
		Vector2.ZERO, Vector2.RIGHT, Vector2.ONE)
	assert_int(shots.size()).is_equal(5)
	assert_str(shots[3].kind).is_equal("orbit-shard")
	assert_str(shots[4].kind).is_equal("orbit-shard")

func test_airborne_height_is_separate_from_ground_origin_and_manifest_anchor() -> void:
	var shot: Dictionary = AbilityProjectiles.plan("rook", {"action": "primary"}, Vector2(10, 20),
		Vector2.RIGHT, Vector2(100, 20), 40.0)[0]
	assert_vector(shot.position).is_equal(Vector2(19, 20))
	assert_float(shot.launch_height).is_equal(40.0)
	assert_float(shot.velocity.length()).is_equal(220.0)

func test_no_projectiles_for_unknown_kit_or_non_projectile_action() -> void:
	assert_int(AbilityProjectiles.plan("unknown", {"action": "primary"}, Vector2.ZERO,
		Vector2.RIGHT, Vector2.ONE).size()).is_equal(0)
	assert_int(AbilityProjectiles.plan("pendle", {"action": "secondary", "powered_at_release": true},
		Vector2.ZERO, Vector2.RIGHT, Vector2.ONE).size()).is_equal(0)
