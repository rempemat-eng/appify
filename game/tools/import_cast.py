#!/usr/bin/env python3
"""Copy the redrawn cast into the game: python3 game/tools/import_cast.py <castwork out dir> [id ...]

The cast is drawn and animated by the procedural rig in the castwork (Claude A's cast lane): for
each character it writes out/<id>/<clip>_<F>_NN.png (one 160 x 144 cell per drawing, foot pivot
at (80, 136)), out/<id>/manifest.json (timings, release frames, anchors per drawing and facing)
and a frames.tres for Codex's studio.  This tool turns one character's folder into what the
game loads, in game/assets/characters/<id>/:

  sheets/<clip>_<F>.png   one horizontal strip per clip and facing (S, N, E, W), cells in order;
                          a weapon clip also has sheets/<clip>_<F>_<tag>.png per aim (contract v2)
  frames.tres             a SpriteFrames: animation <clip>_<F> = AtlasTexture regions of the
                          strip, with the manifest's per-drawing durations (relative to 1 s);
                          <clip>_<D> for the turn in-betweens (SE, NE, SW, NW) of the clips
                          the manifest lists in turn_inbetweens (contract v2.9)
  manifest.json           the castwork manifest, with each frame's sheet and region added

The player reads timing, release frames, anchors and walk speed from manifest.json and drives
the frames itself (actors/cast_sprite.gd), so the .tres durations are for the editor preview.
Every frame is checked for size and its sha256 against the manifest before it is copied.
"""
import hashlib
import json
import os
import sys

from PIL import Image

GAME = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def import_char(src_root, cid):
    src = os.path.join(src_root, cid)
    man = json.load(open(os.path.join(src, 'manifest.json')))
    cw, ch = man['frame_size']
    dst = os.path.join(GAME, 'assets', 'characters', cid)
    os.makedirs(os.path.join(dst, 'sheets'), exist_ok=True)
    subs, anims = [], []
    for clip, ce in man['clips'].items():
        durs = ce['durations']
        sets = []
        for fc, fe in ce['facings'].items():
            sets.append(('%s_%s' % (clip, fc), fe['frames'], None))
            for tag, ae in fe.get('aims', {}).items():      # weapon aims within the facing (contract v2)
                sets.append(('%s_%s_%s' % (clip, fc, tag), ae['frames'], '%s_%s' % (clip, fc) if tag == '0' else None))
        for d, te in ce.get('turns', {}).items():           # turn in-betweens (contract v2.9)
            sets.append(('%s_%s' % (clip, d), te['frames'], None))
        for name, frames, same_as in sets:
            sheet_name = same_as or name                     # aim 0 is the facing's own drawings: no second strip
            if same_as is None:
                sheet = Image.new('RGBA', (cw * len(frames), ch), (0, 0, 0, 0))
            for i, fr in enumerate(frames):
                p = os.path.join(src, fr['file'])
                if same_as is None:
                    data = open(p, 'rb').read()
                    if hashlib.sha256(data).hexdigest() != fr['sha256']:
                        sys.exit('%s: sha256 does not match the manifest' % p)
                    im = Image.open(p).convert('RGBA')
                    if im.size != (cw, ch):
                        sys.exit('%s: %s, expected %dx%d' % (p, im.size, cw, ch))
                    sheet.paste(im, (i * cw, 0))
                fr['sheet'] = 'sheets/%s.png' % sheet_name
                fr['region'] = [i * cw, 0, cw, ch]
            if same_as is None:
                sheet.save(os.path.join(dst, 'sheets', name + '.png'), optimize=True)
            items = []
            for i, d in enumerate(durs):
                sid = 'a_%s_%d' % (sheet_name, i)
                if same_as is None:
                    subs.append('[sub_resource type="AtlasTexture" id="%s"]\natlas = ExtResource("%s")\nregion = Rect2(%d, 0, %d, %d)\n'
                                % (sid, name, i * cw, cw, ch))
                items.append('{"duration": %.4f, "texture": SubResource("%s")}' % (d, sid))
            anims.append((name, ce['loop'], items, same_as is None))
        ce.pop('frames', None)          # the east copy; the game reads facings
    ext = ['[ext_resource type="Texture2D" path="res://assets/characters/%s/sheets/%s.png" id="%s"]' % (cid, n, n)
           for n, _, _, own in anims if own]
    body = ',\n'.join('{"frames": [%s], "loop": %s, "name": &"%s", "speed": 1.0}' % (', '.join(it), 'true' if lp else 'false', n)
                      for n, lp, it, _ in anims)
    tres = ('[gd_resource type="SpriteFrames" load_steps=%d format=3]\n\n' % (len(ext) + len(subs) + 1)
            + '\n'.join(ext) + '\n\n' + '\n'.join(subs) + '\n[resource]\nanimations = [\n' + body + '\n]\n')
    open(os.path.join(dst, 'frames.tres'), 'w').write(tres)
    man['source'] = 'castwork out/%s (procedural rig), imported by game/tools/import_cast.py' % cid
    json.dump(man, open(os.path.join(dst, 'manifest.json'), 'w'), indent=1)
    n = sum(len(fe['frames']) for ce in man['clips'].values() for fe in ce['facings'].values())
    print('%s: %d clips x %d facings, %d drawings -> %s' % (cid, len(man['clips']), len(man['directions']), n, dst))


if __name__ == '__main__':
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    root = sys.argv[1]
    ids = sys.argv[2:] or sorted(d for d in os.listdir(root) if os.path.exists(os.path.join(root, d, 'manifest.json')))
    for cid in ids:
        import_char(root, cid)
