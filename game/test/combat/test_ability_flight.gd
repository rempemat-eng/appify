extends GdUnitTestSuite

func _shot(id := "bramble", powered := false) -> Dictionary:
	return AbilityProjectiles.plan(id, {"action": "primary", "powered_at_release": powered},
		Vector2(86, 98), Vector2.RIGHT, Vector2(200, 98))[0]

func _target(id: int, point: Vector2, radius := 1.0, hp := 100.0) -> Dictionary:
	return {"id": id, "position": point, "radius": radius, "hp": hp}

func test_free_flight_matches_all_original_launches_without_mutating_input() -> void:
	var cases: Array = AbilityCatalogue.read_json("res://test/combat/flight-oracle.json").cases
	assert_int(cases.size()).is_greater(50)
	for case in cases:
		var shot: Dictionary = case.initial.duplicate(true)
		shot.position = Vector2(shot.position[0], shot.position[1])
		shot.velocity = Vector2(shot.velocity[0], shot.velocity[1])
		var result := {}
		for i in int(case.ticks):
			var before := shot.duplicate(true)
			result = AbilityFlight.tick(shot)
			assert_that(shot).is_equal(before)
			if not result.alive:
				break
			shot = result.shot
		assert_bool(result.alive).is_equal(case.alive)
		# Vector2 is float32: <=120 repeated steps versus JS double accumulate <0.001 units.
		assert_vector(result.shot.position).is_equal_approx(Vector2(case.position[0], case.position[1]), Vector2(0.001, 0.001))
		assert_float(result.shot.age).is_equal_approx(case.age, 0.000001)
		assert_float(result.shot.remaining).is_equal_approx(case.remaining, 0.000001)

func test_swept_contact_prevents_tunnelling_and_preserves_previous_hit_ids() -> void:
	var shot := _shot("bramble", true)
	shot.velocity = Vector2(6000, 0)
	var targets: Array[Dictionary] = [_target(2, Vector2(170, 98)), _target(1, Vector2(120, 98)), _target(3, Vector2(140, 98), 1.0, 0.0)]
	var result := AbilityFlight.tick(shot, targets)
	assert_int(result.events.size()).is_equal(2)
	assert_int(result.events[0].target_id).is_equal(1)
	assert_int(result.events[1].target_id).is_equal(2)
	assert_array(result.events[0].shot.hit_ids).is_empty()
	assert_array(result.events[1].shot.hit_ids).contains_exactly([1])
	assert_array(shot.hit_ids).is_empty()
	assert_int(result.shot.pierce).is_equal(1)
	var next := AbilityFlight.tick(result.shot, targets)
	assert_array(next.events).is_empty()

func test_nonpiercing_impact_consumes_without_second_expiry_blast() -> void:
	var shot := _shot("clack")
	shot.remaining = 0.001
	var targets: Array[Dictionary] = [_target(7, shot.position)]
	var result := AbilityFlight.tick(shot, targets)
	assert_bool(result.alive).is_false()
	assert_int(result.events.size()).is_equal(1)
	assert_int(result.events[0].target_id).is_equal(7)
	assert_vector(result.events[0].shot.position).is_equal(targets[0].position)

func test_short_last_step_and_bounds_expire_area_projectiles_once() -> void:
	var shot := _shot("morel")
	shot.remaining = 0.001
	var result := AbilityFlight.tick(shot)
	assert_bool(result.alive).is_false()
	assert_float(result.shot.age).is_equal_approx(0.001, 0.000001)
	assert_vector(result.shot.position).is_equal_approx(shot.position + shot.velocity * 0.001, Vector2.ONE * 0.0001)
	assert_int(result.events.size()).is_equal(1)
	assert_that(result.events[0].target_id).is_null()
	shot = _shot()
	shot.position = Vector2(320, 98)
	shot.velocity = Vector2.ZERO
	assert_bool(AbilityFlight.tick(shot).alive).is_true()
	shot.position.x = 320.001
	assert_bool(AbilityFlight.tick(shot).alive).is_false()

func test_seal_before_or_tied_with_target_amplifies_but_later_seal_does_not() -> void:
	var shot := _shot("mirra")
	shot.velocity = Vector2(6000, 0)
	var targets: Array[Dictionary] = [_target(1, Vector2(145, 98))]
	for x in [110.0, 140.0, 180.0]:
		var seals: Array[Dictionary] = [{"position": Vector2(x, 98), "radius": 0.0, "remaining": 1.0}]
		var result := AbilityFlight.tick(shot, targets, seals)
		var amplified: bool = x <= 140.0
		assert_bool(result.shot.get("amplified", false)).is_equal(amplified)
		assert_float(float(result.shot.damage)).is_equal(28.0 if amplified else 21.0)
		assert_bool(result.alive).is_equal(amplified)
		assert_float(float(seals[0].remaining)).is_equal(1.0)

func test_zero_length_sweep_and_already_hit_target_are_safe() -> void:
	var shot := _shot()
	shot.velocity = Vector2.ZERO
	shot.hit_ids = [1]
	var targets: Array[Dictionary] = [_target(1, shot.position), _target(2, shot.position + Vector2(0, 4))]
	assert_array(AbilityFlight.tick(shot, targets).events).is_empty()
	assert_float(AbilityFlight.entry(Vector2.ZERO, Vector2.ZERO, Vector2.ONE, 0.1)).is_equal(INF)
	assert_float(AbilityFlight.entry(Vector2.ZERO, Vector2.ZERO, Vector2.ZERO, 0.1)).is_equal(0.0)

func test_swept_contacts_match_original_engine_impact_snapshots() -> void:
	var fixture := AbilityCatalogue.read_json("res://test/combat/flight-contacts-oracle.json")
	assert_int(fixture.contacts.size()).is_equal(14)
	for case in fixture.contacts:
		var shot: Dictionary = case.initial.duplicate(true)
		shot.position = Vector2(shot.position[0], shot.position[1])
		shot.velocity = Vector2(shot.velocity[0], shot.velocity[1])
		var targets: Array[Dictionary] = []
		for item in case.targets:
			var target: Dictionary = item.duplicate(true)
			target.position = Vector2(item.position[0], item.position[1])
			targets.append(target)
		var seals: Array[Dictionary] = []
		for item in case.seals:
			var seal: Dictionary = item.duplicate(true)
			seal.position = Vector2(item.position[0], item.position[1])
			seals.append(seal)
		var result := AbilityFlight.tick(shot, targets, seals)
		var impacts: Array = result.events.filter(func(e): return e.type == "impact")
		assert_bool(result.alive).is_equal(case.alive)
		assert_int(impacts.size()).is_equal(case.impacts.size())
		assert_vector(result.shot.position).is_equal_approx(Vector2(case.position[0], case.position[1]), Vector2.ONE * 0.0001)
		assert_int(int(result.shot.pierce)).is_equal(int(case.pierce))
		assert_array(result.shot.hit_ids).contains_exactly(case.hit_ids)
		for i in impacts.size():
			assert_that(impacts[i].target_id).is_equal(case.impacts[i].target_id)
			assert_float(float(impacts[i].shot.damage)).is_equal(float(case.impacts[i].damage))
			assert_array(impacts[i].shot.hit_ids).contains_exactly(case.impacts[i].hit_ids)
