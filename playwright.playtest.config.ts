import { existsSync, readdirSync } from 'node:fs';
import { join } from 'node:path';
import { chromium, defineConfig } from '@playwright/test';

/** The browser to play in: PLAYTEST_BROWSER_PATH, else Playwright's own if it is installed,
 *  else any Chromium under PLAYWRIGHT_BROWSERS_PATH (a container may carry an older build
 *  than this Playwright expects). Undefined lets Playwright report what is missing. */
function browserPath(): string | undefined {
  if (process.env.PLAYTEST_BROWSER_PATH) return process.env.PLAYTEST_BROWSER_PATH;
  if (existsSync(chromium.executablePath())) return undefined;
  const root = process.env.PLAYWRIGHT_BROWSERS_PATH ?? '/opt/pw-browsers';
  if (!existsSync(root)) return undefined;
  for (const dir of readdirSync(root)
    .filter((d) => d.startsWith('chromium'))
    .sort()
    .toReversed())
    for (const sub of ['chrome-linux64/chrome', 'chrome-linux/chrome', ''])
      if (existsSync(join(root, dir, sub)) && (sub || dir === 'chromium'))
        return join(root, dir, sub);
  return undefined;
}
const executablePath = browserPath();

/**
 * The play-test harness (docs/playtest.md): three phone sizes at art densities 1 and 2.
 * Run it with `npm run playtest` (builds the web export, plays every flow, writes
 * artifacts/playtest/REPORT.md). A desktop Chromium emulating phones, not a phone.
 */
const devices = [
  { device: 'iPhone 17 Pro', width: 402, height: 874, dpr: 3 },
  { device: 'Pixel 9', width: 412, height: 915, dpr: 2.625 },
  { device: 'iPhone SE (3rd)', width: 375, height: 667, dpr: 2 },
];

export default defineConfig({
  testDir: './scripts/playtest',
  testMatch: 'playtest.spec.ts',
  fullyParallel: true,
  retries: 0,
  workers: process.env.CI ? 2 : 3,
  timeout: 90_000,
  expect: { timeout: 10_000 },
  outputDir: 'artifacts/playtest/test-results',
  reporter: [['line']],
  use: {
    browserName: 'chromium',
    launchOptions: executablePath ? { executablePath } : undefined,
    baseURL: 'http://127.0.0.1:4178',
    locale: 'en-GB',
    timezoneId: 'UTC',
    colorScheme: 'light',
    isMobile: true,
    hasTouch: true,
    serviceWorkers: 'block',
  },
  projects: devices.flatMap(({ device, width, height, dpr }) =>
    [1, 2].map((density) => ({
      name: `${width}x${height}@${dpr}-d${density}`,
      metadata: { device, density },
      use: { viewport: { width, height }, deviceScaleFactor: dpr },
    })),
  ),
  webServer: {
    command: 'node scripts/screens/serve.mjs',
    url: 'http://127.0.0.1:4178',
    reuseExistingServer: !process.env.CI,
    timeout: 15_000,
  },
});
