class_name CampDen
extends LoopFx
## The woodland camp's bramble den and its shard-lit clumps (castwork/src/den.py): the shards in the
## weave glow while the camp's creatures are shardstruck; once the camp is cleared the shards are
## gone and a few flowers show. Decorative only (no collisions, rewards or saves).

const DEN := "den"
const CLUMP := "clump"
## Foot pivot inside each cropped drawing (den.py CROPS).
const PIVOT := {"den": Vector2(56, 52), "clump": Vector2(24, 26)}

var kind := DEN
var camp: Camp

func _ready() -> void:
	centered = false
	offset = -PIVOT[kind]
	fps = 6.0
	var calm := camp == null or not is_instance_valid(camp) or camp.is_cleared()
	_set_look(calm)
	if not calm:
		camp.cleared.connect(func() -> void: _set_look(true))
	super._ready()

func _set_look(calm: bool) -> void:
	texture = load("res://assets/enemies/%s_%s.png" % [kind, "calm" if calm else "lit"])
	hframes = 1 if calm else 3
	frame = 0
