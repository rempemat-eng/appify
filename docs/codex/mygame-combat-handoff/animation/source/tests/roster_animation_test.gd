extends SceneTree
## Runs the delivered SpriteFrames, actor timeline and contact code in Godot.
var passed := 0
var failed := 0
var skipped: Array[String] = []
var yard
var actor
var baseline: Dictionary

func _initialize() -> void:
	call_deferred("_run")

func check(condition:bool,description:String) -> void:
	if condition:
		passed+=1
		print("PASS "+description)
	else:
		failed+=1
		push_error("FAIL "+description)

func camera_state() -> Dictionary:
	return {"position":yard.camera.position,"zoom":yard.camera.zoom,"offset":yard.camera.offset,"rotation":yard.camera.rotation,"canvas":yard.get_viewport().canvas_transform}

func _run() -> void:
	yard=load("res://scenes/animation_yard.tscn").instantiate()
	root.add_child(yard)
	await physics_frame
	await process_frame
	actor=yard.player
	yard.set_physics_process(false)
	actor.set_physics_process(false)
	baseline=camera_state()
	check(yard.camera.position==Vector2(480,270) and yard.camera.offset==Vector2.ZERO and yard.camera.rotation==0,"fixed camera starts at the room centre without offsets")
	check(not yard.camera.position_smoothing_enabled and not yard.camera.rotation_smoothing_enabled,"camera cannot follow or smooth after movement")
	check(ProjectSettings.get_setting("display/window/stretch/scale_mode")=="integer","full viewport retains integer presentation scaling")
	var allow_partial:bool="--allow-partial" in OS.get_cmdline_user_args()
	for index in yard.IDS.size():
		var id:String=yard.IDS[index]
		if not yard.select_character(index):
			if allow_partial:
				skipped.append(id)
				continue
			check(false,"complete frame resource and metadata available: "+id)
			continue
		_test_resources(id)
		_test_all_clips(id)
		_test_events(id)
		_test_primary_contact(id)
		_test_traversal(id)
		_test_powered_review(id)
		check(camera_state()==baseline,"all clips and contacts leave camera fixed: "+id)
	await _test_controls_and_sweeps()
	if skipped.is_empty():
		_test_ability_logic()
		_test_rook_vault()
		_test_showcase()
	print("Roster animation integration: %d passed, %d failed; skipped %s"%[passed,failed,JSON.stringify(skipped)])
	yard.queue_free()
	await process_frame
	quit(1 if failed>0 else 0)

func _test_resources(id:String) -> void:
	var frames:SpriteFrames=actor.sprite.sprite_frames
	var count:=0
	var hashes:Dictionary={}
	var correct_dimensions:=true
	var dimensions:Array=actor.manifest.get("frame_size",[192,192])
	var expected_size:=Vector2(float(dimensions[0]),float(dimensions[1]))
	var all_clips:=true
	for clip in actor.animation_clips():
		all_clips=all_clips and frames.has_animation(clip)
		var expected:=8
		if clip in ["walk","primary"]:expected=16
		if id=="velvet" and clip=="powered_exit":expected=7
		if id=="cairn":
			if clip in ["walk","primary","secondary"]:expected=16
			if clip in ["hit","defeat"]:expected=4
		check(frames.get_frame_count(clip)==expected,"frame count %s/%s = %d"%[id,clip,expected])
		for index in frames.get_frame_count(clip):
			var texture:=frames.get_frame_texture(clip,index)
			if texture==null:
				check(false,"real texture exists: %s/%s/%d"%[id,clip,index])
				continue
			correct_dimensions=correct_dimensions and texture.get_size()==expected_size
			var image:=texture.get_image()
			if image==null or image.is_empty():
				check(false,"real pixels exist: %s/%s/%d"%[id,clip,index])
				continue
			var context:=HashingContext.new()
			context.start(HashingContext.HASH_SHA256)
			context.update(image.get_data())
			hashes[context.finish().hex_encode()]=true
			count+=1
	var expected_total:=160 if id=="pendle" else (151 if id=="velvet" else 152)
	check(all_clips and count==expected_total,"all base, traversal and powered clips and total pose count exist: "+id)
	check(hashes.size()==count,"each imported pose contains distinct image data: "+id)
	check(correct_dimensions and actor.sprite.texture_filter==CanvasItem.TEXTURE_FILTER_NEAREST,"fixed canvas and nearest filtering: "+id)

func _test_all_clips(id:String) -> void:
	for clip in actor.animation_clips():
		actor.play_study(clip)
		actor.study_loop=false
		actor.event_count=0
		var origin:Vector2=actor.position
		var first:int=actor.sprite.frame
		var elapsed:=0.0
		var every_frame:=true
		for index in actor.sprite.sprite_frames.get_frame_count(clip):
			var duration:float=actor.frame_duration(clip,index)
			var midpoint:=elapsed+duration*0.5
			actor.step(midpoint-actor.clock)
			every_frame=every_frame and actor.sprite.frame==index
			elapsed+=duration
		var advanced:bool=actor.sprite.frame!=first
		check(every_frame,"timeline visits every authored frame in order: %s/%s"%[id,clip])
		actor.step(actor.duration()*2.0)
		check(advanced and actor.sprite.frame==actor.sprite.sprite_frames.get_frame_count(clip)-1 and actor.finished,"authored drawing advance and final settle: %s/%s"%[id,clip])
		check(actor.position==origin and actor.event_count==0 and actor.action.is_empty(),"pose-only review cannot move or damage: %s/%s"%[id,clip])
	# Defeat holds the authored final drawing until a new request.
	actor.play_study("defeat")
	actor.study_loop=false
	actor.step(actor.duration()+0.1)
	var settled:int=actor.sprite.frame
	actor.step(3.0)
	check(actor.clip=="defeat" and actor.sprite.frame==settled,"defeat remains settled rather than restarting: "+id)

func _test_events(id:String) -> void:
	for clip in ["primary","secondary","special"]:
		yard.reset_room()
		actor.enter_practice()
		actor.use_demo_move=true
		actor.position=Vector2(370,360)
		check(actor.start_action(clip),"manual action starts: %s/%s"%[id,clip])
		var release:float=actor.release_time(clip)
		actor.step(release-0.001)
		check(actor.event_count==0 and not actor.released,"no event occurs during anticipation: %s/%s"%[id,clip])
		actor.step(0.002)
		var wanted_frame:int=int(actor.manifest.clips[clip].release_frame)
		check(actor.event_count==1 and actor.released and actor.sprite.frame==wanted_frame,"single event aligns with committed drawing: %s/%s"%[id,clip])
		actor.step(actor.duration(clip)+1.0)
		actor.step(1.0)
		if actor.action=="reload":_advance_actor(actor.duration("reload")+0.1)
		check(actor.event_count==1 and actor.action.is_empty(),"completed action cannot release twice: %s/%s"%[id,clip])
		yard.advance_effects(10.0)
		check(yard.projectiles.is_empty() and yard.particles.is_empty() and yard.impacts.is_empty() and yard.marks.is_empty(),"action effects expire: %s/%s"%[id,clip])
		if clip=="special":
			check(actor.powered_mode,"special equipment persists after activation recovery: "+id)
			check(actor.start_action("special"),"E can start the powered return: "+id)
			actor.step(actor.duration("powered_exit")+0.01)
			check(not actor.powered_mode and yard.special_props.is_empty(),"powered equipment props clear after the authored return: "+id)

func _test_primary_contact(id:String) -> void:
	yard.reset_room()
	yard._enter_practice()
	actor.use_demo_move=true
	actor.start_action("primary")
	actor.step(actor.release_time("primary")+0.001)
	for _index in range(90):yard.advance_effects(1.0/60.0)
	check(yard.targets[0].hits>0,"primary reaches the real forward practice target: "+id)
	check(yard.targets[1].hits==0,"primary leaves off-lane practice prop untouched: "+id)
	yard.reset_room()
	actor.enter_practice()
	actor.use_demo_move=true
	actor.position=Vector2(450,350)
	yard.blockers.append(Rect2(490,260,20,130))
	actor.start_action("primary")
	actor.step(actor.release_time("primary")+0.001)
	for _index in range(35):yard.advance_effects(1.0/60.0)
	check(yard.targets[0].hits==0 and yard.wall_hits>0,"solid blocker wins over a target behind it: "+id)
	yard.blockers.pop_back()

func _advance_actor(seconds:float) -> void:
	var remaining:=seconds
	while remaining>0.000001:
		var slice:=minf(remaining,1.0/120.0)
		actor.step(slice)
		yard.advance_effects(slice)
		remaining-=slice

func _test_traversal(id:String) -> void:
	yard.terrain_mode=false
	yard.reset_room()
	actor.enter_practice()
	actor.position=Vector2(200,350)
	actor.reset_traversal()
	actor.use_demo_move=true
	check(actor.start_jump(),"grounded jump starts with authored anticipation: "+id)
	check(not actor.start_action("primary") and not actor.start_jump(),"airborne action and repeated jump cannot bypass recovery: "+id)
	var peak:=0.0
	var shadow_stays_grounded:=true
	for _i in range(130):
		actor.step(1.0/120.0)
		peak=maxf(peak,actor.jump_height)
		shadow_stays_grounded=shadow_stays_grounded and actor.position==Vector2(200,350) and is_equal_approx(actor.ground_height,0.0)
		shadow_stays_grounded=shadow_stays_grounded and (actor.global_position+actor.sprite.position+actor.foot_pivot).is_equal_approx(actor.visual_foot().round())
	check(peak>30 and shadow_stays_grounded,"jump changes visual height while retaining the ground footprint: "+id)
	check(actor.landing_count==1 and actor.traversal_state.is_empty() and actor.jump_height==0,"jump lands exactly once and finishes recovery: "+id)
	check(actor.event_count==0,"traversal poses cannot cause ability releases: "+id)
	check(actor.start_dodge(),"authored dodge can start grounded: "+id)
	_advance_actor(actor.duration("dodge")+0.1)
	check(actor.position.x>220 and actor.traversal_state.is_empty(),"dodge moves through collision then settles: "+id)
	yard.terrain_mode=true
	yard.reset_room()
	actor.enter_practice()
	actor.position=Vector2(210,280)
	actor.reset_traversal()
	actor.use_demo_move=true
	actor.demo_move=Vector2.RIGHT
	var saw_up:=false
	var saw_down:=false
	var saw_top:=false
	var continuous:=true
	var previous_height:float=actor.ground_height
	for _i in range(800):
		actor.step(1.0/120.0)
		saw_up=saw_up or actor.clip=="stair_up"
		saw_down=saw_down or actor.clip=="stair_down"
		saw_top=saw_top or is_equal_approx(actor.ground_height,32.0)
		continuous=continuous and absf(actor.ground_height-previous_height)<1.0
		continuous=continuous and (actor.global_position+actor.sprite.position+actor.foot_pivot).is_equal_approx(actor.visual_foot().round())
		previous_height=actor.ground_height
		if actor.position.x>595:break
	check(saw_up and saw_down and saw_top and continuous,"both stair clips follow a continuous32pixel elevation profile: "+id)
	actor.demo_move=Vector2.ZERO
	actor.position=Vector2(350,318)
	actor.reset_traversal()
	actor.demo_move=Vector2.UP
	_advance_actor(0.4)
	check(actor.position.y>=307 and actor.ground_height==0,"a tall stair side cannot be entered as a walkable tread: "+id)
	actor.demo_move=Vector2.ZERO
	actor.position=Vector2(618,280)
	actor.reset_traversal()
	actor.demo_move=Vector2.RIGHT
	_advance_actor(0.3)
	check(actor.position.x<630 and actor.ground_height==0,"a16pixel ledge rejects walking through its side: "+id)
	actor.position=Vector2(618,280)
	actor.reset_traversal()
	check(actor.start_jump(),"ledge jump starts: "+id)
	_advance_actor(1.1)
	check(actor.ground_height==16 and actor.jump_height==0,"jump can land on an elevated ledge with feet registered: "+id)
	var saw_drop:=false
	for _i in range(110):
		actor.step(1.0/120.0)
		saw_drop=saw_drop or actor.traversal_state=="fall"
	check(saw_drop and actor.ground_height==0 and actor.jump_height==0,"walking off a ledge falls and lands instead of snapping down: "+id)
	actor.position=Vector2(350,400)
	actor.reset_traversal()
	actor.demo_move=Vector2.RIGHT
	var bridge_safe:=true
	for _i in range(170):
		actor.step(1.0/120.0)
		bridge_safe=bridge_safe and actor.grounded() and actor.jump_height==0
	check(bridge_safe and actor.position.x>470,"bridge supports the footprint over the gap: "+id)
	actor.position=Vector2(385,365)
	actor.reset_traversal()
	actor.demo_move=Vector2.DOWN
	_advance_actor(1.0)
	check(actor.position.distance_to(yard.terrain_checkpoint)<1 and actor.grounded(),"a missed gap landing returns to the traversal checkpoint: "+id)
	check(yard.sample_floor(Vector2(550,400)).surface=="water" and yard.sample_floor(Vector2(170,400)).surface=="mud" and yard.sample_floor(Vector2(700,400)).surface=="ice","surface fixture tags are distinct: "+id)
	yard.terrain_mode=false
	yard.reset_room()

func _test_powered_review(id:String) -> void:
	yard.reset_room()
	actor.enter_practice()
	actor.use_demo_move=true
	actor.start_action("special")
	_advance_actor(actor.duration("special")+0.03)
	check(actor.powered_mode and actor.clip=="powered_idle","activation reaches the held powered idle: "+id)
	check(not actor.start_jump() and not actor.start_dodge(),"uncovered powered traversal is rejected instead of dropping equipment: "+id)
	var position_before:Vector2=actor.position
	actor.demo_move=Vector2.RIGHT
	_advance_actor(0.2)
	check(actor.clip=="powered_walk" and actor.position.x>position_before.x,"powered walk moves on the flat without dropping equipment: "+id)
	actor.demo_move=Vector2.ZERO
	actor.guard_override=true
	_advance_actor(0.6)
	check(actor.clip=="powered_guard" and actor.sprite.frame==actor.guard_hold_frame(),"powered guard retains changed equipment at its brace: "+id)
	actor.guard_override=false
	_advance_actor(0.02)
	check(actor.start_action("primary") and actor.clip=="powered_primary","powered primary uses its own authored action: "+id)
	_advance_actor(actor.duration("powered_primary")+0.03)
	check(actor.powered_mode and actor.clip=="powered_idle","powered strike recovers to the same equipment: "+id)
	if id=="rook":check(yard.special_props.size()==2,"exactly two Rook turret entities persist throughout powered review")
	if id=="mote":check(yard.orbital_shards.size()==3 and yard.orbital_shards.all(func(shard):return not shard is CollisionObject2D),"Mote orbit shards are separate bounded visual entities without invented damage")
	actor.start_action("special")
	_advance_actor(actor.duration("powered_exit")+0.02)
	check(not actor.powered_mode and actor.clip=="idle" and yard.special_props.is_empty() and yard.orbital_shards.is_empty(),"authored powered return restores the base and clears summoned entities: "+id)

func _test_ability_logic() -> void:
	yard.terrain_mode=false
	yard.select_character(yard.IDS.find("nix"))
	yard.reset_room()

	actor.enter_practice()
	actor.position=Vector2(300,350)
	actor.reset_traversal()
	actor.use_demo_move=true
	actor.start_action("secondary")
	var activation:Vector2=actor.activation_origin
	actor.position+=Vector2(20,0)
	actor.step(actor.release_time("secondary")+0.01)
	check(yard.decoy_origin==activation,"Afterimage remains at activation even if the actor moved before release")
	yard.select_character(yard.IDS.find("brine"))
	yard.reset_room()
	actor.enter_practice()
	actor.use_demo_move=true
	actor.start_action("secondary")
	_advance_actor(actor.duration("secondary")+0.02)
	check(yard.hit_total==0 and yard.impacts.is_empty(),"reel without an attached harpoon creates no invented gun-butt attack")
	yard.reset_room()
	yard._enter_practice()
	actor.use_demo_move=true
	actor.start_action("primary")
	_advance_actor(actor.duration("primary")+0.4)
	check(yard.tether_time>0 and yard.tether_target==0,"a harpoon hit records the actual attached target")
	yard._spawn_projectile("harpoon",Vector2(300,275),Vector2.RIGHT,10,Color.WHITE)
	check(yard.tether_time==0 and yard.tether_target==-1,"firing a new harpoon releases the previous tether")
	yard.select_character(yard.IDS.find("iona"))
	yard.reset_room()
	actor.enter_practice()
	actor.use_demo_move=true
	var spear_data:Dictionary=actor.manifest.clips.secondary
	var spear_reach:float=float(spear_data.get("contact_reach",yard.DEFINITIONS.iona.reach))
	var spear_anchor:Array=spear_data.get("release_anchor",[76,-61])
	var spear_face:=542.0 if float(spear_anchor[1])<=-50.0 else 556.0
	actor.position=Vector2(spear_face-spear_reach-20.0,350)
	actor.reset_traversal()
	actor.start_action("secondary")
	actor.step(actor.release_time("secondary")+0.001)
	check(yard.targets[0].hits==0,"lunge cannot hit a target beyond the current spear contact at release")
	_advance_actor(0.2)
	check(yard.targets[0].hits==1,"moving lunge hits its reached target once")
	yard.reset_room()
	actor.enter_practice()
	actor.use_demo_move=true
	actor.position=Vector2(spear_face-spear_reach-20.0,350)
	actor.reset_traversal()
	actor.start_action("secondary")
	actor.step(actor.release_time("secondary")+0.001)
	actor.guard_override=true
	_advance_actor(0.25)
	check(yard.targets[0].hits==0 and yard.lunge_time==0 and actor.dash_time==0,"guard cancellation stops pending lunge motion and contact")
	yard.select_character(yard.IDS.find("pendle"))
	yard.reset_room()
	actor.enter_practice()
	actor.use_demo_move=true
	yard.weapon_ammo=1
	actor.start_action("primary")
	_advance_actor(actor.duration("primary")+0.01)
	check(yard.weapon_ammo==0 and actor.action=="reload" and actor.clip=="reload","empty revolver starts an authored reload after shot recovery")
	_advance_actor(actor.duration("reload")*0.5)
	check(yard.weapon_ammo==0,"revolver ammo stays empty while the cylinder is being reloaded")
	_advance_actor(actor.duration("reload")*0.6)
	check(yard.weapon_ammo==6 and actor.action.is_empty(),"revolver refills only after reload closes")
	actor.start_action("special")
	_advance_actor(actor.duration("special")+0.02)
	var ammo_before:int=yard.weapon_ammo
	actor.start_action("primary")
	actor.step(actor.release_time("powered_primary")+0.01)
	check(yard.projectiles.any(func(p):return p.kind=="rifle") and yard.weapon_ammo==ammo_before,"Longshot fires the drawn rifle without consuming revolver ammunition")
	yard.select_character(0)
	yard.reset_room()
	actor.enter_practice()
	actor.position=Vector2(200,350)
	actor.reset_traversal()
	actor.use_demo_move=true
	actor.demo_move=Vector2.RIGHT
	actor.speed_scale=1.0
	_advance_actor(0.5)
	var full_distance:float=actor.position.x-200
	actor.position=Vector2(200,350)
	actor.reset_traversal()
	actor.speed_scale=0.5
	_advance_actor(0.5)
	var half_distance:float=actor.position.x-200
	check(absf(full_distance-half_distance*2.0)<0.2,"half speed scales displacement and animation by the same simulation time")
	actor.speed_scale=1.0
	yard.reset_room()

func _test_rook_vault() -> void:
	yard.terrain_mode=false
	yard.select_character(yard.IDS.find("rook"))
	yard.reset_room()
	actor.enter_practice()
	actor.position=Vector2(200,350)
	actor.reset_traversal()
	actor.use_demo_move=true
	actor.start_action("secondary")
	actor.step(actor.release_time("secondary")+0.001)
	check(actor.traversal_is_ability and actor.clip=="secondary" and not actor.grounded(),"Thruster Vault launches the same physical height state while retaining its authored clip")
	check(not actor.start_action("primary") and not actor.start_jump(),"Thruster Vault rejects attacks and jumps until supported recovery")
	var peak:=0.0
	for _i in range(110):
		actor.step(1.0/120.0)
		peak=maxf(peak,actor.jump_height)
	check(peak>20 and actor.landing_count==1 and actor.action.is_empty(),"Thruster Vault has one physical arc and one landing rather than a baked double lift")
	check(absf(actor.position.x-260.0)<3,"Thruster Vault covers the declared0.5second motion at120pixels persecond")
	yard.terrain_mode=true
	yard.reset_room()
	actor.enter_practice()
	actor.position=Vector2(618,300)
	actor.reset_traversal()
	actor.use_demo_move=true
	actor.start_action("secondary")
	_advance_actor(1.3)
	check(actor.ground_height==16 and actor.jump_height==0 and actor.landing_count==1,"Thruster Vault lands on the16pixel ledge and holds contact until supported")
	yard.reset_room()
	actor.enter_practice()
	actor.position=Vector2(350,380)
	actor.reset_traversal()
	actor.use_demo_move=true
	actor.start_action("secondary")
	_advance_actor(1.7)
	check(actor.position.distance_to(yard.terrain_checkpoint)<1 and actor.grounded() and actor.action.is_empty(),"a gap wider than Thruster Vault reach causes a real unsupported fall and checkpoint return")
	yard.terrain_mode=false
	yard.reset_room()

func _test_showcase() -> void:
	yard.reset_room()
	yard.traversal_showcase=true
	yard.showcase=false
	yard._toggle_demo()
	var visited:Dictionary={}
	var course_done:=false
	for _i in range(7200):
		yard._run_demo(1.0/60.0)
		actor.step(1.0/60.0)
		yard.advance_effects(1.0/60.0)
		if yard.traversal_showcase_phase>=10:
			course_done=true
			visited[actor.character_id]=true
		if yard.traversal_showcase_done:break
	check(course_done and visited.size()==14 and yard.traversal_showcase_done,"the actual-physics showcase completes the course and all fourteen powered reviews")
	check(camera_state()==baseline,"the entire traversal and powered showcase keeps the camera fixed")
	yard.traversal_showcase=false
	yard.terrain_mode=false
	yard.reset_room()

func _test_controls_and_sweeps() -> void:
	var first:=-1
	for index in yard.IDS.size():
		if yard.select_character(index):
			first=index
			break
	if first<0:
		check(false,"at least one complete actor is available for control tests")
		return
	actor.enter_practice()
	actor.use_demo_move=true
	actor.guard_override=true
	actor.step(actor.duration("guard")*2.0)
	check(actor.guarded and actor.sprite.frame==actor.guard_hold_frame(),"held guard holds the authored brace rather than playing recovery")
	check(not actor.start_action("primary"),"held guard rejects an attack")
	actor.guard_override=false
	actor.step(0.02)
	check(not actor.guarded and actor.clip=="idle","releasing guard restores idle")
	actor.start_action("primary")
	actor.queue_action("secondary")
	actor.step(0.2)
	actor.step(2.0)
	actor.step(0.1)
	check(actor.queued_action.is_empty() and actor.event_count==1,"early queued input expires instead of firing long after recovery")
	yard.reset_room()
	actor.play_study("primary")
	actor.step(0.2)
	yard.paused=true
	actor.pose_paused=true
	var original_count:int=actor.event_count
	var before:int=actor.sprite.frame
	actor.step_pose(1)
	actor.step(3.0)
	check(actor.sprite.frame==before+1 and actor.event_count==original_count,"paused pose stepping is exact and emits no gameplay event")
	actor.step_pose(-1)
	check(actor.sprite.frame==before,"paused pose stepping reverses exactly")
	yard.reset_room()
	actor.enter_practice()
	actor.use_demo_move=true
	actor.demo_move=Vector2.RIGHT
	actor.queue_action("secondary")
	yard._notification(yard.NOTIFICATION_WM_WINDOW_FOCUS_OUT)
	var position_before:Vector2=actor.position
	actor.step(1.0)
	check(yard.focus_paused and actor.suspended and actor.position==position_before and actor.queued_action.is_empty(),"window focus loss suspends movement and clears queued controls")
	yard._notification(yard.NOTIFICATION_WM_WINDOW_FOCUS_IN)
	check(not yard.focus_paused and not actor.suspended and actor.demo_move==Vector2.ZERO,"window focus return cannot restore stale movement")
	yard._notification(yard.NOTIFICATION_APPLICATION_FOCUS_OUT)
	yard._notification(yard.NOTIFICATION_APPLICATION_FOCUS_IN)
	check(not yard.focus_paused and not actor.suspended,"desktop application-focus pair is also supported")
	yard.reset_room()
	yard._spawn_projectile("arrow",Vector2(300,310),Vector2.RIGHT,2000,Color.WHITE)
	yard._step_projectiles(0.3)
	check(yard.targets[0].hits==1 and yard.projectiles.is_empty(),"a fast projectile sweeps through its entire travelled segment")
	yard.reset_room()
	yard.blockers.append(Rect2(430,240,20,150))
	yard._spawn_projectile("arrow",Vector2(300,310),Vector2.RIGHT,2000,Color.WHITE)
	yard._step_projectiles(0.3)
	check(yard.targets[0].hits==0 and yard.wall_hits==1,"a continuous sweep selects the wall before a later target")
	yard.blockers.pop_back()
	yard.reset_room()
	for _index in range(80):
		yard._spawn_projectile("glass",Vector2(200,310),Vector2.RIGHT,10,Color.WHITE)
		yard._add_mark(Vector2(200,350),"crack",Color.WHITE,1.0)
		yard._add_impact(Vector2(200,310),Color.WHITE,"contact",1.0)
		yard._emit_particles(Vector2(200,310),10,Color.WHITE,false)
	check(yard.projectiles.size()<=yard.MAX_PROJECTILES and yard.particles.size()<=yard.MAX_PARTICLES and yard.marks.size()<=yard.MAX_MARKS and yard.impacts.size()<=yard.MAX_IMPACTS,"effects and projectile budgets hold after repeated attacks")
	yard.reset_room()
	check(yard.projectiles.is_empty() and yard.marks.is_empty() and yard.hit_total==0 and actor.event_count==0,"reset restores the actor, counters and practice world")
	check(camera_state()==baseline,"inspection, focus, sweeps and reset never move the camera")
	await physics_frame
	await process_frame
