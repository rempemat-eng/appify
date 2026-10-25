extends GdUnitTestSuite
## The zone loader swaps zones, carries the one player to the named spawn, and refuses unbuilt zones.
## Also the screen's scale rule.

var _table: Dictionary
var _root: Node2D
var _player: Player

func before_test() -> void:
	SaveGame.reset()
	_table = Zones.table
	Zones.table = {"a": "res://test/fixtures/zone_a.tscn", "b": "res://test/fixtures/zone_b.tscn"}
	_root = auto_free(Node2D.new())
	add_child(_root)
	_player = auto_free(load("res://actors/player.tscn").instantiate())
	_player.input_enabled = false
	Zones.current = null
	Zones.attach(_root, _player)

func after_test() -> void:
	Zones.table = _table
	Zones.current = null
	Zones.root = null

func test_go_to_places_the_player() -> void:
	assert_bool(Zones.go_to("a", "west")).is_true()
	assert_str(Zones.current.zone_id).is_equal("a")
	assert_object(_player.get_parent()).is_same(Zones.current.actors)
	assert_vector(_player.global_position).is_equal(Vector2(30, 60))
	assert_str(SaveGame.data.zone).is_equal("a")
	assert_bool(Zones.go_to("b", "from_a")).is_true()
	assert_str(Zones.current.zone_id).is_equal("b")
	assert_vector(_player.global_position).is_equal(Vector2(200, 90))
	assert_int(_root.get_child_count()).is_equal(1)

func test_unbuilt_zone_is_refused() -> void:
	Zones.go_to("a", "west")
	assert_bool(Zones.go_to("nowhere", "start")).is_false()
	assert_str(Zones.current.zone_id).is_equal("a")

func test_woodland_is_registered() -> void:
	assert_bool(_table.has("woodland")).is_true()
	assert_bool(ResourceLoader.exists(_table.woodland)).is_true()

func test_screen_scale_rule() -> void:
	var ps := load("res://main/pixel_screen.gd")
	assert_float(ps.choose_scale(Vector2(1920, 1080), "fill")).is_equal(2.0)
	assert_float(ps.choose_scale(Vector2(3840, 2160), "fill")).is_equal(4.0)
	assert_float(ps.choose_scale(Vector2(1920, 1200), "fill")).is_equal(2.0)
	assert_float(ps.choose_scale(Vector2(1600, 900), "fill")).is_equal_approx(1.6667, 0.001)
	assert_float(ps.choose_scale(Vector2(1600, 900), "whole")).is_equal(1.0)
