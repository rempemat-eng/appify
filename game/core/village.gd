extends Node
## Crossroads' restoration (game-design.md 7.1 to 7.3; docs/vision/vertical-slice.md). Reads the zone
## plans in res://data/plans/*.json: each plan's `restores` (id, name, cost in Glint, optional `if`
## condition) and `stages` (ordered; the last whose `if` holds is the plan's stage).
##
## Restored buildings live in SaveGame.data.village.restored[id] = tier (1 for now), so they persist with
## the save. `restore(id)` pays the cost, records the tier, emits `changed` and reports "restore:<id>" to
## the quests. Work is instant once paid: no timers (7.3). Quest conditions read the same record through
## the "restored" and "not_restored" keys (core/quests.gd).

signal changed(id: String)

const DIR := "res://data/plans"

var plans: Dictionary = {}
var sites: Dictionary = {}  ## restore id -> its entry, with "plan" added

func _ready() -> void:
	load_dir(DIR)

func load_dir(dir: String) -> void:
	for f in DirAccess.get_files_at(dir):
		if f.ends_with(".json"):
			var doc: Variant = JSON.parse_string(FileAccess.get_file_as_string(dir.path_join(f)))
			if typeof(doc) != TYPE_DICTIONARY or not doc.has("id"):
				push_error("Village: %s is not a plan" % f)
				continue
			plans[doc.id] = doc
			for r in doc.get("restores", []):
				var site: Dictionary = r.duplicate()
				site.plan = doc.id
				sites[r.id] = site

func tier(id: String) -> int:
	return int(SaveGame.data.village.restored.get(id, 0))

func is_restored(id: String) -> bool:
	return tier(id) > 0

func cost(id: String) -> int:
	return int(sites.get(id, {}).get("cost", {}).get("glint", 0))

## True when `id` is a known site, not yet restored, its condition holds and the Glint is there.
func can_restore(id: String) -> bool:
	if not sites.has(id) or is_restored(id):
		return false
	return Quests.check(sites[id].get("if")) and int(SaveGame.data.glint) >= cost(id)

func restore(id: String) -> bool:
	if not can_restore(id):
		return false
	SaveGame.add_glint(-cost(id))
	SaveGame.data.village.restored[id] = 1
	changed.emit(id)
	Quests.notify("restore:" + id)
	return true

## The plan's current stage id: the last entry of `stages` whose condition holds ("" without stages).
func stage(plan_id: String) -> String:
	var out := ""
	for s in plans.get(plan_id, {}).get("stages", []):
		if Quests.check(s.get("if")):
			out = s.id
	return out
