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
	return _decode(AbilityCatalogue.read_json("res://test/combat/defence-oracle.json"))

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

func test_defence_and_enemy_projectiles_match_original() -> void:
	var fixture := _fixture()
	assert_int(fixture.cases.size()).is_greater(400)
	for index in fixture.cases.size():
		var case: Dictionary = fixture.cases[index]
		var initial := _restore(fixture.baseline, case.initial)
		var before := initial.duplicate(true)
		var expected := _restore(initial, case.expected)
		var result := initial.duplicate(true)
		for tick in int(case.ticks):
			if case.op == "damage":
				result = AbilityDefence.damage(result, case.args[0], case.args[1], case.args[2],
					case.args[3] if case.args.size() > 3 else "projectile")
			else:
				result = AbilityProjectilePhase.tick(result)
		_compare(result, expected, "defence%d/%s" % [index, case.label])
		assert_that(initial).override_failure_message("input unchanged %d" % index).is_equal(before)

func test_full_absorption_preserves_queued_action_and_primes_counter() -> void:
	var state: Dictionary = _fixture().baseline.duplicate(true)
	state.player.id = "velvet"
	state.player.specialRemaining = 4
	state.player.blocking = true
	state.queuedAction = "secondary"
	state.queueRemaining = 0.5
	var result := AbilityDefence.damage(state, 10, 130, 98)
	assert_float(float(result.player.hp)).is_equal(160.0)
	assert_float(float(result.player.counterRemaining)).is_equal(2.0)
	assert_str(result.queuedAction).is_equal("secondary")

func test_decoy_break_does_not_absorb_enemy_projectile() -> void:
	var fixture := _fixture()
	for case in fixture.cases:
		if case.label == "mixed-decoy":
			var state := _restore(fixture.baseline, case.initial)
			if state.player.id != "bramble" or state.player.hp != 160 or state.player.blocking or state.fields.size() != 2:
				continue
			var result := AbilityProjectilePhase.tick(state)
			assert_float(float(result.player.hp)).is_equal(136.0)
			assert_float(float(result.fields[0].remaining)).is_equal(0.0)
			assert_float(float(result.fields[1].remaining)).is_equal(0.0)
			return
	fail("Missing decoy fixture")
