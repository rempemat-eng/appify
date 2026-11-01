"""The Godot game's landscape screens (lane R, 25 Oct): runs the game at each window size, saves a
screenshot, and reports the scale main/pixel_screen.gd chooses, the black bars, and the share of the
window the HUD's parts cover. A desktop window under Xvfb, not a phone.

  GODOT=/path/to/Godot_v4.7.2 python3 scripts/playtest/godot_screens.py [--out DIR]

Needs Xvfb on DISPLAY (default :96) or a real display. Writes DIR/REPORT.md and DIR/<w>x<h>.png
(default artifacts/godot-screens, git-ignored with artifacts/).
"""
import argparse
import math
import os
import subprocess
import sys
from pathlib import Path

ART = (960, 540)
# window sizes in device px: desktop first, then phones turned to landscape
SCREENS = [
    ('1920x1080 desktop', 1920, 1080),
    ('1280x720 desktop', 1280, 720),
    ('3840x2160 4K', 3840, 2160),
    ('iPhone 17 Pro landscape (874x402@3)', 2622, 1206),
    ('iPhone SE landscape (667x375@2)', 1334, 750),
    ('Pixel 9 landscape (915x412@2.625)', 2402, 1082),
]
# the HUD's parts on the art grid (game/ui/hud.gd at 8 texel margins): meters and the quest panel at
# top left, Glint at top right, the prompt at bottom right, in texels as drawn in the 1080p screenshot
# with an active quest and a three-digit Glint (x, y, w, h)
HUD_PARTS = {'meters': (8, 8, 59, 22), 'quest panel': (8, 33, 232, 43), 'glint': (927, 8, 25, 11),
             'prompt': (898, 516, 54, 16)}


def choose_scale(w, h, mode='fill'):
    """main/pixel_screen.gd choose_scale."""
    k = min(w / ART[0], h / ART[1])
    whole = math.floor(k + 0.0001)
    return max(whole, 1.0) if mode == 'whole' or abs(k - whole) < 0.0001 else k


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default='artifacts/godot-screens')
    ap.add_argument('--no-shots', action='store_true', help='only the arithmetic, no Godot runs')
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    godot = os.environ.get('GODOT', 'godot')
    env = {**os.environ, 'DISPLAY': os.environ.get('DISPLAY', ':96')}
    hud_area = sum(w * h for (_, _, w, h) in HUD_PARTS.values())
    lines = ['# Godot screens', '', '> A desktop window under Xvfb, not a phone: no safe areas, notches, touch or GPU.', '',
             '| Screen | Window | Scale (fill) | Bars (fill) | Scale (whole) | Bars (whole) | HUD share | Shot |',
             '| --- | --- | --- | --- | --- | --- | --- | --- |']
    failed = 0
    for name, w, h in SCREENS:
        row = [name, f'{w}x{h}']
        for mode in ('fill', 'whole'):
            k = choose_scale(w, h, mode)
            bx, by = (w - ART[0] * k) / 2, (h - ART[1] * k) / 2
            row += [f'{k:.3g}', f'{bx:.0f} px each side' if bx >= 1 else (f'{by:.0f} px top and bottom' if by >= 1 else 'none')]
        row.append(f'{100 * hud_area / (ART[0] * ART[1]):.1f} %')
        shot = out / f'{w}x{h}.png'
        if not a.no_shots:
            r = subprocess.run([godot, '--path', 'game', '--audio-driver', 'Dummy', '--resolution', f'{w}x{h}',
                                '--', '--fresh', f'--shot={shot.resolve()}'], env=env, capture_output=True, text=True,
                               timeout=180)
            errors = [ln for ln in (r.stdout + r.stderr).splitlines() if 'SCRIPT ERROR' in ln or ln.startswith('ERROR')]
            ok = r.returncode == 0 and shot.exists() and not errors
            failed += not ok
            row.append(f'[{shot.name}]({shot.name})' if ok else f'**failed** {errors[:1]}')
        else:
            row.append('-')
        lines.append('| ' + ' | '.join(row) + ' |')
    lines += ['', 'The HUD draws on the art grid, so its share of the picture is the same at every size; at a',
              'fractional scale it is drawn with the sharp-bilinear shader like the world.', '']
    (out / 'REPORT.md').write_text('\n'.join(lines))
    print('\n'.join(lines))
    sys.exit(1 if failed else 0)


if __name__ == '__main__':
    main()
