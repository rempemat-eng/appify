const assert = require('node:assert/strict');
const path = require('node:path');
const { inspectSeam, checkZoneBorders } = require('./check-zone-borders.cjs');
let checks = 0;
const ok = (v, label) => {
  assert.ok(v, label);
  checks++;
};
const open = ['....', '....', '....'];
for (const direction of ['east', 'south']) {
  const inputs = { walkA: open, walkB: open, direction };
  const missing = inspectSeam(inputs);
  ok(
    missing.crossings > 0 && !missing.errors.length && missing.terrain === 'unavailable',
    'walk masks never impersonate terrain verification',
  );
  const matching = inspectSeam({
    ...inputs,
    terrainA: ['GGGG', 'PPPP', 'WWWW'],
    terrainB: direction === 'east' ? ['GGGG', 'PPPP', 'WWWW'] : ['WWWW', 'GGGG', 'PPPP'],
  });
  ok(
    matching.terrain === 'verified' && !matching.errors.length,
    'matching semantic strips pass on both axes',
  );
  const bad = inspectSeam({
    ...inputs,
    terrainA: ['PPPP', 'PPPP', 'PPPP'],
    terrainB: ['WWWW', 'WWWW', 'WWWW'],
  });
  ok(
    bad.terrain === 'mismatched' && bad.errors.some((e) => e.includes('P/W')),
    'a road entering water fails instead of being waived by a global tolerance',
  );
  const blend = inspectSeam({
    ...inputs,
    terrainA: ['GGGG', 'GGGG', 'GGGG'],
    terrainB: ['FFFF', 'FFFF', 'FFFF'],
    blends: [['G', 'F']],
  });
  ok(
    blend.terrain === 'verified' && !blend.errors.length,
    'an explicitly declared ground blend passes',
  );
  ok(
    inspectSeam({ ...inputs, walkB: ['####', '####', '####'] }).errors.includes(
      'no shared open crossing',
    ),
    'closing the counterpart border fails',
  );
  ok(
    inspectSeam({ ...inputs, terrainA: ['G'], terrainB: open }).errors.length > 0,
    'bad terrain dimensions fail',
  );
  ok(
    inspectSeam({ ...inputs, terrainA: ['G'] }).errors.length > 0,
    'a malformed single export cannot hide behind a missing counterpart',
  );
  for (const blends of [null, [['G']], [['G', 7]], [['GG', 'F']]])
    ok(
      inspectSeam({ ...inputs, blends }).errors.length > 0,
      'malformed blend metadata fails even before full terrain coverage',
    );
  for (const walkB of [[], ['...', '..'], ['xxxx', '....', '....'], ['....']])
    ok(inspectSeam({ ...inputs, walkB }).errors.length > 0, 'malformed walk fixtures fail closed');
}
ok(
  inspectSeam({ walkA: open, walkB: open, direction: 'north' }).errors.length > 0,
  'unsupported directions are rejected, not silently treated as south',
);
const partial = inspectSeam({ walkA: open, walkB: ['.###', '.###', '.###'], direction: 'east' });
ok(
  partial.crossings === 3 && !partial.errors.length && partial.terrain === 'unavailable',
  'asymmetric props/fences do not imply a terrain seam is verified',
);
const root = path.join(__dirname, '..');
const actual = checkZoneBorders(root);
ok(
  actual.seams.length > 0 && !actual.errors.length,
  'every current generated neighbour has a shared open crossing',
);
ok(
  new Set(actual.seams.map((s) => s.id)).size === actual.seams.length,
  'actual seams checked once',
);
const strict = checkZoneBorders(root, { requireTerrain: true });
const missing = actual.seams.filter((s) => s.terrain === 'unavailable').length;
ok(
  strict.errors.length === missing && strict.terrainVerified === actual.terrainVerified,
  'strict mode fails every missing semantic export rather than announcing false approval',
);
ok(
  JSON.stringify(actual) === JSON.stringify(checkZoneBorders(root)),
  'border inspection is deterministic and read-only',
);
console.log(
  `Zone border checker: ${checks} assertions passed, including bad-road and blocked-seam negative fixtures.`,
);
