/**
 * Exercises the actual Home and rhythm card with React, native UI, storage and
 * timers replaced at their boundaries. Checks emitted props, state transitions
 * and cleanup, not real React scheduling, modal stacking or native lifecycle.
 */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const ts = require('typescript');

process.env.TZ = 'Europe/London';
let checks = 0;
const check = (condition, message) => {
  assert.ok(condition, message);
  checks++;
};
const boundary = new Proxy({}, { get: (_, name) => name });
const jsx = (type, props) => ({ type, props: props || {} });
const jsxRuntime = { jsx, jsxs: jsx, Fragment: 'Fragment' };

function hooks() {
  const slots = [];
  let index = 0;
  let changed = false;
  let effects = new Map();
  const equal = (a, b) =>
    a !== undefined && b !== undefined && a.length === b.length && a.every((v, i) => Object.is(v, b[i]));
  const react = {
    useState(initial) {
      const at = index++;
      if (!slots[at]) slots[at] = { value: typeof initial === 'function' ? initial() : initial };
      return [slots[at].value, (update) => {
        const value = typeof update === 'function' ? update(slots[at].value) : update;
        if (!Object.is(value, slots[at].value)) {
          slots[at].value = value;
          changed = true;
        }
      }];
    },
    useRef(initial) {
      const at = index++;
      if (!slots[at]) slots[at] = { current: initial };
      return slots[at];
    },
    useCallback(callback, dependencies) {
      const at = index++;
      if (!slots[at] || !equal(slots[at].dependencies, dependencies))
        slots[at] = { dependencies, callback };
      return slots[at].callback;
    },
    useEffect(effect, dependencies) {
      const at = index++;
      if (!slots[at]) slots[at] = {};
      effects.set(at, { effect, dependencies });
    },
  };
  return {
    react,
    render(Component, props) {
      let tree;
      let settled = false;
      for (let attempt = 0; attempt < 12; attempt++) {
        index = 0;
        changed = false;
        effects = new Map();
        tree = Component(props);
        if (!changed) { settled = true; break; }
      }
      assert.ok(settled, 'fixture render must settle');
      for (const [at, next] of effects) {
        if (!equal(slots[at].dependencies, next.dependencies)) {
          slots[at].cleanup?.();
          slots[at].dependencies = next.dependencies;
          slots[at].cleanup = next.effect();
        }
      }
      return tree;
    },
    unmount() {
      for (const slot of slots) slot?.cleanup?.();
    },
  };
}

function load(file, imports, globals = {}) {
  const sourcePath = path.join(__dirname, '..', file);
  const source = ts.transpileModule(fs.readFileSync(sourcePath, 'utf8'), {
    compilerOptions: {
      module: ts.ModuleKind.CommonJS,
      jsx: ts.JsxEmit.ReactJSX,
      target: ts.ScriptTarget.ES2022,
    },
  }).outputText;
  const module = { exports: {} };
  vm.runInNewContext(source, {
    module,
    exports: module.exports,
    require: imports,
    console,
    ...globals,
  }, { filename: sourcePath });
  return module.exports;
}

function nodes(tree) {
  if (tree === null || tree === undefined || typeof tree === 'boolean') return [];
  if (Array.isArray(tree)) return tree.flatMap(nodes);
  if (typeof tree !== 'object') return [tree];
  return [tree, ...nodes(tree.props?.children)];
}
function find(tree, predicate) {
  const result = nodes(tree).find((node) => typeof node === 'object' && predicate(node));
  assert.ok(result, 'expected rendered node');
  return result;
}
const byType = (tree, type) => find(tree, (node) => node.type === type);
const text = (tree) => nodes(tree).filter((node) => typeof node === 'string').join(' ');
function timers() {
  const timeouts = new Map();
  const intervals = new Map();
  let serial = 0;
  return {
    timeouts,
    intervals,
    globals: {
      setTimeout(callback, delay) { const id = ++serial; timeouts.set(id, { callback, delay }); return id; },
      clearTimeout(id) { timeouts.delete(id); },
      setInterval(callback, delay) { const id = ++serial; intervals.set(id, { callback, delay }); return id; },
      clearInterval(id) { intervals.delete(id); },
    },
    flush(delay) {
      for (const [id, timer] of [...timeouts]) {
        if (timer.delay !== delay) continue;
        timeouts.delete(id);
        timer.callback();
      }
    },
  };
}

function homeFixture() {
  const runtime = hooks();
  const clock = timers();
  const control = { focused: false, foreground: true };
  const seen = [];
  const state = {
    player: { id: 'test', pet_name: 'MOSS', species: 'BLOB', mode: 'awake', mood: 50, grass: 30, level: 1, offline_seconds: 0 },
    now: 0, voice: null, firstWake: false, tips: [], companionMemories: [],
    alerts: [], seeTip: (tip) => seen.push(tip),
  };
  const useGame = (selector) => selector(state);
  useGame.getState = () => state;
  const Home = load('components/game-screens.tsx', (id) => {
    if (id === 'react') return runtime.react;
    if (id === 'react/jsx-runtime') return jsxRuntime;
    if (id === 'react-native') return { ...Object.fromEntries(['FlatList', 'KeyboardAvoidingView', 'Modal', 'Pressable', 'ScrollView', 'TextInput', 'View'].map((name) => [name, name])), Platform: { OS: 'web' }, useWindowDimensions: () => ({ height: 800, width: 390 }) };
    if (id === 'expo-router') return { useIsFocused: () => control.focused, router: {} };
    if (id === 'react-native-safe-area-context') return { useSafeAreaInsets: () => ({ top: 0, bottom: 0 }) };
    if (id === '@/lib/game') return { useGame, status: () => ({ kind: 'care' }) };
    if (id === '@/lib/cozy') return { cozy: {} };
    if (id === '@/lib/layout') return { gameLayout: { gutter: 16, maxWidth: 640 }, dockClearance: () => 90 };
    if (id === '@/lib/motion') return { useReducedMotion: () => false };
    if (id === '@/lib/app-active') return { useAppActive: () => control.foreground };
    if (id === '@/lib/garden-view') return { useGardenView: () => ['flat', () => {}] };
    if (id === '@/lib/visitors') return { guardianPlayer: (player) => player, isVisitorId: () => false };
    if (id === '@/lib/grasslings') return { grasslings: { BLOB: { name: 'Mossling', habit: 'Rest' } }, growthStage: () => 'Sprout', levelPreview: () => ({ next: 2, cost: 20, unlock: 'A new outing' }) };
    if (id === '@/lib/first-session') return { gardenTips: { phone: { text: 'phone' }, wake: { text: 'wake' }, budget: { text: 'budget' } } };
    if (id === '@/components/offline-garden') return { usePlayPaused: () => false, ...Object.fromEntries(['GardenProgress', 'GardenStreak', 'RecentBreaks', 'PlayPause', 'TogetherInvite'].map((name) => [name, name])) };
    if (id === '@/components/game-ui') return { Page: 'Page', PixelButton: 'PixelButton', PixelText: 'PixelText', styles: {} };
    if (id.startsWith('@/components/') || id.startsWith('@/lib/') || id === 'lucide-react-native') return boundary;
    throw new Error('Unexpected Home import: ' + id);
  }, clock.globals).HomeScreen;
  return { control, state, seen, clock, runtime, render: () => runtime.render(Home) };
}

async function main() {
  const home = homeFixture();
  let tree = home.render();
  check(!byType(tree, 'GardenWorld').props.active, 'unfocused Home is inactive');
  check(home.seen.length === 0, 'unfocused Home does not consume guidance');
  home.state.firstWake = true;
  tree = home.render();
  check(home.seen.length === 0, 'a wake on another tab does not consume the wake tip');
  home.control.focused = true;
  home.control.foreground = false;
  tree = home.render();
  check(home.seen.length === 0, 'background Home does not consume guidance');
  home.control.foreground = true;
  tree = home.render();
  check(byType(tree, 'GardenWorld').props.active, 'visible uncovered Home activates the garden');
  check(home.seen.length === 1 && home.seen[0] === 'wake', 'wake guidance is consumed only when visible');
  byType(tree, 'DailyRhythmCard').props.onOpenChange(true);
  tree = home.render();
  check(byType(tree, 'DailyRhythmCard').props.open, 'Home controls the planner sheet');
  check(!byType(tree, 'GardenWorld').props.active, 'opening the planner deactivates in-flight garden work');
  check(!byType(tree, 'DailyRhythmCard').props.active, 'the planner clock shares the covered Home activity gate');
  check(home.clock.intervals.size === 0, 'planner coverage pauses dialogue rotation');
  home.control.focused = false;
  tree = home.render();
  check(!byType(tree, 'DailyRhythmCard').props.open, 'tab blur closes the controlled planner');
  home.control.focused = true;
  tree = home.render();
  check(!byType(tree, 'DailyRhythmCard').props.open, 'returning Home does not reopen a stale planner');
  check(byType(tree, 'GardenWorld').props.active, 'returning Home reactivates its quiet garden');
  home.runtime.unmount();
  check(home.clock.intervals.size === 0 && home.clock.timeouts.size === 0, 'Home timers clean up');

  let instant = new Date(2026, 9, 16, 16, 59).getTime();
  class ClockDate extends Date {
    static now() { return instant; }
  }
  const rules = load('lib/daily-rhythm.ts', (id) => { throw new Error(id); }, { Date: ClockDate });
  const plan = { ...rules.freshRhythm(), enabled: true };

  async function plannerFixture(raw) {
    const runtime = hooks();
    const clock = timers();
    const changes = [];
    const props = { active: true, open: false, onOpenChange(open) { changes.push(open); props.open = open; } };
    const Card = load('components/daily-rhythm.tsx', (id) => {
      if (id === 'react') return runtime.react;
      if (id === 'react/jsx-runtime') return jsxRuntime;
      if (id === 'react-native') return { StyleSheet: { create: (styles) => styles }, Platform: { OS: 'web' }, ...Object.fromEntries(['View', 'Pressable'].map((name) => [name, name])) };
      if (id === '@react-native-async-storage/async-storage') return { default: { getItem: async () => raw } };
      if (id === '@/lib/daily-rhythm') return rules;
      if (id === '@/lib/cozy') return { cozy: {} };
      if (id === '@/lib/layout') return { gameLayout: { gutter: 16, maxWidth: 640 } };
      if (id === 'react-native-safe-area-context' || id === 'lucide-react-native' || id.startsWith('@/components/')) return boundary;
      throw new Error('Unexpected planner import: ' + id);
    }, { ...clock.globals, Date: ClockDate }).DailyRhythmCard;
    const render = () => runtime.render(Card, props);
    render();
    for (let i = 0; i < 4; i++) await Promise.resolve();
    return { runtime, clock, props, changes, render };
  }
  const planner = await plannerFixture(JSON.stringify(plan));
  tree = planner.render();
  planner.clock.flush(0);
  tree = planner.render();
  check(text(tree).includes('Focus now'), 'loaded planner shows the current focus window');
  check(planner.clock.intervals.size === 1, 'visible enabled planner owns one clock');
  find(tree, (node) => node.props.accessibilityLabel === 'Edit your daily rhythm').props.onPress();
  tree = planner.render();
  check(planner.props.open && planner.clock.intervals.size === 0, 'editing reports coverage and pauses the card clock');
  find(tree, (node) => typeof node.type === 'function' && node.type.name === 'RhythmEditor').props.onClose();
  tree = planner.render();
  check(!planner.props.open && planner.clock.intervals.size === 1, 'cancel closes the editor and resumes one clock');
  planner.props.active = false;
  tree = planner.render();
  check(planner.clock.intervals.size === 0 && planner.clock.timeouts.size === 0, 'inactive planner removes all clock work');
  instant = new Date(2026, 9, 16, 17, 1).getTime();
  planner.props.active = true;
  tree = planner.render();
  planner.clock.flush(0);
  tree = planner.render();
  check(text(tree).includes('Own time now'), 'foreground refresh crosses the window boundary without waiting thirty seconds');
  check(planner.clock.intervals.size === 1, 'resume does not duplicate the planner clock');
  planner.runtime.unmount();
  check(planner.clock.intervals.size === 0 && planner.clock.timeouts.size === 0, 'planner unmount clears clock work');

  const broken = await plannerFixture('{invalid');
  tree = broken.render();
  check(text(tree).includes('Your saved planner could not load.'), 'unreadable planner offers explicit recovery');
  find(tree, (node) => node.type === 'PixelButton' && node.props.label === 'NEW PLAN').props.onPress();
  tree = broken.render();
  check(broken.changes.at(-1) === true && broken.props.open, 'NEW PLAN reports the same parent coverage as normal editing');
  const editor = find(tree, (node) => typeof node.type === 'function' && node.type.name === 'RhythmEditor');
  editor.props.onSaved(rules.freshRhythm());
  tree = broken.render();
  check(broken.changes.at(-1) === false && !broken.props.open, 'save closes the parent-controlled planner');
  check(broken.clock.intervals.size === 0, 'disabled saved plan schedules no clock');
  broken.runtime.unmount();
  console.log('PASS: ' + checks + ' actual Home/planner coverage, hidden guidance, recovery and clock lifecycle assertions.');
}
main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
