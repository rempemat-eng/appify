/**
 * C24: actual keyboard hook + garden/world helper + home callback contracts.
 * React effects, window events, timers and router delivery are substitutes.
 * The home callbacks are selected from the actual TS AST, not copied here.
 * No browser, React scheduling, Reanimated, images or native-device claim.
 */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const ts = require('typescript');
const root = path.resolve(__dirname, '..');
let checks = 0;
const failures = [];
function test(name, run) {
  try {
    run();
    checks++;
  } catch (error) {
    failures.push(`${name}: ${error.message}`);
  }
}
const compile = (source) =>
  ts.transpileModule(source, {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
  }).outputText;
function evaluate(
  source,
  globals,
  importer = (id) => {
    throw new Error(`Unexpected import ${id}`);
  },
) {
  const module = { exports: {} };
  vm.runInNewContext(compile(source), {
    module,
    exports: module.exports,
    require: importer,
    ...globals,
  });
  return module.exports;
}
const keyboardSource = fs.readFileSync(path.join(root, 'lib/keyboard-walk.ts'), 'utf8');

/** A deterministic effect/event clock; callbacks from cleared timers can be probed too. */
function keyboard({ platform = 'web', windowPresent = true } = {}) {
  const hooks = [];
  let cursor = 0;
  let effects = [];
  let serial = 0;
  const timers = new Map();
  const listeners = new Map();
  const calls = { steps: [], stops: 0 };
  const react = {
    useRef(value) {
      const i = cursor++;
      return (hooks[i] ??= { current: value });
    },
    useEffect(fn, deps) {
      const i = cursor++;
      const old = hooks[i];
      if (!old || !deps || deps.some((v, n) => !Object.is(v, old.deps?.[n]))) {
        effects.push(() => {
          old?.cleanup?.();
          hooks[i] = { deps, cleanup: fn() };
        });
      }
    },
  };
  const window = {
    addEventListener(type, fn) {
      if (!listeners.has(type)) listeners.set(type, new Set());
      listeners.get(type).add(fn);
    },
    removeEventListener(type, fn) {
      listeners.get(type)?.delete(fn);
    },
  };
  const mod = evaluate(
    keyboardSource,
    {
      ...(windowPresent ? { window } : {}),
      setInterval(fn, ms) {
        assert.equal(ms, 120);
        const id = ++serial;
        timers.set(id, fn);
        return id;
      },
      clearInterval(id) {
        timers.delete(id);
      },
    },
    (id) => {
      if (id === 'react') return react;
      if (id === 'react-native') return { Platform: { OS: platform } };
      throw new Error(`Unexpected keyboard import ${id}`);
    },
  );
  return {
    ...mod,
    calls,
    timers,
    listeners,
    render(
      enabled = true,
      step = (dx, dy) => calls.steps.push([dx, dy]),
      stop = () => calls.stops++,
    ) {
      cursor = 0;
      effects = [];
      mod.useKeyboardWalk(enabled, step, stop);
      for (const effect of effects) effect();
    },
    event(type, key, options = {}) {
      const e = {
        key,
        target: null,
        prevented: false,
        preventDefault() {
          this.prevented = true;
        },
        ...options,
      };
      for (const fn of listeners.get(type) ?? []) fn(e);
      return e;
    },
    tick() {
      for (const fn of timers.values()) fn();
    },
    unmount() {
      for (const hook of hooks) hook?.cleanup?.();
    },
  };
}
const pure = keyboard();
const dir = (keys) => JSON.stringify(pure.heldDirection(keys));
for (const [keys, expected] of [
  [[], null],
  [['unknown'], null],
  [['w'], { dx: 0, dy: -1 }],
  [['W', 'w', 'ArrowUp'], { dx: 0, dy: -1 }],
  [['ArrowLeft', 'd'], null],
  [['w', 's', 'a', 'd'], null],
  [['w', 'ArrowRight'], { dx: Math.SQRT1_2, dy: -Math.SQRT1_2 }],
])
  test(`held direction ${JSON.stringify(keys)}`, () => {
    const got = pure.heldDirection(keys);
    if (!expected) assert.equal(got, null);
    else {
      assert.ok(Math.abs(got.dx - expected.dx) < 1e-12);
      assert.ok(Math.abs(got.dy - expected.dy) < 1e-12);
    }
  });
test('directions do not mutate caller-held keys', () => {
  const keys = new Set(['w', 'd']);
  const before = [...keys];
  dir(keys);
  assert.deepEqual([...keys], before);
});
for (const [dx, dy] of [
  [0, -1],
  [0, 1],
  [-1, 0],
  [1, 0],
  [Math.SQRT1_2, Math.SQRT1_2],
])
  test(`keySteps priority ${dx},${dy}`, () => {
    const steps = pure.keySteps(dx, dy);
    assert.equal(JSON.stringify(steps[0]), JSON.stringify([dx, dy]));
    assert.equal(steps.length, 3);
    for (const [x, y] of steps) assert.ok(Math.abs(Math.hypot(x, y) - 1) < 1e-12);
    if (dx && dy) {
      assert.equal(
        JSON.stringify(steps.slice(1)),
        JSON.stringify([
          [1, 0],
          [0, 1],
        ]),
      );
    } else
      for (const [x, y] of steps.slice(1))
        assert.ok(dx ? Math.sign(x) === dx : Math.sign(y) === dy);
  });

for (const target of [{ tagName: 'INPUT' }, { tagName: 'TEXTAREA' }, { isContentEditable: true }])
  test(`typing ignored ${JSON.stringify(target)}`, () => {
    const f = keyboard();
    f.render();
    const e = f.event('keydown', 'w', { target });
    f.tick();
    assert.equal(e.prevented, false);
    assert.equal(f.calls.steps.length, 0);
    assert.equal(f.timers.size, 0);
    f.unmount();
  });
for (const modifier of ['altKey', 'ctrlKey', 'metaKey'])
  test(`${modifier} shortcuts ignored`, () => {
    const f = keyboard();
    f.render();
    const e = f.event('keydown', 'ArrowDown', { [modifier]: true });
    assert.equal(e.prevented, false);
    assert.equal(f.timers.size, 0);
    f.unmount();
  });
test('immediate step, one timer, repeats do not accelerate, final release stops once', () => {
  const f = keyboard();
  f.render();
  assert.equal(f.event('keydown', 'd').prevented, true);
  assert.equal(f.calls.steps.length, 1);
  f.event('keydown', 'd', { repeat: true });
  assert.equal(f.calls.steps.length, 1);
  assert.equal(f.timers.size, 1);
  f.tick();
  assert.equal(f.calls.steps.length, 2);
  f.event('keyup', 'd');
  f.event('keyup', 'd');
  f.tick();
  assert.equal(f.timers.size, 0);
  assert.equal(f.calls.steps.length, 2);
  assert.equal(f.calls.stops, 1);
  f.unmount();
});
test('releasing one axis retains the other', () => {
  const f = keyboard();
  f.render();
  f.event('keydown', 'w');
  f.event('keydown', 'd');
  f.event('keyup', 'd');
  f.tick();
  assert.equal(JSON.stringify(f.calls.steps.at(-1)), '[0,-1]');
  assert.equal(f.calls.stops, 0);
  f.unmount();
});
test('mixed-case release clears the same physical letter', () => {
  const f = keyboard();
  f.render();
  f.event('keydown', 'W');
  f.event('keyup', 'w');
  assert.equal(f.timers.size, 0);
  assert.equal(f.calls.stops, 1);
  f.unmount();
});
test('blur stops once and forgets held keys', () => {
  const f = keyboard();
  f.render();
  f.event('keydown', 'w');
  f.event('blur');
  f.event('blur');
  f.tick();
  assert.equal(f.calls.stops, 1);
  assert.equal(f.calls.steps.length, 1);
  f.event('keydown', 'd');
  assert.equal(JSON.stringify(f.calls.steps.at(-1)), '[1,0]');
  f.unmount();
});
test('effect rerender uses latest callbacks without duplicate listeners', () => {
  const f = keyboard();
  f.render();
  f.event('keydown', 'w');
  let next = 0;
  f.render(true, () => next++);
  f.tick();
  assert.equal(next, 1);
  assert.equal(f.listeners.get('keydown').size, 1);
  f.unmount();
});
for (const options of [{ platform: 'ios' }, { platform: 'android' }, { windowPresent: false }])
  test(`no keyboard on ${JSON.stringify(options)}`, () => {
    const f = keyboard(options);
    f.render();
    assert.equal(f.listeners.size, 0);
    assert.equal(f.timers.size, 0);
  });
test('disabled mount, disabling and unmount leave no event listeners or live timer', () => {
  const f = keyboard();
  f.render(false);
  assert.equal(f.listeners.size, 0);
  f.render(true);
  f.event('keydown', 'w');
  f.render(false);
  assert.equal(f.timers.size, 0);
  for (const set of f.listeners.values()) assert.equal(set.size, 0);
  f.render(true);
  f.event('keydown', 'd');
  f.unmount();
  assert.equal(f.timers.size, 0);
  for (const set of f.listeners.values()) assert.equal(set.size, 0);
});
test('opposite-key cancellation then release resumes the still-held direction', () => {
  const f = keyboard();
  f.render();
  f.event('keydown', 'w');
  f.event('keydown', 's');
  f.tick();
  assert.equal(f.timers.size, 0);
  const before = f.calls.steps.length;
  f.event('keyup', 's');
  f.tick();
  assert.ok(f.calls.steps.length > before, 'W remains held but no step resumes after S release');
  f.unmount();
});

// Transpile real pure modules, replacing only PNG bytes with inert import tokens.
const cache = new Map();
function load(file) {
  file = path.resolve(file);
  if (file.endsWith('.png')) return file;
  if (cache.has(file)) return cache.get(file);
  const out = evaluate(fs.readFileSync(file, 'utf8'), {}, (id) => {
    const resolved = id.startsWith('@/')
      ? path.join(root, id.slice(2))
      : id.startsWith('.')
        ? path.resolve(path.dirname(file), id)
        : null;
    assert.ok(
      resolved && resolved.startsWith(root + path.sep),
      `Unexpected pure-module import ${id}`,
    );
    return load(
      resolved.endsWith('.png') || resolved.endsWith('.ts') ? resolved : resolved + '.ts',
    );
  });
  cache.set(file, out);
  return out;
}
const garden = load(path.join(root, 'lib/garden-path.ts'));
const places = load(path.join(root, 'lib/world-places.ts'));
const region = load(path.join(root, 'lib/region-walk.ts'));
const maps = load(path.join(root, 'lib/garden-map.ts'));
const exits = [
  ['gate', { x: 162, y: maps.GARDEN.fenceY }],
  ['trail', { x: garden.TRAIL_X, y: 44 }],
  ['west', { x: 14, y: 440 }],
  ['east', { x: maps.GARDEN.width - 14, y: 220 }],
];
for (const [id, p] of exits)
  test(`${JSON.stringify(id)} actual helpers reach correct neighbouring tile`, () => {
    assert.equal(garden.gardenExitToward(p), id);
    assert.equal(garden.atGardenExit(id, p), true);
    const walk = places.exitWalk(id, p.x, p.y);
    const grid = garden.makeWalkGrid(region.regionWalk('valley'), {
      cell: maps.GARDEN.cell,
      width: region.regionBounds('valley').width,
      start: walk.start,
    });
    const startCell = grid.nearestWalkable(walk.start);
    const goalCell = grid.nearestWalkable(walk.goal);
    const start = grid.toPoint(startCell.cx, startCell.cy);
    const goal = grid.toPoint(goalCell.cx, goalCell.cy);
    const route = grid.findPath(start, goal);
    assert.ok(route.length > 0, 'exit must be reachable in the exported grid');
    const end = route.at(-1);
    assert.ok(Math.hypot(end.x - goal.x, end.y - goal.y) <= maps.GARDEN.cell * 2);
    assert.equal(region.tileAt('valley', goal.x, goal.y).id, places.exits[id].zone);
  });
for (const p of [
  { x: NaN, y: 0 },
  { x: 0, y: Infinity },
  { x: 160, y: 200 },
  { x: 40, y: 44 },
])
  test(`no accidental garden exit ${JSON.stringify(p)}`, () =>
    assert.equal(garden.gardenExitToward(p), null));

// Narrow callback seam: execute actual homeAt/homeward/goHome declarations in a
// closure with controlled focus/refs/router. This is NOT a full World render.
const worldFile = path.join(root, 'app/world.tsx');
const worldSource = fs.readFileSync(worldFile, 'utf8');
const ast = ts.createSourceFile(
  worldFile,
  worldSource,
  ts.ScriptTarget.Latest,
  true,
  ts.ScriptKind.TSX,
);
function declaration(name) {
  const matches = [];
  function visit(node) {
    if (ts.isVariableDeclaration(node) && ts.isIdentifier(node.name) && node.name.text === name)
      matches.push(node);
    ts.forEachChild(node, visit);
  }
  visit(ast);
  assert.equal(matches.length, 1, `exactly one real ${name} declaration required`);
  return `const ${matches[0].getText(ast)};`;
}
function homeFixture(spawn) {
  const routes = [];
  const arrivals = [];
  let focused = true;
  const mod = evaluate(
    [
      declaration('homeAt'),
      declaration('outside'),
      declaration('goHome'),
      declaration('homeward'),
      'exports.homeward = homeward;',
    ].join('\n'),
    {
      spawn,
      useRef: (current) => ({ current }),
      insideDoor: places.regionPoint(places.doors.inside),
      HUT_DOOR: garden.HUT_DOOR,
      inGardenYard: places.inGardenYard,
      navigation: { isFocused: () => focused },
      feedback() {},
      useUi: { setState: (patch) => arrivals.push(patch.homeArrival) },
      router: { replace: (route) => routes.push(route) },
    },
  );
  return {
    ...mod,
    routes,
    arrivals,
    focus(value) {
      focused = value;
    },
  };
}
const yard = (x, y) => places.regionPoint({ region: 'valley', zone: 'garden', at: [x, y] });
test('arrival callbacks actually use the source homeward rule', () => {
  for (const name of ['settle']) assert.match(declaration(name), /homeward\(at\)/);
  assert.match(worldSource, /onMove=\{\(at\) => \{[^]*?homeward\(at\)/);
});
test('standing at garden spawn does not immediately bounce home', () => {
  const at = yard(160, 300);
  const f = homeFixture({ region: 'valley', at });
  f.homeward(at);
  f.homeward(yard(180, 300));
  assert.equal(f.routes.length, 0);
});
test('walking back from outside yard returns exact garden-local coordinates', () => {
  const f = homeFixture({ region: 'valley', at: yard(-8, 440) });
  f.homeward(yard(20, 440));
  assert.equal(f.routes.length, 1);
  assert.equal(f.routes[0], '/');
  assert.equal(f.arrivals[0].x, 20);
  assert.equal(f.arrivals[0].y, 440);
});
test('stale unfocused arrival does not navigate or overwrite homeArrival', () => {
  const f = homeFixture({ region: 'valley', at: yard(-8, 440) });
  f.focus(false);
  f.homeward(yard(20, 440));
  assert.equal(f.routes.length, 0);
  assert.equal(f.arrivals.length, 0);
});
test('unrelated region never returns to the garden', () => {
  const f = homeFixture({ region: 'west', at: { x: 100, y: 100 } });
  f.homeward({ x: 160, y: 300 });
  assert.equal(f.routes.length, 0);
});
test('hut door waits for walking away before returning to the garden door', () => {
  const at = places.regionPoint(places.doors.inside);
  const f = homeFixture({ region: 'home', at });
  f.homeward(at);
  assert.equal(f.routes.length, 0);
  f.homeward({ x: at.x, y: at.y - 30 });
  f.homeward(at);
  assert.equal(f.routes.length, 1);
  assert.equal(f.arrivals[0].x, garden.HUT_DOOR.x);
  assert.equal(f.arrivals[0].y, garden.HUT_DOOR.y);
});
test('walking 24px inside yard returns home once across move and settle callbacks', () => {
  const f = homeFixture({ region: 'valley', at: yard(160, 300) });
  f.homeward(yard(184, 300));
  f.homeward(yard(184, 300));
  assert.equal(f.routes.length, 1, 'same focused arrival must not dispatch router.replace twice');
  assert.equal(f.arrivals.length, 1, 'homeArrival must be committed once');
});
test('a second queued arrival after crossing into yard cannot commit again', () => {
  const f = homeFixture({ region: 'valley', at: yard(-8, 440) });
  f.homeward(yard(20, 440));
  f.homeward(yard(24, 440));
  assert.equal(
    f.routes.length,
    1,
    'route can remain focused until router delivery; need synchronous once guard',
  );
});

console.log(`Keyboard/exits: ${checks} passed; ${failures.length} failed`);
for (const failure of failures) console.error(`FAIL ${failure}`);
if (failures.length) process.exitCode = 1;
