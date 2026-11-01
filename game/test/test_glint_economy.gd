extends GdUnitTestSuite
## Y3's explicit Glint transactions and proposal quotes. These tests neither apply balance
## proposals to the game nor choose income rates, stock rules, respec scope or cosmetic effects.

const Ledger = preload("res://core/glint_economy.gd")
const Sim = preload("res://tools/sim_glint.gd")
const MAX_AMOUNT: int = 9007199254740991

func _read(path: String) -> Dictionary:
	var value: Variant = JSON.parse_string(FileAccess.get_file_as_string(path))
	assert_bool(value is Dictionary).is_true()
	return value if value is Dictionary else {}

func _ok(result: Dictionary) -> bool:
	assert_bool(result.get("ok", false)).is_true()
	return result.get("ok", false)

func _rejected(result: Dictionary) -> void:
	assert_bool(result.get("ok", true)).is_false()
	assert_bool(result.has("code")).is_true()
	assert_bool(result.has("error")).is_true()
	assert_str(str(result.get("error", ""))).is_not_empty()

func _earn(id: String, amount: Variant, source := "fixture:reward") -> Dictionary:
	return {"id": id, "kind": "earn", "amount": amount, "source": source}

func _spend(id: String, amount: Variant, category := "forge", item := "fixture",
		eligible: Variant = true) -> Dictionary:
	return {"id": id, "kind": "spend", "amount": amount, "category": category,
		"item": item, "eligible": eligible, "source": "fixture:offer"}

func _context() -> Dictionary:
	return {"at_hut_bed": true, "in_fight": false, "in_siege": false,
		"in_dungeon": false, "allow_proposal": true}

func _scenario(events: Array, opening: Variant = 0) -> Dictionary:
	return {"schema_version": 1, "currency": "Glint", "opening_balance": opening,
		"events": events}

## Insert raw bytes into a JSON string without asking Godot to decode them first.
func _raw_source_bytes(source: PackedByteArray) -> PackedByteArray:
	var bytes: PackedByteArray = ('{"schema_version":1,"currency":"Glint",'
		+ '"opening_balance":0,"events":[{"id":"parser","kind":"earn",'
		+ '"amount":1,"source":"').to_utf8_buffer()
	bytes.append_array(source)
	bytes.append_array('"}]}'.to_utf8_buffer())
	return bytes

func _parse_refused(bytes: PackedByteArray) -> void:
	var before: PackedByteArray = bytes.duplicate()
	var result: Dictionary = Sim.parse_document(bytes)
	assert_bool(result.get("ok", true)).is_false()
	assert_str(str(result.get("error", ""))).is_not_empty()
	assert_int(str(result.get("sha256", "")).length()).is_equal(64)
	assert_bool(bytes == before).is_true()

func _slice_events() -> Array:
	var events: Array = []
	var restores: Array = _read("res://data/plans/crossroads.json").get("restores", [])
	var costs: Dictionary = {}
	for entry: Dictionary in restores:
		costs[entry.id] = entry.cost.glint
	for id: String in ["woodland_stones", "road_to_crossroads"]:
		var quest: Dictionary = _read("res://data/quests/" + id + ".json")
		events.append(_earn("quest:" + id, quest.rewards.glint, "quest:" + id))
	events.append(_spend("restore:forge", costs.forge, "restoration", "forge"))
	var under: Dictionary = _read("res://data/quests/under_the_stones.json")
	events.append(_earn("quest:under_the_stones", under.rewards.glint, "quest:under_the_stones"))
	events.append(_spend("restore:fern_cottage", costs.fern_cottage, "restoration", "fern_cottage"))
	var home: Dictionary = _read("res://data/quests/home_again.json")
	events.append(_earn("quest:home_again", home.rewards.glint, "quest:home_again"))
	return events

func test_fresh_state_is_explicit_glint_and_detached() -> void:
	var owned: Array = ["bramble/acorn_whistle"]
	var result: Dictionary = Ledger.fresh(25, owned)
	if not _ok(result):
		return
	var state: Dictionary = result.state
	assert_int(int(state.schema_version)).is_equal(1)
	assert_str(state.currency).is_equal("Glint")
	assert_int(int(state.opening_balance)).is_equal(25)
	assert_int(int(state.balance)).is_equal(25)
	assert_int(state.receipts.size()).is_equal(0)
	assert_array(state.owned).is_equal(["bramble/acorn_whistle"])
	owned.append("iona/tempest")
	assert_array(state.owned).is_equal(["bramble/acorn_whistle"])
	state.owned.append("tam/temple_gold")
	assert_array(state.initial_owned).is_equal(["bramble/acorn_whistle"])

func test_fresh_rejects_invalid_amounts_and_duplicate_initial_ownership() -> void:
	for amount: Variant in [true, -1, 0.5, INF, NAN, MAX_AMOUNT + 1]:
		_rejected(Ledger.fresh(amount))
	for owned: Variant in [["same", "same"], [""], [3], "not an array"]:
		_rejected(Ledger.fresh(0, owned))

func test_integral_json_numbers_are_accepted_without_fractional_money() -> void:
	var result: Dictionary = Ledger.fresh(7.0)
	if not _ok(result):
		return
	var applied: Dictionary = Ledger.apply(result.state, _earn("json", 3.0))
	if not _ok(applied):
		return
	assert_int(int(applied.state.balance)).is_equal(10)
	assert_int(typeof(applied.state.balance)).is_equal(TYPE_INT)

func test_earning_and_spending_preserve_all_input_snapshots() -> void:
	var fresh: Dictionary = Ledger.fresh(15)
	if not _ok(fresh):
		return
	var state: Dictionary = fresh.state
	var before: Dictionary = state.duplicate(true)
	var event: Dictionary = _earn("credit", 10)
	event.source_status = "explicit fixture input, not a rate"
	var event_before: Dictionary = event.duplicate(true)
	var credit: Dictionary = Ledger.apply(state, event)
	if not _ok(credit):
		return
	assert_bool(credit.applied).is_true()
	assert_dict(state).is_equal(before)
	assert_dict(event).is_equal(event_before)
	var debit: Dictionary = Ledger.apply(credit.state, _spend("debit", 25))
	if not _ok(debit):
		return
	assert_int(int(debit.state.balance)).is_equal(0)
	assert_int(int(credit.state.balance)).is_equal(25)
	assert_int(debit.state.receipts.size()).is_equal(2)

func test_identical_replay_is_idempotent_and_conflicting_id_is_refused() -> void:
	var fresh: Dictionary = Ledger.fresh()
	if not _ok(fresh):
		return
	var event: Dictionary = _earn("same-id", 20)
	var first: Dictionary = Ledger.apply(fresh.state, event)
	if not _ok(first):
		return
	var saved: Dictionary = first.state.duplicate(true)
	var replay: Dictionary = Ledger.apply(first.state, event.duplicate(true))
	if not _ok(replay):
		return
	assert_bool(replay.applied).is_false()
	assert_dict(replay.state).is_equal(saved)
	assert_dict(replay.receipt).is_equal(first.receipt)
	var conflict: Dictionary = event.duplicate(true)
	conflict.amount = 21
	_rejected(Ledger.apply(first.state, conflict))
	assert_dict(first.state).is_equal(saved)

func test_affordability_and_explicit_eligibility_fail_atomically() -> void:
	var fresh: Dictionary = Ledger.fresh(20)
	if not _ok(fresh):
		return
	var state: Dictionary = fresh.state
	var before: Dictionary = state.duplicate(true)
	_rejected(Ledger.apply(state, _spend("too-much", 21)))
	_rejected(Ledger.apply(state, _spend("blocked", 1, "shop", "seed", false)))
	_rejected(Ledger.apply(state, _spend("not-bool", 1, "shop", "seed", "true")))
	assert_dict(state).is_equal(before)

func test_event_schema_refuses_unknown_fields_and_unsupported_categories() -> void:
	var fresh: Dictionary = Ledger.fresh(100)
	if not _ok(fresh):
		return
	var extra: Dictionary = _earn("unknown", 1)
	extra.rate = 3
	_rejected(Ledger.apply(fresh.state, extra))
	for category: String in ["points", "levels", "XP", "gambling", ""]:
		_rejected(Ledger.apply(fresh.state, _spend("bad:" + category, 1, category)))
	for field: String in ["id", "kind", "amount", "source"]:
		var missing: Dictionary = _earn("missing", 1)
		missing.erase(field)
		_rejected(Ledger.apply(fresh.state, missing))
	var empty_source: Dictionary = _earn("source", 1, "")
	_rejected(Ledger.apply(fresh.state, empty_source))

func test_every_declared_spending_category_is_supported_without_new_rates() -> void:
	var fresh: Dictionary = Ledger.fresh(100)
	if not _ok(fresh):
		return
	var state: Dictionary = fresh.state
	for category: String in ["restoration", "forge", "shop", "cosmetic", "respec", "map_service"]:
		var result: Dictionary = Ledger.apply(state, _spend(category, 1, category, category + "/item"))
		if not _ok(result):
			return
		state = result.state
	assert_int(int(state.balance)).is_equal(94)

func test_zero_amount_is_allowed_only_for_explicit_respec() -> void:
	var fresh: Dictionary = Ledger.fresh()
	if not _ok(fresh):
		return
	_rejected(Ledger.apply(fresh.state, _earn("zero-income", 0)))
	for category: String in ["restoration", "forge", "shop", "cosmetic", "map_service"]:
		_rejected(Ledger.apply(fresh.state, _spend("zero:" + category, 0, category)))
	var free: Dictionary = Ledger.apply(fresh.state, _spend("free-respec", 0, "respec"))
	if not _ok(free):
		return
	assert_int(int(free.state.balance)).is_equal(0)
	assert_int(free.state.receipts.size()).is_equal(1)

func test_invalid_event_amounts_and_balance_overflow_are_refused() -> void:
	var empty: Dictionary = Ledger.fresh()
	var full: Dictionary = Ledger.fresh(MAX_AMOUNT)
	if not _ok(empty) or not _ok(full):
		return
	for amount: Variant in [true, -1, 0.5, INF, NAN, MAX_AMOUNT + 1]:
		_rejected(Ledger.apply(empty.state, _earn("bad-earn", amount)))
		_rejected(Ledger.apply(full.state, _spend("bad-spend", amount)))
	_rejected(Ledger.apply(full.state, _earn("overflow", 1)))
	var boundary: Dictionary = Ledger.apply(empty.state, _earn("maximum", MAX_AMOUNT))
	if not _ok(boundary):
		return
	assert_int(int(boundary.state.balance)).is_equal(MAX_AMOUNT)

func test_cosmetic_ownership_is_unique_but_other_items_can_repeat() -> void:
	var fresh: Dictionary = Ledger.fresh(100)
	if not _ok(fresh):
		return
	var bought: Dictionary = Ledger.apply(fresh.state, _spend("cosmetic-1", 5, "cosmetic", "bramble/acorn_whistle"))
	if not _ok(bought):
		return
	_rejected(Ledger.apply(bought.state, _spend("cosmetic-2", 5, "cosmetic", "bramble/acorn_whistle")))
	var another_folk: Dictionary = Ledger.apply(bought.state, _spend("cosmetic-3", 5, "cosmetic", "iona/acorn_whistle"))
	if not _ok(another_folk):
		return
	var state: Dictionary = another_folk.state
	for id: String in ["forge-1", "forge-2"]:
		var result: Dictionary = Ledger.apply(state, _spend(id, 5, "forge", "same-work"))
		if not _ok(result):
			return
		state = result.state
	assert_int(int(state.balance)).is_equal(80)
	assert_int(state.owned.size()).is_equal(2)

func test_initial_owned_cosmetic_cannot_be_charged_again() -> void:
	var fresh: Dictionary = Ledger.fresh(100, ["bramble/acorn_whistle"])
	if not _ok(fresh):
		return
	_rejected(Ledger.apply(fresh.state, _spend("already-owned", 25, "cosmetic", "bramble/acorn_whistle")))
	assert_int(int(fresh.state.balance)).is_equal(100)

func test_validated_state_survives_json_round_trip_and_replay() -> void:
	var fresh: Dictionary = Ledger.fresh(10)
	if not _ok(fresh):
		return
	var event: Dictionary = _earn("round-trip", 25)
	var applied: Dictionary = Ledger.apply(fresh.state, event)
	if not _ok(applied):
		return
	var decoded: Variant = JSON.parse_string(JSON.stringify(applied.state))
	var restored: Dictionary = Ledger.validate(decoded)
	if not _ok(restored):
		return
	assert_int(int(restored.state.balance)).is_equal(35)
	var replay: Dictionary = Ledger.apply(restored.state, event)
	if not _ok(replay):
		return
	assert_bool(replay.applied).is_false()
	assert_int(int(replay.state.balance)).is_equal(35)

func test_malformed_or_tampered_snapshot_is_not_accepted() -> void:
	var fresh: Dictionary = Ledger.fresh(10)
	if not _ok(fresh):
		return
	for bad: Variant in [null, [], "state", {"schema_version": 1}]:
		_rejected(Ledger.validate(bad))
	for field: String in ["balance", "owned", "receipts"]:
		var tampered: Dictionary = fresh.state.duplicate(true)
		tampered[field] = 11 if field == "balance" else ["invented"]
		_rejected(Ledger.validate(tampered))
	var currency: Dictionary = fresh.state.duplicate(true)
	currency.currency = "Dream Dust"
	_rejected(Ledger.validate(currency))

func test_authored_slice_transaction_order_ends_at_85_glint() -> void:
	var fresh: Dictionary = Ledger.fresh()
	if not _ok(fresh):
		return
	var state: Dictionary = fresh.state
	var events: Array = _slice_events()
	var before: Array = events.duplicate(true)
	var live_before: Dictionary = SaveGame.data.duplicate(true)
	for event: Dictionary in events:
		var result: Dictionary = Ledger.apply(state, event)
		if not _ok(result):
			return
		state = result.state
	assert_int(int(state.balance)).is_equal(85)
	assert_int(state.receipts.size()).is_equal(6)
	assert_array(events).is_equal(before)
	assert_dict(SaveGame.data).is_equal(live_before)

func test_every_authored_positive_quest_reward_can_be_ledgered_once() -> void:
	var fresh: Dictionary = Ledger.fresh()
	if not _ok(fresh):
		return
	var state: Dictionary = fresh.state
	var expected: int = 0
	var documents: int = 0
	for file: String in DirAccess.get_files_at("res://data/quests"):
		if not file.ends_with(".json"):
			continue
		documents += 1
		var quest: Dictionary = _read("res://data/quests/" + file)
		var amount: int = int(quest.get("rewards", {}).get("glint", 0))
		if amount == 0:
			continue
		expected += amount
		var event: Dictionary = _earn("quest:" + quest.id, amount, "quest:" + quest.id)
		var result: Dictionary = Ledger.apply(state, event)
		if not _ok(result):
			return
		state = result.state
		var replay: Dictionary = Ledger.apply(state, event)
		if not _ok(replay):
			return
		assert_bool(replay.applied).is_false()
	assert_int(documents).is_greater_equal(20)
	assert_int(int(state.balance)).is_equal(expected)

func test_all_real_glint_cosmetics_have_explicit_detached_proposal_quotes() -> void:
	var catalogue: Dictionary = _read("res://data/progression/catalogue.json")
	var quoted: int = 0
	for folk: String in catalogue.characters:
		var doc: Dictionary = _read("res://data/progression/" + folk + ".json")
		var before: Dictionary = doc.duplicate(true)
		for item: Dictionary in doc.outfits + doc.accessories:
			if item.unlock.source != "glint":
				continue
			var result: Dictionary = Ledger.quote_cosmetic(doc, item.id, 123, true)
			if not _ok(result):
				return
			quoted += 1
			assert_bool(result.proposal).is_true()
			assert_bool(result.effects_applied).is_false()
			assert_str(result.price_source).is_equal("caller_explicit")
			assert_int(int(result.offer.amount)).is_equal(123)
			assert_str(result.offer.category).is_equal("cosmetic")
			assert_str(result.offer.item).is_equal(folk + "/" + item.id)
			assert_str(result.offer.source).is_equal(item.unlock.event)
			assert_str(result.offer.source_status).is_equal(doc.status)
			assert_bool(result.offer.eligible).is_true()
			result.offer.item = "caller-mutated"
		assert_dict(doc).is_equal(before)
	assert_int(quoted).is_greater_equal(19)

func test_cosmetic_quote_does_not_infer_price_or_eligibility_from_prose() -> void:
	var doc: Dictionary = _read("res://data/progression/bramble.json")
	var quote: Dictionary = Ledger.quote_cosmetic(doc, "ranger_pine", 7, false)
	if not _ok(quote):
		return
	assert_int(int(quote.offer.amount)).is_equal(7)
	assert_bool(quote.offer.eligible).is_false()
	var fresh: Dictionary = Ledger.fresh(100)
	if not _ok(fresh):
		return
	var event: Dictionary = quote.offer.duplicate(true)
	event.id = "explicitly-ineligible"
	_rejected(Ledger.apply(fresh.state, event))

func test_explicit_cosmetic_quote_offer_can_be_applied_without_metadata_leaking() -> void:
	var doc: Dictionary = _read("res://data/progression/bramble.json")
	var quote: Dictionary = Ledger.quote_cosmetic(doc, "acorn_whistle", 250, true)
	var fresh: Dictionary = Ledger.fresh(300)
	if not _ok(quote) or not _ok(fresh):
		return
	var event: Dictionary = quote.offer.duplicate(true)
	event.id = "cosmetic:explicit-quote"
	var result: Dictionary = Ledger.apply(fresh.state, event)
	if not _ok(result):
		return
	assert_int(int(result.state.balance)).is_equal(50)
	assert_bool(result.state.owned.has("bramble/acorn_whistle")).is_true()
	assert_bool(event.has("proposal")).is_false()
	assert_bool(event.has("effects_applied")).is_false()
	assert_bool(event.has("note")).is_false()

func test_cosmetic_quote_rejects_non_glint_duplicate_and_missing_identity() -> void:
	var doc: Dictionary = _read("res://data/progression/bramble.json")
	_rejected(Ledger.quote_cosmetic(doc, "autumn_forester", 100, true))
	_rejected(Ledger.quote_cosmetic(doc, "unknown", 100, true))
	var duplicate: Dictionary = doc.duplicate(true)
	duplicate.outfits.append(duplicate.accessories[-1].duplicate(true))
	_rejected(Ledger.quote_cosmetic(duplicate, "acorn_whistle", 100, true))
	var unsafe: Dictionary = doc.duplicate(true)
	unsafe.id = "two/components"
	_rejected(Ledger.quote_cosmetic(unsafe, "acorn_whistle", 100, true))
	var missing: Dictionary = doc.duplicate(true)
	missing.erase("status")
	_rejected(Ledger.quote_cosmetic(missing, "acorn_whistle", 100, true))

func test_cosmetic_quote_rejects_invalid_price_and_missing_unlock_event() -> void:
	var doc: Dictionary = _read("res://data/progression/bramble.json")
	for price: Variant in [0, -1, true, 0.5, INF, NAN, MAX_AMOUNT + 1]:
		_rejected(Ledger.quote_cosmetic(doc, "acorn_whistle", price, true))
	var missing: Dictionary = doc.duplicate(true)
	missing.accessories[-1].unlock.event = ""
	_rejected(Ledger.quote_cosmetic(missing, "acorn_whistle", 1, true))

func test_respec_quote_uses_actual_policy_first_and_after_prices_without_effects() -> void:
	var policy: Dictionary = _read("res://data/balance/glint.json")
	var before: Dictionary = policy.duplicate(true)
	for uses: int in [0, 1, 25]:
		var quote: Dictionary = Ledger.quote_respec(policy, uses, _context())
		if not _ok(quote):
			return
		assert_bool(quote.proposal).is_true()
		assert_bool(quote.effects_applied).is_false()
		assert_bool(quote.offer.eligible).is_true()
		assert_str(quote.offer.category).is_equal("respec")
		assert_str(quote.offer.source).is_equal("policy:sinks.respec")
		assert_str(quote.offer.source_status).is_equal(policy.status)
		assert_int(int(quote.offer.amount)).is_equal(0 if uses == 0 else 50)
	assert_dict(policy).is_equal(before)

func test_first_and_subsequent_respec_offers_apply_only_explicit_fees() -> void:
	var policy: Dictionary = _read("res://data/balance/glint.json")
	var fresh: Dictionary = Ledger.fresh(50)
	if not _ok(fresh):
		return
	var state: Dictionary = fresh.state
	for uses: int in [0, 1]:
		var quote: Dictionary = Ledger.quote_respec(policy, uses, _context())
		if not _ok(quote):
			return
		var event: Dictionary = quote.offer.duplicate(true)
		event.id = "respec:" + str(uses)
		var result: Dictionary = Ledger.apply(state, event)
		if not _ok(result):
			return
		state = result.state
	assert_int(int(state.balance)).is_equal(0)
	assert_int(state.receipts.size()).is_equal(2)
	assert_array(state.owned).is_equal([])
	assert_bool(state.has("folk")).is_false()
	assert_bool(state.has("skill_points")).is_false()

func test_respec_context_is_explicit_and_each_blocked_context_stays_ineligible() -> void:
	var policy: Dictionary = _read("res://data/balance/glint.json")
	for key: String in ["at_hut_bed", "in_fight", "in_siege", "in_dungeon", "allow_proposal"]:
		var context: Dictionary = _context()
		context[key] = not context[key]
		var quote: Dictionary = Ledger.quote_respec(policy, 1, context)
		if not _ok(quote):
			return
		assert_bool(quote.offer.eligible).is_false()
		var fresh: Dictionary = Ledger.fresh(100)
		if not _ok(fresh):
			return
		var event: Dictionary = quote.offer.duplicate(true)
		event.id = "blocked:" + key
		_rejected(Ledger.apply(fresh.state, event))

func test_respec_quote_rejects_missing_or_malformed_context_and_uses() -> void:
	var policy: Dictionary = _read("res://data/balance/glint.json")
	for uses: Variant in [-1, true, 0.5, INF, NAN, MAX_AMOUNT + 1]:
		_rejected(Ledger.quote_respec(policy, uses, _context()))
	for key: String in _context():
		var missing: Dictionary = _context()
		missing.erase(key)
		_rejected(Ledger.quote_respec(policy, 0, missing))
		var bad: Dictionary = _context()
		bad[key] = "false"
		_rejected(Ledger.quote_respec(policy, 0, bad))

func test_simulation_reuses_actual_slice_values_without_changing_its_document() -> void:
	var doc: Dictionary = _scenario(_slice_events())
	var before: Dictionary = doc.duplicate(true)
	var result: Dictionary = Sim.simulate(doc)
	assert_int(int(result.exit_code)).is_equal(0)
	assert_dict(doc).is_equal(before)

func test_simulation_distinguishes_modeled_refusal_from_malformed_input() -> void:
	for event: Dictionary in [_spend("unaffordable", 11), _spend("blocked", 1, "shop", "seed", false)]:
		var result: Dictionary = Sim.simulate(_scenario([event], 10))
		assert_int(int(result.exit_code)).is_equal(1)
	for doc: Variant in [null, [], {"schema_version": 1}, _scenario([_earn("fractional", 0.5)]),
			{"schema_version": 1, "currency": "Dream Dust", "opening_balance": 0, "events": []}]:
		var result: Dictionary = Sim.simulate(doc)
		assert_int(int(result.exit_code)).is_equal(2)

func test_parser_preserves_literal_unicode_and_legitimate_replacement_character() -> void:
	var source: String = "Café λ 🚀 " + String.chr(0xfffd)
	var bytes: PackedByteArray = JSON.stringify(_scenario([_earn("unicode", 1, source)])).to_utf8_buffer()
	var before: PackedByteArray = bytes.duplicate()
	var parsed: Dictionary = Sim.parse_document(bytes)
	if not _ok(parsed):
		return
	assert_str(parsed.document.events[0].source).is_equal(source)
	assert_bool(bytes == before).is_true()
	assert_int(str(parsed.sha256).length()).is_equal(64)

func test_parser_accepts_utf8_bom_without_losing_exact_byte_identity() -> void:
	var plain: PackedByteArray = JSON.stringify(_scenario([])).to_utf8_buffer()
	var with_bom: PackedByteArray = PackedByteArray([0xef, 0xbb, 0xbf])
	with_bom.append_array(plain)
	var plain_result: Dictionary = Sim.parse_document(plain)
	var bom_result: Dictionary = Sim.parse_document(with_bom)
	if not _ok(plain_result) or not _ok(bom_result):
		return
	assert_dict(bom_result.document).is_equal(plain_result.document)
	assert_bool(bom_result.sha256 != plain_result.sha256).is_true()

func test_parser_accepts_paired_surrogates_bmp_escapes_and_escaped_ufffd() -> void:
	var slash: String = String.chr(92)
	var cases: Array = [
		[slash + "uD83D" + slash + "uDE80", "🚀"],
		[slash + "u00e9", "é"],
		[slash + "ufffd", String.chr(0xfffd)],
	]
	for entry: Array in cases:
		var parsed: Dictionary = Sim.parse_document(_raw_source_bytes(str(entry[0]).to_utf8_buffer()))
		if not _ok(parsed):
			return
		assert_str(parsed.document.events[0].source).is_equal(entry[1])

func test_parser_keeps_literal_backslash_u_text_and_escaped_quotes() -> void:
	var slash: String = String.chr(92)
	for source: String in [slash + "u0000", slash + "uD800",
			String.chr(34) + "quoted " + slash + "u0000" + String.chr(34)]:
		var bytes: PackedByteArray = JSON.stringify(_scenario([_earn("literal", 1, source)])).to_utf8_buffer()
		var parsed: Dictionary = Sim.parse_document(bytes)
		if not _ok(parsed):
			return
		assert_str(parsed.document.events[0].source).is_equal(source)

func test_parser_refuses_raw_nul_invalid_utf8_and_truncated_sequences() -> void:
	var cases: Array = [
		[0x00], [0xff], [0xfe], [0x80], [0xc0, 0x80], [0xc1, 0xbf],
		[0xe0, 0x80, 0xaf], [0xf0, 0x80, 0x80, 0xaf],
		[0xed, 0xa0, 0x80], [0xed, 0xbf, 0xbf],
		[0xf4, 0x90, 0x80, 0x80], [0xf5, 0x80, 0x80, 0x80],
		[0xe2, 0x28, 0xa1], [0xc2], [0xe2, 0x82], [0xf0, 0x9f, 0x9a],
	]
	for raw: Array in cases:
		_parse_refused(_raw_source_bytes(PackedByteArray(raw)))
	for raw: Array in [[0xc2], [0xe2, 0x82], [0xf0, 0x9f, 0x9a]]:
		_parse_refused(PackedByteArray(raw))

func test_parser_refuses_escaped_nul_and_unpaired_json_surrogates() -> void:
	var slash: String = String.chr(92)
	for escaped: String in [slash + "u0000", "before" + slash + "u0000after",
			slash + "ud800", slash + "uDBFF", slash + "udc00", slash + "uDFFF",
			slash + "ud800" + slash + "u0041", slash + "ud800" + slash + "ud800",
			slash + "udc00" + slash + "ud800"]:
		_parse_refused(_raw_source_bytes(escaped.to_utf8_buffer()))
	var document: String = JSON.stringify(_scenario([_earn("PARSER_ID", 1)]))
	_parse_refused(document.replace("PARSER_ID", slash + "u0000").to_utf8_buffer())

func test_parser_refuses_malformed_unicode_escapes_without_decoding_replacements() -> void:
	var slash: String = String.chr(92)
	for escaped: String in [slash + "u", slash + "u12", slash + "u12xz",
			slash + "uD800" + slash + "u12xz"]:
		_parse_refused(_raw_source_bytes(escaped.to_utf8_buffer()))
