#!/usr/bin/env node
/**
 * Header-only moving-water/lava audit. The repository CLI is intentionally not wired into
 * package.json until check-art-density exposes its retirement predicate without running its
 * full image scan. Tests inject that predicate through auditFx's options.
 */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const ts = require('typescript');

const LOOP_MS = 36_000;
const MAX_FRAMES = 8;
const MAX_SIDE = 4096;
const TILE = 256;
const REPORT_BUDGET = 1024 * 1024;

function pngSize(file) {
  const fd = fs.openSync(file, 'r');
  const header = Buffer.alloc(24);
  let count;
  try {
    count = fs.readSync(fd, header, 0, header.length, 0);
  } finally {
    fs.closeSync(fd);
  }
  if (
    count !== header.length ||
    !header.subarray(0, 8).equals(Buffer.from('89504e470d0a1a0a', 'hex')) ||
    header.readUInt32BE(8) !== 13 ||
    header.toString('ascii', 12, 16) !== 'IHDR'
  ) {
    throw new Error(`Invalid PNG header: ${file}`);
  }
  const width = header.readUInt32BE(16);
  const height = header.readUInt32BE(20);
  if (!width || !height) throw new Error(`Invalid PNG dimensions: ${file}`);
  return { width, height };
}

function loadGenerated(root, file) {
  const module = { exports: {} };
  const source = ts.transpileModule(fs.readFileSync(path.join(root, file), 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
  }).outputText;
  vm.runInNewContext(source, {
    module,
    exports: module.exports,
    require(specifier) {
      throw new Error(`${file} unexpectedly imports ${specifier}`);
    },
  });
  return module.exports;
}

function repositoryDefinitions(root) {
  const zones = loadGenerated(root, 'lib/zone-maps.ts');
  const world = loadGenerated(root, 'lib/world-canvas.ts');
  return {
    zoneFlow: zones.zoneFlow,
    zoneFrames: zones.FLOW_FRAMES,
    zoneFrameMs: zones.FLOW_FRAME_MS,
    worldTiles: world.worldTiles,
    worldFrames: world.WORLD_FLOW.frames,
    worldFrameMs: world.WORLD_FLOW.frameMs,
  };
}

function worstZoneTileBytes(rect, frames, scale) {
  const [, , width, height] = rect;
  return Math.min(width, TILE) * Math.min(height, TILE) * scale * scale * frames * 4;
}

function inspectStrip(strip, isRetiring) {
  const { width, height } = pngSize(strip.full);
  const [x, y, worldWidth, worldHeight] = strip.rect;
  const scale = width / worldWidth;
  const frames = height / (worldHeight * scale);
  const decodedBytes = width * height * 4;
  const perTileBytes =
    strip.kind === 'world'
      ? decodedBytes
      : worstZoneTileBytes([x, y, worldWidth, worldHeight], frames, scale);
  const failures = [];
  if (!Number.isInteger(scale) || scale <= 0 || !Number.isInteger(frames) || frames <= 0) {
    failures.push(
      `${strip.file}: ${width} x ${height} does not contain whole ${worldWidth} x ${worldHeight} frames`,
    );
  } else {
    if (frames > MAX_FRAMES)
      failures.push(`${strip.file}: ${frames} frames passes the ${MAX_FRAMES}-frame limit`);
    if (frames * strip.frameMs <= 0 || LOOP_MS % (frames * strip.frameMs) !== 0)
      failures.push(`${strip.file}: ${frames} x ${strip.frameMs} ms does not divide ${LOOP_MS} ms`);
    if (scale !== 1)
      failures.push(`${strip.file}: stored at ${scale} image px per world px; expected 1`);
  }
  if (Math.max(width, height) > MAX_SIDE && !isRetiring(strip.file))
    failures.push(`${strip.file}: ${width} x ${height} passes ${MAX_SIDE} px and is not retiring`);
  return { ...strip, width, height, scale, frames, decodedBytes, perTileBytes, failures };
}

function inventory(root, definitions) {
  const strips = [];
  for (const [zone, rect] of Object.entries(definitions.zoneFlow)) {
    const file = `assets/zones/${zone}/flow.png`;
    strips.push({
      kind: 'zone',
      file,
      full: path.join(root, file),
      rect,
      frameMs: definitions.zoneFrameMs,
      declaredFrames: definitions.zoneFrames,
    });
  }
  for (const [plane, tiles] of Object.entries(definitions.worldTiles)) {
    for (const [key, tile] of Object.entries(tiles)) {
      if (!tile.flow) continue;
      const [column, row] = key.split(',');
      const file = `assets/world/${plane}/f_${column.replace('-', 'm')}_${row.replace('-', 'm')}.png`;
      strips.push({
        kind: 'world',
        file,
        full: path.join(root, file),
        rect: tile.flow,
        frameMs: definitions.worldFrameMs,
        declaredFrames: definitions.worldFrames,
      });
    }
  }
  return strips.sort((a, b) => a.file.localeCompare(b.file));
}

function auditFx(root, options = {}) {
  assert.equal(typeof options.isRetiring, 'function', 'isRetiring predicate is required');
  const definitions = options.definitions ?? repositoryDefinitions(root);
  const rows = inventory(root, definitions).map((strip) => inspectStrip(strip, options.isRetiring));
  return {
    rows,
    failures: rows.flatMap((row) =>
      row.kind === 'world'
        ? row.failures
        : row.failures.map((failure) => `REPORT ONLY: ${failure}`),
    ),
    gatingFailures: rows.flatMap((row) => (row.kind === 'world' ? row.failures : [])),
  };
}

function report(result) {
  const lines = [
    'Moving water and lava (PNG headers only):',
    '  strip                                      frames  loop ms  decoded/tile  gate',
  ];
  for (const row of result.rows) {
    const gate = row.kind === 'world' ? 'world' : 'old zone: report';
    const budget = row.perTileBytes > REPORT_BUDGET ? ' > 1 MiB' : '';
    lines.push(
      `  ${row.file.padEnd(42)} ${String(row.frames).padStart(6)} ${String(row.frames * row.frameMs).padStart(8)} ${String(row.perTileBytes).padStart(13)}${budget}  ${gate}`,
    );
  }
  if (result.failures.length) lines.push('', ...result.failures);
  return lines.join('\n');
}

module.exports = {
  LOOP_MS,
  MAX_FRAMES,
  MAX_SIDE,
  REPORT_BUDGET,
  auditFx,
  inventory,
  inspectStrip,
  pngSize,
  report,
  repositoryDefinitions,
};

if (require.main === module) {
  console.error(
    'check:fx is not wired yet: check-art-density.cjs must export its retirement predicate without running its image scan.',
  );
  process.exitCode = 2;
}
