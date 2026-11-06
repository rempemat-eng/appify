class_name AbilitySpritePresenter
extends RefCounted
## Applies an exact runner drawing, without play_clip/advance or art-template clocks.
## No aim easing, turn interpolation, mirroring, damage, or projectile dispatch here.

static func show_drawing(sprite: CastSprite, sample: Dictionary) -> bool:
	if not is_instance_valid(sprite) or sprite.sprite_frames == null:
		return false
	var clip := str(sample.get("clip", ""))
	var facing := str(sample.get("facing", ""))
	var aim := str(sample.get("aim", ""))
	var index: Variant = sample.get("index")
	if not (index is int or index is float) or not is_finite(float(index)) or index != floor(float(index)) or index < 0:
		return false
	var info: Variant = sprite.manifest.get("clips", {}).get(clip)
	if not info is Dictionary:
		return false
	var selected: Variant = info.get("facings", {}).get(facing)
	if not selected is Dictionary:
		return false
	if aim != "":
		selected = selected.get("aims", {}).get(aim)
		if not selected is Dictionary:
			return false
	var frames: Variant = selected.get("frames")
	var animation := "%s_%s" % [clip, facing]
	if aim != "": animation += "_" + aim
	if not frames is Array or index >= frames.size() or frames[int(index)] != sample.get("frame"):
		return false
	if not sprite.sprite_frames.has_animation(animation) or sprite.sprite_frames.get_frame_count(animation) != frames.size():
		return false # no facing/aim fallback and no clamping a missing drawing
	var start: Variant = sample.get("starts_at")
	if not (start is int or start is float) or not is_finite(float(start)) or start < 0:
		return false
	# Keep CastSprite.anchor() consistent with the exact drawing on both contracts.
	# V2 fields are optional so the existing C60 base remains independently testable.
	sprite.stop()
	sprite.clip = clip
	sprite.facing = facing
	sprite.frame_index = int(index)
	sprite.clip_time = float(start)
	sprite.finished = false
	for property in ["playing", "shown_facing", "aim_tag", "turn_path"]:
		if property in sprite:
			match property:
				"playing": sprite.set(property, clip)
				"shown_facing": sprite.set(property, facing)
				"aim_tag": sprite.set(property, aim)
				"turn_path": sprite.get(property).clear()
	sprite.flip_h = false
	sprite.flip_v = false
	sprite.animation = animation
	sprite.set_frame_and_progress(int(index), 0.0)
	return true
