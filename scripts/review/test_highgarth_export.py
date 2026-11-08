"""Exercise the real town record exporter on authored town/road/terrain records."""
import copy,json,pathlib,sys
from types import SimpleNamespace
import numpy as np
ROOT=pathlib.Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'docs/vision/research/blockout'));import town_plans as tp

def inputs(pid='highgarth'):
 p=json.loads((ROOT/f'docs/vision/research/blockout/towns/{pid}.json').read_text());c,r,w,h=p['terrain']['box_cells'];H,W=r+h,c+w
 K=np.full((H,W),'meadow',dtype='<U12'); codes={'.':'barren','g':'meadow','r':'road','~':'tarn','#':'cliff','b':'bridge'}
 sys.path.insert(0,str(ROOT/'scripts/review'));import town_plan as checker
 rows=np.vectorize(codes.__getitem__)(checker.rle_decode(p['terrain']['rows'],w))
 K[r:r+h,c:c+w]=rows
 bs=[]
 for b in p['buildings']:
  x,y,bw,bh=b['rect_px']; raw={'x':x,'y':y,'w':bw,'h':bh,'use':b['type'],'form':b['form'],'faces':b['faces'],'door':b['door_cells'],'counted':b['counted']}
  if 'bays' in b:raw['bays']=copy.deepcopy(b['bays'])
  if 'plot_cells' in b:raw['plot']=list(b['plot_cells'])+[b['plot']]
  if b.get('from_zone_plan'):raw['plan']=True
  bs.append(raw)
 t=SimpleNamespace(name=p['name'],centre=[(p['footprint_px'][0]+p['footprint_px'][2])//2,(p['footprint_px'][1]+p['footprint_px'][3])//2],purpose=p['site']['reason'],setting=p['site']['terrain'],neighbourhoods=[(d['name'],d.get('declared',''),*d['centre_px']) for d in p['districts'] if 'centre_px' in d],buildings=bs,outskirts=copy.deepcopy(p['outskirts']),gathering=[(g['name'],*g['xy_px']) for g in p['gathering_places']],target=tuple(p['target']),size=p['size_note'],style=p.get('style'))
 elems=[];ids=np.full((h,w),-1,dtype=int)
 for s in p['streets']:
  el=copy.deepcopy(s);el['kind']='arrival' if s['class']=='arrival' else 'street';el['mask']=checker.band([tuple(q) for q in s['vertices_px']],s['width_cells'],'euclid' if s.get('follows_route') else 'cheb',(c,r,w,h));ids[el['mask']]=len(elems);elems.append(el)
 return p,({'K':K,'tiers_pre':np.zeros((H,W),dtype=int),'levelled':[]},p['name'],pid,[t],SimpleNamespace(elems=elems,ids=ids),copy.deepcopy(p['arrivals']),(c,r,w,h),(slice(r,r+h),slice(c,c+w)),p['footprint_px'],[],None)


import unittest
from unittest.mock import patch

def differences(a,b,path=''):
    if type(a) is not type(b): return [path]
    if isinstance(a,dict):
        if a.keys()!=b.keys():return [path]
        return [p for k in a for p in differences(a[k],b[k],path+'/'+str(k))]
    if isinstance(a,list):
        if len(a)!=len(b):return [path]
        return [p for i,(x,y) in enumerate(zip(a,b)) for p in differences(x,y,path+'/'+str(i))]
    return [] if a==b else [path]

class HighgarthExport(unittest.TestCase):
    def test_real_record_retains_all_five_published_corrections(self):
        source,args=inputs();out=tp._record(*args)
        by={b['id']:b for b in out['buildings']}
        for ident,field in [('highgarth-b001','purpose'),('highgarth-b002','purpose'),('highgarth-b002','occupants'),('highgarth-b020','purpose')]:
            expected=next(b for b in source['buildings'] if b['id']==ident)[field]
            self.assertEqual(by[ident][field],expected)
        self.assertEqual(next(l for l in out['landmarks'] if l['building']=='highgarth-b003')['reason'],
                         next(l for l in source['landmarks'] if l['building']=='highgarth-b003')['reason'])
        self.assertEqual(len(out['buildings']),30);self.assertEqual(out['buildings_counted'],27)

    def test_only_five_exported_values_differ_from_generic_fallback(self):
        source,args=inputs();out=tp._record(*args)
        with patch.dict(tp.FORM_DESCRIPTIONS,{},clear=True): old=tp._record(*args)
        self.assertEqual(set(differences(old,out)),{'/buildings/0/purpose','/buildings/1/purpose',
            '/buildings/1/occupants','/buildings/19/purpose','/landmarks/2/reason'})
        self.assertEqual(out['buildings'][4]['purpose'],old['buildings'][4]['purpose'])
        self.assertEqual(source,json.loads((ROOT/'docs/vision/research/blockout/towns/highgarth.json').read_text()))

    def test_override_does_not_skip_the_generic_public_cycle(self):
        _,args=inputs();extra=copy.deepcopy(args[3][0].buildings[0]);extra['form']='hall'
        args[3][0].buildings.insert(1,extra);normal=tp._record(*args)
        with patch.dict(tp.FORM_DESCRIPTIONS,{},clear=True): old=tp._record(*args)
        self.assertEqual(normal['buildings'][1]['purpose'],old['buildings'][1]['purpose'])
        self.assertEqual(normal['buildings'][1]['purpose'],'the school')

    def test_another_real_town_is_byte_equivalent_to_legacy_fallback(self):
        _,args=inputs('gullwick');normal=tp._record(*args)
        with patch.dict(tp.FORM_DESCRIPTIONS,{},clear=True): old=tp._record(*args)
        self.assertEqual(json.dumps(normal,sort_keys=True),json.dumps(old,sort_keys=True))

    def test_highgarth_forms_do_not_override_another_town(self):
        _,args=inputs();args=list(args);args[2]='gullwick'
        normal=tp._record(*args)
        with patch.dict(tp.FORM_DESCRIPTIONS,{},clear=True): old=tp._record(*args)
        self.assertEqual(normal,old)
        self.assertEqual(normal['buildings'][1]['occupants'],'offices and the Company')

    def test_form_identity_survives_reordered_building_ids(self):
        _,args=inputs();args[3][0].buildings.reverse();out=tp._record(*args)
        by={b['form']:b for b in out['buildings']}
        self.assertEqual(by['temple_hall']['purpose'],'the temple hall')
        self.assertEqual(by['pagoda']['occupants'],'unassigned; X3 roles and routines deferred')
        self.assertEqual(by['bathhouse']['purpose'],'the hot spring bathhouse')
        keep=by['watchkeep'];self.assertEqual(next(l for l in out['landmarks'] if l['building']==keep['id'])['reason'],
            "on its stone base behind the tarn: the lord's watch faces the sealed north pass")

if __name__=='__main__':unittest.main()
