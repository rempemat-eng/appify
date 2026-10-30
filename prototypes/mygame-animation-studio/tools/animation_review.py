#!/usr/bin/env python3
"""Review exports without inventing drawings. GIFs are asset loops, not gameplay."""
from pathlib import Path
import argparse
import json
import math
import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[1]
CLIPS=['idle','walk','primary','secondary','special','guard','hit','defeat','jump','stair_up','stair_down','dodge','powered_idle','powered_walk','powered_primary','powered_guard','powered_exit']
FONT='/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'


def load_image(record):
    return Image.open(ROOT/record['path'].removeprefix('res://')).convert('RGBA')


def review(character):
    path=ROOT/'assets/animated'/character/'manifest.json'
    m=json.loads(path.read_text())
    clips=CLIPS+(['reload'] if 'reload' in m['clips'] else [])
    out=ROOT/'captures/animation-review';out.mkdir(parents=True,exist_ok=True)
    font=ImageFont.truetype(FONT,16);small=ImageFont.truetype(FONT,12)
    width,height=m['frame_size']
    cols=max(v['frame_count'] for v in m['clips'].values())
    board=Image.new('RGB',(112+cols*width,52+len(clips)*210),'#20312e');draw=ImageDraw.Draw(board)
    draw.text((20,12),f'{character.upper()} / EXPORTED DRAWINGS / EAST VIEW',font=font,fill='#e6dbc3')
    issues=[];stats={};gifs=[];gif_times=[]
    for row,clip in enumerate(clips):
        data=m['clips'][clip];arrays=[];areas=[];bottoms=[]
        draw.text((8,66+row*210),clip.upper(),font=small,fill='#b0c6b5')
        for index,record in enumerate(data['frames']):
            image=load_image(record);array=np.array(image)
            arrays.append(array);mask=array[:,:,3]>128
            areas.append(int(mask.sum()));bounds=image.getbbox();bottoms.append(bounds[3])
            board.paste(image,(112+index*width,52+row*210),image)
            draw.text((120+index*width,235+row*210),f'{index+1:02} / {data["durations"][index]:.3f}s',font=small,fill='#9eafa0')
            # Explicitly labelled raster review output; no simulated target hits.
            gif=Image.new('RGB',(width*2,420),'#20312e')
            enlarged=image.resize((width*2,height*2),Image.Resampling.NEAREST)
            gif.paste(enlarged,(0,0),enlarged)
            gd=ImageDraw.Draw(gif);gd.text((12,392),f'{character.upper()}  {clip.upper()}  {index+1:02}/{len(data["frames"])}',font=small,fill='#e6dbc3')
            gifs.append(gif);gif_times.append(max(20,round(data['durations'][index]*1000)))
        near=[]
        for i in range(len(arrays)):
            for j in range(i+1,len(arrays)):
                a,b=arrays[i],arrays[j];ma,mb=a[:,:,3]>128,b[:,:,3]>128
                union=ma|mb
                intersection=int((ma&mb).sum());union_count=int(union.sum())
                iou=intersection/max(1,union_count)
                color_delta=float(np.abs(a[:,:,:3].astype(np.int16)-b[:,:,:3].astype(np.int16))[union].mean()) if union_count else 0
                changed=float(np.any(a!=b,axis=2)[union].mean()) if union_count else 0
                if (iou>.975 and color_delta<12) or changed<.045:
                    near.append({'a':i,'b':j,'silhouette_iou':round(iou,4),'rgb_mae':round(color_delta,3),'changed_fraction':round(changed,4)})
        if near:issues.append({'clip':clip,'kind':'near_duplicate_candidates','pairs':near})
        ratio=max(areas)/max(1,min(areas))
        if clip in ['idle','walk'] and ratio>1.42:
            issues.append({'clip':clip,'kind':'large_silhouette_area_change','ratio':round(ratio,4)})
        if clip=='idle' and max(bottoms)-min(bottoms)>7:
            issues.append({'clip':clip,'kind':'idle_ground_registration_spread','pixels':max(bottoms)-min(bottoms)})
        stats[clip]={'frames':len(arrays),'area_min':min(areas),'area_max':max(areas),'area_ratio':round(ratio,4),
                     'bottom_min':min(bottoms),'bottom_max':max(bottoms),'near_duplicate_pair_count':len(near)}
    board.save(out/f'{character}-contact.png')
    gifs[0].save(ROOT/'animation-sheets'/f'{character}-motion.gif',save_all=True,append_images=gifs[1:],duration=gif_times,loop=0,disposal=2,optimize=False)
    report={'id':character,'pose_count':m['pose_count'],'view':'E','fit_factor':m['fit_factor'],'clips':stats,'review_flags':issues,
            'interpretation':'Flags identify candidates for visual review. Distinct image hashes and pose counts do not certify animation quality. GIF is an asset loop, not recorded gameplay.'}
    (out/f'{character}-review.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'id':character,'pose_count':m['pose_count'],'flags':len(issues),'fit_factor':round(m['fit_factor'],3)}))
    return report


def overview():
    manifests=list((ROOT/'assets/animated').glob('*/manifest.json'))
    if not manifests:return
    manifests.sort(key=lambda p:p.parent.name)
    board=Image.new('RGB',(1920,1080),'#192c29');d=ImageDraw.Draw(board)
    title=ImageFont.truetype(FONT,30);small=ImageFont.truetype(FONT,18)
    d.text((30,25),'MYGAME / ANIMATION ROSTER',font=title,fill='#eee1c9')
    d.text((32,72),'Actual exported idle and contact drawings · single east-facing studies',font=small,fill='#a3bcab')
    for index,path in enumerate(manifests):
        m=json.loads(path.read_text());col,row=index%7,index//7;x,y=18+col*270,125+row*450
        d.rounded_rectangle((x,y,x+252,y+425),radius=5,fill='#243b34',outline='#496356',width=2)
        for k,clip in enumerate(['idle','primary']):
            n=0 if clip=='idle' else (m['clips'][clip]['release_frame'] or 0)
            im=load_image(m['clips'][clip]['frames'][n])
            im=im.crop(im.getbbox())
            board.paste(im,(x+(252-im.width)//2,y+180-im.height+k*180),im)
        d.text((x+16,y+370),f'{m["name"]} / {m["pose_count"]} poses',font=small,fill='#eee1c9')
    board.save(ROOT/'animation-sheets/Roster_Overview.png')


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('characters',nargs='*');args=p.parse_args()
    chars=args.characters or [p.parent.name for p in (ROOT/'assets/animated').glob('*/manifest.json')]
    for character in chars:review(character)
    reports=[json.loads(p.read_text()) for p in sorted((ROOT/'captures/animation-review').glob('*-review.json'))]
    (ROOT/'captures/animation-review/summary.json').write_text(json.dumps(reports,indent=2)+'\n')
    overview()


if __name__=='__main__':main()

