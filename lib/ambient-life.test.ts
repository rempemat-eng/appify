import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { runInNewContext } from 'node:vm';
import ts from 'typescript';
import {
  ambientLife,
  lifeTime,
  type LifeContext,
  type LifeEmitter,
  type LifeSeason,
  type LifeWeather,
} from './ambient-life';
import { residentRoutes } from './resident-routes';
import { zoneIds, zoneMaps } from './zone-maps';
import type { TileId } from './region-walk';

let checks = 0;
function equal(actual: unknown, expected: unknown, message: string) {
  assert.deepEqual(actual, expected, message);
  checks++;
}
function ok(value: unknown, message: string) {
  assert.ok(value, message);
  checks++;
}
const base: LifeContext = {
  zone: 'town',
  minuteOfDay: 720,
  season: 'original',
  weather: 'original',
  active: true,
  quiet: false,
  reducedMotion: false,
  elapsedMs: 0,
};

// Execute only the actual renderer's pure catalogue at a VM boundary. Never mock
// coordinates into the production module, import React or run native animations.
const visual = readFileSync(new URL('../components/atlas-life.tsx', import.meta.url), 'utf8');
const start = visual.indexOf('const PERIOD =');
const end = visual.indexOf('\nfunction Particle(', start);
ok(start >= 0 && end > start, 'actual pure emitter catalogue is found');
const catalogText = visual
  .slice(start, end)
  .replace('export function zoneEmitters', 'function zoneEmitters');
const compiled = ts.transpileModule(`${catalogText}\nzoneEmitters;`, {
  compilerOptions: { target: ts.ScriptTarget.ES2022, module: ts.ModuleKind.None },
}).outputText;
const catalogue: (zone: (typeof zoneIds)[number], night?: boolean) => LifeEmitter[] =
  runInNewContext(compiled, { zoneMaps });
const inputs = new Map<TileId, readonly LifeEmitter[]>();
inputs.set('garden', Object.freeze([]));
for (const zone of zoneIds) {
  const candidates: LifeEmitter[] = structuredClone(catalogue(zone, false));
  for (const candidate of candidates) Object.freeze(candidate);
  inputs.set(zone, Object.freeze(candidates));
}
const zones: TileId[] = ['garden', ...zoneIds];
const seasons: LifeSeason[] = ['original', 'spring', 'summer', 'autumn', 'winter'];
const weather: LifeWeather[] = ['original', 'clear', 'rain'];
const times = [360, 720, 1080, 1260];
const routesBefore = structuredClone(residentRoutes);

for (const [minute, time] of [
  [0, 'night'],
  [359.99, 'night'],
  [360, 'dawn'],
  [539.99, 'dawn'],
  [540, 'day'],
  [1079.99, 'day'],
  [1080, 'dusk'],
  [1259.99, 'dusk'],
  [1260, 'night'],
  [1439.99, 'night'],
] as const)
  equal(lifeTime(minute), time, `clock boundary ${minute}`);
for (const minute of [-1, 1440, NaN, Infinity, -Infinity])
  equal(lifeTime(minute), null, 'invalid time fails closed');

for (const zone of zones) {
  const candidates = inputs.get(zone)!;
  const before = structuredClone(candidates);
  for (const minuteOfDay of times)
    for (const season of seasons)
      for (const w of weather) {
        const context = Object.freeze({ ...base, zone, minuteOfDay, season, weather: w });
        const result = ambientLife(context, candidates);
        equal(
          ambientLife(context, candidates),
          result,
          'same explicit inputs give identical plans',
        );
        equal(result.mode, 'animated', 'active original batch animates');
        ok(result.emitters.length <= result.budget.emitters, 'per-zone emitter count bounded');
        ok(result.residents.length <= result.budget.residents, 'per-zone resident count bounded');
        ok(
          result.framesPerSecond <= 12 && result.remainingMs <= 18000,
          'finite frame/batch budgets',
        );
        equal(
          new Set(result.emitters.map((e) => `${e.kind}:${e.x}:${e.y}:${e.seed}`)).size,
          result.emitters.length,
          'stable emitters unique',
        );
        for (const e of result.emitters) {
          ok(
            candidates.some(
              (c) =>
                c.x === e.x &&
                c.y === e.y &&
                c.seed === e.seed &&
                (c.kind === e.kind ||
                  (['butterfly', 'firefly'].includes(c.kind) &&
                    ['butterfly', 'firefly'].includes(e.kind))),
            ),
            'no invented spawn or seed',
          );
          if (w === 'clear') ok(e.kind !== 'rain', 'clear suppresses existing rain');
          if (w === 'rain')
            ok(
              !['butterfly', 'firefly', 'lizard'].includes(e.kind),
              'rain shelters small animals without new coordinates',
            );
          if (season === 'winter')
            ok(
              !['butterfly', 'firefly', 'lizard', 'leaf'].includes(e.kind),
              'winter seasonal selection',
            );
        }
        for (const r of result.residents) {
          const route = residentRoutes[r.id];
          equal(route.zone, zone, 'resident remains in authored zone');
          equal(
            r.from,
            { x: route.from[0], y: route.from[1] },
            'resident starts at authored safe point',
          );
          equal(r.to, { x: route.to[0], y: route.to[1] }, 'resident route is unchanged');
        }
        for (const inactive of [{ active: false }, { quiet: true }]) {
          const off = ambientLife({ ...context, ...inactive }, candidates);
          equal(
            [off.mode, off.framesPerSecond, off.remainingMs, off.emitters, off.residents],
            ['off', 0, 0, [], []],
            'inactive or Quiet produces no work',
          );
        }
        const reduced = ambientLife({ ...context, reducedMotion: true }, candidates);
        equal(
          [reduced.mode, reduced.framesPerSecond, reduced.remainingMs],
          ['still', 0, 0],
          'reduced motion has no clock',
        );
        equal(
          [reduced.emitters, reduced.residents],
          [result.emitters, result.residents],
          'reduced motion keeps still scene, not disappearance',
        );
        const endPlan = ambientLife({ ...context, elapsedMs: 18000 }, candidates);
        equal(
          [endPlan.mode, endPlan.framesPerSecond, endPlan.remainingMs],
          ['still', 0, 0],
          'batch settles once, never an infinite repeat',
        );
        equal(
          ambientLife({ ...context, elapsedMs: 10 ** 9 }, candidates),
          endPlan,
          'long absence creates no catch-up or backlog',
        );
      }
  equal(candidates, before, 'frozen caller catalogue unchanged after matrix');
}
equal(residentRoutes, routesBefore, 'source routes unchanged');

const town = inputs.get('town')!;
equal(
  ambientLife({ ...base, minuteOfDay: 360 }, town).emitters.filter((e) => e.kind === 'butterfly')
    .length,
  2,
  'town butterflies at dawn',
);
equal(
  ambientLife({ ...base, minuteOfDay: 1260 }, town).emitters.filter((e) => e.kind === 'firefly')
    .length,
  2,
  'same positions become fireflies at night',
);
equal(
  ambientLife({ ...base, minuteOfDay: 1260 }, town).residents,
  [],
  'town workers rest at night',
);
equal(
  ambientLife(
    { ...base, zone: 'harbour', minuteOfDay: 1260 },
    inputs.get('harbour')!,
  ).residents.map((r) => r.id),
  ['keeper'],
  'lighthouse keeper on night route',
);
equal(
  ambientLife({ ...base, zone: 'neon', minuteOfDay: 1260 }, inputs.get('neon')!).residents.map(
    (r) => r.id,
  ),
  ['vendor'],
  'city vendor has evening routine',
);
const leaves = inputs.get('woodland')!;
ok(
  ambientLife({ ...base, zone: 'woodland', season: 'autumn' }, leaves).emitters.some(
    (e) => e.kind === 'leaf',
  ),
  'autumn keeps existing leaves',
);
ok(
  !ambientLife({ ...base, zone: 'woodland', season: 'spring' }, leaves).emitters.some(
    (e) => e.kind === 'leaf',
  ),
  'spring does not invent autumn fall',
);
equal(
  ambientLife({ ...base, weather: 'rain' }, []).emitters,
  [],
  'weather never invents a rain position',
);
for (const elapsedMs of [-1, NaN, Infinity])
  equal(
    ambientLife({ ...base, elapsedMs }, town).mode,
    'off',
    'invalid elapsed cannot animate forever',
  );
equal(
  ambientLife({ ...base, elapsedMs: 17999 }, town).remainingMs,
  1,
  'last millisecond remains finite',
);
for (const minuteOfDay of [-1, NaN, 1440])
  equal(ambientLife({ ...base, minuteOfDay }, town).mode, 'off', 'invalid clock cancels scene');
const crowded: LifeEmitter[] = Array.from({ length: 200 }, (_, seed) => ({
  kind: 'rain',
  x: seed % 320,
  y: seed,
  seed,
}));
crowded.push(
  ...town,
  ...town,
  { kind: 'puff', x: NaN, y: 0, seed: 0 },
  { kind: 'fish', x: 320, y: 0, seed: 0 },
  { kind: 'spore', x: 1, y: -1, seed: 0 },
);
const bounded = ambientLife(base, crowded);
equal(bounded.emitters.filter((e) => e.kind === 'rain').length, 12, 'rain has its own cap');
ok(
  bounded.emitters.some((e) => e.kind === 'butterfly'),
  'many rain candidates do not crowd out animals',
);
ok(
  bounded.emitters.every((e) => Number.isFinite(e.x) && e.x < 320 && e.y >= 0),
  'malformed/off-map candidates dropped',
);
const manyKinds: LifeEmitter[] = [];
for (const kind of [
  'puff',
  'ember',
  'spore',
  'gull',
  'butterfly',
  'rain',
  'lizard',
  'fish',
  'leaf',
] as const) {
  for (let seed = 0; seed < 20; seed++) manyKinds.push({ kind, x: seed, y: seed, seed });
}
equal(
  ambientLife(base, manyKinds).emitters.length,
  24,
  'total normal-zone cap reached, not exceeded',
);
equal(
  ambientLife({ ...base, zone: 'neon' }, manyKinds).emitters.length,
  32,
  'total rain-city cap reached, not exceeded',
);
equal(ambientLife({ ...base, zone: 'home' }, []).residents, [], 'interior invents no residents');
const copy = ambientLife(base, town);
if (copy.residents[0]) {
  Object.assign(copy.residents[0].from, { x: -999 });
  equal(residentRoutes, routesBefore, 'consumer cannot mutate shared route through returned point');
}
const source = readFileSync(new URL('./ambient-life.ts', import.meta.url), 'utf8');
ok(
  !/Date\.|new Date|Math\.random|setTimeout|setInterval|AsyncStorage|useGame|router\./.test(source),
  'pure module has no autonomous clock, storage, rewards or navigation',
);
console.log(
  `Ambient life: ${checks} assertions across ${zones.length} zones, all time/season/weather choices; source catalogue only, not renderer or device performance.`,
);
