from pathlib import Path
import hashlib
import argparse
parser=argparse.ArgumentParser(description="Extract exact source methods into a fake-boundary Godot probe; no project files are written.")
parser.add_argument('--player', type=Path, required=True)
parser.add_argument('--cast', type=Path, required=True)
parser.add_argument('--out', type=Path, required=True)
args=parser.parse_args()
def checked_text(path, expected):
 data=path.read_bytes()
 digest=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
 # The local patch transport may append one newline; discard only if exact blob identity proves it.
 if digest != expected and data.endswith(b'\n'):
  trimmed=data[:-1]
  if hashlib.sha1(b'blob '+str(len(trimmed)).encode()+b'\0'+trimmed).hexdigest()==expected:data=trimmed
 digest=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
 if digest!=expected:raise ValueError(str(path)+': wrong pinned source blob')
 return data.decode()
player=checked_text(args.player,'0dd01672a14fda097b3db2e0da8643c5eca6307b')
cast=checked_text(args.cast,'6837d96ed76da2142f36bb611471bc95346d9937')
def extract(src,name):
 lines=src.splitlines(); start=next(i for i,l in enumerate(lines) if l.startswith(f'func {name}('))
 end=start+1
 while end<len(lines) and (not lines[end] or lines[end][0].isspace()):end+=1
 return '\n'.join('\t'+l for l in lines[start:end]).rstrip()+'\n'
parts=['''extends SceneTree
# Source-method probes with fake boundary objects. Not Player/GdUnit/game validation.
class BoundarySprite:
	extends RefCounted
	var calls := []
	func load_character(_id: String) -> bool:
		return true
	func walk_speed() -> float:
		return 67.9
	func play_clip(name: String, fc: String, restart: bool) -> void:
		calls.append([name, fc, restart])

class PlayerMethodProbe:
	extends RefCounted
	const RUN_SPEED := 150.0
	var sprite := BoundarySprite.new()
	var character := "bramble"
	var walk_speed := RUN_SPEED
	var state := &"idle"
	var facing := "S"
	var hp := 5
	var _roll_t := 0.0
	var _swing_t := 0.0
	var _iframe_t := 0.0
''', extract(player,'set_character'),'''
class CastMethodProbe:
	extends RefCounted
	var manifest := {}
	var clip := "probe"
	var facing := "S"
	var frame_index := 0
	var clip_time := 0.0
	var finished := false
	var frame := 0
''']
parts += [extract(cast,n) for n in ['clip_info','duration','release_frame','advance','_sync']]
parts += ['''
class ActionMethodProbe:
	extends RefCounted
	var sprite: CastMethodProbe
	var emitted := []
	func _release(fr: int) -> void:
		emitted.append({"release_frame":fr,"display_frame":sprite.frame_index,"clock":sprite.clip_time})
''',extract(player,'_advance_action'),'''
func make_cast(loop: bool, release: int = 2) -> CastMethodProbe:
	var c := CastMethodProbe.new()
	c.manifest={"clips":{"probe":{"duration":0.4,"durations":[0.1,0.1,0.1,0.1],"loop":loop,"frame_count":4,"release_frame":release}}}
	return c

func _initialize() -> void:
	print("SOURCE-METHOD PROBES: extracted current methods; fake boundary objects; not full Player/GdUnit/game validation")
	var p := PlayerMethodProbe.new()
	p.hp=0
	p.state=&"defeat"
	var accepted := p.set_character("iona")
	print(JSON.stringify({"probe":"defeat_switch","accepted":accepted,"hp":p.hp,"state":String(p.state),"character":p.character}))
	p=PlayerMethodProbe.new()
	p.state=&"dodge"
	p._roll_t=0.42
	p._iframe_t=0.26
	accepted=p.set_character("iona")
	print(JSON.stringify({"probe":"roll_switch","accepted":accepted,"state":String(p.state),"roll_remaining":p._roll_t,"iframes_remaining":p._iframe_t}))
	p=PlayerMethodProbe.new()
	p._swing_t=0.18
	accepted=p.set_character("iona")
	print(JSON.stringify({"probe":"swing_switch","accepted":accepted,"state":String(p.state),"swing_remaining":p._swing_t}))
	var c := make_cast(true)
	var entered := c.advance(0.4)
	print(JSON.stringify({"probe":"one_loop","expected_entries":[1,2,3,0],"actual_entries":entered,"display_frame":c.frame_index}))
	c=make_cast(true)
	entered=c.advance(0.95)
	print(JSON.stringify({"probe":"multiple_loops","expected_entries":[1,2,3,0,1,2,3,0,1],"actual_entries":entered,"display_frame":c.frame_index}))
	var a := ActionMethodProbe.new()
	a.sprite=make_cast(false)
	a._advance_action(0.5)
	a._advance_action(0.1)
	print(JSON.stringify({"probe":"nonloop_coarse_release","emitted":a.emitted,"finished":a.sprite.finished,"display_frame":a.sprite.frame_index}))
	a=ActionMethodProbe.new()
	a.sprite=make_cast(false,0)
	a._advance_action(0.05)
	a._advance_action(0.5)
	print(JSON.stringify({"probe":"zero_entry_forward_robustness","expected_release_count":1,"actual_release_count":a.emitted.size(),"emitted":a.emitted}))
	quit()
''']
out=args.out;out.write_text('\n'.join(parts))
print(out)
print('player_sha256',hashlib.sha256(player.encode()).hexdigest())
print('cast_sha256',hashlib.sha256(cast.encode()).hexdigest())
