extends Node
## Data-driven quests (game-design.md 8.3). Each quest is a JSON file in res://data/quests/:
##
##   { "id": "woodland_stones", "title": "...", "kind": "main",
##     "start":   { "on": "talk:stone_sign", "if": { ...condition... } },
##     "steps":   [ { "id": "clear_camp", "text": "...", "on": "camp:willow",
##                    "done_if": { "flags": ["camp_cleared:willow"] }, "set_flags": [] }, ... ],
##     "rewards": { "glint": 40, "flags": ["..."] } }
##
## The world reports what happens as plain event strings through `notify()`: "talk:<speaker>",
## "camp:<camp>", "enter:<zone>", "pickup:<item>". A step completes when its `on` event arrives and its
## `if` condition holds, or at once when its `done_if` condition already holds (so clearing a camp before
## taking the quest still counts). Progress lives in SaveGame.data.quests[id] = {state, step}.
## A quest never expires and never runs on a clock (8.3).
##
## Conditions (also used by dialogue): { "flags": [..], "not_flags": [..], "done": [quest ids],
## "active": [quest ids], "not_started": [quest ids], "step": [quest id, step id] }; all must hold.

signal started(id: String)
signal advanced(id: String, step: int)
signal completed(id: String)

const DIR := "res://data/quests"

var defs: Dictionary = {}

func _ready() -> void:
	load_dir(DIR)

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

## The text of the first active quest's current step, for the HUD.
func tracked_text() -> String:
	for id in defs:
		if state(id) == "active":
			return "%s: %s" % [defs[id].get("title", id), current_step(id).get("text", "")]
	return ""

# --- conditions ----------------------------------------------------------------
func check(cond: Variant) -> bool:
	if typeof(cond) != TYPE_DICTIONARY:
		return true
	for f in cond.get("flags", []):
		if not SaveGame.has_flag(f):
			return false
	for f in cond.get("not_flags", []):
		if SaveGame.has_flag(f):
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
	if cond.has("step"):
		var qid: String = cond.step[0]
		if state(qid) != "active" or current_step(qid).get("id", "") != cond.step[1]:
			return false
	return true

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
