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

const equal = (a, b) =>
  a !== undefined && b !== undefined && a.length === b.length && a.every((v, i) => Object.is(v, b[i]));

function hooks() {
  const slots = [];
  let index = 0;
  let changed = false;
  let effects = new Map();
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
      esModuleInterop: true,
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
      for (const [id, timer] of timeouts) {
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
  const naps = [];
  const state = {
    player: { id: 'test', pet_name: 'MOSS', species: 'BLOB', mode: 'awake', mood: 50, grass: 30, level: 1, offline_seconds: 0 },
    now: 0, voice: null, firstWake: false, tips: [], companionMemories: [],
    alerts: [], seeTip: (tip) => seen.push(tip),
    sleep(mission, intention) {
      naps.push({ mission, intention });
      state.player = { ...state.player, mode: 'screen_off' };
    },
  };
  const useGame = (selector) => selector(state);
  useGame.getState = () => state;
  const Home = load('components/game-screens.tsx', (id) => {
    if (id === 'react') return runtime.react;
    if (id === 'react/jsx-runtime') return jsxRuntime;
    if (id === 'react-native') return { ...Object.fromEntries(['FlatList', 'KeyboardAvoidingView', 'Modal', 'Pressable', 'ScrollView', 'TextInput', 'View'].map((name) => [name, name])), Platform: { OS: 'web' }, useWindowDimensions: () => ({ height: 800, width: 390 }) };
    if (id === 'expo-router') return { useIsFocused: () => control.focused, router: {} };
    if (id === 'react-native-safe-area-context') return { useSafeAreaInsets: () => ({ top: 0, bottom: 0 }) };
    if (id === '@/lib/game') return { useGame, status: () => ({ kind: 'care' }), feedback: () => {} };
    if (id === '@/lib/cozy') return { cozy: {} };
    if (id === '@/lib/layout') return { gameLayout: { gutter: 16, maxWidth: 640 }, dockClearance: () => 90 };
    if (id === '@/lib/motion') return { useReducedMotion: () => false };
    if (id === '@/lib/app-active') return { useAppActive: () => control.foreground };
    if (id === '@/lib/garden-view') return { useGardenView: () => ['flat', () => {}] };
    if (id === '@/lib/visitors') return { guardianPlayer: (player) => player, isVisitorId: () => false };
    if (id === '@/lib/grasslings') return { grasslings: { BLOB: { name: 'Mossling', habit: 'Rest' } }, growthStage: () => 'Sprout', levelPreview: () => ({ next: 2, cost: 20, unlock: 'A new outing' }) };
    if (id === '@/lib/companion-memories') return { breakIntentionLabel: (value) => ({ rest: 'Rest', read: 'Read', move: 'Move', create: 'Create' })[value] };
    if (id === '@/lib/first-session') return { gardenTips: { phone: { text: 'phone' }, wake: { text: 'wake' }, budget: { text: 'budget' } } };
    if (id === '@/components/offline-garden') return { usePlayPaused: () => false, ...Object.fromEntries(['GardenProgress', 'GardenStreak', 'RecentBreaks', 'PlayPause', 'TogetherInvite'].map((name) => [name, name])) };
    if (id === '@/components/game-ui') return { Page: 'Page', PixelButton: 'PixelButton', PixelText: 'PixelText', styles: {} };
    if (id.startsWith('@/components/') || id.startsWith('@/lib/') || id === 'lucide-react-native') return boundary;
    throw new Error('Unexpected Home import: ' + id);
  }, clock.globals).HomeScreen;
  return { control, state, seen, naps, clock, runtime, render: () => runtime.render(Home) };
}

function visitorPresentationFixture(welcome = false) {
  const runtime = hooks();
  const clock = timers();
  const control = { reduced: false, height: 844, width: 390 };
  const calls = [];
  const shared = [];
  const reward = { settlementId: 'break', cards: [], minutes: 15, grass: 20, visitor: null, postcard: null, hat: null, early: false };
  const state = {
    player: { id: 'test', species: 'BLOB', pet_name: 'MOSS', mode: 'awake', level: 1, collection: [] },
    waitingVisitor: welcome ? null : { id: 'dozebud', expiresAt: 0 },
    now: 0, cardReward: welcome ? reward : null, pendingMemories: [],
    sessions: [], pendingTogetherWakes: [],
    befriendVisitor() {
      calls.push('befriend');
      state.player.collection = [{ id: state.waitingVisitor.id, befriendedAt: 1 }];
      state.waitingVisitor = null;
    },
    dismissCards() { calls.push('dismiss'); state.cardReward = null; },
    sleep() { calls.push('sleep'); state.player.mode = 'screen_off'; },
  };
  const useGame = (selector) => selector(state);
  useGame.getState = () => state;
  const components = load('components/visitors.tsx', (id) => {
    if (id === 'react') return runtime.react;
    if (id === 'react/jsx-runtime') return jsxRuntime;
    if (id === 'react-native') return { View: 'View', ScrollView: 'ScrollView', useWindowDimensions: () => ({ height: control.height, width: control.width }) };
    if (id === 'expo-router') return { router: { navigate: (path) => calls.push('navigate:' + path), replace: (path) => calls.push('replace:' + path) } };
    if (id === 'react-native-safe-area-context') return { useSafeAreaInsets: () => ({ top: 0, bottom: 0 }) };
    if (id === 'react-native-svg') return { __esModule: true, default: 'Svg', Rect: 'Rect' };
    if (id === 'react-native-reanimated') return {
      __esModule: true,
      default: { View: 'AnimatedView' },
      FadeIn: { duration: (duration) => ({ duration }) },
      cancelAnimation: (value) => { value.plan = null; },
      useAnimatedStyle: (getStyle) => getStyle(),
      useSharedValue(initial) {
        const ref = runtime.react.useRef(null);
        if (!ref.current) {
          ref.current = { value: initial, plan: null, set(value) {
            this.plan = typeof value === 'object' ? value : null;
            this.value = typeof value === 'object' ? value.to : value;
          } };
          shared.push(ref.current);
        }
        return ref.current;
      },
      withTiming: (to, options) => ({ to, options }),
      withDelay: (delay, animation) => ({ ...animation, delay }),
    };
    if (id === '@/lib/game') return { useGame, palette: {} };
    if (id === '@/lib/cozy') return { cozy: {}, panelStyle: {} };
    if (id === '@/lib/motion') return { useReducedMotion: () => control.reduced };
    if (id === '@/lib/visitors') return { collectionOf: (player) => player.collection, guardianPlayer: (player) => player, visitorInfo: (id) => ({ id, name: id.toUpperCase() }) };
    if (id === '@/lib/cards') return { cards: {}, cardIds: [] };
    if (id === '@/lib/layout') return { gameLayout: { maxWidth: 640, gutter: 16 } };
    if (id.startsWith('@/components/') || id === 'lucide-react-native') return boundary;
    throw new Error('Unexpected visitor presentation import: ' + id);
  }, clock.globals);
  return { runtime, clock, control, calls, shared, state, render: (active = true) => runtime.render(welcome ? components.WelcomeBack : components.GardenVisitor, { active }) };
}

function visitorAndReturnChecks() {
  const visitor = visitorPresentationFixture();
  let tree = visitor.render();
  const oldPress = byType(tree, 'Pet').props.onPress;
  check(byType(tree, 'Pet').props.active && visitor.shared[0].plan !== null, 'visible visitor owns its finite peek and active pet');
  tree = visitor.render(false);
  check(tree === null && visitor.shared[0].plan === null && visitor.clock.timeouts.size === 0, 'hidden visitor removes its target and decorative work');
  oldPress();
  check(visitor.calls.length === 0, 'a retained visitor callback cannot befriend while covered');
  tree = visitor.render(true);
  const firstVisitorPress = byType(tree, 'Pet').props.onPress;
  visitor.state.waitingVisitor = { id: 'trailhop', expiresAt: 0 };
  tree = visitor.render(true);
  firstVisitorPress();
  check(visitor.calls.length === 0, 'a retained callback cannot befriend a different arriving visitor');
  byType(tree, 'Pet').props.onPress();
  tree = visitor.render(true);
  check(visitor.calls[0] === 'befriend' && byType(tree, 'PixelBurst'), 'current visitor can befriend and celebrate');
  check(visitor.clock.timeouts.size === 1, 'celebration owns one finite timer');
  tree = visitor.render(false);
  check(tree === null && visitor.clock.timeouts.size === 0, 'coverage cancels a pending celebration');
  tree = visitor.render(true);
  check(tree === null, 'resuming does not replay a hidden celebration');
  visitor.state.waitingVisitor = { id: 'dozebud', expiresAt: 0 };
  visitor.control.reduced = true;
  tree = visitor.render(true);
  check(byType(tree, 'AnimatedView').props.entering === undefined && visitor.shared[0].plan === null, 'reduced motion keeps a static visitor without a peek or fade');
  visitor.runtime.unmount();
  check(visitor.clock.timeouts.size === 0, 'visitor unmount clears presentation timers');

  const rest = visitorPresentationFixture(true);
  tree = rest.render();
  check(rest.calls.length === 0, 'rendering rewards never starts another break automatically');
  check(text(tree).includes('simulated offline MIN'), 'return labels the accelerated break clock');
  find(tree, (node) => node.type === 'PixelButton' && node.props.label === 'START A NAP').props.onPress();
  check(rest.calls.join('|') === 'dismiss|replace:/|sleep' && rest.state.player.mode === 'screen_off', 'explicit departure settles the sheet then starts the existing untimed nap');
  rest.runtime.unmount();
  const garden = visitorPresentationFixture(true);
  garden.control.height = 320;
  garden.control.width = 320;
  tree = garden.render();
  check(byType(tree, 'CozySheet').props.style.maxHeight <= 320 && byType(tree, 'ScrollView').props.style.maxHeight >= 0, 'short return window emits bounded sheet and scroll caps');
  find(tree, (node) => node.type === 'PixelButton' && node.props.label === 'BACK TO THE GARDEN').props.onPress();
  check(garden.calls.join('|') === 'dismiss|navigate:/' && garden.state.player.mode === 'awake', 'garden route remains an independent explicit choice');
  garden.runtime.unmount();
}

function journeyChecks() {
  for (const guardian of [null, 'inkling']) {
    const runtime = hooks();
    const calls = [];
    const player = { guardian, collection: [{ id: 'dozebud', befriendedAt: 1 }], postcards: [{ mission: 'park' }, { mission: 'book' }] };
    const Journey = load('components/garden-journey.tsx', (id) => {
      if (id === 'react') return runtime.react;
      if (id === 'react/jsx-runtime') return jsxRuntime;
      if (id === 'react-native' || id === 'lucide-react-native' || id.startsWith('@/components/')) return boundary;
      if (id === '@/lib/cozy') return { cozy: {} };
      if (id === '@/lib/companion-profiles') return { companionProfile: (value) => ({ id: value.guardian, name: value.guardian ? 'INKLING' : 'MOSS', invitation: { title: 'A little idea', body: 'A little time away.' } }) };
      if (id === '@/lib/visitors') return { collectionOf: (value) => value.collection, befriendedVisitorIds: (value) => value.collection.map((entry) => entry.id), postcardsOf: (value) => value.postcards };
      throw new Error('Unexpected journey import: ' + id);
    }).GardenJourney;
    const props = { player, onMissions: () => calls.push('missions'), onJournal: () => calls.push('journal'), onCompanions: () => calls.push('companions'), onSpar: () => calls.push('spar') };
    let tree = runtime.render(Journey, props);
    check(byType(tree, 'PixelButton').props.label === 'PLAN A BREAK', 'established companion choice keeps an offline outing as the primary invitation');
    check(!text(tree).includes('VISIT DAVE') && !text(tree).includes('MEET YOUR COMPANIONS'), 'practice and pet switching remain secondary trail details');
    byType(tree, 'PixelButton').props.onPress();
    check(calls.join('|') === 'missions', 'the primary invitation goes to break planning');
    find(tree, (node) => node.props.accessibilityLabel === 'Explore the garden trail').props.onPress();
    tree = runtime.render(Journey, props);
    check(text(tree).includes(guardian ? 'VISIT DAVE' : 'MEET YOUR COMPANIONS'), 'the expanded trail preserves optional garden discoveries');
    runtime.unmount();
  }
}

async function main() {
  visitorAndReturnChecks();
  journeyChecks();
  const home = homeFixture();
  let tree = home.render();
  check(!byType(tree, 'GardenWorld').props.active, 'unfocused Home is inactive');
  check(!byType(tree, 'GardenVisitor').props.active, 'unfocused Home pauses the visiting companion');
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
  check(byType(tree, 'GardenVisitor').props.active, 'visible uncovered Home activates its visitor');
  check(home.seen.length === 1 && home.seen[0] === 'wake', 'wake guidance is consumed only when visible');
  byType(tree, 'DailyRhythmCard').props.onOpenChange(true);
  tree = home.render();
  check(byType(tree, 'DailyRhythmCard').props.open, 'Home controls the planner sheet');
  check(!byType(tree, 'GardenWorld').props.active, 'opening the planner deactivates in-flight garden work');
  check(!byType(tree, 'DailyRhythmCard').props.active, 'the planner clock shares the covered Home activity gate');
  check(home.clock.intervals.size === 0, 'planner coverage pauses dialogue rotation');
  check(!byType(tree, 'GardenVisitor').props.active, 'planner coverage pauses the visiting companion');
  home.control.focused = false;
  tree = home.render();
  check(!byType(tree, 'DailyRhythmCard').props.open, 'tab blur closes the controlled planner');
  home.control.focused = true;
  tree = home.render();
  check(!byType(tree, 'DailyRhythmCard').props.open, 'returning Home does not reopen a stale planner');
  check(byType(tree, 'GardenWorld').props.active, 'returning Home reactivates its quiet garden');
  find(tree, (node) => node.props.accessibilityLabel === 'Open garden stats').props.onPress();
  tree = home.render();
  check(byType(tree, 'Modal').props.visible && !byType(tree, 'GardenWorld').props.active, 'Stats covers and pauses the garden');
  home.control.focused = false;
  tree = home.render();
  check(!byType(tree, 'Modal').props.visible, 'tab blur closes Stats');
  home.control.focused = true;
  tree = home.render();
  check(!byType(tree, 'Modal').props.visible && byType(tree, 'GardenWorld').props.active, 'returning Home does not reopen stale Stats');
  home.runtime.unmount();
  check(home.clock.intervals.size === 0 && home.clock.timeouts.size === 0, 'Home timers clean up');

  const departure = homeFixture();
  departure.control.focused = true;
  tree = departure.render();
  check(!nodes(tree).some((node) => node?.type === 'BreakIntentionPicker'), 'a quick Home nap requires no intention decision');
  find(tree, (node) => node.props.accessibilityLabel === 'Choose a break idea').props.onPress();
  tree = departure.render();
  check(!byType(tree, 'GardenWorld').props.active, 'choosing an intention cancels garden work');
  byType(tree, 'BreakIntentionPicker').props.onChange('read');
  tree = departure.render();
  check(byType(tree, 'BreakIntentionPicker').props.value === 'read', 'Home holds its optional reading idea');
  find(tree, (node) => node.props.accessibilityLabel === 'Take a nap').props.onPress();
  check(departure.naps.length === 1 && departure.naps[0].mission === undefined && departure.naps[0].intention === 'read', 'header nap forwards the chosen idea to the existing ordinary nap');
  tree = departure.render();
  check(!nodes(tree).some((node) => node?.type === 'BreakIntentionPicker'), 'starting a nap closes the break preparation');
  departure.state.player = { ...departure.state.player, mode: 'awake' };
  tree = departure.render();
  find(tree, (node) => node.props.accessibilityLabel === 'Choose a break idea').props.onPress();
  tree = departure.render();
  check(byType(tree, 'BreakIntentionPicker').props.value === null, 'the next break begins with Just a break');
  byType(tree, 'BreakIntentionPicker').props.onChange('move');
  tree = departure.render();
  byType(tree, 'GardenWorld').props.onNap();
  check(departure.naps[1].intention === 'move', 'the garden bed delegates the same selected idea');
  departure.state.player = { ...departure.state.player, mode: 'awake' };
  tree = departure.render();
  find(tree, (node) => node.type === 'PixelButton' && node.props.label === 'TAKE A NAP').props.onPress();
  check(departure.naps[2].intention === null, 'the primary quick nap preserves no-intention default');
  departure.state.player = { ...departure.state.player, mode: 'awake' };
  tree = departure.render();
  find(tree, (node) => node.props.accessibilityLabel === 'Choose a break idea').props.onPress();
  tree = departure.render();
  byType(tree, 'BreakIntentionPicker').props.onChange('create');
  departure.control.focused = false;
  departure.render();
  departure.control.focused = true;
  tree = departure.render();
  check(!nodes(tree).some((node) => node?.type === 'BreakIntentionPicker') && text(tree).includes('A break idea, if you like'), 'leaving Home clears the unfinished break choice');
  departure.runtime.unmount();

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
      if (id === '@react-native-async-storage/async-storage') return { __esModule: true, default: { getItem: async () => raw } };
      if (id === '@/lib/daily-rhythm') return rules;
      if (id === '@/lib/cozy') return { cozy: {} };
      if (id === '@/lib/layout') return { gameLayout: { gutter: 16, maxWidth: 640 } };
      if (id === 'react-native-safe-area-context' || id === 'lucide-react-native' || id.startsWith('@/components/')) return boundary;
      throw new Error('Unexpected planner import: ' + id);
    }, { ...clock.globals, Date: ClockDate }).DailyRhythmCard;
    const render = () => runtime.render(Card, props);
    render();
    // Let both VM and host promise queues settle after the storage result.
    await new Promise((resolve) => setImmediate(resolve));
    return { runtime, clock, props, changes, render };
  }
  const planner = await plannerFixture(JSON.stringify(plan));
  tree = planner.render();
  planner.clock.flush(0);
  tree = planner.render();
  check(text(tree).includes('Focus now'), 'loaded planner shows the current focus window: ' + text(tree));
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
  console.log('PASS: ' + checks + ' actual Home, break preparation, visitor, return, journey and planner lifecycle assertions.');
}
main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
