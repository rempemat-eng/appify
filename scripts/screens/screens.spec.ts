import { mkdir } from 'node:fs/promises';
import { expect, test, type Locator, type Page } from '@playwright/test';
import { makeSavedGame } from './fixtures';

const screens = [
  'onboarding',
  'garden',
  'hotbar',
  'menu',
  'companions',
  'nap-sheet',
  'welcome-back',
  'missions',
  'shop',
  'arena',
  'battle',
  'journal',
] as const;
type Screen = (typeof screens)[number];

async function click(page: Page, target: Locator) {
  await target.click();
  await page.clock.runFor(700);
}

async function prepare(page: Page, screen: Screen) {
  switch (screen) {
    case 'onboarding':
      await expect(
        page.getByRole('button', { name: 'Plant MOSSLING, habit REST', exact: true }),
      ).toBeVisible();
      break;
    case 'garden':
    case 'hotbar':
      await expect(
        page.getByLabel('Your garden. Tap to walk DOZEBUD around.', { exact: true }),
      ).toBeVisible();
      break;
    case 'menu':
      await click(page, page.getByRole('button', { name: /^Open the menu\./ }));
      await expect(page.getByRole('heading', { name: 'COMPANION', exact: true })).toBeVisible();
      break;
    case 'companions':
      await click(page, page.getByRole('button', { name: /Change companion$/ }));
      await expect(page.getByText('COMPANIONS', { exact: true })).toBeVisible();
      break;
    case 'nap-sheet':
      await click(page, page.getByRole('button', { name: 'Take a nap', exact: true }));
      await expect(page.getByRole('heading', { name: 'TAKE A NAP', exact: true })).toBeVisible();
      break;
    case 'welcome-back':
      await expect(page.getByRole('heading', { name: 'WELCOME BACK', exact: true })).toBeVisible();
      await expect(
        page.getByRole('button', { name: 'BACK TO THE GARDEN', exact: true }),
      ).toBeVisible();
      break;
    case 'missions':
      await click(page, page.getByRole('tab', { name: /^MISSIONS/ }));
      await expect(
        page.getByRole('heading', { name: 'BEYOND THE GARDEN GATE', exact: true }),
      ).toBeVisible();
      break;
    case 'shop':
      await click(page, page.getByRole('tab', { name: /^SHOP/ }));
      await expect(page.getByText('GROW YOUR GARDEN', { exact: true })).toBeVisible();
      break;
    case 'arena':
    case 'battle':
      await click(page, page.getByRole('tab', { name: /^ARENA/ }));
      await expect(page.getByRole('button', { name: 'SPAR WITH DAVE', exact: true })).toBeVisible();
      if (screen === 'battle') {
        await click(page, page.getByRole('button', { name: 'SPAR WITH DAVE', exact: true }));
        await expect(
          page.getByRole('switch', { name: 'Auto sparring at double speed', exact: true }),
        ).toBeVisible();
      }
      break;
    case 'journal':
      await click(page, page.getByRole('button', { name: /^Open the menu\./ }));
      await click(page, page.getByRole('tab', { name: 'Journal', exact: true }));
      await click(page, page.getByRole('button', { name: 'OPEN THE FIELD JOURNAL', exact: true }));
      await expect(page.getByText('FIELD JOURNAL', { exact: true })).toBeVisible();
      break;
  }
}

async function overflow(page: Page, screen: Screen) {
  return page.evaluate((current) => {
    const problems: string[] = [];
    if (
      document.documentElement.scrollWidth > innerWidth + 1 ||
      document.body.scrollWidth > innerWidth + 1
    )
      problems.push(
        `Document width ${Math.max(document.documentElement.scrollWidth, document.body.scrollWidth)} > viewport ${innerWidth}`,
      );
    for (const element of document.querySelectorAll<HTMLElement>('body *')) {
      const style = getComputedStyle(element);
      const rect = element.getBoundingClientRect();
      if (
        rect.width <= 0 ||
        rect.height <= 0 ||
        rect.right <= 0 ||
        rect.left >= innerWidth ||
        rect.bottom <= 0 ||
        rect.top >= innerHeight ||
        style.visibility === 'hidden' ||
        style.display === 'none'
      )
        continue;
      if (
        ['auto', 'scroll'].includes(style.overflowX) &&
        element.scrollWidth > element.clientWidth + 1
      ) {
        // These two existing controls intentionally scroll sideways. Keep the
        // exception tied to their contents and horizontal-only scrolling, so a
        // wider page or overflowing vertical sheet still fails.
        const intentionalRail =
          style.overflowY === 'hidden' &&
          ((current === 'companions' &&
            element.querySelectorAll('[role="button"][aria-label^="Preview "]').length > 1) ||
            (current === 'battle' &&
              element.querySelectorAll('[role="button"][aria-label$="tap to select"]').length > 0));
        if (intentionalRail) continue;
        problems.push(
          `${element.getAttribute('aria-label') ?? element.getAttribute('role') ?? element.tagName}: horizontal scroll ${element.scrollWidth} > ${element.clientWidth}`,
        );
      }
    }
    return problems;
  }, screen);
}

for (const screen of screens) {
  test(screen, async ({ page, browser }, testInfo) => {
    const diagnostics: string[] = [];
    const night = testInfo.project.metadata.timeOfDay === 'night';
    const now = Date.parse(`2026-10-17T${night ? '22' : '14'}:00:00Z`);
    const reduced = testInfo.project.metadata.motion === 'reduced';
    page.on('console', (message) => {
      if (message.type() === 'error') diagnostics.push(`console.error: ${message.text()}`);
    });
    page.on('pageerror', (error) => diagnostics.push(`pageerror: ${error.message}`));
    page.on('requestfailed', (request) => {
      const reason = request.failure()?.errorText ?? 'Unknown transport error';
      if (reason !== 'net::ERR_ABORTED') diagnostics.push(`${reason}: ${request.url()}`);
    });
    page.on('response', (response) => {
      if (response.status() >= 400)
        diagnostics.push(`HTTP ${response.status()}: ${response.url()}`);
    });
    await page.context().route('**/*', (route) => {
      const url = new URL(route.request().url());
      if (url.origin === 'http://127.0.0.1:4178') return route.continue();
      diagnostics.push(`Unexpected external request: ${url.origin}${url.pathname}`);
      return route.abort();
    });
    // Pause before application timers exist, with enough margin for scheduler ticks.
    await page.clock.install({ time: new Date(now - 60_000) });
    await page.clock.pauseAt(new Date(now));
    const startup: { saved: unknown; motion: boolean } = {
      saved: screen === 'onboarding' ? null : makeSavedGame(now, screen === 'welcome-back'),
      motion: reduced,
    };
    await page.addInitScript(({ saved, motion }: { saved: unknown; motion: boolean }) => {
      localStorage.clear();
      if (saved) localStorage.setItem('screenagotchi-v1', JSON.stringify(saved));
      localStorage.setItem('screenagotchi-reduced-motion', JSON.stringify(motion));
      // Seed ambient choices only in this disposable test page.
      let seed = 7351;
      Math.random = () => {
        seed = (seed * 16807) % 2147483647;
        return (seed - 1) / 2147483646;
      };
    }, startup);
    const image = `images/${testInfo.project.name}-${screen}.png`;
    let captured = false;
    await mkdir('artifacts/screens/images', { recursive: true });
    try {
      await page.goto('/', { waitUntil: 'networkidle' });
      await expect(page.locator('#expo-generated-fonts')).toBeAttached();
      await page.evaluate(async () => {
        // CSS fonts are lazy: an unused registered face need not be loaded yet.
        // Explicitly preload the app's registered faces before timed capture.
        for (const family of [
          'PixelifySans_400Regular',
          'PixelifySans_500Medium',
          'PixelifySans_700Bold',
          'PressStart2P_400Regular',
        ]) {
          const loaded = await document.fonts.load(`14px "${family}"`);
          if (loaded.length === 0 || !document.fonts.check(`14px "${family}"`))
            throw new Error(`Font unavailable: ${family}`);
        }
      });
      await expect(
        page.getByRole('img', { name: 'A sleeping Grassling on a pillow', exact: true }),
      ).toBeVisible();
      // Font/store promises can mount the splash after an earlier clock step.
      // Advance its real timer until the existing splash actually unmounts.
      for (let step = 0; step < 8; step++) {
        await page.clock.runFor(250);
        if (
          (await page
            .getByRole('img', { name: 'A sleeping Grassling on a pillow', exact: true })
            .count()) === 0
        )
          break;
      }
      await expect(
        page.getByRole('img', { name: 'A sleeping Grassling on a pillow', exact: true }),
      ).toHaveCount(0);
      await prepare(page, screen);
      const elapsed = (await page.evaluate(() => Date.now())) - now;
      expect(elapsed, 'Scenario must settle before its fixed capture phase').toBeLessThan(5000);
      await page.clock.runFor(5000 - elapsed);
      await page.evaluate(async () => {
        await document.fonts.ready;
        for (const family of [
          'PixelifySans_400Regular',
          'PixelifySans_500Medium',
          'PixelifySans_700Bold',
          'PressStart2P_400Regular',
        ]) {
          if (!document.fonts.check(`14px "${family}"`))
            throw new Error(`Font not loaded: ${family}`);
        }
        await Promise.all(
          Array.from(document.images).map(async (asset) => {
            if (!asset.complete)
              await new Promise<void>((resolve, reject) => {
                asset.addEventListener('load', () => resolve(), { once: true });
                asset.addEventListener(
                  'error',
                  () => reject(new Error(`Image failed: ${asset.src}`)),
                  { once: true },
                );
              });
            if (!asset.naturalWidth) throw new Error(`Image has no pixels: ${asset.src}`);
          }),
        );
      });
      diagnostics.push(...(await overflow(page, screen)));
      let clip: { x: number; y: number; width: number; height: number } | undefined;
      if (screen === 'hotbar') {
        const controls = [
          ...(await page.getByRole('tab').all()),
          page.getByRole('button', { name: 'Take a nap', exact: true }),
        ];
        const boxes = await Promise.all(controls.map((control) => control.boundingBox()));
        const visible = boxes.filter((box) => box !== null);
        const viewport = page.viewportSize()!;
        const left = Math.max(0, Math.floor(Math.min(...visible.map((b) => b.x)) - 8));
        const top = Math.max(0, Math.floor(Math.min(...visible.map((b) => b.y)) - 8));
        const right = Math.min(
          viewport.width,
          Math.ceil(Math.max(...visible.map((b) => b.x + b.width)) + 8),
        );
        const bottom = Math.min(
          viewport.height,
          Math.ceil(Math.max(...visible.map((b) => b.y + b.height)) + 8),
        );
        clip = { x: left, y: top, width: right - left, height: bottom - top };
      }
      await page.screenshot({
        path: `artifacts/screens/${image}`,
        clip,
        animations: 'disabled',
        caret: 'hide',
      });
      captured = true;
      await testInfo.attach('image', {
        path: `artifacts/screens/${image}`,
        contentType: 'image/png',
      });
      expect(diagnostics, 'Console errors, failed requests or horizontal overflow').toEqual([]);
    } finally {
      if (!captured && !page.isClosed()) {
        try {
          await page.screenshot({ path: `artifacts/screens/${image}`, timeout: 3000 });
          captured = true;
        } catch {
          // Preserve the original test failure when its page cannot be captured.
        }
      }
      await testInfo.attach('capture', {
        body: JSON.stringify({
          image: captured ? image : null,
          viewport: page.viewportSize(),
          fixtureTime: new Date(now).toISOString(),
          captureTime: await page.evaluate(() => new Date().toISOString()).catch(() => null),
          browserVersion: browser.version(),
          motion: reduced ? 'reduced' : 'normal',
          timeOfDay: night ? 'night' : 'day',
          route: page.url(),
          fixture:
            screen === 'onboarding'
              ? 'fresh'
              : screen === 'welcome-back'
                ? 'settled-mission'
                : 'established-garden',
          diagnostics,
        }),
        contentType: 'application/json',
      });
    }
  });
}
