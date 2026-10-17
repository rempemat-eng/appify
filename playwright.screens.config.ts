import { defineConfig } from '@playwright/test';

const viewports = [
  { width: 320, height: 640 },
  { width: 402, height: 874 },
  { width: 768, height: 1024 },
];

export default defineConfig({
  testDir: './scripts/screens',
  testMatch: 'screens.spec.ts',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: 0,
  workers: 2,
  timeout: 45_000,
  expect: { timeout: 10_000 },
  outputDir: 'artifacts/screens/test-results',
  reporter: [
    ['line'],
    ['./scripts/screens/reporter.ts'],
    ['html', { outputFolder: 'artifacts/screens/report', open: 'never' }],
  ],
  use: {
    browserName: 'chromium',
    baseURL: 'http://127.0.0.1:4178',
    locale: 'en-GB',
    timezoneId: 'UTC',
    deviceScaleFactor: 1,
    colorScheme: 'light',
    // export:web deliberately has no generated sw.js. Test the uncached export.
    serviceWorkers: 'block',
    screenshot: 'only-on-failure',
    trace: 'retain-on-failure',
  },
  projects: viewports.flatMap((viewport) =>
    (['day', 'night'] as const).flatMap((timeOfDay) =>
      (['normal', 'reduced'] as const).map((motion) => ({
        name: `${viewport.width}-${timeOfDay}-${motion}`,
        metadata: { timeOfDay, motion },
        use: {
          viewport,
          reducedMotion: motion === 'reduced' ? ('reduce' as const) : ('no-preference' as const),
        },
      })),
    ),
  ),
  webServer: {
    command: 'node scripts/screens/serve.mjs',
    url: 'http://127.0.0.1:4178',
    reuseExistingServer: false,
    timeout: 15_000,
  },
});
