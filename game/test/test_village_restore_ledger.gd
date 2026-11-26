extends GdUnitTestSuite
## The real forge restore, real SaveGame disk boundary and real cold_forge quest.
## Files are disposable user://test_* paths, never a player's default save.

const PATH := "user://test_village_restore_ledger.json"
const NESTED_PATH := PATH + ".nested"
const MISSING_PATH := "user://test_village_restore_ledger_missing/save.json"
const DIRECTORY_PATH := PATH + ".directory"
const LEGACY_PATH := PATH + ".legacy"
const FIXTURES := "res://test/fixtures/saves/"

class GateHud:
	extends Control
	var guidance := false

class GateGame:
	extends Node
	var hud: Control

class LabGround:
	extends Node
	var lab := true

var _before := {}
var _connections: Array[Dictionary] = []
var _errors: Array[String] = []

func before_test() -> void:
	_before = {"data": SaveGame.data.duplicate(true), "path": SaveGame.path,
		"resume": SaveGame.resume.duplicate(true), "resume_unsaved": SaveGame.resume_unsaved,
		"sites": Village.sites.duplicate(true), "error_sink": SaveGame.error_sink,
		"boot_error": SaveGame.boot_error, "import_target": SaveGame._legacy_import_target,
		"import_error": SaveGame._legacy_import_error, "zone": Zones.current}
	_errors.clear()
	SaveGame.error_sink = func(message: String) -> void: _errors.append(message)
	SaveGame._legacy_import_target = ""
	SaveGame._legacy_import_error = OK
	Zones.current = null
	SaveGame.data = SaveGame.fresh()
	SaveGame.path = PATH
	SaveGame.resume = {}
	SaveGame.resume_unsaved = false
	SaveGame.data.glint = 70
	assert_int(Village.cost("forge")).is_equal(30)
	Quests.start_quest("cold_forge")
	assert_str(Quests.current_step("cold_forge").id).is_equal("restore")

func after_test() -> void:
	for connection: Dictionary in _connections:
		if connection.signal.is_connected(connection.callback):
			connection.signal.disconnect(connection.callback)
	_connections.clear()
	SaveGame.data = _before.data
	SaveGame.path = _before.path
	SaveGame.resume = _before.resume
	SaveGame.resume_unsaved = _before.resume_unsaved
	SaveGame.error_sink = _before.error_sink
	SaveGame.boot_error = _before.boot_error
	SaveGame._legacy_import_target = _before.import_target
	SaveGame._legacy_import_error = _before.import_error
	Zones.current = _before.zone
	Village.sites = _before.sites
	for target: String in [PATH, PATH + ".tmp", PATH + ".broken", NESTED_PATH,
			NESTED_PATH + ".tmp", DIRECTORY_PATH + ".tmp", LEGACY_PATH,
			MISSING_PATH + ".tmp", MISSING_PATH + ".name-migration.tmp"]:
		DirAccess.remove_absolute(ProjectSettings.globalize_path(target))
	DirAccess.remove_absolute(ProjectSettings.globalize_path(DIRECTORY_PATH))

func _listen(event: Signal, callback: Callable) -> void:
	event.connect(callback)
	_connections.append({"signal": event, "callback": callback})

func _write(doc: Dictionary, target: String = PATH) -> void:
	var file := FileAccess.open(target, FileAccess.WRITE)
	file.store_string(JSON.stringify(doc))
	file.close()

func test_real_restore_save_new_session_load_and_repeat_has_one_receipt() -> void:
	var events: Array = []
	var nested_results: Array = []
	_write({"keep": "other target"}, NESTED_PATH)
	var nested_bytes := FileAccess.get_file_as_bytes(NESTED_PATH)
	_listen(SaveGame.saved, func(target: String) -> void: events.append(["saved", target]))
	_listen(Quests.advanced, func(id: String, _step: int) -> void:
		if id == "cold_forge":
			# Exercise existing authored completion/flags inside a synchronous observer.
			Quests.notify("talk:hale")
			nested_results.append(SaveGame.save(NESTED_PATH)))
	_listen(Quests.completed, func(_id: String) -> void: nested_results.append(SaveGame.save()))
	_listen(Village.changed, func(id: String) -> void:
		events.append(["changed", id])
		nested_results.append(SaveGame.save()))
	SaveGame.data["extension"] = JSON.parse_string('{"opaque": [1, {"keep": true}]}')
	var result: Dictionary = Village.restore_result("forge")
	assert_bool(result.ok and result.applied).is_true()
	assert_str(result.code).is_equal("applied")
	assert_int(SaveGame.data.glint).is_equal(40)
	assert_int(Village.tier("forge")).is_equal(1)
	assert_str(Quests.state("cold_forge")).is_equal("done")
	assert_bool(SaveGame.has_flag("forge_open") and SaveGame.has_flag("undercroft_open")).is_true()
	# One atomic restore write, then the existing success observer's normal save.
	assert_array(events).is_equal([["saved", PATH], ["changed", "forge"], ["saved", PATH]])
	assert_array(nested_results).is_equal([OK, ERR_BUSY, OK])
	assert_array(_errors).is_equal(["SaveGame: nested save to a different path refused"])
	assert_bool(FileAccess.get_file_as_bytes(NESTED_PATH) == nested_bytes).is_true()
	assert_int(SaveGame.data.ledger.receipts.size()).is_equal(1)
	assert_dict(SaveGame.data.ledger.receipts[0]).is_equal(result.receipt)
	assert_int(SaveGame.data.ledger.opening.glint).is_equal(0)
	var committed := SaveGame.data.duplicate(true)
	# The normal quit persistence call, followed by a fresh in-memory session.
	# This does not terminate/relaunch the Godot process; that acceptance remains separate.
	assert_int(SaveGame.save()).is_equal(OK)
	SaveGame.data = SaveGame.fresh()
	assert_int(SaveGame.load_save()).is_equal(OK)
	assert_dict(SaveGame.data).is_equal(committed)
	var bytes := FileAccess.get_file_as_bytes(PATH)
	var event_count := events.size()
	var repeat: Dictionary = Village.restore_result("forge")
	assert_bool(repeat.ok and not repeat.applied).is_true()
	assert_str(repeat.code).is_equal("duplicate")
	assert_dict(repeat.receipt).is_equal(result.receipt)
	assert_bool(Village.restore("forge")).is_false()
	assert_int(events.size()).is_equal(event_count)
	assert_bool(FileAccess.get_file_as_bytes(PATH) == bytes).is_true()
	assert_dict(SaveGame.data).is_equal(committed)

func test_duplicate_and_conflict_precede_eligibility_and_affordability() -> void:
	assert_bool(Village.restore("forge")).is_true()
	SaveGame.data.glint = -3
	Village.sites.forge["if"] = {"flags": ["test_unavailable_condition"]}
	var repeat: Dictionary = Village.restore_result("forge")
	assert_str(repeat.code).is_equal("duplicate")
	assert_int(SaveGame.data.glint).is_equal(-3)
	SaveGame.data.ledger.receipts[0].amount = 31
	var before := SaveGame.data.duplicate(true)
	var bytes := FileAccess.get_file_as_bytes(PATH)
	assert_str(Village.restore_result("forge").code).is_equal("id_conflict")
	assert_dict(SaveGame.data).is_equal(before)
	assert_bool(FileAccess.get_file_as_bytes(PATH) == bytes).is_true()

func test_ungated_restore_keeps_postcommit_observers_hp_autosave() -> void:
	# The real forge is offered before cold_forge starts: no quest signal is
	# guaranteed to call game.autosave before the atomic write.
	SaveGame.data.quests.clear()
	SaveGame.data.tracked = ""
	SaveGame.data.player.hp = 5
	var saves: Array = []
	_listen(SaveGame.saved, func(target: String) -> void: saves.append(target))
	_listen(Village.changed, func(_id: String) -> void:
		# Existing game.gd autosave copies live player HP before requesting save.
		SaveGame.data.player.hp = 2
		SaveGame.save())
	assert_bool(Village.restore("forge")).is_true()
	assert_array(saves).is_equal([PATH, PATH])
	var disk: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(PATH))
	assert_int(int(disk.player.hp)).is_equal(2)
	assert_int(int(disk.glint)).is_equal(40)
	assert_int(disk.ledger.receipts.size()).is_equal(1)

func test_real_legacy_inputs_open_without_recharge_or_fabricated_receipts() -> void:
	for name: String in ["legacy-unversioned.json", "legacy-v0-partial.json", "v1-foundation.json", "v1-village.json"]:
		var doc: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(FIXTURES + name))
		_write(doc)
		var bytes := FileAccess.get_file_as_bytes(PATH)
		assert_int(SaveGame.load_save()).is_equal(OK)
		assert_bool(FileAccess.get_file_as_bytes(PATH) == bytes).is_true()
		var before := SaveGame.data.duplicate(true)
		assert_int(SaveGame.data.ledger.opening.glint).is_equal(int(doc.get("glint", 0)))
		assert_int(SaveGame.data.ledger.opening.from_version).is_equal(int(doc.get("version", 0)))
		assert_array(SaveGame.data.ledger.receipts).is_empty()
		if Village.is_restored("forge"):
			assert_str(Village.restore_result("forge").code).is_equal("already_restored")
			assert_bool(Village.restore("forge")).is_false()
			assert_dict(SaveGame.data).is_equal(before)
		elif int(SaveGame.data.glint) < 30:
			assert_str(Village.restore_result("forge").code).is_equal("insufficient_funds")
			assert_dict(SaveGame.data).is_equal(before)
		assert_bool(FileAccess.get_file_as_bytes(PATH) == bytes).is_true()

func test_refusals_write_nothing_and_preserve_a_negative_purse() -> void:
	SaveGame.data.glint = -3
	var before := SaveGame.data.duplicate(true)
	assert_str(Village.restore_result("forge").code).is_equal("insufficient_funds")
	assert_dict(SaveGame.data).is_equal(before)
	assert_bool(FileAccess.file_exists(PATH)).is_false()
	SaveGame.data.glint = 70
	Village.sites.forge["if"] = {"flags": ["test_unavailable_condition"]}
	before = SaveGame.data.duplicate(true)
	assert_str(Village.restore_result("forge").code).is_equal("not_eligible")
	assert_dict(SaveGame.data).is_equal(before)
	assert_bool(FileAccess.file_exists(PATH)).is_false()

func test_failed_write_restores_snapshot_resyncs_once_and_plain_retry_applies() -> void:
	SaveGame.data.extension = {"opaque": ["keep"]}
	assert_int(SaveGame.save()).is_equal(OK)
	var bytes := FileAccess.get_file_as_bytes(PATH)
	var before := SaveGame.data.duplicate(true)
	var loaded_events: Array = []
	var saved_events: Array = []
	var changed_events: Array = []
	var nested_results: Array = []
	_listen(SaveGame.loaded, func() -> void:
		loaded_events.append(true)
		nested_results.append(SaveGame.save()))
	_listen(SaveGame.saved, func(target: String) -> void: saved_events.append(target))
	_listen(Village.changed, func(id: String) -> void: changed_events.append(id))
	_listen(Quests.advanced, func(_id: String, _step: int) -> void:
		nested_results.append(SaveGame.save(NESTED_PATH)))
	SaveGame.path = MISSING_PATH
	# Derive the actual filesystem's open error, without creating its missing parent.
	var unavailable := FileAccess.open(MISSING_PATH, FileAccess.WRITE)
	var write_error: Error = FileAccess.get_open_error()
	assert_object(unavailable).is_null()
	assert_int(write_error).is_not_equal(OK)
	var response: Dictionary = Village.restore_result("forge")
	assert_str(response.code).is_equal("save_failed")
	assert_dict(SaveGame.data).is_equal(before)
	assert_array(loaded_events).is_equal([true])
	assert_array(saved_events).is_empty()
	assert_array(changed_events).is_empty()
	assert_array(nested_results).is_equal([ERR_BUSY, ERR_BUSY])
	assert_array(_errors).is_equal([
		"SaveGame: nested save to a different path refused",
		"SaveGame: save during transaction rollback refused",
		"SaveGame: transaction save failed (%s)" % error_string(write_error)])
	assert_bool(FileAccess.file_exists(NESTED_PATH)).is_false()
	assert_bool(FileAccess.get_file_as_bytes(PATH) == bytes).is_true()
	SaveGame.path = PATH
	assert_bool(Village.restore("forge")).is_true()
	assert_int(SaveGame.data.glint).is_equal(40)
	assert_int(SaveGame.data.ledger.receipts.size()).is_equal(1)
	assert_int(saved_events.size()).is_equal(1)
	assert_int(changed_events.size()).is_equal(1)
	assert_int(loaded_events.size()).is_equal(1)

func _watch_restore() -> Dictionary:
	var trace := {"data": SaveGame.data.duplicate(true), "resume": SaveGame.resume.duplicate(true),
		"resume_unsaved": SaveGame.resume_unsaved, "loaded": [], "saved": [], "changed": []}
	_listen(SaveGame.loaded, func() -> void: trace.loaded.append(true))
	_listen(SaveGame.saved, func(target: String) -> void: trace.saved.append(target))
	_listen(Village.changed, func(id: String) -> void: trace.changed.append(id))
	return trace

func _assert_failed_restore(trace: Dictionary) -> void:
	assert_str(Village.restore_result("forge").code).is_equal("save_failed")
	assert_dict(SaveGame.data).is_equal(trace.data)
	assert_dict(SaveGame.resume).is_equal(trace.resume)
	assert_bool(SaveGame.resume_unsaved).is_equal(trace.resume_unsaved)
	assert_array(trace.loaded).is_equal([true])
	assert_array(trace.saved).is_empty()
	assert_array(trace.changed).is_empty()
	assert_int(_errors.size()).is_equal(1)
	assert_bool(_errors[0].begins_with("SaveGame: transaction save failed (")).is_true()

func test_failed_rename_rolls_back_without_publishing_and_removes_temp() -> void:
	assert_int(SaveGame.save()).is_equal(OK)
	var bytes := FileAccess.get_file_as_bytes(PATH)
	assert_int(DirAccess.make_dir_absolute(DIRECTORY_PATH)).is_equal(OK)
	SaveGame.path = DIRECTORY_PATH
	SaveGame.resume = {"zone": "woodland", "spawn": "start"}
	SaveGame.resume_unsaved = true
	var trace := _watch_restore()
	_assert_failed_restore(trace)
	assert_bool(DirAccess.dir_exists_absolute(DIRECTORY_PATH)).is_true()
	assert_bool(FileAccess.file_exists(DIRECTORY_PATH + ".tmp")).is_false()
	assert_bool(FileAccess.get_file_as_bytes(PATH) == bytes).is_true()

func test_newer_disk_save_refuses_restore_and_preserves_every_byte() -> void:
	_write({"version": SaveGame.VERSION + 1, "glint": 999, "extension": ["future"]})
	var bytes := FileAccess.get_file_as_bytes(PATH)
	var trace := _watch_restore()
	_assert_failed_restore(trace)
	assert_array(_errors).is_equal([
		"SaveGame: transaction save failed (%s)" % error_string(ERR_UNAVAILABLE)])
	assert_bool(FileAccess.get_file_as_bytes(PATH) == bytes).is_true()
	assert_bool(FileAccess.file_exists(PATH + ".tmp")).is_false()

func test_failed_legacy_import_blocks_restore_without_replacing_old_progress() -> void:
	_write({"version": 2, "glint": 137, "extension": "old progress"}, LEGACY_PATH)
	var bytes := FileAccess.get_file_as_bytes(LEGACY_PATH)
	# A real missing-directory copy failure, not an injected producer or fault flag.
	var import_error: Error = SaveGame._import_legacy_save(LEGACY_PATH, MISSING_PATH)
	assert_int(import_error).is_not_equal(OK)
	SaveGame.path = MISSING_PATH
	var trace := _watch_restore()
	_assert_failed_restore(trace)
	assert_array(_errors).is_equal([
		"SaveGame: transaction save failed (%s)" % error_string(import_error)])
	assert_bool(FileAccess.get_file_as_bytes(LEGACY_PATH) == bytes).is_true()
	assert_bool(FileAccess.file_exists(MISSING_PATH)).is_false()
	assert_bool(FileAccess.file_exists(MISSING_PATH + ".tmp")).is_false()
	assert_bool(FileAccess.file_exists(MISSING_PATH + ".name-migration.tmp")).is_false()

func test_busy_and_invalid_transactions_do_not_invoke_rejected_callbacks() -> void:
	var calls: Array = []
	var nested: Array = []
	var inner := func() -> void: calls.append("inner")
	var outer := func() -> void:
		nested.append(SaveGame.commit_transaction(inner))
		SaveGame.data.glint = 69
	assert_int(SaveGame.commit_transaction(outer)).is_equal(OK)
	assert_array(calls).is_empty()
	assert_array(nested).is_equal([ERR_BUSY])
	assert_array(_errors).is_equal(["SaveGame: nested transaction refused"])
	assert_int(SaveGame.data.glint).is_equal(69)
	var bytes := FileAccess.get_file_as_bytes(PATH)
	SaveGame.data.player = []
	var invalid := SaveGame.data.duplicate(true)
	_errors.clear()
	assert_int(SaveGame.commit_transaction(inner)).is_equal(ERR_INVALID_DATA)
	assert_array(calls).is_empty()
	assert_array(_errors).is_equal(["SaveGame: transaction has invalid save data"])
	assert_dict(SaveGame.data).is_equal(invalid)
	assert_bool(FileAccess.get_file_as_bytes(PATH) == bytes).is_true()
	assert_bool(FileAccess.file_exists(PATH + ".tmp")).is_false()

func test_boot_ignores_crash_temp_then_v2_restore_reload_keeps_one_receipt() -> void:
	var v2 := SaveGame.data.duplicate(true)
	v2.version = 2
	v2.erase("ledger")
	v2.extension = JSON.parse_string('{"opaque": [1, {"keep": true}]}')
	_write(v2)
	var bytes := FileAccess.get_file_as_bytes(PATH)
	_write({"version": 2, "glint": 999, "village": {"restored": {"forge": 1}}}, PATH + ".tmp")
	SaveGame.reset()
	assert_int(SaveGame.boot()).is_equal(OK)
	assert_int(SaveGame.data.glint).is_equal(70)
	assert_bool(Village.is_restored("forge")).is_false()
	assert_int(SaveGame.data.ledger.opening.from_version).is_equal(2)
	assert_int(SaveGame.data.ledger.opening.glint).is_equal(70)
	assert_array(SaveGame.data.ledger.receipts).is_empty()
	assert_dict(SaveGame.data.extension).is_equal(v2.extension)
	assert_bool(FileAccess.get_file_as_bytes(PATH) == bytes).is_true()
	assert_bool(Village.restore("forge")).is_true()
	assert_int(SaveGame.data.glint).is_equal(40)
	assert_int(SaveGame.data.ledger.receipts.size()).is_equal(1)
	assert_bool(FileAccess.file_exists(PATH + ".tmp")).is_false()
	var committed := SaveGame.data.duplicate(true)
	bytes = FileAccess.get_file_as_bytes(PATH)
	SaveGame.reset()
	assert_int(SaveGame.load_save()).is_equal(OK)
	assert_dict(SaveGame.data).is_equal(committed)
	assert_str(Village.restore_result("forge").code).is_equal("duplicate")
	assert_int(SaveGame.data.glint).is_equal(40)
	assert_int(SaveGame.data.ledger.receipts.size()).is_equal(1)
	assert_bool(FileAccess.get_file_as_bytes(PATH) == bytes).is_true()
	assert_array(_errors).is_empty()

func test_damaged_ledger_quarantines_raw_without_reset_or_recharge() -> void:
	var raw: Dictionary = JSON.parse_string('{"receipts": "damaged", "keep": [1, "opaque"]}')
	var doc := SaveGame.data.duplicate(true)
	doc.glint = -3
	doc.village.restored.forge = 1
	doc.ledger = raw.duplicate(true)
	doc.extension = {"keep": "progress"}
	_write(doc)
	var bytes := FileAccess.get_file_as_bytes(PATH)
	SaveGame.reset()
	assert_int(SaveGame.load_save()).is_equal(OK)
	assert_int(SaveGame.data.glint).is_equal(-3)
	assert_int(Village.tier("forge")).is_equal(1)
	assert_dict(SaveGame.data.ledger_quarantine).is_equal(raw)
	assert_dict(SaveGame.data.extension).is_equal(doc.extension)
	assert_dict(SaveGame.data.quests).is_equal(doc.quests)
	assert_array(SaveGame.data.ledger.receipts).is_empty()
	assert_int(SaveGame.data.ledger.opening.glint).is_equal(-3)
	assert_int(SaveGame.data.ledger.opening.restored.forge).is_equal(1)
	var loaded := SaveGame.data.duplicate(true)
	assert_str(Village.restore_result("forge").code).is_equal("already_restored")
	assert_bool(Village.restore("forge")).is_false()
	assert_dict(SaveGame.data).is_equal(loaded)
	assert_bool(FileAccess.get_file_as_bytes(PATH) == bytes).is_true()
	# Explicit persistence keeps the quarantine beside the now-valid empty ledger.
	assert_int(SaveGame.save()).is_equal(OK)
	SaveGame.reset()
	assert_int(SaveGame.load_save()).is_equal(OK)
	assert_dict(SaveGame.data).is_equal(loaded)
	assert_str(Village.restore_result("forge").code).is_equal("already_restored")
	assert_array(_errors).is_empty()

func _assert_gated_restore_stays_in_memory(resume_unsaved := false) -> void:
	assert_int(SaveGame.save()).is_equal(OK)
	SaveGame.resume_unsaved = resume_unsaved
	var bytes := FileAccess.get_file_as_bytes(PATH)
	var ledger: Dictionary = SaveGame.data.ledger.duplicate(true)
	var events: Array = []
	var saves: Array = []
	_listen(SaveGame.saved, func(target: String) -> void: saves.append(target))
	_listen(Quests.advanced, func(id: String, _step: int) -> void:
		if id == "cold_forge":
			events.append("quest")
			SaveGame.save())
	_listen(Village.changed, func(_id: String) -> void:
		events.append("changed")
		SaveGame.save())
	assert_bool(Village.restore("forge")).is_true()
	assert_int(SaveGame.data.glint).is_equal(40)
	assert_int(Village.tier("forge")).is_equal(1)
	assert_array(events).is_equal(["quest", "changed"])
	assert_array(saves).is_empty()
	assert_dict(SaveGame.data.ledger).is_equal(ledger)
	assert_bool(FileAccess.get_file_as_bytes(PATH) == bytes).is_true()
	assert_bool(FileAccess.file_exists(PATH + ".tmp")).is_false()
	assert_array(_errors).is_empty()

func test_picture_demo_guidance_gate_keeps_restore_in_memory() -> void:
	var game: GateGame = auto_free(GateGame.new())
	game.hud = GateHud.new()
	game.add_child(game.hud)
	get_tree().root.add_child(game)
	game.add_to_group("game")
	_assert_gated_restore_stays_in_memory()

func test_lab_resume_migration_observer_cannot_persist_gated_restore() -> void:
	var zone: Zone = auto_free(Zone.new())
	zone.zone_id = "test_ledger_lab"
	var ground := LabGround.new()
	ground.name = "Ground"
	zone.add_child(ground)
	Zones.current = zone
	assert_bool(Zones.in_lab()).is_true()
	SaveGame.resume = {"zone": "woodland", "spawn": "start"}
	# This is game.gd's permitted one-off lab migration save, observed during notify.
	_listen(Quests.advanced, func(_id: String, _step: int) -> void:
		if Zones.in_lab() and SaveGame.resume_unsaved:
			SaveGame.save())
	_assert_gated_restore_stays_in_memory(true)
	assert_bool(SaveGame.resume_unsaved).is_true()
