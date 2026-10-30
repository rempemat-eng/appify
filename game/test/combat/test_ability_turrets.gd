extends GdUnitTestSuite

func _decode(value: Variant) -> Variant:
	if value is Dictionary:
		if value.size() == 1 and value.has("__f64le"):
			return str(value.__f64le).hex_decode().decode_double(0)
		var result := {}
		for key in value:
			result[key] = _decode(value[key])
		return result
	if value is Array:
		return value.map(_decode)
	return value

func _fixture() -> Dictionary:
	return _decode(AbilityCatalogue.read_json("res://test/combat/turret-oracle.json"))

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

func test_turret_phase_matches_original() -> void:
	var fixture := _fixture()
	assert_int(fixture.cases.size()).is_greater(100)
	for index in fixture.cases.size():
		var case: Dictionary = fixture.cases[index]
		var initial := _restore(fixture.baseline, case.initial)
		var before := initial.duplicate(true)
		var expected := _restore(initial, case.expected)
		var result := initial.duplicate(true)
		for tick in int(case.ticks):
			result = AbilityTurrets.tick(result)
		_compare(result, expected, "turret%d" % index)
		assert_that(initial).override_failure_message("input unchanged %d" % index).is_equal(before)

func test_no_designation_means_no_autonomous_shot() -> void:
	var fixture := _fixture()
	var state: Dictionary = fixture.baseline.duplicate(true)
	state.player.designatedId = null
	for turret in state.turrets:
		turret.cooldown = 0.0
	var result := AbilityTurrets.tick(state)
	assert_array(result.projectiles).is_empty()
	assert_that(result.turrets[0].targetId).is_null()
	assert_float(result.turrets[0].aimX).is_equal(float(state.player.aimX))

func test_final_turret_tick_fires_then_removes() -> void:
	var fixture := _fixture()
	var state: Dictionary = fixture.baseline.duplicate(true)
	for turret in state.turrets:
		turret.remaining = 0.001
		turret.cooldown = 0.0
	var result := AbilityTurrets.tick(state)
	assert_array(result.turrets).is_empty()
	assert_int(result.projectiles.size()).is_equal(2)
	assert_float(float(result.projectiles[0].age)).is_zero()
	assert_float(float(result.projectiles[0].remaining)).is_equal(1.0)

func test_phase_does_not_advance_player_or_world_clocks() -> void:
	var fixture := _fixture()
	var state: Dictionary = fixture.baseline.duplicate(true)
	var result := AbilityTurrets.tick(state)
	for key in ["time", "tick", "player", "enemies", "fields", "effects", "statistics", "events"]:
		assert_that(result[key]).is_equal(state[key])

func test_oracle_decodes_exact_double_at_expiry_boundary() -> void:
	var fixture := _fixture()
	var state := _restore(fixture.baseline, fixture.cases[81].initial)
	assert_bool(float(state.turrets[0].remaining) - 1.0/60.0 > AbilityTurrets.EPSILON).is_true()
	assert_int(AbilityTurrets.tick(state).turrets.size()).is_equal(2)
