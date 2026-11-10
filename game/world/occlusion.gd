class_name Occlusion
extends Node2D
## Keeps actors readable behind tall scenery (art-style.md, rule 11, "The companion stays readable"; the app's
## lib/occlusion.ts and its `Ghost`): when one thing drawn in front of an actor hides at least HIDDEN_SHARE of
## its body, a faint copy of the actor (GHOST_ALPHA) is drawn over the scenery. A low fence across the feet
## does not count, because it never hides that much.
##
## Every Zone adds one of these (world/zone.gd), so it works in every zone without scene changes. It follows
## the player and the enemies (GROUPS): the two things a player has to read to play. Villagers and signs do not
## move, so a hidden one is a placement fault, held by test_physics_model.gd instead of being papered over here.
##
## What can hide an actor: a Sprite2D of the zone's scenery that is drawn after it, by z_index or by the y-sort
## (the y of the nearest ancestor that sits in a y-sorted parent). Pictures on the ground layers (z below 0)
## never do. The share is measured on the picture's own alpha, sampled COLS x ROWS over the opaque box of the
## actor's drawing, and the most that any one picture covers counts (as lib/occlusion.ts).
##
## Cost: an actor is measured only when it has moved a texel (or every RECHECK seconds, since a Conditional
## may have shown a cover), against the few pictures registered in its grid cell; a picture's alpha is read
## once, the first time something stands behind it. The ghost fades in over FADE_IN seconds and out over
## FADE_OUT, both at once under reduced motion, and everything stops with the tree when the game is paused.

const HIDDEN_SHARE := 0.4
const GHOST_ALPHA := 0.42
const FADE_IN := 0.18
const FADE_OUT := 0.12
const COLS := 5
const ROWS := 10
const RECHECK := 0.25
const CELL := 192.0                 ## texels a side of the lookup grid
const GHOST_Z := 50                 ## over everything in the world, under the UI's CanvasLayer
const GROUPS: Array[StringName] = [&"player", &"enemy"]

class Cover extends RefCounted:
	var sprite: Sprite2D
	var item: Node2D                ## the node the y-sort orders the picture by
	var rect := Rect2()             ## the picture's box in the world
	var at := Vector2.ZERO          ## where the sprite stood when it was registered (a mover is dropped)
	var z := 0
	var stamp := 0

class Track extends RefCounted:
	var actor: Node2D
	var sprite: Node2D              ## the actor's drawing: an AnimatedSprite2D or a Sprite2D
	var item: Node2D
	var box := Rect2()              ## the opaque box of the drawing, in the sprite's own space
	var boxed := false
	var at := Vector2i(-99999, -99999)
	var wait := 0.0
	var share := 0.0
	var hidden := false
	var ghost: Sprite2D
	var fade := 0.0

var zone: Node2D
var _covers: Array[Cover] = []
var _grid := {}                     ## Vector2i cell -> Array of Cover
var _masks := {}                    ## Texture2D -> BitMap (or null when its image cannot be read)
var _tracks := {}                   ## actor instance id -> Track
var _dirty := true
var _dirty_wait := 0.0
var _stamp := 0

func _ready() -> void:
	name = "Occlusion"
	z_index = GHOST_Z
	if zone == null:
		zone = get_parent() as Node2D
	get_tree().node_added.connect(_on_tree_changed)
	get_tree().node_removed.connect(_on_tree_changed)

func _exit_tree() -> void:
	var tree := get_tree()
	if tree != null:
		if tree.node_added.is_connected(_on_tree_changed):
			tree.node_added.disconnect(_on_tree_changed)
		if tree.node_removed.is_connected(_on_tree_changed):
			tree.node_removed.disconnect(_on_tree_changed)

func _on_tree_changed(node: Node) -> void:
	# scenery that arrives late (a camp's den, the Thornback asleep) or goes; a ghost of ours is not scenery
	if node is Sprite2D and node.get_parent() != self:
		_dirty = true

# --- what the tests and the HUD may ask ------------------------------------------------------
## The share of `actor`'s body that the most covering picture hides, measured now.
func hidden_share(actor: Node2D) -> float:
	_refresh_covers()
	var t := _track(actor)
	return _measure(t) if t != null else 0.0

func is_ghosted(actor: Node2D) -> bool:
	var t: Track = _tracks.get(actor.get_instance_id())
	return t != null and t.hidden

## The faint copy drawn for `actor`, or null while it is not hidden.
func ghost_of(actor: Node2D) -> Sprite2D:
	var t: Track = _tracks.get(actor.get_instance_id())
	return t.ghost if t != null and t.ghost != null and t.ghost.visible else null

func cover_count() -> int:
	_refresh_covers()
	return _covers.size()

# --- the loop --------------------------------------------------------------------------------
func _physics_process(delta: float) -> void:
	if zone == null:
		return
	_dirty_wait = maxf(_dirty_wait - delta, 0.0)
	if _dirty and _dirty_wait <= 0.0:
		_refresh_covers()
		_dirty_wait = RECHECK
		for id in _tracks:
			(_tracks[id] as Track).wait = 0.0
	var seen := {}
	for group in GROUPS:
		for node in get_tree().get_nodes_in_group(group):
			var actor := node as Node2D
			if actor == null or not zone.is_ancestor_of(actor):
				continue
			var t := _track(actor)
			if t == null:
				continue
			seen[actor.get_instance_id()] = true
			var at := Vector2i(actor.global_position.round())
			t.wait -= delta
			if at != t.at or t.wait <= 0.0:
				t.at = at
				t.wait = RECHECK
				t.share = _measure(t)
				t.hidden = t.share >= HIDDEN_SHARE and actor.is_visible_in_tree()
	for id in _tracks.keys():
		if not seen.has(id):
			var gone: Track = _tracks[id]
			if gone.ghost != null and is_instance_valid(gone.ghost):
				gone.ghost.queue_free()
			_tracks.erase(id)

func _process(delta: float) -> void:
	var instant: bool = SaveGame.setting("reduced_motion", false)
	for id in _tracks:
		var t: Track = _tracks[id]
		if not is_instance_valid(t.actor) or not is_instance_valid(t.sprite):
			continue
		if instant:
			t.fade = 1.0 if t.hidden else 0.0
		elif t.hidden:
			t.fade = minf(t.fade + delta / FADE_IN, 1.0)
		else:
			t.fade = maxf(t.fade - delta / FADE_OUT, 0.0)
		if t.fade <= 0.0:
			if t.ghost != null:
				t.ghost.visible = false
			continue
		if t.ghost == null:
			t.ghost = Sprite2D.new()
			t.ghost.name = "Ghost"
			add_child(t.ghost)
		_copy_drawing(t.sprite, t.ghost)
		var ease_out := 1.0 - (1.0 - t.fade) * (1.0 - t.fade)
		var tint: Color = t.sprite.modulate
		t.ghost.modulate = Color(tint.r, tint.g, tint.b, tint.a * GHOST_ALPHA * ease_out)
		t.ghost.visible = t.sprite.is_visible_in_tree()

# --- actors ----------------------------------------------------------------------------------
func _track(actor: Node2D) -> Track:
	var id := actor.get_instance_id()
	var t: Track = _tracks.get(id)
	if t != null and is_instance_valid(t.sprite):
		return t
	var sprite := _drawing_of(actor)
	if sprite == null:
		return null                 # not drawn yet (a creature is dressed a frame after it enters)
	t = Track.new()
	t.actor = actor
	t.sprite = sprite
	t.item = _sort_item(actor)
	_tracks[id] = t
	return t

## The first AnimatedSprite2D or Sprite2D under an actor, breadth first (Player/Sprite, Mossling/Sprite,
## SliceEnemy/Look/Sprite, Thornback/Sprite).
static func _drawing_of(actor: Node) -> Node2D:
	var queue: Array[Node] = [actor]
	while not queue.is_empty():
		var n: Node = queue.pop_front()
		for c in n.get_children():
			if c is AnimatedSprite2D or c is Sprite2D:
				return c
			queue.append(c)
	return null

## The texture and the part of it that a drawing shows now: [texture, region in the texture].
static func _frame_of(sprite: Node2D) -> Array:
	var anim := sprite as AnimatedSprite2D
	if anim != null:
		var frames := anim.sprite_frames
		if frames == null or not frames.has_animation(anim.animation):
			return [null, Rect2()]
		var tex := frames.get_frame_texture(anim.animation, anim.frame)
		return [tex, Rect2(Vector2.ZERO, tex.get_size()) if tex != null else Rect2()]
	var s := sprite as Sprite2D
	if s.texture == null:
		return [null, Rect2()]
	var base := Rect2(Vector2.ZERO, s.texture.get_size())
	if s.region_enabled:
		base = s.region_rect
	var size := base.size / Vector2(s.hframes, s.vframes)
	return [s.texture, Rect2(base.position + Vector2(s.frame_coords) * size, size)]

## Where a drawing's frame sits in the sprite's own space (its offset and centring applied).
static func _frame_origin(sprite: Node2D, size: Vector2) -> Vector2:
	var offset: Vector2 = sprite.get("offset")
	return offset - size / 2.0 if sprite.get("centered") else offset

func _body_box(t: Track) -> Rect2:
	if t.boxed:
		return t.box
	var frame := _frame_of(t.sprite)
	var tex: Texture2D = frame[0]
	var region: Rect2 = frame[1]
	if tex == null:
		return Rect2()
	var used := Rect2(Vector2.ZERO, region.size)
	var img := tex.get_image()
	if img != null and not img.is_empty():
		if img.is_compressed():
			img.decompress()
		var part := Rect2i(region) if img.get_size() != Vector2i(region.size) else Rect2i(Vector2i.ZERO, img.get_size())
		var opaque := img.get_region(part).get_used_rect()
		if opaque.size.x > 0 and opaque.size.y > 0:
			used = Rect2(opaque)
	t.box = Rect2(_frame_origin(t.sprite, region.size) + used.position, used.size)
	t.boxed = true
	return t.box

func _copy_drawing(from: Node2D, to: Sprite2D) -> void:
	if from is AnimatedSprite2D:
		to.texture = _frame_of(from)[0]
	else:
		var s := from as Sprite2D
		to.texture = s.texture
		to.hframes = s.hframes
		to.vframes = s.vframes
		to.frame = s.frame
		to.region_enabled = s.region_enabled
		to.region_rect = s.region_rect
	to.centered = from.get("centered")
	to.offset = from.get("offset")
	to.flip_h = from.get("flip_h")
	to.flip_v = from.get("flip_v")
	to.global_transform = from.global_transform

# --- scenery ---------------------------------------------------------------------------------
## The node the y-sort orders `node` by: itself or its nearest ancestor whose parent is y-sorted.
func _sort_item(node: Node2D) -> Node2D:
	var k: Node = node
	while k != null and k != zone:
		var p := k.get_parent() as CanvasItem
		if p != null and p.y_sort_enabled:
			return k as Node2D
		k = p
	return null

func _z_of(node: CanvasItem) -> int:
	var z := 0
	var k: Node = node
	while k is CanvasItem and k != zone.get_parent():
		z += (k as CanvasItem).z_index
		if not (k as CanvasItem).z_as_relative:
			break
		k = k.get_parent()
	return z

func _refresh_covers() -> void:
	if not _dirty or zone == null:
		return
	_dirty = false
	_covers.clear()
	_grid.clear()
	_gather(zone)

func _gather(node: Node) -> void:
	for c in node.get_children():
		if c == self or c is CharacterBody2D or c is AnimatedSprite2D:
			continue                # ghosts and actors are not scenery
		if c is Sprite2D and c.texture != null:
			_register(c)
		_gather(c)

func _register(sprite: Sprite2D) -> void:
	var z := _z_of(sprite)
	if z < 0:
		return                      # the ground, shadows, floor plates, wall torches: under everyone
	var item := _sort_item(sprite)
	if item == null and z == 0:
		return                      # not in the y-sort: drawn in tree order, never judged here
	var cv := Cover.new()
	cv.sprite = sprite
	cv.item = item
	cv.z = z
	cv.at = sprite.global_position
	cv.rect = sprite.global_transform * sprite.get_rect()
	_covers.append(cv)
	var c0 := Vector2i((cv.rect.position / CELL).floor())
	var c1 := Vector2i((cv.rect.end / CELL).floor())
	for cy in range(c0.y, c1.y + 1):
		for cx in range(c0.x, c1.x + 1):
			var key := Vector2i(cx, cy)
			if not _grid.has(key):
				_grid[key] = []
			_grid[key].append(cv)

func _mask_of(tex: Texture2D) -> BitMap:
	if _masks.has(tex):
		return _masks[tex]
	var bm: BitMap = null
	var img := tex.get_image()
	if img != null and not img.is_empty():
		if img.is_compressed():
			img.decompress()
		bm = BitMap.new()
		bm.create_from_image_alpha(img, 0.5)
	_masks[tex] = bm
	return bm

# --- the measure -----------------------------------------------------------------------------
func _measure(t: Track) -> float:
	if not is_instance_valid(t.sprite) or t.item == null or not is_instance_valid(t.item):
		return 0.0
	var size: Vector2 = _frame_of(t.sprite)[1].size
	var xf: Transform2D = t.sprite.global_transform
	var loose := xf * Rect2(_frame_origin(t.sprite, size), size)
	var near := _near(loose)
	if near.is_empty():
		return 0.0
	var box := xf * _body_box(t)
	if box.size.x <= 0.0 or box.size.y <= 0.0:
		return 0.0
	var z := _z_of(t.actor)
	var y := t.item.global_position.y
	var most := 0
	for cv in near:
		if not is_instance_valid(cv.sprite) or cv.sprite.global_position != cv.at:
			_dirty = true           # it moved or went: scenery stands still
			continue
		if not cv.rect.intersects(box) or not cv.sprite.is_visible_in_tree():
			continue
		var in_front := cv.z > z or (cv.z == z and cv.item != null and cv.item.global_position.y > y)
		if not in_front:
			continue
		most = maxi(most, _covered(cv, box))
		if most >= COLS * ROWS:
			break
	return float(most) / float(COLS * ROWS)

func _near(rect: Rect2) -> Array[Cover]:
	_stamp += 1
	var out: Array[Cover] = []
	var c0 := Vector2i((rect.position / CELL).floor())
	var c1 := Vector2i((rect.end / CELL).floor())
	for cy in range(c0.y, c1.y + 1):
		for cx in range(c0.x, c1.x + 1):
			for cv: Cover in _grid.get(Vector2i(cx, cy), []):
				if cv.stamp != _stamp:
					cv.stamp = _stamp
					if cv.rect.intersects(rect):
						out.append(cv)
	return out

## How many of the COLS x ROWS points of `box` (world) an opaque texel of the cover's picture covers.
func _covered(cv: Cover, box: Rect2) -> int:
	var s := cv.sprite
	var bm := _mask_of(s.texture)
	var base := Vector2.ZERO
	if s.region_enabled:
		base = s.region_rect.position
	var fsize := s.get_rect().size
	var origin := cv.rect.position - (base + Vector2(s.frame_coords) * fsize)   # the texture's (0, 0) in the world
	var n := 0
	for j in ROWS:
		var py := box.position.y + (j + 0.5) * box.size.y / ROWS
		if py < cv.rect.position.y or py >= cv.rect.end.y:
			continue
		for i in COLS:
			var px := box.position.x + (i + 0.5) * box.size.x / COLS
			if px < cv.rect.position.x or px >= cv.rect.end.x:
				continue
			if bm == null or bm.get_bit(int(px - origin.x), int(py - origin.y)):
				n += 1
	return n
