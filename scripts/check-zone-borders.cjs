#!/usr/bin/env node
/** C20: walk-seam checks now; semantic terrain checks only where generators export it.
 * No PNG colour guessing and no claim that a walk mask proves visual continuity.
 * Run with node --import tsx; --require-terrain fails on missing coverage.
 */
const path = require('node:path');

const shape = (rows, alphabet) =>
  Array.isArray(rows) &&
  rows.length > 0 &&
  typeof rows[0] === 'string' &&
  rows[0].length > 0 &&
  rows.every(
    (row) =>
      typeof row === 'string' && row.length === rows[0].length && (!alphabet || alphabet.test(row)),
  );

function inspectSeam({ walkA, walkB, terrainA, terrainB, direction, blends = [] }) {
  const errors = [];
  const result = { crossings: 0, walkMismatch: 0, terrain: 'unavailable', errors };
  if (!['east', 'south'].includes(direction)) {
    errors.push('invalid edge direction');
    return result;
  }
  if (
    !shape(walkA, /^[.#]+$/) ||
    !shape(walkB, /^[.#]+$/) ||
    walkA.length !== walkB.length ||
    walkA[0].length !== walkB[0].length
  ) {
    errors.push('invalid or inconsistent walk grid');
    return result;
  }
  const height = walkA.length,
    width = walkA[0].length;
  const pairs =
    direction === 'east'
      ? walkA.map((row, y) => [row[width - 1], walkB[y][0]])
      : Array.from({ length: width }, (_, x) => [walkA[height - 1][x], walkB[0][x]]);
  result.crossings = pairs.filter(([a, b]) => a === '.' && b === '.').length;
  result.walkMismatch = pairs.filter(([a, b]) => a !== b).length;
  if (!result.crossings) errors.push('no shared open crossing');
  // Fence sides/props intentionally differ (especially the garden). A walk mask
  // only establishes a shared crossing, not a road/water/material classification.
  if (
    [terrainA, terrainB].some(
      (rows) =>
        rows !== undefined && (!shape(rows) || rows.length !== height || rows[0].length !== width),
    )
  ) {
    result.terrain = 'invalid';
    errors.push('terrain grid must match the walk grid dimensions');
    return result;
  }
  if (
    !Array.isArray(blends) ||
    blends.some(
      (pair) =>
        !Array.isArray(pair) ||
        pair.length !== 2 ||
        pair.some((code) => typeof code !== 'string' || code.length !== 1),
    )
  ) {
    result.terrain = 'invalid';
    errors.push('invalid explicit terrain blend pairs');
    return result;
  }
  if (terrainA === undefined || terrainB === undefined) return result;
  const terrainPairs =
    direction === 'east'
      ? terrainA.map((row, y) => [row[width - 1], terrainB[y][0]])
      : Array.from({ length: width }, (_, x) => [terrainA[height - 1][x], terrainB[0][x]]);
  terrainPairs.forEach(([a, b], i) => {
    if (a !== b && !blends.some(([x, y]) => (a === x && b === y) || (a === y && b === x)))
      errors.push(`terrain mismatch at edge cell ${i}: ${a}/${b}`);
  });
  result.terrain = errors.some((e) => e.startsWith('terrain mismatch')) ? 'mismatched' : 'verified';
  return result;
}

function checkZoneBorders(root, { requireTerrain = false } = {}) {
  const regions = require(path.join(root, 'lib/region-walk.ts'));
  const zones = require(path.join(root, 'lib/zone-maps.ts'));
  const garden = require(path.join(root, 'lib/garden-map.ts'));
  const { regionEdges } = require(path.join(root, 'lib/world-travel.ts'));
  const seams = [],
    errors = [];
  for (const region of Object.keys(zones.regionLayout)) {
    const rows = regions.regionWalk(region);
    for (const { a, b, direction } of regionEdges(region)) {
      const id = `${region}:${a.id}/${b.id}`;
      const localRows = (tile) => {
        const o = regions.tileOrigin(region, tile);
        const x = o.x / regions.TILE.cell,
          y = o.y / regions.TILE.cell;
        return rows
          .slice(y, y + regions.TILE.height / regions.TILE.cell)
          .map((row) => row.slice(x, x + regions.TILE.width / regions.TILE.cell));
      };
      const terrain = (tile) =>
        tile.id === 'garden' ? garden.gardenTerrain : zones.zoneTerrain?.[tile.id];
      const seam = inspectSeam({
        walkA: localRows(a),
        walkB: localRows(b),
        terrainA: terrain(a),
        terrainB: terrain(b),
        direction,
        blends: zones.zoneBorderBlends?.[id] ?? [],
      });
      seams.push({ id, direction, ...seam });
      errors.push(...seam.errors.map((e) => `${id}: ${e}`));
      if (requireTerrain && seam.terrain === 'unavailable')
        errors.push(`${id}: semantic terrain export missing`);
    }
  }
  return { seams, errors, terrainVerified: seams.filter((s) => s.terrain === 'verified').length };
}

if (require.main === module) {
  const report = checkZoneBorders(path.join(__dirname, '..'), {
    requireTerrain: process.argv.includes('--require-terrain'),
  });
  for (const error of report.errors) console.error(error);
  console.log(
    `Zone borders: ${report.seams.length} walk seams; ${report.terrainVerified}/${report.seams.length} semantic terrain borders verified.`,
  );
  if (report.terrainVerified < report.seams.length)
    console.log(
      'INCOMPLETE TERRAIN COVERAGE: generator exports required; no pixel or road/water continuity approval. Use --require-terrain to enforce full coverage.',
    );
  process.exitCode = report.errors.length ? 1 : 0;
}
module.exports = { inspectSeam, checkZoneBorders };
