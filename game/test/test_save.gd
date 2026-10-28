extends GdUnitTestSuite
## The save survives a round trip through JSON, and older or partial documents load into the current shape.

const PATH := "user://test_save.json"

func before_test() -> void:
	SaveGame.reset()

func after_test() -> void:
	DirAccess.remove_absolute(ProjectSettings.globalize_path(PATH))
	DirAccess.remove_absolute(ProjectSettings.globalize_path(PATH + ".tmp"))
	DirAccess.remove_absolute(ProjectSettings.globalize_path(PATH + ".directory"))

func test_round_trip() -> void:
	SaveGame.add_glint(123)
	SaveGame.set_flag("camp_cleared:meadow")
	SaveGame.data.zone = "woodland"
	SaveGame.data.spawn = "stones"
	Quests.start_quest("woodland_stones")
	Quests.notify("camp:meadow")
	var before: Dictionary = SaveGame.data.duplicate(true)
	assert_int(SaveGame.save(PATH)).is_equal(OK)
	SaveGame.reset()
	assert_int(SaveGame.data.glint).is_equal(0)
	assert_int(SaveGame.load_save(PATH)).is_equal(OK)
	assert_dict(SaveGame.data).is_equal(before)
	assert_int(typeof(SaveGame.data.glint)).is_equal(TYPE_INT)
	assert_int(Quests.step_index("woodland_stones")).is_equal(1)

func test_old_document_is_migrated() -> void:
	var f := FileAccess.open(PATH, FileAccess.WRITE)
	f.store_string(JSON.stringify({"glint": 7.0, "flags": {"a": true}}))
	f.close()
	assert_int(SaveGame.load_save(PATH)).is_equal(OK)
	assert_int(SaveGame.data.version).is_equal(SaveGame.VERSION)
	assert_int(SaveGame.data.glint).is_equal(7)
	assert_bool(SaveGame.has_flag("a")).is_true()
	assert_str(SaveGame.data.zone).is_equal("woodland")
	assert_bool(SaveGame.data.settings.has("reduced_motion")).is_true()

func test_missing_file_starts_fresh() -> void:
	SaveGame.add_glint(5)
	assert_int(SaveGame.load_save("user://no_such_save.json")).is_equal(ERR_FILE_NOT_FOUND)
	assert_int(SaveGame.data.glint).is_equal(0)

func test_broken_file_is_refused() -> void:
	var f := FileAccess.open(PATH, FileAccess.WRITE)
	f.store_string("not json")
	f.close()
	SaveGame.add_glint(5)
	assert_int(SaveGame.load_save(PATH)).is_equal(ERR_PARSE_ERROR)
	assert_int(SaveGame.data.glint).is_equal(5)  # the running game is kept

# Historical fixtures are representative documents from the actual two version-1 source shapes,
# plus the loader's already supported versionless/explicit-zero partial documents.
const FIXTURES := "res://test/fixtures/saves/"

func _write_document(doc: Variant) -> void:
	var file := FileAccess.open(PATH, FileAccess.WRITE)
	file.store_string(JSON.stringify(doc))
	file.close()

func test_every_historical_shape_loads_and_round_trips() -> void:
	for name in ["legacy-unversioned.json", "legacy-v0-partial.json", "v1-foundation.json", "v1-village.json"]:
		var text := FileAccess.get_file_as_string(FIXTURES + name)
		var doc: Dictionary = JSON.parse_string(text)
		_write_document(doc)
		var disk_before := FileAccess.get_file_as_bytes(PATH)
		assert_int(SaveGame.load_save(PATH)).is_equal(OK)
		var expected: Dictionary = SaveGame._migrate(doc)
		assert_dict(SaveGame.data).is_equal(expected)
		assert_bool(FileAccess.get_file_as_bytes(PATH) == disk_before).is_true()
		assert_int(SaveGame.save(PATH)).is_equal(OK)
		SaveGame.reset()
		assert_int(SaveGame.load_save(PATH)).is_equal(OK)
		assert_dict(SaveGame.data).is_equal(expected)

func test_migration_is_detached_and_idempotent() -> void:
	var doc: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(FIXTURES + "v1-village.json"))
	var before := doc.duplicate(true)
	var migrated: Dictionary = SaveGame._migrate(doc)
	assert_dict(doc).is_equal(before)
	assert_int(typeof(doc.player.hp)).is_equal(TYPE_FLOAT)
	assert_dict(SaveGame._migrate(migrated)).is_equal(migrated)
	migrated.player.extension.name = "changed"
	migrated.extension.nested[2].keep = false
	migrated.quests.retired_quest.note = "changed"
	assert_dict(doc).is_equal(before)

func test_partial_nested_defaults_preserve_custom_fields() -> void:
	var doc := {"settings": {"custom": [1]}, "player": {"hp": 2.0, "custom": true}, "village": {"custom": true}}
	var before := doc.duplicate(true)
	var migrated: Dictionary = SaveGame._migrate(doc)
	assert_dict(doc).is_equal(before)
	assert_int(migrated.player.hp).is_equal(2)
	assert_int(migrated.player.max_hp).is_equal(5)
	assert_bool(migrated.player.custom).is_true()
	assert_bool(migrated.village.custom).is_true()
	assert_dict(migrated.village.restored).is_empty()
	assert_bool(migrated.settings.reduced_motion).is_false()
	assert_str(migrated.settings.pixel_scale).is_equal("fill")
	migrated.settings.custom.append(2)
	assert_dict(doc).is_equal(before)

func test_defaults_are_not_shared_between_migrations() -> void:
	var first: Dictionary = SaveGame._migrate({})
	first.flags.a = true
	first.player.hp = 1
	first.village.restored.forge = 1
	assert_dict(SaveGame._migrate({})).is_equal(SaveGame.fresh())

func test_future_version_preserves_disk_live_state_and_signals() -> void:
	var future := {"version": SaveGame.VERSION + 1, "glint": 77, "new_shape": {"value": true}}
	_write_document(future)
	var bytes := FileAccess.get_file_as_bytes(PATH)
	SaveGame.add_glint(12)
	var live := SaveGame.data.duplicate(true)
	var events: Array = []
	var listener := func() -> void: events.append(true)
	SaveGame.loaded.connect(listener)
	assert_int(SaveGame.load_save(PATH)).is_equal(ERR_UNAVAILABLE)
	SaveGame.loaded.disconnect(listener)
	assert_array(events).is_empty()
	assert_dict(SaveGame.data).is_equal(live)
	assert_bool(FileAccess.get_file_as_bytes(PATH) == bytes).is_true()
	assert_dict(SaveGame._migrate(future)).is_empty()
	# The game can autosave after a failed load. The future disk document still wins.
	assert_int(SaveGame.save(PATH)).is_equal(ERR_UNAVAILABLE)
	assert_bool(FileAccess.get_file_as_bytes(PATH) == bytes).is_true()
	assert_dict(SaveGame.data).is_equal(live)

func test_malformed_nested_documents_are_refused_without_mutation() -> void:
	var invalid: Array = [
		{"settings": null}, {"settings": []}, {"player": "bad"},
		{"flags": []}, {"quests": []}, {"quests": {"q": null}},
		{"quests": {"q": {"step": "1"}}}, {"quests": {"q": {"state": 1}}},
		{"village": []}, {"village": {"restored": null}},
		{"village": {"restored": {"forge": "1"}}},
		{"player": {"hp": null}}, {"player": {"max_hp": []}},
		{"zone": 1}, {"spawn": null}, {"glint": true},
		{"settings": {"reduced_motion": "yes"}}, {"settings": {"pixel_scale": false}},
	]
	SaveGame.add_glint(9)
	var live := SaveGame.data.duplicate(true)
	for doc in invalid:
		var before: Dictionary = doc.duplicate(true)
		_write_document(doc)
		var bytes := FileAccess.get_file_as_bytes(PATH)
		assert_int(SaveGame.load_save(PATH)).is_equal(ERR_INVALID_DATA)
		assert_dict(SaveGame.data).is_equal(live)
		assert_bool(FileAccess.get_file_as_bytes(PATH) == bytes).is_true()
		assert_dict(SaveGame._migrate(doc)).is_empty()
		assert_dict(doc).is_equal(before)

func test_invalid_versions_are_refused() -> void:
	for version in [-1, 0.5, "1", true, null, [], {}]:
		_write_document({"version": version})
		assert_int(SaveGame.load_save(PATH)).is_equal(ERR_INVALID_DATA)
		assert_dict(SaveGame.data).is_equal(SaveGame.fresh())

func test_numeric_fields_require_exact_finite_whole_numbers() -> void:
	for number in [1.5, INF, -INF, NAN, 9007199254740992.0]:
		for doc in [{"glint": number}, {"player": {"hp": number}},
				{"player": {"max_hp": number}}, {"quests": {"q": {"step": number}}},
				{"village": {"restored": {"forge": number}}}]:
			assert_dict(SaveGame._migrate(doc)).is_empty()

func test_exact_numeric_boundaries_and_negative_legacy_values_round_trip() -> void:
	for number in [-9007199254740991, -1, 0, 9007199254740991]:
		SaveGame.data.glint = number
		assert_int(SaveGame.save(PATH)).is_equal(OK)
		SaveGame.reset()
		assert_int(SaveGame.load_save(PATH)).is_equal(OK)
		assert_int(SaveGame.data.glint).is_equal(number)
		assert_int(typeof(SaveGame.data.glint)).is_equal(TYPE_INT)

func test_save_validation_preserves_previous_file_and_live_version() -> void:
	SaveGame.add_glint(8)
	assert_int(SaveGame.save(PATH)).is_equal(OK)
	var bytes := FileAccess.get_file_as_bytes(PATH)
	SaveGame.data.version = 2
	var live := SaveGame.data.duplicate(true)
	assert_int(SaveGame.save(PATH)).is_equal(ERR_UNAVAILABLE)
	assert_dict(SaveGame.data).is_equal(live)
	assert_bool(FileAccess.get_file_as_bytes(PATH) == bytes).is_true()
	SaveGame.data.version = 1
	SaveGame.data.player = []
	assert_int(SaveGame.save(PATH)).is_equal(ERR_INVALID_DATA)
	assert_bool(FileAccess.get_file_as_bytes(PATH) == bytes).is_true()
	assert_bool(FileAccess.file_exists(PATH + ".tmp")).is_false()

func test_failed_write_and_rename_do_not_publish_or_emit() -> void:
	var events: Array = []
	var listener := func(_target: String) -> void: events.append(true)
	SaveGame.saved.connect(listener)
	SaveGame.data.erase("version")
	var before := SaveGame.data.duplicate(true)
	assert_int(SaveGame.save("user://absent_save_parent_7137/save.json")).is_not_equal(OK)
	var directory := PATH + ".directory"
	assert_int(DirAccess.make_dir_absolute(directory)).is_equal(OK)
	assert_int(SaveGame.save(directory)).is_not_equal(OK)
	SaveGame.saved.disconnect(listener)
	assert_array(events).is_empty()
	assert_dict(SaveGame.data).is_equal(before)
	assert_bool(DirAccess.dir_exists_absolute(directory)).is_true()
	assert_bool(FileAccess.file_exists(directory + ".tmp")).is_false()

func test_success_signals_and_default_path_override() -> void:
	var original_path: String = SaveGame.path
	SaveGame.path = PATH
	var events: Array = []
	var on_save := func(target: String) -> void: events.append(target)
	var on_load := func() -> void: events.append("loaded")
	SaveGame.saved.connect(on_save)
	SaveGame.loaded.connect(on_load)
	SaveGame.add_glint(31)
	assert_int(SaveGame.save()).is_equal(OK)
	SaveGame.reset()
	assert_int(SaveGame.load_save()).is_equal(OK)
	SaveGame.saved.disconnect(on_save)
	SaveGame.loaded.disconnect(on_load)
	SaveGame.path = original_path
	assert_array(events).is_equal([PATH, "loaded"])
	assert_int(SaveGame.data.glint).is_equal(31)

func test_non_object_json_preserves_running_state() -> void:
	SaveGame.add_glint(16)
	for doc in [null, [], true, 1, "text"]:
		_write_document(doc)
		assert_int(SaveGame.load_save(PATH)).is_equal(ERR_PARSE_ERROR)
		assert_int(SaveGame.data.glint).is_equal(16)

func test_future_target_is_protected_without_a_prior_load() -> void:
	for version in [2, 999, 9007199254740992.0]:
		_write_document({"version": version, "extension": ["future"]})
		var bytes := FileAccess.get_file_as_bytes(PATH)
		SaveGame.add_glint(1)
		var live := SaveGame.data.duplicate(true)
		assert_int(SaveGame.save(PATH)).is_equal(ERR_UNAVAILABLE)
		assert_dict(SaveGame.data).is_equal(live)
		assert_bool(FileAccess.get_file_as_bytes(PATH) == bytes).is_true()
