extends GdUnitTestSuite

const Runtime = preload("res://core/folk_progression.gd")
const ROOT := "res://data/progression/"
var model: RefCounted
var catalogue: Dictionary
var documents: Array

func before_test() -> void:
	catalogue = JSON.parse_string(FileAccess.get_file_as_string(ROOT + "catalogue.json"))
	documents = []
	for id in catalogue.characters:
		documents.append(JSON.parse_string(FileAccess.get_file_as_string(ROOT + id + ".json")))
	model = Runtime.new()
	assert_int(model.configure(catalogue, documents)).is_equal(OK)

func _join(id: String = "bramble", at_level: int = 1) -> void:
	assert_int(model.advance_level(at_level)).is_equal(OK)
	assert_int(model.join_folk(id)).is_equal(OK)

func test_all_fourteen_real_trees_and_tiers_are_consumed_without_mutation() -> void:
	var original_catalogue := catalogue.duplicate(true)
	var original_documents := documents.duplicate(true)
	assert_int(catalogue.characters.size()).is_equal(14)
	assert_int(model.advance_level(30)).is_equal(OK)
	for doc in documents:
		# Each tier matrix starts in a fresh save; inherited late-join tiers have their own test.
		assert_int(model.configure(catalogue, documents)).is_equal(OK)
		assert_int(model.advance_level(30)).is_equal(OK)
		assert_int(model.join_folk(doc.id)).is_equal(OK)
		assert_int(model.available_points(doc.id)).is_equal(29)
		var count := 0
		var cost := 0
		for branch in doc.abilities.skill_tree.branches:
			for node in branch.nodes:
				count += 1
				cost += int(node.cost)
				assert_dict(model.node_offer(doc.id, node.id).node).is_equal(node)
		assert_int(count).is_equal(15)
		assert_int(cost).is_equal(33)
		for tier in [2, 3, 4]:
			var offer: Dictionary = model.tier_offer(doc.id, tier, {"forge_open": true, "great_forge": true})
			assert_bool(offer.allowed).is_true()
			assert_dict(offer.tier).is_equal(doc.weapon.tiers[tier - 1])
			assert_dict(offer.cost).is_equal(doc.weapon.tiers[tier - 1].cost)
			assert_int(model.record_tier(doc.id, tier, {"forge_open": true, "great_forge": true})).is_equal(OK)
	assert_dict(catalogue).is_equal(original_catalogue)
	assert_array(documents).is_equal(original_documents)
	assert_str(model.catalogue_status()).contains("placeholder")

func test_level_points_are_shared_in_level_but_independent_per_folk() -> void:
	_join()
	assert_int(model.available_points("bramble")).is_equal(0)
	assert_int(model.advance_level(2)).is_equal(OK)
	assert_int(model.unlock_node("bramble", "fletcher")).is_equal(OK)
	assert_int(model.available_points("bramble")).is_equal(0)
	assert_int(model.join_folk("iona")).is_equal(OK)
	assert_int(model.available_points("iona")).is_equal(1)
	assert_int(model.advance_level(4)).is_equal(OK)
	assert_int(model.available_points("bramble")).is_equal(2)
	assert_int(model.available_points("iona")).is_equal(3)
	assert_int(model.available_points("absent")).is_equal(-1)

func test_unlock_needs_level_prerequisites_and_conserved_points() -> void:
	_join()
	assert_str(model.node_offer("bramble", "fletcher").reason).is_equal("level")
	assert_int(model.advance_level(3)).is_equal(OK)
	assert_str(model.node_offer("bramble", "steady_aim").reason).is_equal("prerequisite")
	assert_int(model.unlock_node("bramble", "fletcher")).is_equal(OK)
	assert_str(model.node_offer("bramble", "steady_aim").reason).is_equal("points")
	assert_int(model.advance_level(4)).is_equal(OK)
	assert_int(model.unlock_node("bramble", "steady_aim")).is_equal(OK)
	assert_int(model.available_points("bramble")).is_equal(0)
	var before: Dictionary = model.snapshot()
	assert_int(model.unlock_node("bramble", "steady_aim")).is_equal(ERR_UNAVAILABLE)
	assert_int(model.unlock_node("bramble", "unknown")).is_equal(ERR_UNAVAILABLE)
	assert_int(model.unlock_node("unknown", "fletcher")).is_equal(ERR_UNAVAILABLE)
	assert_dict(model.snapshot()).is_equal(before)

func test_canonical_changes_stay_unavailable_pending_c60() -> void:
	_join("bramble", 30)
	for id in ["fletcher", "steady_aim", "long_eye", "steady_aim_2"]:
		assert_int(model.unlock_node("bramble", id)).is_equal(OK)
	var before: Dictionary = model.snapshot()
	assert_str(model.node_offer("bramble", "briar_volley").reason).is_equal("c60_approval_required")
	assert_int(model.unlock_node("bramble", "briar_volley")).is_equal(ERR_UNAVAILABLE)
	assert_dict(model.snapshot()).is_equal(before)

func test_level_thirty_budget_can_buy_everything_except_one_keystone() -> void:
	_join("bramble", 30)
	for branch in documents[0].abilities.skill_tree.branches:
		for node in branch.nodes:
			if node.id != "briar_volley":
				assert_int(model.unlock_node("bramble", node.id)).is_equal(OK)
	assert_int(model.snapshot().folk.bramble.nodes.size()).is_equal(14)
	assert_int(model.available_points("bramble")).is_equal(0)
	assert_int(model.unlock_node("bramble", "briar_volley")).is_equal(ERR_UNAVAILABLE)

func test_tier_boundaries_and_forge_requirements() -> void:
	_join()
	for entry in [[2, 8, "forge_open"], [3, 16, "forge_open"], [4, 24, "great_forge"]]:
		assert_int(model.advance_level(entry[1] - 1)).is_equal(OK)
		assert_str(model.tier_offer("bramble", entry[0], {entry[2]: true}).reason).is_equal("level")
		assert_int(model.advance_level(entry[1])).is_equal(OK)
		assert_str(model.tier_offer("bramble", entry[0]).reason).is_equal(entry[2])
		var before: Dictionary = model.snapshot()
		assert_int(model.record_tier("bramble", entry[0], {entry[2]: "true"})).is_equal(ERR_UNAVAILABLE)
		assert_dict(model.snapshot()).is_equal(before)
		var offer: Dictionary = model.tier_offer("bramble", entry[0], {entry[2]: true})
		assert_bool(offer.allowed).is_true()
		assert_str(offer.status).contains("placeholder")
		assert_int(model.record_tier("bramble", entry[0], {entry[2]: true})).is_equal(OK)
	assert_int(model.snapshot().folk.bramble.weapon_tier).is_equal(4)

func test_tiers_cannot_be_skipped_repeated_or_downgraded() -> void:
	_join("bramble", 30)
	var before: Dictionary = model.snapshot()
	for tier in [0, 1, 3, 4, 5, 2.5, true, null, INF]:
		assert_int(model.record_tier("bramble", tier, {"forge_open": true, "great_forge": true})).is_equal(ERR_UNAVAILABLE)
	assert_int(model.record_tier("absent", 2)).is_equal(ERR_UNAVAILABLE)
	assert_int(model.record_tier("bramble", 2, [])).is_equal(ERR_UNAVAILABLE)
	assert_dict(model.snapshot()).is_equal(before)

func test_late_joiner_gets_unspent_points_and_tier_three_but_not_starfall() -> void:
	_join("bramble", 24)
	assert_int(model.unlock_node("bramble", "fletcher")).is_equal(OK)
	for tier in [2, 3, 4]:
		assert_int(model.record_tier("bramble", tier, {"forge_open": true, "great_forge": true})).is_equal(OK)
	assert_int(model.join_folk("cairn")).is_equal(OK)
	assert_int(model.snapshot().folk.cairn.weapon_tier).is_equal(3)
	assert_int(model.available_points("cairn")).is_equal(23)
	assert_array(model.snapshot().folk.cairn.nodes).is_empty()
	assert_int(model.join_folk("cairn")).is_equal(ERR_ALREADY_EXISTS)
	assert_int(model.join_folk("absent")).is_equal(ERR_DOES_NOT_EXIST)

func test_invalid_levels_preserve_state_and_emit_nothing() -> void:
	_join("bramble", 5)
	var before: Dictionary = model.snapshot()
	var events: Array = []
	model.changed.connect(func(value: Dictionary) -> void: events.append(value))
	for value in [0, 4, 31, 6.5, "6", true, null, NAN, INF, -INF]:
		assert_int(model.advance_level(value)).is_equal(ERR_INVALID_PARAMETER)
	assert_dict(model.snapshot()).is_equal(before)
	assert_array(events).is_empty()
	assert_int(model.advance_level(5)).is_equal(OK)
	assert_array(events).is_empty()

func test_input_configuration_offers_and_snapshots_are_detached() -> void:
	_join("bramble", 8)
	catalogue.status = "changed"
	documents[0].abilities.skill_tree.branches[0].nodes[0].cost = 50
	documents[0].weapon.tiers[1].requires.level = 30
	assert_bool(model.node_offer("bramble", "fletcher").allowed).is_true()
	var offer: Dictionary = model.tier_offer("bramble", 2, {"forge_open": true})
	offer.cost.glint = 0
	offer.tier.mechanics.clear()
	assert_float(model.tier_offer("bramble", 2, {"forge_open": true}).cost.glint).is_equal(60.0)
	var snapshot: Dictionary = model.snapshot()
	snapshot.folk.bramble.nodes.append("fletcher")
	assert_int(model.available_points("bramble")).is_equal(7)
	model.changed.connect(func(value: Dictionary) -> void: value.folk.clear())
	assert_int(model.unlock_node("bramble", "fletcher")).is_equal(OK)
	assert_bool(model.snapshot().folk.has("bramble")).is_true()

func test_restore_round_trip_keeps_unknown_extensions_and_normalises_numbers() -> void:
	_join("bramble", 16)
	for id in ["fletcher", "steady_aim", "long_eye"]:
		assert_int(model.unlock_node("bramble", id)).is_equal(OK)
	assert_int(model.record_tier("bramble", 2, {"forge_open": true})).is_equal(OK)
	var state: Dictionary = model.snapshot()
	state.progression.xp = 7
	state.folk.bramble.look = {"outfit": "unknown_future_look"}
	state.extension = {"list": [1]}
	state.folk.bramble.nodes.reverse()  # persisted ownership is a set, not an event log
	var decoded: Dictionary = JSON.parse_string(JSON.stringify(state))
	var before := decoded.duplicate(true)
	assert_int(model.restore(decoded)).is_equal(OK)
	assert_dict(decoded).is_equal(before)
	var expected := before.duplicate(true)
	expected.progression.level = 16
	expected.folk.bramble.weapon_tier = 2
	assert_dict(model.snapshot()).is_equal(expected)
	assert_int(typeof(model.snapshot().progression.level)).is_equal(TYPE_INT)
	assert_int(typeof(model.snapshot().folk.bramble.weapon_tier)).is_equal(TYPE_INT)
	decoded.extension.list.append(2)
	assert_int(model.snapshot().extension.list.size()).is_equal(1)

func test_invalid_restores_refuse_without_mutation_or_signals() -> void:
	_join("bramble", 4)
	assert_int(model.unlock_node("bramble", "fletcher")).is_equal(OK)
	var before: Dictionary = model.snapshot()
	var events: Array = []
	model.changed.connect(func(value: Dictionary) -> void: events.append(value))
	var invalid: Array = [null, [], {}, {"progression": null, "folk": {}},
		{"progression": {"level": 2.5}, "folk": {}}, {"progression": {"level": 31}, "folk": {}},
		{"progression": {"level": 4}, "folk": {"unknown": {"nodes": [], "weapon_tier": 1}}}]
	for bad_record in [null, [], {"nodes": [], "weapon_tier": 2},
			{"nodes": ["steady_aim"], "weapon_tier": 1},
			{"nodes": ["fletcher", "fletcher"], "weapon_tier": 1},
			{"nodes": ["unknown"], "weapon_tier": 1},
			{"nodes": [], "weapon_tier": "1"}, {"nodes": null, "weapon_tier": 1}]:
		invalid.append({"progression": {"level": 4}, "folk": {"bramble": bad_record}})
	for value in invalid:
		assert_int(model.restore(value)).is_equal(ERR_INVALID_DATA)
		assert_dict(model.snapshot()).is_equal(before)
	assert_array(events).is_empty()

func test_restore_refuses_overspent_points_even_with_valid_prerequisites() -> void:
	var state := {"progression": {"level": 3}, "folk": {"bramble": {"nodes": ["fletcher", "steady_aim"], "weapon_tier": 1}}}
	assert_int(model.restore(state)).is_equal(ERR_INVALID_DATA)

func test_malformed_catalogues_and_graphs_are_rejected_atomically() -> void:
	_join("bramble", 4)
	var before: Dictionary = model.snapshot()
	var bad_catalogues: Array = [null, [], {}, {"schema_version": 2}]
	for c in bad_catalogues:
		assert_int(model.configure(c, documents)).is_equal(ERR_INVALID_DATA)
		assert_dict(model.snapshot()).is_equal(before)
	for mode in ["duplicate_id", "cycle", "missing_prerequisite", "fraction_cost", "null_branch", "invalid_tier", "future_schema"]:
		var changed := documents.duplicate(true)
		var nodes: Array = changed[0].abilities.skill_tree.branches[0].nodes
		match mode:
			"duplicate_id": nodes[1].id = nodes[0].id
			"cycle": nodes[0].requires = [nodes[1].id]
			"missing_prerequisite": nodes[0].requires = ["missing"]
			"fraction_cost": nodes[0].cost = 1.5
			"null_branch": changed[0].abilities.skill_tree.branches[0] = null
			"invalid_tier": changed[0].weapon.tiers[1].requires.level = 9
			"future_schema": changed[0].schema_version = 2
		assert_int(model.configure(catalogue, changed)).is_equal(ERR_INVALID_DATA)
		assert_dict(model.snapshot()).is_equal(before)
	assert_int(model.configure(catalogue, documents.slice(1))).is_equal(ERR_INVALID_DATA)
	assert_dict(model.snapshot()).is_equal(before)

func test_unconfigured_runtime_cannot_create_progress_or_restore() -> void:
	var empty := Runtime.new()
	assert_int(empty.join_folk("bramble")).is_equal(ERR_DOES_NOT_EXIST)
	assert_int(empty.advance_level(2)).is_equal(ERR_INVALID_PARAMETER)
	assert_int(empty.restore({"progression": {"level": 1}, "folk": {}})).is_equal(ERR_INVALID_DATA)
	assert_bool(empty.node_offer("bramble", "fletcher").allowed).is_false()
	assert_bool(empty.tier_offer("bramble", 2).allowed).is_false()

func test_folk_material_costs_are_not_replaced_by_generic_counts() -> void:
	_join("bramble", 8)
	var offer: Dictionary = model.tier_offer("bramble", 2, {"forge_open": true})
	assert_dict(offer.cost.home_material).is_equal({"material": "timber", "count": 2.0})
	offer.cost.home_material.material = "changed"
	assert_str(model.tier_offer("bramble", 2, {"forge_open": true}).cost.home_material.material).is_equal("timber")

func test_nested_configuration_type_errors_are_clean_and_atomic() -> void:
	_join("bramble", 8)
	var before: Dictionary = model.snapshot()
	for field in ["levels", "characters", "weapon_tiers"]:
		for bad in [null, false, "bad", 2, []]:
			var changed := catalogue.duplicate(true)
			changed[field] = bad
			assert_int(model.configure(changed, documents)).is_equal(ERR_INVALID_DATA)
			assert_dict(model.snapshot()).is_equal(before)
	for mode in ["missing_node_array", "null_requires", "negative_cost", "nonfinite_level", "bad_material", "bad_count", "bad_tier_level"]:
		var changed := documents.duplicate(true)
		match mode:
			"missing_node_array": changed[0].abilities.skill_tree.branches[0].nodes = null
			"null_requires": changed[0].abilities.skill_tree.branches[0].nodes[0].requires = null
			"negative_cost": changed[0].abilities.skill_tree.branches[0].nodes[0].cost = -1
			"nonfinite_level": changed[0].abilities.skill_tree.branches[0].nodes[0].level = INF
			"bad_material": changed[0].weapon.tiers[1].cost.home_material.material = []
			"bad_count": changed[0].weapon.tiers[1].cost.home_material.count = NAN
			"bad_tier_level": changed[0].weapon.tiers[0].requires.level = 2
		assert_int(model.configure(catalogue, changed)).is_equal(ERR_INVALID_DATA)
		assert_dict(model.snapshot()).is_equal(before)
