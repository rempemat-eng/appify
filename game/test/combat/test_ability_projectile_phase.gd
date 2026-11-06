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
	return _decode(AbilityCatalogue.read_json("res://test/combat/projectile-phase-oracle.json"))

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

func test_full_player_projectile_phase_matches_original() -> void:
	var fixture := _fixture()
	assert_int(fixture.cases.size()).is_greater(180)
	for index in fixture.cases.size():
		var case: Dictionary = fixture.cases[index]
		var initial := _restore(fixture.baseline, case.initial)
		var before := initial.duplicate(true)
		var expected := _restore(initial, case.expected)
		var result := initial.duplicate(true)
		for tick in int(case.ticks):
			result = AbilityProjectilePhase.tick(result)
		_compare(result, expected, "phase%d" % index)
		assert_that(initial).override_failure_message("input unchanged %d" % index).is_equal(before)

func test_later_projectile_observes_first_shot_kill() -> void:
	var fixture := _fixture()
	var state: Dictionary = fixture.baseline.duplicate(true)
	state.enemies = [state.enemies[0]]
	state.enemies[0].hp = 1
	var shot := {"id": 90, "kind": "arrow", "owner": "player", "source": "bramble",
		"x": 95.0, "y": 98.0, "vx": 6000.0, "vy": 0.0, "radius": 2, "remaining": 1.0,
		"damage": 22, "pierce": 0, "hitIds": [], "blastRadius": 0, "powered": false,
		"launchHeight": 0, "age": 0.0, "flightDuration": 1.0}
	state.projectiles = [shot, shot.duplicate(true)]
	state.projectiles[1].id = 91
	var result := AbilityProjectilePhase.tick(state)
	assert_int(int(result.statistics.kills)).is_equal(1)
	assert_int(result.projectiles.size()).is_equal(1)
	assert_int(result.projectiles[0].id).is_equal(91)
	assert_array(result.projectiles[0].hitIds).is_empty()

func test_snapshot_adapter_preserves_unknown_fields_and_copies_hit_history() -> void:
	var source := {"id": 90, "x": 320.000001, "y": 108.000001, "vx": 3.000001, "vy": 4.000001,
		"owner": "player", "hitIds": [2], "blastRadius": 0, "launchHeight": 7,
		"flightDuration": 1, "future": {"field": [1, 2]}}
	var adapted := AbilityProjectilePhase.from_canonical(source)
	assert_that(AbilityProjectilePhase.to_canonical(adapted)).is_equal(source)
	adapted.hit_ids.append(4)
	adapted.future.field.append(3)
	assert_array(source.hitIds).is_equal([2])
	assert_array(source.future.field).is_equal([1, 2])

func test_phase_advances_no_time_status_or_field_timer() -> void:
	var fixture := _fixture()
	var state: Dictionary = fixture.baseline.duplicate(true)
	state.enemies[0].rootRemaining = 0.4
	state.fields = [{"kind": "seal", "x": 110, "y": 98, "remaining": 0.4, "radius": 1}]
	var result := AbilityProjectilePhase.tick(state)
	for key in ["time", "tick", "player", "fields", "enemies", "turrets"]:
		assert_that(result[key]).is_equal(state[key])
