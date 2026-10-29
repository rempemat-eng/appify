extends Node2D
## Base-pose review and an isolated effects yard, never the main game's simulation.

const ActorScript = preload("res://scripts/roster_actor.gd")
const IDS := ["bramble", "morel", "velvet", "cairn", "iona", "tam", "brine", "pendle", "mirra", "ashe", "clack", "nix", "rook", "mote"]
const CLIPS := ["idle", "walk", "primary", "secondary", "special", "guard", "hit", "defeat", "jump", "stair_up", "stair_down", "dodge", "powered_idle", "powered_walk", "powered_primary", "powered_guard", "powered_exit"]
const PAPER := Color("e9dfc8")
const MOSS := Color("9ab58c")
const INK := Color("1a2d2d")
const BOUNDS := Rect2(76, 205, 808, 231)
const MAX_PROJECTILES := 24
const MAX_PARTICLES := 140
const MAX_IMPACTS := 32
const MAX_MARKS := 16
const DEFINITIONS := {
	"bramble": {"name":"Bramble", "primary":"arrow", "secondary":"billhook", "color":"c0c792", "reach":85.0, "hand":Vector2(44,-66),"secondary_hand":Vector2(64,-50)},
	"morel": {"name":"Morel", "primary":"flask", "secondary":"catalyst", "color":"c9b675", "reach":80.0, "hand":Vector2(44,-62)},
	"velvet": {"name":"Velvet", "primary":"sabre", "secondary":"lantern", "color":"c3bbdd", "reach":54.0, "hand":Vector2(36,-51),"secondary_hand":Vector2(-15,-47)},
	"cairn": {"name":"Cairn", "primary":"slam", "secondary":"boulder", "color":"b8bd99", "reach":86.0, "hand":Vector2(68,-3),"secondary_hand":Vector2(80,-72)},
	"iona": {"name":"Iona", "primary":"spear", "secondary":"lunge", "color":"c8dfd5", "reach":94.0, "hand":Vector2(76,-61)},
	"tam": {"name":"Tam", "primary":"palm", "secondary":"ridge", "color":"b4d5db", "reach":66.0, "hand":Vector2(47,-67)},
	"brine": {"name":"Brine", "primary":"harpoon", "secondary":"reel", "color":"a3c9bc", "reach":76.0, "hand":Vector2(68,-75)},
	"pendle": {"name":"Pendle", "primary":"bullet", "secondary":"fan", "color":"ddbc89", "reach":80.0, "hand":Vector2(56,-69)},
	"mirra": {"name":"Mirra", "primary":"water", "secondary":"seal", "color":"91d5d5", "reach":80.0, "hand":Vector2(40,-62)},
	"ashe": {"name":"Ashe", "primary":"sword", "secondary":"thrust", "color":"e8ad75", "reach":111.0, "hand":Vector2(93,-87)},
	"clack": {"name":"Clack", "primary":"rocket", "secondary":"vent", "color":"d1bd94", "reach":94.0, "hand":Vector2(42,-77)},
	"nix": {"name":"Nix", "primary":"beam", "secondary":"decoy", "color":"87e1d1", "reach":80.0, "hand":Vector2(34,-60)},
	"rook": {"name":"Rook", "primary":"carbine", "secondary":"vault", "color":"e4b88a", "reach":80.0, "hand":Vector2(55,-61)},
	"mote": {"name":"Mote", "primary":"glass", "secondary":"gravity", "color":"b8c7e3", "reach":80.0, "hand":Vector2(38,-61)}
}

var player: RosterStudyActor
var camera: Camera2D
var actors: Node2D
var selected := 0
var loaded_count := 0
var projectiles: Array[Dictionary] = []
var particles: Array[Dictionary] = []
var impacts: Array[Dictionary] = []
var marks: Array[Dictionary] = []
var targets: Array[Dictionary] = []
var blockers: Array[Rect2] = [Rect2(785, 240, 38, 150)]
var special_props: Array[Node2D] = []
var orbital_shards: Array[Node2D] = []
var orbit_clock := 0.0
var decoy: Sprite2D
var decoy_time := 0.0
var decoy_origin := Vector2.ZERO
var decoy_cooldown := 0.0
var tether_time := 0.0
var tether_point := Vector2.ZERO
var hit_total := 0
var wall_hits := 0
var quiet := true
var paused := false
var focus_paused := false
var inspector_open := false
var auto_demo := false
var demo_clock := 0.0
var demo_character := -1
var demo_clip := -1
var demo_events := 0
var demo_clip_age := 0.0
var showcase := false
var showcase_phase := 0
var traversal_showcase := false
var traversal_showcase_phase := -1
var traversal_showcase_done := false
var tick_clock := 0.0
var message_clock := 0.0
var weapon_ammo := 6
var weapon_reload := 0.0
var selector: OptionButton
var status: Label
var detail: Label
var notice: Label
var pause_button: Button
var loop_button: Button
var practice_button: Button
var speed_button: Button
var demo_button: Button
var clip_buttons: Dictionary = {}
var inspector: PanelContainer
var inspect_image: TextureRect
var inspect_label: Label
var ground: Node2D
var foreground: Node2D
var rng := RandomNumberGenerator.new()
var terrain_mode := false
var terrain_button: Button
var terrain_checkpoint := Vector2(150,300)
var lunge_time := 0.0
var lunge_hits: Dictionary = {}
var tether_target := -1
const PIT := Rect2(360,372,110,54)
const BRIDGE := Rect2(360,389,110,22)
const WATER := Rect2(518,365,95,64)
const MUD := Rect2(132,367,95,62)
const ICE := Rect2(673,366,78,63)

class PracticeProp extends Node2D:
	var kind := "wood"
	var hits := 0
	var hit_time := 0.0
	var exposed := 0.0
	var broken := false
	func _draw() -> void:
		draw_colored_polygon(PackedVector2Array([Vector2(-27,-3),Vector2(-17,-8),Vector2(17,-8),Vector2(27,-3),Vector2(17,4),Vector2(-17,4)]),Color(0.07,0.12,0.11,0.4))
		var recoil := Vector2(roundf(sin(hit_time*35.0)*minf(4.0,hit_time*24.0)),0)
		draw_set_transform(recoil)
		if kind == "crate":
			if broken:
				for i in range(5):
					draw_rect(Rect2(-25+i*11,-8-(i%2)*3,16,4),Color("8c7154"))
				return
			draw_rect(Rect2(-24,-44,48,42),Color("4b4939"))
			for i in range(5):
				draw_rect(Rect2(-22+i*9,-42,8,38),Color("a68c60") if i%2 else Color("92744f"))
			draw_line(Vector2(-20,-37),Vector2(19,-9),Color("c1a77b"),4)
			draw_rect(Rect2(-24,-43,48,5),Color("c8ad7a"))
			draw_rect(Rect2(-24,-7,48,5),Color("66553e"))
		else:
			draw_line(Vector2(-16,-3),Vector2(16,-3),Color("624d39"),5)
			draw_rect(Rect2(-4,-56,8,54),Color("856747"))
			draw_rect(Rect2(-18,-90,36,40),Color("51473a"))
			draw_rect(Rect2(-16,-88,32,36),Color("b39768"))
			for i in range(3):
				draw_rect(Rect2(-14+i*10,-86,8,32),Color("c6aa79") if i%2 else Color("b49a6b"))
			draw_rect(Rect2(-11,-83,22,24),Color("6b5846"))
			draw_rect(Rect2(-8,-80,16,18),Color("cbb384"))
			draw_rect(Rect2(-4,-76,8,10),Color("594b3d"))
			if hit_time>0.10:
				draw_rect(Rect2(-16,-88,32,2),Color("e3d2aa"))
			if exposed>0.0:
				draw_rect(Rect2(-20,-92,40,44),Color("c7b5dd"),false,1)

class EffectsLayer extends Node2D:
	var yard: Node2D
	func _draw() -> void:
		yard.draw_effects(self)

class GroundLayer extends Node2D:
	var yard: Node2D
	func _draw() -> void:
		yard.draw_ground(self)

class ProjectileView extends Node2D:
	var yard: Node2D
	var projectile: Dictionary
	func _draw() -> void:
		yard.draw_projectile(self,projectile)

class TurretView extends Node2D:
	func _draw() -> void:
		draw_rect(Rect2(-10,-4,20,4),Color("2d4547"))
		draw_rect(Rect2(-7,-17,14,13),Color("bcb7a2"))
		draw_rect(Rect2(-5,-20,10,7),Color("e1d2ac"))
		draw_rect(Rect2(3,-17,13,4),Color("e0ac73"))
		draw_rect(Rect2(13,-16,3,2),Color("f3dec0"))

class OrbitShardView extends Node2D:
	var spin := 0.0
	func _draw() -> void:
		draw_set_transform(Vector2(0,-46),spin)
		draw_colored_polygon(PackedVector2Array([Vector2(7,0),Vector2(-3,-4),Vector2(-5,3)]),Color("b8c7e3"))
		draw_line(Vector2(-2,-2),Vector2(5,0),Color("e3e7d2"),1)

func _ready() -> void:
	_setup_input()
	rng.seed=8140
	camera=$Camera2D
	actors=$Actors
	ground=GroundLayer.new()
	ground.yard=self
	add_child(ground)
	move_child(ground,0)
	player=ActorScript.new()
	player.name="ReviewActor"
	player.position=Vector2(360,350)
	actors.add_child(player)
	player.action_released.connect(_on_release)
	player.action_finished.connect(_on_action_finished)
	player.action_cancelled.connect(_on_action_cancelled)
	player.footfall.connect(_on_footfall)
	player.landed.connect(_on_landing)
	player.void_fall.connect(_on_void_fall)
	player.floor_sampler = sample_floor
	foreground=EffectsLayer.new()
	foreground.yard=self
	foreground.z_index=5
	add_child(foreground)
	_build_boundaries()
	_build_targets()
	_build_ui()
	refresh_availability()
	select_character(0)
	if "--traversal-showcase" in OS.get_cmdline_user_args():
		traversal_showcase=true
		_toggle_demo()
	elif "--showcase" in OS.get_cmdline_user_args():
		showcase=true
		_toggle_demo()
	elif "--demo" in OS.get_cmdline_user_args():
		_toggle_demo()
	queue_redraw()

func sample_floor(point:Vector2) -> Dictionary:
	var result:={"height":0.0,"support":true,"surface":"stone","stairs":false,"terrain":terrain_mode}
	if not terrain_mode:return result
	if point.y>=241 and point.y<=307:
		if point.x>=216 and point.x<312:
			result.height=(point.x-216.0)/3.0
			result.stairs=true
		elif point.x>=312 and point.x<=488:result.height=32.0
		elif point.x>488 and point.x<=584:
			result.height=(584.0-point.x)/3.0
			result.stairs=true
	if Rect2(630,240,82,67).has_point(point):result.height=16.0
	if PIT.has_point(point) and not BRIDGE.has_point(point):
		result.support=false
		result.surface="void"
	elif BRIDGE.has_point(point):result.surface="wood"
	elif WATER.has_point(point):result.surface="water"
	elif MUD.has_point(point):result.surface="mud"
	elif ICE.has_point(point):result.surface="ice"
	return result

func _toggle_terrain() -> void:
	if player.powered_mode:
		_show_notice("E returns the equipment to base before traversal practice.")
		return
	terrain_mode=not terrain_mode
	reset_room()
	_enter_practice()
	player.position=terrain_checkpoint if terrain_mode else Vector2(300,350)
	player.reset_traversal()
	queue_redraw()
	_show_notice("Traversal: K jump, Shift dodge. Stairs rise continuously; bridge, ledge and surface contacts are test fixtures." if terrain_mode else "Target practice restored.")

func _on_footfall(point:Vector2) -> void:
	match player.surface:
		"water":_add_impact(point,Color("a1cdd2"),"ripple",0.45)
		"ice":_emit_particles(point,2,Color("c0d7da"),false)
		"wood":_emit_particles(point,2,Color("b39c70"),true)
		"mud":_emit_particles(point,3,Color("6d6851"),false)
		_:_emit_particles(point,3,Color("9caa86"),false)

func _on_landing(point:Vector2,surface:String) -> void:
	if surface=="water":_add_impact(point,Color("a1cdd2"),"ripple",0.55)
	else:_emit_particles(point,5,Color("a8ad92"),surface=="wood")

func _on_void_fall() -> void:
	_clear_effects()
	player.clear_controls()
	player.action=""
	player.position=terrain_checkpoint
	player.reset_traversal()
	player.enter_practice()
	_show_notice("Returned to the traversal checkpoint after a missed landing.")

func _setup_input() -> void:
	var bindings:={"r_left":[KEY_A,KEY_LEFT],"r_right":[KEY_D,KEY_RIGHT],"r_up":[KEY_W,KEY_UP],"r_down":[KEY_S,KEY_DOWN],"r_guard":[KEY_SPACE]}
	for key in bindings:
		if not InputMap.has_action(key):InputMap.add_action(key)
		for code in bindings[key]:
			var event:=InputEventKey.new()
			event.physical_keycode=code
			if not InputMap.action_has_event(key,event):InputMap.action_add_event(key,event)

func _build_boundaries() -> void:
	var rectangles:=[Rect2(40,130,880,75),Rect2(40,436,880,30),Rect2(40,130,36,330),Rect2(884,130,36,330)]
	rectangles.append_array(blockers)
	for rect in rectangles:
		var body:=StaticBody2D.new()
		body.position=rect.get_center()
		body.collision_layer=1
		body.collision_mask=2
		var shape:=CollisionShape2D.new()
		var rectangle:=RectangleShape2D.new()
		rectangle.size=rect.size
		shape.shape=rectangle
		body.add_child(shape)
		add_child(body)

func _build_targets() -> void:
	for entry in [[Vector2(560,350),"wood"],[Vector2(650,420),"crate"]]:
		var node:=PracticeProp.new()
		node.kind=entry[1]
		node.position=entry[0]
		actors.add_child(node)
		var target:={"position":entry[0],"kind":entry[1],"hits":0,"health":100,"restore":0.0,"node":node}
		var body:=StaticBody2D.new()
		body.collision_layer=1
		body.collision_mask=2
		var shape:=CollisionShape2D.new()
		var footprint:=RectangleShape2D.new()
		footprint.size=Vector2(44,12) if entry[1]=="crate" else Vector2(24,12)
		shape.position=Vector2(0,-5)
		shape.shape=footprint
		body.add_child(shape)
		node.add_child(body)
		target.collision=shape
		targets.append(target)

func _label(parent:Node,text:String,at:Vector2,size:int,color:Color=PAPER)->Label:
	var label:=Label.new()
	label.text=text
	label.position=at
	label.add_theme_font_size_override("font_size",size)
	label.modulate=color
	label.mouse_filter=Control.MOUSE_FILTER_IGNORE
	parent.add_child(label)
	return label

func _button(parent:Node,text:String,at:Vector2,size:Vector2,callback:Callable)->Button:
	var button:=Button.new()
	button.text=text
	button.position=at
	button.size=size
	button.focus_mode=Control.FOCUS_NONE
	button.add_theme_font_size_override("font_size",11)
	var style:=StyleBoxFlat.new()
	style.bg_color=Color("2d4541")
	style.border_color=Color("5e7969")
	style.set_border_width_all(1)
	style.set_content_margin_all(4)
	button.add_theme_stylebox_override("normal",style)
	button.pressed.connect(callback)
	parent.add_child(button)
	return button

func _build_ui() -> void:
	var canvas:=CanvasLayer.new()
	add_child(canvas)
	_label(canvas,"MYGAME / MOTION STUDIO",Vector2(30,14),22)
	_label(canvas,"Authored base clips / east view / fixed camera",Vector2(31,43),11,Color("a6b8a7"))
	terrain_button=_button(canvas,"T  TERRAIN COURSE",Vector2(380,20),Vector2(176,26),_toggle_terrain)
	_button(canvas,"[",Vector2(607,17),Vector2(30,28),func():select_character(selected-1))
	selector=OptionButton.new()
	selector.position=Vector2(643,17)
	selector.size=Vector2(232,28)
	selector.focus_mode=Control.FOCUS_NONE
	selector.add_theme_font_size_override("font_size",13)
	for id in IDS:selector.add_item(DEFINITIONS[id].name)
	selector.item_selected.connect(select_character)
	canvas.add_child(selector)
	_button(canvas,"]",Vector2(881,17),Vector2(30,28),func():select_character(selected+1))
	for index in CLIPS.size():
		var name:String=CLIPS[index]
		var title:String=name.to_upper().replace("POWERED_","PWR ").replace("STAIR_","STAIR ")
		if index<8:title="%d %s"%[index+1,title]
		clip_buttons[name]=_button(canvas,title,Vector2(30+(index%9)*99,72+(index/9)*30),Vector2(94,27),func():choose_clip(name))
	clip_buttons["reload"]=_button(canvas,"RELOAD",Vector2(822,102),Vector2(94,27),func():choose_clip("reload"))
	var status_back:=ColorRect.new()
	status_back.position=Vector2(24,130)
	status_back.size=Vector2(912,21)
	status_back.color=Color("172c2a")
	status_back.mouse_filter=Control.MOUSE_FILTER_IGNORE
	canvas.add_child(status_back)
	status=_label(canvas,"",Vector2(31,132),13,MOSS)
	detail=_label(canvas,"",Vector2(542,133),11,Color("a6b8a7"))
	notice=_label(canvas,"",Vector2(31,448),11,Color("d0c8ad"))
	practice_button=_button(canvas,"B  TARGET PRACTICE",Vector2(30,472),Vector2(170,27),_toggle_practice)
	pause_button=_button(canvas,"P  PAUSE",Vector2(207,472),Vector2(91,27),_toggle_pause)
	_button(canvas,",",Vector2(305,472),Vector2(29,27),func():_step_pose(-1))
	_button(canvas,".",Vector2(339,472),Vector2(29,27),func():_step_pose(1))
	speed_button=_button(canvas,"V  1x",Vector2(375,472),Vector2(77,27),_toggle_speed)
	loop_button=_button(canvas,"LOOP ON",Vector2(459,472),Vector2(93,27),_toggle_loop)
	_button(canvas,"C  INSPECT",Vector2(559,472),Vector2(102,27),_toggle_inspector)
	demo_button=_button(canvas,"TAB  ROSTER DEMO",Vector2(668,472),Vector2(155,27),_toggle_demo)
	_button(canvas,"R  RESET",Vector2(830,472),Vector2(81,27),reset_room)
	_label(canvas,"WASD move   J primary   Q secondary   E powered review / exit   SPACE brace   K jump   SHIFT dodge",Vector2(31,511),11,PAPER)
	_label(canvas,"1-8 studies   [ / ] character   T terrain   H hit   L defeat   M quiet effects   F fullscreen",Vector2(31,525),10,Color("91a792"))
	inspector=PanelContainer.new()
	inspector.position=Vector2(548,104)
	inspector.size=Vector2(384,358)
	var panel_style:=StyleBoxFlat.new()
	panel_style.bg_color=Color("172c2a")
	panel_style.border_color=Color("657f66")
	panel_style.set_border_width_all(1)
	inspector.add_theme_stylebox_override("panel",panel_style)
	var content:=Control.new()
	content.custom_minimum_size=Vector2(384,358)
	inspector.add_child(content)
	inspect_image=TextureRect.new()
	inspect_image.position=Vector2(0,-40)
	inspect_image.size=Vector2(384,384)
	inspect_image.texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
	inspect_image.expand_mode=TextureRect.EXPAND_IGNORE_SIZE
	inspect_image.stretch_mode=TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	content.add_child(inspect_image)
	inspect_label=_label(content,"",Vector2(16,314),12,PAPER)
	inspector.visible=false
	canvas.add_child(inspector)

func refresh_availability() -> int:
	loaded_count=0
	for id in IDS:
		if ResourceLoader.exists("res://assets/animated/%s/frames.tres"%id) and FileAccess.file_exists("res://assets/animated/%s/manifest.json"%id):loaded_count+=1
	return loaded_count

func select_character(index:int) -> bool:
	if not is_instance_valid(player):return false
	selected=posmod(index,IDS.size())
	_clear_effects()
	paused=false
	focus_paused=false
	player.suspended=false
	player.pose_paused=false
	player.position=Vector2(360,350)
	var result:=player.load_character(IDS[selected])
	if is_instance_valid(selector):selector.select(selected)
	if clip_buttons.has("reload"):clip_buttons.reload.disabled=IDS[selected]!="pendle"
	weapon_ammo=6
	weapon_reload=0.0
	_reset_targets()
	if result:
		_show_notice("Select a clip, or J/Q/E for practice. K jumps; Shift dodges; T opens the terrain course.")
	else:
		_show_notice("Animation assets unavailable for %s."%DEFINITIONS[IDS[selected]].name)
	return result

func choose_clip(name:String) -> void:
	if not player.available:return
	auto_demo=false
	_clear_effects()
	player.pose_paused=false
	paused=false
	player.position=Vector2(360,350)
	player.play_study(name)
	player.study_loop=name in ["idle","walk","stair_up","stair_down","powered_idle","powered_walk"]
	_show_notice("Clip study. Damage and projectile events are disabled while reviewing poses.")

func _enter_practice() -> void:
	if not player.available:return
	if player.study_mode:
		player.enter_practice()
		var melee:bool=DEFINITIONS[player.character_id].primary in ["sabre","slam","spear","palm","sword"]
		var anchor:Vector2=_release_anchor(player.character_id,"primary",DEFINITIONS[player.character_id].hand)
		var target_face:=542.0 if anchor.y<=-50.0 else 556.0
		var contact_x:float=target_face-anchor.x
		player.position=Vector2(contact_x if melee else 300,350)
		_clear_effects()
	paused=false
	player.pose_paused=false

func _toggle_practice() -> void:
	auto_demo=false
	if player.study_mode:
		_enter_practice()
		_show_notice("Target practice uses real contacts. East is the authored review view.")
	else:
		choose_clip("idle")

func _toggle_pause() -> void:
	paused=not paused
	player.pose_paused=paused
	player.clear_controls()

func _step_pose(direction:int) -> void:
	if not player.available:return
	auto_demo=false
	paused=true
	_clear_effects()
	player.clear_controls()
	player.step_pose(direction)

func _toggle_speed() -> void:
	player.speed_scale=0.5 if player.speed_scale>0.5 else 1.0

func _toggle_loop() -> void:
	player.study_loop=not player.study_loop

func _toggle_inspector() -> void:
	inspector_open=not inspector_open
	inspector.visible=inspector_open

func _show_notice(message:String) -> void:
	if is_instance_valid(notice):notice.text=message
	message_clock=5.0

func _process(delta:float) -> void:
	if not is_instance_valid(player) or not is_instance_valid(status):return
	message_clock=maxf(0.0,message_clock-delta)
	notice.modulate.a=minf(1.0,message_clock*2.0)
	var id:String=IDS[selected]
	var mode:="POSE STUDY" if player.study_mode else "TARGET PRACTICE"
	if terrain_mode and not player.study_mode:mode="TERRAIN COURSE"
	if player.powered_mode:mode="HELD POWERED REVIEW"
	status.text="%s / %s / %s"%[DEFINITIONS[id].name.to_upper(),mode,"PAUSED" if paused or focus_paused else player.phase]
	if player.available:
		detail.text="%s  %02d / %02d    %02d HITS    %d / 14 LOADED"%[player.clip.to_upper(),player.sprite.frame+1,player.sprite.sprite_frames.get_frame_count(player.clip),hit_total,loaded_count]
		if inspector_open:
			inspect_image.texture=player.sprite.sprite_frames.get_frame_texture(player.clip,player.sprite.frame)
			var source_size:Vector2=inspect_image.texture.get_size()
			var integer_scale:=1.0 if source_size.x>192.0 else 2.0
			inspect_image.size=source_size*integer_scale
			inspect_image.position=Vector2((384.0-inspect_image.size.x)/2.0,80 if integer_scale==1.0 else -40)
			inspect_label.text="%s / %s / %02d / %.0fx\n%.0f ms   P pause   , / . step"%[DEFINITIONS[id].name,player.clip,player.sprite.frame+1,integer_scale,player.clock*1000.0]
	else:
		detail.text="ASSETS UNAVAILABLE / %d OF 14 LOADED"%loaded_count
	pause_button.text="P  RESUME" if paused else "P  PAUSE"
	practice_button.text="B  POSE STUDY" if not player.study_mode else "B  TARGET PRACTICE"
	speed_button.text="V  %.1fx"%player.speed_scale
	loop_button.text="LOOP ON" if player.study_loop else "LOOP OFF"
	demo_button.text="TAB  STOP DEMO" if auto_demo else "TAB  ROSTER DEMO"
	terrain_button.text="T  RETURN TO TARGETS" if terrain_mode else "T  TERRAIN COURSE"
	ground.queue_redraw()
	foreground.queue_redraw()
	tick_clock+=delta
	if OS.has_feature("web") and tick_clock>=0.08:
		tick_clock=0.0
		var snapshot:={"id":id,"selected":selected,"count":IDS.size(),"loaded":loaded_count,"available":player.available,"clip":player.clip,"frame":player.sprite.frame if player.available else -1,"frame_count":player.sprite.sprite_frames.get_frame_count(player.clip) if player.available else 0,"state":player.action,"phase":player.phase,"clock":player.clock,"x":player.position.x,"y":player.position.y,"events":player.event_count,"hits":hit_total,"target_hits":targets.map(func(t):return t.hits),"wall_hits":wall_hits,"projectiles":projectiles.size(),"particles":particles.size(),"marks":marks.size(),"study":player.study_mode,"paused":paused,"focus":focus_paused,"loop":player.study_loop,"speed":player.speed_scale,"inspector":inspector_open,"demo":auto_demo,"demo_clock":demo_clock,"decoy":decoy_time,"decoy_origin":[decoy_origin.x,decoy_origin.y],"turrets":special_props.size(),"camera_x":camera.position.x,"camera_y":camera.position.y,"camera_zoom":[camera.zoom.x,camera.zoom.y],"camera_offset":[camera.offset.x,camera.offset.y],"camera_rotation":camera.rotation}
		snapshot.merge({"clips_count":player.animation_clips().size(),"terrain":terrain_mode,"ground_height":player.ground_height,"jump_height":player.jump_height,"render_height":player.render_height,"grounded":player.grounded(),"traversal":player.traversal_state,"landings":player.landing_count,"surface":player.surface,"blocked_step":player.blocked_step,"powered":player.powered_mode,"ammo":weapon_ammo,"reload":weapon_reload,"tether":tether_time,"tether_target":tether_target,"lunge":lunge_time,"orbit_shards":orbital_shards.size(),"shadow_position":[roundf(player.position.x),roundf(player.position.y-player.ground_height)],"shadow_scale":1.0-clampf(player.shadow_lift()/95.0,0.0,0.5)})
		JavaScriptBridge.eval("window.rosterStudy="+JSON.stringify(snapshot)+";",true)

func _physics_process(delta:float) -> void:
	if not is_instance_valid(player) or focus_paused or paused:return
	var dt:=delta*player.speed_scale
	if auto_demo:_run_demo(dt)
	advance_effects(dt)

func advance_effects(dt:float) -> void:
	_step_projectiles(dt)
	if lunge_time>0:
		lunge_time=maxf(0.0,lunge_time-dt)
		_melee(player.visual_foot(),float(DEFINITIONS[player.character_id].reach),Color(DEFINITIONS[player.character_id].color),"spear",true)
	if not orbital_shards.is_empty():
		orbit_clock+=dt
		for index in range(orbital_shards.size()):
			var angle:=orbit_clock*1.7+index*TAU/float(orbital_shards.size())
			var node:Node2D=orbital_shards[index]
			node.position=(player.visual_foot()+Vector2(cos(angle)*37,sin(angle)*12)).round()
			node.spin=angle
			node.queue_redraw()
	decoy_cooldown=maxf(0.0,decoy_cooldown-dt)
	decoy_time=maxf(0.0,decoy_time-dt)
	tether_time=maxf(0.0,tether_time-dt)
	if tether_time<=0.0:tether_target=-1
	if tether_target>=0 and (tether_target>=targets.size() or int(targets[tether_target].health)<=0):
		tether_time=0.0
		tether_target=-1
	if is_instance_valid(decoy):
		decoy.modulate.a=minf(0.52,decoy_time*2.0)
		if decoy_time<=0.0:decoy.queue_free()
	if weapon_reload>0.0:
		if player.action=="reload":weapon_reload=maxf(0.001,player.duration("reload")-player.clock)
		elif player.action.is_empty() and not player.guarded and not player.study_mode:player.start_reload()
	for target in targets:
		var node:PracticeProp=target.node
		node.hit_time=maxf(0.0,node.hit_time-dt)
		node.exposed=maxf(0.0,node.exposed-dt)
		if target.health<=0:
			target.restore+=dt
			if target.restore>2.5:
				target.health=100
				target.restore=0.0
				node.broken=false
		target.collision.set_deferred("disabled",target.health<=0 and target.kind=="crate")
		node.queue_redraw()
	for group in [particles,impacts,marks]:
		for index in range(group.size()-1,-1,-1):
			var item:Dictionary=group[index]
			item.life-=dt
			if item.has("velocity"):
				item.position+=item.velocity*dt
				item.velocity.y+=65.0*dt
			if item.life<=0.0:group.remove_at(index)

func _on_release(id:String,kind:String,origin:Vector2,direction:Vector2) -> void:
	if player.study_mode:return
	var definition:Dictionary=DEFINITIONS[id]
	var color:=Color(definition.color)
	var fallback:Vector2=definition.get("secondary_hand",definition.hand) if kind=="secondary" else definition.hand
	var hand:Vector2=origin+_release_anchor(id,player.clip,fallback)
	if kind=="primary":
		if id=="pendle" and player.powered_mode:
			_spawn_projectile("rifle",hand,direction,660.0,color)
			return
		match definition.primary:
			"sabre","slam","spear","palm","sword":_melee(origin,float(definition.reach),color,definition.primary)
			"beam":_beam(hand,direction,color)
			"glass":
				for spread in [-0.10,0.0,0.10]:_spawn_projectile("glass",hand,direction.rotated(spread),340.0,color)
			"bullet":
				if weapon_ammo>0 and weapon_reload<=0.0:
					weapon_ammo-=1
					_spawn_projectile("bullet",hand,direction,660.0,color)
					if weapon_ammo==0:weapon_reload=player.duration("reload")
				else:_show_notice("Pendle is reloading the six-round revolver.")
			_:
				var speeds:={"arrow":430.0,"flask":285.0,"harpoon":410.0,"water":325.0,"rocket":280.0,"carbine":620.0}
				_spawn_projectile(definition.primary,hand,direction,float(speeds.get(definition.primary,350.0)),color)
	elif kind=="secondary":
		match definition.secondary:
			"billhook":_melee(origin,92.0,color,"billhook")
			"catalyst":
				var found:=false
				for mark in marks:
					if mark.kind=="reagent":
						_area_hit(mark.position,65,color)
						mark.life=0.0
						found=true
				if not found:_show_notice("Catalyst needs a flask reagent mark to reactivate.")
			"lantern":
				_add_impact(hand,color,"lantern",0.45)
				for target in targets:
					if target.position.distance_to(origin)<130.0 and _first_wall_t(origin+Vector2(0,-42),target.position+Vector2(0,-42),0.0)>1.0:target.node.exposed=1.4
			"boulder":_spawn_projectile("boulder",hand,direction,350.0,color)
			"lunge":
				player.dash(190.0,0.18)
				lunge_time=0.18
				lunge_hits.clear()
			"ridge":
				_add_mark(origin+Vector2(110,-3),"ridge",color,1.25)
				for index in range(targets.size()):
					var target:Dictionary=targets[index]
					if target.position.x>origin.x and target.position.x<origin.x+230 and absf(target.position.y-origin.y)<22 and _first_wall_t(origin+Vector2(0,-3),target.position+Vector2(0,-7),0.0)>1.0:_hit_target(index,target.position+Vector2(0,-7),color,18)
			"reel":
				if tether_time>0.0:
					_add_impact(tether_point,color,"reel",0.5)
					if tether_target>=0:
						player.dash_time=0.18
						player.dash_velocity=(Vector2(targets[tether_target].position)-player.global_position).normalized()*100.0
					_show_notice("Reeling the attached line against the anchored practice target.")
				else:_show_notice("Reel needs an attached harpoon. Fire J at a target first.")
			"fan":
				if weapon_reload<=0.0:
					for index in range(weapon_ammo):_spawn_projectile("bullet",hand,direction.rotated((index-(weapon_ammo-1)*0.5)*0.035),660.0,color)
					weapon_ammo=0
					weapon_reload=player.duration("reload")
			"seal":_add_mark(origin+Vector2(150,-2),"seal",color,4.0)
			"thrust":_melee(origin,115.0,color,"thrust")
			"vent":_area_hit(origin+Vector2(60,-35),65,color)
			"decoy":_make_decoy(player.activation_origin)
			"vault":
				player.dash(120.0,0.5,true)
				_emit_particles(origin,10,Color("d8c292"),false)
			"gravity":_add_mark(origin+Vector2(140,-3),"gravity",color,1.4)
	else:
		# Held powered review has no invented buff, charge cost or timed duration.
		_add_impact(origin+Vector2(0,-42),color,"activation",0.65)
		if id=="rook":
			for offset in [Vector2(-45,-8),Vector2(36,14)]:
				var turret:=TurretView.new()
				turret.position=origin+offset
				actors.add_child(turret)
				special_props.append(turret)
		if id=="mirra":
			var seals:Array=[]
			for mark in marks:
				if mark.kind=="seal":seals.append(mark.position)
			if seals.size()>1:
				if _first_wall_t(seals[0],seals[1],0.0)>1.0:_add_impact(seals[0],color,"current",0.5,seals[1])
		if id=="mote":
			orbit_clock=0.0
			for _index in range(3):
				var shard:=OrbitShardView.new()
				shard.position=origin
				actors.add_child(shard)
				orbital_shards.append(shard)
		_show_notice("Powered equipment stays until E returns it. WASD moves on the flat; J/Space reviews strike/brace.")

func _release_anchor(_id:String,clip:String,fallback:Vector2) -> Vector2:
	var data:Dictionary=player.manifest.get("clips",{}).get(clip,{})
	var value=data.get("release_anchor",null)
	if value is Array and value.size()==2:return Vector2(float(value[0]),float(value[1]))
	return fallback

func _current_hand_anchor() -> Vector2:
	var data:Dictionary=player.manifest.get("clips",{}).get(player.clip,{})
	var track:Array=data.get("hand_anchors",[])
	if player.sprite.frame<track.size():
		var value=track[player.sprite.frame]
		if value is Array and value.size()==2:return Vector2(float(value[0]),float(value[1]))
	return _release_anchor(player.character_id,player.clip,DEFINITIONS[player.character_id].hand)

func _on_action_finished(_id:String,kind:String) -> void:
	if kind=="reload":
		weapon_ammo=6
		weapon_reload=0.0
	elif player.character_id=="pendle" and weapon_ammo==0 and kind in ["primary","secondary"]:player.start_reload()
	if kind=="powered_exit":
		for node in special_props:
			if is_instance_valid(node):node.queue_free()
		special_props.clear()
		for shard in orbital_shards:
			if is_instance_valid(shard):shard.queue_free()
		orbital_shards.clear()

func _on_action_cancelled(id:String,kind:String) -> void:
	if id=="iona" and kind=="secondary":
		lunge_time=0.0
		lunge_hits.clear()

func _make_decoy(origin:Vector2) -> void:
	if decoy_cooldown>0.0:
		_show_notice("Afterimage is cooling down.")
		return
	if is_instance_valid(decoy):decoy.queue_free()
	decoy=Sprite2D.new()
	decoy.texture=player.sprite.sprite_frames.get_frame_texture("idle",0)
	decoy.centered=false
	decoy.offset=-player.foot_pivot
	decoy.texture_filter=CanvasItem.TEXTURE_FILTER_NEAREST
	decoy.modulate=Color(0.45,1.0,0.9,0.52)
	decoy.position=origin.round()
	actors.add_child(decoy)
	decoy_origin=origin
	decoy_time=3.0
	decoy_cooldown=6.0

func _spawn_projectile(kind:String,origin:Vector2,direction:Vector2,speed:float,color:Color) -> void:
	if projectiles.size()>=MAX_PROJECTILES:return
	if kind=="harpoon":
		tether_time=0.0
		tether_target=-1
	var height:=maxf(2.0,player.global_position.y-origin.y)
	var item:={"kind":kind,"position":origin,"previous":origin,"ground":origin+Vector2(0,height),"height":height,"start_height":height,"age":0.0,"life":1.3,"direction":direction.normalized(),"speed":speed,"color":color,"radius":16.0 if kind=="boulder" else (6.0 if kind in ["rocket","flask","water"] else 2.0),"amplified":false}
	# A long weapon cannot create its projectile beyond an adjacent solid object.
	# This also makes a close-range boulder contact the post occupied by the hand.
	var shoulder:=Vector2(player.global_position.x,origin.y)
	if origin.x>=shoulder.x and origin.x-shoulder.x<=130.0:
		var obstruction:=_first_collision(shoulder,origin,float(item.radius))
		if not obstruction.is_empty():
			var point:=shoulder.lerp(origin,float(obstruction.t))
			if obstruction.kind=="target":
				_hit_target(int(obstruction.index),point,color,25 if kind in ["rocket","boulder"] else 15)
				if kind=="harpoon":_attach_harpoon(int(obstruction.index),point)
			else:
				wall_hits+=1
				_emit_particles(point,8,Color("adad98"),false)
			_add_impact(point,color,"contact",0.18)
			return
	var node:=ProjectileView.new()
	node.yard=self
	node.projectile=item
	node.position=item.ground.round()
	item.node=node
	actors.add_child(node)
	projectiles.append(item)
	var clip_data:Dictionary=player.manifest.get("clips",{}).get(player.clip,{})
	var baked:Array=clip_data.get("baked_effects",[])
	if "muzzle_flash" not in baked:
		var existing:=impacts.any(func(impact):return impact.kind=="muzzle" and Vector2(impact.position).distance_to(origin)<2.0 and float(impact.life)>0.07)
		if not existing:_add_impact(origin,color,"muzzle",0.09)

func _step_projectiles(dt:float) -> void:
	for index in range(projectiles.size()-1,-1,-1):
		var item:Dictionary=projectiles[index]
		item.previous=item.position
		item.age+=dt
		item.life-=dt
		if item.kind=="boulder":
			item.ground+=item.direction*item.speed*dt
			var t:=clampf(float(item.age)/1.08,0.0,1.0)
			item.height=float(item.start_height)*(1.0-t)+sin(t*PI)*20.0
			item.position=item.ground-Vector2(0,item.height)
		else:
			item.position+=item.direction*item.speed*dt
			item.ground=item.position+Vector2(0,item.height)
		item.node.position=Vector2(item.ground).round()
		item.node.queue_redraw()
		var collision:=_first_collision(item.previous,item.position,float(item.radius))
		if not collision.is_empty():
			var point:Vector2=item.previous.lerp(item.position,float(collision.t))
			if collision.kind=="target":
				_hit_target(int(collision.index),point,item.color,25 if item.kind in ["rocket","boulder"] else 15)
				if item.kind=="harpoon":
					_attach_harpoon(int(collision.index),point)
			else:
				wall_hits+=1
				_emit_particles(point,10,Color("adad98"),false)
			if item.kind=="flask":_add_mark(point+Vector2(0,25),"reagent",item.color,3.5)
			if item.kind in ["boulder","rocket"]:_add_mark(point+Vector2(0,12),"crack",item.color,3.5)
			_add_impact(point,item.color,"contact",0.18)
			item.node.queue_free()
			projectiles.remove_at(index)
		elif item.life<=0.0 or (item.kind=="boulder" and item.age>=1.08):
			if item.kind=="boulder":
				_add_mark(item.ground,"crack",item.color,3.5)
				_emit_particles(item.ground,10,item.color,false)
			item.node.queue_free()
			projectiles.remove_at(index)
		elif item.kind=="water" and not item.amplified:
			for mark in marks:
				if mark.kind=="seal" and Geometry2D.get_closest_point_to_segment(mark.position-Vector2(0,40),item.previous,item.position).distance_to(mark.position-Vector2(0,40))<24.0:
					item.amplified=true
					_add_impact(item.position,item.color,"contact",0.15)

func _attach_harpoon(index:int,point:Vector2) -> void:
	if int(targets[index].health)<=0:return
	tether_time=2.0
	tether_point=point
	tether_target=index

func _beam(origin:Vector2,direction:Vector2,color:Color) -> void:
	var end:=origin+direction*560
	var hit:=_first_collision(origin,end,0.5)
	if not hit.is_empty():
		end=origin.lerp(end,float(hit.t))
		if hit.kind=="target":_hit_target(int(hit.index),end,color,15)
		else:
			wall_hits+=1
			_emit_particles(end,10,Color("b5b4a0"),false)
		_add_impact(end,color,"contact",0.18)
	_add_impact(origin,color,"beam",0.105,end)

func _melee(origin:Vector2,reach:float,color:Color,kind:String,lunge:bool=false) -> void:
	var definition:Dictionary=DEFINITIONS[player.character_id]
	var data:Dictionary=player.manifest.get("clips",{}).get(player.clip,{})
	reach=float(data.get("contact_reach",reach))
	var fallback:Vector2=definition.get("secondary_hand",definition.hand) if player.clip=="secondary" else definition.hand
	var hand:Vector2=origin+_release_anchor(player.character_id,player.clip,fallback)
	var from:=Vector2(origin.x,hand.y)
	var to:=Vector2(origin.x+reach,hand.y)
	var wall:=_first_wall_t(from,to,0.0)
	if wall<=1.0:
		wall_hits+=1
		hand=from.lerp(to,wall)
		_emit_particles(hand,8,Color("b1b29c"),false)
	if not lunge:_add_impact(hand,color,kind,0.19)
	for index in range(targets.size()):
		var target:Dictionary=targets[index]
		if lunge and lunge_hits.has(index):continue
		if absf(player.ground_height-float(target.get("ground_height",0.0)))>12.0:continue
		var relative:Vector2=target.position-origin
		if relative.x<10 or relative.x>reach+18:continue
		for shape in _target_shapes(target):
			var contact:=_segment_rect_t(from,to,shape.grow(2))
			if contact<=1.0 and contact<wall:
				var point:=from.lerp(to,contact)
				point=Vector2(clampf(point.x,shape.position.x,shape.end.x),clampf(point.y,shape.position.y,shape.end.y))
				_hit_target(index,point,color,30 if kind=="slam" else 18)
				if lunge:lunge_hits[index]=true
				break
	if kind=="slam":_add_mark(hand,"crack",color,4.0)

func _area_hit(point:Vector2,radius:float,color:Color) -> void:
	_add_impact(point,color,"burst",0.23)
	_emit_particles(point,10,color,false)
	for index in range(targets.size()):
		var target:Dictionary=targets[index]
		if target.position.distance_to(point+Vector2(0,22))<radius and _first_wall_t(point,target.position+Vector2(0,-22),0.0)>1.0:
			_hit_target(index,target.position+Vector2(0,-25),color,18)

func _hit_target(index:int,point:Vector2,color:Color,damage:int) -> void:
	var target:Dictionary=targets[index]
	if target.health<=0:return
	target.hits+=1
	target.health=maxi(0,int(target.health)-damage)
	target.node.hits=target.hits
	target.node.hit_time=0.18
	target.node.broken=target.health<=0 and target.kind=="crate"
	hit_total+=1
	_emit_particles(point,8 if quiet else 14,Color("bd9f72"),true)
	_add_impact(point,color,"contact",0.16)

func _first_collision(from:Vector2,to:Vector2,radius:float) -> Dictionary:
	var best:=_first_wall_t(from,to,radius)
	var result:Dictionary={} if best>1.0 else {"t":best,"kind":"wall"}
	for index in range(targets.size()):
		var target:Dictionary=targets[index]
		if target.health<=0 and target.kind=="crate":continue
		for shape in _target_shapes(target):
			var time:=_segment_rect_t(from,to,shape.grow(radius))
			if time<best:
				best=time
				result={"t":time,"kind":"target","index":index}
	return result

func _target_shapes(target:Dictionary) -> Array[Rect2]:
	var result:Array[Rect2]=[]
	if target.kind=="crate":
		result.append(Rect2(target.position+Vector2(-24,-44),Vector2(48,42)))
	else:
		result.append(Rect2(target.position+Vector2(-18,-90),Vector2(36,40)))
		result.append(Rect2(target.position+Vector2(-4,-50),Vector2(8,48)))
	return result

func _first_wall_t(from:Vector2,to:Vector2,radius:float) -> float:
	var best:=INF
	for blocker in blockers:
		var visible_stone:=Rect2(blocker.position-Vector2(0,53),blocker.size+Vector2(0,53))
		best=minf(best,_segment_rect_t(from,to,visible_stone.grow(radius)))
	for boundary in [Rect2(-300,-300,376,1200),Rect2(884,-300,500,1200),Rect2(-300,-300,1600,432),Rect2(-300,436,1600,500)]:best=minf(best,_segment_rect_t(from,to,boundary.grow(radius)))
	return best

func _segment_rect_t(from:Vector2,to:Vector2,rect:Rect2) -> float:
	var enter:=0.0
	var leave:=1.0
	var movement:=to-from
	for axis in range(2):
		if absf(movement[axis])<0.000001:
			if from[axis]<rect.position[axis] or from[axis]>rect.end[axis]:return INF
		else:
			var first:float=(rect.position[axis]-from[axis])/movement[axis]
			var last:float=(rect.end[axis]-from[axis])/movement[axis]
			enter=maxf(enter,minf(first,last))
			leave=minf(leave,maxf(first,last))
			if enter>leave:return INF
	return enter if enter<=1.0 and leave>=0.0 else INF

func _emit_particles(point:Vector2,count:int,color:Color,wood:bool) -> void:
	for _index in range(count):
		if particles.size()>=MAX_PARTICLES:break
		particles.append({"position":point,"velocity":Vector2(rng.randf_range(-34,34),rng.randf_range(-52,-14)),"life":rng.randf_range(0.25,0.5),"color":color,"wood":wood,"size":rng.randi_range(1,3)})

func _add_impact(point:Vector2,color:Color,kind:String,life:float,end:Vector2=Vector2.ZERO) -> void:
	if impacts.size()>=MAX_IMPACTS:impacts.pop_front()
	impacts.append({"position":point,"end":end,"color":color,"kind":kind,"life":life,"max":life})

func _add_mark(point:Vector2,kind:String,color:Color,life:float) -> void:
	if marks.size()>=MAX_MARKS:marks.pop_front()
	marks.append({"position":point.round(),"kind":kind,"color":color,"life":life,"max":life})

func _clear_effects() -> void:
	for projectile in projectiles:
		if is_instance_valid(projectile.node):projectile.node.queue_free()
	projectiles.clear()
	particles.clear()
	impacts.clear()
	marks.clear()
	if is_instance_valid(decoy):decoy.queue_free()
	decoy_time=0.0
	decoy_cooldown=0.0
	tether_time=0.0
	tether_target=-1
	lunge_time=0.0
	lunge_hits.clear()
	for node in special_props:
		if is_instance_valid(node):node.queue_free()
	special_props.clear()
	for shard in orbital_shards:
		if is_instance_valid(shard):shard.queue_free()
	orbital_shards.clear()

func _reset_targets() -> void:
	hit_total=0
	wall_hits=0
	for target in targets:
		target.hits=0
		target.health=100
		target.restore=0.0
		target.node.hits=0
		target.node.hit_time=0.0
		target.node.broken=false
		target.node.exposed=0.0
		target.collision.set_deferred("disabled",false)

func reset_room(stop_demo:bool=true) -> void:
	if stop_demo:auto_demo=false
	_clear_effects()
	_reset_targets()
	player.reset_pose()
	player.position=Vector2(360,350)
	player.reset_traversal()
	paused=false
	weapon_ammo=6
	weapon_reload=0.0

func _toggle_demo() -> void:
	auto_demo=not auto_demo
	reset_room(false)
	demo_clock=0.0
	demo_character=-1
	demo_clip=-1
	demo_events=0
	demo_clip_age=0.0
	traversal_showcase_phase=-1
	traversal_showcase_done=false
	_show_notice("Every character and every base clip are shown. TAB returns control.")

func _run_demo(dt:float) -> void:
	demo_clock+=dt
	if traversal_showcase:
		_run_traversal_showcase(dt)
		return
	if showcase:
		_run_showcase(dt)
		return
	if demo_character<0:
		demo_character=0
		demo_clip=0
		select_character(0)
		if player.available:player.play_study(CLIPS[0])
		player.study_loop=false
	demo_clip_age+=dt
	var wait_time:=player.duration()+0.22 if player.available else 0.2
	if demo_clip_age>=wait_time:
		demo_clip_age=0.0
		demo_clip+=1
		if demo_clip>=player.animation_clips().size():
			demo_clip=0
			demo_character=posmod(demo_character+1,IDS.size())
			select_character(demo_character)
		if player.available:player.play_study(player.animation_clips()[demo_clip])
		player.study_loop=false

func _run_showcase(dt:float) -> void:
	if demo_character<0:
		demo_character=0
		select_character(demo_character)
		_enter_practice()
		player.use_demo_move=true
		player.demo_move=Vector2(0.18,0)
		showcase_phase=0
		demo_clip_age=0.0
	demo_clip_age+=dt
	if not player.available:
		demo_clip_age=3.0
	if showcase_phase==0 and demo_clip_age>=0.72:
		player.demo_move=Vector2.ZERO
		player.start_action("primary")
		showcase_phase=1
		demo_clip_age=0.0
	elif showcase_phase==1 and demo_clip_age>=player.duration("primary")+0.12:
		player.start_action("secondary")
		showcase_phase=2
		demo_clip_age=0.0
	elif showcase_phase==2 and demo_clip_age>=player.duration("secondary")+0.42:
		demo_character=posmod(demo_character+1,IDS.size())
		select_character(demo_character)
		_enter_practice()
		player.use_demo_move=true
		player.demo_move=Vector2(0.18,0)
		showcase_phase=0
		demo_clip_age=0.0

func _run_traversal_showcase(dt:float) -> void:
	demo_clip_age+=dt
	if traversal_showcase_phase<0:
		terrain_mode=true
		select_character(IDS.find("cairn"))
		_enter_practice()
		player.position=terrain_checkpoint
		player.reset_traversal()
		player.use_demo_move=true
		player.demo_move=Vector2.RIGHT
		traversal_showcase_phase=0
		demo_clip_age=0.0
		queue_redraw()
	elif traversal_showcase_phase==0 and player.position.x>=617:
		player.start_jump()
		traversal_showcase_phase=1
		demo_clip_age=0.0
	elif traversal_showcase_phase==1 and player.position.x>=743 and player.traversal_state.is_empty():
		player.demo_move=Vector2.DOWN
		player.start_dodge()
		traversal_showcase_phase=2
		demo_clip_age=0.0
	elif traversal_showcase_phase==2 and player.traversal_state.is_empty() and demo_clip_age>0.1:
		player.demo_move=Vector2.ZERO
		traversal_showcase_phase=3
		demo_clip_age=0.0
	elif traversal_showcase_phase==3 and demo_clip_age>0.3:
		terrain_mode=false
		queue_redraw()
		demo_character=0
		_start_showcase_character()
	elif traversal_showcase_phase==10 and player.traversal_state.is_empty() and demo_clip_age>0.2:
		player.start_action("secondary" if player.character_id=="rook" else "special")
		traversal_showcase_phase=15 if player.character_id=="rook" else 11
		demo_clip_age=0.0
	elif traversal_showcase_phase==15 and player.traversal_state.is_empty() and player.action.is_empty():
		player.start_action("special")
		traversal_showcase_phase=11
		demo_clip_age=0.0
	elif traversal_showcase_phase==11 and player.powered_mode and player.action.is_empty():
		player.demo_move=Vector2.RIGHT
		traversal_showcase_phase=12
		demo_clip_age=0.0
	elif traversal_showcase_phase==12 and demo_clip_age>0.30:
		player.demo_move=Vector2.ZERO
		player.start_action("primary")
		traversal_showcase_phase=13
		demo_clip_age=0.0
	elif traversal_showcase_phase==13 and player.action.is_empty() and demo_clip_age>0.1:
		player.start_action("special")
		traversal_showcase_phase=14
		demo_clip_age=0.0
	elif traversal_showcase_phase==14 and not player.powered_mode and player.action.is_empty():
		demo_character+=1
		if demo_character>=IDS.size():
			auto_demo=false
			traversal_showcase_done=true
			print("Traversal showcase complete after %.3f simulation seconds"%demo_clock)
			player.demo_move=Vector2.ZERO
			_show_notice("Traversal and all fourteen powered reviews complete.")
			if "--quit-on-showcase" in OS.get_cmdline_user_args():get_tree().quit()
		else:_start_showcase_character()

func _start_showcase_character() -> void:
	select_character(demo_character)
	_enter_practice()
	player.use_demo_move=true
	player.demo_move=Vector2.ZERO
	player.start_jump()
	traversal_showcase_phase=10
	demo_clip_age=0.0

func _unhandled_input(event:InputEvent) -> void:
	if not is_instance_valid(player):return
	if event is InputEventKey and event.pressed and not event.echo:
		if event.physical_keycode>=KEY_1 and event.physical_keycode<=KEY_8:
			choose_clip(CLIPS[event.physical_keycode-KEY_1])
			return
		match event.physical_keycode:
			KEY_BRACKETLEFT:
				auto_demo=false
				select_character(selected-1)
			KEY_BRACKETRIGHT:
				auto_demo=false
				select_character(selected+1)
			KEY_J,KEY_Q,KEY_E:
				auto_demo=false
				_enter_practice()
				if terrain_mode and event.physical_keycode==KEY_E:
					_show_notice("T returns to flat target practice before powered equipment review.")
				elif player.powered_mode and event.physical_keycode==KEY_Q:
					_show_notice("This powered review covers idle, walk, strike, brace and return. E restores base abilities.")
				else:player.queue_action("primary" if event.physical_keycode==KEY_J else ("secondary" if event.physical_keycode==KEY_Q else "special"))
			KEY_K,KEY_SHIFT:
				auto_demo=false
				_enter_practice()
				if player.powered_mode:
					_show_notice("E returns the equipment to base before jump or dodge practice.")
				elif event.physical_keycode==KEY_K:player.start_jump()
				else:player.start_dodge()
			KEY_T:_toggle_terrain()
			KEY_N:
				var names:Array=player.animation_clips()
				var current:=names.find(player.clip)
				choose_clip(names[posmod(current+(-1 if event.shift_pressed else 1),names.size())])
			KEY_SPACE:
				auto_demo=false
				_enter_practice()
			KEY_B:_toggle_practice()
			KEY_C:_toggle_inspector()
			KEY_P:_toggle_pause()
			KEY_V:_toggle_speed()
			KEY_COMMA:_step_pose(-1)
			KEY_PERIOD:_step_pose(1)
			KEY_R:reset_room()
			KEY_H:choose_clip("hit")
			KEY_L:choose_clip("defeat")
			KEY_M:quiet=not quiet
			KEY_TAB:_toggle_demo()
			KEY_F:DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED if DisplayServer.window_get_mode()==DisplayServer.WINDOW_MODE_FULLSCREEN else DisplayServer.WINDOW_MODE_FULLSCREEN)
			KEY_ESCAPE:DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)

func _notification(what:int) -> void:
	if not is_instance_valid(player):return
	if what in [NOTIFICATION_APPLICATION_FOCUS_OUT,NOTIFICATION_WM_WINDOW_FOCUS_OUT]:
		focus_paused=true
		player.suspended=true
		player.clear_controls()
	elif what in [NOTIFICATION_APPLICATION_FOCUS_IN,NOTIFICATION_WM_WINDOW_FOCUS_IN]:
		focus_paused=false
		player.suspended=false

func _draw() -> void:
	draw_rect(Rect2(0,0,960,540),Color("172b2a"))
	draw_rect(Rect2(44,139,872,303),Color("344e43"))
	for row in range(10):
		for column in range(19):
			var x:=45+column*46+(23 if row%2 else 0)
			var y:=143+row*30
			if x>=912:continue
			var color:Color=[Color("52685a"),Color("5d705e"),Color("596e5e"),Color("4d6458")][(column*11+row*7)%4]
			draw_rect(Rect2(x,y,mini(44,914-x),28),color)
			draw_line(Vector2(x+1,y),Vector2(mini(x+42,913),y),Color("788671"),1)
			if (column*7+row*3)%11==0:
				draw_line(Vector2(x+12,y+5),Vector2(x+17,y+13),Color("3f594b"),1)
				draw_line(Vector2(x+17,y+13),Vector2(x+14,y+20),Color("3f594b"),1)
	for column in range(19):
		var x:=43+column*46
		draw_rect(Rect2(x,139,44,12),Color("8d9b80"))
		draw_rect(Rect2(x,151,44,20),Color("405849"))
		draw_rect(Rect2(x,430,44,12),Color("7b8d74"))
	for rect in blockers:
		draw_rect(Rect2(rect.position+Vector2(-5,-48),rect.size+Vector2(10,45)),Color("2d453b"))
		draw_rect(Rect2(rect.position+Vector2(-3,-53),rect.size+Vector2(6,-4)),Color("5e7561"))
		draw_rect(Rect2(rect.position+Vector2(-5,-56),Vector2(rect.size.x+10,11)),Color("94a487"))
		for i in range(5):draw_line(rect.position+Vector2(-2,-34+i*30),rect.position+Vector2(rect.size.x+2,-34+i*30),Color("344d3f"),2)
	for point in [Vector2(97,193),Vector2(865,196),Vector2(105,408),Vector2(852,406)]:
		for i in range(16):
			var p:Vector2=point+Vector2((i*17)%49-24,(i*11)%23-11)
			draw_rect(Rect2(p,Vector2(3+i%3,2)),Color("83965e") if i%2 else Color("627d4e"))
			draw_line(p,p+Vector2(-2,-4-i%3),Color("9dac79"),1)
	for point in [Vector2(560,350),Vector2(650,420)]:
		draw_line(point+Vector2(-28,8),point+Vector2(28,8),Color("8b9c7a"),1)
	if terrain_mode:_draw_terrain()

func _draw_terrain() -> void:
	# This geometry is a labelled collision/registration fixture, not a production map.
	var top:=Color("8b967d")
	var line:=Color("b7b99a")
	var face:=Color("495e51")
	draw_rect(Rect2(312,209,176,66),top)
	draw_rect(Rect2(312,275,176,32),face)
	for index in range(8):
		var x:=216.0+index*12.0
		var h:=index*4.0
		draw_colored_polygon(PackedVector2Array([Vector2(x,241-h),Vector2(x+12,237-h),Vector2(x+12,303-h),Vector2(x,307-h)]),top)
		draw_line(Vector2(x,241-h),Vector2(x,307-h),line,1)
		draw_line(Vector2(x,307-h),Vector2(x+12,303-h),face,3)
		x=488.0+index*12.0
		h=32.0-index*4.0
		draw_colored_polygon(PackedVector2Array([Vector2(x,241-h),Vector2(x+12,245-h),Vector2(x+12,311-h),Vector2(x,307-h)]),top)
		draw_line(Vector2(x,241-h),Vector2(x,307-h),line,1)
		draw_line(Vector2(x,307-h),Vector2(x+12,311-h),face,3)
	draw_line(Vector2(312,209),Vector2(488,209),line,2)
	for x in range(322,488,28):draw_line(Vector2(x,215),Vector2(x+6,266),Color("7b8b73"),1)
	draw_rect(Rect2(630,224,82,67),Color("91a086"))
	draw_rect(Rect2(630,291,82,16),face)
	draw_line(Vector2(630,224),Vector2(712,224),line,2)
	draw_rect(PIT.grow(3),Color("34463c"))
	draw_rect(PIT,Color("152723"))
	for x in range(362,470,12):
		draw_rect(Rect2(x,389,10,22),Color("9b805b"))
		draw_line(Vector2(x,390),Vector2(x+9,390),Color("c0a477"),1)
	draw_line(Vector2(359,389),Vector2(471,389),Color("514b37"),2)
	draw_line(Vector2(359,411),Vector2(471,411),Color("514b37"),2)
	draw_rect(WATER,Color("4c7776"))
	for i in range(7):draw_line(Vector2(525+i*12,381+(i%3)*13),Vector2(534+i*12,381+(i%3)*13),Color("83aaa0"),1)
	draw_rect(MUD,Color("66664d"))
	for i in range(13):draw_rect(Rect2(139+(i*19)%78,375+(i*13)%44,5,2),Color("7b7856"))
	draw_rect(ICE,Color("9ebdb8"))
	for i in range(5):draw_line(Vector2(677+i*14,371),Vector2(690+i*12,418),Color("b9d2c6"),1)
	var font:=ThemeDB.fallback_font
	for item in [[Vector2(323,232),"STAIR +32"],[Vector2(638,246),"LEDGE +16"],[Vector2(373,438),"GAP / BRIDGE"],[Vector2(532,438),"WATER"],[Vector2(146,438),"MUD"],[Vector2(684,438),"ICE"]]:
		draw_string(font,item[0],item[1],HORIZONTAL_ALIGNMENT_LEFT,-1,10,Color("d5d5b6"))

func draw_ground(layer:Node2D) -> void:
	if is_instance_valid(player):
		var point:Vector2=(player.position-Vector2(0,player.ground_height)).round()
		var shrink:=1.0-clampf(player.shadow_lift()/95.0,0.0,0.5)
		var shade:=0.4-clampf(player.shadow_lift()/220.0,0.0,0.2)
		var outline:=PackedVector2Array()
		for offset in [Vector2(-30,-3),Vector2(-20,-9),Vector2(20,-9),Vector2(30,-3),Vector2(20,4),Vector2(-20,4)]:outline.append(point+(offset*shrink).round())
		layer.draw_colored_polygon(outline,Color(0.07,0.13,0.11,shade))
	for projectile in projectiles:
		var point:Vector2=Vector2(projectile.ground).round()
		if projectile.kind in ["boulder","flask","rocket"]:layer.draw_rect(Rect2(point+Vector2(-9,-2),Vector2(18,3)),Color(0.07,0.13,0.11,0.35))
	for mark in marks:
		var p:Vector2=mark.position
		var color:Color=mark.color
		var fade:=minf(1.0,float(mark.life))
		match mark.kind:
			"crack":
				for i in range(6):
					var angle:=i*TAU/6.0+0.13
					var mid:=p+Vector2(cos(angle)*11,sin(angle)*5).round()
					var end:=p+Vector2(cos(angle+0.1)*23,sin(angle+0.1)*11).round()
					layer.draw_line(p,mid,Color(0.19,0.27,0.20,fade),2)
					layer.draw_line(mid,end,Color(0.19,0.27,0.20,fade),1)
			"ridge":
				for i in range(7):
					var at:=p+Vector2(-80+i*28,0)
					layer.draw_colored_polygon(PackedVector2Array([at+Vector2(-9,0),at+Vector2(0,-17-i%3*3),at+Vector2(8,0)]),Color(color,fade*0.8))
			"seal","gravity":
				for i in range(8):
					var a:=i*TAU/8.0
					var q:=p+Vector2(cos(a)*21,sin(a)*9).round()
					layer.draw_rect(Rect2(q,Vector2(3,2)),Color(color,fade*0.7))
				layer.draw_line(p+Vector2(-10,0),p+Vector2(10,0),Color(color,fade*0.6),1)
			"reagent":
				layer.draw_rect(Rect2(p+Vector2(-13,-3),Vector2(26,5)),Color(color,fade*0.4))
				layer.draw_rect(Rect2(p+Vector2(-8,-5),Vector2(16,8)),Color(color,fade*0.3))

func draw_projectile(layer:Node2D,item:Dictionary) -> void:
	var p:Vector2=Vector2(item.position).round()-layer.position
	var direction:Vector2=item.direction
	var color:Color=item.color
	match item.kind:
		"arrow","harpoon":
			layer.draw_line(p-direction*13,p+direction*8,Color("504d3a"),3)
			layer.draw_line(p-direction*12,p+direction*7,color,1)
			var side:=direction.orthogonal()*4
			layer.draw_colored_polygon(PackedVector2Array([p+direction*12,p+direction*5+side,p+direction*5-side]),Color("e3ddc1"))
			layer.draw_line(p-direction*10,p-direction*15+side,color,1)
		"bullet","carbine","rifle":
			layer.draw_line(p-direction*12,p,color,2)
			layer.draw_rect(Rect2(p,Vector2(3,2)),PAPER)
		"rocket":
			layer.draw_rect(Rect2(p+Vector2(-9,-4),Vector2(16,8)),Color("d4c3a2"))
			layer.draw_colored_polygon(PackedVector2Array([p+Vector2(13,0),p+Vector2(5,-4),p+Vector2(5,4)]),Color("947d60"))
			layer.draw_rect(Rect2(p+Vector2(-16,-2),Vector2(8,4)),Color("e8b47b"))
			layer.draw_rect(Rect2(p+Vector2(-22,-1),Vector2(6,2)),Color("a7896c"))
		"flask":
			layer.draw_rect(Rect2(p+Vector2(-5,-5),Vector2(10,10)),Color("4e5147"))
			layer.draw_rect(Rect2(p+Vector2(-3,-3),Vector2(6,7)),color)
			layer.draw_rect(Rect2(p+Vector2(-2,-8),Vector2(4,4)),Color("c1bd9f"))
			layer.draw_rect(Rect2(p+Vector2(-2,-2),Vector2(2,3)),PAPER)
		"boulder":
			var texture_path:="res://assets/cairn/boulder-%d.png"%(int(item.age*12.0)%4)
			if ResourceLoader.exists(texture_path):layer.draw_texture_rect(load(texture_path),Rect2(p-Vector2(16,16),Vector2(32,32)),false)
		"water":
			layer.draw_colored_polygon(PackedVector2Array([p+direction*9,p+Vector2(-4,-5),p-direction*12,p+Vector2(-4,5)]),Color("447c80"))
			layer.draw_line(p-direction*5,p+direction*6,color,4)
			layer.draw_rect(Rect2(p+Vector2(0,-1),Vector2(4,2)),Color("d8f1df"))
		"glass":
			layer.draw_colored_polygon(PackedVector2Array([p+direction*11,p+direction*-5+Vector2(0,-4),p+direction*-3+Vector2(0,4)]),color)
			layer.draw_line(p-direction*2,p+direction*7,PAPER,1)

func draw_effects(layer:Node2D) -> void:
	if is_instance_valid(player) and player.character_id=="rook" and player.traversal_is_ability and player.traversal_state=="air" and player.traversal_clock<0.11:
		var clip_data:Dictionary=player.manifest.get("clips",{}).get("secondary",{})
		for anchor in clip_data.get("thruster_anchors",[]):
			if not anchor is Array or anchor.size()!=2:continue
			var nozzle:Vector2=(player.visual_foot()+Vector2(float(anchor[0]),float(anchor[1]))).round()
			var length:=9.0+roundf(sin(player.traversal_clock*95.0)*3.0)
			layer.draw_colored_polygon(PackedVector2Array([nozzle+Vector2(-3,0),nozzle+Vector2(3,0),nozzle+Vector2(-7,length),nozzle+Vector2(-8,length-4)]),Color("d99d66"))
			layer.draw_line(nozzle+Vector2(0,1),nozzle+Vector2(-6,length-4),Color("f1d5a1"),2)
	for item in impacts:
		var point:Vector2=Vector2(item.position).round()
		var color:Color=item.color
		var age:=float(item.max)-float(item.life)
		var fade:=float(item.life)/float(item.max)
		match item.kind:
			"ripple":
				for i in range(12):
					var a:=i*TAU/12.0
					var b:=(i+1)*TAU/12.0
					var radius:=7.0+age*20.0
					layer.draw_line(point+Vector2(cos(a)*radius,sin(a)*radius*0.35).round(),point+Vector2(cos(b)*radius,sin(b)*radius*0.35).round(),Color(color,fade*0.65),1)
			"beam":
				layer.draw_line(point,Vector2(item.end).round(),color,2)
				if age<0.045:layer.draw_line(point,Vector2(item.end).round(),PAPER,1)
			"muzzle","contact":
				if age<0.07:
					layer.draw_line(point-Vector2(4,0),point+Vector2(4,0),PAPER,1)
					layer.draw_line(point-Vector2(0,4),point+Vector2(0,4),color,1)
			"sabre","sword","billhook","thrust","spear","palm","gun-butt":
				var length:=12.0+age*55.0
				var from:=point+Vector2(-7,-length*0.5).round()
				var middle:=point+Vector2(7,0)
				var to:=point+Vector2(-4,length*0.5).round()
				layer.draw_line(from,middle,Color(color,fade),2)
				layer.draw_line(middle,to,Color(color,fade),2)
			"slam","burst":
				for i in range(6):
					var at:=point+Vector2((i-2.5)*(4+age*22),-sin(i*PI/5.0)*(2+age*8)).round()
					layer.draw_rect(Rect2(at,Vector2(3,2)),Color(color,fade))
			"lantern","activation","reel":
				for i in range(6):
					var angle:=i*TAU/6.0+age*0.8
					var at:=point+Vector2(cos(angle)*(12+age*8),sin(angle)*(17+age*5)).round()
					layer.draw_rect(Rect2(at,Vector2(2,3)),Color(color,fade*0.8))
			"current":layer.draw_line(point,Vector2(item.end).round(),Color(color,fade*0.6),2)
	for particle in particles:
		var point:Vector2=Vector2(particle.position).round()
		layer.draw_rect(Rect2(point,Vector2(particle.size,3 if particle.wood else particle.size)),particle.color)
	if tether_time>0.0 and is_instance_valid(player):
		layer.draw_line((player.visual_foot()+_current_hand_anchor()).round(),tether_point.round(),Color("b8c1a4"),1)
	if is_instance_valid(player) and player.character_id=="mirra" and player.powered_mode:
		var seals:Array=marks.filter(func(mark):return mark.kind=="seal" and float(mark.life)>0.0)
		for index in range(seals.size()-1):
			var from:Vector2=seals[index].position
			var to:Vector2=seals[index+1].position
			if _first_wall_t(from,to,0.0)>1.0:layer.draw_line(from.round(),to.round(),Color("91d5d5",0.6),2)
	if is_instance_valid(player) and player.guarded:
		var color:=Color(DEFINITIONS[player.character_id].color)
		var point:Vector2=player.visual_foot().round()+Vector2(43,-42)
		for i in range(5):layer.draw_rect(Rect2(point+Vector2(i%2,-15+i*7),Vector2(2,4)),Color(color,0.6))
