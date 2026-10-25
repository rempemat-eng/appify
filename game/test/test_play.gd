extends GdUnitTestSuite
## Plays the main scene through its real input map: walk to the sign, read it with E through the
## dialogue box, and the quest starts. Uses GdUnit's scene runner (simulated keys, real frames).

const SAVE := "user://test_play_save.json"

func before_test() -> void:
	SaveGame.reset()
	SaveGame.path = SAVE

func after_test() -> void:
	SaveGame.path = SaveGame.DEFAULT_PATH
	DirAccess.remove_absolute(ProjectSettings.globalize_path(SAVE))

## Frames run unthrottled in headless tests, so wait on physics ticks, not process frames.
func _ticks(n: int) -> void:
	for i in n:
		await get_tree().physics_frame

func _press(runner: GdUnitSceneRunner, key: Key) -> void:
	runner.simulate_key_pressed(key)
	await _ticks(3)

func test_read_the_sign_with_e() -> void:
	var runner := scene_runner("res://main.tscn")
	await _ticks(5)
	var player := runner.find_child("Player") as Player
	assert_object(player).is_not_null()
	player.use_mouse_aim = false
	player.global_position = Vector2(372, 1125)  # just south of the stone sign
	await _ticks(5)
	assert_object(player.focus).is_not_null()
	await _press(runner, KEY_E)
	var box := runner.find_child("DialogueBox") as Control
	assert_bool(box.visible).is_true()
	assert_bool(Dialogue.busy).is_true()
	for i in 6:  # finish and advance each line, then close
		if box.visible:
			await _press(runner, KEY_E)
	assert_bool(box.visible).is_false()
	await _ticks(20)
	assert_bool(Dialogue.busy).is_false()
	assert_str(Quests.state("woodland_stones")).is_equal("active")
	assert_bool(FileAccess.file_exists(SAVE)).is_true()  # the quest start autosaved

func test_space_rolls() -> void:
	var runner := scene_runner("res://main.tscn")
	await _ticks(5)
	var player := runner.find_child("Player") as Player
	player.use_mouse_aim = false
	runner.simulate_key_pressed(KEY_SPACE)
	await _ticks(2)
	assert_bool(player.is_rolling()).is_true()
	assert_int(player.roll_charges).is_equal(Player.ROLL_CHARGES - 1)
