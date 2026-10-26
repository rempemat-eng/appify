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
	var bytes := FileAccess.get_file_as_bytes("res://test/combat/simulation-oracle.json.gz")
	var text := bytes.decompress_dynamic(128 * 1024 * 1024, FileAccess.COMPRESSION_GZIP).get_string_from_utf8()
	return _decode(JSON.parse_string(text))

func _difference(actual: Variant, expected: Variant, path: String) -> String:
	if expected is Dictionary:
		if not actual is Dictionary or actual.size() != expected.size():
			return path + " dictionary keys"
		for key in expected:
			if not actual.has(key):
				return path + "." + key + " missing"
			var difference := _difference(actual[key], expected[key], path + "." + key)
			if not difference.is_empty():
				return difference
	elif expected is Array:
		if not actual is Array or actual.size() != expected.size():
			return path + " array length"
		for index in expected.size():
			var difference := _difference(actual[index], expected[index], path + "[%d]" % index)
			if not difference.is_empty():
				return difference
	elif expected is float or expected is int:
		if not (actual is float or actual is int) or absf(float(actual) - float(expected)) > 0.000001:
			return path + " actual=%s expected=%s" % [actual, expected]
	elif actual != expected:
		return path + " actual=%s expected=%s" % [actual, expected]
	return ""

func _restore(base: Dictionary, patch: Dictionary) -> Dictionary:
	var result := base.duplicate(true)
	for key in patch:
		if patch[key] is Dictionary and result.get(key) is Dictionary:
			result[key] = _restore(result[key], patch[key])
		else:
			result[key] = patch[key].duplicate(true) if patch[key] is Array or patch[key] is Dictionary else patch[key]
	return result

func test_full_dispatcher_matches_original() -> void:
	var fixture := _fixture()
	assert_int(fixture.cases.size()).is_greater(150)
	for index in fixture.cases.size():
		var case: Dictionary = fixture.cases[index]
		var initial := _restore(fixture.baseline, case.initial)
		var before := initial.duplicate(true)
		var expected := _restore(initial, case.expected)
		var result := AbilitySimulation.step(initial, case.input, case.dt)
		assert_str(_difference(result, expected, "simulation%d/%s" % [index, case.label])).is_empty()
		assert_that(initial).is_equal(before)

func test_inactive_invalid_delta_and_unowned_live_mode_do_not_advance() -> void:
	var source: Dictionary = _fixture().baseline
	for delta in [0.0, -1.0, NAN, INF, -INF]:
		assert_that(AbilitySimulation.step(source, {}, delta)).is_equal(source)
	assert_that(AbilitySimulation.step(source, {"active": false}, 0.1)).is_equal(source)
	source.mode = "live"
	assert_that(AbilitySimulation.step(source, {"primary": true}, 0.1)).is_equal(source)

func test_nonfinite_inputs_fall_back_and_raw_input_is_unchanged() -> void:
	var source: Dictionary = _fixture().baseline
	var input := {"moveX": INF, "moveY": NAN, "aimX": -INF, "aimY": NAN}
	var normal := AbilitySimulation.normalise_input(input, source.player)
	assert_float(normal.moveX).is_zero()
	assert_float(normal.moveY).is_zero()
	assert_float(normal.aimX).is_equal(float(source.player.aimX))
	assert_float(normal.aimY).is_equal(float(source.player.aimY))
	assert_bool(is_inf(input.moveX)).is_true()
	assert_bool(is_nan(input.moveY)).is_true()
