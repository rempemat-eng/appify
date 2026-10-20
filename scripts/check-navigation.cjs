/**
 * C28 source-boundary navigation ownership regressions.
 * Actual TS function/attribute bodies; hook, focus, Reanimated, path and store boundaries
 * substituted. No app/network/save writes. NOT React/Expo/native/browser scheduling.
 * Run: npm run check:navigation [-- /absolute/current-source-directory]
 */
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const { createRequire } = require('node:module');
const appDir = path.resolve(process.argv[2] ?? path.join(__dirname, '..'));
const ts = createRequire(path.join(appDir, 'package.json'))('typescript');

function source(file) {
  const text = fs.readFileSync(path.join(appDir, file), 'utf8');
  return ts.createSourceFile(file, text, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
}
const world = source('app/(tabs)/world.tsx');
const atlas = source('components/atlas-walk.tsx');
const journey = source('components/journey.tsx');
function one(file, predicate, label) {
  const matches = [];
  function visit(node) {
    if (predicate(node)) matches.push(node);
    ts.forEachChild(node, visit);
  }
  visit(file);
  assert.equal(matches.length, 1, 'source contract: exactly one ' + label);
  return matches[0];
}
const variable = (file, name) =>
  one(
    file,
    (n) => ts.isVariableDeclaration(n) && n.name.getText(file.getSourceFile()) === name,
    name,
  );
const fn = (file, name) =>
  one(file, (n) => ts.isFunctionDeclaration(n) && n.name?.text === name, name);
function evaluate(code, bindings) {
  const out = { exports: {} };
  const context = vm.createContext({ ...bindings, module: out, exports: out.exports });
  const js = ts.transpileModule(code, {
    compilerOptions: {
      module: ts.ModuleKind.CommonJS,
      jsx: ts.JsxEmit.React,
      target: ts.ScriptTarget.ES2022,
    },
  }).outputText;
  vm.runInContext(js, context, { timeout: 1000 });
  return { value: out.exports, context };
}
function expression(text, bindings) {
  return evaluate('module.exports = (' + text + ');', bindings).value;
}
const results = [];
function test(name, run) {
  try {
    run();
    results.push({ name, ok: true });
  } catch (error) {
    results.push({ name, ok: false, reason: error.message });
  }
}

// Read the actual parent props and the child's keyboard enable expression.
// A changed/missing component or hook fails extraction rather than silently dropping coverage.
const atlasTag = one(
  world,
  (n) => ts.isJsxSelfClosingElement(n) && n.tagName.getText(world) === 'AtlasWalk',
  'World AtlasWalk',
);
function prop(name) {
  const attr = atlasTag.attributes.properties.find(
    (n) => ts.isJsxAttribute(n) && n.name.getText(world) === name,
  );
  assert.ok(attr && ts.isJsxExpression(attr.initializer), 'source prop: ' + name);
  return attr.initializer.expression.getText(world);
}
const keyboard = one(
  atlas,
  (n) => ts.isCallExpression(n) && n.expression.getText(atlas) === 'useKeyboardWalk',
  'Atlas keyboard registration',
);
const keyEnabled = keyboard.arguments[0].getText(atlas);
/** @type {Array<[string, boolean, object | null, boolean, object | null, boolean]>} */
const keyboardCases = [
  ['awake world', false, null, true, null, true],
  ['map', true, null, true, null, false],
  ['journey', false, {}, true, null, false],
  ['map and journey', true, {}, true, null, false],
  ['blur', false, null, false, null, false],
  ['blur with map', true, null, false, null, false],
  ['blur with journey', false, {}, false, null, false],
  ['parent follow ownership', false, null, true, {}, false],
];
for (const [name, mapOpen, trip, focused, follow, expected] of keyboardCases) {
  test('held-key registration: ' + name, () => {
    const interactive = expression(prop('interactive'), { mapOpen, trip });
    const active = expression(prop('active'), { focused });
    assert.equal(!!expression(keyEnabled, { interactive, active, follow }), expected);
  });
}

// Actual walkTo closure. A finished animation can queue its JS completion before
// another walk cancels the native animation. The queue is deliberately not cleared by cancel.
const shared = () => ({
  value: 0,
  plan: null,
  get() {
    return this.value;
  },
  set(v) {
    if (typeof v === 'number') this.value = v;
    else this.plan = v;
  },
});
const ease = (v) => v;
function walkFixture(reduced = false, follow = null) {
  const queue = [];
  const ownX = shared(),
    ownY = shared(),
    pos = { current: { x: 0, y: 0 } };
  const arrivals = [];
  const calls = { current: { onSettle: (p) => arrivals.push({ ...p }) } };
  const bindings = {
    follow,
    reduced,
    levels: null,
    ownX,
    ownY,
    pos,
    calls,
    region: 'fixture',
    logicalOf: (p) => p,
    toScreen: (p) => p,
    spotOf: (p) => p,
    grid: { walk: { findPath: (_from, goal) => [{ ...goal }] } },
    cancelAnimation() {},
    setLevel() {},
    setWalking() {},
    setFeet() {},
    settleSquash() {},
    setFacing() {},
    setHere() {},
    tileAt: () => undefined,
    tileWithHysteresis: () => undefined,
    legFacing: () => null,
    maxWalkMs: undefined,
    SPEED: 80,
    KEY_SPEED: 100,
    Easing: { linear: ease, quad: ease, inOut: ease, in: ease, out: ease },
    runOnJS:
      (f) =>
      (...args) =>
        queue.push(() => f(...args)),
    withTiming: (to, config, callback) => ({ to, config, callback }),
    withSequence: (...steps) => ({ steps }),
    ride() {
      throw new Error('unexpected lift in ground fixture');
    },
  };
  const walk = expression(variable(atlas, 'walkTo').initializer.getText(atlas), bindings);
  return {
    walk,
    pos,
    calls,
    arrivals,
    complete(finished = true) {
      const end = ownY.plan?.steps?.at(-1);
      assert.ok(end?.callback, 'actual final Y timing callback exists');
      end.callback(finished);
    },
    flush() {
      while (queue.length) queue.shift()();
    },
  };
}
test('walk control: normal completion arrives once', () => {
  const h = walkFixture();
  h.walk({ x: 10, y: 20 });
  h.complete();
  h.flush();
  assert.deepEqual(h.arrivals, [{ x: 10, y: 20 }]);
});
test('walk control: reduced motion arrives immediately', () => {
  const h = walkFixture(true);
  h.walk({ x: 10, y: 20 });
  assert.deepEqual(h.arrivals, [{ x: 10, y: 20 }]);
});
test('walk control: cancelled animation does not arrive', () => {
  const h = walkFixture();
  h.walk({ x: 10, y: 20 });
  h.complete(false);
  h.flush();
  assert.equal(h.arrivals.length, 0);
});
test('walk control: parent follow owns movement', () => {
  const h = walkFixture(false, {});
  h.walk({ x: 10, y: 20 });
  assert.equal(h.arrivals.length, 0);
  assert.equal(h.pos.current.x, 0);
});
for (const action of ['pass', 'door', 'journey']) {
  test('superseded walk must not dispatch latest parent ' + action, () => {
    const h = walkFixture(),
      dispatched = [];
    h.walk({ x: 10, y: 20 });
    h.complete(); // finished, JS arrival not yet run
    h.calls.current = { onSettle: () => dispatched.push(action) };
    h.walk({ x: 70, y: 80 }); // new intention before the queued old JS callback
    h.flush();
    assert.equal(dispatched.length, 0, 'old queued arrival called current ' + action + ' callback');
    assert.notEqual(h.pos.current.x, 10, 'old queued arrival replaced current position');
  });
}

// Actual World arrive/legDone bodies, with pure boundary spies instead of real stores/router.
function tripParent(legs = ['steam']) {
  const state = { writes: 0, home: 0, spawn: { key: 0 } };
  const b = {
    trip: { from: 'valley', legs, leg: 0 },
    dest: legs.at(-1),
    travelPoints: Object.fromEntries(
      ['steam', 'neon'].map((id) => [id, { region: id, at: { x: 10, y: 20 } }]),
    ),
    regionPoint: (p) => p.at,
    HUB_REGION: 'valley',
    toGarden: (p) => p,
    navigation: { isFocused: () => true },
    useCallback: (callback) => callback,
    setSpawn: (f) => {
      state.spawn = f(state.spawn);
    },
    setGoal() {},
    setZone() {},
    setCard() {},
    tileAt: () => undefined,
    doorAt: () => null,
    outside: { current: false },
    walkWorld: () => state.writes++,
    sendHome: () => state.home++,
  };
  const e = evaluate(
    'const arrive = ' +
      variable(world, 'arrive').initializer.getText(world) +
      ';\n' +
      'const legDone = ' +
      variable(world, 'legDone').initializer.getText(world) +
      ';\n' +
      'module.exports={arrive,legDone};',
    {
      ...b,
      setTrip: (v) => {
        e.context.trip = v;
      },
    },
  );
  return { ...e.value, state, context: e.context };
}
const journeyFn = fn(journey, 'Journey');
const layerStatement = journeyFn.body.statements.find(
  (n) =>
    ts.isVariableStatement(n) &&
    n.declarationList.declarations.some((v) => v.name.getText(journey) === 'layers'),
);
assert.ok(layerStatement, 'Journey lifecycle/render boundary exists');
const journeyPrefix = journeyFn.body.statements
  .filter((n) => n.end <= layerStatement.pos)
  .map((n) => n.getText(journey))
  .join('\n');
function journeyFixture(parent, { active = true, reduced = false } = {}) {
  let cleanup, timing, timer;
  const queue = [];
  const e = evaluate(
    'function life({onArrive,onSkip,ms}){\n' +
      journeyPrefix +
      '\nreturn {skip};}\nmodule.exports=life;',
    {
      useReducedMotion: () => reduced,
      useAppActive: () => active,
      useSharedValue: () => ({ set() {} }),
      useRef: (v) => ({ current: v }),
      useEffect: (callback) => {
        cleanup = callback();
      },
      cancelAnimation() {},
      setTimeout: (f) => {
        timer = f;
        return 1;
      },
      clearTimeout: () => {
        timer = null;
      },
      STILL_MS: 500,
      Easing: { quad: null, inOut: () => null },
      runOnJS: (f) => () => queue.push(f),
      withTiming: (_to, _config, callback) => {
        timing = callback;
        return {};
      },
    },
  );
  const control = e.value({ onArrive: parent.legDone, onSkip: parent.arrive, ms: 100 });
  return {
    ...control,
    queueFinish() {
      assert.ok(timing);
      timing(true);
    },
    flush() {
      while (queue.length) queue.shift()();
    },
    finish() {
      assert.ok(timing);
      timing(true);
      while (queue.length) queue.shift()();
    },
    cancelled() {
      assert.ok(timing);
      timing(false);
      while (queue.length) queue.shift()();
    },
    still() {
      assert.ok(timer);
      timer();
    },
    unmount() {
      cleanup?.();
    },
  };
}
test('journey: SKIP then queued final leg commits once', () => {
  const p = tripParent(),
    j = journeyFixture(p);
  j.queueFinish();
  j.skip();
  j.flush();
  j.skip();
  assert.equal(p.state.writes, 1);
});
test('journey: final leg then SKIP commits once', () => {
  const p = tripParent(),
    j = journeyFixture(p);
  j.finish();
  j.skip();
  j.finish();
  assert.equal(p.state.writes, 1);
});
test('journey: SKIP racing intermediate leg ends whole trip once', () => {
  const p = tripParent(['steam', 'neon']),
    j = journeyFixture(p);
  j.queueFinish();
  j.skip();
  j.flush();
  assert.equal(p.state.writes, 1);
  assert.equal(p.state.spawn.region, 'neon');
});
test('journey: completed intermediate leg then new-leg SKIP commits once', () => {
  const p = tripParent(['steam', 'neon']),
    first = journeyFixture(p);
  first.finish();
  first.unmount();
  assert.equal(p.state.writes, 0);
  const next = journeyFixture(p);
  next.skip();
  next.finish();
  assert.equal(p.state.writes, 1);
});
test('journey control: cancelled timing is not arrival', () => {
  const p = tripParent(),
    j = journeyFixture(p);
  j.cancelled();
  assert.equal(p.state.writes, 0);
});
test('journey: background arrival commits once', () => {
  const p = tripParent(),
    j = journeyFixture(p, { active: false });
  j.skip();
  j.unmount();
  assert.equal(p.state.writes, 1);
});
test('journey: reduced motion timer and SKIP commit once', () => {
  const p = tripParent(),
    j = journeyFixture(p, { reduced: true });
  j.still();
  j.skip();
  j.unmount();
  assert.equal(p.state.writes, 1);
});
test('journey: leaving screen mid-trip commits destination once', () => {
  const p = tripParent(),
    j = journeyFixture(p);
  j.unmount(); // WorldTab removes World on blur, which removes this Journey.
  assert.equal(
    p.state.writes,
    1,
    'unmount cancelled the animation but never committed destination',
  );
});

// WorldTab renders World at a hook boundary. The child's real link initializer and
// consume effect are extracted; presentation and all unrelated World hooks are excluded.
const worldFn = fn(world, 'World');
const linkDeclaration = variable(worldFn, '[link]');
const linkStatement = worldFn.body.statements.find(
  (n) => ts.isVariableStatement(n) && n.declarationList.declarations.includes(linkDeclaration),
);
const clearEffect = one(
  worldFn,
  (n) =>
    ts.isCallExpression(n) &&
    n.expression.getText(world) === 'useEffect' &&
    n.arguments[0]?.getText(world).includes('worldLink: null'),
  'world link consume effect',
);
const childProbe =
  'function World(){const params={};\n' +
  linkStatement.getText(world) +
  '\n' +
  clearEffect.getText(world) +
  ';\nreturn link;}';
function refocusFixture() {
  let focused = false,
    ui = null,
    current,
    pending = false,
    child = null;
  const parent = { hooks: [], cursor: 0, effects: [] },
    mounts = [];
  const useState = (init) => {
    const c = current,
      i = c.cursor++;
    if (!(i in c.hooks)) c.hooks[i] = typeof init === 'function' ? init() : init;
    return [
      c.hooks[i],
      (v) => {
        c.hooks[i] = typeof v === 'function' ? v(c.hooks[i]) : v;
        pending = true;
      },
    ];
  };
  const useRef = (init) => {
    const c = current,
      i = c.cursor++;
    if (!(i in c.hooks)) c.hooks[i] = { current: init };
    return c.hooks[i];
  };
  const useEffect = (callback, deps) => {
    const c = current,
      i = c.cursor++,
      old = c.hooks[i];
    if (!old || deps.some((v, j) => !Object.is(v, old[j]))) c.effects.push(callback);
    c.hooks[i] = deps;
  };
  const component = evaluate(fn(world, 'WorldTab').getText(world) + '\n' + childProbe, {
    useState,
    useRef,
    useEffect,
    useIsFocused: () => focused,
    useUi: {
      getState: () => ({ worldLink: ui }),
      setState: (s) => {
        ui = s.worldLink;
      },
    },
    React: { createElement: (type, props) => ({ type, key: props?.key ?? null }) },
  }).value.default;
  function render() {
    current = parent;
    parent.cursor = 0;
    parent.effects = [];
    const element = component();
    if (!element) child = null;
    else if (!child || child.key !== element.key) {
      child = { key: element.key, hooks: [], cursor: 0, effects: [] };
      mounts.push(child);
    }
    if (child) {
      current = child;
      child.cursor = 0;
      child.effects = [];
      child.link = element.type();
    }
    if (child) for (const effect of child.effects) effect();
    for (const effect of parent.effects) effect();
  }
  return {
    mounts,
    drive(focus, link) {
      focused = focus;
      if (link !== undefined) ui = link;
      let limit = 10;
      do {
        pending = false;
        render();
        assert.ok(--limit > 0, 'focus render loop');
      } while (pending);
      return child?.link ?? null;
    },
  };
}
test('world tab: first visit and same-focus render consume one link once', () => {
  const h = refocusFixture(),
    link = { trip: { from: 'valley', to: 'steam' } };
  assert.equal(JSON.stringify(h.drive(true, link)), JSON.stringify(link));
  h.drive(true);
  assert.equal(h.mounts.length, 1);
  assert.equal(h.drive(false), null);
});
test('world tab: second visit preserves latest ferry link and mounts once', () => {
  const h = refocusFixture();
  h.drive(true, { from: 'hut' });
  h.drive(false);
  const link = { trip: { from: 'pier', to: 'isles' } };
  const actual = h.drive(true, link);
  assert.equal(JSON.stringify(actual), JSON.stringify(link), 'refocus discarded latest WorldLink');
  assert.equal(h.mounts.length, 2, 'one child per visit');
});
for (const r of results)
  console.log((r.ok ? 'PASS ' : 'FAIL ') + r.name + (r.ok ? '' : '\n  ' + r.reason));
const failed = results.filter((r) => !r.ok);
console.log(
  results.length +
    ' navigation cases: ' +
    (results.length - failed.length) +
    ' passed, ' +
    failed.length +
    ' failed. Source-boundary harness, not runtime certification.',
);
if (failed.length) process.exitCode = 1;
