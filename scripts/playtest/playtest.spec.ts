/**
 * The play-test harness (Claude M, 21 Oct; docs/playtest.md). Plays the game's main flows in
 * Chromium at three phone sizes and at art densities 1 and 2, takes a screenshot at every
 * step and records what it measured (the HUD's and hotbar's size, the smallest touch target,
 * whether the interface drew its 2x icons, browser errors) for `scripts/playtest/run.mjs` to
 * turn into a short report. Lane R runs it twice a day.
 *
 * This is a desktop browser emulating a phone's viewport, pixel ratio and touch. It is not a
 * phone: it says nothing about a phone's GPU, memory, frame rate, audio, safe areas or
 * native behaviour.
 */
import { mkdir, writeFile } from 'node:fs/promises';
import { expect, test, type Page, type TestInfo } from '@playwright/test';
import { makeSavedGame } from '../screens/fixtures';

const ORIGIN = 'http://127.0.0.1:4178';
const OUT = 'artifacts/playtest';
const SAVE_KEY = 'screenagotchi-v1';
const MOTION_KEY = 'screenagotchi-reduced-motion';
const SPLASH = 'A sleeping Grassling on a pillow';
const WALK_LAYER =
  /^(Your garden\. Tap to walk .+ around\.|Walk around home garden\. Tap where to go\.)$/;
const FONTS = [
  'PixelifySans_400Regular',
  'PixelifySans_500Medium',
  'PixelifySans_700Bold',
  'PressStart2P_400Regular',
];

type Flow = {
  /** a fresh profile (onboarding) or the established garden fixture */
  fresh?: boolean;
  /** 22:00 instead of 14:00 UTC (the garden's night starts at 21:00) */
  night?: boolean;
  reduced?: boolean;
  play: (run: Run) => Promise<void>;
};

type Step = { name: string; image: string; note?: string };
type Measure = Record<string, number | string | boolean | null>;

class Run {
  steps: Step[] = [];
  measures: Measure = {};
  notes: string[] = [];
  constructor(
    readonly page: Page,
    readonly info: TestInfo,
    readonly flow: string,
  ) {}

  async settle(ms = 700) {
    await this.page.clock.runFor(ms);
  }

  async tap(target: ReturnType<Page['getByRole']>, ms = 700) {
    await target.tap();
    await this.settle(ms);
  }

  /** A finger on the world's tap layer at a share of its width and height. */
  async tapWorld(fx: number, fy: number, ms = 700) {
    const layer = this.page.getByRole('button', { name: WALK_LAYER }).first();
    const area = (await layer.boundingBox())!;
    await this.page.touchscreen.tap(area.x + area.width * fx, area.y + area.height * fy);
    await this.settle(ms);
  }

  async shot(name: string, note?: string) {
    const image = `${this.info.project.name}/${this.flow}-${String(this.steps.length + 1).padStart(2, '0')}-${name}.png`;
    await mkdir(`${OUT}/images/${this.info.project.name}`, { recursive: true });
    await this.page.screenshot({
      path: `${OUT}/images/${image}`,
      animations: 'disabled',
      caret: 'hide',
    });
    this.steps.push({ name, image, note });
  }

  /** The HUD bar, the hotbar, the smallest visible touch target and the icon grid in use. */
  async measureInterface() {
    Object.assign(this.measures, await this.page.evaluate(interfaceMetrics));
  }
}

/** Runs in the page: sizes in CSS px of the interface on screen now. */
function interfaceMetrics() {
  const tabs = [...document.querySelectorAll('[role=tab]')].map((el) => el.getBoundingClientRect());
  const nap = document.querySelector('[aria-label="Take a nap"]')?.getBoundingClientRect();
  const menu = document.querySelector('[aria-label^="Open the menu."]')?.getBoundingClientRect();
  // controls a player taps in the HUD and hotbar (the world's tap layer is excluded)
  const controls = [...document.querySelectorAll('[role=tab],[role=button],[role=switch]')]
    .filter((el) => !/Tap where to go|Tap to walk/.test(el.getAttribute('aria-label') ?? ''))
    .map((el) => ({ el, r: el.getBoundingClientRect() }))
    .filter(
      (c): c is { el: Element; r: DOMRect } =>
        !!c.r &&
        c.r.width > 0 &&
        c.r.height > 0 &&
        c.r.bottom > 0 &&
        c.r.top < innerHeight &&
        c.r.right > 0 &&
        c.r.left < innerWidth,
    );
  const under = controls.filter(({ r }) => Math.min(r.width, r.height) < 44 - 0.5);
  const small = under.length;
  const smallLabels = under
    .map(
      ({ el, r }) =>
        `${(el.getAttribute('aria-label') ?? el.textContent ?? '?').slice(0, 40)} (${Math.round(r.width)}x${Math.round(r.height)})`,
    )
    .join('; ');
  const svgs = [...document.querySelectorAll('svg[viewBox]')].map((s) => s.getAttribute('viewBox'));
  return {
    tabHeight: tabs.length ? Math.round(Math.max(...tabs.map((r) => r.height)) * 10) / 10 : null,
    tabWidth: tabs.length ? Math.round(Math.min(...tabs.map((r) => r.width)) * 10) / 10 : null,
    hotbarTop: tabs.length ? Math.round(Math.min(...tabs.map((r) => r.top))) : null,
    napButton: nap ? `${Math.round(nap.width)}x${Math.round(nap.height)}` : null,
    menuButton: menu ? `${Math.round(menu.width)}x${Math.round(menu.height)}` : null,
    hudBottom: menu ? Math.round(menu.bottom) : null,
    controls: controls.length,
    controlsUnder44: small,
    smallControls: smallLabels || null,
    icons2x: svgs.filter((v) => v === '0 0 32 32').length,
    icons1x: svgs.filter((v) => v === '0 0 16 16').length,
    horizontalOverflow: document.documentElement.scrollWidth > innerWidth + 1,
  };
}

const flows: Record<string, Flow> = {
  onboarding: {
    fresh: true,
    async play(run) {
      const { page } = run;
      await expect(page.getByRole('button', { name: /^Plant MOSSLING/ })).toBeVisible();
      await run.shot('seeds');
      await run.tap(page.getByRole('button', { name: /^Plant MOSSLING/ }));
      await run.tap(page.getByRole('button', { name: 'PLANT A SEED', exact: true }), 1500);
      await page.getByLabel('Your name').fill('Tilly');
      await page.getByLabel('Grassling name').fill('Moss');
      await run.shot('names');
      await run.tap(page.getByRole('button', { name: 'GROW MY GARDEN', exact: true }), 3000);
      await expect(page.getByRole('button', { name: WALK_LAYER }).first()).toBeVisible();
      await run.measureInterface();
      await run.shot('first-garden');
    },
  },
  hub: {
    async play(run) {
      const { page } = run;
      await expect(page.getByRole('button', { name: WALK_LAYER }).first()).toBeVisible();
      await run.measureInterface();
      await run.shot('garden');
      await run.tap(page.getByRole('button', { name: /^Open the menu\./ }));
      await expect(page.getByRole('heading', { name: 'COMPANION', exact: true })).toBeVisible();
      await run.shot('menu');
    },
  },
  'walk-interrupted': {
    async play(run) {
      const { page } = run;
      const layer = page.getByRole('button', { name: WALK_LAYER }).first();
      await expect(layer).toBeVisible();
      // walk toward the bed (arriving there would offer a nap), then change course after a
      // moment: the first walk's arrival must not fire
      await run.tap(page.getByRole('button', { name: 'nap in your bed', exact: true }), 350);
      await run.shot('walking-to-bed');
      await run.tapWorld(0.7, 0.72, 6000);
      await run.shot('changed-course');
      await expect(page.getByRole('heading', { name: 'TAKE A NAP', exact: true })).toHaveCount(0);
      await expect(page.getByRole('button', { name: 'WAKE UP', exact: true })).toHaveCount(0);
      run.notes.push('After the interruption: no nap sheet, no nap started.');
    },
  },
  nap: {
    async play(run) {
      const { page } = run;
      await run.tap(page.getByRole('button', { name: 'Take a nap', exact: true }));
      await expect(page.getByRole('heading', { name: 'TAKE A NAP', exact: true })).toBeVisible();
      await run.shot('nap-sheet');
      await run.tap(page.getByRole('button', { name: 'START NAP', exact: true }), 3000);
      await expect(page.getByRole('button', { name: 'WAKE UP', exact: true })).toBeVisible();
      await run.shot('napping');
      await run.tap(page.getByRole('button', { name: 'WAKE UP', exact: true }), 2000);
      await run.shot('woken');
    },
  },
  spar: {
    async play(run) {
      const { page } = run;
      await run.tap(page.getByRole('tab', { name: /^ARENA/ }));
      await expect(page.getByRole('button', { name: 'SPAR WITH DAVE', exact: true })).toBeVisible();
      await run.shot('arena');
      await run.tap(page.getByRole('button', { name: 'SPAR WITH DAVE', exact: true }), 1500);
      await expect(
        page.getByRole('switch', { name: 'Auto sparring at double speed', exact: true }),
      ).toBeVisible();
      await run.measureInterface();
      await run.shot('battle');
    },
  },
  night: {
    night: true,
    async play(run) {
      const { page } = run;
      await expect(page.getByRole('button', { name: WALK_LAYER }).first()).toBeVisible();
      await run.shot('garden-at-night');
    },
  },
  'reduced-motion': {
    reduced: true,
    async play(run) {
      const { page } = run;
      const layer = page.getByRole('button', { name: WALK_LAYER }).first();
      await expect(layer).toBeVisible();
      await run.tapWorld(0.3, 0.7, 400);
      await run.shot('walk-reduced');
      run.notes.push('Reduced motion: walking is instant, no bobbing (check the screenshot).');
    },
  },
};

for (const [flow, spec] of Object.entries(flows)) {
  test(flow, async ({ page, browser }, info) => {
    const density = Number(info.project.metadata.density);
    const errors: string[] = [];
    page.on('console', (m) => {
      if (m.type() === 'error') errors.push(`console.error: ${m.text()}`);
    });
    page.on('pageerror', (e) => errors.push(`pageerror: ${e.message}`));
    await page.context().route('**/*', (route) => {
      const url = new URL(route.request().url());
      if (url.origin === ORIGIN) return route.continue();
      errors.push(`external request blocked: ${url.origin}${url.pathname}`);
      return route.abort();
    });
    const now = Date.parse(`2026-10-17T${spec.night ? '22' : '14'}:00:00Z`);
    await page.clock.install({ time: new Date(now - 60_000) });
    await page.clock.pauseAt(new Date(now));
    const seed: { saved: unknown; reduced: boolean; keys: { save: string; motion: string } } = {
      saved: spec.fresh ? null : makeSavedGame(now),
      reduced: !!spec.reduced,
      keys: { save: SAVE_KEY, motion: MOTION_KEY },
    };
    await page.addInitScript(({ saved, reduced, keys }) => {
      if (sessionStorage.getItem('napattack-playtest-seeded')) return;
      sessionStorage.setItem('napattack-playtest-seeded', 'true');
      localStorage.clear();
      if (saved) localStorage.setItem(keys.save, JSON.stringify(saved));
      localStorage.setItem(keys.motion, JSON.stringify(reduced));
      let state = 7351;
      Math.random = () => {
        state = (state * 16807) % 2147483647;
        return (state - 1) / 2147483646;
      };
    }, seed);
    if (spec.reduced) await page.emulateMedia({ reducedMotion: 'reduce' });

    const run = new Run(page, info, flow);
    let failure: string | null = null;
    try {
      await page.goto(`/?density=${density}`, { waitUntil: 'networkidle' });
      await page.evaluate(async (families) => {
        for (const family of families) await document.fonts.load(`14px "${family}"`);
      }, FONTS);
      for (let i = 0; i < 12; i++) {
        await page.clock.runFor(250);
        if ((await page.getByRole('img', { name: SPLASH, exact: true }).count()) === 0) break;
      }
      await spec.play(run);
    } catch (error) {
      failure = error instanceof Error ? error.message.split('\n')[0] : String(error);
      try {
        await run.shot('failure');
      } catch {
        // keep the original failure
      }
    } finally {
      await mkdir(`${OUT}/results`, { recursive: true });
      await writeFile(
        `${OUT}/results/${info.project.name}--${flow}.json`,
        JSON.stringify(
          {
            project: info.project.name,
            device: info.project.metadata.device,
            density,
            flow,
            viewport: page.viewportSize(),
            dpr: info.project.use.deviceScaleFactor,
            reduced: !!spec.reduced,
            night: !!spec.night,
            browser: `Chromium ${browser.version()} (desktop, emulating a phone)`,
            ok: failure === null && errors.length === 0,
            failure,
            errors,
            steps: run.steps,
            measures: run.measures,
            notes: run.notes,
          },
          null,
          2,
        ),
      );
    }
    expect(failure, 'flow failed').toBeNull();
    expect(errors, 'browser errors').toEqual([]);
  });
}
