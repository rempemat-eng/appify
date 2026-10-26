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

func test_all_impact_damage_field_and_reaction_snapshots_match_original() -> void:
	var fixture := AbilityCatalogue.read_json("res://test/combat/impact-oracle.json")
	assert_int(fixture.cases.size()).is_greater(150)
	for index in fixture.cases.size():
		var case: Dictionary = fixture.cases[index]
		var initial := _restore(fixture.baseline, case.initial)
		var before: Dictionary = initial.duplicate(true)
		var expected := _restore(initial, case.expected)
		var args: Variant = case.args
		var result := {}
		match case.operation:
			"impact": result = AbilityImpacts.impact(initial, args.shot, args.target_id)
			"damage": result = AbilityImpacts.damage(initial, args.target_id, args.amount, args.knockback)
			"field": result = AbilityImpacts.field(initial, args[0], args[1], args[2], args[3], args[4], args[5])
			"react": result = AbilityImpacts.react(initial, args.ids, args.chained)
		_compare(result, expected, "case%d/%s" % [index, case.operation])
		assert_that(initial).override_failure_message("input unchanged %d" % index).is_equal(before)

func test_missing_target_does_not_invent_damage_or_status() -> void:
	var fixture := AbilityCatalogue.read_json("res://test/combat/impact-oracle.json")
	var case: Dictionary = fixture.cases[0]
	var initial := _restore(fixture.baseline, case.initial)
	var shot: Dictionary = case.args.shot.duplicate(true)
	shot.kind = "water"
	shot.blastRadius = 0
	assert_that(AbilityImpacts.impact(initial, shot, 9999)).is_equal(initial)
	assert_that(AbilityImpacts.damage(initial, 9999, 22)).is_equal(initial)
