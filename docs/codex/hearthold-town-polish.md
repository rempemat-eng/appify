# Hearthold town polish — Y15/r1

MyGame · slot=tempo · [ASSIGN6471953452](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6471953452), following [Claude A’s priority brief](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6471345306).

Base and integration target: `claude-a/continent-v53@4984438d09b5fe1333d3e6ea6e6ee82be2bdc908` (PR303).

## Existing systems and resulting proposal

The existing hand-authored `towns55.hearthold` owns the overview layout, `town_plans.py` exports it, and `scripts/review/town_plan.py` checks the plan against `blockout-v55.json`. This step follows that README’s current counting, detached-frontage, theme and eight-pixel soft-grid contracts. It extends the existing plan with three records, without rebuilding a generator or checker.

The original 32 buildings contribute 28 counted buildings and four excluded landmarks. Add one detached house and one detached cottage with rear yards in the lower town on Well Lane, plus one craft workshop at Smiths’ Row’s east end. Count becomes **31**, within the **30–45** guide; fronts become **35**. The existing house range is 80–104 × 48–64 world pixels, cottage 56–80 × 40–48, workshop 88–120 × 56–72. The additions are respectively 80 × 48, 72 × 48 and 88 × 56. No new form, size range or rule is introduced.

| New ID | Footprint (world x, y, width, depth) | Faces | Rear yard (cell x, y, width, depth) |
| --- | --- | --- | --- |
| hearthold-b033 | 2024, 5648, 80, 48 | hearthold-s09 / Well Lane | 251, 706, 2, 6 |
| hearthold-b034 | 2032, 5584, 72, 48 | hearthold-s09 / Well Lane | 252, 698, 2, 6 |
| hearthold-b035 | 2744, 5520, 88, 56 | hearthold-s06 / Smiths’ Row | 343, 697, 11, 2 |

Original building records/IDs, streets, arrivals, fortification including gate and sealed postern, terrain, theme, named yards/vines, landmarks, squares/open uses, residents and routines are unchanged. Only additive buildings and district membership/mixes, count/front totals, the east footprint bound and its derived screen extent change. Existing unnamed households/workers remain explicitly unauthored: no resident names, population numbers, trade assignment, clocks, rewards or routines are invented.

## Inset and integration

[The inset](hearthold-town-inset.svg) is a source-coordinate diagnostic. It shows the unchanged terrain and street bands, original building records in blue, additions in orange, plots and door cells. Its exact rect/polyline/text primitives were rasterized and inspected with Pillow. All IDs, the proposed additions and the separate legend are visible. The existing town PNG remains unchanged; this diagram is not a replacement or an art proposal.

This direct JSON proposal changes no shared generator/exporter, checker, package, lockfile, runtime, Player or art files. **The current generator/exporter would overwrite these additions on regeneration.** Claude A must review the proposed placements and preserve accepted records in the generator before regeneration. The terrain grid proves no simplified water/barrier/route overlap; it does not prove flat physical tiers, cliff clearance or gameplay-scale access. The workshop is near the eastern barrier; its actual slope/retaining needs require Claude A’s terrain review. No visual, art, device, runtime, whole-world or full Y15 approval is claimed.

## Validation

The actual town checker passes: **31 buildings, 18 streets, three arrivals, one gate, eight towers, five blocks and five reported dead ends, 2.6 × 3.9 screens**. Reported dead ends are inherited diagnostics, not newly accepted runtime routes. The original 28-count plan was within the checker’s warning tolerance; this step follows the newer explicit priority brief to reach the guide.

Focused audit below verifies exact original-record/contracts preservation, additive district changes, count/front/extent, new footprints and plots inside the terrain bounds, clear land and no street/building/plot/square/named-open-use encroachment. Exploratory read-only candidate queries rejected a route-overlapping cottage location and an eastern barrier location before authoring; neither was passed off as valid. Run from the repo root with the real base object available:

```python
import json,pathlib,subprocess,sys
import numpy as np
root=pathlib.Path.cwd();rel='docs/vision/research/blockout/towns/hearthold.json';p=json.loads((root/rel).read_text());base=json.loads(subprocess.check_output(['git','show','4984438d09b5fe1333d3e6ea6e6ee82be2bdc908:'+rel],text=True));sys.path.insert(0,str(root/'scripts/review'));import town_plan as t
changed={k for k in p if p[k]!=base[k]};assert changed=={'buildings','buildings_counted','fronts','districts','footprint_px','game_layout'},changed
assert len(p['buildings'])==35 and p['buildings'][:32]==base['buildings'];assert len({b['id'] for b in p['buildings']})==35
for k in ('streets','arrivals','terrain','site','theme','features','landmarks','residents','routines','outskirts','squares','open_uses','lifted','ground','fortification','size_table_px'):assert p[k]==base[k],k
assert p['buildings_counted']==sum(b['counts_as'] for b in p['buildings'])==31
assert p['fronts']==base['fronts']+3 and p['game_layout']=={**base['game_layout'],'screens':[2.6,3.9]}
for d in p['districts']:
 original=next(x for x in base['districts'] if x['id']==d['id']);new=[b for b in p['buildings'][32:] if b['district']==d['id']];expected=json.loads(json.dumps(original))
 for b in new:expected['buildings'].append(b['id']);expected['mix'][b['form']]=expected['mix'].get(b['form'],0)+1
 assert d==expected,d['id']
c0,r0,w,h=p['terrain']['box_cells'];a=t.rle_decode(p['terrain']['rows'],w);net=np.zeros((h,w),bool);rects=[]
for st in p['streets']:net|=t.band(st['vertices_px'],st['width_cells'],'euclid' if st['class']=='arrival' else 'cheb',(c0,r0,w,h))
for b in p['buildings']:
 c,r,bw,bh=b['footprint_cells'];assert b['rect_px']==[v*8 for v in (c,r,bw,bh)]
 for field in ('footprint_cells','plot_cells'):
  if b.get(field):rects.append((b['id']+':'+field,b[field]))
for b in p['buildings'][32:]:
 for field in ('footprint_cells','plot_cells'):
  c,r,bw,bh=b[field];assert c>=c0 and r>=r0 and c+bw<=c0+w and r+bh<=r0+h
  sl=(slice(r-r0,r-r0+bh),slice(c-c0,c-c0+bw));assert set(a[sl].flatten())<=set('.g');assert not net[sl].any()
  for name,(x,y,ww,hh) in rects:
   if name.startswith(b['id']):continue
   assert not(c<x+ww and c+bw>x and r<y+hh and r+bh>y),(b['id'],field,name)
  for o in p['outskirts']:
   x,y,xx,yy=o['box'];x,y,xx,yy=[v/8 for v in (x,y,xx,yy)];assert not(c<xx and c+bw>x and r<yy and r+bh>y),(b['id'],o['name'])
  for q in p['squares']+p['open_uses']:
   x,y,ww,hh=q['cells'];assert not(c<x+ww and c+bw>x and r<y+hh and r+bh>y),(b['id'],q['id'])
fails,notes,n=t.check_plan(p,json.loads((root/'docs/vision/research/blockout/blockout-v55.json').read_text()));assert not fails,fails
print('PASS exact original32/IDs/routes/walls/gates/postern/terrain/theme/landmarks/life/size-table preservation; additive district/count/front/extent checks; new footprints+plots bounds/land/street/building/plot/square/named-open-use separation; real checker31/18/3')
```

Required final frozen-source gates: `npm run verify` (includes kit checks, zero lint warnings, web and iOS exports) and `npm run check:art-repro`, serially with durable logs/exits/source guards. Final exact head/tree/base and collected outcomes are recorded in the remote checkpoint/PR handoff. No Godot/runtime source changes here, so no new Godot suite is required. Inspect the matching hosted workflow filters after readiness; a filtered-out workflow or draft skip is not a pass.
