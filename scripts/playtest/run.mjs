// The play-test harness's runner (docs/playtest.md): builds the web export (skip with
// --no-build), plays every flow at three phone sizes and densities 1 and 2, and writes
// artifacts/playtest/REPORT.md from the per-flow results. Extra arguments go to Playwright
// (for example `-- --project=402x874@3-d2 --grep nap`).
import { spawn } from 'node:child_process';
import { mkdir, readFile, readdir, rm, writeFile } from 'node:fs/promises';

const OUT = 'artifacts/playtest';
const args = process.argv.slice(2);
const build = !args.includes('--no-build');
const passThrough = args.filter((a) => a !== '--no-build');
const env = {
  ...process.env,
  TZ: 'UTC',
  EXPO_OFFLINE: '1',
  EXPO_NO_DOTENV: '1',
  EXPO_PUBLIC_BILT_URL: '',
  EXPO_PUBLIC_BILT_ANON_KEY: '',
};
const run = (cmd) =>
  new Promise((resolve, reject) => {
    const child = spawn(process.execPath, cmd, { env, stdio: 'inherit' });
    child.once('error', reject);
    child.once('exit', (code, signal) => resolve(signal ? 1 : (code ?? 1)));
  });

await rm(OUT, { recursive: true, force: true });
await mkdir(OUT, { recursive: true });
if (build) {
  const code = await run([
    'node_modules/expo/bin/cli',
    'export',
    '-p',
    'web',
    '--clear',
    '--output-dir',
    '.expo/screens-export',
  ]);
  if (code) process.exit(code);
}
const tests = await run([
  'node_modules/@playwright/test/cli.js',
  'test',
  '--config=playwright.playtest.config.ts',
  ...passThrough,
]);

// ---- the report ----------------------------------------------------------------------------
const files = (await readdir(`${OUT}/results`).catch(() => [])).filter((f) => f.endsWith('.json'));
const results = await Promise.all(
  files.map(async (f) => JSON.parse(await readFile(`${OUT}/results/${f}`, 'utf8'))),
);
results.sort((a, b) => a.project.localeCompare(b.project) || a.flow.localeCompare(b.flow));
const projects = [...new Set(results.map((r) => r.project))];
const flows = [...new Set(results.map((r) => r.flow))];
const cell = (r) => (!r ? '–' : r.ok ? 'pass' : `**FAIL**`);
const lines = [
  '# Play-test report',
  '',
  `Run ${new Date().toISOString()} on ${results[0]?.browser ?? 'Chromium'}.`,
  '',
  "> **A desktop browser, not a phone.** Chromium emulates each phone's viewport, pixel ratio and",
  "> touch. Nothing here measures a phone's GPU, memory, frame rate, audio, safe areas, the",
  '> keyboard or native behaviour. Clocks are faked (14:00 UTC by day, 22:00 at night).',
  '',
  `**${results.filter((r) => r.ok).length} of ${results.length} flows passed.**`,
  '',
  `| Flow | ${projects.join(' | ')} |`,
  `| --- | ${projects.map(() => '---').join(' | ')} |`,
  ...flows.map(
    (flow) =>
      `| ${flow} | ${projects.map((p) => cell(results.find((r) => r.project === p && r.flow === flow))).join(' | ')} |`,
  ),
  '',
  '## The interface on each screen (the garden, after onboarding or with the saved garden)',
  '',
  'Sizes in CSS px. The HUD and hotbar must be the same size at density 1 and 2, and no',
  'control a player taps may be under 44 px.',
  '',
  '| Screen | Hotbar tab (min width x height) | Nap button | Menu button | Controls under 44 px | Icons 2x / 1x | Overflow |',
  '| --- | --- | --- | --- | --- | --- | --- |',
];
const sizeIssues = [];
for (const p of projects) {
  const r = results.find((x) => x.project === p && x.flow === 'hub' && x.measures.tabHeight);
  if (!r) continue;
  const m = r.measures;
  lines.push(
    `| ${p} (${r.device}) | ${m.tabWidth} x ${m.tabHeight} | ${m.napButton} | ${m.menuButton} | ${m.controlsUnder44} of ${m.controls} | ${m.icons2x} / ${m.icons1x} | ${m.horizontalOverflow ? '**yes**' : 'no'} |`,
  );
  if (m.controlsUnder44)
    sizeIssues.push(`${p}: ${m.controlsUnder44} controls under 44 px: ${m.smallControls}`);
  if (m.horizontalOverflow) sizeIssues.push(`${p}: horizontal overflow`);
}
// the same interface at both densities
for (const p of projects.filter((x) => x.endsWith('-d2'))) {
  const d1 = results.find((x) => x.project === p.replace(/-d2$/, '-d1') && x.flow === 'hub');
  const d2 = results.find((x) => x.project === p && x.flow === 'hub');
  if (!d1?.measures.tabHeight || !d2?.measures.tabHeight) continue;
  for (const k of ['tabHeight', 'tabWidth', 'napButton', 'menuButton', 'hudBottom', 'hotbarTop'])
    if (d1.measures[k] !== d2.measures[k])
      sizeIssues.push(`${p}: ${k} ${d1.measures[k]} at density 1 but ${d2.measures[k]} at 2`);
}
lines.push('', '## Findings', '');
const failures = results.filter((r) => !r.ok);
if (!failures.length && !sizeIssues.length)
  lines.push('- None: every flow passed and the interface held its size.');
for (const r of failures)
  lines.push(
    `- **${r.flow}** on ${r.project}: ${r.failure ?? ''}${r.errors.length ? ` (${r.errors.length} browser errors: ${r.errors.slice(0, 2).join('; ')})` : ''}`,
  );
for (const issue of sizeIssues) lines.push(`- ${issue}`);
const notes = [...new Set(results.flatMap((r) => r.notes))];
if (notes.length) lines.push('', '## Notes', '', ...notes.map((n) => `- ${n}`));
lines.push('', '## Screenshots', '');
for (const r of results) {
  lines.push(
    `- **${r.flow}**, ${r.project}: ${r.steps.map((s) => `[${s.name}](images/${s.image})`).join(', ')}`,
  );
}
lines.push(
  '',
  '## Not covered',
  '',
  '- Real phones, the iOS and Android builds, and the simulator: none of this ran on them.',
  '- Sound (muted in headless Chromium), haptics, the software keyboard, notches and home indicators.',
  '- Saved progress across real sessions and app restarts beyond one page load.',
  '- Frame rate and memory: see `npm run check:budgets` for the source-level budgets.',
  '',
);
await writeFile(`${OUT}/REPORT.md`, lines.join('\n'));
console.log(
  `\nPlay-test report: ${OUT}/REPORT.md (${results.filter((r) => r.ok).length}/${results.length} flows passed)`,
);
process.exitCode = tests || (failures.length ? 1 : 0);
