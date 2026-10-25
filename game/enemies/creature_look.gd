class_name CreatureLook
extends Node2D
## The drawn woodland creature for one SliceEnemy (castwork: boarlet, toad, tortoise, thornback):
## a child of the enemy that only reads it (role, state, elapsed, facing, hp, velocity, shot) and
## never changes its behaviour. It hides Codex's placeholder drawing (the enemy's own _draw, via
## self_modulate, which does not reach children), plays the matching clip, draws a soft contact
## shadow and the ground tell in the one reserved telegraph colour, dresses the shooter's shot as a
## thorn seed, and on `died` hands over to a FreedCreature that calms and leaves.
##
## State -> clip: idle -> idle, approach/leash -> move, windup -> telegraph (stretched to the
## role's windup_time), attack -> attack, recover -> stagger; a hit plays hurt (or, during a tell
## or a charge, only a brief flash, so the tell is never cut short).

const LOOKS := {"rusher": "boarlet", "shooter": "toad", "shield": "tortoise", "elite": "thornback"}
## Contact shadow half-widths in texels (the creature's footprint).
const SHADOW := {"boarlet": 22.0, "toad": 21.0, "tortoise": 25.0, "thornback": 32.0}
## The reserved telegraph colour (game-design 4.4), as Codex's placeholder marks used it.
const TELL := Color(1.0, 0.65, 0.15)
const SEED := preload("res://assets/enemies/seed.png")

var enemy: SliceEnemy
var sprite: CastSprite
var character := ""
var _hp := 0
var _flash := 0.0
var _hurt := 0.0
var _state := ""

func _ready() -> void:
	enemy = get_parent() as SliceEnemy
	if enemy == null:
		queue_free()
		return
	character = String(LOOKS.get(enemy.role, "boarlet"))
	sprite = CastSprite.new()
	sprite.name = "Sprite"
	add_child(sprite)
	if not sprite.load_character(character):
		sprite.queue_free()
		sprite = null
		return
	enemy.self_modulate = Color(1, 1, 1, 0)   # the placeholder silhouette and marks
	_hp = enemy.hp
	enemy.died.connect(_on_died)
	enemy.released.connect(_on_released)
	_play()

func _process(delta: float) -> void:
	if sprite == null or enemy.dead:
		return
	var busy := enemy.state == "windup" or enemy.state == "attack"
	if enemy.hp < _hp:
		if busy:
			_flash = 0.12
		else:
			_hurt = sprite.duration("hurt")
	_hp = enemy.hp
	_flash = maxf(0.0, _flash - delta)
	var speed := 1.0
	if enemy.state != _state:
		_state = enemy.state
		if busy:
			_hurt = 0.0
	_hurt = maxf(0.0, _hurt - delta)
	if enemy.state == "windup":
		speed = sprite.duration("telegraph") / enemy.windup_time()
	_play()
	sprite.advance(delta * speed)
	sprite.modulate = Color(1.6, 1.6, 1.6) if _flash > 0.0 else Color.WHITE
	queue_redraw()

## The clip and facing for the enemy's current state.
func clip_for_state() -> Array:
	var fc := CastSprite.facing_for(enemy.facing, sprite.facing)
	if _hurt > 0.0:
		return ["hurt", sprite.facing]
	match enemy.state:
		"approach":
			if enemy.velocity.length() < 1.0:
				return ["idle", fc]
			return ["move", fc]
		"leash":
			return ["move", CastSprite.facing_for(enemy.velocity, fc)]
		"windup":
			return ["telegraph", fc]
		"attack":
			return ["attack", fc]
		"recover":
			return ["stagger", fc]
	return ["idle", fc]

func _play() -> void:
	var c := clip_for_state()
	var restart: bool = c[0] != sprite.clip and not bool(sprite.clip_info(c[0]).loop)
	sprite.play_clip(c[0], c[1], restart)

func _draw() -> void:
	if sprite == null or enemy.dead:
		return
	var rx: float = SHADOW.get(character, 16.0)
	draw_set_transform(Vector2.ZERO, 0.0, Vector2(1.0, 0.36))
	draw_circle(Vector2.ZERO, rx, Color(0.06, 0.08, 0.04, 0.32))
	draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
	if enemy.state == "windup":
		_draw_tell(clampf(enemy.elapsed / enemy.windup_time(), 0.0, 1.0))

## The ground mark of the wind-up, one shape per attack kind (lane for a charge, ring for the
## stomp, a narrow sighting wedge for the spit). It fills as the tell runs and brightens once,
## solidly, for the last part before the commit; no blinking.
func _draw_tell(p: float) -> void:
	var f := enemy.facing.normalized() if enemy.facing.length() > 0.01 else Vector2.DOWN
	var side := f.orthogonal()
	var a := 0.85 if p >= 0.8 else 0.45
	var edge := Color(TELL, a)
	var fill := Color(TELL, a * 0.35)
	match enemy.role:
		"shield":
			var r := 22.0 * SliceEnemy.DENSITY
			draw_set_transform(Vector2.ZERO, 0.0, Vector2(1.0, 0.5))
			draw_circle(Vector2.ZERO, r * p, fill)
			draw_arc(Vector2.ZERO, r, 0.0, TAU, 40, edge, 2.0)
			draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
		"shooter":
			# a short sighting wedge at its feet (not an aim line: the read is the toad's pose and the
			# glint at its lips)
			var length := 16.0 * SliceEnemy.DENSITY
			var w := 9.0
			var base := f * 10.0
			var tip := base + f * length * (0.4 + 0.6 * p)
			draw_colored_polygon(PackedVector2Array([base + side * 3.0, tip + side * w, tip - side * w, base - side * 3.0]), Color(TELL, a * 0.6))
		_:
			var length := 125.0 * SliceEnemy.DENSITY * 0.18 + 20.0
			var w: float = float(SHADOW.get(character, 16.0)) * 0.8
			var lane := PackedVector2Array([side * w, side * w + f * length, -side * w + f * length, -side * w])
			draw_colored_polygon(PackedVector2Array([side * w, side * w + f * length * p, -side * w + f * length * p, -side * w]), fill)
			draw_polyline(lane + PackedVector2Array([lane[0]]), edge, 1.0)

func _on_released() -> void:
	if enemy.role != "shooter" or not is_instance_valid(enemy.shot):
		return
	enemy.shot.self_modulate = Color(1, 1, 1, 0)   # the placeholder dot
	var s := Sprite2D.new()
	s.texture = SEED
	s.hframes = 2
	s.rotation = enemy.shot.direction.angle()
	s.position = Vector2(0, -6)
	enemy.shot.add_child(s)

func _on_died() -> void:
	if sprite == null:
		return
	var freed := FreedCreature.new()
	freed.character = character
	freed.facing = sprite.facing
	var player := get_tree().get_first_node_in_group("player") as Node2D
	var away := -enemy.facing
	if player != null:
		away = player.global_position.direction_to(enemy.global_position)
	freed.away = away if away.length() > 0.01 else Vector2.DOWN
	freed.position = enemy.position
	enemy.get_parent().add_child.call_deferred(freed)
	visible = false
