"""Extract published authoring timing/anchors without loading or exporting any art."""
from pathlib import Path
import ast,json,hashlib,math
ROOT=Path(__file__).resolve().parent
SOURCE=ROOT/'source/tools/build_animation_roster.py'
tree=ast.parse(SOURCE.read_text())
constants={}
for node in tree.body:
 if isinstance(node,ast.Assign):
  for target in node.targets:
   if isinstance(target,ast.Name) and target.id in ['IDS','V3_RELEASES','RELEASE_ANCHORS']:
    constants[target.id]=ast.literal_eval(node.value)
function=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='timing')
namespace={'V3_RELEASES':constants['V3_RELEASES']}
exec(compile(ast.Module(body=[function],type_ignores=[]),str(SOURCE),'exec'),namespace)
base=['idle','walk','primary','secondary','special','guard','hit','defeat','jump','stair_up','stair_down','dodge']
power=['powered_idle','powered_walk','powered_primary','powered_guard','powered_exit']
anchors={};anchor_provenance=[]
for path in sorted((ROOT/'source/art-source/animated/v3').glob('*.json')):
 document=json.loads(path.read_text());payload=document.get('anchors',document)
 anchor_provenance.append({'path':str(path.relative_to(ROOT/'source')),'sha256_of_local_reference':hashlib.sha256(path.read_bytes()).hexdigest()})
 for char in constants['IDS']:
  for clip,entry in payload.get(char,{}).items():
   if clip.startswith('_'):continue
   values={key:value for key,value in entry.items() if key in ['release_anchor','hand_anchors','thruster_anchors','baked_effects']}
   if 'contact_reach' in entry:values['presentation_contact_reach']=entry['contact_reach']
   anchors.setdefault(char,{}).setdefault(clip,{}).update(values)
characters={}
for char in constants['IDS']:
 clips={}
 for name in base+power+(['reload'] if char=='pendle' else []):
  count=16 if name in ['walk','primary'] else 8
  if char=='cairn':
   if name=='secondary':count=16
   if name in ['hit','defeat']:count=4
  if char=='velvet' and name=='powered_exit':count=7
  durations,loop,release=namespace['timing'](char,name,count)
  assert len(durations)==count and all(math.isfinite(t) and t>0 for t in durations)
  data={'frame_count':count,'durations':durations,'duration':sum(durations),'loop':loop,'release_frame':release,'release_time':sum(durations[:release]) if release is not None else None,'hold_frame':(3 if char=='cairn' and name=='guard' else min(4,count-1)) if name in ['guard','powered_guard'] else None}
  if (char,name) in constants['RELEASE_ANCHORS']:data['release_anchor']=constants['RELEASE_ANCHORS'][(char,name)]
  if char=='pendle' and name=='primary':data['baked_effects']=['muzzle_flash']
  data.update(anchors.get(char,{}).get(name,{}));clips[name]=data
 characters[char]={'view':'E','frame_size':[256,192] if char=='ashe' else [224,192] if char=='iona' else [192,192],'foot_pivot':[132,172] if char=='ashe' else [96,172],'old_body_height_target':112 if char=='cairn' else 96,'pose_count':sum(x['frame_count'] for x in clips.values()),'clips':clips}
assert len(characters)==14 and sum(c['pose_count'] for c in characters.values())==2135
for char,data in characters.items():
 for name,clip in data['clips'].items():
  assert clip['release_frame'] is None or 0<=clip['release_frame']<clip['frame_count']
  if 'hand_anchors' in clip:assert len(clip['hand_anchors'])==clip['frame_count'],(char,name)
  if 'release_anchor' in clip:assert len(clip['release_anchor'])==2
output={'schema_version':1,'status':'legacy_east_reference_only','source_commit':'4d7efc7085786c897fc0c50f7151a0ae7e62f0c2','source_prefix':'prototypes/mygame-animation-studio/','authority_warning':'These are v3 authored drawing times and E screen-space anchors, not recovered canonical balance. Claude A must re-author anchors for the74px code-drawn art. Frame counts are references, not requirements.','anchor_coordinates':'Source art texels relative to the per-view foot pivot; positiveX right, positiveY down. They are not world collision coordinates.','characters':characters,'anchor_sources':anchor_provenance}
(ROOT/'legacy-east-animation-reference.json').write_text(json.dumps(output,indent=2)+'\n')
print(json.dumps({'characters':len(characters),'clips':sum(len(c['clips']) for c in characters.values()),'poses':sum(c['pose_count'] for c in characters.values()),'validation':'duration lengths, finite positive timing, release bounds, full attachment tracks and published totals passed'}))
