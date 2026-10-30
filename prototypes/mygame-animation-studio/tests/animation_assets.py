#!/usr/bin/env python3
"""Verify all delivered body drawings, native resources and atlas coordinates."""
from pathlib import Path
import hashlib
import json
import sys
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[1]
IDS=['bramble','morel','velvet','cairn','iona','tam','brine','pendle','mirra','ashe','clack','nix','rook','mote']
CLIPS=['idle','walk','primary','secondary','special','guard','hit','defeat','jump','stair_up','stair_down','dodge','powered_idle','powered_walk','powered_primary','powered_guard','powered_exit']


def run(available=False):
    results=[]
    for character in IDS:
        folder=ROOT/'assets/animated'/character
        if not (folder/'manifest.json').exists():
            if available:continue
            raise AssertionError(f'{character}: missing complete animation export')
        m=json.loads((folder/'manifest.json').read_text())
        assert set(m['clips'])==set(CLIPS+(['reload'] if character=='pendle' else []))
        size=[256,192] if character=='ashe' else [224,192] if character=='iona' else [192,192]
        pivot=[132,172] if character=='ashe' else [96,172]
        assert m['frame_size']==size and m['foot_pivot']==pivot
        assert abs(m['fit_factor']-1.0)<1e-6,(character,'model shrunk to fit a wide pose')
        hashes=set();count=0
        for clip,data in m['clips'].items():
            expected=16 if clip in ['walk','primary'] or character=='cairn' and clip=='secondary' else 4 if character=='cairn' and clip in ['hit','defeat'] else 7 if character=='velvet' and clip=='powered_exit' else 8
            assert data['frame_count']==expected,(character,clip,data['frame_count'])
            assert len(data['durations'])==expected and abs(sum(data['durations'])-data['duration'])<1e-7
            for record in data['frames']:
                path=ROOT/record['path'].removeprefix('res://');im=Image.open(path).convert('RGBA');a=np.asarray(im)
                assert list(im.size)==size
                assert set(np.unique(a[:,:,3])) <= {0,255}
                bounds=im.getbbox();assert bounds and bounds[0]>0 and bounds[1]>0 and bounds[2]<size[0] and bounds[3]<size[1],(character,clip,bounds)
                digest=hashlib.sha256(im.tobytes()).hexdigest()
                assert digest==record['sha256'] and digest not in hashes,(character,clip,'duplicate or changed drawing')
                hashes.add(digest);count+=1
            if data['release_frame'] is not None:
                assert abs(sum(data['durations'][:data['release_frame']])-data['release_time'])<1e-7
            if clip in ['primary','secondary','powered_primary']:
                assert len(data.get('release_anchor',[]))==2,(character,clip,'missing reviewed action anchor')
            if 'hand_anchors' in data:
                assert len(data['hand_anchors'])==expected and all(len(p)==2 and np.isfinite(p).all() for p in data['hand_anchors'])
            if clip in ['jump','stair_up','stair_down','dodge'] or character=='rook' and clip=='secondary':
                assert all(r.get('registration')=='per_frame_support_bottom; engine_owns_world_height' for r in data['frames'])
        if character=='brine':
            for clip in ['idle','primary','secondary','powered_primary']:
                data=m['clips'][clip]
                assert 'hand_anchors' in data,(character,clip,'tether must follow the visible gun')
                if data['release_frame'] is not None:assert data['hand_anchors'][data['release_frame']]==data['release_anchor']
        if character=='rook':assert m['clips']['secondary']['thruster_anchors']==[[-26,-59]]
        assert count==(160 if character=='pendle' else 151 if character=='velvet' else 152)
        resource=(folder/'frames.tres').read_text();assert resource.count('[ext_resource type="Texture2D"')==count
        atlas=Image.open(ROOT/f'animation-sheets/{character}.png').convert('RGBA')
        meta=json.loads((ROOT/f'animation-sheets/{character}.json').read_text())
        assert meta['pose_count']==count and atlas.size==(size[0]*8,((count+7)//8)*192)
        for frame in meta['frames']:
            crop=atlas.crop((frame['x'],frame['y'],frame['x']+size[0],frame['y']+size[1]))
            original=Image.open(folder/f'{frame["name"]}.png').convert('RGBA')
            assert crop.tobytes()==original.tobytes(),(character,frame['name'],'atlas differs from engine sprite')
        results.append({'id':character,'poses':count,'status':'passed'})
    if not available:assert len(results)==14
    print(json.dumps({'characters':len(results),'distinct_exported_poses':sum(r['poses'] for r in results),'results':results},indent=2))


if __name__=='__main__':run('--available' in sys.argv)

