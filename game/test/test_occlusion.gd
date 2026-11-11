extends GdUnitTestSuite
## An actor behind tall scenery stays readable (world/occlusion.gd; art-style.md rule 11): when one picture
## drawn in front hides at least 40 % of its body, a faint copy shows through. Measured on a made-up stage
## first (so every branch of the rule is pinned), then where it was found by playing: behind the oak on
## Crossroads' terrace road and under the woodland's willow.

var _table: Dictionary

func before_test() -> void:
	SaveGame.reset()
	_table = Zones.table

func after_test() -> void:
	SaveGame.reset()
	Zones.table = _table
	Zones.current = null
	Zones.root = null

func _picture(w: int, h: int, opaque: Rect2i) -> ImageTexture:
	var img := Image.create(w, h, false, Image.FORMAT_RGBA8)
	img.fill(Color(0, 0, 0, 0))
	img.fill_rect(opaque, Color(0.2, 0.5, 0.2, 1.0))
	return ImageTexture.create_from_image(img)

## A y-sorted stage with an Occlusion, as Zone._ready builds it.
func _stage() -> Node2D:
	var root: Node2D = auto_free(Node2D.new())
	root.y_sort_enabled = true
	add_child(root)
	var occ := Occlusion.new()
	occ.zone = root
	root.add_child(occ)
	return root

func _occ(root: Node2D) -> Occlusion:
	return root.get_node("Occlusion") as Occlusion

## Scenery with its feet at `feet`: a picture w x h whose opaque part is `opaque` (all of it by default).
func _scenery(root: Node2D, feet: Vector2, w: int, h: int, opaque := Rect2i()) -> Sprite2D:
	var s := Sprite2D.new()
	s.texture = _picture(w, h, opaque if opaque.size != Vector2i.ZERO else Rect2i(0, 0, w, h))
	s.centered = false
	s.offset = Vector2(-w / 2.0, -h)
	s.position = feet
	root.add_child(s)
	return s

## An actor 20 x 40 with its feet at `feet`, drawn by a Sprite2D child, in `group`.
func _actor(root: Node2D, feet: Vector2, group := "player") -> Node2D:
	var a := Node2D.new()
	a.add_to_group(group)
	a.position = feet
	var s := Sprite2D.new()
	s.name = "Sprite"
	s.texture = _picture(40, 60, Rect2i(10, 20, 20, 40))   # a drawing with empty margins, as the cast's cells
	s.centered = false
	s.offset = Vector2(-20, -60)
	a.add_child(s)
	root.add_child(a)
	return a

## Waits `n` physics frames and then two drawn ones: `process_frame` fires before the nodes' own _process,
## so only after the second has every node drawn what the last physics step decided.
func _frames(n: int) -> void:
	for i in n:
		await get_tree().physics_frame
	await get_tree().process_frame
	await get_tree().process_frame

func test_a_tall_thing_in_front_ghosts_the_actor() -> void:
	var root := _stage()
	_scenery(root, Vector2(100, 200), 120, 160)            # a wall of leaves over x 40..160, y 40..200
	var hero := _actor(root, Vector2(100, 150))            # feet behind the tree's feet: wholly hidden
	assert_float(_occ(root).hidden_share(hero)).is_equal(1.0)
	await _frames(30)
	assert_bool(_occ(root).is_ghosted(hero)).is_true()
	var ghost := _occ(root).ghost_of(hero)
	assert_object(ghost).is_not_null()
	assert_float(ghost.modulate.a).is_equal_approx(Occlusion.GHOST_ALPHA, 0.01)
	assert_vector(ghost.global_position).is_equal(hero.global_position)
	assert_object(ghost.texture).is_same((hero.get_node("Sprite") as Sprite2D).texture)
	assert_int(ghost.z_index + _occ(root).z_index).is_greater(10)   # drawn over the scenery

func test_in_front_of_it_nothing_shows() -> void:
	var root := _stage()
	_scenery(root, Vector2(100, 200), 120, 160)
	var hero := _actor(root, Vector2(100, 210))            # feet in front of the tree's feet
	assert_float(_occ(root).hidden_share(hero)).is_equal(0.0)
	await _frames(30)
	assert_bool(_occ(root).is_ghosted(hero)).is_false()
	assert_object(_occ(root).ghost_of(hero)).is_null()

func test_a_low_fence_across_the_feet_does_not_count() -> void:
	var root := _stage()
	_scenery(root, Vector2(100, 200), 120, 12)             # y 188..200: the lowest 12 of the body's 40
	var hero := _actor(root, Vector2(100, 198))
	var share := _occ(root).hidden_share(hero)
	assert_float(share).is_greater(0.0)
	assert_float(share).is_less(Occlusion.HIDDEN_SHARE)
	await _frames(30)
	assert_bool(_occ(root).is_ghosted(hero)).is_false()

func test_only_what_is_drawn_hides() -> void:
	# the picture's box covers the actor, but its texels there are clear (a crown's empty corner)
	var root := _stage()
	_scenery(root, Vector2(100, 200), 120, 160, Rect2i(0, 0, 120, 60))   # opaque only over y 40..100
	var hero := _actor(root, Vector2(100, 190))            # body y 150..190: under the clear part
	assert_float(_occ(root).hidden_share(hero)).is_equal(0.0)
	hero.position = Vector2(100, 110)                      # body y 70..110: three quarters under the leaves
	assert_float(_occ(root).hidden_share(hero)).is_between(0.6, 0.9)

func test_the_ground_layer_and_hidden_things_never_hide() -> void:
	var root := _stage()
	var floor_plate := _scenery(root, Vector2(100, 200), 120, 160)
	floor_plate.z_index = -9
	var hero := _actor(root, Vector2(100, 150))
	assert_float(_occ(root).hidden_share(hero)).is_equal(0.0)
	var wall := _scenery(root, Vector2(100, 200), 120, 160)
	assert_float(_occ(root).hidden_share(hero)).is_equal(1.0)
	wall.visible = false                                   # a Conditional that does not hold
	assert_float(_occ(root).hidden_share(hero)).is_equal(0.0)

func test_enemies_are_ghosted_and_bystanders_are_not() -> void:
	var root := _stage()
	_scenery(root, Vector2(100, 200), 120, 160)
	var foe := _actor(root, Vector2(80, 150), "enemy")
	var bystander := _actor(root, Vector2(120, 150), "villager")
	await _frames(30)
	assert_bool(_occ(root).is_ghosted(foe)).is_true()
	assert_bool(_occ(root).is_ghosted(bystander)).is_false()

func test_the_ghost_fades_in_and_goes_when_the_actor_steps_out() -> void:
	# stepped by hand, so a slow frame on a busy machine cannot finish the fade before it is looked at
	var root := _stage()
	_scenery(root, Vector2(100, 200), 120, 160)
	var hero := _actor(root, Vector2(100, 150))
	var occ := _occ(root)
	occ.set_physics_process(false)
	occ.set_process(false)
	occ._physics_process(1.0 / 60.0)
	occ._process(Occlusion.FADE_IN / 3.0)
	var ghost := occ.ghost_of(hero)
	assert_object(ghost).is_not_null()
	assert_float(ghost.modulate.a).is_between(0.05, Occlusion.GHOST_ALPHA - 0.05)   # fading in: never a pop
	occ._process(Occlusion.FADE_IN)
	assert_float(occ.ghost_of(hero).modulate.a).is_equal_approx(Occlusion.GHOST_ALPHA, 0.001)
	hero.position = Vector2(100, 260)                      # out in front
	occ._physics_process(1.0 / 60.0)
	assert_bool(occ.is_ghosted(hero)).is_false()
	occ._process(Occlusion.FADE_OUT / 2.0)
	assert_float(occ.ghost_of(hero).modulate.a).is_less(Occlusion.GHOST_ALPHA)
	occ._process(Occlusion.FADE_OUT)
	assert_object(occ.ghost_of(hero)).is_null()            # finite: nothing left drawn

func test_reduced_motion_shows_it_at_once() -> void:
	SaveGame.data.settings.reduced_motion = true
	var root := _stage()
	_scenery(root, Vector2(100, 200), 120, 160)
	var hero := _actor(root, Vector2(100, 150))
	var occ := _occ(root)
	occ.set_physics_process(false)
	occ.set_process(false)
	occ._physics_process(1.0 / 60.0)
	occ._process(0.001)                                    # one drawn frame, however short
	var ghost := occ.ghost_of(hero)
	assert_object(ghost).is_not_null()
	assert_float(ghost.modulate.a).is_equal_approx(Occlusion.GHOST_ALPHA, 0.001)
	hero.position = Vector2(100, 260)
	occ._physics_process(1.0 / 60.0)
	occ._process(0.001)
	assert_object(occ.ghost_of(hero)).is_null()            # and gone at once

func test_scenery_that_arrives_later_counts() -> void:
	var root := _stage()
	var hero := _actor(root, Vector2(100, 150))
	await _frames(4)
	assert_bool(_occ(root).is_ghosted(hero)).is_false()
	_scenery(root, Vector2(100, 200), 120, 160)            # a camp's den set down after the zone was read
	await _frames(40)
	assert_bool(_occ(root).is_ghosted(hero)).is_true()

func test_scaled_and_flipped_scenery_is_read_where_it_is_drawn() -> void:
	# a picture 60 x 80 whose left half is opaque, drawn at twice its size and flipped: on screen it covers
	# x 40..160, y 40..200 and its right half (x 100..160) is the opaque one
	var root := _stage()
	var s := _scenery(root, Vector2(100, 200), 60, 80, Rect2i(0, 0, 30, 80))
	s.scale = Vector2(2, 2)
	s.flip_h = true
	var hero := _actor(root, Vector2(130, 150))            # body x 120..140: behind the opaque half
	assert_float(_occ(root).hidden_share(hero)).is_equal(1.0)
	hero.position = Vector2(70, 150)                       # body x 60..80: behind the clear half
	assert_float(_occ(root).hidden_share(hero)).is_equal(0.0)
	hero.position = Vector2(100, 150)                      # body x 90..110: half and half
	assert_float(_occ(root).hidden_share(hero)).is_between(0.4, 0.6)

func test_the_share_is_of_the_body_not_of_its_box() -> void:
	# a body that fills only the left half of its drawing's box, half behind a wall: the box is a quarter
	# covered, the body half
	var root := _stage()
	_scenery(root, Vector2(100, 200), 120, 160, Rect2i(0, 80, 120, 80))    # opaque over y 120..200
	var a := Node2D.new()
	a.add_to_group("player")
	a.position = Vector2(100, 140)
	var spr := Sprite2D.new()
	var img := Image.create(40, 60, false, Image.FORMAT_RGBA8)
	img.fill(Color(0, 0, 0, 0))
	img.fill_rect(Rect2i(0, 0, 20, 60), Color.WHITE)       # an L: a full-height left half ...
	img.fill_rect(Rect2i(20, 0, 20, 4), Color.WHITE)       # ... and a cap that makes the box 40 wide
	spr.texture = ImageTexture.create_from_image(img)
	spr.centered = false
	spr.offset = Vector2(-20, -60)
	a.add_child(spr)
	root.add_child(a)
	# the body spans y 80..140; the wall covers y 120..140 of it: a third of the left half, none of the cap
	assert_float(_occ(root).hidden_share(a)).is_equal_approx(20.0 * 20.0 / (20.0 * 60.0 + 20.0 * 4.0), 0.02)

# --- the places found by playing --------------------------------------------------------------
func _enter(zone: String, at: Vector2) -> Player:
	var holder: Node2D = auto_free(Node2D.new())
	add_child(holder)
	var player: Player = auto_free(load("res://actors/player.tscn").instantiate())
	player.input_enabled = false
	Zones.current = null
	Zones.attach(holder, player)
	assert_bool(Zones.go_to(zone, "start")).is_true()
	player.global_position = at
	return player

func test_every_zone_has_one() -> void:
	for zone in ["woodland", "crossroads", "undercroft"]:
		_enter(zone, Vector2.ZERO)
		assert_object(Zones.current.occlusion).is_not_null()
		assert_object(Zones.current.get_node_or_null("Occlusion")).is_same(Zones.current.occlusion)

func test_behind_the_oak_on_the_terrace_road_the_player_shows_through() -> void:
	var player := _enter("crossroads", Vector2(330, 225))  # on the terrace road, under Oak13's crown
	var occ: Occlusion = Zones.current.occlusion
	assert_float(occ.hidden_share(player)).is_greater_equal(0.9)
	await _frames(30)
	assert_bool(occ.is_ghosted(player)).is_true()
	assert_object(occ.ghost_of(player)).is_not_null()
	player.global_position = Vector2(330, 420)             # the lawn south of the tree: in the open
	await _frames(30)
	assert_bool(occ.is_ghosted(player)).is_false()

func test_under_the_willow_the_player_shows_through() -> void:
	var player := _enter("woodland", Vector2(800, 1290))   # the path where it passes behind the willow
	var occ: Occlusion = Zones.current.occlusion
	assert_float(occ.hidden_share(player)).is_greater_equal(Occlusion.HIDDEN_SHARE)
	await _frames(30)
	assert_bool(occ.is_ghosted(player)).is_true()
	player.global_position = Zones.current.spawn_position("start")   # the open meadow
	await _frames(30)
	assert_bool(occ.is_ghosted(player)).is_false()

func test_forty_percent_means_forty_percent_of_the_body() -> void:
	# three spots at the willow's edge, with the share counted on Bramble's 2176 opaque texels against the
	# willow's alpha (audit of #466): 45.6 % and 42.2 % hidden must show the copy, 39.5 % must not. Measured
	# over the body's box it read 40, 36 and 46 %.
	var player := _enter("woodland", Vector2(890, 1290))
	var occ: Occlusion = Zones.current.occlusion
	assert_float(occ.hidden_share(player)).is_equal_approx(0.456, 0.012)
	player.global_position = Vector2(891, 1290)
	assert_float(occ.hidden_share(player)).is_equal_approx(0.422, 0.012)
	assert_float(occ.hidden_share(player)).is_greater_equal(Occlusion.HIDDEN_SHARE)
	player.global_position = Vector2(840, 1290)
	assert_float(occ.hidden_share(player)).is_equal_approx(0.395, 0.012)
	assert_float(occ.hidden_share(player)).is_less(Occlusion.HIDDEN_SHARE)
	# and the running loop, with its quick first pass, decides the same
	occ.set_physics_process(false)
	for spot in [[890, true], [891, true], [840, false]]:
		player.global_position = Vector2(spot[0], 1290)
		occ._physics_process(1.0 / 60.0)
		assert_bool(occ.is_ghosted(player)).override_failure_message("x %d" % spot[0]).is_equal(spot[1])
