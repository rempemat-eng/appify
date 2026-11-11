extends Node
## Data-driven quests (game-design.md 8.3). Each quest is a JSON file in res://data/quests/:
##
##   { "id": "woodland_stones", "title": "...", "kind": "main",
##     "start":   { "on": "talk:stone_sign", "if": { ...condition... } },
##     "steps":   [ { "id": "clear_camp", "text": "...", "on": "camp:willow",
##                    "done_if": { "flags": ["camp_cleared:willow"] }, "set_flags": [] }, ... ],
##     "rewards": { "glint": 40, "flags": ["..."] },
##     "next_visit_flags": ["..."] }      (optional: set at the next zone load once the quest has started)
##
## The world reports what happens as plain event strings through `notify()`: "talk:<speaker>",
## "camp:<camp>", "enter:<zone>", "restore:<id>", "pickup:<item>". A step completes when its `on` event arrives and its
## `if` condition holds, or at once when its `done_if` condition already holds (so clearing a camp before
## taking the quest still counts). Progress lives in SaveGame.data.quests[id] = {state, step}.
## A quest never expires and never runs on a clock (8.3).
##
## Conditions (also used by dialogue): { "flags": [..], "not_flags": [..], "done": [quest ids],
## "active": [quest ids], "not_started": [quest ids], "started": [quest ids], "step": [quest id, step id],
## "past": [quest id, step id], "not_past": [quest id, step id], "restored": [restore ids],
## "not_restored": [restore ids], "glint_at_least": n }; all must hold.
## "started" is active or done; "past" holds once the quest has left that step behind (or is done).
## The flag "zone_built:<zone id>" is not in the save: it holds while that zone is in this build
## (has_flag below). Restores live in SaveGame.data.village.restored (core/village.gd).
## Quest and dialogue files keep to the operators scripts/narrative/validate.py knows (check:quests);
## "started", "past" and "not_past" are for zone plans, zone scenes and data/leads.json.
##
## The HUD tracks one quest: the active quest that moved last (SaveGame.data.tracked). With no quest
## active it shows a lead instead, the first entry of data/leads.json whose condition holds, so the
## player always has a line saying where the story goes on.

signal started(id: String)
signal advanced(id: String, step: int)
signal completed(id: String)

const DIR := "res://data/quests"
const LEADS := "res://data/leads.json"
const ZONE_BUILT := "zone_built:"

var defs: Dictionary = {}
var leads: Array = []
var cards: Array = []

func _ready() -> void:
	load_dir(DIR)
	var doc: Variant = JSON.parse_string(FileAccess.get_file_as_string(LEADS)) if FileAccess.file_exists(LEADS) else null
	if typeof(doc) == TYPE_DICTIONARY:
		leads = doc.get("leads", [])
		cards = doc.get("cards", [])
	SaveGame.loaded.connect(shelve_unbuilt)
	shelve_unbuilt()   # the save was read before this autoload woke (core/save_game.gd boot)

## A save can hold an active quest that this build cannot start: its start condition asks for a zone
## that is not built ("zone_built:<zone>"), and the save was made by a build without that gate. Such a
## quest could never finish here, so it goes back to not started; its giver offers it again when the
## zone lands. Run on every load.
func shelve_unbuilt() -> void:
	for id: String in defs:
		if state(id) != "active":
			continue
		for f: String in defs[id].get("start", {}).get("if", {}).get("flags", []):
			if f.begins_with(ZONE_BUILT) and not has_flag(f):
				SaveGame.data.quests.erase(id)
				if str(SaveGame.data.get("tracked", "")) == id:
					SaveGame.data.tracked = ""
				break

func load_dir(dir: String) -> void:
	for f in DirAccess.get_files_at(dir):
		if f.ends_with(".json"):
			add_def(JSON.parse_string(FileAccess.get_file_as_string(dir.path_join(f))))

func add_def(def: Variant) -> void:
	if typeof(def) != TYPE_DICTIONARY or not def.has("id") or not def.has("steps"):
		push_error("Quests: a quest needs an id and steps: %s" % str(def).left(80))
		return
	defs[def.id] = def

# --- state ---------------------------------------------------------------------
func _rec(id: String) -> Dictionary:
	return SaveGame.data.quests.get(id, {})

func state(id: String) -> String:
	return _rec(id).get("state", "none")

func step_index(id: String) -> int:
	return int(_rec(id).get("step", 0))

func current_step(id: String) -> Dictionary:
	if state(id) != "active":
		return {}
	return defs[id].steps[step_index(id)]

## The quest the HUD tracks: the active quest that moved last, else any active quest, else "".
func tracked_id() -> String:
	var id := str(SaveGame.data.get("tracked", ""))
	if defs.has(id) and state(id) == "active":
		return id
	for other: String in defs:
		if state(other) == "active":
			return other
	return ""

## The first title card (data/leads.json "cards") whose condition holds and which this save has not
## shown yet (flag "seen:<id>"), or {}. game.gd shows it and sets the flag.
func due_card() -> Dictionary:
	for card: Dictionary in cards:
		if not SaveGame.has_flag("seen:" + str(card.get("id", ""))) and check(card.get("if")):
			return card
	return {}

## The lead shown while no quest is active: {"title", "text"} of the first entry of data/leads.json
## whose condition holds, or {}.
func lead() -> Dictionary:
	for entry: Dictionary in leads:
		if check(entry.get("if")):
			return entry
	return {}

## "Title: text" for the HUD: the tracked quest's current step, or (unless `with_lead` is false) the
## lead when no quest is active.
func tracked_text(with_lead := true) -> String:
	var id := tracked_id()
	if id != "":
		return "%s: %s" % [defs[id].get("title", id), current_step(id).get("text", "")]
	var l := lead() if with_lead else {}
	if l.is_empty():
		return ""
	return "%s: %s" % [l.get("title", ""), l.get("text", "")]

# --- conditions ----------------------------------------------------------------
## A flag as conditions see it: the save's flags, plus "zone_built:<zone id>", which is never saved and
## holds while that zone is in this build (data/zones.json). A quest whose places are not built yet
## asks for it in its start condition, so it cannot start and then wait on things that do not exist.
func has_flag(flag: String) -> bool:
	if flag.begins_with(ZONE_BUILT):
		return Zones.has_zone(flag.trim_prefix(ZONE_BUILT))
	return SaveGame.has_flag(flag)

func check(cond: Variant) -> bool:
	if typeof(cond) != TYPE_DICTIONARY:
		return true
	for f in cond.get("flags", []):
		if not has_flag(f):
			return false
	for f in cond.get("not_flags", []):
		if has_flag(f):
			return false
	for q in cond.get("done", []):
		if state(q) != "done":
			return false
	for q in cond.get("active", []):
		if state(q) != "active":
			return false
	for q in cond.get("not_started", []):
		if state(q) != "none":
			return false
	for q in cond.get("started", []):
		if state(q) == "none":
			return false
	if cond.has("past") and not is_past(cond.past[0], cond.past[1]):
		return false
	if cond.has("not_past") and is_past(cond.not_past[0], cond.not_past[1]):
		return false
	var restored: Dictionary = SaveGame.data.village.restored
	for r in cond.get("restored", []):
		if int(restored.get(r, 0)) <= 0:
			return false
	for r in cond.get("not_restored", []):
		if int(restored.get(r, 0)) > 0:
			return false
	if int(SaveGame.data.glint) < int(cond.get("glint_at_least", 0)):
		return false
	if cond.has("step"):
		var qid: String = cond.step[0]
		if state(qid) != "active" or current_step(qid).get("id", "") != cond.step[1]:
			return false
	return true

## True once quest `id` has left step `step_id` behind: it is done, or active at a later step.
func is_past(id: String, step_id: String) -> bool:
	match state(id):
		"done":
			return true
		"active":
			var steps: Array = defs[id].steps
			for i in steps.size():
				if steps[i].get("id", "") == step_id:
					return step_index(id) > i
	return false

## Called by Zones just before a zone loads (a door, getting up after being downed, the start of the
## game): every started quest's `next_visit_flags` are set. A quest uses it for what happens off
## screen once the player has moved on: Hale stays on the woodland path while the player is still
## there, and stands in Crossroads from the next load ("hale_walked_home", The road home).
func zone_loading() -> void:
	for id: String in defs:
		if state(id) != "none":
			for f: String in defs[id].get("next_visit_flags", []):
				SaveGame.set_flag(f)

# --- events --------------------------------------------------------------------
## Reports something that happened. Active quests move first, then quests that start on this event.
## Returns true when any quest changed.
func notify(event: String) -> bool:
	var changed := false
	for id in defs.keys():
		if state(id) == "active":
			var step := current_step(id)
			if step.get("on", "") == event and check(step.get("if")):
				_advance(id)
				changed = true
	for id in defs.keys():
		var def: Dictionary = defs[id]
		var start: Dictionary = def.get("start", {})
		if state(id) == "none" and start.get("on", "") == event and check(start.get("if")):
			start_quest(id)
			changed = true
	return changed

func start_quest(id: String) -> void:
	if not defs.has(id) or state(id) != "none":
		return
	SaveGame.data.quests[id] = {"state": "active", "step": 0}
	SaveGame.data.tracked = id
	started.emit(id)
	_settle(id)

func _advance(id: String) -> void:
	var step := current_step(id)
	for f in step.get("set_flags", []):
		SaveGame.set_flag(f)
	var next := step_index(id) + 1
	if next >= defs[id].steps.size():
		_complete(id)
		return
	SaveGame.data.quests[id].step = next
	SaveGame.data.tracked = id
	advanced.emit(id, next)
	_settle(id)

## Completes steps whose done_if already holds.
func _settle(id: String) -> void:
	if state(id) == "active":
		var step := current_step(id)
		if step.has("done_if") and check(step.done_if):
			_advance(id)

func _complete(id: String) -> void:
	var rewards: Dictionary = defs[id].get("rewards", {})
	SaveGame.add_glint(int(rewards.get("glint", 0)))
	for f in rewards.get("flags", []):
		SaveGame.set_flag(f)
	SaveGame.data.quests[id] = {"state": "done", "step": defs[id].steps.size()}
	completed.emit(id)
