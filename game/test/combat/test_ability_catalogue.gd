extends GdUnitTestSuite

func test_units_do_not_scale_damage_timers_or_screen_anchors() -> void:
	assert_float(AbilityCatalogue.actor_distance(57.0)).is_equal(171.0)
	var bramble := AbilityCatalogue.kit("bramble")
	assert_float(float(bramble.base.primary_projectiles[0].damage)).is_equal(22.0)
	assert_float(float(bramble.base.actions.primary.release_seconds)).is_equal(0.1596)
	assert_float(float(bramble.powered.duration_seconds)).is_equal(8.0)

func test_cairn_hitbox_follows_manifest_height_without_changing_other_reach() -> void:
	assert_float(AbilityCatalogue.hitbox_distance(32.0, "cairn", {"body_height_target": 104})).is_equal_approx(96.0 * 104.0 / 74.0, 0.000001)
	assert_float(AbilityCatalogue.hitbox_distance(32.0, "cairn", {"body_height_target": 88.8})).is_equal_approx(115.2, 0.000001)
	assert_float(AbilityCatalogue.hitbox_distance(36.0, "bramble", {"body_height_target": 104})).is_equal(108.0)

func test_known_stateful_rules_are_not_replaced_by_animation_descriptions() -> void:
	var pendle := AbilityCatalogue.kit("pendle")
	assert_int(int(pendle.resources.ammo_capacity)).is_equal(6)
	var mote := AbilityCatalogue.kit("mote")
	assert_int(mote.powered.primary_projectiles.size()).is_equal(5)
	var nix := AbilityCatalogue.kit("nix")
	assert_float(float(nix.base.actions.secondary.release_seconds)).is_equal(0.05)
	assert_float(float(nix.powered.duration_seconds)).is_equal(7.0)
	assert_bool(AbilityCatalogue.kit("unknown").is_empty()).is_true()
