extends RefCounted
## Y7: view state only. The caller owns pause, saving, item actions and quest progression.

signal changed(view: Dictionary)

var _tabs: Array = []
var _rows: Dictionary = {}
var _selected: Dictionary = {}
var _tab := ""
var _open := false
var _detail := false

## Invalid replacement input leaves all previous state intact.
func configure(tabs: Variant) -> bool:
	if not tabs is Array or tabs.is_empty():
		return false
	var seen := {}
	for id in tabs:
		if not _id(id) or seen.has(id):
			return false
		seen[id] = true
	_tabs = tabs.duplicate(true)
	_rows.clear()
	_selected.clear()
	for id in _tabs:
		_rows[id] = []
		_selected[id] = ""
	_tab = _tabs[0]
	_open = false
	_detail = false
	_emit()
	return true

func open(tab: String = "") -> bool:
	var target := _tab if tab.is_empty() else tab
	if not _tabs.has(target):
		return false
	if _open and _tab == target and not _detail:
		return true
	_open = true
	_tab = target
	_detail = false
	_emit()
	return true

func close() -> void:
	if not _open:
		return
	_open = false
	_detail = false
	_emit()

## Back/Escape closes the detail first, then the menu. Returns whether it consumed Back.
func back() -> bool:
	if not _open:
		return false
	if _detail:
		_detail = false
		_emit()
	else:
		close()
	return true

func select_tab(tab: String) -> bool:
	if not _open or not _tabs.has(tab):
		return false
	if _tab != tab or _detail:
		_tab = tab
		_detail = false
		_emit()
	return true

func move_tab(direction: int) -> bool:
	if not _open or direction == 0:
		return false
	return select_tab(_tabs[posmod(_tabs.find(_tab) + signi(direction), _tabs.size())])

## Item/quest IDs are view identities, not a new inventory/save contract. No counts or rules added.
## Unknown fields are carried verbatim; duplicate/blank IDs or non-record rows reject atomically.
func set_rows(tab: String, rows: Variant) -> bool:
	if not _tabs.has(tab) or not rows is Array:
		return false
	var seen := {}
	for row in rows:
		if not row is Dictionary or not _id(row.get("id")) or seen.has(row.id):
			return false
		seen[row.id] = true
	var old_index := _index(tab)
	var old_id: String = _selected[tab]
	_rows[tab] = rows.duplicate(true)
	if not seen.has(old_id):
		_selected[tab] = "" if rows.is_empty() else rows[clampi(old_index, 0, rows.size() - 1)].id
		if tab == _tab:
			_detail = false
	_emit()
	return true

func select_row(id: String) -> bool:
	if not _open:
		return false
	for row in _rows[_tab]:
		if row.id == id:
			if _selected[_tab] != id:
				_selected[_tab] = id
				_detail = false
				_emit()
			return true
	return false

func move_row(direction: int) -> bool:
	if not _open or direction == 0 or _rows[_tab].is_empty():
		return false
	var index := clampi(_index(_tab) + signi(direction), 0, _rows[_tab].size() - 1)
	return select_row(_rows[_tab][index].id)

func show_detail() -> bool:
	if not _open or _selected[_tab].is_empty():
		return false
	if not _detail:
		_detail = true
		_emit()
	return true

func snapshot() -> Dictionary:
	return {"open": _open, "tab": _tab, "tabs": _tabs.duplicate(true),
		"detail": _detail, "selected": _selected.duplicate(true), "rows": _rows.duplicate(true)}

func _index(tab: String) -> int:
	for i in _rows[tab].size():
		if _rows[tab][i].id == _selected[tab]:
			return i
	return 0

func _emit() -> void:
	changed.emit(snapshot())

static func _id(value: Variant) -> bool:
	return value is String and not value.strip_edges().is_empty()

## Read-only inventory projection. It neither guesses item stats nor equips/salvages anything.
static func inventory(records: Variant, query: String = "") -> Dictionary:
	if not records is Array:
		return _failure("inventory must be an array")
	var out := []
	var seen := {}
	var needle := query.to_lower()
	for row in records:
		if not row is Dictionary or not _id(row.get("id")) or seen.has(row.id):
			return _failure("inventory records need unique nonblank string ids")
		seen[row.id] = true
		var label: Variant = row.get("name", row.id)
		if not label is String:
			return _failure("inventory name must be a string")
		if needle.is_empty() or needle in label.to_lower() or needle in row.id.to_lower():
			out.append(row.duplicate(true))
	return {"ok": true, "rows": out, "error": ""}

## Consumes Quests.defs and SaveGame.data.quests, not a second quest engine.
## Unknown saved IDs are errors so content migrations cannot silently erase journal history.
static func journal(definitions: Variant, records: Variant) -> Dictionary:
	if not definitions is Dictionary or not records is Dictionary:
		return _failure("quest definitions and records must be dictionaries")
	var out := []
	for id in records:
		if not _id(id) or not definitions.has(id):
			return _failure("unknown saved quest: %s" % str(id))
		var rec: Variant = records[id]
		var def: Variant = definitions[id]
		if not rec is Dictionary or not def is Dictionary or def.get("id") != id:
			return _failure("invalid quest record/definition: %s" % id)
		var state: Variant = rec.get("state", "none")
		var steps: Variant = def.get("steps")
		if not state in ["none", "active", "done"] or not steps is Array or steps.is_empty():
			return _failure("invalid quest state/steps: %s" % id)
		var step: Variant = rec.get("step", 0)
		if not _whole(step) or step < 0 or step > steps.size():
			return _failure("invalid quest step: %s" % id)
		if (state == "active" and step >= steps.size()) or (state == "done" and step != steps.size()):
			return _failure("inconsistent quest progress: %s" % id)
		if state == "none":
			continue
		var title: Variant = def.get("title", id)
		var kind: Variant = def.get("kind", "")
		if not title is String or not kind is String:
			return _failure("invalid quest display text: %s" % id)
		var text := ""
		if state == "active":
			var current: Variant = steps[int(step)]
			if not current is Dictionary or not current.get("text", "") is String:
				return _failure("invalid current quest step: %s" % id)
			text = current.get("text", "")
		out.append({"id": id, "title": title, "kind": kind, "state": state,
			"step": int(step), "step_count": steps.size(), "text": text})
	out.sort_custom(func(a: Dictionary, b: Dictionary) -> bool:
		if a.state != b.state:
			return a.state == "active"
		return a.id < b.id)
	return {"ok": true, "rows": out, "error": ""}

static func _whole(value: Variant) -> bool:
	return (value is int or value is float) and is_finite(float(value)) and float(value) == floorf(float(value))

static func _failure(error: String) -> Dictionary:
	return {"ok": false, "rows": [], "error": error}
