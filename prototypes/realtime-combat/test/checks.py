"""Smaller checks: frame rate with no screenshots in the way, walking away from Glares, keyboard
and mouse fallback, reduced motion, and the landscape layout with notch safe areas."""
import asyncio, json, os
from playwright.async_api import async_playwright

H = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL = 'file://' + H + '/index.html?skiphowto'
SH = os.path.join(H, 'shots')


async def hold_keys(pg, keys, ms):
    for k in keys:
        await pg.keyboard.down(k)
    await pg.wait_for_timeout(ms)
    for k in keys:
        await pg.keyboard.up(k)


async def main():
    out = {}
    async with async_playwright() as p:
        br = await p.chromium.launch()
        # ---- phone portrait: fps, walking away, reduced motion
        ctx = await br.new_context(viewport={'width': 402, 'height': 874}, device_scale_factor=3, has_touch=True, is_mobile=True)
        pg = await ctx.new_page()
        errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        await pg.goto(URL); await pg.wait_for_timeout(500)
        await pg.wait_for_timeout(2000)
        out['fps_walk_idle'] = await pg.evaluate('__game.fps()')
        await hold_keys(pg, ['ArrowDown'], 1500)  # keyboard walks (and runs)
        i = await pg.evaluate('__game.info()')
        out['keyboard_moved_to'] = [round(i['b']['x']), round(i['b']['y'])]
        out['field_after_keys'] = i['field']
        await pg.wait_for_timeout(5000)  # Glares drift in; stand still (the bot is not dodging here)
        out['fps_field_fight'] = await pg.evaluate('__game.fps()')
        out['foes_in_field'] = len((await pg.evaluate('__game.info()'))['foes'])
        for wx, wy in [(130, 280), (131, 330), (138, 350)]:  # walk away over the bridge: they lose interest
            for _ in range(60):
                b = (await pg.evaluate('__game.info()'))['b']
                dx, dy = wx - b['x'], wy - b['y']
                if abs(dx) < 3 and abs(dy) < 3:
                    break
                keys = (['ArrowRight'] if dx > 2 else ['ArrowLeft'] if dx < -2 else []) + (['ArrowDown'] if dy > 2 else ['ArrowUp'] if dy < -2 else [])
                await hold_keys(pg, keys, 80)
        await pg.wait_for_timeout(300)
        i = await pg.evaluate('__game.info()')
        out['after_walking_away'] = {'field': i['field'], 'b': [round(i['b']['x']), round(i['b']['y'])], 'toast': await pg.inner_text('#toast')}
        await pg.screenshot(path=os.path.join(SH, 'p-12-glares-lose-interest.png'))
        # reduced motion on, back into the field
        await pg.click('#pause'); await pg.click('#optreduced'); await pg.click('#resume')
        out['reduced'] = await pg.evaluate('__game.S && JSON.parse(localStorage.getItem("napattack-action-reduced"))')
        await pg.wait_for_timeout(4200)
        await hold_keys(pg, ['ArrowDown'], 1600)
        await pg.wait_for_timeout(3500)
        await pg.screenshot(path=os.path.join(SH, 'p-13-reduced-motion.png'))
        out['reduced_shake'] = await pg.evaluate('__game.S.shake')
        out['errors_portrait'] = errs
        await ctx.close()

        # ---- landscape with notch safe areas (iPhone: 59 px each side, 21 bottom)
        ctx = await br.new_context(viewport={'width': 874, 'height': 402}, device_scale_factor=3, has_touch=True, is_mobile=True)
        pg = await ctx.new_page()
        await pg.goto(URL); await pg.wait_for_timeout(400)
        await pg.evaluate("""() => { const r = document.documentElement.style; r.setProperty('--sal', '59px'); r.setProperty('--sar', '59px'); r.setProperty('--sab', '21px'); }""")
        await pg.wait_for_timeout(300)
        boxes = {}
        for sel in ['#who', '#chip', '#pause', '#loose', '#dodge', '#stickhint']:
            b = await pg.locator(sel).bounding_box()
            boxes[sel] = [round(v) for v in (b['x'], b['y'], b['width'], b['height'])] if b else None
        out['landscape_notch_boxes'] = boxes
        await pg.screenshot(path=os.path.join(SH, 'l-12-notch-safe-areas.png'))
        await ctx.close()

        # ---- desktop: mouse drag walks, dpr 1
        ctx = await br.new_context(viewport={'width': 1280, 'height': 800}, device_scale_factor=1)
        pg = await ctx.new_page()
        await pg.goto(URL); await pg.wait_for_timeout(400)
        b0 = (await pg.evaluate('__game.info()'))['b']
        await pg.mouse.move(400, 500); await pg.mouse.down(); await pg.mouse.move(400, 540, steps=4)
        await pg.wait_for_timeout(1200); await pg.mouse.up()
        b1 = (await pg.evaluate('__game.info()'))['b']
        out['mouse_drag_moved'] = [round(b1['x'] - b0['x']), round(b1['y'] - b0['y'])]
        out['desktop_K'] = await pg.evaluate('__game.K()')
        await pg.screenshot(path=os.path.join(SH, 'd-01-desktop.png'))
        await ctx.close()
        # ---- the how-to card on first load, both ways round
        for name, vp in (('p-00-howto', (402, 874)), ('l-00-howto', (874, 402))):
            ctx = await br.new_context(viewport={'width': vp[0], 'height': vp[1]}, device_scale_factor=3, has_touch=True, is_mobile=True)
            pg = await ctx.new_page(); await pg.goto('file://' + H + '/index.html'); await pg.wait_for_timeout(500)
            await pg.screenshot(path=os.path.join(SH, name + '.png'))
            out[name + '_start_box'] = await pg.locator('#start').bounding_box()
            await ctx.close()
        await br.close()
    print(json.dumps(out, indent=1))


asyncio.run(main())
