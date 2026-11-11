class_name AbilityProjectiles
extends RefCounted
## Pure launch descriptions in CANONICAL planar units. Not world nodes or damage dispatch.
## Call once after contact presentation for a runner release. Resource consumption has already
## happened. Screen muzzle anchors and world conversion belong to the later presentation bridge.

static func plan(id: String, release: Dictionary, origin: Vector2, direction: Vector2,
		aim_point: Vector2, airborne_height: float = 0.0) -> Array[Dictionary]:
	var kit := AbilityCatalogue.kit(id)
	var result: Array[Dictionary] = []
	if kit.is_empty():
		return result
	var powered := bool(release.get("powered_at_release", false))
	var action := str(release.get("action", ""))
	var specs: Array = []
	if action == "primary":
		specs = kit["powered" if powered else "base"].primary_projectiles.duplicate(true)
	elif action == "secondary" and id == "pendle" and not powered:
		var fan: Dictionary = kit.executed_rules.ordinary_secondary
		var rounds := clampi(int(release.get("rounds", 0)), 0, 3)
		for index in rounds:
			specs.append({"kind": "fan-bullet", "speed": fan.speed,
				"angle_offset_radians": float(fan.angle_spacing_radians) * (index - (rounds - 1) / 2.0),
				"planar_spawn_forward": 9.0, "radius": fan.radius,
				"lifetime_seconds": fan.lifetime_seconds, "damage": fan.bullet_damage,
				"pierce_budget": 0, "blast_radius": 0.0})
	elif action == "secondary" and id == "cairn":
		var rock: Dictionary = kit.executed_rules.boulder
		specs.append({"kind": "boulder", "speed": rock.speed, "angle_offset_radians": 0.0,
			"planar_spawn_forward": 9.0, "radius": rock.radius,
			"lifetime_seconds": rock.lifetime_seconds,
			"damage": rock.powered_damage if powered else rock.damage,
			"pierce_budget": rock.pierce_budget,
			"blast_radius": rock.powered_blast_radius if powered else 0.0})
	for spec in specs:
		var angle := direction.angle() + float(spec.angle_offset_radians)
		var forward := Vector2.from_angle(angle)
		var speed := float(spec.speed)
		var seed := float(spec.planar_spawn_forward)
		var remaining: float
		if spec.lifetime_seconds == null:
			# Morel's one dynamic lifetime, from the executed E branch, not eval of data text.
			var flask: Dictionary = kit.executed_rules.flask
			remaining = (clampf(origin.distance_to(aim_point), float(flask.aimed_distance_min),
				float(flask.aimed_distance_max)) - seed) / speed
		else:
			remaining = float(spec.lifetime_seconds)
		result.append({"kind": spec.kind, "owner": "player", "source": id,
			"position": origin + forward * seed, "velocity": forward * speed,
			"radius": float(spec.radius), "remaining": remaining,
			"damage": float(spec.damage), "pierce": int(spec.pierce_budget),
			"blast_radius": float(spec.blast_radius), "powered": powered,
			"launch_height": airborne_height, "age": 0.0,
			"flight_duration": clampf((origin.distance_to(aim_point) - seed) / speed, 0.05, remaining),
			"hit_ids": []})
	return result
