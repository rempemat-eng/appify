/**
 * Exercises Home, rhythm, visitors, returns and journey with React, native UI, storage and
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
  a !== undefined &&
  b !== undefined &&
  a.length === b.length &&
  a.every((v, i) => Object.is(v, b[i]));

function hooks() {
  const slots = [];
  let index = 0;
  let changed = false;
  let effects = new Map();
  const react = {
    useState(initial) {
      const at = index++;
      if (!slots[at]) slots[at] = { value: typeof initial === 'function' ? initial() : initial };
      return [
        slots[at].value,
        (update) => {
          const value = typeof update === 'function' ? update(slots[at].value) : update;
          if (!Object.is(value, slots[at].value)) {
            slots[at].value = value;
            changed = true;
          }
        },
      ];
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
    useMemo(compute, dependencies) {
      const at = index++;
      if (!slots[at] || !equal(slots[at].dependencies, dependencies))
        slots[at] = { dependencies, value: compute() };
      return slots[at].value;
    },
    useLayoutEffect(effect, dependencies) {
      react.useEffect(effect, dependencies);
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
        if (!changed) {
          settled = true;
          break;
        }
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
  vm.runInNewContext(
    source,
    {
      module,
      exports: module.exports,
      require: imports,
      console,
      ...globals,
    },
    { filename: sourcePath },
  );
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
const text = (tree) =>
  nodes(tree)
    .filter((node) => typeof node === 'string')
    .join(' ');
function timers() {
  const timeouts = new Map();
  const intervals = new Map();
  let serial = 0;
  return {
    timeouts,
    intervals,
    globals: {
      setTimeout(callback, delay) {
        const id = ++serial;
        timeouts.set(id, { callback, delay });
        return id;
      },
      clearTimeout(id) {
        timeouts.delete(id);
      },
      setInterval(callback, delay) {
        const id = ++serial;
        intervals.set(id, { callback, delay });
        return id;
      },
      clearInterval(id) {
        intervals.delete(id);
      },
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
  const control = { focused: false, foreground: true, ambience: undefined };
  const ui = { sheet: null };
  const seen = [];
  const naps = [];
  const state = {
    player: {
      id: 'test',
      pet_name: 'MOSS',
      species: 'BLOB',
      mode: 'awake',
      mood: 50,
      grass: 30,
      level: 1,
      offline_seconds: 0,
    },
    // Local noon: the garden's daytime ambience.
    now: new Date(2026, 9, 16, 12).getTime(),
    missionReturnPending: false,
    voice: null,
    firstWake: false,
    tips: [],
    companionMemories: [],
    alerts: [],
    decor: [],
    seeTip: (tip) => seen.push(tip),
    sleep(mission, intention) {
      naps.push({ mission, intention });
      state.player = { ...state.player, mode: 'screen_off' };
    },
  };
  const useGame = (selector) => selector(state);
  useGame.getState = () => state;
  const Home = load(
    'components/game-screens.tsx',
    (id) => {
      if (id === 'react') return runtime.react;
      if (id === 'react/jsx-runtime') return jsxRuntime;
      if (id === 'react-native')
        return {
          ...Object.fromEntries(
            [
              'FlatList',
              'KeyboardAvoidingView',
              'Modal',
              'Pressable',
              'ScrollView',
              'TextInput',
              'View',
            ].map((name) => [name, name]),
          ),
          Platform: { OS: 'web' },
          useWindowDimensions: () => ({ height: 800, width: 390 }),
        };
      if (id === 'expo-router') return { useIsFocused: () => control.focused, router: {} };
      if (id === 'react-native-safe-area-context')
        return { useSafeAreaInsets: () => ({ top: 0, bottom: 0 }) };
      if (id === '@/lib/game')
        return { useGame, status: () => ({ kind: 'care' }), feedback: () => {} };
      if (id === '@/lib/cozy') return { cozy: {} };
      if (id === '@/lib/layout')
        return {
          gameLayout: { gutter: 16, maxWidth: 640 },
          hotbarClearance: () => 90,
          hudClearance: () => 70,
        };
      if (id === '@/lib/ui')
        return {
          useUi: (selector) => selector(ui),
          openSheet: (sheet) => {
            ui.sheet = sheet;
          },
          closeSheet: () => {
            ui.sheet = null;
          },
        };
      if (id === '@/components/garden-journey') return { gardenMarker: () => 'missions' };
      // keepsakes (C12): not decorating here; the model is tested in check:world
      if (id === '@/lib/decor')
        return {
          checkDecor: () => ({ ok: true }),
          foundKeepsakes: () => [],
          tapToDecorate: () => ({ hand: null, walk: null }),
        };
      if (id === '@/lib/motion') return { useReducedMotion: () => false };
      if (id === '@/lib/app-active') return { useAppActive: () => control.foreground };
      if (id === '@/lib/sound')
        return {
          useAmbience(kind) {
            control.ambience = kind;
          },
        };
      if (id === '@/lib/garden-view') return { useGardenView: () => ['flat', () => {}] };
      if (id === '@/lib/visitors')
        return { guardianPlayer: (player) => player, isVisitorId: () => false };
      if (id === '@/lib/grasslings')
        return {
          grasslings: { BLOB: { name: 'Mossling', habit: 'Rest' } },
          growthStage: () => 'Sprout',
          levelPreview: () => ({ next: 2, cost: 20, unlock: 'A new outing' }),
        };
      if (id === '@/lib/companion-memories')
        return {
          breakIntentionLabel: (value) =>
            ({ rest: 'Rest', read: 'Read', move: 'Move', create: 'Create' })[value],
        };
      if (id === '@/lib/first-session')
        return {
          gardenTips: {
            phone: { text: 'phone' },
            wake: { text: 'wake' },
            budget: { text: 'budget' },
          },
        };
      if (id === '@/components/offline-garden')
        return {
          usePlayPaused: () => false,
          ...Object.fromEntries(
            ['GardenProgress', 'GardenStreak', 'RecentBreaks', 'PlayPause', 'TogetherInvite'].map(
              (name) => [name, name],
            ),
          ),
        };
      if (id === '@/components/game-ui')
        return { Page: 'Page', PixelButton: 'PixelButton', PixelText: 'PixelText', styles: {} };
      if (id.startsWith('@/components/') || id.startsWith('@/lib/') || id === 'lucide-react-native')
        return boundary;
      throw new Error('Unexpected Home import: ' + id);
    },
    clock.globals,
  ).HomeScreen;
  return { control, state, seen, naps, clock, runtime, ui, render: () => runtime.render(Home) };
}

function napSheetFixture() {
  const runtime = hooks();
  const ui = { sheet: 'nap' };
  const naps = [];
  const state = {
    player: { id: 'test', pet_name: 'MOSS', species: 'BLOB', mode: 'awake', mood: 50, grass: 30 },
    sleep(mission, intention) {
      naps.push({ mission, intention });
      state.player = { ...state.player, mode: 'screen_off' };
    },
  };
  const useGame = (selector) => selector(state);
  useGame.getState = () => state;
  const NapSheet = load('components/game-menus.tsx', (id) => {
    if (id === 'react') return runtime.react;
    if (id === 'react/jsx-runtime') return jsxRuntime;
    if (id === 'react-native')
      return {
        ...Object.fromEntries(
          ['Modal', 'Pressable', 'ScrollView', 'Text', 'View'].map((name) => [name, name]),
        ),
        useWindowDimensions: () => ({ height: 800, width: 390 }),
      };
    if (id === 'expo-router') return { router: { push: () => {} } };
    if (id === 'react-native-safe-area-context')
      return { useSafeAreaInsets: () => ({ top: 0, bottom: 0 }) };
    if (id === '@/lib/game') return { useGame, feedback: () => {} };
    if (id === '@/lib/ui')
      return {
        useUi: (selector) => selector(ui),
        openSheet: (sheet) => {
          ui.sheet = sheet;
        },
        closeSheet: () => {
          ui.sheet = null;
        },
      };
    if (id === '@/lib/visitors') return { guardianPlayer: (player) => player };
    if (id === '@/components/offline-garden')
      return { usePlayPaused: () => false, GardenProgress: 'GardenProgress' };
    if (id === '@/components/game-ui')
      return { PixelButton: 'PixelButton', PixelText: 'PixelText' };
    if (id.startsWith('@/components/') || id.startsWith('@/lib/')) return boundary;
    throw new Error('Unexpected menu import: ' + id);
  }).NapSheet;
  return { ui, state, naps, runtime, render: () => runtime.render(NapSheet) };
}

function visitorPresentationFixture(welcome = false) {
  const runtime = hooks();
  const clock = timers();
  const control = { reduced: false, height: 844, width: 390 };
  const calls = [];
  const shared = [];
  const reward = {
    settlementId: 'break',
    cards: [],
    minutes: 15,
    grass: 20,
    visitor: null,
    postcard: null,
    hat: null,
    early: false,
  };
  const state = {
    player: {
      id: 'test',
      species: 'BLOB',
      pet_name: 'MOSS',
      mode: 'awake',
      level: 1,
      collection: [],
    },
    waitingVisitor: welcome ? null : { id: 'dozebud', expiresAt: 0 },
    now: 0,
    missionReturnPending: false,
    cardReward: welcome ? reward : null,
    pendingMemories: [],
    sessions: [],
    pendingTogetherWakes: [],
    befriendVisitor() {
      calls.push('befriend');
      state.player.collection = [{ id: state.waitingVisitor.id, befriendedAt: 1 }];
      state.waitingVisitor = null;
    },
    dismissCards() {
      calls.push('dismiss');
      state.cardReward = null;
      state.missionReturnPending = false;
      state.player.mode = 'awake';
    },
    sleep() {
      calls.push('sleep');
      state.player.mode = 'screen_off';
    },
  };
  const useGame = (selector) => selector(state);
  useGame.getState = () => state;
  const components = load(
    'components/visitors.tsx',
    (id) => {
      if (id === 'react') return runtime.react;
      if (id === 'react/jsx-runtime') return jsxRuntime;
      if (id === 'react-native')
        return {
          View: 'View',
          ScrollView: 'ScrollView',
          useWindowDimensions: () => ({ height: control.height, width: control.width }),
        };
      if (id === 'expo-router')
        return {
          router: {
            navigate: (destination) => calls.push('navigate:' + destination),
            replace: (destination) => calls.push('replace:' + destination),
          },
        };
      if (id === 'react-native-safe-area-context')
        return { useSafeAreaInsets: () => ({ top: 0, bottom: 0 }) };
      if (id === 'react-native-svg') return { __esModule: true, default: 'Svg', Rect: 'Rect' };
      if (id === 'react-native-reanimated')
        return {
          __esModule: true,
          default: { View: 'AnimatedView' },
          FadeIn: { duration: (duration) => ({ duration }) },
          cancelAnimation: (value) => {
            value.plan = null;
          },
          useAnimatedStyle: (getStyle) => getStyle(),
          useSharedValue(initial) {
            const ref = runtime.react.useRef(null);
            if (!ref.current) {
              ref.current = {
                value: initial,
                plan: null,
                set(value) {
                  this.plan = typeof value === 'object' ? value : null;
                  this.value = typeof value === 'object' ? value.to : value;
                },
              };
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
      if (id === '@/lib/visitors')
        return {
          collectionOf: (player) => player.collection,
          guardianPlayer: (player) => player,
          visitorInfo: (visitorId) => ({ id: visitorId, name: visitorId.toUpperCase() }),
        };
      if (id === '@/lib/cards') return { cards: {}, cardIds: [] };
      if (id === '@/lib/layout') return { gameLayout: { maxWidth: 640, gutter: 16 } };
      if (id === '@/lib/world-catalogue')
        return load('lib/world-catalogue.ts', (dependency) => {
          throw new Error('Unexpected catalogue import: ' + dependency);
        });
      if (id === '@/lib/scene-assets')
        return load('lib/scene-assets.ts', (asset) => {
          if (asset.endsWith('.png')) return asset;
          throw new Error('Unexpected scene asset import: ' + asset);
        });
      if (id.startsWith('@/components/') || id === 'lucide-react-native') return boundary;
      throw new Error('Unexpected visitor presentation import: ' + id);
    },
    clock.globals,
  );
  return {
    runtime,
    clock,
    control,
    calls,
    shared,
    state,
    render: (active = true) =>
      runtime.render(welcome ? components.WelcomeBack : components.GardenVisitor, { active }),
  };
}

function visitorAndReturnChecks() {
  const visitor = visitorPresentationFixture();
  let tree = visitor.render();
  const oldPress = byType(tree, 'Pet').props.onPress;
  check(
    byType(tree, 'Pet').props.active && visitor.shared[0].plan !== null,
    'visible visitor owns its finite peek and active pet',
  );
  tree = visitor.render(false);
  check(
    tree === null && visitor.shared[0].plan === null && visitor.clock.timeouts.size === 0,
    'hidden visitor removes its target and decorative work',
  );
  oldPress();
  check(visitor.calls.length === 0, 'a retained visitor callback cannot befriend while covered');
  tree = visitor.render(true);
  const firstVisitorPress = byType(tree, 'Pet').props.onPress;
  visitor.state.waitingVisitor = { id: 'trailhop', expiresAt: 0 };
  tree = visitor.render(true);
  firstVisitorPress();
  check(
    visitor.calls.length === 0,
    'a retained callback cannot befriend a different arriving visitor',
  );
  byType(tree, 'Pet').props.onPress();
  tree = visitor.render(true);
  check(
    visitor.calls[0] === 'befriend' && byType(tree, 'PixelBurst'),
    'current visitor can befriend and celebrate',
  );
  check(visitor.clock.timeouts.size === 1, 'celebration owns one finite timer');
  tree = visitor.render(false);
  check(
    tree === null && visitor.clock.timeouts.size === 0,
    'coverage cancels a pending celebration',
  );
  tree = visitor.render(true);
  check(tree === null, 'resuming does not replay a hidden celebration');
  visitor.state.waitingVisitor = { id: 'dozebud', expiresAt: 0 };
  visitor.control.reduced = true;
  tree = visitor.render(true);
  check(
    byType(tree, 'AnimatedView').props.entering === undefined && visitor.shared[0].plan === null,
    'reduced motion keeps a static visitor without a peek or fade',
  );
  visitor.runtime.unmount();
  check(visitor.clock.timeouts.size === 0, 'visitor unmount clears presentation timers');

  const rest = visitorPresentationFixture(true);
  tree = rest.render();
  check(rest.calls.length === 0, 'rendering rewards never starts another break automatically');
  check(text(tree).includes('simulated offline MIN'), 'return labels the accelerated break clock');
  find(
    tree,
    (node) => node.type === 'PixelButton' && node.props.label === 'START A NAP',
  ).props.onPress();
  check(
    rest.calls.join('|') === 'dismiss|replace:/|sleep' && rest.state.player.mode === 'screen_off',
    'explicit departure settles the sheet then starts the existing untimed nap',
  );
  rest.runtime.unmount();
  const garden = visitorPresentationFixture(true);
  garden.control.height = 320;
  garden.control.width = 320;
  tree = garden.render();
  check(
    byType(tree, 'CozySheet').props.style.maxHeight <= 320 &&
      byType(tree, 'ScrollView').props.style.maxHeight >= 0,
    'short return window emits bounded sheet and scroll caps',
  );
  const originalBodyCap = byType(tree, 'ScrollView').props.style.maxHeight;
  find(tree, (node) => node.props.accessibilityRole === 'header').props.onLayout({
    nativeEvent: { layout: { height: 48 } },
  });
  find(tree, (node) => {
    const children = Array.isArray(node.props.children)
      ? node.props.children
      : [node.props.children];
    return (
      typeof node.props.onLayout === 'function' &&
      children.some((child) => child?.type === 'PixelButton' && child.props.label === 'START A NAP')
    );
  }).props.onLayout({ nativeEvent: { layout: { height: 160 } } });
  tree = garden.render();
  check(
    byType(tree, 'ScrollView').props.style.maxHeight < originalBodyCap &&
      byType(tree, 'CozySheet').props.style.maxHeight <= 320,
    'larger measured heading and footer reduce body space within the short window',
  );
  find(
    tree,
    (node) => node.type === 'PixelButton' && node.props.label === 'BACK TO THE GARDEN',
  ).props.onPress();
  check(
    garden.calls.join('|') === 'dismiss|navigate:/' && garden.state.player.mode === 'awake',
    'garden route remains an independent explicit choice',
  );
  garden.runtime.unmount();

  const completed = visitorPresentationFixture(true);
  completed.state.player.mode = 'mission';
  completed.state.missionReturnPending = true;
  tree = completed.render();
  check(
    text(tree).includes('your garden is still shielded') &&
      text(tree).includes('play time begin when you choose BACK TO THE GARDEN') &&
      completed.calls.length === 0 &&
      completed.state.player.mode === 'mission',
    'completed mission welcome explains pending protection without returning during render',
  );
  find(
    tree,
    (node) => node.type === 'PixelButton' && node.props.label === 'BACK TO THE GARDEN',
  ).props.onPress();
  check(
    completed.calls.join('|') === 'dismiss|navigate:/' &&
      !completed.state.missionReturnPending &&
      completed.state.player.mode === 'awake',
    'completed mission returns through the same explicit garden action',
  );
  completed.runtime.unmount();
}

function napReturnControls() {
  const runtime = hooks();
  const clock = timers();
  const calls = [];
  const state = {
    ready: true,
    player: { mode: 'mission', mission_id: 'book', mission_ends_at: 30000 },
    missionReturnPending: false,
    battle: null,
    alerts: [],
    message: null,
    flash: null,
    guideOpen: false,
    deckOpen: false,
    cardReward: null,
    recap: null,
    wake() {
      calls.push('wake');
    },
    dismissCards() {
      calls.push('dismiss');
    },
  };
  const useGame = (selector) => selector(state);
  useGame.getState = () => state;
  useGame.setState = (patch) => Object.assign(state, patch);
  const { GameOverlays } = load(
    'components/game-overlays.tsx',
    (id) => {
      if (id === 'react') return runtime.react;
      if (id === 'react/jsx-runtime') return jsxRuntime;
      if (id === 'react-native')
        return {
          ...boundary,
          View: 'View',
          Modal: 'Modal',
          useWindowDimensions: () => ({ width: 390, height: 844 }),
        };
      if (id === 'react-native-reanimated')
        return {
          __esModule: true,
          default: boundary,
          FadeIn: boundary,
        };
      if (id === 'react-native-safe-area-context')
        return {
          useSafeAreaInsets: () => ({ top: 20, bottom: 16 }),
        };
      if (id === '@/lib/game') return { useGame, gameStore: useGame };
      if (id === '@/lib/cozy') return { cozy: { paper: 'paper', night: 'night' } };
      if (id === '@/lib/layout') return { gameSideInset: () => 16, gameColumn: {} };
      if (id === '@/lib/motion') return { useReducedMotion: () => false };
      if (id === '@/lib/overlay-priority') return load('lib/overlay-priority.ts', () => {});
      if (id.startsWith('@/') || id === 'lucide-react-native' || id === 'expo-haptics')
        return boundary;
      throw new Error('Unexpected overlay control import: ' + id);
    },
    clock.globals,
  );
  const render = () => runtime.render(GameOverlays);
  const nap = (tree) =>
    find(tree, (node) => typeof node.type === 'function' && node.type.name === 'ScreenOff');
  let tree = render();
  check(!nap(tree).props.confirmEarlyReturn, 'timed mission starts without a return prompt');
  byType(tree, 'Modal').props.onRequestClose();
  tree = render();
  check(
    nap(tree).props.confirmEarlyReturn && calls.length === 0,
    'Escape or native Back requests confirmation instead of forfeiting a timed mission',
  );
  byType(tree, 'Modal').props.onRequestClose();
  tree = render();
  check(
    !nap(tree).props.confirmEarlyReturn && calls.length === 0,
    'Back on the confirmation keeps exploring without waking',
  );
  nap(tree).props.onRequestReturn();
  tree = render();
  check(
    nap(tree).props.confirmEarlyReturn && calls.length === 0,
    'explicit wake uses the same timed-mission confirmation',
  );
  nap(tree).props.onKeepExploring();
  tree = render();
  check(
    !nap(tree).props.confirmEarlyReturn && calls.length === 0,
    'Keep Exploring cancels without a store action',
  );
  nap(tree).props.onRequestReturn();
  tree = render();
  nap(tree).props.onReturnEarly();
  check(calls.join('|') === 'wake', 'only explicit Return Early invokes wake');
  calls.length = 0;
  nap(render()).props.onRequestReturn();
  state.missionReturnPending = true;
  state.cardReward = { mission: 'book' };
  tree = render();
  check(
    nodes(tree).some((node) => node?.type === 'WelcomeBack') &&
      !nodes(tree).some(
        (node) => typeof node?.type === 'function' && node.type.name === 'ScreenOff',
      ),
    'mission completing during confirmation replaces the nap with its saved welcome',
  );
  const backdrop = byType(tree, 'Modal').props.children;
  check(
    backdrop.props.style.backgroundColor === 'paper' && backdrop.props.style.paddingBottom === 0,
    'pending mission welcome uses reward-sheet backdrop and inset despite non-awake shield mode',
  );
  state.missionReturnPending = false;
  state.cardReward = null;
  state.player = { mode: 'mission', mission_id: 'book', mission_ends_at: 60000 };
  tree = render();
  check(
    !nap(tree).props.confirmEarlyReturn,
    'a later mission never inherits an earlier confirmation',
  );
  state.player = { mode: 'screen_off', mission_id: null, mission_ends_at: 0 };
  tree = render();
  byType(tree, 'Modal').props.onRequestClose();
  check(calls.length === 0, 'Back leaves an untimed nap running');
  nap(render()).props.onRequestReturn();
  check(calls.join('|') === 'wake', 'an untimed nap still wakes through its explicit button');
  runtime.unmount();
  check(clock.timeouts.size === 0, 'return controls add no lingering timers');
}

function journeyChecks() {
  for (const guardian of [null, 'inkling']) {
    const runtime = hooks();
    const calls = [];
    const player = {
      guardian,
      collection: [{ id: 'dozebud', befriendedAt: 1 }],
      postcards: [{ mission: 'park' }, { mission: 'book' }],
    };
    const Journey = load('components/garden-journey.tsx', (id) => {
      if (id === 'react') return runtime.react;
      if (id === 'react/jsx-runtime') return jsxRuntime;
      if (id === 'react-native' || id === 'lucide-react-native' || id.startsWith('@/components/'))
        return boundary;
      if (id === '@/lib/cozy') return { cozy: {} };
      if (id === '@/lib/companion-profiles')
        return {
          companionProfile: (value) => ({
            id: value.guardian,
            name: value.guardian ? 'INKLING' : 'MOSS',
            invitation: { title: 'A little idea', body: 'A little time away.' },
          }),
        };
      if (id === '@/lib/visitors')
        return {
          collectionOf: (value) => value.collection,
          befriendedVisitorIds: (value) => value.collection.map((entry) => entry.id),
          postcardsOf: (value) => value.postcards,
        };
      throw new Error('Unexpected journey import: ' + id);
    }).GardenJourney;
    const props = {
      player,
      onMissions: () => calls.push('missions'),
      onJournal: () => calls.push('journal'),
      onCompanions: () => calls.push('companions'),
      onSpar: () => calls.push('spar'),
    };
    let tree = runtime.render(Journey, props);
    check(
      byType(tree, 'PixelButton').props.label === 'PLAN A BREAK',
      'established companion choice keeps an offline outing as the primary invitation',
    );
    check(
      !nodes(tree).some(
        (node) =>
          node?.type === 'PixelButton' &&
          ['VISIT DAVE', 'MEET YOUR COMPANIONS'].includes(node.props.label),
      ),
      'practice and pet switching remain secondary trail details',
    );
    byType(tree, 'PixelButton').props.onPress();
    check(calls.join('|') === 'missions', 'the primary invitation goes to break planning');
    find(
      tree,
      (node) => node.props.accessibilityLabel === 'Explore the garden trail',
    ).props.onPress();
    tree = runtime.render(Journey, props);
    check(
      nodes(tree).some(
        (node) =>
          node?.type === 'PixelButton' &&
          node.props.label === (guardian ? 'VISIT DAVE' : 'MEET YOUR COMPANIONS'),
      ),
      'the expanded trail preserves optional garden discoveries',
    );
    runtime.unmount();
  }
}

const unreadableSaveProblem = () => ({
  kind: 'unreadable',
  confirmationId: null,
  busy: false,
  error: null,
});

function saveRecoveryControls() {
  const runtime = hooks();
  const recoveryRuntime = hooks();
  const clock = timers();
  const calls = [];
  const state = {
    ready: true,
    player: null,
    saveLoadProblem: unreadableSaveProblem(),
    alerts: [],
    message: 'load failure',
    flash: null,
    guideOpen: false,
    deckOpen: false,
    cardReward: null,
    recap: null,
    battle: null,
    missionReturnPending: false,
    requestSaveRecovery() {
      calls.push('request');
      state.saveLoadProblem = { ...state.saveLoadProblem, confirmationId: 'current' };
      return 'current';
    },
    cancelSaveRecovery() {
      calls.push('cancel');
      state.saveLoadProblem = { ...state.saveLoadProblem, confirmationId: null };
    },
    confirmSaveRecovery(token) {
      calls.push('confirm:' + token);
      return Promise.resolve(true);
    },
    retrySaveLoad() {
      calls.push('retry');
      return Promise.resolve();
    },
  };
  const useGame = (select) => select(state);
  useGame.getState = () => state;
  useGame.setState = (patch) => Object.assign(state, patch);
  const recovery = load('components/save-recovery.tsx', (id) => {
    if (id === 'react') return recoveryRuntime.react;
    if (id === 'react/jsx-runtime') return jsxRuntime;
    if (id === 'react-native')
      return { View: 'View', Text: 'Text', ScrollView: 'ScrollView', Platform: { OS: 'web' } };
    if (id === '@/lib/game') return { gameStore: useGame };
    if (id === '@/lib/cozy') return { cozy: {} };
    if (id === '@/lib/ui-tokens')
      return {
        barControl: () => 44,
        panelGap: () => 8,
        contentInset: () => 8,
        iconSize: { medium: () => 16 },
        type: {},
      };
    if (id === '@/components/pixel-frame') return { FrameFill: 'FrameFill', usePixelUnit: () => 1 };
    if (id.startsWith('@/components/')) return boundary;
    throw new Error('Unexpected recovery import: ' + id);
  });
  const { GameOverlays } = load(
    'components/game-overlays.tsx',
    (id) => {
      if (id === 'react') return runtime.react;
      if (id === 'react/jsx-runtime') return jsxRuntime;
      if (id === 'react-native')
        return {
          View: 'View',
          Modal: 'Modal',
          useWindowDimensions: () => ({ width: 320, height: 640 }),
        };
      if (id === 'react-native-reanimated')
        return { __esModule: true, default: boundary, FadeIn: boundary };
      if (id === 'react-native-safe-area-context')
        return { useSafeAreaInsets: () => ({ top: 0, bottom: 0 }) };
      if (id === '@/lib/game') return { useGame, gameStore: useGame };
      if (id === '@/lib/cozy') return { cozy: {} };
      if (id === '@/lib/layout') return { gameSideInset: () => 8, gameColumn: {} };
      if (id === '@/lib/motion') return { useReducedMotion: () => false };
      if (id === '@/lib/overlay-priority') return load('lib/overlay-priority.ts', () => {});
      if (id === '@/components/save-recovery') return recovery;
      if (id.startsWith('@/') || id === 'expo-haptics') return boundary;
      throw new Error('Unexpected recovery-overlay import: ' + id);
    },
    clock.globals,
  );
  const render = () => runtime.render(GameOverlays);
  const controls = () =>
    recoveryRuntime.render(recovery.SaveRecovery, { problem: state.saveLoadProblem });
  const has = (tree, label) => nodes(tree).some((node) => node?.props?.label === label);
  const button = (tree, label) =>
    find(tree, (node) => node.type === 'PixelButton' && node.props.label === label);
  const back = () => byType(render(), 'Modal').props.onRequestClose();
  for (const kind of ['unreadable', 'newer', 'storage']) {
    state.saveLoadProblem = kind === 'unreadable' ? unreadableSaveProblem() : { kind };
    const tree = render();
    check(
      byType(tree, 'Modal').props.visible,
      kind + ': recovery keeps the blocking modal visible',
    );
    check(
      nodes(tree).some((node) => node.type === recovery.SaveRecovery),
      kind + ': real recovery precedes onboarding',
    );
    check(
      !nodes(tree).some(
        (node) => typeof node.type === 'function' && node.type.name === 'Onboarding',
      ),
      kind + ': onboarding cannot hatch behind a failed save',
    );
    check(!text(tree).includes('load failure'), kind + ': no competing failure toast');
    const ui = controls();
    check(
      has(ui, 'START FRESH') === (kind === 'unreadable'),
      kind + ': only unreadable data can request recovery',
    );
    check(has(ui, 'TRY LOADING AGAIN'), kind + ': retry remains available');
    button(ui, 'TRY LOADING AGAIN').props.onPress();
    check(calls.pop() === 'retry', kind + ': retry delegates without confirming');
    back();
    check(calls.length === 0, kind + ': Back cannot leave recovery or start fresh');
  }
  state.saveLoadProblem = unreadableSaveProblem();
  button(controls(), 'START FRESH').props.onPress();
  check(calls.join('|') === 'request', 'start fresh only requests a confirmation');
  let ui = controls();
  check(
    text(ui).includes('Your old save will be kept on this device. Start a new garden?'),
    'confirmation explains that the original is kept',
  );
  check(
    has(ui, 'YES, START FRESH') && has(ui, 'CANCEL') && !has(ui, 'START FRESH'),
    'explicit confirmation replaces the initial action',
  );
  button(ui, 'CANCEL').props.onPress();
  check(
    calls.at(-1) === 'cancel' && has(controls(), 'START FRESH'),
    'Cancel restores recovery without confirming',
  );
  state.saveLoadProblem = { ...unreadableSaveProblem(), confirmationId: 'new' };
  ui = controls();
  state.saveLoadProblem = { ...state.saveLoadProblem, confirmationId: 'latest' };
  button(ui, 'YES, START FRESH').props.onPress();
  check(
    calls.at(-1) === 'confirm:latest',
    'a stale rendered confirmation reads the live store token',
  );
  state.saveLoadProblem = { ...state.saveLoadProblem, busy: true, confirmationId: null };
  ui = controls();
  check(
    has(ui, 'STARTING FRESH...') && !has(ui, 'START FRESH'),
    'pending backup keeps the confirmation visible',
  );
  check(
    button(ui, 'STARTING FRESH...').props.disabled && button(ui, 'CANCEL').props.disabled,
    'pending backup disables both confirmation controls',
  );
  const count = calls.length;
  button(ui, 'STARTING FRESH...').props.onPress();
  button(ui, 'CANCEL').props.onPress();
  back();
  check(calls.length === count, 'even stale handlers cannot cancel or resubmit a busy recovery');
  state.saveLoadProblem = { ...unreadableSaveProblem(), error: 'Backup write failed' };
  ui = controls();
  check(text(byType(ui, 'View')).includes('Backup write failed'), 'backup failure remains visible');
  check(
    nodes(ui).some((node) => node.props?.accessibilityRole === 'alert'),
    'backup failure is announced as an alert',
  );
  calls.length = 0;
  state.saveLoadProblem = { ...unreadableSaveProblem(), confirmationId: 'escape' };
  back();
  check(
    calls.join('|') === 'cancel' && state.saveLoadProblem.confirmationId === null,
    'Back only cancels the explicit confirmation',
  );
  for (const layer of [
    { player: { mode: 'mission', mission_id: 'book', mission_ends_at: 30000 } },
    { player: { mode: 'awake' }, cardReward: { mission: 'book' } },
    { player: { mode: 'awake' }, battle: { target: { id: 'test' } } },
  ]) {
    Object.assign(state, { player: null, cardReward: null, battle: null }, layer);
    check(
      nodes(render()).some((node) => node.type === recovery.SaveRecovery),
      'a save problem overrides other game layers',
    );
  }
  state.ready = false;
  check(
    !nodes(render()).some((node) => node.type === recovery.SaveRecovery),
    'initial loading retains priority over a not-yet-ready recovery',
  );
  runtime.unmount();
  recoveryRuntime.unmount();
}

async function main() {
  visitorAndReturnChecks();
  napReturnControls();
  saveRecoveryControls();
  journeyChecks();
  const home = homeFixture();
  let tree = home.render();
  check(!byType(tree, 'GardenWorld').props.active, 'unfocused Home is inactive');
  check(home.control.ambience === null, 'unfocused Home asks for no ambience');
  check(
    !byType(tree, 'GardenVisitor').props.active,
    'unfocused Home pauses the visiting companion',
  );
  check(home.seen.length === 0, 'unfocused Home does not consume guidance');
  home.state.firstWake = true;
  tree = home.render();
  check(home.seen.length === 0, 'a wake on another tab does not consume the wake tip');
  home.control.focused = true;
  home.control.foreground = false;
  tree = home.render();
  check(home.seen.length === 0, 'background Home does not consume guidance');
  check(home.control.ambience === null, 'a backgrounded app stops the garden ambience');
  home.control.foreground = true;
  tree = home.render();
  check(byType(tree, 'GardenWorld').props.active, 'visible uncovered Home activates the garden');
  check(home.control.ambience === 'day', 'the visible garden plays daytime ambience at noon');
  check(byType(tree, 'GardenVisitor').props.active, 'visible uncovered Home activates its visitor');
  check(
    home.seen.length === 1 && home.seen[0] === 'wake',
    'wake guidance is consumed only when visible',
  );
  // Any game sheet (nap, menu, planner, stats...) covers Home and pauses it.
  for (const sheet of ['rhythm', 'stats', 'nap', 'menu']) {
    home.ui.sheet = sheet;
    tree = home.render();
    check(!byType(tree, 'GardenWorld').props.active, `the ${sheet} sheet pauses garden work`);
    check(!byType(tree, 'GardenVisitor').props.active, `the ${sheet} sheet pauses the visitor`);
    check(home.clock.intervals.size === 0, `the ${sheet} sheet pauses idle chatter`);
    check(home.control.ambience === null, `the ${sheet} sheet quiets the garden ambience`);
    home.ui.sheet = null;
    tree = home.render();
    check(
      byType(tree, 'GardenWorld').props.active,
      `closing the ${sheet} sheet resumes the garden`,
    );
  }
  check(
    byType(tree, 'GardenWorld').props.viewportHeight === 800,
    'the garden fills the whole screen height',
  );
  check(byType(tree, 'GardenWorld').props.marker === 'missions', 'the garden shows its next place');
  byType(tree, 'GardenWorld').props.onNap();
  check(home.ui.sheet === 'nap', 'the garden bed opens the same nap sheet as the hotbar');
  home.ui.sheet = null;
  home.control.focused = false;
  tree = home.render();
  check(!byType(tree, 'GardenWorld').props.active, 'tab blur pauses the garden');
  check(home.control.ambience === null, 'tab blur stops the garden ambience');
  home.control.focused = true;
  tree = home.render();
  check(byType(tree, 'GardenWorld').props.active, 'returning Home reactivates its quiet garden');
  check(home.control.ambience === 'day', 'returning Home resumes the ambience');
  home.state.now = new Date(2026, 9, 16, 22).getTime();
  tree = home.render();
  check(
    home.control.ambience === 'night',
    'after nine in the evening the garden plays night sounds',
  );
  home.state.now = new Date(2026, 9, 16, 12).getTime();
  tree = home.render();
  home.runtime.unmount();
  check(home.clock.intervals.size === 0 && home.clock.timeouts.size === 0, 'Home timers clean up');

  // The nap sheet holds the optional break idea and starts the ordinary nap.
  const departure = napSheetFixture();
  tree = departure.render();
  check(
    byType(tree, 'BreakIntentionPicker').props.value === null,
    'a nap starts as just a break, with no decision required',
  );
  byType(tree, 'BreakIntentionPicker').props.onChange('read');
  tree = departure.render();
  check(
    byType(tree, 'BreakIntentionPicker').props.value === 'read',
    'the nap sheet holds its optional reading idea',
  );
  find(
    tree,
    (node) => node.type === 'PixelButton' && node.props.label === 'START NAP',
  ).props.onPress();
  check(
    departure.naps.length === 1 &&
      departure.naps[0].mission === undefined &&
      departure.naps[0].intention === 'read',
    'START NAP forwards the chosen idea to the existing ordinary nap',
  );
  check(departure.ui.sheet === null, 'starting a nap closes the sheet');
  departure.state.player = { ...departure.state.player, mode: 'awake' };
  departure.ui.sheet = 'nap';
  tree = departure.render();
  check(
    byType(tree, 'BreakIntentionPicker').props.value === null,
    'the next break begins with just a break again',
  );
  byType(tree, 'BreakIntentionPicker').props.onChange('move');
  departure.ui.sheet = null;
  departure.render();
  departure.ui.sheet = 'nap';
  tree = departure.render();
  check(
    byType(tree, 'BreakIntentionPicker').props.value === null,
    'closing the sheet clears an unfinished break choice',
  );
  find(
    tree,
    (node) => node.type === 'PixelButton' && node.props.label === 'START NAP',
  ).props.onPress();
  check(departure.naps[1].intention === null, 'a quick nap keeps the no-idea default');
  departure.runtime.unmount();

  let instant = new Date(2026, 9, 16, 16, 59).getTime();
  class ClockDate extends Date {
    static now() {
      return instant;
    }
  }
  const rules = load(
    'lib/daily-rhythm.ts',
    (id) => {
      throw new Error(id);
    },
    { Date: ClockDate },
  );
  const plan = { ...rules.freshRhythm(), enabled: true };

  async function plannerFixture(raw) {
    const runtime = hooks();
    const clock = timers();
    const changes = [];
    const props = {
      active: true,
      open: false,
      onOpenChange(open) {
        changes.push(open);
        props.open = open;
      },
    };
    const Card = load(
      'components/daily-rhythm.tsx',
      (id) => {
        if (id === 'react') return runtime.react;
        if (id === 'react/jsx-runtime') return jsxRuntime;
        if (id === 'react-native')
          return {
            StyleSheet: { create: (styles) => styles },
            Platform: { OS: 'web' },
            ...Object.fromEntries(['View', 'Pressable'].map((name) => [name, name])),
          };
        if (id === '@react-native-async-storage/async-storage')
          return { __esModule: true, default: { getItem: async () => raw } };
        if (id === '@/lib/daily-rhythm') return rules;
        if (id === '@/lib/cozy') return { cozy: {} };
        if (id === '@/lib/layout') return { gameLayout: { gutter: 16, maxWidth: 640 } };
        if (
          id === 'react-native-safe-area-context' ||
          id === 'lucide-react-native' ||
          id.startsWith('@/components/')
        )
          return boundary;
        throw new Error('Unexpected planner import: ' + id);
      },
      { ...clock.globals, Date: ClockDate },
    ).DailyRhythmCard;
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
  check(
    text(tree).includes('Focus now'),
    'loaded planner shows the current focus window: ' + text(tree),
  );
  check(planner.clock.intervals.size === 1, 'visible enabled planner owns one clock');
  find(tree, (node) => node.props.accessibilityLabel === 'Edit your daily rhythm').props.onPress();
  tree = planner.render();
  check(
    planner.props.open && planner.clock.intervals.size === 0,
    'editing reports coverage and pauses the card clock',
  );
  find(
    tree,
    (node) => typeof node.type === 'function' && node.type.name === 'RhythmEditor',
  ).props.onClose();
  tree = planner.render();
  check(
    !planner.props.open && planner.clock.intervals.size === 1,
    'cancel closes the editor and resumes one clock',
  );
  planner.props.active = false;
  tree = planner.render();
  check(
    planner.clock.intervals.size === 0 && planner.clock.timeouts.size === 0,
    'inactive planner removes all clock work',
  );
  instant = new Date(2026, 9, 16, 17, 1).getTime();
  planner.props.active = true;
  tree = planner.render();
  planner.clock.flush(0);
  tree = planner.render();
  check(
    text(tree).includes('Own time now'),
    'foreground refresh crosses the window boundary without waiting thirty seconds',
  );
  check(planner.clock.intervals.size === 1, 'resume does not duplicate the planner clock');
  planner.runtime.unmount();
  check(
    planner.clock.intervals.size === 0 && planner.clock.timeouts.size === 0,
    'planner unmount clears clock work',
  );

  const broken = await plannerFixture('{invalid');
  tree = broken.render();
  check(
    text(tree).includes('Your saved planner could not load.'),
    'unreadable planner offers explicit recovery',
  );
  find(
    tree,
    (node) => node.type === 'PixelButton' && node.props.label === 'NEW PLAN',
  ).props.onPress();
  tree = broken.render();
  check(
    broken.changes.at(-1) === true && broken.props.open,
    'NEW PLAN reports the same parent coverage as normal editing',
  );
  const editor = find(
    tree,
    (node) => typeof node.type === 'function' && node.type.name === 'RhythmEditor',
  );
  editor.props.onSaved(rules.freshRhythm());
  tree = broken.render();
  check(
    broken.changes.at(-1) === false && !broken.props.open,
    'save closes the parent-controlled planner',
  );
  check(broken.clock.intervals.size === 0, 'disabled saved plan schedules no clock');
  broken.runtime.unmount();
  console.log(
    'PASS: ' +
      checks +
      ' actual Home, break preparation, visitor, return, journey and planner lifecycle assertions.',
  );
}
main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
