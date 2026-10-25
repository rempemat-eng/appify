extends GdUnitTestSuite
## The save survives a round trip through JSON, and older or partial documents load into the current shape.

const PATH := "user://test_save.json"

func before_test() -> void:
	SaveGame.reset()

func after_test() -> void:
	DirAccess.remove_absolute(ProjectSettings.globalize_path(PATH))

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
