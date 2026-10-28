extends GdUnitTestSuite

const Runtime = preload("res://core/weapon_lines.gd")
const DATA := "res://data/weapon_lines.json"
const DATA_SHA256 := "cf53148627f01ca27aee0a01af325e4758175e88cd7250dfd315a0e74b91f73e"
const TEMP := "user://weapon_lines_test.json"
var document: Dictionary
var resolver: RefCounted

func before_test() -> void:
	document = JSON.parse_string(FileAccess.get_file_as_string(DATA))
	resolver = Runtime.new()
	assert_int(resolver.configure(document)).is_equal(OK)

func after_test() -> void:
	DirAccess.remove_absolute(TEMP)

func test_committed_table_is_the_frozen_pinned_extraction() -> void:
	assert_str(FileAccess.get_sha256(DATA)).is_equal(DATA_SHA256)
	assert_str(document.source.commit).is_equal(Runtime.SOURCE_COMMIT)
	assert_int(int(document.source.pr)).is_equal(290)
	assert_int(document.lines.size()).is_equal(14)

func test_every_folk_and_all_fifty_six_stages_match_source_records() -> void:
	var before := document.duplicate(true)
	for row in document.lines:
		assert_dict(resolver.line(row.id)).is_equal(row.weapon)
		for tier in [1, 2, 3, 4]:
			var result: Dictionary = resolver.at_tier(row.id, tier)
			assert_bool(result.ok).is_true()
			assert_dict(result.stage).is_equal(row.weapon.tiers[tier - 1])
			assert_str(result.provenance.blob).is_equal(row.source_blob)
			assert_str(result.provenance.weapon_sha256).is_equal(row.weapon_sha256)
			assert_str(result.provenance.path).is_equal(row.source_path)
			assert_bool(result.preview_only).is_true()
			assert_bool(result.approved).is_false()
			assert_bool(result.mechanics_applied).is_false()
			assert_str(result.status).contains("unapproved")
			assert_str(result.status).contains("placeholder")
	assert_dict(document).is_equal(before)

func test_named_evolutions_and_repeated_forms_remain_distinct_stages() -> void:
	var forms := {
		"bramble": ["bow", "crossbow", "repeater", "repeater"],
		"pendle": ["one revolver", "heavy revolver", "two revolvers", "two revolvers"],
		"iona": ["spear", "winged spear", "glaive", "glaive"],
		"morel": ["hand flasks", "bandolier", "mortar", "mortar"],
	}
	for folk in forms:
		for i in 4:
			assert_str(resolver.at_tier(folk, i + 1).stage.form).is_equal(forms[folk][i])
	var comparison: Dictionary = resolver.compare("bramble", 3, 4)
	assert_bool(comparison.form_changed).is_false()
	assert_bool(comparison.mechanics_changed).is_true()
	assert_bool(resolver.compare("bramble", 1, 2).form_changed).is_true()
	assert_bool(resolver.compare("pendle", 2, 3).form_changed).is_true()

func test_every_valid_projection_resolves_without_granting_or_changing_progress() -> void:
	for row in document.lines:
		for i in 4:
			var state := {"progression": {"level": Runtime.LEVELS[i], "xp": 9},
				"folk": {row.id: {"weapon_tier": i + 1, "nodes": [], "look": {"outfit": "keep"}}},
				"glint": 43, "extension": ["keep"]}
			var before := state.duplicate(true)
			var result: Dictionary = resolver.current(state, row.id)
			assert_bool(result.ok).is_true()
			assert_dict(result.stage).is_equal(row.weapon.tiers[i])
			assert_dict(state).is_equal(before)
	var unjoined := {"progression": {"level": 30}, "folk": {}}
	assert_str(resolver.current(unjoined, "bramble").reason).is_equal("unjoined")
	var high_level := {"progression": {"level": 30}, "folk": {"bramble": {"weapon_tier": 1}}}
	assert_int(int(resolver.current(high_level, "bramble").stage.tier)).is_equal(1)

func test_invalid_projections_and_tiers_are_clean_read_only_refusals() -> void:
	for value in [null, [], {}, {"progression": [], "folk": {}},
			{"progression": {"level": 1}, "folk": []},
			{"progression": {"level": 31}, "folk": {}},
			{"progression": {"level": true}, "folk": {}},
			{"progression": {"level": NAN}, "folk": {}}]:
		assert_bool(resolver.current(value, "bramble").ok).is_false()
	for value in [0, 5, 1.5, "2", true, null, [], NAN, INF, -INF]:
		assert_bool(resolver.at_tier("bramble", value).ok).is_false()
		assert_bool(resolver.compare("bramble", 1, value).ok).is_false()
		assert_bool(resolver.compare("bramble", value, 2).ok).is_false()
		var state := {"progression": {"level": 30}, "folk": {"bramble": {"weapon_tier": value}}}
		assert_bool(resolver.current(state, "bramble").ok).is_false()
	assert_str(resolver.current({"progression": {"level": 7}, "folk": {"bramble": {"weapon_tier": 2}}}, "bramble").reason).is_equal("tier_above_level")
	assert_bool(resolver.at_tier("unknown", 1).ok).is_false()
	assert_dict(resolver.line("unknown")).is_empty()

func test_input_and_all_returned_nested_metadata_are_detached() -> void:
	document.lines[0].weapon.tiers[1].mechanics.fire_interval_pct = 999
	var result: Dictionary = resolver.at_tier("bramble", 2)
	assert_float(result.stage.mechanics.fire_interval_pct).is_equal(35.0)
	result.stage.art.description = "changed"
	result.source.commit = "changed"
	result.provenance.blob = "changed"
	var line: Dictionary = resolver.line("bramble")
	line.tiers[1].mechanics.clear()
	var ids: Array = resolver.folk_ids()
	ids.clear()
	var comparison: Dictionary = resolver.compare("bramble", 1, 2)
	comparison.after.mechanics.clear()
	assert_int(resolver.folk_ids().size()).is_equal(14)
	assert_float(resolver.at_tier("bramble", 2).stage.mechanics.fire_interval_pct).is_equal(35.0)
	assert_str(resolver.status().source.commit).is_equal(Runtime.SOURCE_COMMIT)

func test_configuration_refusal_preserves_previous_catalogue() -> void:
	var before: Dictionary = resolver.line("bramble")
	for value in [null, [], {}, {"schema_version": 2}]:
		assert_int(resolver.configure(value)).is_equal(ERR_INVALID_DATA)
		assert_dict(resolver.line("bramble")).is_equal(before)
	for mode in ["approved", "applied", "missing_status", "source", "source_hash", "duplicate", "null_weapon", "null_tiers", "bad_form", "bad_level", "bad_requires", "bad_mechanics"]:
		var changed := document.duplicate(true)
		match mode:
			"approved": changed.approved = true
			"applied": changed.mechanics_applied = true
			"missing_status": changed.status = "approved"
			"source": changed.source.commit = "missing"
			"source_hash": changed.lines[0].source_blob = "bad"
			"duplicate": changed.lines[1].id = changed.lines[0].id
			"null_weapon": changed.lines[0].weapon = null
			"null_tiers": changed.lines[0].weapon.tiers = null
			"bad_form": changed.lines[0].weapon.tiers[0].form = " "
			"bad_level": changed.lines[0].weapon.tiers[0].level = true
			"bad_requires": changed.lines[0].weapon.tiers[0].requires = []
			"bad_mechanics": changed.lines[0].weapon.tiers[0].mechanics = []
		assert_int(resolver.configure(changed)).is_equal(ERR_INVALID_DATA)
		assert_dict(resolver.line("bramble")).is_equal(before)

func _check_stored(path: String) -> Dictionary:
	var output: Array = []
	var script := ProjectSettings.globalize_path("res://../scripts/progression/weapon_lines.py").simplify_path()
	var code := OS.execute("python3", [script, "--check-stored", "--path", path], output, true)
	return {"code": code, "output": "\n".join(output)}

func test_offline_cli_checks_real_table_without_git_or_source_checkout() -> void:
	var result := _check_stored(ProjectSettings.globalize_path(DATA))
	assert_int(result.code).is_equal(0)
	assert_str(result.output).contains("14 lines / 56 stages")

func test_offline_cli_rejects_stale_fingerprints_without_writing_input() -> void:
	var original := FileAccess.get_file_as_string(DATA)
	var old_name: String = document.lines[0].weapon.tiers[1].name
	var bad := original.replace(JSON.stringify(old_name), JSON.stringify("changed"))
	assert_bool(bad != original).is_true()
	var file := FileAccess.open(TEMP, FileAccess.WRITE)
	file.store_string(bad)
	file.close()
	var before := FileAccess.get_file_as_bytes(TEMP)
	var result := _check_stored(ProjectSettings.globalize_path(TEMP))
	assert_int(result.code).is_equal(1)
	assert_str(result.output).contains("fingerprint mismatch")
	assert_bool(FileAccess.get_file_as_bytes(TEMP) == before).is_true()

func test_offline_cli_rejects_missing_malformed_or_approved_documents() -> void:
	assert_int(_check_stored(ProjectSettings.globalize_path(TEMP)).code).is_equal(1)
	for value in [null, [], {"schema_version": 2}, {"schema_version": 1, "approved": true}]:
		var file := FileAccess.open(TEMP, FileAccess.WRITE)
		file.store_string(JSON.stringify(value))
		file.close()
		var before := FileAccess.get_file_as_bytes(TEMP)
		assert_int(_check_stored(ProjectSettings.globalize_path(TEMP)).code).is_equal(1)
		assert_bool(FileAccess.get_file_as_bytes(TEMP) == before).is_true()

func test_unconfigured_resolver_never_returns_a_live_stage() -> void:
	var empty := Runtime.new()
	assert_array(empty.folk_ids()).is_empty()
	assert_bool(empty.at_tier("bramble", 1).ok).is_false()
	assert_bool(empty.status().approved).is_false()
	assert_bool(empty.status().mechanics_applied).is_false()
