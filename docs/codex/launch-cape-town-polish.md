# Launch Cape town polish — Y15/r1

MyGame · slot=prism · ASSIGN [6471716660](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6471716660), following Claude A’s [priority brief](https://github.com/rempemat-eng/appify/issues/149#issuecomment-6471345306).

Base and integration target: `claude-a/continent-v53@4984438d09b5fe1333d3e6ea6e6ee82be2bdc908` (PR303). This is a direct JSON placement proposal for review.

## Existing systems and the change

The existing `towns55.launch_cape` places the six works buildings and pad. `town_plans.py` exports the plan; `scripts/review/town_plan.py` checks it against `blockout-v55.json`. The blockout README’s counting, detached frontage, theme and soft-grid requirements remain authoritative. The baseline checker passes with a count warning: three counted buildings against a 4–8 guide.

Add two detached staff cottages and one workshop at the northern entrance on the existing Pad Road. Count changes **3 → 6**, fronts **6 → 9**; the three existing excluded landmarks retain their records and placement reasons. The cottages use the existing `towns55.BLD` cottage range 56–80 × 40–48 world pixels (each new footprint is 64 × 48). The workshop is 104 × 56 within the existing 88–120 × 56–72 range. All coordinates, doors and rear garden/yard plots are on the existing eight-pixel grid. No street or route is added or moved.

The original six building records are byte-equivalent after JSON parsing. Streets, arrival, terrain/water/barriers, pad district, theme, landmarks, ground, yards, residents and routines remain unchanged. Only the new homes’ district, works membership/mix, count/front total, cottage size-table entry, northern footprint bound and derived screen extent are updated. Occupants are unnamed staff roles with individual residents/workers and routines explicitly unauthored.

## Buffer and inset

[The inset](launch-cape-town-inset.svg) is an inspected source-coordinate diagnostic, not game artwork or visual approval. It draws the unchanged terrain and street bands, existing buildings in blue, additions in orange, plots, door cells and the existing pad reference point. There was no committed Launch Cape inset to reuse.

All additions end at or north of world y=5952; both houses end at or north of y=5880. The nearest new house edge is 575 world pixels from the existing pad reference `(12085,6455)`; the workshop edge is 503 pixels away. These are measured distances to a point, **not** a safety threshold, pad boundary or approved clearance. No pad, apron or buffer terrain is changed. The README’s older “nearest house 770 px” description predates these proposed houses; Claude A must review the new placement and reconcile that prose if accepting it. No new safety/gameplay rule is proposed.

The SVG was inspected through a Pillow rendering of its exact rect/polyline/circle/text primitives. Adjacent equal-colour terrain cells are coalesced into horizontal rectangles; the before/after raster pixels are identical. Its pad circle identifies only the reference point. It does not depict the pad/apron footprint, cliff tiers, final rendering, interiors or gameplay scale.

## Integration responsibility and limits

This step changes only `towns/launch-cape.json` and these two documentation files. It does not edit the shared generator/exporter, town checker, package/lock files, runtime, Player, art or other towns. **Regenerating with the unchanged exporter would overwrite this proposal.** Claude A must adopt/preserve the accepted placements in the generator before regeneration and review the actual terrain tiers, works access and pad separation. No generator reproducibility, whole-world export, art, device, live-runtime or resident-routine acceptance is claimed. Existing theme placeholders and rules are preserved.

## Validation

`python3 scripts/review/town_plan.py --town launch-cape` passes: six counted buildings, three streets, one arrival, zero blocks/dead ends, 1.2 × 3.9 screens. The initial workshop door was four cells from its faced street; moving the workshop eight pixels west corrected that actual failure. The initial local SVG preview encountered an empty text node; the preview renderer was corrected and inspected successfully. Neither failed attempt is a pass.

The focused audit below checks the original records/contracts, exact count/IDs, documented forms, geometry bounds, dry land, street/plot/building separation and district updates, and calls the real checker. Run from the repository root with the actual base commit available. It does not infer a terrain tier or safety threshold from the simplified terrain grid.

```python
import json,subprocess,sys,math
from pathlib import Path
import numpy as np
root=Path.cwd();sys.path.insert(0,str(root/'scripts/review'));import town_plan as t
rel='docs/vision/research/blockout/towns/launch-cape.json';base=json.loads(subprocess.check_output(['git','show','4984438d09b5fe1333d3e6ea6e6ee82be2bdc908:'+rel],cwd=root));p=json.loads((root/rel).read_text())
changed={k for k in p if p[k]!=base[k]};assert changed=={'buildings','buildings_counted','fronts','size_table_px','districts','footprint_px','game_layout'},changed
assert p['buildings'][:6]==base['buildings'];assert len(p['buildings'])==9;assert len({b['id'] for b in p['buildings']})==9
for k in ('streets','arrivals','terrain','site','theme','features','landmarks','residents','routines','outskirts','squares','open_uses','lifted','ground'):assert p[k]==base[k],k
assert p['size_table_px']=={**base['size_table_px'],'cottage':[[56,80],[40,48]]}
assert sum(b['counts_as'] for b in p['buildings'])==p['buildings_counted']==6;assert p['fronts']==len(p['buildings'])==9
assert p['districts'][0]==base['districts'][0] and p['districts'][2]==base['districts'][2]
assert p['districts'][1]=={**base['districts'][1],'buildings':base['districts'][1]['buildings']+['launch-cape-b009'],'mix':{**base['districts'][1]['mix'],'workshop':3}}
assert p['game_layout']=={**base['game_layout'],'screens':[1.2,3.9]}
ter=t.rle_decode(p['terrain']['rows'],79);c0,r0,w,h=p['terrain']['box_cells'];net=np.zeros((h,w),bool)
for st in p['streets']:net|=t.band(st['vertices_px'],st['width_cells'],'euclid' if st['class']=='arrival' else 'cheb',(c0,r0,w,h))
rects=[]
for b in p['buildings']:
 c,r,bw,bh=b['footprint_cells'];assert b['rect_px']==[v*8 for v in (c,r,bw,bh)]
 if b in p['buildings'][6:]:
  assert c>=c0 and r>=r0 and c+bw<=c0+w and r+bh<=r0+h
  assert set(ter[r-r0:r-r0+bh,c-c0:c-c0+bw].flatten())<=set('.g')
 rects.append((b['id'],(c,r,bw,bh)))
for b in p['buildings'][6:]:
 c,r,bw,bh=b['plot_cells'];assert c>=c0 and r>=r0 and c+bw<=c0+w and r+bh<=r0+h
 assert set(ter[r-r0:r-r0+bh,c-c0:c-c0+bw].flatten())<=set('.g')
 assert not net[r-r0:r-r0+bh,c-c0:c-c0+bw].any()
 rects.append((b['id']+'-plot',(c,r,bw,bh)))
for i,(name,(x,y,w,h)) in enumerate(rects):
 for other,(a,b,c,d) in rects[i+1:]:assert not (x<a+c and x+w>a and y<b+d and y+h>b),(name,other)
# Measurement to the existing reference point, not a pad perimeter or safety threshold.
for b in p['buildings'][6:]:
 x,y,w,h=b['rect_px'];dist=math.hypot(max(x-12085,12085-x-w,0),max(y-6455,6455-y-h,0));print(b['id'],b['rect_px'],'point_distance_px',round(dist,3))
bo=json.loads((root/'docs/vision/research/blockout/blockout-v55.json').read_text());fails,notes,count=t.check_plan(p,bo);assert not fails,fails
print('PASS: original records/routes/terrain/theme preserved; exact count, IDs, forms, footprint/plot bounds, land, street/rectangle separation, district references and actual checker')
```

Required final-source gates: `npm run verify` (includes kit checks, zero lint warnings, web and iOS exports) and `npm run check:art-repro`, run serially with source guards and durable logs/exits. Exact published head/tree and final outcomes belong in the same remote checkpoint and PR handoff, not a claim based on partial output. No Godot/runtime source changed, so no new Godot suite is required for this offline JSON proposal. Matching hosted checks and their filters must be inspected after readiness; skips are not passes.
