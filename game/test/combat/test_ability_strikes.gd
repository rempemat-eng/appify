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
	return _decode(AbilityCatalogue.read_json("res://test/combat/strike-oracle.json"))

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

func test_strikes_match_original() -> void:
	var fixture := _fixture()
	assert_int(fixture.cases.size()).is_greater(150)
	for index in fixture.cases.size():
		var case: Dictionary = fixture.cases[index]
		var initial := _restore(fixture.baseline, case.initial)
		var before := initial.duplicate(true)
		var expected := _restore(initial, case.expected)
		var result: Dictionary
		var args: Array = case.args
		match case.op:
			"arc": result = AbilityStrikes.arc(initial, args[0], args[1], args[2], args[3])
			"beam": result = AbilityStrikes.beam(initial, args[0], args[1], args[2], args[3], args[4])
			"dash": result = AbilityStrikes.dash(initial, args[0])
		_compare(result, expected, "strike%d/%s" % [index, case.label])
		assert_that(initial).is_equal(before)

func test_equal_distance_beam_hits_first_array_entry() -> void:
	var state: Dictionary = _fixture().baseline.duplicate(true)
	var enemy: Dictionary = state.enemies[0].duplicate(true)
	enemy.x = state.player.x + 20
	enemy.y = state.player.y
	state.enemies = [enemy.duplicate(true), enemy.duplicate(true)]
	state.enemies[0].id = 101
	state.enemies[1].id = 102
	var result := AbilityStrikes.beam(state, 80, 8, 10, false, "beam")
	assert_float(float(result.enemies[0].hp)).is_equal(float(enemy.hp) - 10)
	assert_float(float(result.enemies[1].hp)).is_equal(float(enemy.hp))
