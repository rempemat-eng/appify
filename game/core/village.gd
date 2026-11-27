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
	return bool(restore_result(id).get("applied", false))

## Only the existing forge uses the durable ledger in this step. Other restores
## retain their existing payment/notification path and do not acquire receipts.
func restore_result(id: String) -> Dictionary:
	if id == "forge":
		return _restore_forge(id)
	if not can_restore(id):
		return {"ok": false, "applied": false, "code": "not_available"}
	SaveGame.add_glint(-cost(id))
	SaveGame.data.village.restored[id] = 1
	changed.emit(id)
	Quests.notify("restore:" + id)
	return {"ok": true, "applied": true, "code": "applied"}

func _restore_forge(id: String) -> Dictionary:
	# Stored applied payloads always say eligible=true. Do not reinterpret a
	# repeat using a quest condition that may have changed since the first call.
	var event := {"id": "restore:%s:t1" % id, "kind": "spend", "amount": cost(id),
		"source": "restore:" + id, "category": "restoration", "item": id, "eligible": true}
	var expected: Dictionary = event.duplicate(true)
	expected.tier = 1
	var ledger: Variant = SaveGame.data.get("ledger", {})
	if not ledger is Dictionary or not ledger.get("receipts", []) is Array:
		return {"ok": false, "applied": false, "code": "invalid_ledger"}
	for receipt: Variant in ledger.get("receipts", []):
		if receipt is Dictionary and receipt.get("id") == event.id:
			if receipt != expected:
				return {"ok": false, "applied": false, "code": "id_conflict"}
			return {"ok": true, "applied": false, "code": "duplicate", "receipt": receipt.duplicate(true)}
	if is_restored(id):
		return {"ok": true, "applied": false, "code": "already_restored"}
	if not sites.has(id) or not Quests.check(sites[id].get("if")):
		return {"ok": false, "applied": false, "code": "not_eligible"}
	if int(SaveGame.data.glint) < cost(id):
		return {"ok": false, "applied": false, "code": "insufficient_funds"}
	if not _restoration_writes_allowed():
		# Keep the existing picture/demo/lab behavior: apply in memory, no durable receipt.
		var in_memory := func() -> void:
			SaveGame.add_glint(-cost(id))
			SaveGame.data.village.restored[id] = 1
			Quests.notify("restore:" + id)
			changed.emit(id)
		SaveGame.apply_in_memory(in_memory)
		return {"ok": true, "applied": true, "code": "applied"}
	# This state is transaction-local validation only. SaveGame's signed purse
	# remains authoritative; a negative purse never reaches fresh().
	var initial := GlintEconomy.fresh(SaveGame.data.glint)
	if not initial.ok:
		return initial
	var applied := GlintEconomy.apply(initial.state, event)
	if not applied.ok:
		return applied
	var stored: Dictionary = applied.receipt.duplicate(true)
	stored.tier = 1
	var change := func() -> void:
		SaveGame.data.glint = applied.state.balance
		SaveGame.data.village.restored[id] = 1
		SaveGame.data.ledger.receipts.append(stored.duplicate(true))
		Quests.notify("restore:" + id)
	var err: Error = SaveGame.commit_transaction(change)
	if err != OK:
		return {"ok": false, "applied": false, "code": "save_failed"}
	# Existing success observers can capture live state (game.gd copies HP) and
	# perform their normal autosave; that is outside the atomic restore boundary.
	changed.emit(id)
	return {"ok": true, "applied": true, "code": "applied", "receipt": stored.duplicate(true)}

## Consume the same live gates as game.gd autosave(), without copying argument parsing.
## The lab's one-off resume migration is not permission to commit a restoration receipt.
func _restoration_writes_allowed() -> bool:
	if Zones.in_lab():
		return false
	var game := get_tree().get_first_node_in_group("game")
	if game != null:
		var hud := game.get("hud") as Control
		if hud != null and not bool(hud.get("guidance")):
			return false
	return true

## The plan's current stage id: the last entry of `stages` whose condition holds ("" without stages).
func stage(plan_id: String) -> String:
	var out := ""
	for s in plans.get(plan_id, {}).get("stages", []):
		if Quests.check(s.get("if")):
			out = s.id
	return out
