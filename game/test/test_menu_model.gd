extends GdUnitTestSuite

const Model = preload("res://core/menu_model.gd")

func _menu() -> RefCounted:
	var menu = Model.new()
	assert_bool(menu.configure(["inventory", "journal", "settings"])).is_true()
	return menu

func test_unconfigured_and_closed_input_is_inert() -> void:
	var menu = Model.new()
	assert_bool(menu.open()).is_false()
	assert_bool(menu.back()).is_false()
	assert_bool(menu.show_detail()).is_false()
	assert_bool(menu.move_row(1)).is_false()
	assert_bool(menu.move_tab(1)).is_false()
	assert_bool(menu.select_row("a")).is_false()
	assert_bool(menu.select_tab("journal")).is_false()

func test_configuration_rejects_invalid_input_atomically() -> void:
	var menu = _menu()
	menu.open("journal")
	var before: Dictionary = menu.snapshot()
	for bad in [null, {}, [], [""], [" "], [1], ["journal", "journal"]]:
		assert_bool(menu.configure(bad)).is_false()
		assert_dict(menu.snapshot()).is_equal(before)

func test_tab_wrapping_and_back_do_not_reopen_closed_menu() -> void:
	var menu = _menu()
	assert_bool(menu.open()).is_true()
	menu.move_tab(-1)
	assert_str(menu.snapshot().tab).is_equal("settings")
	menu.move_tab(1)
	assert_str(menu.snapshot().tab).is_equal("inventory")
	assert_bool(menu.open("missing")).is_false()
	assert_bool(menu.back()).is_true()
	assert_bool(menu.back()).is_false()
	assert_bool(menu.snapshot().open).is_false()

func test_empty_rows_and_bounded_selection() -> void:
	var menu = _menu()
	menu.open()
	assert_bool(menu.show_detail()).is_false()
	assert_bool(menu.move_row(1)).is_false()
	menu.set_rows("inventory", [{"id": "a"}, {"id": "b"}])
	menu.move_row(-1)
	assert_str(menu.snapshot().selected.inventory).is_equal("a")
	menu.move_row(100)
	menu.move_row(1)
	assert_str(menu.snapshot().selected.inventory).is_equal("b")
	assert_bool(menu.select_row("unknown")).is_false()

func test_detail_back_and_tab_changes_preserve_per_tab_selection() -> void:
	var menu = _menu()
	menu.set_rows("inventory", [{"id": "a"}, {"id": "b"}])
	menu.set_rows("journal", [{"id": "q"}])
	menu.open()
	menu.select_row("b")
	menu.show_detail()
	assert_bool(menu.snapshot().detail).is_true()
	menu.back()
	assert_bool(menu.snapshot().open).is_true()
	assert_bool(menu.snapshot().detail).is_false()
	menu.show_detail()
	menu.select_tab("journal")
	assert_bool(menu.snapshot().detail).is_false()
	menu.select_tab("inventory")
	assert_str(menu.snapshot().selected.inventory).is_equal("b")
	menu.close()
	menu.open()
	assert_str(menu.snapshot().selected.inventory).is_equal("b")
	assert_bool(menu.snapshot().detail).is_false()

func test_row_refresh_retains_identity_or_selects_nearest_without_stale_detail() -> void:
	var menu = _menu()
	menu.set_rows("inventory", [{"id": "a"}, {"id": "b"}, {"id": "c"}])
	menu.open()
	menu.select_row("b")
	menu.show_detail()
	menu.set_rows("inventory", [{"id": "c"}, {"id": "b"}])
	assert_str(menu.snapshot().selected.inventory).is_equal("b")
	assert_bool(menu.snapshot().detail).is_true()
	menu.set_rows("inventory", [{"id": "c"}])
	assert_str(menu.snapshot().selected.inventory).is_equal("c")
	assert_bool(menu.snapshot().detail).is_false()
	menu.set_rows("inventory", [])
	assert_str(menu.snapshot().selected.inventory).is_empty()
	assert_bool(menu.show_detail()).is_false()

func test_rows_reject_invalid_replacements_and_preserve_input() -> void:
	var menu = _menu()
	menu.set_rows("inventory", [{"id": "a", "opaque": {"future": [1]}}])
	menu.open()
	menu.show_detail()
	var before: Dictionary = menu.snapshot()
	for bad in [null, {}, [null], [{}], [{"id": ""}], [{"id": "a"}, {"id": "a"}]]:
		assert_bool(menu.set_rows("inventory", bad)).is_false()
		assert_dict(menu.snapshot()).is_equal(before)
	assert_bool(menu.set_rows("unknown", [])).is_false()
	var rows := [{"id": "new", "opaque": [1]}]
	menu.set_rows("inventory", rows)
	rows[0].opaque.append(2)
	assert_array(menu.snapshot().rows.inventory[0].opaque).is_equal([1])

func test_signal_and_snapshot_payloads_are_detached() -> void:
	var menu = _menu()
	menu.changed.connect(func(view: Dictionary) -> void:
		view.tabs.clear()
		view.rows.clear()
		view.selected.clear())
	menu.set_rows("inventory", [{"id": "a", "opaque": [1]}])
	menu.open()
	var view: Dictionary = menu.snapshot()
	view.rows.inventory[0].opaque.append(2)
	view.tabs.clear()
	assert_array(menu.snapshot().tabs).is_equal(["inventory", "journal", "settings"])
	assert_array(menu.snapshot().rows.inventory[0].opaque).is_equal([1])

func test_inventory_preserves_order_fields_and_searches_case_insensitively() -> void:
	var items := [{"id": "b", "name": "Bronze fitting", "future": {"x": [1]}}, {"id": "a"}]
	var result: Dictionary = Model.inventory(items)
	assert_bool(result.ok).is_true()
	assert_array(result.rows).is_equal(items)
	assert_int(Model.inventory(items, "BRONZE").rows.size()).is_equal(1)
	assert_str(Model.inventory(items, "A").rows[0].id).is_equal("a")
	assert_array(Model.inventory(items, "unknown").rows).is_empty()
	result.rows[0].future.x.append(2)
	assert_array(items[0].future.x).is_equal([1])

func test_inventory_malformed_rows_never_become_empty_success() -> void:
	for bad in [null, {}, [null], [{}], [{"id": " "}], [{"id": "a", "name": null}], [{"id": "a"}, {"id": "a"}]]:
		var result: Dictionary = Model.inventory(bad, "no match")
		assert_bool(result.ok).is_false()
		assert_array(result.rows).is_empty()
		assert_str(result.error).is_not_empty()

func test_every_authored_quest_and_step_project_without_mutating_live_state() -> void:
	var before: Dictionary = SaveGame.data.duplicate(true)
	var defs_before: Dictionary = Quests.defs.duplicate(true)
	assert_int(Quests.defs.size()).is_equal(20)
	assert_array(Model.journal(Quests.defs, {}).rows).is_empty()
	for id in Quests.defs:
		var def: Dictionary = Quests.defs[id]
		for step in def.steps.size():
			var records := {id: {"state": "active", "step": float(step), "future": [1]}}
			var result: Dictionary = Model.journal(Quests.defs, records)
			assert_bool(result.ok).is_true()
			assert_str(result.rows[0].text).is_equal(def.steps[step].get("text", ""))
			assert_int(result.rows[0].step).is_equal(step)
			assert_str(result.rows[0].title).is_equal(def.title)
			assert_dict(records).is_equal({id: {"state": "active", "step": float(step), "future": [1]}})
		var done: Dictionary = Model.journal(Quests.defs, {id: {"state": "done", "step": def.steps.size()}})
		assert_bool(done.ok).is_true()
		assert_str(done.rows[0].text).is_empty()
	assert_dict(SaveGame.data).is_equal(before)
	assert_dict(Quests.defs).is_equal(defs_before)

func test_journal_hides_unstarted_and_orders_active_before_completed() -> void:
	var defs := {"z": {"id": "z", "steps": [{"text": "next"}]}, "a": {"id": "a", "steps": [{}]}, "secret": {"id": "secret", "steps": [{}]}}
	var result: Dictionary = Model.journal(defs, {"a": {"state": "done", "step": 1}, "secret": {}, "z": {"state": "active"}})
	assert_bool(result.ok).is_true()
	assert_int(result.rows.size()).is_equal(2)
	assert_str(result.rows[0].id).is_equal("z")
	assert_str(result.rows[1].id).is_equal("a")

func test_journal_reports_unknown_and_malformed_saved_progress() -> void:
	var defs := {"q": {"id": "q", "steps": [{"text": "next"}]}}
	for bad in [null, [], {"missing": {}}, {"q": null}, {"q": {"state": "future"}}, {"q": {"state": "active", "step": 1}}, {"q": {"state": "done", "step": 0}}, {"q": {"step": -1}}, {"q": {"step": 0.5}}, {"q": {"step": INF}}, {"q": {"step": true}}]:
		var result: Dictionary = Model.journal(defs, bad)
		assert_bool(result.ok).is_false()
		assert_str(result.error).is_not_empty()
	assert_bool(Model.journal(null, {}).ok).is_false()
	assert_bool(Model.journal({"q": {"id": "other", "steps": [{}]}}, {"q": {}}).ok).is_false()

func test_live_quest_transition_is_reflected_without_a_second_progress_engine() -> void:
	var before: Dictionary = SaveGame.data.duplicate(true)
	SaveGame.reset()
	Quests.start_quest("woodland_stones")
	var first: Dictionary = Model.journal(Quests.defs, SaveGame.data.quests)
	assert_int(first.rows[0].step).is_equal(0)
	Quests.notify("camp:meadow")
	var next: Dictionary = Model.journal(Quests.defs, SaveGame.data.quests)
	assert_int(next.rows[0].step).is_equal(1)
	assert_str(next.rows[0].text).is_equal(Quests.current_step("woodland_stones").text)
	SaveGame.data = before
