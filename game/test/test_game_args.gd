extends GdUnitTestSuite
## Y33 source-prepared controls for the real parse_args -> _camp path.
## Not executed yet: an allocated import/runtime must first establish actual RED.
## Intended fixture bypass: production save/reset, zone boot, character setup and enemy/dresser
## lifecycle callbacks. This isolation has NOT been observed in an allocated runtime yet.

const GAME := preload("res://game.gd")

# The real game's onready variables still need correctly typed children. Suppress only
# unrelated camera lifecycle registration/processing; _camp itself is never overridden.
class QuietCamera extends PhantomCamera2D:
	func _enter_tree() -> void:
		pass
	func _exit_tree() -> void:
		pass
	func _ready() -> void:
		pass
	func _process(_delta: float) -> void:
		pass
	func _physics_process(_delta: float) -> void:
		pass

class CampHarness extends "res://game.gd":
	func _ready() -> void:
		pass
	func _process(_delta: float) -> void:
		pass
	func _unhandled_input(_event: InputEvent) -> void:
		pass

func _fixture(tokens: PackedStringArray) -> Array:
	var game: CampHarness = auto_free(CampHarness.new())
	var zone_root := Node2D.new()
	zone_root.name = "ZoneRoot"
	game.add_child(zone_root)
	var camera := QuietCamera.new()
	camera.name = "PCam"
	game.add_child(camera)
	var ui := Node.new()
	ui.name = "UI"
	game.add_child(ui)
	var hud := Control.new()
	hud.name = "HUD"
	ui.add_child(hud)
	var paused := Label.new()
	paused.name = "Paused"
	ui.add_child(paused)
	add_child(game)

	# Intentionally stay outside SceneTree to avoid Player/camp/dresser lifecycle
	# callbacks; confirm this fixture boundary in the allocated run. The consumer still uses
	# the actual Player type, parser, packed camp scene and player-parent placement code.
	var host: Node2D = auto_free(Node2D.new())
	var player := Player.new()
	player.position = Vector2(37.0, 19.0)
	host.add_child(player)
	game.player = player
	game.args = GAME.parse_args(tokens)
	return [game, host, player]

func _assert_real_camp(tokens: PackedStringArray, expected_world_offset: Vector2) -> void:
	var fixture := _fixture(tokens)
	var game: CampHarness = fixture[0]
	var host: Node2D = fixture[1]
	var player: Player = fixture[2]
	# A consumer script error must yield a failure, not leave this test awaiting an
	# aborted coroutine forever. The real method defers by one process frame.
	game.call_deferred("_camp")
	for _frame in 4:
		await get_tree().process_frame
	assert_int(host.get_child_count()).is_equal(2)
	if host.get_child_count() != 2:
		return
	var camp := host.get_child(1) as Node2D
	assert_object(camp).is_not_null()
	if camp == null:
		return
	assert_object(camp.get_parent()).is_same(host)
	assert_str(camp.scene_file_path).is_equal("res://enemies/woodland_camp.tscn")
	assert_str(camp.get_script().resource_path).is_equal("res://enemies/woodland_camp.gd")
	assert_str(camp.get("camp_id")).is_equal("woodland_slice_c61")
	assert_object(camp.get_node_or_null("Dresser")).is_not_null()
	assert_vector(camp.position).is_equal(player.position + expected_world_offset * GAME.DENSITY)
	assert_bool(host.is_inside_tree()).is_false()
	assert_bool(player.is_inside_tree()).is_false()
	assert_bool(camp.is_inside_tree()).is_false()

func test_parser_preserves_bare_camp_as_boolean_true() -> void:
	var parsed := GAME.parse_args(PackedStringArray(["--camp"]))
	assert_bool(parsed.has("camp")).is_true()
	assert_bool(parsed.camp is bool).is_true()
	assert_bool(parsed.camp).is_true()

func test_parser_preserves_explicit_camp_text() -> void:
	var parsed := GAME.parse_args(PackedStringArray(["--camp=-4.5,2.25"]))
	assert_str(parsed.camp).is_equal("-4.5,2.25")

func test_absent_camp_is_not_inferred_from_other_arguments() -> void:
	var fixture := _fixture(PackedStringArray(["--fresh", "--zone=woodland"]))
	var game: CampHarness = fixture[0]
	var host: Node2D = fixture[1]
	assert_bool(game.args.has("camp")).is_false()
	assert_int(host.get_child_count()).is_equal(1)
	# There is no production _camp call without the flag, matching _ready's guard.

func test_bare_camp_reaches_existing_north_default() -> void:
	await _assert_real_camp(PackedStringArray(["--camp"]), Vector2(0.0, -70.0))

func test_explicit_positive_offset_reaches_real_consumer() -> void:
	await _assert_real_camp(PackedStringArray(["--camp=12,8"]), Vector2(12.0, 8.0))

func test_explicit_negative_decimal_offset_reaches_real_consumer() -> void:
	await _assert_real_camp(PackedStringArray(["--camp=-4.5,-2.25"]), Vector2(-4.5, -2.25))

func test_explicit_zero_offset_is_not_replaced_by_default() -> void:
	await _assert_real_camp(PackedStringArray(["--camp=0,0"]), Vector2.ZERO)
