import assert from 'node:assert/strict';
import { registerHooks } from 'node:module';
import { regionPoint, travelPoints } from './world-places';

// Simulate the next layout at the version/migration boundary only. The actual
// map builder and world restorer below must distinguish saved and live positions.
// This is not a test of authored layout history (world-save.test.ts owns that).
const moved = { region: 'west', ...regionPoint(travelPoints.west) };
const source = `
  export const LAYOUT_VERSION = 2;
  export const carryForward = (version) =>
    version === 1 ? ${JSON.stringify(moved)} : null;
`;
const url = `data:text/javascript,${encodeURIComponent(source)}`;
const hooks = registerHooks({
  resolve(specifier, context, nextResolve) {
    if (specifier === './world-layouts' || specifier === '@/lib/world-layouts')
      return { url, shortCircuit: true };
    return nextResolve(specifier, context);
  },
  load(target, context, nextLoad) {
    if (target === url)
      return {
        format: 'module',
        source: source.replace(
          'version === 1 ?',
          '(globalThis[Symbol.for("napattack.map-layout-migrations")]++, version === 1) ?',
        ),
        shortCircuit: true,
      };
    return nextLoad(target, context);
  },
});

async function main() {
  try {
    const { buildWorldMap } = await import('./world-map');
    const live = {
      region: 'valley' as const,
      ...regionPoint({ region: 'valley', zone: 'park', at: [160, 200] }),
    };
    const oldSave = { ...live, visited: ['garden'], layout: 1 };
    const key = Symbol.for('napattack.map-layout-migrations');
    const counters = globalThis as typeof globalThis & { [key: symbol]: number };
    counters[key] = 0;
    const saved = buildWorldMap({ world: oldSave, mapSeen: [] });
    assert.equal(saved.nodes.find((n) => n.id === 'zone:gulch')?.state, 'here');
    assert.equal(counters[key], 1, 'legacy saved position migrates once, not again as current');

    counters[key] = 0;
    const current = buildWorldMap({ world: oldSave, mapSeen: [], current: live });
    assert.equal(current.nodes.find((n) => n.id === 'zone:park')?.state, 'here');
    assert.equal(counters[key], 1, 'only saved coordinates migrate; live point is current layout');
    assert.ok(!current.visitedSnapshot.includes('park'), 'live position is not saved discovery');
    const home = buildWorldMap({ world: oldSave, mapSeen: [], current: 'garden' });
    assert.equal(home.nodes.find((n) => n.id === 'zone:garden')?.state, 'here');
    const future = buildWorldMap({
      world: { ...oldSave, layout: 999 },
      mapSeen: [],
      current: live,
    });
    assert.equal(future.nodes.find((n) => n.id === 'zone:park')?.state, 'here');
    assert.deepEqual(future.visitedSnapshot, ['garden']);
    assert.deepEqual(oldSave, { ...live, visited: ['garden'], layout: 1 });
    console.log('World map layout boundary: 9 checks passed (simulated next version).');
  } finally {
    hooks.deregister();
    delete (globalThis as typeof globalThis & { [key: symbol]: number })[
      Symbol.for('napattack.map-layout-migrations')
    ];
  }
}
void main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
