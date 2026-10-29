/**
 * Checks the actual shared garden-view preference through its exported hook.
 * Run: node scripts/check-garden-view.cjs
 *
 * useSyncExternalStore captures the real subscribe/snapshot functions, while
 * AsyncStorage uses explicitly deferred reads and writes. This checks shared
 * state, race handling and persistence order, not React scheduling, DOM/native
 * rendering, real device storage or visual hydration behavior.
 */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const ts = require('typescript');

const sourcePath = path.join(__dirname, '..', 'lib', 'garden-view.ts');
const source = ts.transpileModule(fs.readFileSync(sourcePath, 'utf8'), {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
}).outputText;
const key = 'napattack-garden-view';
let checks = 0;
const check = (condition, message) => {
  assert.ok(condition, message);
  checks++;
};
const settle = () => new Promise((resolve) => setImmediate(resolve));
function deferred() {
  let resolve;
  let reject;
  const promise = new Promise((resolvePromise, rejectPromise) => {
    resolve = resolvePromise;
    reject = rejectPromise;
  });
  return { promise, resolve, reject };
}

function fixture() {
  const read = deferred();
  const readKeys = [];
  const writeCalls = [];
  let persisted = null;
  let captured;
  const storage = {
    getItem(storageKey) {
      readKeys.push(storageKey);
      return read.promise;
    },
    setItem(storageKey, value) {
      const completion = deferred();
      writeCalls.push({ key: storageKey, value, completion });
      return completion.promise.then(() => {
        persisted = value;
      });
    },
  };
  const moduleFixture = { exports: {} };
  vm.runInNewContext(
    source,
    {
      module: moduleFixture,
      exports: moduleFixture.exports,
      require(id) {
        if (id === 'react')
          return {
            useSyncExternalStore(subscribe, snapshot, serverSnapshot) {
              captured = { subscribe, snapshot, serverSnapshot };
              return snapshot();
            },
          };
        if (id === '@react-native-async-storage/async-storage')
          return { __esModule: true, default: storage };
        throw new Error(`Unexpected import: ${id}`);
      },
    },
    { filename: sourcePath },
  );
  return {
    read,
    readKeys,
    writeCalls,
    persisted: () => persisted,
    consumer() {
      const [initial, choose] = moduleFixture.exports.useGardenView();
      return { initial, choose, ...captured };
    },
  };
}

async function sharedConsumers() {
  const shared = fixture();
  const home = shared.consumer();
  const nap = shared.consumer();
  check(
    home.initial === 'flat' && nap.initial === 'flat',
    'consumers begin with the same flat snapshot',
  );
  check(shared.readKeys.length === 0, 'rendering the hook does not start storage hydration');
  check(home.choose === nap.choose, 'all consumers share the same choose function');
  const homeStates = [];
  const napStates = [];
  const stopHome = home.subscribe(() => homeStates.push(home.snapshot()));
  const stopNap = nap.subscribe(() => napStates.push(nap.snapshot()));
  check(
    shared.readKeys.length === 1 && shared.readKeys[0] === key,
    'subscriptions share one lazy storage read',
  );
  shared.read.resolve('tilt');
  await settle();
  check(
    home.snapshot() === 'tilt' && nap.snapshot() === 'tilt',
    'saved tilt hydrates every consumer',
  );
  check(
    homeStates.join() === 'tilt' && napStates.join() === 'tilt',
    'hydration notifies each active consumer once',
  );
  const later = shared.consumer();
  check(
    later.initial === 'tilt',
    'a later nap consumer immediately sees the shared loaded preference',
  );
  check(later.serverSnapshot() === 'flat', 'server snapshot remains flat after tilt hydration');
  home.choose('flat');
  check(
    home.snapshot() === 'flat' && nap.snapshot() === 'flat',
    'manual choice changes shared snapshots synchronously',
  );
  const notificationCount = homeStates.length;
  home.choose('flat');
  check(
    homeStates.length === notificationCount,
    'choosing the same value does not emit a redundant update',
  );
  stopNap();
  home.choose('tilt');
  check(
    homeStates.at(-1) === 'tilt' && napStates.at(-1) === 'flat',
    'unsubscribed consumer stops receiving preference notifications',
  );
  stopHome();
  const stoppedCount = homeStates.length;
  home.choose('flat');
  check(
    homeStates.length === stoppedCount,
    'no listeners receive updates after all consumers unsubscribe',
  );
  const returning = shared.consumer();
  const stopReturning = returning.subscribe(() => {});
  check(
    returning.initial === 'flat' && shared.readKeys.length === 1,
    'resubscribing preserves shared memory without rehydrating stale storage',
  );
  stopReturning();
}

async function hydrationRaces() {
  for (const [manual, stored] of [
    ['tilt', 'flat'],
    ['flat', 'tilt'],
  ]) {
    const race = fixture();
    const consumer = race.consumer();
    const states = [];
    const stop = consumer.subscribe(() => states.push(consumer.snapshot()));
    consumer.choose(manual);
    check(
      consumer.snapshot() === manual,
      `${manual}: manual choice is immediate while hydration is pending`,
    );
    race.read.resolve(stored);
    await settle();
    check(
      consumer.snapshot() === manual,
      `${manual}: late conflicting hydration cannot overwrite a manual choice`,
    );
    check(
      states.length === (manual === 'flat' ? 0 : 1),
      `${manual}: ignored hydration emits no extra notification`,
    );
    check(
      race.writeCalls.length === 1 && race.writeCalls[0].value === manual,
      `${manual}: even an unchanged explicit choice is persisted`,
    );
    check(
      consumer.serverSnapshot() === 'flat',
      `${manual}: manual choice never changes the server snapshot`,
    );
    race.writeCalls[0].completion.resolve();
    await settle();
    stop();
  }
}

async function unknownStoredValues() {
  for (const stored of [null, '', '2.5D', 'TILT', '"tilt"', 'flat']) {
    const unknown = fixture();
    const consumer = unknown.consumer();
    let notifications = 0;
    const stop = consumer.subscribe(() => {
      notifications++;
    });
    unknown.read.resolve(stored);
    await settle();
    check(
      consumer.snapshot() === 'flat',
      `${String(stored)}: unsupported or flat stored value preserves the flat default`,
    );
    check(
      notifications === 0 && unknown.writeCalls.length === 0,
      `${String(stored)}: ignored hydration neither emits nor rewrites storage`,
    );
    stop();
  }
}

async function storageFailures() {
  const failure = fixture();
  const consumer = failure.consumer();
  const states = [];
  const stop = consumer.subscribe(() => states.push(consumer.snapshot()));
  failure.read.reject(new Error('Test-only unavailable storage'));
  await settle();
  check(
    consumer.snapshot() === 'flat' && states.length === 0,
    'read failure leaves a stable flat preference',
  );
  consumer.choose('tilt');
  await settle();
  check(
    consumer.snapshot() === 'tilt' && failure.writeCalls.length === 1,
    'manual preference remains usable after read failure',
  );
  failure.writeCalls[0].completion.reject(new Error('Test-only failed write'));
  await settle();
  check(
    consumer.snapshot() === 'tilt' && states.join() === 'tilt',
    'failed persistence does not revert the visible preference or emit extra updates',
  );
  consumer.choose('flat');
  await settle();
  check(
    failure.writeCalls.length === 2 && failure.writeCalls[1].value === 'flat',
    'a failed write does not block the next explicit choice',
  );
  failure.writeCalls[1].completion.resolve();
  await settle();
  check(failure.persisted() === 'flat', 'the next successful choice persists normally');
  const another = failure.consumer();
  const stopAnother = another.subscribe(() => {});
  check(
    failure.readKeys.length === 1 && failure.writeCalls.length === 2,
    'new consumer does not automatically retry failed storage operations',
  );
  stop();
  stopAnother();
}

async function orderedWrites() {
  const ordered = fixture();
  const consumer = ordered.consumer();
  const stop = consumer.subscribe(() => {});
  ordered.read.resolve('flat');
  await settle();
  consumer.choose('tilt');
  consumer.choose('flat');
  consumer.choose('tilt');
  check(consumer.snapshot() === 'tilt', 'rapid choices immediately expose the latest preference');
  await settle();
  check(
    ordered.writeCalls.length === 1 && ordered.writeCalls[0].value === 'tilt',
    'only the first queued write starts while storage is deferred',
  );
  ordered.writeCalls[0].completion.resolve();
  await settle();
  check(
    ordered.persisted() === 'tilt' &&
      ordered.writeCalls.length === 2 &&
      ordered.writeCalls[1].value === 'flat',
    'second write starts only after the first settles',
  );
  ordered.writeCalls[1].completion.resolve();
  await settle();
  check(
    ordered.persisted() === 'flat' &&
      ordered.writeCalls.length === 3 &&
      ordered.writeCalls[2].value === 'tilt',
    'third write starts only after the second settles',
  );
  ordered.writeCalls[2].completion.resolve();
  await settle();
  check(
    ordered.persisted() === consumer.snapshot(),
    'final persisted preference agrees with the latest rapid choice',
  );
  check(
    ordered.writeCalls.every((write) => write.key === key),
    'every queued write uses the shared preference storage key',
  );
  stop();
}

const allNodes = (tree) => {
  if (tree === null || tree === undefined || typeof tree === 'boolean') return [];
  if (Array.isArray(tree)) return tree.flatMap(allNodes);
  if (typeof tree !== 'object') return [tree];
  return [tree, ...allNodes(tree.props?.children)];
};
const findNode = (tree, predicate) => {
  const found = allNodes(tree).find((node) => typeof node === 'object' && predicate(node));
  assert.ok(found, 'expected nap presentation node');
  return found;
};
const hasType = (tree, type) =>
  allNodes(tree).some((node) => typeof node === 'object' && node.type === type);
const visibleText = (tree) =>
  allNodes(tree)
    .filter((node) => typeof node === 'string' || typeof node === 'number')
    .join(' ')
    .replace(/\s+/g, ' ')
    .trim();
const jsx = (type, props) => ({ type, props: props || {} });

// Execute ScreenOff itself with React and native components replaced only at
// their boundaries. Scene absence proves unmount intent, not real timer cleanup,
// React scheduling, native lifecycle or screen-lock/phone-usage behaviour.
function quietNapPresentation() {
  const overlayPath = path.join(__dirname, '..', 'components', 'game-overlays.tsx');
  const overlaySource = ts.transpileModule(
    fs.readFileSync(overlayPath, 'utf8') + '\nexports.TestScreenOff = ScreenOff;\n',
    {
      compilerOptions: {
        module: ts.ModuleKind.CommonJS,
        target: ts.ScriptTarget.ES2022,
        jsx: ts.JsxEmit.ReactJSX,
        esModuleInterop: true,
      },
    },
  ).outputText;
  // components are their names; the window is a 402 x 874 phone (the nap screen sizes its
  // window from the screen's height)
  const boundary = new Proxy(
    {},
    {
      get: (_, name) =>
        name === 'useWindowDimensions' ? () => ({ width: 402, height: 874 }) : name,
    },
  );
  // The real shared Space handler for role="switch" controls, on the web.
  const switchKeysModule = { exports: {} };
  vm.runInNewContext(
    ts.transpileModule(
      fs.readFileSync(path.join(__dirname, '..', 'lib', 'switch-keys.ts'), 'utf8'),
      { compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 } },
    ).outputText,
    {
      module: switchKeysModule,
      exports: switchKeysModule.exports,
      require: () => ({ Platform: { OS: 'web' } }),
    },
  );
  const missionFixtures = [
    { id: 'park', name: 'PARK PATROL', duration: 15, reward: 20 },
    { id: 'book', name: 'BOOK CLUB', duration: 30, reward: 60 },
    { id: 'mountain', name: 'MOUNTAIN RETREAT', duration: 60, reward: 150 },
  ];
  for (const mission of [null, ...missionFixtures]) {
    for (const together of [false, true]) {
      const label = (mission?.id ?? 'untimed') + (together ? '/together' : '/solo');
      let hookIndex = 0;
      const slots = [];
      let wakes = 0;
      let writes = 0;
      let quietWrites = 0;
      let confirmEarlyReturn = false;
      const player = {
        id: 'garden-test',
        pet_name: 'MOSS',
        species: 'BLOB',
        guardian: 'inkling',
        level: 2,
        mode: mission ? 'mission' : 'screen_off',
        mission_id: mission?.id ?? null,
        mission_ends_at: 1000 + (mission?.duration ?? 0) * 1000,
        offline_seconds: 35,
        grass: 140,
      };
      const keptMemory = Object.freeze({ id: 'read-memory', intention: 'read' });
      const state = {
        player,
        quietView: false,
        now: 1000,
        offStart: 30,
        offGrass: 135,
        activeBreakContext: { intention: 'read' },
        companionMemories: Object.freeze([keptMemory]),
        togetherId: together ? 'shared-nap' : null,
        sessions: together
          ? [
              {
                id: 'shared-nap',
                player_a: player.id,
                player_b: 'friend',
                status: 'active',
                started_at: new Date(0).toISOString(),
              },
            ]
          : [],
        rivals: together ? [{ ...player, id: 'friend', pet_name: 'BUD', guardian: null }] : [],
        message: null,
      };
      const useGame = (selector) => selector(state);
      useGame.getState = () => state;
      useGame.setState = () => {
        writes++;
      };
      const gameStore = {
        getState: () => ({
          ...state,
          wake: () => {
            wakes++;
          },
          setQuietView: (value) => {
            quietWrites++;
            state.quietView = value;
          },
        }),
      };
      const moduleFixture = { exports: {} };
      vm.runInNewContext(
        overlaySource,
        {
          module: moduleFixture,
          exports: moduleFixture.exports,
          require(id) {
            if (id === 'react')
              return {
                useState(initial) {
                  const at = hookIndex++;
                  if (!slots[at])
                    slots[at] = { value: typeof initial === 'function' ? initial() : initial };
                  return [
                    slots[at].value,
                    (update) => {
                      slots[at].value =
                        typeof update === 'function' ? update(slots[at].value) : update;
                    },
                  ];
                },
                useEffect() {
                  throw new Error('ScreenOff must not own effect clocks');
                },
                useRef(initial) {
                  return { current: initial };
                },
              };
            if (id === 'react/jsx-runtime') return { jsx, jsxs: jsx, Fragment: 'Fragment' };
            if (id === 'react-native') return boundary;
            if (id === 'react-native-reanimated')
              return { __esModule: true, default: boundary, FadeIn: boundary };
            if (id === '@/lib/cozy') return { cozy: {} };
            if (id === '@/lib/game')
              return {
                useGame,
                gameStore,
                missions: missionFixtures,
                clock: (seconds) =>
                  Math.floor(seconds / 60) + ':' + String(seconds % 60).padStart(2, '0'),
              };
            if (id === '@/lib/visitors')
              return {
                guardianPlayer: (value) =>
                  value.guardian === 'inkling'
                    ? { ...value, pet_name: 'INKLING', species: 'CUBE' }
                    : value,
              };
            if (id === '@/lib/garden-view')
              return {
                useGardenView: () => [
                  'tilt',
                  () => {
                    writes++;
                  },
                ],
              };
            if (id === '@/lib/companion-memories')
              return { breakIntentionLabel: () => 'A few pages' };
            if (id === '@/lib/switch-keys') return switchKeysModule.exports;
            if (
              id.startsWith('@/components/') ||
              id.startsWith('@/lib/') ||
              id === 'lucide-react-native' ||
              id === 'expo-haptics' ||
              id === 'react-native-safe-area-context'
            )
              return boundary;
            throw new Error('Unexpected nap presentation import: ' + id);
          },
        },
        { filename: overlayPath },
      );
      const render = () => {
        hookIndex = 0;
        return moduleFixture.exports.TestScreenOff({
          confirmEarlyReturn,
          onRequestReturn: () => {
            if (mission) confirmEarlyReturn = true;
            else wakes++;
          },
          onKeepExploring: () => {
            confirmEarlyReturn = false;
          },
          onReturnEarly: () => {
            wakes++;
            confirmEarlyReturn = false;
          },
        });
      };
      const model = () => JSON.stringify({ ...state, quietView: undefined });
      const modelBefore = model();
      let tree = render();
      const measure = findNode(tree, (node) => typeof node.props?.onLayout === 'function');
      measure.props.onLayout({ nativeEvent: { layout: { width: 390 } } });
      tree = render();
      let quiet = findNode(tree, (node) => node.props?.accessibilityLabel === 'Quiet view');
      check(
        quiet.props.accessibilityRole === 'switch' &&
          quiet.props.accessibilityState.checked === false &&
          quiet.props['aria-checked'] === false &&
          quiet.props.style.minHeight >= 44 &&
          quiet.props.style.minWidth >= 44,
        label + ': quiet view begins off with switch semantics and a usable target',
      );
      check(
        hasType(tree, mission ? 'WorldScene' : 'GardenWorld') && hasType(tree, 'LightSweep'),
        label + ': the existing scenery remains visible by default',
      );
      if (!mission) {
        const garden = findNode(tree, (node) => node.type === 'GardenWorld');
        // The garden is top-down only now (2.5D was retired); the nap shows a
        // window onto the hut and bed rather than the whole tall map.
        check(
          garden.props.napping === true &&
            garden.props.view === undefined &&
            typeof garden.props.viewportHeight === 'number' &&
            garden.props.viewportHeight > 0 &&
            garden.props.memories === state.companionMemories,
          label + ': ordinary nap shows a window of the garden with saved memories',
        );
      }
      check(
        visibleText(tree).includes('INKLING is settling in. Put your phone down'),
        label + ': invitation uses the current companion',
      );
      check(!hasType(tree, 'Pulse'), label + ': earnings do not mount a pulsing effect');
      if (mission)
        check(
          visibleText(tree).includes(
            mission.duration + ' simulated MIN · ' + mission.duration + '-second demo',
          ) && visibleText(tree).includes('SHIELDED UNTIL RETURN'),
          label + ': real demo duration and automatic return limits are explicit',
        );
      else
        check(
          visibleText(tree).includes('Untimed nap') &&
            visibleText(tree).includes('1 real second = 1 simulated MIN'),
          label + ': ordinary nap remains untimed with the accelerated clock explained',
        );
      quiet.props.onPress();
      tree = render();
      quiet = findNode(tree, (node) => node.props?.accessibilityLabel === 'Quiet view');
      check(
        quiet.props.accessibilityState.checked === true && quiet.props['aria-checked'] === true,
        label + ': enabling quiet view updates both checked states',
      );
      check(
        ['GardenWorld', 'WorldScene', 'PixelScene', 'LightSweep', 'Pet', 'Pulse'].every(
          (type) => !hasType(tree, type),
        ),
        label + ': quiet view unmounts all decorative worlds, light effects and pets',
      );
      slots.length = 0;
      tree = render();
      findNode(tree, (node) => typeof node.props?.onLayout === 'function').props.onLayout({
        nativeEvent: { layout: { width: 390 } },
      });
      tree = render();
      check(
        findNode(tree, (node) => node.props?.accessibilityLabel === 'Quiet view').props
          .accessibilityState.checked === true &&
          !hasType(tree, mission ? 'WorldScene' : 'GardenWorld'),
        label + ': a new nap presentation reads the saved quiet preference instead of resetting it',
      );
      check(
        visibleText(tree).includes(
          mission ? 'SHIELDED UNTIL RETURN' : 'NAPPING · GARDEN SHIELDED',
        ) &&
          (mission
            ? allNodes(tree).some(
                (node) =>
                  typeof node === 'object' &&
                  node.props?.accessibilityLabel?.includes('remaining in this demo mission'),
              )
            : visibleText(tree).includes('NAPPED 5 SIMULATED MIN')),
        label + ': quiet view retains status and countdown or elapsed progress',
      );
      const info = findNode(
        tree,
        (node) => node.props?.accessibilityLabel === 'About the simulated nap timer',
      );
      info.props.onPress();
      tree = render();
      check(
        visibleText(tree).includes('Sleep and phone inactivity are not measured.') &&
          visibleText(tree).includes(
            mission ? 'stays shielded until you return' : 'This nap has no end timer.',
          ) &&
          findNode(tree, (node) => node.props?.accessibilityLabel === 'Close nap information')
            .props['aria-expanded'] === true,
        label + ': help remains accessible and honest in quiet view',
      );
      if (together)
        check(
          visibleText(tree).includes('TOUCH GRASS TOGETHER') &&
            visibleText(tree).includes('SHARED TIMER:'),
          label + ': quiet view retains shared session status',
        );
      check(
        quietWrites === 1 && writes === 0 && wakes === 0 && model() === modelBefore,
        label +
          ': presentation writes only the quiet preference, leaving game and memories unchanged',
      );
      quiet = findNode(tree, (node) => node.props?.accessibilityLabel === 'Quiet view');
      quiet.props.onPress();
      tree = render();
      check(
        hasType(tree, mission ? 'WorldScene' : 'GardenWorld') &&
          findNode(tree, (node) => node.props?.accessibilityLabel === 'Close nap information')
            .props['aria-expanded'] === true,
        label + ': restoring scenery retains the help state and current session',
      );
      findNode(
        tree,
        (node) => node.type === 'PixelButton' && node.props.label === 'WAKE UP',
      ).props.onPress();
      if (mission) {
        tree = render();
        check(
          wakes === 0 &&
            visibleText(tree).includes('RETURN EARLY?') &&
            visibleText(tree).includes('Cards already earned stay yours.') &&
            visibleText(tree).includes(mission.reward + ' Dream Dust'),
          label +
            ': wake first explains the completion rewards forfeited and preserves earned cards',
        );
        findNode(
          tree,
          (node) => node.type === 'PixelButton' && node.props.label === 'KEEP EXPLORING',
        ).props.onPress();
        tree = render();
        check(
          wakes === 0 && !visibleText(tree).includes('RETURN EARLY?'),
          label + ': keeping the mission cancels without waking',
        );
        findNode(
          tree,
          (node) => node.type === 'PixelButton' && node.props.label === 'WAKE UP',
        ).props.onPress();
        tree = render();
        findNode(
          tree,
          (node) => node.type === 'PixelButton' && node.props.label === 'RETURN EARLY',
        ).props.onPress();
      }
      check(
        wakes === 1 && writes === 0 && quietWrites === 2 && model() === modelBefore,
        label +
          ': deliberate return remains available once without changing progress in presentation',
      );
      // Keyboard: Space toggles the Quiet view switch once, without scrolling.
      tree = render();
      quiet = findNode(tree, (node) => node.props?.accessibilityLabel === 'Quiet view');
      const keyTarget = {};
      let prevented = 0;
      const space = (overrides = {}) =>
        quiet.props.onKeyDown({
          key: ' ',
          target: keyTarget,
          currentTarget: keyTarget,
          repeat: false,
          preventDefault: () => prevented++,
          ...overrides,
        });
      space();
      space({ repeat: true });
      space({ ctrlKey: true });
      check(
        quietWrites === 3 && prevented === 2 && state.quietView,
        label + ': Space toggles Quiet view once; held keys and shortcuts do nothing more',
      );
      tree = render();
      quiet = findNode(tree, (node) => node.props?.accessibilityLabel === 'Quiet view');
      quiet.props.onKeyDown({
        key: ' ',
        target: keyTarget,
        currentTarget: keyTarget,
        repeat: false,
        preventDefault: () => prevented++,
      });
      check(
        quietWrites === 4 && !state.quietView && writes === 0,
        label + ': Space restores the scenery and touches no game state',
      );
    }
  }
}

// Exercise the real PixelScene output and generated frame metadata. These
// checks inspect layout plans, not browser image decoding or visual quality.
function decorativeFramePresentation() {
  const load = (file, imports) => {
    const filename = path.join(__dirname, '..', file);
    const compiled = ts.transpileModule(fs.readFileSync(filename, 'utf8'), {
      compilerOptions: {
        module: ts.ModuleKind.CommonJS,
        target: ts.ScriptTarget.ES2022,
        jsx: ts.JsxEmit.ReactJSX,
        esModuleInterop: true,
      },
    }).outputText;
    const module = { exports: {} };
    vm.runInNewContext(
      compiled,
      {
        module,
        exports: module.exports,
        require: imports,
        setInterval() {
          throw new Error('Decorative frames must not own clocks');
        },
        setTimeout() {
          throw new Error('Decorative frames must not own clocks');
        },
      },
      { filename },
    );
    return module.exports;
  };
  const art = load('lib/scene-assets.ts', (id) => {
    assert.ok(id.startsWith('@/assets/scenes/') && id.endsWith('.png'));
    return id;
  });
  let bounds;
  const game = { now: new Date('2026-10-16T12:00:00Z').getTime() };
  const ui = load('components/pixel-scenes.tsx', (id) => {
    if (id === 'react')
      return {
        useEffect() {},
        useState(initial) {
          bounds ??= initial;
          return [
            bounds,
            (next) => {
              bounds = typeof next === 'function' ? next(bounds) : next;
            },
          ];
        },
      };
    if (id === 'react/jsx-runtime') return { jsx, jsxs: jsx };
    if (id === 'react-native')
      return {
        Image: 'Image',
        View: 'View',
        StyleSheet: { absoluteFill: {} },
      };
    if (id === 'react-native-svg') return { default: 'Svg', G: 'G', Rect: 'Rect' };
    // the battle field's entrance parallax (not rendered by these frame checks)
    if (id === 'react-native-reanimated')
      return {
        default: { View: 'Animated.View' },
        Easing: { out: (f) => f, cubic: (t) => t },
        useAnimatedStyle: (f) => f,
        useSharedValue: (value) => ({ value, set() {} }),
        withTiming: (value) => value,
      };
    if (id === '@/lib/motion') return { useReducedMotion: () => false };
    if (id === '@/lib/scene-art') return { propPixels: {}, sceneColors: { ink: '#2A2421' } };
    if (id === '@/lib/scene-assets') return art;
    if (id === '@/lib/game')
      return {
        useGame: (selector) => selector(game),
        status: () => ({ kind: 'awake' }),
      };
    if (id.startsWith('@/assets/battle/') && id.endsWith('.png')) return id;
    // a region ring's battle backdrop (journey art); these frame checks use the garden field
    if (id === '@/lib/journey-assets')
      return {
        JOURNEY: { width: 320, height: 240, rail: 160 },
        YARD_FEET: 84,
        journeyLayers: {},
        journeyYards: {},
      };
    throw new Error('Unexpected decorative frame import: ' + id);
  });
  const render = (props, width, height) => {
    bounds = undefined;
    let tree = ui.PixelScene({ ...props, height });
    tree.props.onLayout({ nativeEvent: { layout: { width, height } } });
    tree = ui.PixelScene({ ...props, height });
    return tree.props.children[0].props.children.props;
  };
  for (const [kind, width, height, landmarkTop, landmarkBottom] of [
    // native rows in the 2x frame (step 7c): the same landmarks as before
    ['town', 600, 160, 96, 172],
    ['town', 320, 160, 96, 172],
    ['market', 96, 80, 144, 216],
    ['trail', 600, 192, 212, 260],
    ['trail', 320, 192, 212, 260],
  ]) {
    const image = render({ kind }, width, height);
    const pixel = image.style.width / art.sceneFrame.width;
    const nativeTop = (image.style.height + image.style.bottom - height) / pixel;
    const nativeBottom = (image.style.height + image.style.bottom) / pixel;
    check(
      nativeTop <= landmarkTop && nativeBottom >= landmarkBottom,
      `${kind} ${width}x${height}: authored landmarks remain inside the scenery crop`,
    );
    check(
      Number.isInteger(pixel) &&
        image.style.height / art.sceneFrame.height === pixel &&
        Number.isInteger(image.style.left) &&
        Number.isInteger(image.style.bottom) &&
        image.style.width >= width,
      `${kind} ${width}x${height}: crop uses integer pixels and covers the banner width`,
    );
  }
  const companion = render({ kind: 'town', children: 'companion' }, 600, 160);
  check(companion.style.bottom === 0, 'companion frames retain the default ground anchor');
  // a 600 px banner shows the 432 px frame at 2x (it must cover the width)
  const groundAt600 = art.sceneFrame.ground * 2;
  for (const inset of [0, 24, groundAt600]) {
    const image = render({ kind: 'town', groundInset: inset }, 600, 160);
    check(
      image.style.bottom === inset - groundAt600,
      `explicit ground inset ${inset}: foot placement overrides decorative focus`,
    );
  }
  const sunrise = render({ kind: 'town', sunrise: true }, 600, 160);
  check(
    sunrise.source === art.sceneReturn && sunrise.style.bottom === 0,
    'sunrise return frame keeps its authored source and ground anchor',
  );
  const sky = render({ kind: 'town', skyOnly: true }, 600, 192);
  check(
    sky.source === art.sceneSkies.day && sky.style.top === 0 && sky.style.bottom === undefined,
    'sky-only scenery ignores landmark focus and retains its sky anchor',
  );
  const night = render({ kind: 'night' }, 600, 160);
  check(
    night.source === art.sceneNight && night.style.bottom === 0,
    'night frame keeps its authored source and ground anchor',
  );
}

async function main() {
  await sharedConsumers();
  await hydrationRaces();
  await unknownStoredValues();
  await storageFailures();
  await orderedWrites();
  quietNapPresentation();
  decorativeFramePresentation();
  console.log(
    `PASS: ${checks} actual garden-view shared-state, hydration, persistence-order, cleanup, quiet-nap and decorative-frame presentation assertions.`,
  );
}
main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
