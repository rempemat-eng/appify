"""Check legacy references; optionally cross-check an explicitly supplied sheet ZIP."""
from pathlib import Path
import argparse,hashlib,json,math,zipfile
root=Path(__file__).resolve().parent
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--archive',type=Path,help='Existing delivered MyGame_All_Character_Animation_Sheets.zip; no PNG is decoded')
parser.add_argument('--report',type=Path,default=root/'validation.json')
args=parser.parse_args()
reference=json.loads((root/'legacy-east-animation-reference.json').read_text())
provenance=json.loads((root/'source-provenance.json').read_text())
checks=0
for record in provenance['records']:
 raw=(root/'source'/record['path']).read_bytes()
 assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==record['git_blob_sha'],record['path'];checks+=1
frames=clips=0
for char,data in reference['characters'].items():
 assert data['view']=='E' and data['pose_count']==sum(d['frame_count'] for d in data['clips'].values());checks+=1
 for name,clip in data['clips'].items():
  assert len(clip['durations'])==clip['frame_count'] and all(math.isfinite(t) and t>0 for t in clip['durations']);checks+=1
  assert math.isclose(clip['duration'],sum(clip['durations']),rel_tol=1e-12,abs_tol=1e-12);checks+=1
  if clip['release_frame'] is not None:
   assert 0<=clip['release_frame']<clip['frame_count'] and math.isclose(clip['release_time'],sum(clip['durations'][:clip['release_frame']]),rel_tol=1e-12,abs_tol=1e-12);checks+=1
  if 'hand_anchors' in clip:assert len(clip['hand_anchors'])==clip['frame_count'];checks+=1
  for field in ['release_anchor','hand_anchors','thruster_anchors']:
   values=([clip[field]] if field=='release_anchor' else clip[field]) if field in clip else []
   for point in values:assert len(point)==2 and all(isinstance(v,(int,float)) and math.isfinite(v) for v in point);checks+=1
  clips+=1;frames+=clip['frame_count']
assert len(reference['characters'])==14 and clips==239 and frames==2135;checks+=1
archive_data=None
if args.archive is not None:
 archive=args.archive.resolve()
 expected='f8d69a4b25d998377bc33aa39f94bce1ccdc104b3f7e73967273bcd27bb2a6a3'
 actual=hashlib.sha256(archive.read_bytes()).hexdigest();assert actual==expected;checks+=1
 with zipfile.ZipFile(archive) as z:
  assert z.testzip() is None;checks+=1
  for char,data in reference['characters'].items():
   sheet=json.loads(z.read(f'MyGame_Animation_Sheets/{char}.json'))
   assert sheet['view']==data['view'] and sheet['frame_size']==data['frame_size'] and sheet['foot_pivot']==data['foot_pivot'];checks+=1
   assert sheet['pose_count']==data['pose_count']==len(sheet['frames']);checks+=1
   groups={}
   for frame in sheet['frames']:groups.setdefault(frame['clip'],[]).append(frame)
   assert set(groups)==set(data['clips']);checks+=1
   for name,clip in data['clips'].items():
    stored=groups[name];assert len(stored)==clip['frame_count']==len(clip['durations']);checks+=1
    for index,(frame,duration) in enumerate(zip(stored,clip['durations'])):
     assert frame['index']==index and math.isclose(frame['duration_seconds'],duration,rel_tol=1e-12,abs_tol=1e-12);checks+=1
    if clip['release_frame'] is not None:
     assert math.isclose(clip['release_time'],sum(f['duration_seconds'] for f in stored[:clip['release_frame']]),rel_tol=1e-12,abs_tol=1e-12);checks+=1
    if 'hand_anchors' in clip:assert len(clip['hand_anchors'])==len(stored);checks+=1
 archive_data={'filename':archive.name,'sha256':actual,'zip_crc':'passed','metadata_comparison':'all14 sheets,239 clips and2135 reference drawings','png_decode':'none'}
mode='legacy_source_and_existing_archive' if archive_data else 'legacy_source_structural_only'
report={'status':'passed','mode':mode,'checks':checks,'source_git_blobs':len(provenance['records']),'source_commit':reference['source_commit'],'characters':len(reference['characters']),'clips':clips,'reference_drawings':frames,'existing_archive_check':archive_data,'scope':'Legacy E authoring timing, layout and attachment-track shape; no new art, engine port or canonical balance validation.','not_tested':['Godot4.7.2 or adopted plugin compatibility','new74px art or S/N/W anchors','formal JSON-schema validation: jsonschema dependency is not installed','new game/ implementation']}
if archive_data is None:report['not_tested'].append('Independent comparison with the existing delivered sheet archive: pass --archive PATH to include it')
args.report.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
