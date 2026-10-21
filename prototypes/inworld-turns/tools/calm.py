"""Capture a Glare being calmed: it turns gold, folds into a spark and drifts home."""
import asyncio, os, sys
from playwright.async_api import async_playwright
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from play import st, tapbtn, until, SH
from paths import page, to_fight
async def main():
    async with async_playwright() as p:
        b, pg, errs = await page(p, qs='?seed=4')
        await to_fight(pg)
        await pg.evaluate('NA.foeHp(3)')
        s = await st(pg); hand = s['fight']['hand']
        c = next(h for h in hand if h in ('stretch', 'loose', 'longshot'))
        await tapbtn(pg, 'slot-' + str(hand.index(c))); await pg.wait_for_timeout(120); await tapbtn(pg, 'hub')
        await until(pg, lambda s: s['fight'] and s['fight']['foes'][0]['hp'] == 0, 6000, 20)
        await pg.wait_for_timeout(450); await pg.screenshot(path=f'{SH}/26-calmed-gold.png')
        await pg.wait_for_timeout(500); await pg.screenshot(path=f'{SH}/27-folds-into-spark.png')
        print('errors', errs); await b.close()
asyncio.run(main())
