class_name FolkProgression
extends RefCounted
## Y1's isolated state API over the authored proposal. No autoload, combat effects or payments.
## The level-point rule is progression.md §2: one point per level from 2, independently per folk.

signal changed(snapshot: Dictionary)

var _catalogue: Dictionary = {}
var _definitions: Dictionary = {}
var _nodes: Dictionary = {}
var _state: Dictionary = {"progression": {"level": 1}, "folk": {}}
var _maximum_level := 1

## Configure atomically from catalogue.json and the corresponding folk documents.
func configure(catalogue: Variant, documents: Variant) -> Error:
	if not catalogue is Dictionary or not documents is Array:
		return ERR_INVALID_DATA
	if not _whole(catalogue.get("schema_version")) or catalogue.schema_version != 1:
		return ERR_INVALID_DATA
	if not catalogue.get("status") is String or not catalogue.get("levels") is Dictionary:
		return ERR_INVALID_DATA
	var limits: Variant = catalogue.levels.get("range")
	if not limits is Array or limits.size() != 2 or not _whole(limits[0]) or not _whole(limits[1]):
		return ERR_INVALID_DATA
	if limits[0] != 1 or limits[1] < 1:
		return ERR_INVALID_DATA
	var ids: Variant = catalogue.get("characters")
	if not _unique_strings(ids) or ids.is_empty():
		return ERR_INVALID_DATA
	var tiers: Variant = catalogue.get("weapon_tiers")
	if not tiers is Dictionary or not _valid_tiers(tiers.get("tiers"), int(limits[1])):
		return ERR_INVALID_DATA
	var definitions := {}
	var nodes := {}
	for doc in documents:
		if not doc is Dictionary or not doc.get("id") is String or not ids.has(doc.id) or definitions.has(doc.id):
			return ERR_INVALID_DATA
		if not _whole(doc.get("schema_version")) or doc.schema_version != 1:
			return ERR_INVALID_DATA
		if not doc.get("abilities") is Dictionary or not doc.abilities.get("skill_tree") is Dictionary:
			return ERR_INVALID_DATA
		var branches: Variant = doc.abilities.skill_tree.get("branches")
		if not branches is Array or branches.is_empty():
			return ERR_INVALID_DATA
		var indexed := {}
		var branch_ids := {}
		for branch in branches:
			if not branch is Dictionary or not _id(branch.get("id")) or branch_ids.has(branch.id):
				return ERR_INVALID_DATA
			branch_ids[branch.id] = true
			if not branch.get("nodes") is Array or branch.nodes.is_empty():
				return ERR_INVALID_DATA
			for node in branch.nodes:
				if not node is Dictionary or not _id(node.get("id")) or indexed.has(node.id):
					return ERR_INVALID_DATA
				if not _whole(node.get("cost")) or node.cost < 1 or not _whole(node.get("level")):
					return ERR_INVALID_DATA
				if node.level < 1 or node.level > limits[1] or not _unique_strings(node.get("requires")):
					return ERR_INVALID_DATA
				if node.has("touches_canonical") and not node.touches_canonical is bool:
					return ERR_INVALID_DATA
				indexed[node.id] = node.duplicate(true)
		if not _valid_graph(indexed):
			return ERR_INVALID_DATA
		if not doc.get("weapon") is Dictionary or not _valid_tiers(doc.weapon.get("tiers"), int(limits[1])):
			return ERR_INVALID_DATA
		for i in tiers.tiers.size():
			var entry: Dictionary = doc.weapon.tiers[i]
			if entry.requires != tiers.tiers[i].requires or entry.sockets != tiers.tiers[i].sockets:
				return ERR_INVALID_DATA
		definitions[doc.id] = doc.duplicate(true)
		nodes[doc.id] = indexed
	if definitions.size() != ids.size():
		return ERR_INVALID_DATA
	_catalogue = catalogue.duplicate(true)
	_definitions = definitions
	_nodes = nodes
	_maximum_level = int(limits[1])
	_state = {"progression": {"level": 1}, "folk": {}}
	_publish()
	return OK

func catalogue_status() -> String:
	return _catalogue.get("status", "unconfigured")

func snapshot() -> Dictionary:
	return _state.duplicate(true)

func level() -> int:
	return int(_state.progression.level)

## Level increases grant points to each joined folk without buying or spending anything.
func advance_level(next_level: Variant) -> Error:
	if _definitions.is_empty() or not _whole(next_level) or next_level < level() or next_level > _maximum_level:
		return ERR_INVALID_PARAMETER
	if next_level != level():
		_state.progression.level = int(next_level)
		_publish()
	return OK

## Late joiners inherit the highest reached tier, capped below Starfall, and no spent points.
func join_folk(folk: String) -> Error:
	if not _definitions.has(folk):
		return ERR_DOES_NOT_EXIST
	if _state.folk.has(folk):
		return ERR_ALREADY_EXISTS
	var tier := 1
	for record in _state.folk.values():
		tier = maxi(tier, mini(int(record.weapon_tier), 3))
	_state.folk[folk] = {"nodes": [], "weapon_tier": tier}
	_publish()
	return OK

func available_points(folk: String) -> int:
	if not _state.folk.has(folk):
		return -1
	var spent := 0
	for id in _state.folk[folk].nodes:
		spent += int(_nodes[folk][id].cost)
	return level() - 1 - spent

## Offers are detached metadata, not applied combat modifiers or approval of the proposal.
func node_offer(folk: String, id: String) -> Dictionary:
	var offer := {"allowed": false, "reason": "unknown", "status": catalogue_status()}
	if not _state.folk.has(folk) or not _nodes[folk].has(id):
		return offer
	var node: Dictionary = _nodes[folk][id]
	offer.node = node.duplicate(true)
	offer.available_points = available_points(folk)
	if _state.folk[folk].nodes.has(id):
		offer.reason = "owned"
	elif level() < node.level:
		offer.reason = "level"
	elif not _has_all(_state.folk[folk].nodes, node.requires):
		offer.reason = "prerequisite"
	elif available_points(folk) < node.cost:
		offer.reason = "points"
	elif node.get("touches_canonical", false):
		offer.reason = "c60_approval_required"
	else:
		offer.allowed = true
		offer.reason = "available"
	return offer

func unlock_node(folk: String, id: String) -> Error:
	if not node_offer(folk, id).allowed:
		return ERR_UNAVAILABLE
	_state.folk[folk].nodes.append(id)
	_publish()
	return OK

## Payment belongs to Y3. This API only supplies/records the next eligible tier.
## Call record_tier only after the caller's approved forge/payment transaction succeeds.
func tier_offer(folk: String, next_tier: Variant, access: Variant = {}) -> Dictionary:
	var offer := {"allowed": false, "reason": "unknown", "status": catalogue_status()}
	if not _state.folk.has(folk) or not _whole(next_tier) or next_tier < 1 or next_tier > 4:
		return offer
	if not access is Dictionary:
		offer.reason = "invalid_access"
		return offer
	var entry: Dictionary = _definitions[folk].weapon.tiers[int(next_tier) - 1]
	var common: Dictionary = _catalogue.weapon_tiers.tiers[int(next_tier) - 1]
	offer.tier = entry.duplicate(true)
	var cost: Variant = entry.get("cost", common.get("cost"))
	offer.cost = cost.duplicate(true) if cost is Dictionary else null
	if next_tier != int(_state.folk[folk].weapon_tier) + 1:
		offer.reason = "sequence"
	elif level() < entry.requires.level:
		offer.reason = "level"
	else:
		for key in entry.requires:
			if key == "level":
				continue
			if not access.get(key, false) is bool or access.get(key, false) != entry.requires[key]:
				offer.reason = key
				return offer
		offer.allowed = true
		offer.reason = "available"
	return offer

func record_tier(folk: String, next_tier: Variant, access: Variant = {}) -> Error:
	if not tier_offer(folk, next_tier, access).allowed:
		return ERR_UNAVAILABLE
	_state.folk[folk].weapon_tier = int(next_tier)
	_publish()
	return OK

## Restore only the progression projection. Unknown JSON extensions are preserved, never spent.
## Historical ownership need not be in purchase order; the complete prerequisite set must exist.
func restore(value: Variant) -> Error:
	if _definitions.is_empty() or not value is Dictionary or not value.get("progression") is Dictionary or not value.get("folk") is Dictionary:
		return ERR_INVALID_DATA
	var proposed_level: Variant = value.progression.get("level")
	if not _whole(proposed_level) or proposed_level < 1 or proposed_level > _maximum_level:
		return ERR_INVALID_DATA
	for folk in value.folk:
		if not _definitions.has(folk):
			return ERR_INVALID_DATA
		var record: Variant = value.folk[folk]
		if not record is Dictionary or not _unique_strings(record.get("nodes")) or not _whole(record.get("weapon_tier")):
			return ERR_INVALID_DATA
		var tier := int(record.weapon_tier)
		if tier < 1 or tier > 4 or proposed_level < _definitions[folk].weapon.tiers[tier - 1].requires.level:
			return ERR_INVALID_DATA
		var spent := 0
		for id in record.nodes:
			if not _nodes[folk].has(id):
				return ERR_INVALID_DATA
			var node: Dictionary = _nodes[folk][id]
			if proposed_level < node.level or not _has_all(record.nodes, node.requires):
				return ERR_INVALID_DATA
			if node.cost > int(proposed_level) - 1 - spent:
				return ERR_INVALID_DATA
			spent += int(node.cost)
		if spent > int(proposed_level) - 1:
			return ERR_INVALID_DATA
	_state = value.duplicate(true)
	_state.progression.level = int(proposed_level)
	for record in _state.folk.values():
		record.weapon_tier = int(record.weapon_tier)
	_publish()
	return OK

func _publish() -> void:
	changed.emit(snapshot())

func _valid_tiers(entries: Variant, maximum: int) -> bool:
	if not entries is Array or entries.size() != 4:
		return false
	var previous_level := 0
	for i in entries.size():
		var entry: Variant = entries[i]
		if not entry is Dictionary or not _whole(entry.get("tier")) or entry.tier != i + 1:
			return false
		if not entry.get("requires") is Dictionary or not _whole(entry.requires.get("level")):
			return false
		if (i == 0 and entry.requires.level != 1) or entry.requires.level <= previous_level or entry.requires.level > maximum:
			return false
		previous_level = int(entry.requires.level)
		if not _whole(entry.get("sockets")) or entry.sockets < 1:
			return false
		for key in entry.requires:
			if key != "level" and (not key is String or not entry.requires[key] is bool):
				return false
		if entry.has("cost") and entry.cost != null:
			if not entry.cost is Dictionary:
				return false
			for amount in entry.cost.values():
				if amount is Dictionary:
					if not _id(amount.get("material")) or not _whole(amount.get("count")) or amount.count < 0:
						return false
				elif not _whole(amount) or amount < 0:
					return false
	return true

func _valid_graph(nodes: Dictionary) -> bool:
	var visited := {}
	while visited.size() < nodes.size():
		var progressed := false
		for id in nodes:
			if not visited.has(id) and _has_all(visited.keys(), nodes[id].requires):
				visited[id] = true
				progressed = true
		if not progressed:
			return false
	return true

func _has_all(owned: Array, required: Array) -> bool:
	for id in required:
		if not owned.has(id):
			return false
	return true

func _unique_strings(value: Variant) -> bool:
	if not value is Array:
		return false
	var seen := {}
	for id in value:
		if not _id(id) or seen.has(id):
			return false
		seen[id] = true
	return true

func _id(value: Variant) -> bool:
	return value is String and not value.is_empty()

func _whole(value: Variant) -> bool:
	if typeof(value) == TYPE_INT:
		return value >= -9007199254740991 and value <= 9007199254740991
	return typeof(value) == TYPE_FLOAT and is_finite(value) and value == floor(value) and absf(value) <= 9007199254740991.0
