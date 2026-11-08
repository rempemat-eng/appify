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
        retired={'crossroads':{12,14,15,16,17,18,19,20,21,22,28,29,30,34,36},'neon-harbour':set()}   # round 10 (Matt, 8 Nov): the cross thins out
        for pid,expected in towns.RETAINED.items():
            P=json.loads((BLOCKOUT/f'towns/{pid}.json').read_text())
            inventory=towns.FEEDBACK_BUILDINGS[pid]
            source=[(int(b['id'].rsplit('-b',1)[1]),b['form'],*b['rect_px'][2:],b.get('bays',[])) for b in P['buildings']]
            self.assertEqual(inventory,[r for r in source if r[0] not in retired[pid]])
            count=sum(0 if f in plans.LANDMARK_FORMS or towns.TYPE_OF.get(f,f) in plans.LANDMARK_TYPES else max(1,(len(b)+4)//5) for _,f,_,_,b in inventory)
            self.assertEqual(count,expected)

    def test_actual_crossroads_authoring_retains_all_fixed_and_street_front_buildings(self):
        # Actual authoring/physics on a bounded dry fixture; no world/noise/render.
        from types import SimpleNamespace
        shape=(560,920);T=terrain(shape)
        T['route_px']={'Valley lane south':[(6256,3808),(6256,4320)],
                       'Foothill Road':[(7240,3320),(7240,3480)]}
        fixed,_=towns.crossroads_plan(str(ROOT))
        with patch.multiple(g,H=shape[0],W=shape[1]), patch.multiple(towns,H=shape[0],W=shape[1]):
            town=towns._feedback_crossroads(T,SimpleNamespace(ROOT=str(ROOT)))
        self.assertEqual(len(town.buildings),towns.RETAINED['crossroads'])
        self.assertEqual({b['layout_id'] for b in town.buildings},{f'crossroads-b{r[0]:03d}' for r in towns.FEEDBACK_BUILDINGS['crossroads']})
        self.assertEqual([(b['x'],b['y'],b['w'],b['h']) for b in town.buildings[:7]],
                         [tuple(b[:4]) for b in fixed])
        occupied=np.zeros(shape,bool)
        for b in town.buildings:
            x,y,w,h=(b[k]//8 for k in ('x','y','w','h'))
            self.assertFalse(occupied[y:y+h,x:x+w].any(),b['layout_id'])
            occupied[y:y+h,x:x+w]=True
            self.assertFalse(np.isin(T['K'][y:y+h,x:x+w],plans.WATER_K+plans.BARRIER_K).any(),b['layout_id'])
            if not b.get('plan'):
                self.assertFalse(T['street'][y:y+h,x:x+w].any(),b['layout_id'])

    def test_actual_crossroads_fronts_fit_authored_sleepwater_corridor(self):
        # Synthetic inherited reach + actual authored v56 diversion, not real world terrain.
        from types import SimpleNamespace
        shape=(560,920);T=terrain(shape);yy,xx=np.mgrid[:shape[0],:shape[1]]
        T['route_px']={'Valley lane south':[(6256,3808),(6256,4320)],
                       'Foothill Road':[(7240,3320),(7240,3480)]}
        inherited=[(6256,3040),(6256,3120),(6280,3320),(6336,3540),(6352,3740),
                   (6384,3928),(6400,4056),(6384,4240),(6352,4448)]
        zone=json.loads((ROOT/'game/data/plans/crossroads.json').read_text())
        ox,oy=zone['origin_on_canvas'];_,_,zw,zh=zone['box']
        with patch.multiple(g,H=shape[0],W=shape[1],PX=xx*8+4,PY=yy*8+4), patch.multiple(towns,H=shape[0],W=shape[1]):
            # Match the authored 24px channel; assert the synthetic source is connected first.
            old=world.G._orig_line_mask(inherited,24);self.assertEqual(ndi.label(old)[1],1)
            T['K'][old]='river';T['water'][old]=True
            T['barriers']['river']=old.copy();T['river_masks']={'the Sleepwater':old.copy()}
            T['river_px']={'the Sleepwater':inherited}
            rec=world.feedback_river(T,world.CROSSROADS_RIVER,(ox,oy,ox+zw,oy+zh))
            self.assertEqual(ndi.label(T['river_masks']['the Sleepwater'])[1],1)
            town=towns._feedback_crossroads(T,SimpleNamespace(ROOT=str(ROOT)))
        self.assertEqual(rec['zone_water_cells'],0)
        self.assertEqual(len(town.buildings),towns.RETAINED['crossroads'])
        self.assertEqual({b['layout_id'] for b in town.buildings},{f'crossroads-b{r[0]:03d}' for r in towns.FEEDBACK_BUILDINGS['crossroads']})
        self.assertEqual(ndi.label(T['river_masks']['the Sleepwater'])[1],1)
        occupied=np.zeros(shape,bool)
        for b in town.buildings:
            x,y,w,h=(b[k]//8 for k in ('x','y','w','h'))
            self.assertFalse(np.isin(T['K'][y:y+h,x:x+w],plans.WATER_K+plans.BARRIER_K).any(),b['layout_id'])
            self.assertFalse(occupied[y:y+h,x:x+w].any(),b['layout_id']);occupied[y:y+h,x:x+w]=True
            if not b.get('plan'):self.assertFalse(T['street'][y:y+h,x:x+w].any(),b['layout_id'])
        # Street bridges are allowed; buildings cannot consume the actual channel.
        self.assertFalse(occupied[T['river_masks']['the Sleepwater']].any())
        self.assertTrue(np.isin(T['K'][T['river_masks']['the Sleepwater']],plans.WATER_K+['bridge']).all())

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
            towns._feedback_rows(t,[(1,'row_house',64,32,[])],[('x',160,64,448,-1,'frontage')])   # 2 Nov: refused -> deferred, logged
            self.assertEqual(t.buildings,[]);self.assertTrue(T.get('hand_fail'))
            self.assertEqual([d['id'] for d in t.deferred_fill],['neon-harbour-b001'])
            self.assertIn('terrain and occupancy fit',t.deferred_fill[0]['reason'])

    def test_actual_frontage_refuses_impassable_or_reserved_ground(self):
        # These are real Town.hand/free refusals, with no checker or method stub.
        for kind in ('river','cliff','road','taken','keepout'):
            with self.subTest(kind=kind), patch.multiple(towns,H=48,W=64):
                T=terrain();t=towns.Town(T,'Crossroads',(200,200),'large',(30,45),'fixture','fixture',seed=101)
                if kind in ('taken','keepout'):
                    T[kind][:20,:]=True
                else:
                    T['K'][:20,:]=kind
                towns._feedback_rows(t,[(8,'row_house',80,24,[])],[('x',160,64,448,-1,'reserved frontage')])   # refused -> deferred, never forced
                self.assertEqual(t.buildings,[])
                self.assertEqual([d['id'] for d in t.deferred_fill],['crossroads-b008'])
        with patch.multiple(towns,H=48,W=64):
            T=terrain();t=towns.Town(T,'Crossroads',(200,200),'large',(30,45),'fixture','fixture',seed=101)
            self.assertFalse(t.hand(-8,64,48,48,'house'))
            self.assertEqual(t.buildings,[])

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
        P={'crossroads':{'buildings_counted':towns.RETAINED['crossroads'],'buildings':[b]},'neon-harbour':{'buildings_counted':72,'buildings':[]}}
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
           for pid,count in [('crossroads',towns.RETAINED['crossroads']),('neon-harbour',71),('other-town',3)]}
        T['K'][1,1]='river'
        checker=plans.TW._review()
        with patch.object(checker,'check_plan',side_effect=[(['original-one'],[],towns.RETAINED['crossroads']),(['original-two'],[],71),(['original-three'],[],3)]), patch('builtins.print'):
            out=world.feedback_plan_checks(T,P)
        self.assertTrue(set(P).issubset(out))
        self.assertTrue(all(not q['pass'] for q in out.values()))
        for pid,n in [('crossroads','one'),('neon-harbour','two'),('other-town','three')]:
            self.assertIn('original-'+n,out[pid]['failures'])
            self.assertTrue(any('literal water/barrier' in f for f in out[pid]['failures']))
        self.assertIn('retained_count: 71 != 72',out['neon-harbour']['failures'])

    def test_report_refuses_missing_target_missing_other_and_all_pass_subset(self):
        all_ids=set(world.EXPECTED_TOWN_PLANS)     # 2 Nov: Canalside and Glintside are districts of Neon Harbour now
        self.assertEqual(len(all_ids),19)
        self.assertTrue({p.stem for p in (BLOCKOUT/'towns').glob('*.json')} - all_ids == {'canalside','glintside'})
        checker=plans.TW._review()
        for missing in ({'crossroads'},{'halcyon-row'},all_ids-{'crossroads','neon-harbour'}):
            with self.subTest(missing=sorted(missing)):
                T=terrain((8,8));T['route_px']={}
                provided={pid:{'terrain':{'box_cells':[0,0,8,8],'rows':[]},
                           'buildings_counted':dict(towns.RETAINED).get(pid,3),'buildings':[]}
                          for pid in all_ids-missing}
                with patch.object(checker,'check_plan',return_value=([],[],3)),patch('builtins.print'):
                    out=world.feedback_plan_checks(T,provided)
                self.assertEqual(set(out),all_ids)
                for pid in missing:
                    self.assertFalse(out[pid]['pass'])
                    self.assertTrue(any('missing_plan' in f for f in out[pid]['failures']))
                self.assertTrue(any(not q['pass'] for q in out.values()))

    def test_report_refuses_unexpected_town_identity(self):
        T=terrain((8,8));T['route_px']={}
        P={'invented-town':{'terrain':{'box_cells':[0,0,8,8],'rows':[]},'buildings_counted':3,'buildings':[]}}
        with patch.object(plans.TW._review(),'check_plan',return_value=([],[],3)),patch('builtins.print'):
            out=world.feedback_plan_checks(T,P)
        self.assertFalse(out['invented-town']['pass'])
        self.assertTrue(any('unexpected_plan' in f for f in out['invented-town']['failures']))

    def test_map_state_reads_only_the_selected_revision_stats(self):
        T=terrain((8,8));T.update(sea=~T['land'],FRAME=np.zeros((8,8),bool),
            crater_mask=np.zeros((8,8),bool),craters={},river_px={},delta=[])
        T['route_px']={'the Northway (closed)':[]}
        for revision in ('v55','v56'):
            with self.subTest(revision=revision), patch.multiple(world,REVISION=revision,
                    PLAN_DIRECTORY='towns-v56' if revision=='v56' else 'towns'), patch.object(
                    g,'colour',return_value=np.zeros((8,8,3),np.uint8)):
                marker=[{'id':'retained-farm'}]
                S={'T':T,'t':np.zeros((8,8),int),'res':{},'town_rec':{},'plans':{},
                   'stats':{'v53':{'hero':{}},revision:{'farms':marker,'physical_checks':{'fixture':{'pass':False}}}}}
                out=world.map_state(S)
                self.assertEqual(out['farms'],marker)
                self.assertEqual(out['revision'],revision)
                self.assertEqual(out['physical_checks'],{'fixture':{'pass':False}} if revision=='v56' else None)

    def test_v56_plan_writer_preserves_historical_town_files(self):
        T=terrain((8,8));P={'terrain':{'box_cells':[0,0,4,4],'rows':[]}}
        with tempfile.TemporaryDirectory() as tmp:
            folder=Path(tmp);(folder/'towns').mkdir();old=folder/'towns/crossroads.json';old.write_text('historical sentinel')
            with patch.multiple(world,DATA=tmp,PLAN_DIRECTORY='towns-v56'):
                world.write_plans({'T':T,'plans':{'crossroads':P}})
            self.assertEqual(old.read_text(),'historical sentinel');self.assertTrue((folder/'towns-v56/crossroads.json').exists())


def relief_scene():
    """A grown-frame stand-in for grow56.relief: a high back range with plateau snowfields across the whole top, and the
    world's ice below it (rows inside the world, north of y 700), so continuous snow and ice cross every band boundary."""
    import grow56 as GR
    from map53 import load_palette
    R, ink = load_palette(str(ROOT))
    Hc, Wc = 130, 150
    rows = np.arange(Hc)[:, None].astype(np.float32); cols = np.arange(Wc)[None, :].astype(np.float32)
    H = np.where(rows < 70, 1.05 - 0.004 * rows + 0.03 * np.sin(cols / 7.0) * np.cos(rows / 9.0), 0.0).astype(np.float32)
    H = np.broadcast_to(H, (Hc, Wc)).copy()
    plat = np.broadcast_to(np.where(rows < 60, 1.0, 0.0), (Hc, Wc)).astype(np.float32).copy()
    cid = {'rock': 1, 'crag': 2, 'glacier': 3, 'snow': 4, 'meadow': 0}
    cgx = np.zeros((Hc, Wc), np.int16)
    cgx[60:122, 12:138] = cid["glacier"]                             # the ice runs on below the snow
    cgx[90:110, 60:90] = cid['snow']
    Sx = {'h': (0.3 + 0.002 * rows + 0.0 * cols).astype(np.float32), 'vol_mask': None}
    GR._RANGE[id(Sx)] = {'H': H, 'Hs': ndi.gaussian_filter(H, 1.5), 'plat': plat}
    return GR, Sx, R, ink, cgx, cid, Hc, Wc


class Standing(unittest.TestCase):
    """Art director, 4 Nov: nothing may stand on a rail line, a road, a river or water (town-checks, every v56 town)."""
    def plan(self, rects):
        return {'buildings': [{'id': f'x-b{i:03d}', 'form': 'house', 'footprint_cells': list(r)} for i, r in enumerate(rects, 1)]}

    def test_rail_road_river_and_water_are_findings(self):
        shape = (40, 60); K = np.full(shape, 'meadow', dtype=object); K[30:34, 40:50] = 'creek'
        rail = np.zeros(shape, bool); rail[10, :] = True
        lines = {'the rail line (test)': rail}
        P = self.plan([(2, 8, 4, 4), (42, 29, 4, 3), (20, 20, 4, 4)])
        out = world.standing_failures(K, P, lines)
        self.assertEqual(len(out), 2)
        self.assertIn('x-b001 (house) stands on the rail line (test)', out[0])
        self.assertIn('x-b002 (house) stands on creek water', out[1])

    def test_actual_towns_stand_clear(self):
        report = json.loads((BLOCKOUT / 'town-checks-v56.json').read_text())
        self.assertEqual(set(report), world.EXPECTED_TOWN_PLANS)
        for pid, r in report.items():
            self.assertEqual([f for f in r['failures'] if f.startswith('standing')], [], pid)


class LeaderLines(unittest.TestCase):
    """Art director, 4 Nov: a label's leader line never crosses a building."""
    def test_leader_goes_round_a_building(self):
        import math
        from PIL import Image, ImageDraw, ImageFont
        import map53
        d = ImageDraw.Draw(Image.new('RGBA', (400, 400)))
        font = ImageFont.load_default()
        pl = map53.Placer(d, 400, 400)
        pl.reserve((150, 150, 250, 250))                              # the near spots round the icon are taken
        house = (205, 185, 240, 215); pl.leader_block = [house]      # a building just east of the icon
        b = pl.put((200, 200), 'Palm Spring', font, (0, 0, 0), (255, 255, 255), [(0, 0, 'mm')], leader=[80])
        self.assertIsNotNone(b)
        ex, ey = min(max(200, b[0]), b[2]), min(max(200, b[1]), b[3])
        self.assertFalse(map53.seg_hits_box((200, 200), (ex, ey), house))
        self.assertTrue(map53.seg_hits_box((200, 200), (260, 200), house))
        self.assertFalse(map53.seg_hits_box((200, 200), (140, 200), house))


class CityLighting(unittest.TestCase):
    """Round 10 (Matt, 8 Nov: "think critically what a cool city would be"): neon on one strip and a few named arteries."""
    def plan(self, lit):
        sts = [{'id': f's{i}', 'class': 'side', 'vertices_px': [[0, i * 100], [1000, i * 100]]} for i in range(10)]
        for i, L in lit.items():
            sts[i]['lighting'] = L
        return {'streets': sts}

    def test_lighting_rules(self):
        sys.path.insert(0, str(ROOT / 'scripts/review'))
        import town_plan
        strip = {'kind': 'strip', 'name': 'the Lantern Mile'}; art = {'kind': 'artery', 'name': 'the Spine'}
        self.assertEqual(town_plan.lighting_failures(self.plan({0: strip, 1: art, 2: art})), [])
        self.assertTrue(any('neon strips' in f for f in town_plan.lighting_failures(self.plan({1: art, 2: art}))))
        self.assertTrue(any('are lit' in f for f in town_plan.lighting_failures(self.plan({i: art for i in range(1, 8)} | {0: strip}))))
        self.assertTrue(any('unnamed' in f for f in town_plan.lighting_failures(self.plan({0: strip, 1: {'kind': 'artery'}, 2: art}))))

    def test_actual_neon_is_lit_on_the_strip_and_arteries(self):
        P = json.loads((BLOCKOUT / 'towns-v56/neon-harbour.json').read_text())
        kinds = {st['lighting']['kind'] for st in P['streets'] if st.get('lighting')}
        self.assertEqual(kinds, {'strip', 'artery'})
        sys.path.insert(0, str(ROOT / 'scripts/review'))
        import town_plan
        self.assertEqual(town_plan.lighting_failures(P), [])


class ReliefBands(unittest.TestCase):
    """grow56.relief draws in bands of rows; the result must not depend on where the bands fall."""

    def check(self, k, bands):
        from PIL import Image
        GR, Sx, R, ink, cgx, cid, Hc, Wc = relief_scene()
        Wi, Hi = int(Wc * 8 * k), int(Hc * 8 * k)
        base = Image.fromarray(np.full((Hi, Wi, 3), (120, 140, 90), np.uint8))
        whole, _ = GR.relief(base, Sx, R, ink, k, {}, [], cgx=cgx, cid=cid, band=Hi + 1)
        whole = np.asarray(whole)
        w16 = whole.astype(np.int16)
        snow = (w16.min(-1) >= 140) & (w16[..., 2] >= w16[..., 0] - 2)          # snow and ice: pale, not warm
        self.assertGreater(snow.mean(), 0.2, 'the scene must hold snow and ice')
        for band in bands:
            self.assertLess(band, Hi)
            cut = list(range(band, Hi, band))
            self.assertTrue(all(snow[r - 4:r + 4].mean() > 0.1 for r in cut), 'snow or ice must cross every band boundary')
            got = np.asarray(GR.relief(base, Sx, R, ink, k, {}, [], cgx=cgx, cid=cid, band=band)[0])
            diff = np.argwhere(np.any(got != whole, -1))
            self.assertEqual(len(diff), 0, f'k {k:.4f} band {band}: {len(diff)} pixels differ, first at {diff[:3].tolist()}')

    def test_bands_match_one_pass_at_3840(self):
        self.check(2160 / 7744, (64, 97, 150))

    def test_bands_match_one_pass_at_5760(self):
        self.check(3240 / 7744, (64, 101, 180))


if __name__=='__main__':unittest.main()
