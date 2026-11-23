extends GdUnitTestSuite
## The real forge restore, real SaveGame disk boundary and real cold_forge quest.
## Files are disposable user://test_* paths, never a player's default save.

const PATH := "user://test_village_restore_ledger.json"
const NESTED_PATH := PATH + ".nested"
const MISSING_PATH := "user://test_village_restore_ledger_missing/save.json"
const FIXTURES := "res://test/fixtures/saves/"

var _before := {}
var _connections: Array[Dictionary] = []

func before_test() -> void:
	_before = {"data": SaveGame.data.duplicate(true), "path": SaveGame.path,
		"resume": SaveGame.resume.duplicate(true), "resume_unsaved": SaveGame.resume_unsaved,
		"sites": Village.sites.duplicate(true)}
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
	Village.sites = _before.sites
	for target: String in [PATH, PATH + ".tmp", NESTED_PATH, NESTED_PATH + ".tmp"]:
		DirAccess.remove_absolute(ProjectSettings.globalize_path(target))

func _listen(event: Signal, callback: Callable) -> void:
	event.connect(callback)
	_connections.append({"signal": event, "callback": callback})

func _write(doc: Dictionary) -> void:
	var file := FileAccess.open(PATH, FileAccess.WRITE)
	file.store_string(JSON.stringify(doc))
	file.close()

func test_real_restore_save_new_session_load_and_repeat_has_one_receipt() -> void:
	var events: Array = []
	var nested_results: Array = []
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
	SaveGame.data.extension = {"opaque": [1, {"keep": true}]}
	var result: Dictionary = Village.restore_result("forge")
	assert_bool(result.ok and result.applied).is_true()
	assert_str(result.code).is_equal("applied")
	assert_int(SaveGame.data.glint).is_equal(40)
	assert_int(Village.tier("forge")).is_equal(1)
	assert_str(Quests.state("cold_forge")).is_equal("done")
	assert_bool(SaveGame.has_flag("forge_open") and SaveGame.has_flag("undercroft_open")).is_true()
	# One atomic restore write, then the existing success observer's normal save.
	assert_array(events).is_equal([["saved", PATH], ["changed", "forge"], ["saved", PATH]])
	assert_array(nested_results).is_equal([OK, OK, OK])
	assert_bool(FileAccess.file_exists(NESTED_PATH)).is_false()
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
	_listen(SaveGame.loaded, func() -> void: loaded_events.append(true))
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
	var responses: Array = []
	# GdUnit's expected-error assertion is real, but check.sh's raw ERROR rejection
	# still needs lead disposition before allocating runtime; no suppression is applied.
	await assert_error(func() -> void: responses.append(Village.restore_result("forge"))).is_push_error(
		"SaveGame: transaction save failed (%s)" % error_string(write_error))
	assert_str(responses[0].code).is_equal("save_failed")
	assert_dict(SaveGame.data).is_equal(before)
	assert_array(loaded_events).is_equal([true])
	assert_array(saved_events).is_empty()
	assert_array(changed_events).is_empty()
	assert_array(nested_results).is_equal([OK])
	assert_bool(FileAccess.file_exists(NESTED_PATH)).is_false()
	assert_bool(FileAccess.get_file_as_bytes(PATH) == bytes).is_true()
	SaveGame.path = PATH
	assert_bool(Village.restore("forge")).is_true()
	assert_int(SaveGame.data.glint).is_equal(40)
	assert_int(SaveGame.data.ledger.receipts.size()).is_equal(1)
	assert_int(saved_events.size()).is_equal(1)
	assert_int(changed_events.size()).is_equal(1)
	assert_int(loaded_events.size()).is_equal(1)
