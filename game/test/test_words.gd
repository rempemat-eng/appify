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

## Nothing the slice's people say promises what the slice does not deliver (15 Nov). There is no weapon
## upgrade (and Bramble carries a bow, not a blade), no tonics or flasks, no seeds or planting, no
## companion who comes along, no bounties, and the bell tower is not built. Read over the three zones'
## files and act 1's lines for the same speakers, with the quest text the tracker shows.
const PROMISES := {
	"your blade": "there is no weapon upgrade, and Bramble's weapon is a bow",
	"flask": "nothing fills a flask",
	"onics for the road": "Morel sells no tonics",
	"seed": "nothing can be planted",
	"lant them": "nothing can be planted",
	"terrace beds": "the terrace beds cannot be planted",
	"dig your beds": "the terrace beds cannot be planted",
	"what grows": "nothing can be planted",
	"ake me with you": "nobody joins the player in the slice",
	"ounties": "there are no bounties",
	"BELL TOWER WILL": "the bell tower is not built, and the first night is signalled without it",
	"APOTHECARY OPEN": "the apothecary offers nothing yet",
	"first upgrade": "there is no weapon upgrade",
}
## Speakers the three-zone slice can meet (data/dialogue/crossroads.json, woodland.json, undercroft.json),
## whose lines in other files (act 1's) count too.
func _slice_speakers() -> Dictionary:
	var out := {}
	for f: String in ["crossroads.json", "woodland.json", "undercroft.json"]:
		var doc: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(DIALOGUE.path_join(f)))
		for speaker: String in doc:
			out[speaker] = true
	return out

func test_no_line_of_the_slice_promises_what_it_does_not_deliver() -> void:
	var speakers := _slice_speakers()
	var read := 0
	for l: Array in _lines():
		if not speakers.has(l[1]) or l[0] in ["raids.json", "frostline.json", "brackens.json"]:
			continue          # raids.json is the first night's own file (its lines change with Matt's 13 Nov answers)
		read += 1
		for promise: String in PROMISES:
			assert_bool(String(l[2]).contains(promise)).override_failure_message(
				"%s, %s: \"%s\" (%s)" % [l[0], l[1], l[2], PROMISES[promise]]).is_false()
	assert_int(read).is_greater(80)
	# the quest text the tracker and a later journal show, for the quests this build can start
	for id: String in ["woodland_stones", "road_to_crossroads", "cold_forge", "under_the_stones", "home_again", "a1_the_torn_roof"]:
		var def: Dictionary = Quests.defs[id]
		var texts := [String(def.get("title", "")), String(def.get("summary", ""))]
		for step: Dictionary in def.steps:
			texts.append(String(step.get("text", "")))
		for text: String in texts:
			for promise: String in PROMISES:
				assert_bool(text.contains(promise)).override_failure_message("%s: \"%s\" (%s)" % [id, text, PROMISES[promise]]).is_false()

## The voices stay: each rewritten line is still said at the same moment by the same person.
func test_the_rewritten_lines_show_where_the_old_ones_did() -> void:
	SaveGame.reset()
	for q: String in ["woodland_stones", "road_to_crossroads", "cold_forge", "under_the_stones"]:
		SaveGame.data.quests[q] = {"state": "done", "step": Quests.defs[q].steps.size()}
	assert_str(" ".join(Dialogue.lines_for("hale"))).contains("The lantern hums").contains("hinges")
	assert_str(" ".join(Dialogue.lines_for("morel"))).contains("bakery's yard").contains("nowhere dry")
	assert_str(" ".join(Dialogue.lines_for("notice_board"))).contains("THE LANTERN IS LIT")
	SaveGame.data.village.restored["fern_cottage"] = 1
	assert_str(" ".join(Dialogue.lines_for("ada_fern"))).contains("Our door!").contains("front step")
	SaveGame.data.quests["home_again"] = {"state": "done", "step": 2}
	assert_str(" ".join(Dialogue.lines_for("ada_fern"))).contains("kettle")
	assert_str(" ".join(Dialogue.lines_for("morel"))).contains("My roof is still in the bakery's yard").contains("before the winter")
	SaveGame.data.quests["a1_the_torn_roof"] = {"state": "active", "step": 1}
	assert_str(" ".join(Dialogue.lines_for("morel"))).contains("A roof!").contains("When the Col Path opens")
	SaveGame.data.quests["a1_the_torn_roof"] = {"state": "done", "step": 2}
	assert_str(" ".join(Dialogue.lines_for("morel"))).contains("Nothing worth bottling yet")
	assert_str(" ".join(Dialogue.lines_for("notice_board"))).contains("MOREL HAS A ROOF AGAIN").contains("COL PATH TO THE FROSTLINE STILL BURIED")
	SaveGame.reset()
