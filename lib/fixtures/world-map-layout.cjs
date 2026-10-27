// Configured before the layout-boundary harness imports the production map.
// Explicit exports also expose the fixture through Node's native ESM import.
const fixture = globalThis[Symbol.for('napattack.map-layout-fixture')];
if (!fixture) throw new Error('The world map layout fixture requires its test harness.');

exports.LAYOUT_VERSION = fixture.currentLayoutVersion + 1;
exports.carryForward = (version) => {
  globalThis[Symbol.for('napattack.map-layout-migrations')]++;
  return version === fixture.currentLayoutVersion ? { ...fixture.moved } : null;
};
