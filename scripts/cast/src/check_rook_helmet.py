"""python3 check_rook_helmet.py: Matt, 26 Oct ("make sure the hair doesn't poke through the helmet").
In every exported Rook drawing with the bubble helmet worn (every clip, facing, turn and aim), no
pixel of his hair reaches the glass's rim or beyond: the hair lies inside the glass.  Exit 1 on a
fault."""
import json
import sys
import numpy as np
from PIL import Image
import anim
import rook
import anim_rook as A
from ew import MATS

anim.add_powered(A)
HAIR = {tuple(int(round(v)) for v in t) for t in MATS['rk_hair'].tones}
GLASS = {tuple(int(round(v)) for v in t) for t in MATS['rk_visor'].tones}


def main():
    man = json.load(open('../out/rook/manifest.json'))
    bad = n = 0
    for clip, ce in man['clips'].items():
        worn = [rook.P0(**P)['helmet'] == 'head' for P, _ in A.TABLE[clip]]
        sets = list(ce['facings'].items()) + list(ce.get('turns', {}).items())
        for fc, fe in list(ce['facings'].items()):
            sets += [(fc + '~' + t, ae) for t, ae in fe.get('aims', {}).items()]
        for fc, fe in sets:
            for i, fr in enumerate(fe['frames']):
                if not worn[i]:
                    continue
                a = np.array(Image.open('../out/rook/' + fr['file']).convert('RGBA'))
                W = a.shape[1]
                flat, op = a[..., :3].reshape(-1, 3), (a[..., 3] > 0).reshape(-1)
                hm = np.array([tuple(c) in HAIR for c in flat]) & op
                gm = np.array([tuple(c) in GLASS for c in flat]) & op
                n += 1
                hy, hx = np.divmod(np.nonzero(hm)[0], W)
                gy, gx = np.divmod(np.nonzero(gm)[0], W)
                top = gy.min()
                sel = gy < top + 26                               # the worn bubble: glass in the head's rows
                cx, cy = (gx[sel].min() + gx[sel].max()) / 2, (gy[sel].min() + gy[sel].max()) / 2
                r = max(np.ptp(gx[sel]), np.ptp(gy[sel])) / 2
                near = hy < top + 26
                out = np.hypot(hx[near] - cx, hy[near] - cy) > r - 0.5
                if out.any():
                    bad += 1
                    print('hair at or past the glass: %s %s #%d (%d px)' % (clip, fc, i, int(out.sum())))
    print('rook: %d worn-helmet drawings, hair at or past the glass in %d' % (n, bad))
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
