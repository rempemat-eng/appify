/** Reproducible Expo assets + a read-only render/playtest against existing world data.
 * Usage: node --import tsx scripts/export-mygame-world.ts --studio /path/to/studio
 * Requires Python/Pillow, already used by the repository's art pipeline. */
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import {
  existsSync,
  mkdirSync,
  readFileSync,
  readdirSync,
  writeFileSync,
  copyFileSync,
  unlinkSync,
} from 'node:fs';
import { dirname, join, relative, resolve } from 'node:path';
import { stripTypeScriptTypes } from 'node:module';
import { fileURLToPath } from 'node:url';
import { z } from 'zod';
import {
  MYGAME_CHARACTERS,
  type MyGameCharacterAsset,
  type MyGameClip,
} from '../lib/mygame-character';
import { WORLD_TILE, worldChunks, worldAreas, worldTiles, worldDecks } from '../lib/world-canvas';

const root = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const args = process.argv.slice(2);
const option = (name: string, fallback?: string) => {
  const index = args.indexOf(name);
  return index < 0 ? fallback : args[index + 1];
};
const studioArg = option('--studio');
if (!studioArg) throw new Error('--studio must identify the source Godot studio');
const studio = resolve(studioArg);
const output = resolve(option('--out', join(root, 'prototypes/mygame-world-preview'))!);
const hash = (path: string) => createHash('sha256').update(readFileSync(path)).digest('hex');
const json = (path: string, value: unknown) => {
  mkdirSync(dirname(path), { recursive: true });
  writeFileSync(path, JSON.stringify(value, null, 2) + '\n');
};
const walk = (dir: string): string[] =>
  readdirSync(dir, { withFileTypes: true }).flatMap((item) =>
    item.isDirectory() ? walk(join(dir, item.name)) : [join(dir, item.name)],
  );
const sizeSchema = z.tuple([z.number().int().positive(), z.number().int().positive()]);
const offsetSchema = z.tuple([z.number().int().nonnegative(), z.number().int().nonnegative()]);
const shaSchema = z.string().regex(/^[a-f0-9]{64}$/);
const manifestSchema = z.object({
  schema_version: z.number().int().optional(),
  status: z.string().optional(),
  missing_clips: z.array(z.string()).optional(),
  id: z.enum(MYGAME_CHARACTERS),
  view: z.enum(['E', 'SE', 'S', 'SW', 'W', 'NW', 'N', 'NE']),
  frame_size: sizeSchema,
  foot_pivot: offsetSchema,
  body_height_target: z.number().positive(),
  clips: z.record(
    z.string(),
    z.object({
      durations: z.array(z.number().positive()),
      loop: z.boolean(),
      release_frame: z.number().int().nonnegative().nullable().default(null),
      hold_frame: z.number().int().nonnegative().nullable().default(null),
      release_anchor: z.tuple([z.number(), z.number()]).optional(),
      frames: z.array(
        z.object({
          path: z.string(),
          sha256: shaSchema,
          logical_sha256: shaSchema.optional(),
          crop_offset: offsetSchema.optional(),
          stored_size: sizeSchema.optional(),
        }),
      ),
    }),
  ),
});
type StudioManifest = z.infer<typeof manifestSchema>;
const characters = new Map<string, MyGameCharacterAsset>();
const sources: { path: string; sha256: string }[] = [];
const jobs: {
  output: string;
  size: readonly [number, number];
  virtualSize: readonly [number, number];
  cellSize: readonly [number, number];
  columns: number;
  frames: {
    file: string;
    size: readonly [number, number];
    offset: readonly [number, number];
    hash: string;
    logicalHash?: string;
  }[];
}[] = [];
const images: string[] = [];
const candidates = new Map<string, { path: string; manifest: StudioManifest }>();
for (const path of walk(join(studio, 'assets/animated'))
  .filter((p) => p.endsWith('/manifest.json'))
  .sort()) {
  const manifest = manifestSchema.parse(JSON.parse(readFileSync(path, 'utf8')));
  if (!MYGAME_CHARACTERS.includes(manifest.id)) continue;
  const key = `${manifest.id}/${manifest.view}`;
  const previous = candidates.get(key);
  if (previous) {
    if ((previous.manifest.schema_version ?? 3) === (manifest.schema_version ?? 3))
      throw new Error(`Duplicate manifest schema ${key}`);
    if ((previous.manifest.schema_version ?? 3) > (manifest.schema_version ?? 3)) continue;
  }
  candidates.set(key, { path, manifest });
}
const selectedViews: {
  id: string;
  view: string;
  path: string;
  policy: string;
  status?: string;
  missingClips?: string[];
}[] = [];
for (const { path, manifest } of candidates.values()) {
  if (!MYGAME_CHARACTERS.includes(manifest.id)) continue;
  if (!['E', 'SE', 'S', 'SW', 'W', 'NW', 'N', 'NE'].includes(manifest.view))
    throw new Error(`Unknown drawn view in ${path}`);
  sources.push({ path: relative(studio, path), sha256: hash(path) });
  selectedViews.push({
    id: manifest.id,
    view: manifest.view,
    path: relative(studio, path),
    policy: manifest.schema_version === 4 ? 'v4 drawn view' : 'legacy root E fallback',
    status: manifest.status,
    missingClips: manifest.missing_clips,
  });
  const asset: MyGameCharacterAsset = characters.get(manifest.id) ?? {
    id: manifest.id,
    views: {},
  };
  if (asset.views[manifest.view]) throw new Error(`Duplicate ${manifest.id}/${manifest.view}`);
  const clips: Record<string, MyGameClip> = {};
  for (const [name, clip] of Object.entries(manifest.clips)) {
    const [width, height] = manifest.frame_size;
    if (
      !clip.frames.length ||
      clip.durations.length !== clip.frames.length ||
      !clip.durations.every((n) => Number.isFinite(n) && n > 0)
    )
      throw new Error(`Invalid timings ${manifest.id}/${name}`);
    for (const index of [clip.release_frame, clip.hold_frame]) {
      if (index !== null && (!Number.isInteger(index) || index < 0 || index >= clip.frames.length))
        throw new Error(`Invalid event frame ${manifest.id}/${name}`);
    }
    const stored = clip.frames.map((frame) => {
      const file = resolve(studio, frame.path.replace(/^res:\/\//, ''));
      if (!file.startsWith(studio + '/') || !existsSync(file))
        throw new Error(`Missing/unsafe frame ${file}`);
      const size = frame.stored_size ?? manifest.frame_size;
      const offset = frame.crop_offset ?? ([0, 0] as const);
      if (
        ![...size, ...offset].every(Number.isInteger) ||
        size.some((n) => n <= 0) ||
        offset.some((n) => n < 0) ||
        offset[0] + size[0] > width ||
        offset[1] + size[1] > height
      )
        throw new Error(`Invalid virtual crop ${file}`);
      return { file, size, offset, hash: frame.sha256, logicalHash: frame.logical_sha256 };
    });
    const cellSize: [number, number] = [
      Math.max(...stored.map((f) => f.size[0])),
      Math.max(...stored.map((f) => f.size[1])),
    ];
    const columns = Math.min(16, Math.floor(4096 / cellSize[0]));
    const capacity = columns * Math.floor(4096 / cellSize[1]);
    if (capacity < 1) throw new Error(`Atlas cell too large ${manifest.id}/${name}`);
    const frames: MyGameClip['frames'][number][] = [];
    for (let offset = 0, page = 0; offset < stored.length; offset += capacity, page++) {
      const pageFrames = stored.slice(offset, offset + capacity);
      const atlas = `${manifest.id}/${manifest.view}/${name}${stored.length > capacity ? `-${page}` : ''}.png`;
      const pageColumns = Math.min(columns, pageFrames.length);
      const atlasSize: [number, number] = [
        pageColumns * cellSize[0],
        Math.ceil(pageFrames.length / pageColumns) * cellSize[1],
      ];
      jobs.push({
        output: join(output, atlas),
        size: atlasSize,
        virtualSize: manifest.frame_size,
        cellSize,
        columns: pageColumns,
        frames: pageFrames,
      });
      images.push(atlas);
      pageFrames.forEach((frame, index) =>
        frames.push({
          asset: atlas,
          atlasSize,
          rect: [
            (index % pageColumns) * cellSize[0],
            Math.floor(index / pageColumns) * cellSize[1],
            ...frame.size,
          ],
          cropOffset: frame.offset,
          duration: clip.durations[offset + index],
        }),
      );
    }
    clips[name] = {
      loop: clip.loop,
      releaseFrame: clip.release_frame,
      holdFrame: clip.hold_frame,
      releaseAnchor: clip.release_anchor ?? null,
      frames,
    };
  }
  asset.views[manifest.view] = {
    frameSize: manifest.frame_size,
    footPivot: manifest.foot_pivot,
    bodyHeight: manifest.body_height_target,
    status: manifest.status ?? 'legacy root E fallback',
    missingClips: manifest.missing_clips,
    clips,
  };
  characters.set(manifest.id, asset);
}
for (const id of MYGAME_CHARACTERS)
  if (!characters.has(id)) throw new Error(`Missing character ${id}`);
execFileSync(
  'python3',
  [
    '-c',
    `
import json,sys,hashlib
from pathlib import Path
from PIL import Image
for job in json.load(sys.stdin):
    out=Image.new('RGBA',job['size'])
    for index,record in enumerate(job['frames']):
        frame=Image.open(record['file']).convert('RGBA')
        assert list(frame.size)==record['size'],('unexpected stored dimensions',record['file'])
        assert hashlib.sha256(frame.tobytes()).hexdigest()==record['hash'],('changed pixels without manifest',record['file'])
        if record.get('logicalHash'):
            virtual=Image.new('RGBA',job['virtualSize']); virtual.paste(frame,tuple(record['offset']))
            assert hashlib.sha256(virtual.tobytes()).hexdigest()==record['logicalHash'],('incorrect crop reconstruction',record['file'])
        out.paste(frame,((index%job['columns'])*job['cellSize'][0],(index//job['columns'])*job['cellSize'][1]))
    path=Path(job['output']); path.parent.mkdir(parents=True,exist_ok=True)
    out.save(path,optimize=True)
`,
  ],
  { input: JSON.stringify(jobs), maxBuffer: 1024 * 1024 },
);
const currentImages = new Set(images);
for (const file of walk(output)) {
  const path = relative(output, file).split('\\').join('/');
  if (
    MYGAME_CHARACTERS.some((id) => id === path.split('/')[0]) &&
    /^[a-z]+\/(E|SE|S|SW|W|NW|N|NE)\/[^/]+\.png$/.test(path) &&
    !currentImages.has(path)
  )
    unlinkSync(file);
}
const catalogue = Object.fromEntries(characters);
json(join(output, 'characters.json'), catalogue);
const characterModule = relative(output, join(root, 'lib/mygame-character')).split('\\').join('/');
writeFileSync(
  join(output, 'registry.ts'),
  `// Generated by scripts/export-mygame-world.ts.\nimport type { ImageSourcePropType } from 'react-native';\nimport type { MyGameCharacterAsset, MyGameCharacterId } from '${characterModule.startsWith('.') ? characterModule : './' + characterModule}';\nimport catalogue from './characters.json';\n${images.map((path, index) => `import image${index} from './${path}';`).join('\n')}\n// oxlint-disable-next-line typescript/no-unsafe-type-assertion -- generated JSON was schema-checked and pixel-verified by the exporter.\nexport const myGameCharacterAssets = catalogue as unknown as Record<MyGameCharacterId, MyGameCharacterAsset>;\nexport const myGameCharacterImages: Readonly<Record<string, ImageSourcePropType>> = {\n${images.map((path, index) => `  '${path}': image${index},`).join('\n')}\n};\n`,
);
json(join(output, 'world.json'), {
  tileSize: WORLD_TILE.size,
  cellSize: WORLD_TILE.cell,
  tiles: worldTiles,
  chunks: worldChunks,
  areas: worldAreas,
  decks: worldDecks,
});
const fixturePlane = 'continent';
const fixtureOrigin = [144, 1500] as const;
const fixtureSize = [480, 270] as const;
const worldFiles = new Map<string, string>();
const background = 'world/ground.png';
const groundTiles = Object.entries(worldTiles[fixturePlane]).flatMap(([key, tile]) => {
  const [column, row] = key.split(',').map(Number);
  const x = column * WORLD_TILE.size,
    y = row * WORLD_TILE.size;
  if (
    x >= fixtureOrigin[0] + fixtureSize[0] ||
    y >= fixtureOrigin[1] + fixtureSize[1] ||
    x + WORLD_TILE.size <= fixtureOrigin[0] ||
    y + WORLD_TILE.size <= fixtureOrigin[1]
  )
    return [];
  return [{ path: join(root, 'assets/world', tile.art + '.png'), x, y, fill: tile.fill }];
});
execFileSync(
  'python3',
  [
    '-c',
    `
import json,sys
from PIL import Image,ImageDraw
from pathlib import Path
data=json.load(sys.stdin); out=Image.new('RGBA',(data['size'][0]*2,data['size'][1]*2))
for tile in data['tiles']:
    x=(tile['x']-data['origin'][0])*2; y=(tile['y']-data['origin'][1])*2
    if tile.get('fill'): ImageDraw.Draw(out).rectangle((x,y,x+512-1,y+512-1),fill=tile['fill'])
    else: out.paste(Image.open(tile['path']).convert('RGBA'),(x,y))
path=Path(data['output']); path.parent.mkdir(parents=True,exist_ok=True); out.save(path,optimize=True)
`,
  ],
  {
    input: JSON.stringify({
      origin: fixtureOrigin,
      size: fixtureSize,
      tiles: groundTiles,
      output: join(output, background),
    }),
  },
);
// Use the generated main-world prop lookup, without importing PNGs into Node.
const zoneSource = readFileSync(join(root, 'lib/zone-assets.ts'), 'utf8');
const imports = new Map(
  [...zoneSource.matchAll(/import (\w+) from ['"]@\/(assets\/[^'"]+)['"]/g)].map((m) => [
    m[1],
    m[2],
  ]),
);
const propSource = zoneSource.slice(
  zoneSource.indexOf('export const zoneProps:'),
  zoneSource.indexOf('export const zoneProps:') + 40000,
);
const propPaths = new Map(
  [...propSource.matchAll(/^  ([\w]+): (\w+),$/gm)].map((m) => [m[1], imports.get(m[2])]),
);
const props = Object.values(worldTiles[fixturePlane])
  .flatMap((t) => t.objects)
  .filter(
    (o) =>
      o[2] < fixtureOrigin[0] + fixtureSize[0] &&
      o[2] + o[4] > fixtureOrigin[0] &&
      o[3] < fixtureOrigin[1] + fixtureSize[1] &&
      o[3] + o[5] > fixtureOrigin[1],
  )
  .map(([id, sprite, x, y, w, h]) => {
    const path = propPaths.get(sprite);
    if (!path) throw new Error(`No main-world sprite ${sprite}`);
    const asset = `world/${sprite}.png`;
    worldFiles.set(join(root, path), asset);
    return { id, asset, x, y, w, h };
  });
for (const [from, to] of worldFiles) {
  mkdirSync(dirname(join(output, to)), { recursive: true });
  copyFileSync(from, join(output, to));
}
json(join(output, 'fixture.json'), {
  plane: fixturePlane,
  origin: fixtureOrigin,
  size: fixtureSize,
  background,
  props,
  // Opt-in landscape fixture only. This does not change main's world framing.
  logicalTexels: [960, 540],
  assetPixelsPerWorldPixel: 2,
});
writeFileSync(
  join(output, 'character-runtime.mjs'),
  stripTypeScriptTypes(readFileSync(join(root, 'lib/mygame-character.ts'), 'utf8')).replace(
    /[ \t]+$/gm,
    '',
  ),
);
const studioRosterPath = join(studio, 'assets/animated/roster.json');
if (existsSync(studioRosterPath))
  copyFileSync(studioRosterPath, join(output, 'studio-roster.json'));
json(join(output, 'provenance.json'), {
  worldSourceRevision: execFileSync(
    'git',
    ['log', '-1', '--format=%H', '--', 'lib/world-canvas.ts'],
    {
      cwd: root,
      encoding: 'utf8',
    },
  ).trim(),
  worldSourceSha256: hash(join(root, 'lib/world-canvas.ts')),
  manifests: sources,
  selectedViews,
  studioRoster: existsSync(studioRosterPath)
    ? {
        file: 'studio-roster.json',
        sha256: hash(studioRosterPath),
        policy: 'Original view status and missing_clips retained verbatim',
      }
    : null,
  characters: characters.size,
  atlases: images.length,
  directionPolicy: 'Only drawn views; no mirroring or relabelled facings',
  worldIntegration:
    'Existing-map render fixture and AtlasWalk scene node; production actor API not connected',
});
writeFileSync(join(output, 'preview.html'), previewHtmlSource());
console.log(
  `Exported ${characters.size} characters, ${images.length} clip atlases; existing-map preview: ${join(output, 'preview.html')}`,
);

function previewHtmlSource() {
  return `<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>MyGame · Existing world render fixture</title>
<style>body{margin:0;background:#141d25;color:#f4ead5;font:15px system-ui;padding:20px;max-width:1050px;margin:auto}h1{font-size:22px}label{margin-right:18px;display:inline-block}select,button{font:inherit;background:#263944;color:#f4ead5;padding:8px;border:1px solid #66848d;border-radius:4px}canvas{width:960px;max-width:100%;height:auto;image-rendering:pixelated;border:2px solid #658782;display:block;margin-top:16px}p{max-width:770px;line-height:1.5}#status{white-space:pre-line}.fhd{padding:0;margin:0;max-width:none}.fhd canvas{position:fixed;inset:0;width:100vw;height:100vh;max-width:none;margin:0;border:0}.fhd h1,.fhd p,.fhd label,.fhd button,.fhd small,.fhd a{position:relative;z-index:1;background:#141d25d9}.fhd p{font-size:12px}.fhd h1{margin:4px;font-size:16px}small{color:#b6cbc9}</style>
<h1>MyGame · The existing Snowy Ridge</h1><p>This uses the repository’s real world tile, props and passability. Arrow keys/WASD walk on its existing ground. Choose a pose to inspect it; stair drawings are previews because this map currently defines no stairs. The normal game’s player/combat API is not connected here. <a href="?fhd=1">Open opt-in 1920×1080 fixture</a>.</p>
<label>Character <select id="character"></select></label><label>Clip <select id="clip"></select></label><label>Drawn view <select id="view"></select></label><label><input id="grid" type="checkbox"> Walk cells</label><label><input id="reduced" type="checkbox"> Reduced motion</label><button id="restart">Restart clip</button><canvas id="world" width="960" height="540" tabindex="0" aria-label="Character render on real Snowy Ridge map"></canvas><p id="status"></p><small>Depth follows the ground foot. View art is never mirrored. Preview scale: two source pixels per world pixel. At 1920×1080 in FHD mode each source texel is 2×2 screen pixels. Missing directional clips are reported visibly.</small>
<script type="module">
import {makeMyGameWorldSupport,myGameClip,sampleMyGameClip,projectMyGameCharacter} from './character-runtime.mjs';
document.body.classList.toggle('fhd',new URLSearchParams(location.search).has('fhd'));
const [characters,world,fixture]=await Promise.all(['characters.json','world.json','fixture.json'].map(p=>fetch(p).then(r=>r.json())));
const $=id=>document.getElementById(id), canvas=$('world'),ctx=canvas.getContext('2d'),support=makeMyGameWorldSupport(world),keys=new Set(),images=new Map();
let id='cairn',view='E',clip='walk',elapsed=0,last=0,active=!document.hidden,foot=null,missing=false;
const image=p=>{if(!images.has(p)){const im=new Image();im.src=p;images.set(p,im)}return images.get(p)};
const ground=image(fixture.background);fixture.props.forEach(p=>image(p.asset));
for(const key of Object.keys(characters))$('character').add(new Option(key,key));$('character').value=id;
function selectCharacter(){id=$('character').value; const asset=characters[id];$('view').replaceChildren(...Object.keys(asset.views).map(v=>new Option(v,v)));view=asset.views[view]?view:Object.keys(asset.views)[0];$('view').value=view;selectView()}
function selectView(){view=$('view').value;const clips=characters[id].views[view].clips;$('clip').replaceChildren(...Object.keys(clips).map(c=>new Option(c,c)));clip=clips[clip]?clip:Object.keys(clips)[0];$('clip').value=clip;elapsed=0;missing=false}
$('character').onchange=selectCharacter;$('view').onchange=selectView;$('clip').onchange=()=>{clip=$('clip').value;elapsed=0};$('restart').onclick=()=>{elapsed=0};selectCharacter();
const origin=fixture.origin;
for(let y=100;y<170&&!foot;y+=4)for(let x=220;x<280&&!foot;x+=4){const p={x:origin[0]+x+2,y:origin[1]+y+2};if(support(fixture.plane,p).walkable)foot=p}
if(!foot)throw Error('Real fixture has no initial walk cell');window.__mygameWorldFixture={getState:()=>({id,view,clip,foot:{...foot},elapsed,active})};
const directions={ArrowLeft:[-1,0],a:[-1,0],ArrowRight:[1,0],d:[1,0],ArrowUp:[0,-1],w:[0,-1],ArrowDown:[0,1],s:[0,1]};
window.addEventListener('keydown',e=>{if(directions[e.key]&&!['SELECT','INPUT'].includes(document.activeElement.tagName)){keys.add(e.key);e.preventDefault()}});window.addEventListener('keyup',e=>keys.delete(e.key));window.addEventListener('blur',()=>{keys.clear();active=false});window.addEventListener('focus',()=>{active=!document.hidden;last=0});document.addEventListener('visibilitychange',()=>{active=!document.hidden;last=0;keys.clear()});
function draw(now){const dt=last&&active?Math.min((now-last)/1000,.05):0;last=now;if(active)elapsed+=dt;let dx=0,dy=0;for(const key of keys){const d=directions[key];dx+=d[0];dy+=d[1]}if(dx||dy){const len=Math.hypot(dx,dy);dx/=len;dy/=len;const step=40*dt;const x={x:Math.max(origin[0]+4,Math.min(origin[0]+fixture.size[0]-4,foot.x+dx*step)),y:foot.y};if(support(fixture.plane,x).walkable)foot.x=x.x;const y={x:foot.x,y:Math.max(origin[1]+4,Math.min(origin[1]+fixture.size[1]-4,foot.y+dy*step))};if(support(fixture.plane,y).walkable)foot.y=y.y;const desired=Math.abs(dx)>.3?(dy>.3?(dx>0?'SE':'SW'):dy<-.3?(dx>0?'NE':'NW'):(dx>0?'E':'W')):(dy>0?'S':'N');missing=!myGameClip(characters[id],desired,clip);if(!missing){view=desired;$('view').value=view}}
ctx.imageSmoothingEnabled=false;ctx.clearRect(0,0,960,540);if(ground.complete&&ground.naturalWidth)ctx.drawImage(ground,0,0,960,540);
if($('grid').checked)for(let y=0;y<fixture.size[1];y+=4)for(let x=0;x<fixture.size[0];x+=4){const s=support(fixture.plane,{x:origin[0]+x,y:origin[1]+y});ctx.fillStyle=s.walkable?'#a3ffb62c':'#ff53534c';ctx.fillRect(x*2,y*2,8,8)}
const asset=characters[id],geometry=asset.views[view],c=myGameClip(asset,view,clip),sample=sampleMyGameClip(c,elapsed,{reducedMotion:$('reduced').checked,holding:clip.includes('guard')}),p=projectMyGameCharacter({asset:geometry,foot:{x:foot.x-origin[0],y:foot.y-origin[1]},supportHeight:0,airborneHeight:0,worldUnit:2,assetPixelsPerWorldPixel:fixture.assetPixelsPerWorldPixel,devicePixelRatio:1});
const nodes=fixture.props.map(o=>({depth:(o.y+o.h-origin[1]),draw(){const im=image(o.asset);if(im.complete)ctx.drawImage(im,(o.x-origin[0])*2,(o.y-origin[1])*2,o.w*2,o.h*2)}}));nodes.push({depth:p.depth,draw(){ctx.fillStyle='#14202855';ctx.beginPath();ctx.ellipse(p.shadow.x,p.shadow.y,15,3.5,0,0,Math.PI*2);ctx.fill();const f=sample.frame,im=image(f.asset);if(im.complete)ctx.drawImage(im,...f.rect,p.left+f.cropOffset[0]*p.sourceUnit,p.top+f.cropOffset[1]*p.sourceUnit,f.rect[2]*p.sourceUnit,f.rect[3]*p.sourceUnit)}});nodes.sort((a,b)=>a.depth-b.depth).forEach(n=>n.draw());
$('status').textContent=id+' · '+view+' · '+clip+' · pose '+(sample.index+1)+'/'+c.frames.length+'\\nGround: '+support(fixture.plane,foot).material+' · world foot '+foot.x.toFixed(1)+', '+foot.y.toFixed(1)+'\\nCoverage: '+(geometry.status||'legacy snapshot')+(geometry.missingClips?.length?' · unavailable clips: '+geometry.missingClips.join(', '):'')+(missing?' · requested movement direction has no drawn clip; showing selected view':'');requestAnimationFrame(draw)}requestAnimationFrame(draw);
</script></html>`;
}
