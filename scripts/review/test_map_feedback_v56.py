"""Bounded v56 source controls; no continent build, renderer or engine."""
import copy
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[2]
BLOCKOUT = ROOT / 'docs/vision/research/blockout'
sys.path.insert(0, str(BLOCKOUT))
import geo5 as g
import geo55 as world
import town_plans as plans
import towns55 as towns


def terrain(shape=(48,64)):
    z=np.zeros(shape,bool)
    return {'K':np.full(shape,'meadow',dtype='<U12'), 'K0':np.full(shape,'meadow',dtype='<U12'),
            'h':np.zeros(shape),'tiers_pre':np.zeros(shape,int),'land':~z,'water':z.copy(),
            'taken':z.copy(),'street':z.copy(),'used':z.copy(),'keepout':z.copy(),
            'barrier':z.copy(),'hardbar':z.copy(),'slope':np.zeros(shape),'barriers':{},'route_px':{}}


class MapFeedbackV56(unittest.TestCase):
    def test_actual_crossroads_defect_and_retained_count_inventory(self):
        P=json.loads((BLOCKOUT/'towns/crossroads.json').read_text());c,r,w,h=P['terrain']['box_cells']
        rows=[''.join(ch*int(n or 1) for n,ch in re.findall(r'(\d*)([^\d])',row)) for row in P['terrain']['rows']]
        wet={}
        for b in P['buildings']:
            x,y,bw,bh=b['footprint_cells']
            n=sum(rows[yy-r][xx-c]=='~' for yy in range(y,y+bh) for xx in range(x,x+bw))
            if n:wet[b['id']]=n
        self.assertEqual(wet,{'crossroads-b001':5,'crossroads-b003':16,'crossroads-b007':6})
        for pid,expected in [('crossroads',40),('neon-harbour',72)]:
            P=json.loads((BLOCKOUT/f'towns/{pid}.json').read_text())
            inventory=towns.FEEDBACK_BUILDINGS[pid]
            self.assertEqual(inventory,[(int(b['id'].rsplit('-b',1)[1]),b['form'],*b['rect_px'][2:],b.get('bays',[])) for b in P['buildings']])
            count=sum(0 if f in plans.LANDMARK_FORMS or towns.TYPE_OF.get(f,f) in plans.LANDMARK_TYPES else max(1,(len(b)+4)//5) for _,f,_,_,b in inventory)
            self.assertEqual(count,expected)

    def test_channel_moves_ground_polyline_and_masks_together(self):
        T=terrain((48,48));yy,xx=np.mgrid[:48,:48]
        old=np.abs(xx*8+4-128)<12
        T['K'][old]='river';T['water'][old]=True;T['barriers']['river']=old.copy()
        T['river_masks']={'the Sleepwater':old.copy()}
        line=[(128,y) for y in range(0,385,16)];T['river_px']={'the Sleepwater':line}
        before=T['K'].copy()
        with patch.multiple(g,H=48,W=48,PX=xx*8+4,PY=yy*8+4):
            out=world.feedback_river(T,[(128,64),(240,88),(240,256),(128,288)],(88,112,192,224),corridor=(64,56,288,304))
        self.assertEqual(out['zone_water_cells'],0)
        self.assertFalse(np.isin(T['K'][14:28,11:24],plans.WATER_K).any())
        self.assertNotEqual(T['river_px']['the Sleepwater'],line)
        self.assertEqual(ndi.label(T['river_masks']['the Sleepwater'])[1],1)
        self.assertFalse(T['barriers']['river'][14:28,11:24].any())
        np.testing.assert_array_equal(before[:7],T['K'][:7]);np.testing.assert_array_equal(before[38:],T['K'][38:])
        self.assertGreater(out['retired_channel_cells'],0);self.assertGreater(out['new_channel_cells'],0)

    def test_channel_refuses_missing_join_and_crossing_built_zone(self):
        T=terrain((48,48));yy,xx=np.mgrid[:48,:48]
        T['river_masks']={'the Sleepwater':np.zeros((48,48),bool)};T['river_px']={'the Sleepwater':[(8,8),(8,16)]}
        with patch.multiple(g,H=48,W=48,PX=xx*8+4,PY=yy*8+4):
            with self.assertRaisesRegex(ValueError,'no inherited river'):
                world.feedback_river(T,[(128,64),(128,288)],(88,112,192,224),corridor=(64,56,288,304))
            T['river_px']['the Sleepwater']=[(128,y) for y in range(0,385,16)]
            with self.assertRaisesRegex(ValueError,'still crosses'):
                world.feedback_river(T,[(128,64),(128,288)],(88,112,192,224),corridor=(64,56,288,304))

    def test_frontage_uses_real_street_edge_and_refuses_water(self):
        yy,xx=np.mgrid[:48,:64]
        with patch.multiple(towns,H=48,W=64,PX=xx*8+4,PY=yy*8+4):
            T=terrain();t=towns.Town(T,'Neon Harbour: test',(200,200),'city district',(1,10),'fixture','fixture',seed=201)
            t.street([(32,160),(480,160)],'main',name='main')
            towns._feedback_rows(t,[(1,'house',80,48,[])],[('x',160,64,448,-1,'frontage')])
            b=t.buildings[0];self.assertEqual(b['y']+b['h'],136)
            self.assertEqual(b['layout_id'],'neon-harbour-b001')
            self.assertFalse(T['street'][b['y']//8:(b['y']+b['h'])//8,b['x']//8:(b['x']+b['w'])//8].any())
            T=terrain();T['K'][14:20,:]='river'
            t=towns.Town(T,'Neon Harbour: test',(200,200),'city district',(1,10),'fixture','fixture',seed=201)
            with self.assertRaisesRegex(ValueError,'cannot place'):
                towns._feedback_rows(t,[(1,'row_house',64,32,[])],[('x',160,64,448,-1,'frontage')])
            self.assertEqual(t.buildings,[]);self.assertTrue(T.get('hand_fail'))

    def test_target_restore_preserves_unrelated_ground_and_routes(self):
        T=terrain();boxes=[(64,64,160,160)]
        T['route_px']={n:[(8,8),(16,16)] for n in ('Quay Street','Old Bridges','Cape Road','Lull Road','Delta Road','Valley lane south')}
        saved=towns._feedback_snapshot(T,boxes);T['K'][8:20,8:20]='building';T['K'][30,30]='warehouse'
        T['route_px']['Quay Street']=[(80,80),(88,88)];T['route_px']['unrelated']=[(24,24),(32,32)]
        towns._feedback_restore(T,saved,boxes)
        self.assertTrue((T['K'][8:20,8:20]=='meadow').all());self.assertEqual(T['K'][30,30],'warehouse')
        self.assertEqual(T['route_px']['Quay Street'],[(8,8),(16,16)]);self.assertIn('unrelated',T['route_px'])

    def test_final_ground_checks_inherited_footprints_and_counts(self):
        T=terrain();b={'id':'crossroads-b001','from_zone_plan':True,'footprint_cells':[8,8,3,3]}
        P={'crossroads':{'buildings_counted':40,'buildings':[b]},'neon-harbour':{'buildings_counted':72,'buildings':[]}}
        world.feedback_checks(T,P)
        for kind in ('river','cliff'):
            T['K'][8,8]=kind
            with self.assertRaisesRegex(ValueError,'final water/barrier'):world.feedback_checks(T,P)
        T['K'][8,8]='meadow';P['crossroads']['buildings'].append(copy.deepcopy(b))
        with self.assertRaisesRegex(ValueError,'overlaps another'):world.feedback_checks(T,P)
        P['crossroads']['buildings']=[b];P['neon-harbour']['buildings_counted']=73
        with self.assertRaisesRegex(ValueError,'expected retained 72'):world.feedback_checks(T,P)

    def test_complete_report_retains_findings_for_every_town(self):
        T=terrain((8,8));T['route_px']={}
        P={pid:{'terrain':{'box_cells':[0,0,8,8],'rows':[]},'buildings_counted':count,
                'buildings':[{'id':pid+'-b001','footprint_cells':[1,1,2,2]}]}
           for pid,count in [('crossroads',40),('neon-harbour',71),('other-town',3)]}
        T['K'][1,1]='river'
        checker=plans.TW._review()
        with patch.object(checker,'check_plan',side_effect=[(['original-one'],[],40),(['original-two'],[],71),(['original-three'],[],3)]), patch('builtins.print'):
            out=world.feedback_plan_checks(T,P)
        self.assertEqual(set(out),set(P))
        self.assertTrue(all(not q['pass'] for q in out.values()))
        for pid,n in [('crossroads','one'),('neon-harbour','two'),('other-town','three')]:
            self.assertIn('original-'+n,out[pid]['failures'])
            self.assertTrue(any('literal water/barrier' in f for f in out[pid]['failures']))
        self.assertIn('retained_count: 71 != 72',out['neon-harbour']['failures'])

    def test_v56_plan_writer_preserves_historical_town_files(self):
        T=terrain((8,8));P={'terrain':{'box_cells':[0,0,4,4],'rows':[]}}
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp);(folder/'towns').mkdir();old=folder/'towns/crossroads.json';old.write_text('historical sentinel')
            with patch.multiple(world,DATA=tmp,PLAN_DIRECTORY='towns-v56'):
                world.write_plans({'T':T,'plans':{'crossroads':P}})
            self.assertEqual(old.read_text(),'historical sentinel');self.assertTrue((folder/'towns-v56/crossroads.json').exists())

if __name__=='__main__':unittest.main()
