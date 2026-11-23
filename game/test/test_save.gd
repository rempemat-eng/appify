extends GdUnitTestSuite
## The save survives a round trip through JSON, and older or partial documents load into the current shape.

const PATH := "user://test_save.json"
const LEGACY_NAME_FIXTURE := "res://test/fixtures/legacy_napattack_v2.json"
const LEGACY_PATH := PATH + ".legacy"
const RENAMED_PATH := PATH + ".renamed"
const OTHER_PATH := PATH + ".other"

# Only the directory lookup is replaced: these tests exercise real boot/load/save and
# real disposable files, never a player's old sibling directory or default save.
class MigrationSave:
	extends "res://core/save_game.gd"
	var legacy_source := ""
	var legacy_lookups := 0

	func _legacy_save_path() -> String:
		legacy_lookups += 1
		return legacy_source

# Exercise the real card decision without entering the game scene or writing a story autosave.
class RecoveryCardHud:
	extends Control
	var guidance := true
	var cards: Array[Dictionary] = []

	func show_card(title: String, subtitle: String, text: String, secs := 9.0) -> void:
		cards.append({"title": title, "subtitle": subtitle, "text": text, "seconds": secs})

class RecoveryCardGame:
	extends "res://game.gd"
	var autosave_calls := 0

	func autosave() -> void:
		autosave_calls += 1

var _migration_saves: Array[Node] = []
var _card_state := {}

func before_test() -> void:
	SaveGame.reset()

func after_test() -> void:
	if not _card_state.is_empty():
		SaveGame.data = _card_state.data
		SaveGame.boot_error = _card_state.boot_error
		SaveGame._legacy_import_error = _card_state.import_error
		Dialogue.busy = _card_state.dialogue_busy
		Zones.current = _card_state.zone
		_card_state.clear()
	for instance: Node in _migration_saves:
		instance.free()
	_migration_saves.clear()
	for file: String in [LEGACY_PATH, RENAMED_PATH, RENAMED_PATH + ".tmp",
			RENAMED_PATH + ".broken", RENAMED_PATH + ".name-migration.tmp", OTHER_PATH]:
		DirAccess.remove_absolute(ProjectSettings.globalize_path(file))
	DirAccess.remove_absolute(ProjectSettings.globalize_path(PATH))
	DirAccess.remove_absolute(ProjectSettings.globalize_path(PATH + ".tmp"))
	DirAccess.remove_absolute(ProjectSettings.globalize_path(PATH + ".directory"))

func _migration_save() -> MigrationSave:
	var instance := MigrationSave.new()
	instance.path = RENAMED_PATH
	instance.legacy_source = LEGACY_PATH
	_migration_saves.append(instance)
	return instance

func _write_migration_file(target: String, text: String) -> void:
	var file := FileAccess.open(target, FileAccess.WRITE)
	file.store_string(text)
	file.close()

func _recovery_card_game() -> RecoveryCardGame:
	if _card_state.is_empty():
		_card_state = {"data": SaveGame.data.duplicate(true), "boot_error": SaveGame.boot_error,
			"import_error": SaveGame._legacy_import_error, "dialogue_busy": Dialogue.busy, "zone": Zones.current}
	SaveGame.boot_error = OK
	SaveGame._legacy_import_error = OK
	Dialogue.busy = false
	Zones.current = null
	# No story card is due on a repeat call; the test double also refuses any actual autosave.
	for card: Dictionary in Quests.cards:
		SaveGame.data.flags["seen:" + str(card.get("id", ""))] = true
	var game: RecoveryCardGame = auto_free(RecoveryCardGame.new())
	game.hud = RecoveryCardHud.new()
	game.add_child(game.hud)
	return game

func test_default_legacy_lookup_uses_the_real_absolute_sibling_without_booting() -> void:
	var instance := preload("res://core/save_game.gd").new()
	_migration_saves.append(instance)
	assert_str(instance.path).is_equal(SaveGame.DEFAULT_PATH)
	var legacy: String = instance._legacy_save_path()
	var parent := OS.get_user_data_dir().get_base_dir()
	assert_bool(legacy.is_absolute_path()).is_true()
	assert_str(legacy).is_equal(parent.path_join("napattack/save_0.json"))
	assert_str(legacy.get_base_dir().get_base_dir()).is_equal(parent)
	assert_bool(legacy == OS.get_user_data_dir().path_join("napattack/save_0.json")).is_false()

func test_failed_import_card_keeps_its_cause_and_shows_once_without_autosaving() -> void:
	# Even an overlapping load-error code is an import failure when the copy failed.
	for err: Error in [ERR_FILE_CANT_READ, ERR_FILE_CANT_WRITE, ERR_PARSE_ERROR, ERR_INVALID_DATA, ERR_UNAVAILABLE]:
		var game := _recovery_card_game()
		var card_hud := game.hud as RecoveryCardHud
		SaveGame.boot_error = err
		SaveGame._legacy_import_error = err
		await game._show_due_card()
		assert_int(card_hud.cards.size()).is_equal(1)
		var card: Dictionary = card_hud.cards[0]
		assert_str(card.title).is_equal("A new game")
		assert_str(card.subtitle).contains("napattack")
		assert_str(card.text).contains("old progress is still in the napattack folder")
		assert_str(card.text).contains("this session cannot save")
		assert_bool(str(card.text).contains(".broken")).is_false()
		assert_bool(str(card.text).contains("newer one")).is_false()
		assert_float(card.seconds).is_equal(14.0)
		await game._show_due_card()
		assert_int(card_hud.cards.size()).is_equal(1)
		assert_int(game.autosave_calls).is_equal(0)
		assert_int(SaveGame.boot_error).is_equal(err)
		assert_int(SaveGame._legacy_import_error).is_equal(err)

func test_load_error_cards_keep_their_existing_explanations_without_an_import_failure() -> void:
	for err: Error in [ERR_PARSE_ERROR, ERR_INVALID_DATA, ERR_UNAVAILABLE]:
		var game := _recovery_card_game()
		var card_hud := game.hud as RecoveryCardHud
		SaveGame.boot_error = err
		await game._show_due_card()
		assert_int(card_hud.cards.size()).is_equal(1)
		var card: Dictionary = card_hud.cards[0]
		if err == ERR_UNAVAILABLE:
			assert_str(card.subtitle).contains("newer version")
			assert_str(card.text).contains("will not be saved over the newer one")
			assert_bool(str(card.text).contains(".broken")).is_false()
		else:
			assert_str(card.subtitle).is_equal("The save could not be read")
			assert_str(card.text).contains(SaveGame.path.get_file() + ".broken")
		assert_bool(str(card.text).contains("napattack")).is_false()
		assert_float(card.seconds).is_equal(14.0)
		await game._show_due_card()
		assert_int(card_hud.cards.size()).is_equal(1)
		assert_int(game.autosave_calls).is_equal(0)

func test_a_clean_or_missing_save_does_not_show_a_recovery_card() -> void:
	for err: Error in [OK, ERR_FILE_NOT_FOUND]:
		var game := _recovery_card_game()
		SaveGame.boot_error = err
		await game._show_due_card()
		assert_array((game.hud as RecoveryCardHud).cards).is_empty()
		assert_bool(game._told_about_the_save).is_false()
		assert_int(game.autosave_calls).is_equal(0)

func test_failed_import_card_waits_until_guidance_is_enabled() -> void:
	var game := _recovery_card_game()
	var card_hud := game.hud as RecoveryCardHud
	SaveGame.boot_error = ERR_FILE_CANT_WRITE
	SaveGame._legacy_import_error = ERR_FILE_CANT_WRITE
	card_hud.guidance = false
	await game._show_due_card()
	assert_array(card_hud.cards).is_empty()
	assert_bool(game._told_about_the_save).is_false()
	card_hud.guidance = true
	await game._show_due_card()
	assert_int(card_hud.cards.size()).is_equal(1)
	assert_int(game.autosave_calls).is_equal(0)

func test_old_folder_v2_import_keeps_original_bytes_progress_and_unknown_fields() -> void:
	var text := FileAccess.get_file_as_string(LEGACY_NAME_FIXTURE)
	_write_migration_file(LEGACY_PATH, text)
	var original := FileAccess.get_file_as_bytes(LEGACY_PATH)
	var instance := _migration_save()
	assert_int(instance.boot()).is_equal(OK)
	assert_bool(FileAccess.get_file_as_bytes(LEGACY_PATH) == original).is_true()
	assert_bool(FileAccess.get_file_as_bytes(RENAMED_PATH) == original).is_true()
	var expected: Dictionary = SaveGame._migrate(JSON.parse_string(text))
	assert_dict(instance.data).is_equal(expected)
	assert_int(instance.data.glint).is_equal(137)
	assert_int(instance.data.quests.woodland_stones.step).is_equal(1)
	assert_bool(instance.data.settings.gentle_sound).is_true()
	assert_dict(instance.data.extension).is_equal(expected.extension)
	assert_str(instance.data.player.extension.name).is_equal("keep this unknown player field")
	assert_str(instance.data.quests.retired_quest.note).is_equal("keep this unknown quest")
	# The first normal save and later round trips keep all of the loaded state.
	var live := instance.data.duplicate(true)
	assert_int(instance.save()).is_equal(OK)
	var saved_bytes := FileAccess.get_file_as_bytes(RENAMED_PATH)
	instance.reset()
	assert_int(instance.boot()).is_equal(OK)
	assert_dict(instance.data).is_equal(live)
	assert_int(instance.save()).is_equal(OK)
	assert_bool(FileAccess.get_file_as_bytes(RENAMED_PATH) == saved_bytes).is_true()
	assert_bool(FileAccess.get_file_as_bytes(LEGACY_PATH) == original).is_true()

func test_new_folder_save_wins_even_when_damaged_or_from_a_future_version() -> void:
	_write_migration_file(LEGACY_PATH, FileAccess.get_file_as_string(LEGACY_NAME_FIXTURE))
	var old_bytes := FileAccess.get_file_as_bytes(LEGACY_PATH)
	for pair: Array in [
			[JSON.stringify({"version": 2, "glint": 19, "extension": "newer progress"}), OK],
			["not json", ERR_PARSE_ERROR],
			[JSON.stringify({"version": 99, "extension": "future progress"}), ERR_UNAVAILABLE]]:
		_write_migration_file(RENAMED_PATH, pair[0])
		var new_bytes := FileAccess.get_file_as_bytes(RENAMED_PATH)
		var instance := _migration_save()
		assert_int(instance.boot()).is_equal(pair[1])
		assert_bool(FileAccess.get_file_as_bytes(RENAMED_PATH) == new_bytes).is_true()
		assert_bool(FileAccess.get_file_as_bytes(LEGACY_PATH) == old_bytes).is_true()
		if pair[1] == OK:
			assert_int(instance.data.glint).is_equal(19)
			assert_str(instance.data.extension).is_equal("newer progress")

func test_fresh_boot_skips_the_old_directory_entirely() -> void:
	_write_migration_file(LEGACY_PATH, FileAccess.get_file_as_string(LEGACY_NAME_FIXTURE))
	var old_bytes := FileAccess.get_file_as_bytes(LEGACY_PATH)
	var instance := _migration_save()
	assert_int(instance.boot(true)).is_equal(OK)
	assert_int(instance.legacy_lookups).is_equal(0)
	assert_bool(FileAccess.file_exists(RENAMED_PATH)).is_false()
	assert_bool(FileAccess.get_file_as_bytes(LEGACY_PATH) == old_bytes).is_true()

func test_custom_save_path_does_not_resolve_a_real_legacy_directory() -> void:
	var instance := preload("res://core/save_game.gd").new()
	_migration_saves.append(instance)
	instance.path = RENAMED_PATH
	assert_str(instance._legacy_save_path()).is_empty()
	assert_int(instance.boot()).is_equal(ERR_FILE_NOT_FOUND)
	assert_bool(FileAccess.file_exists(RENAMED_PATH)).is_false()

func test_missing_old_save_still_starts_a_new_game() -> void:
	var instance := _migration_save()
	assert_int(instance.boot()).is_equal(ERR_FILE_NOT_FOUND)
	assert_dict(instance.data).is_equal(SaveGame.fresh())
	assert_int(instance.save()).is_equal(OK)

func test_failed_old_folder_import_blocks_fresh_autosave_and_retries_on_boot() -> void:
	_write_migration_file(LEGACY_PATH, FileAccess.get_file_as_string(LEGACY_NAME_FIXTURE))
	var old_bytes := FileAccess.get_file_as_bytes(LEGACY_PATH)
	var obstruction := RENAMED_PATH + ".name-migration.tmp"
	assert_int(DirAccess.make_dir_absolute(obstruction)).is_equal(OK)
	var instance := _migration_save()
	var err: Error = instance.boot()
	assert_int(err).is_not_equal(OK)
	instance.add_glint(1)
	assert_int(instance.save()).is_equal(err)
	# An absolute spelling of the same target must not bypass the guard.
	assert_int(instance.save(ProjectSettings.globalize_path(RENAMED_PATH))).is_equal(err)
	assert_bool(FileAccess.file_exists(RENAMED_PATH)).is_false()
	assert_bool(FileAccess.get_file_as_bytes(LEGACY_PATH) == old_bytes).is_true()
	# A deliberately separate output is allowed while default autosave is blocked.
	assert_int(instance.save(OTHER_PATH)).is_equal(OK)
	assert_int(DirAccess.remove_absolute(obstruction)).is_equal(OK)
	assert_int(instance.boot()).is_equal(OK)
	assert_int(instance.data.glint).is_equal(137)
	assert_bool(FileAccess.get_file_as_bytes(RENAMED_PATH) == old_bytes).is_true()

func test_imported_damaged_and_future_saves_keep_the_existing_boot_contract() -> void:
	for pair: Array in [["not json", ERR_PARSE_ERROR],
			[JSON.stringify({"version": 99}), ERR_UNAVAILABLE],
			[JSON.stringify({"version": 2, "player": []}), ERR_INVALID_DATA]]:
		_write_migration_file(LEGACY_PATH, pair[0])
		var old_bytes := FileAccess.get_file_as_bytes(LEGACY_PATH)
		var instance := _migration_save()
		assert_int(instance.boot()).is_equal(pair[1])
		assert_bool(FileAccess.get_file_as_bytes(RENAMED_PATH) == old_bytes).is_true()
		if pair[1] == ERR_UNAVAILABLE:
			assert_int(instance.save()).is_equal(ERR_UNAVAILABLE)
			assert_bool(FileAccess.get_file_as_bytes(RENAMED_PATH) == old_bytes).is_true()
		else:
			assert_bool(FileAccess.get_file_as_bytes(RENAMED_PATH + ".broken") == old_bytes).is_true()
			assert_int(instance.save()).is_equal(OK)
		assert_bool(FileAccess.get_file_as_bytes(LEGACY_PATH) == old_bytes).is_true()
		DirAccess.remove_absolute(RENAMED_PATH)

func test_an_occupied_destination_directory_is_not_replaced() -> void:
	_write_migration_file(LEGACY_PATH, FileAccess.get_file_as_string(LEGACY_NAME_FIXTURE))
	var old_bytes := FileAccess.get_file_as_bytes(LEGACY_PATH)
	assert_int(DirAccess.make_dir_absolute(RENAMED_PATH)).is_equal(OK)
	var instance := _migration_save()
	assert_int(instance.boot()).is_equal(ERR_FILE_NOT_FOUND)
	assert_bool(DirAccess.dir_exists_absolute(RENAMED_PATH)).is_true()
	assert_bool(FileAccess.get_file_as_bytes(LEGACY_PATH) == old_bytes).is_true()

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
	var expected := SaveGame.fresh()
	expected.ledger.opening.from_version = 0
	assert_dict(SaveGame._migrate({})).is_equal(expected)

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
	SaveGame.data.version = SaveGame.VERSION + 1
	var live := SaveGame.data.duplicate(true)
	assert_int(SaveGame.save(PATH)).is_equal(ERR_UNAVAILABLE)
	assert_dict(SaveGame.data).is_equal(live)
	assert_bool(FileAccess.get_file_as_bytes(PATH) == bytes).is_true()
	SaveGame.data.version = SaveGame.VERSION
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
	for version in [SaveGame.VERSION + 1, 999, 9007199254740992.0]:
		_write_document({"version": version, "extension": ["future"]})
		var bytes := FileAccess.get_file_as_bytes(PATH)
		SaveGame.add_glint(1)
		var live := SaveGame.data.duplicate(true)
		assert_int(SaveGame.save(PATH)).is_equal(ERR_UNAVAILABLE)
		assert_dict(SaveGame.data).is_equal(live)
		assert_bool(FileAccess.get_file_as_bytes(PATH) == bytes).is_true()

## Reduced motion and pixel scale, damaged (15 Nov, the audit of #494): until then a save whose
## reduced_motion was not true or false, or whose pixel_scale was not a string, was refused whole, and the
## progress in it with it (these two documents were in the refused list above). They now load as a damaged
## sound setting does: the one setting at its default, everything else the save's own, version 2. An
## unknown pixel scale ("huge") falls back too.
func test_a_damaged_motion_or_scale_setting_loads_at_its_default_and_keeps_the_progress() -> void:
	for damage: Dictionary in [{"reduced_motion": "yes"}, {"reduced_motion": 1}, {"reduced_motion": null},
			{"pixel_scale": false}, {"pixel_scale": 2}, {"pixel_scale": null}, {"pixel_scale": "huge"},
			{"pixel_scale": ""}, {"reduced_motion": [], "pixel_scale": {}}]:
		var doc := {"version": 2, "glint": 41, "flags": {"met_hale": true}, "zone": "crossroads",
			"settings": {"reduced_motion": true, "pixel_scale": "whole", "gentle_sound": true}}
		for key: String in damage:
			doc.settings[key] = damage[key]
		_write_document(doc)
		SaveGame.reset()
		assert_int(SaveGame.load_save(PATH)).override_failure_message("refused for %s" % [damage]).is_equal(OK)
		var settings: Dictionary = SaveGame.data.settings
		assert_bool(settings.reduced_motion == (false if damage.has("reduced_motion") else true)).override_failure_message(
			"reduced_motion is %s after %s" % [settings.reduced_motion, damage]).is_true()
		assert_bool(settings.pixel_scale == ("fill" if damage.has("pixel_scale") else "whole")).override_failure_message(
			"pixel_scale is %s after %s" % [settings.pixel_scale, damage]).is_true()
		assert_int(SaveGame.data.version).is_equal(SaveGame.VERSION)

		assert_int(SaveGame.data.glint).is_equal(41)
		assert_bool(SaveGame.has_flag("met_hale")).is_true()
		assert_str(SaveGame.data.zone).is_equal("crossroads")
		assert_bool(settings.gentle_sound).is_true()
		# and it saves and loads again as it now is
		var now := SaveGame.data.duplicate(true)
		assert_int(SaveGame.save(PATH)).is_equal(OK)
		SaveGame.reset()
		assert_int(SaveGame.load_save(PATH)).is_equal(OK)
		assert_dict(SaveGame.data).is_equal(now)
	# the two known scales stay as they are
	for scale: String in ["fill", "whole"]:
		assert_str(SaveGame._migrate({"settings": {"pixel_scale": scale}}).settings.pixel_scale).is_equal(scale)

## What the fallback above does not open: a document that is not a save of this game is still refused whole.
func test_what_is_refused_stays_refused_beside_the_setting_fallbacks() -> void:
	var refused: Array = [
		[{"version": 99}, ERR_UNAVAILABLE], [{"version": SaveGame.VERSION + 1, "settings": {"pixel_scale": 3}}, ERR_UNAVAILABLE],
		[{"version": -1}, ERR_INVALID_DATA], [{"version": "2"}, ERR_INVALID_DATA],
		[{"settings": "fill"}, ERR_INVALID_DATA], [{"settings": []}, ERR_INVALID_DATA], [{"settings": null}, ERR_INVALID_DATA],
		[{"settings": [], "glint": 4}, ERR_INVALID_DATA], [{"glint": "4", "settings": {"reduced_motion": "yes"}}, ERR_INVALID_DATA],
		[{"player": [], "settings": {"pixel_scale": false}}, ERR_INVALID_DATA], [{"zone": 3}, ERR_INVALID_DATA],
	]
	SaveGame.add_glint(6)
	var live := SaveGame.data.duplicate(true)
	for pair: Array in refused:
		_write_document(pair[0])
		var bytes := FileAccess.get_file_as_bytes(PATH)
		assert_int(SaveGame.load_save(PATH)).override_failure_message("%s was not refused" % [pair[0]]).is_equal(pair[1])
		assert_dict(SaveGame.data).is_equal(live)
		assert_bool(FileAccess.get_file_as_bytes(PATH) == bytes).is_true()
		assert_dict(SaveGame._migrate(pair[0])).is_empty()

func test_ledger_opening_preserves_signed_legacy_provenance_once() -> void:
	for name: String in ["legacy-unversioned.json", "legacy-v0-partial.json", "v1-foundation.json", "v1-village.json"]:
		var doc: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(FIXTURES + name))
		var before := doc.duplicate(true)
		var migrated: Dictionary = SaveGame._migrate(doc)
		assert_dict(doc).is_equal(before)
		assert_int(migrated.ledger.schema_version).is_equal(1)
		assert_int(migrated.ledger.opening.glint).is_equal(int(doc.get("glint", 0)))
		assert_int(migrated.ledger.opening.from_version).is_equal(int(doc.get("version", 0)))
		var restored := {}
		for id: String in doc.get("village", {}).get("restored", {}):
			restored[id] = int(doc.village.restored[id])
		assert_dict(migrated.ledger.opening.restored).is_equal(restored)
		assert_array(migrated.ledger.receipts).is_empty()
		var opening: Dictionary = migrated.ledger.opening.duplicate(true)
		migrated.glint += 1
		migrated.village.restored.test_later_restore = 1
		var again: Dictionary = SaveGame._migrate(migrated)
		assert_dict(again.ledger.opening).is_equal(opening)
		assert_dict(again).is_equal(migrated)

func test_malformed_ledger_is_refused_without_replaying_or_changing_the_purse() -> void:
	for bad: Variant in [null, [], {"schema_version": 2},
			{"schema_version": 1, "opening": {"glint": 0, "restored": {}, "from_version": 2}, "receipts": [{}]}]:
		var doc := SaveGame.fresh()
		doc.glint = -3
		doc.ledger = bad
		var before := doc.duplicate(true)
		assert_dict(SaveGame._migrate(doc)).is_empty()
		assert_dict(doc).is_equal(before)
