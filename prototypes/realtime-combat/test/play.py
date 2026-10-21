"""Play the action prototype through with real touch input (CDP touch events): walk the path,
fight the field Glares (dodge telegraphs, stand still to draw, tap Glares or press LOOSE),
walk to the stone ring and calm the Static Storm. Screenshots at the moments that matter.

usage: python3 play.py portrait|landscape [--tired]"""
import asyncio, json, math, os, sys, time
from playwright.async_api import async_playwright

H = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL = 'file://' + H + '/index.html?skiphowto'
MODE = sys.argv[1] if len(sys.argv) > 1 else 'portrait'
TIRED = '--tired' in sys.argv
VP = {'portrait': (402, 874), 'landscape': (874, 402)}[MODE]
SHOTS = os.path.join(H, 'shots')
TAG = 'p' if MODE == 'portrait' else 'l'
log = []
dbg = []


class Touch:
    """Multi-touch through CDP: every event carries all active points."""

    def __init__(self, cdp):
        self.cdp, self.pts, self.nid = cdp, {}, 1

    async def _send(self, kind):
        pts = [{'x': x, 'y': y, 'id': i, 'radiusX': 6, 'radiusY': 6, 'force': 1} for i, (x, y) in self.pts.items()]
        await self.cdp.send('Input.dispatchTouchEvent', {'type': kind, 'touchPoints': pts})

    async def down(self, x, y):
        i = self.nid; self.nid += 1
        self.pts[i] = (x, y); await self._send('touchStart'); return i

    async def move(self, i, x, y):
        self.pts[i] = (x, y); await self._send('touchMove')

    async def up(self, i):
        del self.pts[i]
        await self.cdp.send('Input.dispatchTouchEvent', {'type': 'touchEnd', 'touchPoints': [
            {'x': x, 'y': y, 'id': j} for j, (x, y) in self.pts.items()]})

    async def tap(self, x, y):
        i = await self.down(x, y); await asyncio.sleep(0.05); await self.up(i)


async def main():
    async with async_playwright() as p:
        br = await p.chromium.launch()
        ctx = await br.new_context(viewport={'width': VP[0], 'height': VP[1]}, device_scale_factor=3, has_touch=True, is_mobile=True)
        pg = await ctx.new_page()
        errs = []
        pg.on('console', lambda m: errs.append(m.type + ': ' + m.text) if m.type in ('error',) else None)
        pg.on('pageerror', lambda e: errs.append('PAGEERROR ' + str(e)))
        await pg.goto(URL)
        await pg.wait_for_timeout(700)
        cdp = await ctx.new_cdp_session(pg)
        T = Touch(cdp)
        W, Hh = VP
        anchor = (W * 0.3, Hh * 0.62) if MODE == 'portrait' else (W * 0.22, Hh * 0.62)
        state = {'stick': None, 'shots': set(), 'fps': [], 'dodges': 0, 'flicks': 0, 'taps': 0, 'looses': 0, 'hits_taken': 0}

        async def info():
            return await pg.evaluate('__game.info()')

        async def shot(name):
            if name in state['shots']:
                return
            state['shots'].add(name)
            path = os.path.join(SHOTS, f'{TAG}-{name}.png')
            await pg.screenshot(path=path)
            log.append('shot ' + path)

        async def stick_to(dx, dy, mag=1.0):
            """Hold a drag from the anchor towards (dx, dy)."""
            d = math.hypot(dx, dy) or 1
            tx, ty = anchor[0] + dx / d * 40 * mag, anchor[1] + dy / d * 40 * mag
            if state['stick'] is None:
                state['stick'] = await T.down(*anchor)
                await T.move(state['stick'], anchor[0] + dx / d * 14, anchor[1] + dy / d * 14)
            await T.move(state['stick'], tx, ty)

        async def release():
            if state['stick'] is not None:
                await T.up(state['stick']); state['stick'] = None

        async def press(sel):
            box = await pg.locator(sel).bounding_box()
            if not box:
                log.append('no box for ' + sel); return
            await T.tap(box['x'] + box['width'] / 2, box['y'] + box['height'] / 2)

        async def flick(dx, dy):
            await release()
            d = math.hypot(dx, dy) or 1
            x0, y0 = anchor
            i = await T.down(x0, y0)
            for k in range(1, 4):
                await T.move(i, x0 + dx / d * 18 * k, y0 + dy / d * 18 * k)
                await asyncio.sleep(0.02)
            await T.up(i)
            state['flicks'] += 1

        async def walk_to(x, y, tol=6, timeout=25):
            t0 = time.time()
            last, stuck = None, 0
            while time.time() - t0 < timeout:
                s = await info()
                b = s['b']
                if s['field'] == 'fight' or s['arena'] in ('intro', 'fight'):
                    await release(); return s
                dx, dy = x - b['x'], y - b['y']
                if math.hypot(dx, dy) < tol:
                    await release(); return s
                if last and math.hypot(b['x'] - last[0], b['y'] - last[1]) < 0.3:
                    stuck += 1
                else:
                    stuck = 0
                last = (b['x'], b['y'])
                if stuck > 8:  # nudge sideways round a corner
                    await stick_to(-dy, dx); await asyncio.sleep(0.3); stuck = 0
                await stick_to(dx, dy)
                await asyncio.sleep(0.06)
            await release()
            log.append(f'walk_to timeout ({x},{y}) at {last}')
            return await info()

        async def fight(until, label, tired=False, timeout=150):
            t0 = time.time()
            still_since = None
            n = 0
            while time.time() - t0 < timeout:
                s = await info()
                n += 1
                if n % 25 == 0:
                    state['fps'].append(await pg.evaluate('__game.fps()'))
                if until(s):
                    await release(); return s
                if s['down']:
                    await release(); return s
                if label == 'field' and s['field'] == 'idle' and not tired:  # wandered off: go back in
                    await walk_to(150, 225); continue
                b = s['b']
                # screenshots of the moments that matter
                if s['tels'] and s['tels'][0]['remain'] < 0.5:
                    await shot(f'{label}-telegraph')
                if b['aim'] >= 3:
                    await shot(f'{label}-drawn')
                if s['phase'] == 2 and any(f['shield'] for f in s['foes']):
                    await shot('arena-split-shield')
                if s['phase'] == 3 and s['tels'] and s['tels'][0]['type'] == 'sweep' and s['tels'][0]['remain'] < 0.7:
                    await shot('arena-last-gust')
                if tired:
                    await release(); await asyncio.sleep(0.1); continue
                threat = [t for t in s['tels'] if t['inside'] and t['remain'] < 0.75]
                if s['tels']:
                    dbg.append((s['t'], b['st'], [(t['type'], t['inside'], round(t['remain'], 2)) for t in s['tels']]))
                if threat and b['st'] in ('free', 'shoot', 'hurt') and b['dodgeCd'] <= 0:
                    t = threat[0]
                    if t['type'] == 'ping':
                        ex, ey = b['x'] - t['c']['x'], b['y'] - t['c']['y']
                        if math.hypot(ex, ey) < 1:
                            ex, ey = 1, 0
                    else:
                        ex, ey = t['esc']
                    # alternate the two ways to dodge
                    if state['dodges'] % 2 == 0:
                        await flick(ex, ey)
                    else:
                        await release(); await stick_to(ex, ey)
                        await press('#dodge'); await asyncio.sleep(0.05); await release()
                    state['dodges'] += 1
                    still_since = None
                    await asyncio.sleep(0.35)
                    continue
                inside = [t for t in s['tels'] if t['inside']]
                if inside:  # cannot roll yet: walk out of it
                    t = inside[0]
                    if t['type'] == 'ping':
                        ex, ey = b['x'] - t['c']['x'], b['y'] - t['c']['y']
                    else:
                        ex, ey = t['esc']
                    await stick_to(ex, ey + 0.001); still_since = None
                    await asyncio.sleep(0.06); continue
                foes = [f for f in s['foes'] if f['st'] not in ('calming',)]
                if not foes:
                    await release(); await asyncio.sleep(0.1); continue
                near = min(foes, key=lambda f: math.hypot(f['x'] - b['x'], f['y'] - b['y']))
                d = math.hypot(near['x'] - b['x'], near['y'] - b['y'])
                if d > 105 and s['arena'] != 'fight':  # step closer (Glares do not chase)
                    await stick_to(near['x'] - b['x'], near['y'] - b['y']); still_since = None
                    await asyncio.sleep(0.08); continue
                if s['arena'] == 'fight' and ((b['x'] - 82) / 52) ** 2 + ((b['y'] - 410) / 30) ** 2 > 0.45 and not s['tels']:
                    await stick_to(82 - b['x'], 410 - b['y']); still_since = None  # keep off the rim
                    await asyncio.sleep(0.12); continue
                if d < 18 and not s['tels']:  # too close: step back
                    await stick_to(b['x'] - near['x'], b['y'] - near['y'] + 0.01); still_since = None
                    await asyncio.sleep(0.15); continue
                await release()
                if still_since is None:
                    still_since = time.time()
                # stand still to draw, then loose: tap the Glare or press LOOSE
                if time.time() - still_since > (0.5 if s['tels'] else 1.0) or b['aim'] >= 3:
                    target = [f for f in foes if not f['shield']] or foes
                    tg = min(target, key=lambda f: math.hypot(f['x'] - b['x'], f['y'] - b['y']))
                    if (state['taps'] + state['looses']) % 2 == 0:
                        await T.tap(tg['css']['x'], tg['css']['y']); state['taps'] += 1
                    else:
                        await press('#loose'); state['looses'] += 1
                    still_since = None
                    await asyncio.sleep(0.25)
                else:
                    await asyncio.sleep(0.06)
            log.append(f'fight {label} timeout')
            return await info()

        await shot('01-walk')
        # ---- the field fight
        s = await walk_to(130, 200)
        await asyncio.sleep(0.4)
        await shot('02-glare-drifts-in')
        if TIRED:
            s = await fight(lambda s: s['down'], 'tired', tired=True, timeout=60)
            await asyncio.sleep(1.8)
            await shot('03-tired')
            log.append('down card shown: ' + str((await info())['down']))
            await press('#getup'); await asyncio.sleep(0.5)
            s = await info(); log.append(f"after get up hp={s['b']['hp']} field={s['field']}")
            s = await walk_to(130, 200)
            await asyncio.sleep(0.5)
            if s['field'] != 'fight':
                await asyncio.sleep(6); s = await walk_to(150, 230)
        s = await fight(lambda s: s['field'] == 'done' and not [f for f in s['foes'] if f['kind'] == 'glare'], 'field')
        log.append(f"field: {s['field']} calmed={s['calmed']} hp={s['b']['hp']}")
        await asyncio.sleep(0.4)
        await shot('04-calmed-sparks')
        await asyncio.sleep(1.2)
        await shot('05-path-quiet')
        # ---- to the stone ring
        for wp in [(130, 270), (131, 300), (136, 330), (145, 372), (128, 396), (100, 408)]:
            s = await walk_to(*wp)
            if s['arena'] in ('intro', 'fight'):
                break
            if wp == (145, 372):
                await shot('06-signpost')
        await asyncio.sleep(0.5)
        await shot('07-arena-intro')
        await asyncio.sleep(1.2)
        s = await fight(lambda s: s['arena'] in ('outro', 'done'), 'arena', timeout=200)
        log.append('events ' + json.dumps(s['events']))
        open(os.path.join(H, 'test', 'dbg.json'), 'w').write(json.dumps(dbg))
        log.append(f"arena: {s['arena']} phase={s['phase']} hp={s['b']['hp']} down={s['down']}")
        if s['down']:
            await shot('arena-tired')
        await asyncio.sleep(1.0)
        await shot('08-arena-calmed')
        await asyncio.sleep(2.2)
        await shot('09-victory')
        log.append('win card: ' + str((await info())['win']))
        if (await info())['win']:
            await press('#walkon'); await asyncio.sleep(0.6)
            await shot('10-walk-on')
        # pause menu and reduced motion toggle
        await press('#pause'); await asyncio.sleep(0.3)
        await shot('11-pause')
        await press('#optreduced'); await asyncio.sleep(0.1)
        await press('#resume'); await asyncio.sleep(0.3)
        log.append('fps samples ' + json.dumps(state['fps']))
        log.append(f"flicks={state['flicks']} dodges={state['dodges']} taps={state['taps']} looses={state['looses']}")
        log.append('errors: ' + json.dumps(errs))
        await br.close()
    print('\n'.join(log))


asyncio.run(main())
