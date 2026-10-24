#!/usr/bin/env python3
"""Register and pack authored sprite drawings; never create/interpolate poses.

The importer uses connected components so that a weapon protruding beyond a
nominal atlas cell is not cut off. Missing or merged bodies are hard errors.
Every strip uses one scale and ground baseline. Different source masters are
calibrated to the same character height before fitting the common game canvas.
"""
from __future__ import annotations
from pathlib import Path
from dataclasses import dataclass, replace
import argparse
import hashlib
import json
import math
import os
import numpy as np
from scipy import ndimage
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
IDS = ['bramble','morel','velvet','cairn','iona','tam','brine','pendle','mirra','ashe','clack','nix','rook','mote']
BASE_CLIPS = ['idle','walk','primary','secondary','special','guard','hit','defeat']
TRAVERSAL_CLIPS = ['jump','stair_up','stair_down','dodge']
POWERED_CLIPS = ['powered_idle','powered_walk','powered_primary','powered_guard','powered_exit']
CLIPS = BASE_CLIPS + TRAVERSAL_CLIPS + POWERED_CLIPS
SIZE = (192,192)
PIVOT = (96,172)
V3_ORDERS = {
    ('ashe','primary'):[0,1,2,3,4,5,6,8,9,10,11,12,13,14,15,7],
    ('mote','primary'):[0,1,2,3,4,5,6,8,9,10,11,12,13,14,7,15],
    ('bramble','powered_primary'):[0,1,2,3,5,4,6,7],
    ('morel','primary'):[0,1,2,7,6,3,5,4,8,9,10,11,12,13,14,15],
    ('velvet','primary'):[0,4,1,7,2,3,6,5,8,9,10,11,12,13,14,15],
    ('tam','primary'):[0,1,2,4,5,6,3,7,8,9,10,11,12,13,14,15],
    ('nix','powered_primary'):[0,1,2,3,6,4,5,7],
    ('mirra','powered_primary'):[0,5,3,1,2,4,6,7],
}
V3_RELEASES = {('ashe','primary'):7, ('bramble','powered_primary'):5, ('cairn','powered_primary'):5, ('nix','powered_primary'):5, ('brine','powered_primary'):3, ('mirra','powered_primary'):5}
RELEASE_ANCHORS = {
    ('clack','primary'):[56,-78], ('clack','powered_primary'):[41,-69],
    ('ashe','primary'):[100,-61],
}


@dataclass
class Part:
    image: Image.Image
    bounds: tuple[int,int,int,int]
    slot: int
    origin: tuple[float,float]
    main_area: int
    foot_y: float


def sha(image):
    return hashlib.sha256(image.tobytes()).hexdigest()


def save_png(image,path):
    """Interrupted export must never replace a complete atlas with half a PNG."""
    temporary=path.with_name(path.name+'.'+str(os.getpid())+'.tmp')
    try:
        image.save(temporary,format='PNG')
        temporary.replace(path)
    finally:
        if temporary.exists():temporary.unlink()


def cuts(mask, count, axis, body_centres=None):
    """Prefer a clear gap near each expected division, not a hard cell cut."""
    projection = mask.sum(axis=1 if axis == 0 else 0)
    length = len(projection)
    centres=None
    if body_centres is not None and len(body_centres)>=count:
        points=np.asarray(body_centres,dtype=float)
        centres=np.quantile(points,(np.arange(count)+.5)/count)
        for _ in range(30):
            groups=np.abs(points[:,None]-centres[None,:]).argmin(axis=1)
            updated=np.array([np.median(points[groups==i]) if (groups==i).any() else centres[i] for i in range(count)])
            updated.sort()
            if np.max(abs(updated-centres))<.01:break
            centres=updated
    result = [0]
    for n in range(1,count):
        target = float((centres[n-1]+centres[n])/2) if centres is not None else length*n/count
        radius=float((centres[n]-centres[n-1])*.28) if centres is not None else length/count*.25
        lo,hi = max(0,int(target-radius)),min(length,int(target+radius))
        band = projection[lo:hi]
        candidates = np.flatnonzero(band == band.min())+lo
        chosen = candidates[np.argmin(abs(candidates-target))]
        result.append(int(chosen))
    return result+[length]


def extract(path, columns, rows, wanted, body_rows=None):
    image = Image.open(path).convert('RGBA')
    rgba = np.asarray(image)
    opaque = rgba[:,:,3] >= 128
    labels,n = ndimage.label(opaque,np.ones((3,3)))
    counts = np.bincount(labels.ravel())
    boxes = ndimage.find_objects(labels)
    largest = sorted(counts[1:],reverse=True)[:columns*rows]
    if not largest:
        raise ValueError(f'{path.name}: transparent sheet')
    min_body = max(80,int(np.median(largest)*.30))
    main_boxes=[box for label,box in enumerate(boxes,1) if box is not None and counts[label]>=min_body]
    xs=cuts(opaque,columns,1,[(b[1].start+b[1].stop)/2 for b in main_boxes])
    ys=cuts(opaque,rows,0,[(b[0].start+b[0].stop)/2 for b in main_boxes])
    occupants = {}
    assigned = {}
    for label,box in enumerate(boxes,1):
        if box is None or counts[label] < 3:
            continue
        yy,xx = box
        # Large bodies determine the slot, minor detached pixels use its grid.
        cx,cy=(xx.start+xx.stop)/2,(yy.start+yy.stop)/2
        col = min(columns-1,max(0,int(np.searchsorted(xs,cx,side='right')-1)))
        row = min(rows-1,max(0,int(np.searchsorted(ys,cy,side='right')-1)))
        slot = row*columns+col
        assigned.setdefault(slot,[]).append(label)
        if counts[label] >= min_body:
            occupants.setdefault(slot,[]).append(label)
    wanted = set(wanted)
    main = {}
    for slot in sorted(wanted):
        candidates = sorted(occupants.get(slot,[]),key=lambda label:counts[label],reverse=True)
        if not candidates:
            raise ValueError(f'{path.name}: missing independent body at row{slot//columns+1} col{slot%columns+1}')
        biggest = candidates[0]
        yy,xx=boxes[biggest-1]
        if xx.stop-xx.start > image.width/columns*1.65 or yy.stop-yy.start > image.height/rows*1.50:
            raise ValueError(f'{path.name}: merged/crossed body at row{slot//columns+1} col{slot%columns+1}: {(xx.start,yy.start,xx.stop,yy.stop)}')
        # Two large separated parts can be a golem arm or detached weapon; a
        # second complete body is ambiguous and requires source review.
        if len(candidates)>1 and counts[candidates[1]] > counts[biggest]*.66:
            raise ValueError(f'{path.name}: two substantial bodies share slot{slot}; source review required')
        main[slot]=biggest
    # A source-row ground line preserves the changing height of a crouch.
    baselines={}
    for row in range(rows):
        bottoms=[boxes[main[s]-1][0].stop for s in wanted if s//columns==row]
        if bottoms:baselines[row]=float(np.quantile(bottoms,.75))
    parts={}
    for slot in sorted(wanted):
        members=assigned[slot]
        # Only the source pixels assigned to this actor survive packing.
        keep=np.isin(labels,members)
        yy,xx=np.where(keep)
        box=(int(xx.min()),int(yy.min()),int(xx.max())+1,int(yy.max())+1)
        crop=rgba[box[1]:box[3],box[0]:box[2]].copy()
        crop[:,:,3]=np.where(keep[box[1]:box[3],box[0]:box[2]],255,0)
        col,row=slot%columns,slot//columns
        origin=((xs[col]+xs[col+1])/2,baselines[row])
        parts[slot]=Part(Image.fromarray(crop),box,slot,origin,int(counts[main[slot]]),float(boxes[main[slot]-1][0].stop))
    body_rows=body_rows or [0]
    heights=[]
    for slot,part in parts.items():
        if slot//columns not in body_rows:continue
        # Exclude a narrow spear/weapon above the head from body calibration.
        col=slot%columns
        centre=(xs[col]+xs[col+1])/2
        width=(xs[col+1]-xs[col])
        strip=opaque[:,max(0,int(centre-width*.22)):min(image.width,int(centre+width*.22))]
        y0,y1=ys[slot//columns],ys[slot//columns+1]
        counts_y=strip[y0:y1].sum(axis=1)
        threshold=max(4,float(np.quantile(counts_y[counts_y>0],.65))*.25) if (counts_y>0).any() else 4
        visible=np.flatnonzero(counts_y >= threshold)
        if len(visible):
            heights.append(part.origin[1]-(y0+visible[0]))
    nominal=float(np.median(heights)) if heights else float(np.median([p.image.height for p in parts.values()]))
    return parts,{'width':image.width,'height':image.height,'columns':columns,'rows':rows,'column_cuts':xs,'row_cuts':ys,'baselines':baselines,'body_height':nominal,'body_min_area':min_body}


def base_specs(character):
    base={'file':f'{character}-64.png','columns':8,'rows':8,'body_rows':[0],
          'clips':{clip:list(range(i*8,(i+1)*8)) for i,clip in enumerate(BASE_CLIPS)}}
    if character=='brine':
        base['clips']['defeat']=[56+i for i in [0,1,2,3,7,4,5,6]]
    if character=='tam':
        base['clips']['defeat']=[56+i for i in [0,1,2,3,4,5,7,6]]
    if character=='cairn':
        base['clips']={'idle':list(range(8)),'walk':list(range(8,24)),'primary':list(range(24,40)),
                       'secondary':list(range(40,56)),'guard':list(range(56,64))}
        return [base,{'file':'cairn-extra16.png','columns':4,'rows':4,'body_rows':[0],
                      'clips':{'special':list(range(8)),'hit':list(range(8,12)),'defeat':list(range(12,16))}}]
    if character=='nix' and (ROOT/'art-source/animated/nix-repair24.png').exists():
        base.update({'rows':7,'extra_slots':[28,29],'clips':{'idle':list(range(8)),'walk':list(range(8,16)),
                                      'primary':list(range(16,24)),'special':list(range(32,40)),'hit':list(range(40,48))}})
        return [base,{'file':'nix-repair24.png','columns':8,'rows':3,'body_rows':[0],
                      'clips':{'secondary':list(range(8)),'guard':list(range(8,16)),'defeat':list(range(16,24))}}]
    if character=='mirra' and (ROOT/'art-source/animated/mirra-repair24.png').exists():
        for clip in ['special','hit','defeat']:base['clips'].pop(clip)
        return [base,{'file':'mirra-repair24.png','columns':8,'rows':3,'body_rows':[0],
                      'clips':{'special':list(range(8)),'hit':list(range(8,16)),'defeat':list(range(16,24))}}]
    if character=='ashe' and (ROOT/'art-source/animated/ashe-repair24.png').exists():
        for clip in ['primary','secondary','defeat']:base['clips'].pop(clip)
        return [base,{'file':'ashe-repair24.png','columns':8,'rows':3,'body_rows':[0],
                      'clips':{'primary':list(range(8)),'secondary':list(range(8,16)),'defeat':list(range(16,24))}}]
    result=[base]
    for clip in BASE_CLIPS:
        filename=f'{character}-{clip}8.png'
        if (ROOT/'art-source/animated'/filename).exists():
            base['clips'].pop(clip,None)
            result.append({'file':filename,'columns':4,'rows':2,'body_rows':[0],
                           'clips':{clip:list(range(8))}})
    return result


def specs(character):
    """New coherent cycles replace old cycles rather than alternate masters."""
    result=base_specs(character)
    folder=ROOT/'art-source/animated/v3'
    extension=folder/f'{character}-extension64.png'
    if character=='cairn':
        result.append({'file':'v3/cairn-extension32.png','columns':8,'rows':4,'body_rows':[1,2],
                       'clips':{clip:list(range(i*8,(i+1)*8)) for i,clip in enumerate(TRAVERSAL_CLIPS)}})
    elif extension.exists():
        for spec in result:
            spec['clips'].pop('walk',None);spec['clips'].pop('primary',None)
        result.append({'file':f'v3/{character}-extension64.png','columns':8,'rows':8,'body_rows':[0,1],
                       'clips':{'walk':list(range(16)),'primary':list(range(16,32)),
                                **{clip:list(range(32+i*8,40+i*8)) for i,clip in enumerate(TRAVERSAL_CLIPS)}}})
        if character=='clack':
            result[-1]['clips']['dodge']=[56,57,58,59,60,63,61,62]
    elif character=='nix' and (folder/'nix-extension48.png').exists():
        for spec in result:
            spec['clips'].pop('walk',None);spec['clips'].pop('primary',None)
        result += [{'file':'v3/nix-cycles32.png','columns':8,'rows':4,'body_rows':[0,1],
                    'clips':{'walk':list(range(16)),'primary':list(range(16,32))}},
                   {'file':'v3/nix-extension48.png','columns':8,'rows':6,'body_rows':[0],
                    'clips':{clip:list(range(16+i*8,24+i*8)) for i,clip in enumerate(TRAVERSAL_CLIPS)}}]
    else:
        raise FileNotFoundError(extension)
    result.append({'file':f'v3/{character}-powered40.png','columns':8,'rows':5,'body_rows':[0],
                   'clips':{clip:list(range(i*8,(i+1)*8)) for i,clip in enumerate(POWERED_CLIPS)}})
    # Explicit retakes replace the selected cells, never pad missing art.
    repairs=folder/f'{character}-repair24.png'
    if repairs.exists():
        for spec in result:
            spec['clips'].pop('primary',None);spec['clips'].pop('stair_down',None)
        result.append({'file':f'v3/{character}-repair24.png','columns':8,'rows':3,'body_rows':[0],
                       'clips':{'primary':list(range(16)),'stair_down':list(range(16,24))}})
    for clip in ['primary','secondary']+TRAVERSAL_CLIPS+POWERED_CLIPS:
        count=16 if clip=='primary' else 8
        replacement=folder/f'{character}-{clip}{count}.png'
        if not replacement.exists():
            replacement=folder/f'{character}-{clip.replace("_","-")}{count}.png'
        if replacement.exists():
            for spec in result:spec['clips'].pop(clip,None)
            result.append({'file':f'v3/{replacement.name}','columns':4 if character=='iona' and clip=='primary' else 8 if count==16 else 4,
                           'rows':4 if character=='iona' and clip=='primary' else 2,
                           'body_rows':[0],'clips':{clip:list(range(count))}})
    if (folder/f'{character}-powered-repair16.png').exists():
        for spec in result:
            spec['clips'].pop('powered_primary',None);spec['clips'].pop('powered_exit',None)
        result.append({'file':f'v3/{character}-powered-repair16.png','columns':8,'rows':2,'body_rows':[0],
                       'clips':{'powered_primary':list(range(8)),'powered_exit':list(range(8,16))}})
    if character in ['morel','velvet']:
        name=f'v3/{character}-powered-primary-exit16.png'
        if (ROOT/'art-source/animated'/name).exists():
            replacements={'powered_exit':list(range(8,16)) if character=='morel' else [8,9,10,12,13,14]}
            if character=='morel':replacements['powered_primary']=list(range(8))
            for spec in result:
                for clip in replacements:spec['clips'].pop(clip,None)
            result.append({'file':name,'columns':8,'rows':2,'body_rows':[0] if character=='morel' else [1],
                           **({'calibration_slots':[8,9,10,12,13,14]} if character=='velvet' else {}),'clips':replacements})
            if character=='velvet':
                for spec in result:
                    if spec['file']=='v3/velvet-powered40.png':spec['extra_slots']=[39]
    if character=='pendle':
        result.append({'file':'v3/pendle-reload8.png','columns':4,'rows':2,'body_rows':[0],
                       'clips':{'reload':list(range(8))}})
    for spec in result:
        for clip,indices in list(spec['clips'].items()):
            order=V3_ORDERS.get((character,clip))
            if order is not None and spec['file'].startswith('v3/'):
                spec['clips'][clip]=[indices[i] for i in order]
    return [spec for spec in result if spec['clips']]


def timing(character,clip,count):
    if clip in ['idle','powered_idle']:return [1.60/count]*count,True,None
    if clip in ['walk','powered_walk','stair_up','stair_down']:return [(1.04 if character=='cairn' else .72)/count]*count,True,None
    if clip in ['guard','powered_guard']:return [.055]*min(count,4)+[.12]*(count-min(count,4)),False,None
    if clip=='jump':return [.08,.055,.08,.11,.11,.08,.07,.115],False,None
    if clip=='dodge':return [.055,.045,.04,.045,.06,.07,.08,.10],False,None
    if clip=='powered_exit':return ([.11,.11,.11,.11,.12,.14,.16] if count==7 else [.11,.10,.10,.09,.09,.10,.12,.15]),False,None
    if clip=='reload':return [.10,.12,.15,.17,.19,.16,.12,.10],False,None
    if clip=='hit':return ([.035,.065,.09,.12,.13,.15,.16,.18] if count==8 else [.045,.08,.13,.20]),False,None
    if clip=='defeat':return ([.08,.10,.10,.12,.15,.18,.24,.30] if count==8 else [.10,.15,.22,.35]),False,None
    if count==16:
        if character!='cairn':
            # More drawings must not double action latency or recovery. The
            # normal eight-pose attack rhythm is divided into breakdowns.
            keys=[.07,.07,.08,.11,.04,.055,.085,.13]
            weights=[d*w for d in keys for w in [.55,.45]]
            release=V3_RELEASES.get((character,clip),8)
            return ([w*.33/sum(weights[:release]) for w in weights[:release]]+
                    [w*(sum(keys)-.33)/sum(weights[release:]) for w in weights[release:]]),False,release
        # Long loaded poses, one decisive transition, then a longer settle.
        return [.065,.06,.06,.06,.065,.07,.08,.10,.035,.04,.05,.07,.08,.09,.11,.13],False,8
    if clip=='special':return [.09,.08,.09,.12,.06,.08,.12,.18],False,(2 if character=='mote' else 4)
    if character=='cairn' and clip=='powered_primary':
        return [.10,.10,.10,.12,.14,.06,.14,.18],False,5
    if clip=='powered_primary' and (character,clip) in V3_RELEASES:
        weights=[.07,.07,.08,.11,.04,.055,.085,.13]
        release=V3_RELEASES[(character,clip)]
        return ([w*.33/sum(weights[:release]) for w in weights[:release]]+
                [w*(sum(weights)-.33)/sum(weights[release:]) for w in weights[release:]]),False,release
    return [.07,.07,.08,.11,.04,.055,.085,.13],False,(3 if character=='rook' and clip=='secondary' else 4)


def export_character(character):
    collected={};source_records=[];source_parts={}
    anchors={};anchor_sources=[];anchor_release_checks={}
    anchor_folder=ROOT/'art-source/animated/v3'
    anchor_files=list(anchor_folder.glob('*-anchors.json'))
    if (anchor_folder/'rook-thrusters.json').exists():anchor_files.append(anchor_folder/'rook-thrusters.json')
    for path in sorted(anchor_files):
        data=json.loads(path.read_text())
        if 'anchors' in data:data=data['anchors']
        if character in data:
            for clip,values in data[character].items():
                if clip.startswith('_'):continue
                if not set(values)<= {'release_anchor','contact_reach','hand_anchors','baked_effects','thruster_anchors','release_frame','note','evidence'}:
                    raise ValueError(f'{path.name}: unknown anchor fields for {clip}')
                if 'release_frame' in values:anchor_release_checks[clip]=values['release_frame']
                values={key:value for key,value in values.items() if key not in ['release_frame','note','evidence']}
                previous=anchors.get(clip,{})
                if any(previous[key]!=values[key] for key in set(previous)&set(values)):
                    raise ValueError(f'{character}/{clip}: conflicting anchor authorship')
                anchors.setdefault(clip,{}).update(values)
            anchor_sources.append({'path':str(path.relative_to(ROOT)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    size=(256,192) if character=='ashe' else (224,192) if character=='iona' else SIZE
    pivot=(132,172) if character=='ashe' else PIVOT
    desired=112 if character=='cairn' else 96
    for spec in specs(character):
        path=ROOT/'art-source/animated'/spec['file']
        if not path.exists():raise FileNotFoundError(path)
        # Calibration poses remain available even when a newer strip replaces
        # their animation. Otherwise a defeat-only leftover is accidentally
        # enlarged using the short collapsed body as the standing model.
        calibration=spec.get('calibration_slots',[row*spec['columns']+col for row in spec['body_rows'] for col in range(spec['columns'])])
        wanted=sorted(set(sum(spec['clips'].values(),[])+spec.get('extra_slots',[])+calibration))
        parts,source=extract(path,spec['columns'],spec['rows'],wanted,spec['body_rows'])
        base_scale=desired/source['body_height']
        source.update({'path':str(path.relative_to(ROOT)),'base_scale':base_scale})
        source_records.append(source)
        source_parts[spec['file']]=(parts,source)
        for clip,indices in spec['clips'].items():
            collected[clip]=[(replace(parts[i],origin=(parts[i].origin[0],parts[i].foot_y))
                              if (clip in TRAVERSAL_CLIPS and source['path'].startswith('art-source/animated/v3/')) or character=='rook' and clip=='secondary'
                              else parts[i],source) for i in indices]
    if character=='nix' and 'nix-repair24.png' in source_parts:
        # Two original secondary drawings have correct metal emitter anatomy;
        # their matching repair cells were rejected in the art review.
        base_parts,base_source=source_parts['nix-64.png']
        collected['secondary'][4]=(base_parts[28],base_source)
        collected['secondary'][5]=(base_parts[29],base_source)
    if character=='velvet':
        parts,source=source_parts['v3/velvet-powered40.png']
        collected['powered_exit'].append((parts[39],source))
    single_patches={
        'nix':[('primary',3,'nix-primary03-fix.png')],
        'morel':[('powered_primary',2,'morel-powered-primary-single.png')],
        'velvet':[('powered_primary',4,'velvet-powered-primary-single-v2.png')],
    }
    for clip,index,name in single_patches.get(character,[]):
        patch=ROOT/'art-source/animated/v3'/name
        if not patch.exists():raise FileNotFoundError(patch)
        parts,source=extract(patch,1,1,[0],[0])
        source.update({'path':str(patch.relative_to(ROOT)),'base_scale':desired/source['body_height']})
        source_records.append(source)
        collected[clip][index]=(parts[0],source)
    expected_clips=CLIPS+(['reload'] if character=='pendle' else [])
    if set(collected)!=set(expected_clips):raise ValueError(f'{character}: incomplete action set {set(collected)}')
    # Fit all of a character's source masters together with a single additional
    # factor, retaining their calibrated body size and all authored poses.
    fit=1.0
    for values in collected.values():
        for part,source in values:
            x0,y0,x1,y1=part.bounds;ox,oy=part.origin;s=source['base_scale']
            margin=2 if character=='ashe' else 3
            for extent,available in [((ox-x0)*s,pivot[0]-margin),((x1-ox)*s,size[0]-pivot[0]-margin),((oy-y0)*s,pivot[1]-margin),((y1-oy)*s,size[1]-pivot[1]-margin)]:
                if extent>available:fit=min(fit,available/extent)
    output=ROOT/'assets/animated'/character;output.mkdir(parents=True,exist_ok=True)
    manifest={'id':character,'name':character.capitalize(),'view':'E','frame_size':list(size),'foot_pivot':list(pivot),
              'body_height_target':desired,'fit_factor':fit,'sources':source_records,'anchor_sources':anchor_sources,'clips':{}}
    ext=[];animations=[];all_hashes=set();all_frames=[];resource_id=0
    for clip in expected_clips:
        values=collected[clip];durations,loop,release_frame=timing(character,clip,len(values))
        records=[];entries=[]
        for index,(part,source) in enumerate(values):
            scale=source['base_scale']*fit
            image=part.image
            resized=image.resize((max(1,round(image.width*scale)),max(1,round(image.height*scale))),Image.Resampling.NEAREST)
            x=round(pivot[0]+(part.bounds[0]-part.origin[0])*scale)
            y=round(pivot[1]+(part.bounds[1]-part.origin[1])*scale)
            if x<1 or y<1 or x+resized.width>size[0]-1 or y+resized.height>size[1]-1:
                raise ValueError(f'{character}/{clip}/{index}: fitted sprite clips {(x,y,resized.size)}')
            frame=Image.new('RGBA',size);frame.alpha_composite(resized,(x,y))
            patch_path=ROOT/'art-source/animated'/f'{character}-{clip}{index:02d}-fix.png'
            patch_metadata=None
            if patch_path.exists() and not source['path'].startswith('art-source/animated/v3/'):
                patch=Image.open(patch_path).convert('RGBA')
                if abs(patch.width/patch.height-size[0]/size[1])>.001:
                    raise ValueError(f'{patch_path.name}: edited canvas aspect changed')
                array=np.asarray(patch).copy()
                array[:,:,3]=np.where(array[:,:,3]>=128,255,0)
                patch=Image.fromarray(array)
                # A registered frame edit retains the entire source canvas,
                # including its original pivot and padding. Never refit it.
                packed=patch.resize(size,Image.Resampling.NEAREST)
                frame=Image.new('RGBA',size);frame.alpha_composite(packed)
                box=frame.getbbox()
                if not box or box[0]<1 or box[1]<1 or box[2]>size[0]-1 or box[3]>size[1]-1:
                    raise ValueError(f'{patch_path.name}: edited frame clips its canvas')
                patch_metadata={'source':str(patch_path.relative_to(ROOT)),'slot':None,'source_bounds':list(patch.getbbox()),
                     'source_origin':[pivot[0]*patch.width/size[0],pivot[1]*patch.height/size[1]],
                     'scale':size[0]/patch.width,'registration':'full_canvas_edit'}
            digest=sha(frame)
            if digest in all_hashes:raise ValueError(f'{character}/{clip}/{index}: duplicate packed drawing')
            all_hashes.add(digest)
            filename=f'{clip}-{index:02d}.png';save_png(frame,output/filename)
            record={'path':f'res://assets/animated/{character}/{filename}','source':source['path'],'slot':part.slot,
                    'source_bounds':list(part.bounds),'source_origin':list(part.origin),'scale':scale,
                    'packed_bounds':list(frame.getbbox()),'sha256':digest}
            if (clip in TRAVERSAL_CLIPS and source['path'].startswith('art-source/animated/v3/')) or character=='rook' and clip=='secondary':
                record['registration']='per_frame_support_bottom; engine_owns_world_height'
            if patch_metadata is not None:record.update(patch_metadata)
            records.append(record);all_frames.append((clip,index,frame,durations[index]))
            resource_id+=1
            ext.append(f'[ext_resource type="Texture2D" path="{record["path"]}" id="f{resource_id}"]')
            entries.append('{"duration": %.6f, "texture": ExtResource("f%d")}'%(durations[index],resource_id))
        hold_frame=3 if character=='cairn' and clip=='guard' else min(4,len(values)-1)
        manifest['clips'][clip]={'frame_count':len(values),'durations':durations,'duration':sum(durations),'loop':loop,
                                 'release_frame':release_frame,'release_time':sum(durations[:release_frame]) if release_frame is not None else None,
                                 'hold_frame':hold_frame if clip in ['guard','powered_guard'] else None,'frames':records}
        if (character,clip) in RELEASE_ANCHORS:
            manifest['clips'][clip]['release_anchor']=RELEASE_ANCHORS[(character,clip)]
        if character=='pendle' and clip=='primary':
            manifest['clips'][clip]['baked_effects']=['muzzle_flash']
        if clip in anchors:
            data=anchors[clip]
            if clip in anchor_release_checks and anchor_release_checks[clip]!=release_frame:
                raise ValueError(f'{character}/{clip}: anchor reviewed on another release frame')
            if 'hand_anchors' in data and len(data['hand_anchors'])!=len(values):
                raise ValueError(f'{character}/{clip}: anchors must match every selected frame')
            points=([data['release_anchor']] if 'release_anchor' in data else [])+data.get('hand_anchors',[])+data.get('thruster_anchors',[])
            for point in points:
                if len(point)!=2 or not all(math.isfinite(v) for v in point):
                    raise ValueError(f'{character}/{clip}: invalid anchor {point}')
                if not 0<=point[0]+pivot[0]<size[0] or not 0<=point[1]+pivot[1]<size[1]:
                    raise ValueError(f'{character}/{clip}: anchor leaves frame {point}')
            manifest['clips'][clip].update(data)
        animations.append('{"frames": [%s], "loop": %s, "name": &"%s", "speed": 1.0}'%(', '.join(entries),str(loop).lower(),clip))
    manifest['pose_count']=len(all_frames)
    (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    resource=f'[gd_resource type="SpriteFrames" load_steps={resource_id+1} format=3]\n\n'+'\n'.join(ext)+'\n\n[resource]\nanimations = [\n'+',\n'.join(animations)+'\n]\n'
    (output/'frames.tres').write_text(resource)
    sheets=ROOT/'animation-sheets';sheets.mkdir(exist_ok=True)
    atlas=Image.new('RGBA',(8*size[0],math.ceil(len(all_frames)/8)*size[1]))
    atlas_frames=[]
    for slot,(clip,index,frame,duration) in enumerate(all_frames):
        x,y=slot%8*size[0],slot//8*size[1];atlas.alpha_composite(frame,(x,y))
        atlas_frames.append({'name':f'{clip}-{index:02d}','clip':clip,'index':index,'x':x,'y':y,'w':size[0],'h':size[1],'duration_seconds':duration,'pivot':list(pivot)})
    save_png(atlas,sheets/f'{character}.png')
    (sheets/f'{character}.json').write_text(json.dumps({'character':character,'view':'E','columns':8,'frame_size':list(size),
       'foot_pivot':list(pivot),'pose_count':len(all_frames),'frames':atlas_frames},indent=2)+'\n')
    return manifest


def write_roster():
    characters=[]
    for character in IDS:
        p=ROOT/'assets/animated'/character/'manifest.json'
        if not p.exists():continue
        m=json.loads(p.read_text())
        characters.append({'id':character,'name':character.capitalize(),'manifest':f'res://assets/animated/{character}/manifest.json',
                           'frames':f'res://assets/animated/{character}/frames.tres','pose_count':m['pose_count'],
                           'frame_size':m['frame_size'],'foot_pivot':m['foot_pivot']})
    (ROOT/'assets/animated/roster.json').write_text(json.dumps({'version':1,'frame_size':list(SIZE),'foot_pivot':list(PIVOT),
      'view':'E','characters':characters,'pose_count':sum(c['pose_count'] for c in characters)},indent=2)+'\n')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('characters',nargs='*',choices=IDS)
    parser.add_argument('--available',action='store_true',help='Import complete available sets; report missing masters without hiding invalid drawings')
    args=parser.parse_args()
    targets=args.characters or IDS
    failures=[]
    for character in targets:
        try:
            m=export_character(character)
            print(json.dumps({'id':character,'status':'imported','poses':m['pose_count'],'fit_factor':round(m['fit_factor'],4)}),flush=True)
        except FileNotFoundError as error:
            failures.append({'id':character,'status':'missing_source','error':str(error)})
        except (ValueError,AssertionError) as error:
            failures.append({'id':character,'status':'rejected','error':str(error)})
    write_roster()
    for failure in failures:print(json.dumps(failure),flush=True)
    if failures and (not args.available or any(f['status']=='rejected' for f in failures)):raise SystemExit(1)


if __name__=='__main__':main()

