"""Play-test: a field fight and the arena, at 402 x 874 with touch, saving screenshots."""
import asyncio, json, os, sys, time
from playwright.async_api import async_playwright
H = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL = 'file://' + os.path.join(H, 'index.html')
SH = os.path.join(H, 'shots')
QS = sys.argv[1] if len(sys.argv) > 1 else '?seed=7'
TAG = sys.argv[2] if len(sys.argv) > 2 else ''
LOG = []

async def st(pg): return await pg.evaluate('NA.state')
async def tap(pg, x, y): await pg.touchscreen.tap(x, y)
async def tapbtn(pg, bid):
    s = await st(pg)
    for b in s['buttons'][::-1]:
        if b['id'] == bid:
            await tap(pg, b['x'] + b['w'] / 2, b['y'] + b['h'] / 2); return True
    return False
async def tapworld(pg, x, y):
    sx, sy = await pg.evaluate(f'NA.toScreen({x},{y})'); await tap(pg, sx, sy)
async def shot(pg, name): await pg.screenshot(path=f'{SH}/{TAG}{name}.png'); LOG.append('shot ' + name)
async def until(pg, cond, timeout=20000, step=100):
    t = time.time()
    while time.time() - t < timeout / 1000:
        s = await st(pg)
        if cond(s): return s
        await pg.wait_for_timeout(step)
    raise RuntimeError('timeout waiting; state=' + json.dumps({k: s[k] for k in ('mode', 'fight', 'banners')})[:600])

async def take_turn(pg, prefer, shots, timing_good=True):
    s = await until(pg, lambda s: (s['fight'] and s['fight']['awaiting']) or s['mode'] != 'fight', 30000)
    if s['mode'] != 'fight': return False
    f = s['fight']
    hand, en = f['hand'], f['energy']
    cost = {'loose': 1, 'longshot': 2, 'cover': 1, 'stretch': 0}
    choice = None
    for c in prefer(f):
        if c in ('pass', 'moss') or c.startswith('step'): choice = c; break
        if c in hand and cost[c] <= en: choice = c; break
    LOG.append(f"turn {f['turn']} hp {s['bram']['hp']} aim {s['bram']['aim']} en {en} hand {hand} foes {[(q['kind'], q['hp'], q['intent']) for q in f['foes']]} -> {choice}")
    if choice == 'pass':
        await tapbtn(pg, 'still')
    elif choice == 'moss':
        await tapbtn(pg, 'moss'); await pg.wait_for_timeout(250)
        if 'moss' in shots: await shot(pg, shots.pop('moss'))
        await tapbtn(pg, 'hub')
    elif choice.startswith('step'):
        sp = f['spots'][0]
        await tap(pg, sp['screen'][0], sp['screen'][1]); await pg.wait_for_timeout(250)
        if 'step' in shots: await shot(pg, shots.pop('step'))
        await tapbtn(pg, 'hub')
    else:
        await tapbtn(pg, 'slot-' + str(hand.index(choice))); await pg.wait_for_timeout(250)
        if 'select' in shots: await shot(pg, shots.pop('select'))
        await tapbtn(pg, 'hub')
        if choice in ('loose', 'longshot'):
            s2 = await until(pg, lambda s: s['fight'] and s['fight']['timingOpen'], 4000, 15)
            tin = s2['fight']['timingIn']
            if 'ring' in shots:
                await pg.wait_for_timeout(max(0, tin - 260)); await shot(pg, shots.pop('ring'))
                s2 = await st(pg); tin = s2['fight']['timingIn'] or 0
            if timing_good:
                await pg.wait_for_timeout(max(0, tin - 15)); await tap(pg, 200, 300)
            await pg.wait_for_timeout(120)
            if 'impact' in shots: await shot(pg, shots.pop('impact'))
    # the foes' turn
    if 'foe' in shots:
        await until(pg, lambda s: not s['fight'] or not s['fight']['awaiting'], 3000, 50)
        await pg.wait_for_timeout(1500); await shot(pg, shots.pop('foe'))
    return True

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx = await b.new_context(viewport={'width': 402, 'height': 874}, device_scale_factor=3, is_mobile=True, has_touch=True)
        pg = await ctx.new_page()
        errs = []
        pg.on('console', lambda m: errs.append(m.type + ': ' + m.text) if m.type in ('error', 'warning') else None)
        pg.on('pageerror', lambda e: errs.append('pageerror: ' + str(e)))
        await pg.goto(URL + QS)
        await pg.wait_for_timeout(1200)
        await tapbtn(pg, 'howto-go'); await pg.wait_for_timeout(300)
        # walk down the path towards the footbridge
        await tapworld(pg, 132, 262)
        await pg.wait_for_timeout(1500)
        await shot(pg, '02-walking')
        s = await until(pg, lambda s: any(f['kind'] == 'glare' and 20 < f['screen'][0] < 380 for f in s['foes']), 15000)
        await pg.wait_for_timeout(600)
        await shot(pg, '03-glare-drifts-in')
        # walk to meet it (tap it)
        g = [f for f in (await st(pg))['foes'] if f['kind'] == 'glare'][0]
        await tap(pg, g['screen'][0], g['screen'][1])
        s = await until(pg, lambda s: s['mode'] in ('intro', 'fight'), 15000, 30)
        await pg.wait_for_timeout(250)
        await shot(pg, '04-encounter')
        s = await until(pg, lambda s: s['fight'] and s['fight']['awaiting'], 8000)
        await pg.wait_for_timeout(600)
        await shot(pg, '05-field-fight')
        shots = {'select': '06-field-select', 'ring': '07-field-timing-ring', 'impact': '08-field-impact', 'foe': '09-field-foe-turn', 'step': '06b-field-step'}
        def prefer(f):
            order = []
            if f['turn'] == 1: order.append('cover')
            if f['turn'] == 2 and f['spots']: order.append('step')
            order += ['longshot', 'loose', 'stretch', 'pass']
            return order
        n = 0
        while (await st(pg))['mode'] == 'fight' and n < 14:
            await take_turn(pg, prefer, shots); n += 1
        await pg.wait_for_timeout(700)
        await shot(pg, '10-field-calmed')
        await until(pg, lambda s: s['mode'] == 'walk', 15000)
        await pg.wait_for_timeout(800)
        await shot(pg, '11-walk-on')
        # the arena
        await tapbtn(pg, 'tab-arena')
        await pg.wait_for_timeout(2500)
        await shot(pg, '12-to-the-ring')
        await until(pg, lambda s: s['fight'] and s['fight']['kind'] == 'arena' and s['fight']['awaiting'], 25000)
        await pg.wait_for_timeout(500)
        await shot(pg, '13-arena-phase1')
        shots = {'foe': '14-arena-foe-turn'}
        def prefer2(f):
            foes = f['foes']; order = []
            intents = [q['intent'] for q in foes if q['hp'] > 0]
            if 'STORM SWEEP' in intents and f['spots']: return ['step']
            if 'OVERLOAD' in intents: return ['cover', 'moss', 'pass'] if True else []
            if len(foes) > 1: order += ['loose', 'longshot', 'stretch', 'pass']
            else: order += ['longshot', 'loose', 'stretch', 'pass']
            return order
        n = 0; split_shot = False; sweep_shot = False
        while (await st(pg))['mode'] == 'fight' and n < 16:
            s = await st(pg)
            if s['fight'] and s['fight']['lane'] and not sweep_shot:
                sweep_shot = True; await shot(pg, '15-arena-sweep-telegraph')
            if s['fight'] and len(s['fight']['foes']) > 1 and not split_shot:
                split_shot = True; await pg.wait_for_timeout(300); await shot(pg, '16-arena-phase2')
                shots['ring'] = '17-arena-timing-ring'
            await take_turn(pg, prefer2, shots); n += 1
        await pg.wait_for_timeout(600)
        await shot(pg, '18-arena-victory')
        await pg.wait_for_timeout(1800)
        await shot(pg, '19-arena-celebration')
        s = await st(pg)
        LOG.append('final ' + json.dumps({'mode': s['mode'], 'banners': s['banners'], 'fight': s['fight'] and {k: s['fight'][k] for k in ('done', 'over')}}))
        await tapbtn(pg, 'walkon')
        await until(pg, lambda s: s['mode'] == 'walk', 10000)
        await pg.wait_for_timeout(1500)
        await shot(pg, '20-after-arena')
        LOG.append('stats ' + json.dumps(await pg.evaluate('NA.stats'))); LOG.append('ERRORS ' + str(errs))
        await b.close()
if __name__ == '__main__':
    try:
        asyncio.run(main())
    finally:
        print('\n'.join(LOG))
