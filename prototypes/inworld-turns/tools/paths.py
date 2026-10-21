"""Edge paths: leave, tired, walking past, interrupted walks, reduced motion, timing off, touch sizes, a narrow phone."""
import asyncio, json, os, sys, time
from playwright.async_api import async_playwright
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from play import st, tap, tapbtn, tapworld, until, SH, URL
OUT = []
def log(*a): OUT.append(' '.join(str(x) for x in a))

async def page(p, w=402, h=874, qs='?seed=11'):
    b = await p.chromium.launch()
    ctx = await b.new_context(viewport={'width': w, 'height': h}, device_scale_factor=3, is_mobile=True, has_touch=True)
    pg = await ctx.new_page(); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None)
    await pg.goto(URL + qs); await pg.wait_for_timeout(1000)
    await tapbtn(pg, 'howto-go'); await pg.wait_for_timeout(200)
    return b, pg, errs

def small(btns): return [(b['id'], round(b['w']), round(b['h'])) for b in btns if b['w'] < 44 or b['h'] < 44]

async def to_fight(pg):
    await pg.evaluate('NA.spawnNow()')
    await until(pg, lambda s: any(f['kind'] == 'glare' for f in s['foes']), 5000)
    await pg.evaluate('NA.glareTo(176, 276)')
    await pg.evaluate('NA.teleport(164, 280)')
    await until(pg, lambda s: s['fight'] and s['fight']['awaiting'], 10000)
    await pg.wait_for_timeout(500)

async def main():
    async with async_playwright() as p:
        # 1. walking past: the glare lingers by the path; crossing the bridge does not start a fight
        b, pg, errs = await page(p)
        await pg.evaluate('NA.spawnNow()')
        await until(pg, lambda s: any(f['kind'] == 'glare' for f in s['foes']), 5000)
        await pg.evaluate('NA.glareTo(180, 278)')
        await pg.evaluate('NA.teleport(128, 250)')
        log('walk-past touch sizes (walk):', small((await st(pg))['buttons']))
        await tapworld(pg, 132, 340)
        await pg.wait_for_timeout(4500)
        s = await st(pg); log('walk-past: mode', s['mode'], 'bram', round(s['bram']['x']), round(s['bram']['y']))
        await pg.screenshot(path=f'{SH}/21-walk-past-no-chase.png')
        # 2. interrupted walk: two taps, the second wins, no stale path
        await tapworld(pg, 200, 420); await pg.wait_for_timeout(300); await tapworld(pg, 150, 470)
        await pg.wait_for_timeout(5000)
        s = await st(pg); log('interrupted: bram', round(s['bram']['x']), round(s['bram']['y']), 'act', s['bram']['act'], 'mode', s['mode'])
        # settings overlay
        await tapbtn(pg, 'settings'); await pg.wait_for_timeout(300)
        log('settings touch sizes:', small([b for b in (await st(pg))['buttons'] if b['id'].startswith('set') ]))
        await pg.screenshot(path=f'{SH}/22-settings.png')
        await tapbtn(pg, 'settings-close'); await pg.wait_for_timeout(200)
        # 3. leave: nothing lost, it drifts on, no instant re-meeting
        await to_fight(pg)
        s = await st(pg)
        log('fight touch sizes:', small(s['buttons']))
        await tapbtn(pg, 'leave')
        await until(pg, lambda s: s['mode'] == 'walk', 8000)
        await pg.wait_for_timeout(2500)
        s = await st(pg); log('leave: mode', s['mode'], 'hp', s['bram']['hp'], 'foes', [(f['kind'], f['state']) for f in s['foes']])
        log('errors', errs)
        await b.close()
        # 4. tired: Bramble sits down, nothing lost
        b, pg, errs = await page(p, qs='?seed=5')
        await to_fight(pg)
        await pg.evaluate('NA.setHp(3)')
        await tapbtn(pg, 'still')
        await until(pg, lambda s: s['bram']['act'] in ('lie', 'sleep'), 8000, 50)
        await pg.wait_for_timeout(900)
        await pg.screenshot(path=f'{SH}/23-tired-sits-down.png')
        await until(pg, lambda s: s['mode'] == 'walk', 12000)
        s = await st(pg); log('tired: back to walk, hp', s['bram']['hp'])
        log('errors', errs)
        await b.close()
        # 5. reduced motion and timing OFF
        b, pg, errs = await page(p, qs='?seed=9&reduced=1')
        await to_fight(pg)
        s = await st(pg); log('reduced: cam k', s['cam']['k'])
        hand = s['fight']['hand']
        c = 'loose' if 'loose' in hand else 'longshot' if 'longshot' in hand else None
        if c:
            await tapbtn(pg, 'slot-' + str(hand.index(c))); await pg.wait_for_timeout(100); await tapbtn(pg, 'hub')
            s2 = await until(pg, lambda s: s['fight'] and s['fight']['timingOpen'], 4000, 10)
            await pg.wait_for_timeout(max(0, s2['fight']['timingIn'] - 30))
            await pg.screenshot(path=f'{SH}/24-reduced-motion-still-ring.png')
        await until(pg, lambda s: s['fight'] and s['fight']['awaiting'], 10000)
        await tapbtn(pg, 'timing'); await tapbtn(pg, 'timing')
        s = await st(pg); log('timing now', await pg.evaluate('NA.settings.timing'))
        hand = s['fight']['hand']
        c = next((h for h in hand if h in ('loose', 'stretch')), None)
        if c:
            await tapbtn(pg, 'slot-' + str(hand.index(c))); await pg.wait_for_timeout(100); await tapbtn(pg, 'hub')
            await pg.wait_for_timeout(900)
            s = await st(pg); log('timing off: ring open?', s['fight'] and s['fight']['timingOpen'])
        log('errors', errs)
        await b.close()
        # 6. a narrower phone
        b, pg, errs = await page(p, w=360, h=780, qs='?seed=3')
        await to_fight(pg)
        await pg.wait_for_timeout(2400)
        await pg.screenshot(path=f'{SH}/25-narrow-360.png')
        log('narrow touch sizes:', small((await st(pg))['buttons']))
        log('errors', errs)
        await b.close()
    print('\n'.join(OUT))
if __name__ == '__main__':
    asyncio.run(main())
