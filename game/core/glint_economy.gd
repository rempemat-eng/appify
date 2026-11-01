class_name GlintEconomy
extends RefCounted
## An isolated Glint transaction ledger. It never reads/writes SaveGame or grants
## progression, cosmetics, perks or rewards to the live game. Prices and access
## decisions are explicit inputs; proposal quotes remain proposals.

const MAX_EXACT := 9007199254740991 # Exact JSON interchange, not a gameplay cap.
const CATEGORIES := ["restoration", "forge", "shop", "cosmetic", "respec", "map_service"]

static func _error(code: String, message: String) -> Dictionary:
	return {"ok": false, "code": code, "error": message}

static func _number(value: Variant) -> int:
	if typeof(value) == TYPE_INT:
		return value if value >= 0 and value <= MAX_EXACT else -1
	if typeof(value) == TYPE_FLOAT and is_finite(value) and value >= 0 and value <= MAX_EXACT and floor(value) == value:
		return int(value)
	return -1

static func _text(value: Variant) -> bool:
	if typeof(value) != TYPE_STRING or value.strip_edges().is_empty():
		return false
	for index: int in value.length():
		if value.unicode_at(index) == 0:
			return false
	return true

static func _component(value: Variant) -> bool:
	return _text(value) and not "/" in value and not "\\" in value and value not in [".", ".."]

static func _keys(value: Dictionary, allowed: Array) -> bool:
	for key: Variant in value:
		if key not in allowed:
			return false
	return true

static func _identities(value: Variant) -> Dictionary:
	if typeof(value) != TYPE_ARRAY:
		return _error("invalid_owned", "Owned identities must be an array of unique nonempty strings")
	var result: Array = []
	for item: Variant in value:
		if not _text(item) or item in result:
			return _error("invalid_owned", "Owned identities must be unique nonempty strings")
		result.append(item)
	return {"ok": true, "items": result}

static func _state(opening: int, owned: Array) -> Dictionary:
	return {"schema_version": 1, "currency": "Glint", "opening_balance": opening,
		"initial_owned": owned.duplicate(), "balance": opening, "owned": owned.duplicate(), "receipts": []}

static func fresh(opening_balance: Variant = 0, initial_owned: Variant = []) -> Dictionary:
	var opening: int = _number(opening_balance)
	var identities: Dictionary = _identities(initial_owned)
	if opening < 0:
		return _error("invalid_amount", "Opening Glint must be an exact nonnegative JSON integer")
	if not identities.ok:
		return identities
	return {"ok": true, "state": _state(opening, identities.items)}

static func _event(value: Variant) -> Dictionary:
	if typeof(value) != TYPE_DICTIONARY:
		return _error("invalid_event", "A transaction must be an object")
	var event: Dictionary = value
	if not _keys(event, ["id", "kind", "amount", "source", "source_status", "category", "item", "eligible"]):
		return _error("invalid_event", "Unknown transaction field; currency and economic meaning cannot be reinterpreted")
	if not _text(event.get("id")) or not _text(event.get("source")):
		return _error("invalid_event", "A transaction needs nonempty id and source strings")
	if event.has("source_status") and not _text(event.source_status):
		return _error("invalid_event", "source_status must be a nonempty string when supplied")
	var amount: int = _number(event.get("amount"))
	if amount < 0:
		return _error("invalid_amount", "Transaction Glint must be an exact nonnegative JSON integer")
	var payload: Dictionary = {"id": event.id, "kind": event.get("kind"), "amount": amount, "source": event.source}
	if event.has("source_status"):
		payload.source_status = event.source_status
	match event.get("kind"):
		"earn":
			if amount == 0 or event.has("category") or event.has("item") or event.has("eligible"):
				return _error("invalid_event", "Earning needs a positive explicit amount and no purchase fields")
		"spend":
			if event.get("category") not in CATEGORIES or not _text(event.get("item")) or typeof(event.get("eligible")) != TYPE_BOOL:
				return _error("invalid_event", "Spending needs a supported category, item and explicit boolean eligibility; Glint never buys levels, XP or points")
			if amount == 0 and event.category != "respec":
				return _error("invalid_event", "Only an explicitly quoted respec may have a zero price")
			payload.merge({"category": event.category, "item": event.item, "eligible": event.eligible})
		_:
			return _error("invalid_event", "Transaction kind must be earn or spend")
	return {"ok": true, "event": payload}

## Internal only: state and event are newly built, already validated values.
static func _step(state: Dictionary, event: Dictionary) -> Dictionary:
	if event.kind == "earn":
		if event.amount > MAX_EXACT - state.balance:
			return _error("overflow", "Earning exceeds exact JSON interchange range")
		state.balance += event.amount
	else:
		if not event.eligible:
			return _error("not_eligible", "The caller has not established access/stock/context eligibility")
		if event.category == "cosmetic" and event.item in state.owned:
			return _error("already_owned", "This cosmetic identity is already owned")
		if event.amount > state.balance:
			return _error("insufficient_funds", "The explicit price exceeds available Glint")
		state.balance -= event.amount
		if event.category == "cosmetic":
			state.owned.append(event.item)
	state.receipts.append(event.duplicate(true))
	return {"ok": true, "state": state, "applied": true, "receipt": event.duplicate(true)}

## Restoration validates the whole ledger, not just its claimed closing balance.
static func validate(snapshot: Variant) -> Dictionary:
	if typeof(snapshot) != TYPE_DICTIONARY:
		return _error("invalid_snapshot", "Ledger snapshot must be an object")
	if not _keys(snapshot, ["schema_version", "currency", "opening_balance", "initial_owned", "balance", "owned", "receipts"]):
		return _error("invalid_snapshot", "Ledger snapshot contains unknown fields")
	if _number(snapshot.get("schema_version")) != 1 or snapshot.get("currency") != "Glint":
		return _error("invalid_snapshot", "Ledger needs schema_version 1 and currency Glint")
	var initial: Dictionary = fresh(snapshot.get("opening_balance"), snapshot.get("initial_owned"))
	var owned: Dictionary = _identities(snapshot.get("owned"))
	if not initial.ok or not owned.ok or _number(snapshot.get("balance")) < 0 or typeof(snapshot.get("receipts")) != TYPE_ARRAY:
		return _error("invalid_snapshot", "Ledger opening, balance, ownership or receipt array is malformed")
	var state: Dictionary = initial.state
	var seen: Dictionary = {}
	for index: int in snapshot.receipts.size():
		var checked: Dictionary = _event(snapshot.receipts[index])
		if not checked.ok:
			return _error("invalid_snapshot", "Receipt %d: %s" % [index, checked.error])
		var event: Dictionary = checked.event
		if seen.has(event.id):
			return _error("invalid_snapshot", "Receipt IDs must be unique; replays are not stored twice")
		seen[event.id] = true
		var result: Dictionary = _step(state, event)
		if not result.ok:
			return _error("invalid_snapshot", "Receipt %d: %s" % [index, result.error])
	if state.balance != _number(snapshot.balance) or state.owned != owned.items:
		return _error("invalid_snapshot", "Closing balance/ownership does not match the ordered receipts")
	return {"ok": true, "state": state}

## A successful duplicate returns a detached state, without another charge/reward.
static func apply(snapshot: Variant, value: Variant) -> Dictionary:
	var checked: Dictionary = validate(snapshot)
	if not checked.ok:
		return checked
	var normal: Dictionary = _event(value)
	if not normal.ok:
		return normal
	var event: Dictionary = normal.event
	var state: Dictionary = checked.state
	for receipt: Dictionary in state.receipts:
		if receipt.id == event.id:
			if receipt != event:
				return _error("duplicate_conflict", "Transaction ID already names a different payload")
			return {"ok": true, "state": state, "applied": false, "receipt": receipt.duplicate(true)}
	return _step(state, event)

## Item identity and unlock provenance come from the supplied folk document.
## Price/access remain explicit caller assumptions; prose prices are not parsed.
static func quote_cosmetic(folk: Variant, item_id: Variant, price: Variant, eligible: Variant) -> Dictionary:
	if typeof(folk) != TYPE_DICTIONARY or not _component(folk.get("id")) or not _text(folk.get("status")) or not _component(item_id):
		return _error("invalid_catalogue", "A cosmetic quote needs a folk identity/status and item identity")
	var amount: int = _number(price)
	if amount <= 0 or typeof(eligible) != TYPE_BOOL:
		return _error("invalid_quote", "Cosmetic price must be explicit/positive and eligibility must be boolean")
	var found: Dictionary = {}
	var ids: Dictionary = {}
	for group: String in ["outfits", "accessories"]:
		if typeof(folk.get(group)) != TYPE_ARRAY:
			return _error("invalid_catalogue", "Folk outfits/accessories must be arrays")
		for record: Variant in folk[group]:
			if typeof(record) != TYPE_DICTIONARY or not _component(record.get("id")) or ids.has(record.id):
				return _error("invalid_catalogue", "Cosmetic identities must be usable and unique across slots")
			ids[record.id] = true
			if record.id == item_id:
				found = record
	if found.is_empty() or typeof(found.get("unlock")) != TYPE_DICTIONARY or found.unlock.get("source") != "glint" or not _text(found.unlock.get("event")):
		return _error("invalid_quote", "Item is absent or is not an authored Glint unlock")
	if found.unlock.has("note") and typeof(found.unlock.note) != TYPE_STRING:
		return _error("invalid_catalogue", "Unlock note must be text when supplied")
	return {"ok": true, "offer": {"kind": "spend", "category": "cosmetic", "amount": amount,
		"item": folk.id + "/" + item_id, "eligible": eligible, "source": found.unlock.event, "source_status": folk.status},
		"proposal": true, "effects_applied": false, "price_source": "caller_explicit",
		"note": found.unlock.get("note", ""), "unlock_event": found.unlock.event}

## Quotes a supplied proposal policy only. The receiving owner still has to
## approve policy, establish the use-count scope, and atomically reset points.
static func quote_respec(policy: Variant, uses: Variant, context: Variant) -> Dictionary:
	if typeof(policy) != TYPE_DICTIONARY or not _text(policy.get("status")) or typeof(policy.get("sinks")) != TYPE_DICTIONARY or typeof(policy.sinks.get("respec")) != TYPE_DICTIONARY:
		return _error("invalid_policy", "Respec requires an explicit policy/status with sinks.respec")
	var fees: Dictionary = policy.sinks.respec
	var first: int = _number(fees.get("first"))
	var after: int = _number(fees.get("after"))
	var count: int = _number(uses)
	if first < 0 or after <= 0 or count < 0:
		return _error("invalid_policy", "Respec fees/use count must be exact nonnegative integers; subsequent fee must be positive")
	var fields: Array = ["at_hut_bed", "in_fight", "in_siege", "in_dungeon", "allow_proposal"]
	if typeof(context) != TYPE_DICTIONARY or not _keys(context, fields):
		return _error("invalid_context", "Supply every respec context flag explicitly")
	for key: String in fields:
		if typeof(context.get(key)) != TYPE_BOOL:
			return _error("invalid_context", "Respec context flags must all be explicit booleans")
	var eligible: bool = context.at_hut_bed and context.allow_proposal and not context.in_fight and not context.in_siege and not context.in_dungeon
	return {"ok": true, "offer": {"kind": "spend", "category": "respec", "item": "respec",
		"amount": first if count == 0 else after, "eligible": eligible,
		"source": "policy:sinks.respec", "source_status": policy.status},
		"proposal": true, "effects_applied": false, "price_source": "provided_policy",
		"uses": count, "context": context.duplicate(true)}
