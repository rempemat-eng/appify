class_name CreatureLook
extends Node2D
## The drawn woodland creature for one SliceEnemy (castwork: boarlet, toad, tortoise, thornback):
## a child of the enemy that only reads it (role, state, elapsed, facing, hp, velocity, shot) and
## never changes its behaviour. It hides Codex's placeholder drawing (the enemy's own _draw, via
## self_modulate, which does not reach children), plays the matching clip, draws a soft contact
## shadow, tells each wind-up in the world (no lane, ring or wedge: Matt rejected UI boxes for the
## boss, 26 Oct), dresses the shooter's shot as a thorn seed, and on `died` hands over to a
## FreedCreature that calms and leaves.
##
## The tells, as the Thornback's (bosses/thornback.gd): the body winds up (it squats and leans back,
## then springs), dust kicks back from its feet, a short run of scuffs and pebbles ahead of it points
## the way and reaches further as the tell runs, and one glint at the commit. The toad's aim: its
## throat puffs, its head turns to the target, and a few dust motes rise along the first metre of the
## line. Timings are the enemy's own (windup_time); under reduced motion the body holds still and the
## dust does not flicker, but the marks and the glint still show.
##
## State -> clip: idle -> idle, approach/leash -> move, windup -> telegraph (stretched to the
## role's windup_time), attack -> attack, recover -> stagger; a hit plays hurt (or, during a tell
## or a charge, only a brief flash, so the tell is never cut short).

const LOOKS := {"rusher": "boarlet", "shooter": "toad", "shield": "tortoise", "elite": "thornback"}
## Contact shadow half-widths in texels (the creature's footprint).
const SHADOW := {"boarlet": 22.0, "toad": 21.0, "tortoise": 25.0, "thornback": 32.0}
## Colours from the house ramps, as the Thornback's: the dust (path 4), the scuffs (path 2), the lit
## glint (lamp 4), the toad's throat (its pale belly).
const DUST := Color("#c39771")
const SCUFF := Color("#885c4b")
const LIT := Color("#f5d49c")
const THROAT := Color("#e2d6a4")
const TOAD_EDGE := Color("#2e3a1e")
const GLINT_TIME := 0.12
## Scuff run length at the end of the tell, in world px (the charge's first stride), per role.
const RUN := {"rusher": 26.0, "elite": 34.0, "shield": 14.0}
const SEED := preload("res://assets/enemies/seed.png")

var enemy: SliceEnemy
var sprite: CastSprite
var character := ""
var _hp := 0
var _flash := 0.0
var _hurt := 0.0
var _state := ""
var _glint := 0.0
var tells: Node2D          ## over the sprite: dust puffs, the throat, the motes and the glint

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
	tells = Node2D.new()
	tells.name = "Tells"
	add_child(tells)
	tells.draw.connect(_draw_tells)
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
		if _state == "windup" and enemy.state == "attack":
			_glint = GLINT_TIME
		_state = enemy.state
		if busy:
			_hurt = 0.0
	_glint = maxf(0.0, _glint - delta)
	_pose()
	_hurt = maxf(0.0, _hurt - delta)
	if enemy.state == "windup":
		speed = sprite.duration("telegraph") / enemy.windup_time()
	_play()
	sprite.advance(delta * speed)
	sprite.modulate = Color(1.6, 1.6, 1.6) if _flash > 0.0 else Color.WHITE
	queue_redraw()
	tells.queue_redraw()

## The body's wind-up: it squats and leans back from where it will go as the tell runs (anticipation),
## the toad turns its head to the target; all of it let go at the commit. Still under reduced motion.
func _pose() -> void:
	sprite.scale = Vector2.ONE
	sprite.position = Vector2.ZERO
	sprite.rotation = 0.0
	if enemy.state != "windup" or _reduced():
		return
	var k := _k()
	var f := _aim()
	if enemy.role == "shooter":
		# the head turns to the exact line (the clip only has four facings): a small tilt
		var fc := CastSprite.facing_for(enemy.facing, sprite.facing)
		var base := {"E": 0.0, "S": PI / 2.0, "W": PI, "N": -PI / 2.0}.get(fc, 0.0) as float
		var d := wrapf(f.angle() - base, -PI, PI)
		sprite.rotation = clampf(d, -0.2, 0.2) * minf(1.0, k * 2.0)
		return
	var e := k * k * (3.0 - 2.0 * k)
	sprite.scale = Vector2(1.0 + 0.06 * e, 1.0 - 0.07 * e)
	sprite.position = (-f * 2.0 * e).round()

func _k() -> float:
	return clampf(enemy.elapsed / maxf(enemy.windup_time(), 0.01), 0.0, 1.0)

func _aim() -> Vector2:
	return enemy.facing.normalized() if enemy.facing.length() > 0.01 else Vector2.DOWN

func _reduced() -> bool:
	return bool(SaveGame.setting("reduced_motion", false))

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
	# contact shadow: a soft outer pool and a darker core right under the feet, offset a little
	# east and down (the light is upper left)
	draw_set_transform(Vector2(2, 1), 0.0, Vector2(1.0, 0.36))
	draw_circle(Vector2.ZERO, rx, Color(0.06, 0.08, 0.04, 0.24))
	draw_circle(Vector2.ZERO, rx * 0.7, Color(0.04, 0.05, 0.03, 0.22))
	draw_set_transform(Vector2.ZERO, 0.0, Vector2.ONE)
	if enemy.state == "windup":
		_draw_marks(_k())

## On the floor ahead of it during the wind-up: a short run of scuffs and kicked pebbles from its
## snout, pointing the way and reaching further as the tell runs (its length says when, no box);
## the toad leaves no run (its read is the throat, the head and the motes, over the sprite).
func _draw_marks(k: float) -> void:
	if enemy.role == "shooter":
		return
	var f := _aim()
	var side := f.orthogonal()
	var rx: float = SHADOW.get(character, 16.0)
	# dust kicked back from the hind feet, two puffs a stroke, low on the floor behind it
	var beat := 0 if _reduced() else int(enemy.elapsed / 0.18) % 2
	var heel := -f * rx * 1.05
	for j in 2:
		var puff := heel - f * (5.0 + 7.0 * j + 4.0 * beat) + Vector2(0, -2.0 * j)
		draw_rect(Rect2(_px(puff), Vector2(6 - 3 * j, 3)), Color(DUST, 0.75 - 0.25 * j))
	var snout := f * rx * 1.1
	var reach := float(RUN.get(enemy.role, 24.0)) * SliceEnemy.DENSITY * (0.25 + 0.75 * k)
	var d := 0.0
	var i := 0
	while d < reach:
		var off := side * (float((i * 5) % 3) - 1.0) * 5.0
		draw_line(_px(snout + f * d + off), _px(snout + f * (d + 6.0) + off), Color(SCUFF, 0.85), 3.0)
		if i % 2 == 1:
			draw_rect(Rect2(_px(snout + f * (d + 3.0) - off * 1.6), Vector2(3, 3)), Color(DUST, 0.9))
		d += 10.0
		i += 1

## Over the sprite: dust kicked back from the feet in two puffs a stroke (the toad: its throat
## puffing and dust motes along the first metre of its line), and one glint at the commit.
func _draw_tells() -> void:
	if sprite == null or enemy.dead:
		return
	var f := _aim()
	var fv := CastSprite.facing_vector(sprite.facing)       # where the drawing's head is (four facings)
	var rx: float = SHADOW.get(character, 16.0)
	var head := fv * rx * 0.8 + Vector2(0, -rx * 0.9)
	if enemy.state == "windup":
		var k := _k()
		if enemy.role == "shooter":
			# the throat sac under the jaw swells, outlined in the toad's own dark green, a lit spot on it
			var r := 1.5 + 3.5 * k * (1.0 if _reduced() else 0.85 + 0.15 * absf(sin(enemy.elapsed * 14.0)))
			# under the jaw: ahead of the body side-on, low on its chest facing us, hidden facing away
			if sprite.facing != "N":
				_draw_throat(_px(Vector2(fv.x * rx * 0.95, -rx * (0.45 if fv.y == 0.0 else 0.3))), r)
			var metre := 15.0 * SliceEnemy.DENSITY                  # about a metre: a person is 25 world px
			for j in 4:
				var t := (float(j) + 1.0) / 4.0
				if t > k + 0.15:
					break
				var rise := 0.0 if _reduced() else fmod(enemy.elapsed * 9.0 + float(j) * 3.0, 6.0)
				var mote := f * (rx + metre * t) + side_wobble(f, j) + Vector2(0, -2.0 - rise)
				tells.draw_rect(Rect2(_px(mote), Vector2(3, 3)), Color(DUST, 0.85 - 0.15 * float(j)))
	if _glint > 0.0:
		var a := _glint / GLINT_TIME
		var at := _px(head + Vector2(0, -6))
		for v in [Vector2(9, 0), Vector2(0, 9)]:
			tells.draw_line(at - v, at + v, Color(1, 0.97, 0.9, a), 3.0)

func _draw_throat(at: Vector2, r: float) -> void:
	tells.draw_circle(at, r + 1.0, Color(TOAD_EDGE, 0.9))
	tells.draw_circle(at, r, Color(THROAT, 0.95))
	tells.draw_rect(Rect2(at + Vector2(-r * 0.5, -r * 0.6).round(), Vector2(2, 2)), Color(1, 0.98, 0.9, 0.8))

func side_wobble(f: Vector2, j: int) -> Vector2:
	return f.orthogonal() * (3.0 if j % 2 == 0 else -3.0)

## Snaps a point to the 3-texel world pixel, so the marks sit on the art's grid.
func _px(p: Vector2) -> Vector2:
	return (p / SliceEnemy.DENSITY).round() * SliceEnemy.DENSITY

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
