extends GdUnitTestSuite
## What the slice says against what it shows and delivers (the mechanics review of 14 Nov: the rules were
## sound, the story around them thin). Each test reads the dialogue and quest data as the game loads it.

const DIALOGUE := "res://data/dialogue"

## Every line of every speaker in data/dialogue: [[file, speaker, line], ...].
func _lines() -> Array:
	var out := []
	for f in DirAccess.get_files_at(DIALOGUE):
		if not f.ends_with(".json"):
			continue
		var doc: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(DIALOGUE.path_join(f)))
		for speaker: String in doc:
			for entry: Dictionary in doc[speaker].get("entries", []):
				for line: String in entry.get("lines", []):
					out.append([f, speaker, line])
	return out

## The shard lantern stands on its own ring of setts, 20 px of paving from the well (13 Nov). No line
## may put it on the well or run its light down its iron into it; its light still reaches the well
## (the homecoming clears it: decisions-2026-11-11.md, "the lantern clears it").
func test_no_line_puts_the_shard_lantern_on_the_well() -> void:
	var lantern_lines := 0
	for l: Array in _lines():
		var line := String(l[2])
		if not line.to_lower().contains("lantern") and l[1] != "shard_lantern":
			continue
		lantern_lines += 1
		for wrong: String in ["beside the well", "lantern by the well", "into the well", "down the iron", "iron lantern"]:
			assert_bool(line.contains(wrong)).override_failure_message(
				"%s, %s: \"%s\" says \"%s\", and the lantern stands on its own in the square" % [l[0], l[1], line, wrong]).is_false()
	assert_int(lantern_lines).is_greater(8)
	# the three lines that were reworded still carry the light to the well
	SaveGame.reset()
	assert_str(Dialogue.lines_for("shard_lantern")[0]).contains("on its ring of setts").contains("empty cradles")
	SaveGame.data.quests["under_the_stones"] = {"state": "active", "step": 4}
	assert_str(Dialogue.lines_for("shard_lantern")[0]).contains("You lift the shard").contains("to the well")
	for f: String in ["shard_home:woodland", "shard_home:frostline", "shard_home:brackens"]:
		SaveGame.set_flag(f)
	assert_str(Dialogue.lines_for("shard_lantern")[0]).contains("Three great shards").contains("to the well")
	SaveGame.reset()
