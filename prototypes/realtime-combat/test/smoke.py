import asyncio, os, sys
from playwright.async_api import async_playwright
H = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL = 'file://' + H + '/index.html'
async def main():
    async with async_playwright() as p:
        br = await p.chromium.launch(args=['--use-gl=swiftshader', '--enable-unsafe-swiftshader'])
        ctx = await br.new_context(viewport={'width': 402, 'height': 874}, device_scale_factor=3, has_touch=True, is_mobile=True)
        pg = await ctx.new_page()
        errs = []
        pg.on('console', lambda m: errs.append(m.type + ': ' + m.text) if m.type in ('error', 'warning') else None)
        pg.on('pageerror', lambda e: errs.append('PAGEERROR ' + str(e)))
        await pg.goto(URL)
        await pg.wait_for_timeout(800)
        await pg.screenshot(path=H + '/shots/00-howto.png')
        await pg.tap('#start')
        await pg.wait_for_timeout(600)
        await pg.screenshot(path=H + '/shots/01-start.png')
        print(await pg.evaluate('JSON.stringify({b:[__game.S.br.x,__game.S.br.y], K:__game.K(), fps:__game.fps()})'))
        print('\n'.join(errs))
        await br.close()
asyncio.run(main())
