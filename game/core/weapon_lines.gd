class_name WeaponLines
extends RefCounted
## Read-only resolver for the pinned UNAPPROVED proposal. No combat/animation/payment writes.

const SOURCE_COMMIT := "debdf9495bd32966e1f1b65a67a5e6964b62b743"
const LEVELS := [1, 8, 16, 24]
var _source: Dictionary = {}
var _lines: Dictionary = {}
var _status := "unconfigured"

func configure(document: Variant) -> Error:
	if not document is Dictionary or not _whole(document.get("schema_version")) or document.schema_version != 1:
		return ERR_INVALID_DATA
	if document.get("approved") != false or not document.get("approved") is bool:
		return ERR_INVALID_DATA
	if document.get("mechanics_applied") != false or not document.get("mechanics_applied") is bool:
		return ERR_INVALID_DATA
	if not document.get("status") is String or not document.status.contains("unapproved") or not document.status.contains("placeholder"):
		return ERR_INVALID_DATA
	if not document.get("source") is Dictionary or document.source.get("commit") != SOURCE_COMMIT:
		return ERR_INVALID_DATA
	if not _hash(document.source.get("catalogue_blob"), 40) or document.source.get("pr") != 290:
		return ERR_INVALID_DATA
	var rows: Variant = document.get("lines")
	if not rows is Array or rows.size() != 14:
		return ERR_INVALID_DATA
	var indexed := {}
	for row in rows:
		if not row is Dictionary or not _name(row.get("id")) or indexed.has(row.id):
			return ERR_INVALID_DATA
		if row.get("source_path") != "game/data/progression/%s.json" % row.id or not _hash(row.get("source_blob"), 40) or not _hash(row.get("weapon_sha256"), 64):
			return ERR_INVALID_DATA
		var weapon: Variant = row.get("weapon")
		if not weapon is Dictionary or not _name(weapon.get("item")) or not _name(weapon.get("line")):
			return ERR_INVALID_DATA
		var tiers: Variant = weapon.get("tiers")
		if not tiers is Array or tiers.size() != 4:
			return ERR_INVALID_DATA
		for i in tiers.size():
			var stage: Variant = tiers[i]
			if not stage is Dictionary or not _whole(stage.get("tier")) or stage.tier != i + 1:
				return ERR_INVALID_DATA
			if not _whole(stage.get("level")) or stage.level != LEVELS[i] or not _name(stage.get("name")) or not _name(stage.get("form")):
				return ERR_INVALID_DATA
			if not stage.get("requires") is Dictionary or not _whole(stage.requires.get("level")) or stage.requires.level != stage.level:
				return ERR_INVALID_DATA
			for key in stage.requires:
				if key != "level" and (not key is String or not stage.requires[key] is bool):
					return ERR_INVALID_DATA
			if not stage.get("mechanics") is Dictionary:
				return ERR_INVALID_DATA
		indexed[row.id] = row.duplicate(true)
	_source = document.source.duplicate(true)
	_status = document.status
	_lines = indexed
	return OK

func status() -> Dictionary:
	return {"status": _status, "approved": false, "mechanics_applied": false,
		"preview_only": true, "source": _source.duplicate(true)}

func folk_ids() -> Array:
	return _lines.keys()

func line(folk: String) -> Dictionary:
	return _lines[folk].weapon.duplicate(true) if _lines.has(folk) else {}

func at_tier(folk: String, tier: Variant) -> Dictionary:
	var result := status()
	result.ok = false
	result.reason = "unknown_folk"
	if not _lines.has(folk):
		return result
	if not _whole(tier) or tier < 1 or tier > 4:
		result.reason = "invalid_tier"
		return result
	var record: Dictionary = _lines[folk]
	result.ok = true
	result.reason = "proposal_only"
	result.folk = folk
	result.stage = record.weapon.tiers[int(tier) - 1].duplicate(true)
	result.provenance = {"path": record.source_path, "blob": record.source_blob,
		"weapon_sha256": record.weapon_sha256}
	return result

## Resolve a caller-owned Y1/Y6 projection without changing level, ownership, forge or currency.
## The level gate checks consistency of an already recorded tier; it never grants one.
func current(projection: Variant, folk: String) -> Dictionary:
	var failure := status()
	failure.ok = false
	failure.reason = "invalid_projection"
	if not projection is Dictionary or not projection.get("progression") is Dictionary or not projection.get("folk") is Dictionary:
		return failure
	var level: Variant = projection.progression.get("level")
	if not _whole(level) or level < 1 or level > 30:
		return failure
	if not projection.folk.has(folk):
		failure.reason = "unjoined"
		return failure
	var record: Variant = projection.folk[folk]
	if not record is Dictionary:
		return failure
	var result := at_tier(folk, record.get("weapon_tier"))
	if not result.ok:
		return result
	if level < result.stage.level:
		failure.reason = "tier_above_level"
		return failure
	return result

## Compare explicit stages, never infer an upgrade from level alone or interpret modifier prose.
func compare(folk: String, from_tier: Variant, to_tier: Variant) -> Dictionary:
	var before := at_tier(folk, from_tier)
	if not before.ok:
		return before
	var after := at_tier(folk, to_tier)
	if not after.ok:
		return after
	var result := status()
	result.ok = true
	result.reason = "proposal_only"
	result.before = before.stage
	result.after = after.stage
	result.form_changed = before.stage.form != after.stage.form
	result.mechanics_changed = before.stage.mechanics != after.stage.mechanics
	return result

func _name(value: Variant) -> bool:
	return value is String and not value.strip_edges().is_empty()

func _hash(value: Variant, size: int) -> bool:
	if not value is String or value.length() != size:
		return false
	for ch in value:
		if not ch in "0123456789abcdef":
			return false
	return true

func _whole(value: Variant) -> bool:
	if typeof(value) == TYPE_INT:
		return value >= -9007199254740991 and value <= 9007199254740991
	return typeof(value) == TYPE_FLOAT and is_finite(value) and value == floor(value) and absf(value) <= 9007199254740991.0
