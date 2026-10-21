import asyncio, json, os, sys
from playwright.async_api import async_playwright
H = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL = 'file://' + os.path.join(H, 'index.html')
SH = os.path.join(H, 'shots')

async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch()
        ctx = await b.new_context(viewport={'width': 402, 'height': 874}, device_scale_factor=3, is_mobile=True, has_touch=True)
        pg = await ctx.new_page()
        errs = []
        pg.on('console', lambda m: errs.append(m.type + ': ' + m.text) if m.type in ('error', 'warning') else None)
        pg.on('pageerror', lambda e: errs.append('pageerror: ' + str(e)))
        await pg.goto(URL + '?seed=7')
        await pg.wait_for_timeout(1500)
        await pg.screenshot(path=f'{SH}/00-howto.png')
        st = await pg.evaluate('NA.state')
        print(json.dumps({k: st[k] for k in ('mode', 'overlay')}), [ (b['id']) for b in st['buttons']][-3:])
        go = [b for b in st['buttons'] if b['id'] == 'howto-go'][0]
        await pg.touchscreen.tap(go['x'] + go['w'] / 2, go['y'] + go['h'] / 2)
        await pg.wait_for_timeout(800)
        await pg.screenshot(path=f'{SH}/01-walk.png')
        print(errs)
        await b.close()
asyncio.run(main())
