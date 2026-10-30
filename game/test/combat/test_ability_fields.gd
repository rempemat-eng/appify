extends GdUnitTestSuite

func _compare(actual: Variant, expected: Variant, path: String) -> void:
	if expected is Dictionary:
		assert_bool(actual is Dictionary).override_failure_message(path).is_true()
		assert_int(actual.size()).override_failure_message(path + " keys").is_equal(expected.size())
		for key in expected:
			assert_bool(actual.has(key)).override_failure_message(path + "." + key).is_true()
			if actual.has(key):
				_compare(actual[key], expected[key], path + "." + key)
	elif expected is Array:
		assert_int(actual.size()).override_failure_message(path + " length").is_equal(expected.size())
		for index in mini(actual.size(), expected.size()):
			_compare(actual[index], expected[index], path + "[%d]" % index)
	elif expected is float or expected is int:
		assert_float(float(actual)).override_failure_message(path).is_equal_approx(float(expected), 0.000001)
	else:
		assert_that(actual).override_failure_message(path).is_equal(expected)

func _restore(base: Dictionary, patch: Dictionary) -> Dictionary:
	var result := base.duplicate(true)
	for key in patch:
		if patch[key] is Dictionary and result.get(key) is Dictionary:
			result[key] = _restore(result[key], patch[key])
		else:
			result[key] = patch[key].duplicate(true) if patch[key] is Array or patch[key] is Dictionary else patch[key]
	return result

func test_field_and_status_phases_match_original() -> void:
	var fixture := AbilityCatalogue.read_json("res://test/combat/field-oracle.json")
	assert_int(fixture.cases.size()).is_greater(200)
	for index in fixture.cases.size():
		var case: Dictionary = fixture.cases[index]
		var initial := _restore(fixture.baseline, case.initial)
		var before: Dictionary = initial.duplicate(true)
		var expected := _restore(initial, case.expected)
		var result := initial.duplicate(true)
		for tick in int(case.ticks):
			match case.operation:
				"fields": result = AbilityFields.tick_fields(result)
				"statuses": result = AbilityFields.tick_statuses(result)
				"phases":
					result.time += 1.0 / 60.0
					result.tick += 1
					result = AbilityFields.tick_fields(AbilityFields.tick_statuses(result))
		_compare(result, expected, "case%d/%s" % [index, case.operation])
		assert_that(initial).override_failure_message("input unchanged %d" % index).is_equal(before)

func test_expiring_field_still_ticks_before_removal() -> void:
	var fixture := AbilityCatalogue.read_json("res://test/combat/field-oracle.json")
	var state: Dictionary = fixture.baseline.duplicate(true)
	state.fields = [{"id": 99, "kind": "flame", "x": 120, "y": 98, "radius": 18,
		"remaining": 0.001, "damage": 8, "tickIn": 0.0, "source": "ashe"}]
	var result := AbilityFields.tick_fields(state)
	assert_array(result.fields).is_empty()
	assert_float(result.enemies[0].hp).is_equal(92.0)
	assert_float(state.enemies[0].hp).is_equal(100.0)

func test_status_phase_does_not_run_legacy_enemy_ai_even_in_live_mode() -> void:
	var fixture := AbilityCatalogue.read_json("res://test/combat/field-oracle.json")
	var state: Dictionary = fixture.baseline.duplicate(true)
	state.mode = "live"
	state.enemies[0].rootRemaining = 0.1
	var result := AbilityFields.tick_statuses(state)
	assert_float(result.enemies[0].rootRemaining).is_equal_approx(0.1 - 1.0/60.0, 0.000001)
	for index in state.enemies.size():
		for key in ["x", "y", "phase", "phaseRemaining", "cooldown", "targetId"]:
			assert_that(result.enemies[index][key]).is_equal(state.enemies[index][key])
