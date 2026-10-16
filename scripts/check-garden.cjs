/**
 * Source-level GardenWorld regression harness.
 * Run: npm run check:garden
 * Direct use: node scripts/check-garden.cjs [appify-directory]
 *
 * Transpiles the actual GardenWorld, pathfinding, projection, map and companion
 * identity/life helpers. Keepsake artwork is a leaf component boundary. React hooks, timers,
 * native components, and Reanimated scheduling are boundary substitutes so the
 * assertions inspect emitted animation plans and queued arrival handlers.
 * This does not validate React scheduling, real Reanimated frames, browser
 * focus behavior, visual layout, or native device execution.
 * No app files, saved state, package files, or network services are changed.
 */
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const { createRequire } = require('node:module');

const appDir = path.resolve(process.argv[2] ?? path.join(__dirname, '..'));
const appRequire = createRequire(path.join(appDir, 'package.json'));
const ts = appRequire('typescript');
const compile = (file) =>
  ts.transpileModule(fs.readFileSync(path.join(appDir, file), 'utf8'), {
    compilerOptions: {
      module: ts.ModuleKind.CommonJS,
      jsx: ts.JsxEmit.ReactJSX,
      target: ts.ScriptTarget.ES2022,
    },
  }).outputText;

const mapModule = { exports: {} };
vm.runInNewContext(compile('lib/garden-map.ts'), {
  module: mapModule,
  exports: mapModule.exports,
});
const map = mapModule.exports;
let hooks,
  index,
  effects,
  timers,
  intervals,
  serial,
  shared,
  reduced,
  routes,
  sleeps,
  feeds,
  gameWrites,
  announcements,
  appActive,
  dirty;
let fakeNow = Date.UTC(2026, 9, 16, 14);
class QAClock extends Date {
  static now() {
    return fakeNow;
  }
}
const game = {
  player: {
    id: 'gardener',
    code: 'ABCD',
    name: 'GARDENER',
    pet_name: 'Fern',
    species: 'BLOB',
    level: 1,
    mode: 'awake',
    mood: 50,
    grass: 20,
    hat: null,
    owned_hats: [],
    care_until: 0,
    recovery_until: 0,
    mission_id: null,
    mission_ends_at: 0,
    offline_seconds: 0,
    last_seen: fakeNow,
    deck: ['stretch'],
    guardian: null,
    collection: [],
    postcards: [],
  },
  now: fakeNow,
  sleep() {
    sleeps++;
  },
};
const react = {
  useState(init) {
    const i = index++;
    hooks[i] ??= { value: typeof init === 'function' ? init() : init };
    return [
      hooks[i].value,
      (value) => {
        const next = typeof value === 'function' ? value(hooks[i].value) : value;
        if (!Object.is(next, hooks[i].value)) dirty = true;
        hooks[i].value = next;
      },
    ];
  },
  useRef(init) {
    const i = index++;
    return (hooks[i] ??= { current: init });
  },
  useEffect(fn, deps) {
    const i = index++;
    const old = hooks[i];
    if (!old || !deps || deps.some((value, k) => value !== old.deps?.[k])) {
      effects.push(() => {
        old?.cleanup?.();
        hooks[i] = { deps, cleanup: fn() };
      });
    }
  },
  useLayoutEffect(fn, deps) {
    react.useEffect(fn, deps);
  },
};
const anim = {
  useSharedValue(value) {
    const ref = react.useRef(null);
    if (!ref.current) {
      ref.current = {
        value,
        animation: null,
        get() {
          return this.value;
        },
        set(next) {
          if (typeof next === 'number') {
            this.value = next;
            this.animation = null;
          } else this.animation = next;
        },
      };
      shared.push(ref.current);
    }
    return ref.current;
  },
  useAnimatedStyle: (fn) => fn(),
  withTiming: (to, { duration }, callback) => ({ to, duration, callback }),
  withSequence: (...steps) => ({ steps }),
  cancelAnimation(value) {
    value.animation = null;
  },
  runOnJS: (fn) => fn,
  Easing: { linear: 'linear' },
};
const useGame = (select) => select(game);
useGame.getState = () => game;
useGame.setState = (patch) => {
  gameWrites.push(patch);
};
const jsxElement = (type, props, key) => ({ type, props, key });
const deps = {
  react,
  'react/jsx-runtime': { jsx: jsxElement, jsxs: jsxElement },
  'react-native': {
    Image: 'Image',
    Platform: { OS: 'web' },
    Pressable: 'Pressable',
    View: 'View',
    AccessibilityInfo: { announceForAccessibility: (text) => announcements.push(text) },
  },
  'react-native-reanimated': { ...anim, default: { View: 'Animated.View' } },
  'expo-router': { router: { push: (route) => routes.push(route) } },
  'expo-haptics': { selectionAsync: async () => {} },
  '@/lib/cozy': { cozy: {} },
  '@/lib/motion': { useReducedMotion: () => reduced },
  '@/lib/app-active': { useAppActive: () => appActive },
  '@/lib/game': { useGame, playPaused: () => false },
  '@/lib/garden-map': map,
  './garden-map': map,
  '@/components/guardian-pet': { GuardianPet: 'GuardianPet' },
  '@/components/garden-keepsakes': { GardenKeepsakeArt: 'GardenKeepsakeArt' },
  '@/components/game-ui': { FloatingZ: 'FloatingZ', Pet: 'Pet' },
  '@/components/pixel-feedback': { BodyText: 'BodyText' },
};
const mod = { exports: {} };
function evaluate(file, destination, extra = '') {
  vm.runInNewContext(compile(file) + extra, {
    module: destination,
    exports: destination.exports,
    require: (id) => {
      if (id.startsWith('@/assets/')) return { asset: id };
      if (!(id in deps)) throw new Error(`Unsubstituted import: ${id}`);
      return deps[id];
    },
    setTimeout: (fn, ms) => {
      const id = ++serial;
      timers.set(id, { fn, ms });
      return id;
    },
    clearTimeout: (id) => timers.delete(id),
    setInterval: (fn, ms) => {
      const id = ++serial;
      intervals.set(id, { fn, ms });
      return id;
    },
    clearInterval: (id) => intervals.delete(id),
    console,
    Date: QAClock,
    Math,
  });
}
const reactionsModule = { exports: {} };
for (const name of [
  'offline-rules',
  'visitors',
  'grasslings',
  'companion-profiles',
  'garden-life',
]) {
  const domainModule = { exports: {} };
  evaluate(`lib/${name}.ts`, domainModule);
  deps[`@/lib/${name}`] = domainModule.exports;
}
const pathModule = { exports: {} };
evaluate('lib/garden-path.ts', pathModule);
deps['@/lib/garden-path'] = pathModule.exports;
const projectionModule = { exports: {} };
evaluate('lib/garden-projection.ts', projectionModule);
deps['@/lib/garden-projection'] = projectionModule.exports;
const flatProjection = projectionModule.exports.makeProjection('flat', 384, map.GARDEN);
const flatPlace = (x, y, groundY = y) =>
  projectionModule.exports.lift(flatProjection, x, y, groundY);
evaluate('components/garden-reactions.tsx', reactionsModule);
deps['@/components/garden-reactions'] = reactionsModule.exports;
evaluate('components/garden-world.tsx', mod, '\nmodule.exports.Ambient = Ambient;');
mod.exports.findPath = pathModule.exports.findPath;

function render(napping = false, options = {}) {
  let tree;
  let attempts = 0;
  do {
    dirty = false;
    index = 0;
    effects = [];
    tree = mod.exports.GardenWorld({
      width: options.width ?? 384,
      player: game.player,
      grumpy: false,
      sleepy: false,
      napping,
      active: options.active ?? true,
      view: options.view ?? 'flat',
      memories: options.memories ?? [],
      onFeed: () => {
        feeds++;
      },
      onNap: options.onNap,
    });
    if (!dirty) effects.forEach((fn) => fn());
    if (++attempts > 5) throw new Error('Source render did not settle');
  } while (dirty);
  return tree;
}
function setup(napping = false, options = {}) {
  hooks = [];
  timers = new Map();
  intervals = new Map();
  serial = 0;
  shared = [];
  routes = [];
  sleeps = 0;
  feeds = 0;
  gameWrites = [];
  announcements = [];
  reduced = false;
  appActive = true;
  return render(napping, options);
}
function find(tree, label) {
  if (!tree || typeof tree !== 'object') return null;
  if (tree.props?.accessibilityLabel === label) return tree;
  for (const child of [tree.props?.children].flat(Infinity)) {
    const found = find(child, label);
    if (found) return found;
  }
  return null;
}
function actionElement(tree, action) {
  if (action === 'pond') return find(tree, 'Look into the pond');
  const actionObject = map.gardenObjects.find((object) => object.action === action);
  return allElements(tree).find(
    (element) => element.type === 'Pressable' && element.key === actionObject.id,
  );
}
const press = (tree, action) => actionElement(tree, action).props.onPress();
const end = (sequence) => sequence.steps.at(-1).callback;
const ms = (sequence) => sequence.steps.reduce((total, step) => total + step.duration, 0);
function complete(value, sequence) {
  sequence.steps.forEach((step) => {
    value.value = step.to;
    step.callback?.(true);
  });
}
let count = 0;
const check = (condition, label) => {
  assert.ok(condition, label);
  count++;
};
// Arrays from vm contexts have different prototypes; compare their plain data.
const same = (a, b) => JSON.stringify(a) === JSON.stringify(b);

let worldTree = setup();
press(worldTree, 'arena');
let horizontalSequence = shared[0].animation;
let verticalSequence = shared[1].animation;
check(ms(horizontalSequence) === ms(verticalSequence), 'full X/Y durations agree');
check(ms(verticalSequence) > 800, 'last Y leg retains travel duration');
check(routes.length === 0, 'no premature action');
end(verticalSequence)(false);
check(routes.length === 0, 'canceled completion is inert');
complete(shared[0], horizontalSequence);
complete(shared[1], verticalSequence);
end(verticalSequence)(true);
check(routes.length === 1, 'arrival runs action exactly once');
check(same([shared[0].value, shared[1].value], [98, 142]), 'both visual axes arrive');

worldTree = setup();
press(worldTree, 'mail');
const oldY = shared[1].animation;
shared[0].value = 40.9;
shared[1].value = 113.9;
press(worldTree, 'arena');
horizontalSequence = shared[0].animation;
verticalSequence = shared[1].animation;
const actualOrigin = { x: 40.9, y: 113.9 };
const plannedPath = mod.exports.findPath(actualOrigin, map.gardenHotspots.arena);
check(
  same(
    horizontalSequence.steps.map((step) => step.to),
    plannedPath.map((point) => point.x),
  ),
  'retarget X uses actual origin',
);
check(
  same(
    verticalSequence.steps.slice(0, -1).map((step) => step.to),
    plannedPath.map((point) => point.y),
  ),
  'retarget Y uses actual origin',
);
check(
  Math.abs(
    horizontalSequence.steps[0].duration -
      (Math.hypot(plannedPath[0].x - actualOrigin.x, plannedPath[0].y - actualOrigin.y) / 34) *
        1000,
  ) < 0.0001,
  'duration uses actual displayed origin',
);
end(oldY)(true);
check(routes.length === 0, 'stale queued completion ignored');
complete(shared[0], horizontalSequence);
complete(shared[1], verticalSequence);
check(routes.length === 1, 'replacement journey acts once');

worldTree = setup();
press(worldTree, 'shop');
verticalSequence = shared[1].animation;
hooks.forEach((hook) => hook?.cleanup?.());
end(verticalSequence)(true);
check(routes.length === 0, 'unmounted completion ignored');

worldTree = setup();
press(worldTree, 'arena');
verticalSequence = shared[1].animation;
reduced = true;
render();
// Snapshot entries because callbacks can mutate the timer map.
for (const [id, timer] of Array.from(timers)) {
  if (timer.ms === 0) {
    timers.delete(id);
    timer.fn();
  }
}
check(
  same([shared[0].value, shared[1].value], [98, 142]),
  'motion change stops travel at endpoint',
);
end(verticalSequence)(true);
check(routes.length === 1, 'motion change cannot duplicate arrival');

worldTree = setup(true);
check(worldTree.props.inert === true, 'nap subtree is inert');
check(worldTree.props['aria-hidden'] === true, 'nap subtree hidden from accessibility');
press(worldTree, 'arena');
check(shared[0].animation === null, 'nap objects cannot start travel');
check(routes.length === 0, 'nap objects cannot navigate');
const originalChecks = count;

// Tab blur must cancel work even though React keeps Home mounted.
worldTree = setup();
press(worldTree, 'arena');
verticalSequence = shared[1].animation;
shared[0].value = 97;
shared[1].value = 121;
const inactive = render(false, { active: false });
check(
  shared.every((value) => value.animation === null),
  'blur cancels both animation axes',
);
check(same([shared[0].value, shared[1].value], [97, 121]), 'blur preserves the displayed position');
end(verticalSequence)(true);
check(routes.length === 0, 'stale arrival after blur cannot navigate');
press(inactive, 'shop');
press(worldTree, 'arena');
check(
  routes.length === 0 && shared[0].animation === null,
  'inactive current and stale press handlers are no-ops',
);
check(intervals.size === 0 && timers.size === 0, 'blur clears ground/idle/readout clocks');
check(inactive.props.inert === true, 'inactive scenery cannot receive web keyboard input');
worldTree = render();
check(
  same([shared[0].value, shared[1].value], [97, 121]),
  'returning Home preserves the stopped position',
);
end(verticalSequence)(true);
check(routes.length === 0, 'canceled arrival remains invalid after refocus');

worldTree = setup();
press(worldTree, 'nap');
complete(shared[0], shared[0].animation);
complete(shared[1], shared[1].animation);
const pendingNap = [...timers].find(([, timer]) => timer.ms === 500);
check(Boolean(pendingNap), 'nap arrival schedules its existing half-second pause');
render(false, { active: false });
check(!timers.has(pendingNap[0]), 'blur clears a pending nap timer');
pendingNap[1].fn();
check(sleeps === 0, 'queued nap callback cannot sleep after blur');
render();
pendingNap[1].fn();
check(sleeps === 0, 'queued old nap callback remains invalid after refocus');

worldTree = setup(false, { active: false });
press(worldTree, 'shop');
check(
  shared[0].animation === null && routes.length === 0,
  'initially inactive garden rejects direct actions',
);
check(
  timers.size === 0 && intervals.size === 0,
  'initially inactive garden starts no world clocks',
);
// Ambient is a separate component with its own hook state, exercised independently.
hooks = [];
index = 0;
effects = [];
mod.exports.Ambient({
  scale: 2,
  place: flatPlace,
  width: 384,
  height: 352,
  rain: false,
  night: false,
  day: true,
  reduced: false,
  active: true,
});
effects.forEach((fn) => fn());
check(
  [...intervals.values()].some((timer) => timer.ms === 110),
  'active Ambient starts its own clock',
);
index = 0;
effects = [];
mod.exports.Ambient({
  scale: 2,
  place: flatPlace,
  width: 384,
  height: 352,
  rain: false,
  night: false,
  day: true,
  reduced: false,
  active: false,
});
effects.forEach((fn) => fn());
check(intervals.size === 0, 'inactive Ambient stops its own clock');
const activityChecks = count - originalChecks;

// Inspect actual JSX geometry, not a duplicate implementation of target layout.
function allElements(node) {
  if (!node || typeof node !== 'object') return [];
  return [node, ...[node.props?.children].flat(Infinity).flatMap(allElements)];
}
const geometryStart = count;
for (const viewMode of ['flat', 'tilt']) {
  for (const platform of ['web', 'ios']) {
    deps['react-native'].Platform.OS = platform;
    for (const width of [320, 390, 430, 640]) {
      worldTree = setup(false, { width, view: viewMode });
      const elements = allElements(worldTree);
      const height = worldTree.props.style.height;
      const scale = width / map.GARDEN.width;
      const expectedProjection = projectionModule.exports.makeProjection(
        viewMode,
        width,
        map.GARDEN,
        viewMode === 'tilt' ? Math.round(width * 0.14) : 0,
      );
      for (const object of map.gardenObjects.filter((gardenObject) => gardenObject.action)) {
        const target = elements.find(
          (element) => element.key === object.id && element.type === 'Pressable',
        );
        assert.ok(target, `${platform}/${width}: ${object.id} target exists`);
        const box = target.props.style;
        const art = elements.find(
          (element) => element.type === 'Image' && element.key === `${object.id}-image`,
        ).props.style;
        const split = ['read', 'water', 'lantern'].includes(object.action);
        const expectedArt = projectionModule.exports.billboard(
          expectedProjection,
          object.x,
          object.y,
          object.w,
          object.h,
        );
        check(
          box.width >= 44 && box.height >= 44,
          `${platform}/${width}/${object.id}: target is at least 44x44`,
        );
        check(
          box.left >= 0 &&
            box.top >= 0 &&
            box.left + box.width <= width &&
            box.top + box.height <= height,
          `${platform}/${width}/${object.id}: target stays in scene`,
        );
        check(
          (split ? art.left : box.left + art.left) ===
            Math.round(viewMode === 'flat' ? object.x * scale : expectedArt.left) &&
            (split ? art.top : box.top + art.top) ===
              Math.round(viewMode === 'flat' ? object.y * scale : expectedArt.top) &&
            art.width === Math.round(viewMode === 'flat' ? object.w * scale : expectedArt.width) &&
            art.height === Math.round(viewMode === 'flat' ? object.h * scale : expectedArt.height),
          `${viewMode}/${platform}/${width}/${object.id}: art follows its actual projection, preserving flat identity`,
        );
        if (split)
          check(
            box.zIndex > 158 &&
              elements.find((element) => element.key === `${object.id}-art`).props.pointerEvents ===
                'none',
            `${platform}/${width}/${object.id}: hit area is above guardian while art stays passive`,
          );
      }
      const pond = find(worldTree, 'Look into the pond').props.style;
      check(
        pond.width >= 44 &&
          pond.height >= 44 &&
          pond.left >= 0 &&
          pond.top >= 0 &&
          pond.left + pond.width <= width &&
          pond.top + pond.height <= height,
        `${viewMode}/${platform}/${width}/pond: target meets size and bounds`,
      );
    }
  }
}
const geometryChecks = count - geometryStart;

// Independent BFS over the actual generated map, using the same no-corner rule.
const rows = map.gardenWalk.length;
const cols = map.gardenWalk[0].length;
const walkable = (x, y) =>
  y >= 0 &&
  y < rows &&
  x >= 0 &&
  x < cols &&
  x * 4 + 2 >= 20 &&
  x * 4 + 2 <= 172 &&
  y * 4 + 2 >= 40 &&
  y * 4 + 2 <= 158 &&
  map.gardenWalk[y][x] === '.';
const cellKey = (x, y) => `${x},${y}`;
const queue = [[24, 28]]; // START(96,112) / 4px cells
const reached = new Set([cellKey(...queue[0])]);
for (let cursor = 0; cursor < queue.length; cursor++) {
  const [x, y] = queue[cursor];
  for (const [dx, dy] of [
    [1, 0],
    [-1, 0],
    [0, 1],
    [0, -1],
    [1, 1],
    [1, -1],
    [-1, 1],
    [-1, -1],
  ]) {
    const nx = x + dx;
    const ny = y + dy;
    const key = cellKey(nx, ny);
    if (
      !walkable(nx, ny) ||
      reached.has(key) ||
      (dx && dy && (!walkable(x + dx, y) || !walkable(x, y + dy)))
    )
      continue;
    reached.add(key);
    queue.push([nx, ny]);
  }
}
const reachabilityStart = count;
const walkableCount = map.gardenWalk.reduce(
  (total, row, y) => total + [...row].filter((_, x) => walkable(x, y)).length,
  0,
);
check(reached.size === walkableCount, 'all walkable cells remain one connected component');
for (const [action, spot] of Object.entries(map.gardenHotspots)) {
  check(
    reached.has(
      cellKey(Math.floor(spot.x / map.GARDEN.cell), Math.floor(spot.y / map.GARDEN.cell)),
    ),
    `${action}: actual hotspot remains reachable`,
  );
  const route = mod.exports.findPath({ x: 96, y: 112 }, spot);
  check(
    route.length > 0 &&
      route.every((point) => point.x >= 20 && point.x <= 172 && point.y >= 40 && point.y <= 158),
    `${action}: actual path uses safe actor cells`,
  );
}
for (const edge of [
  { x: 0, y: 0 },
  { x: 192, y: 0 },
  { x: 0, y: 176 },
  { x: 192, y: 176 },
]) {
  const route = mod.exports.findPath({ x: 96, y: 112 }, edge);
  check(
    route.length > 0 &&
      route.every((point) => point.x >= 20 && point.x <= 172 && point.y >= 40 && point.y <= 158),
    'edge click resolves to reachable safe actor endpoints',
  );
}
const reachabilityChecks = count - reachabilityStart;

// New interactions are cosmetic: execute actual handlers while spying on their
// game/native/navigation boundaries, without replacing any effect/action logic.
const cosmeticStart = count;
deps['react-native'].Platform.OS = 'web';
const reactionElement = (tree) =>
  allElements(tree).find((element) => element.type === reactionsModule.exports.GardenReactions);
const feedbackElement = (tree) =>
  allElements(tree).find((element) => element.props?.role === 'status');
const guardianElement = (tree) =>
  allElements(tree).find((element) => element.type === 'GuardianPet');
function finishTravel() {
  const horizontal = shared[0].animation;
  const vertical = shared[1].animation;
  if (horizontal) complete(shared[0], horizontal);
  if (vertical) complete(shared[1], vertical);
  return vertical;
}
function perform(tree, action) {
  press(tree, action);
  finishTravel();
  return render();
}
function noGameChange(before) {
  return (
    JSON.stringify(game.player) === before &&
    routes.length === 0 &&
    sleeps === 0 &&
    feeds === 0 &&
    gameWrites.length === 0
  );
}
for (const action of ['read', 'water', 'pond', 'lantern']) {
  worldTree = setup();
  const before = JSON.stringify(game.player);
  press(worldTree, action);
  worldTree = render();
  check(
    !reactionElement(worldTree) && !feedbackElement(worldTree),
    `${action}: effect waits for visual arrival`,
  );
  const completed = finishTravel();
  worldTree = render();
  const reaction = reactionElement(worldTree);
  const feedback = feedbackElement(worldTree);
  check(
    reaction?.props.reaction.kind === action && Boolean(feedback?.props.children),
    `${action}: arrival gives visible reaction and text`,
  );
  check(
    feedback.props['aria-live'] === 'polite',
    `${action}: successful feedback is a polite status`,
  );
  const id = reaction.props.reaction.id;
  end(completed)(true);
  worldTree = render();
  check(
    reactionElement(worldTree)?.props.reaction.id === id,
    `${action}: duplicate arrival cannot restart its effect`,
  );
  check(noGameChange(before), `${action}: no resource writes, routes, sleep or feed calls`);
  check(
    announcements.length === 0,
    `${action}: web feedback does not call native announcement API`,
  );
  const oldText = feedback.props.children;
  worldTree = perform(worldTree, action);
  if (action === 'lantern') {
    const target = actionElement(worldTree, action);
    check(
      target.props['aria-pressed'] === false && target.props.accessibilityLabel.includes('on'),
      'second lantern action turns light off and exposes matching state',
    );
    check(
      !reactionElement(worldTree) &&
        feedbackElement(worldTree)?.props.children.includes('lights out'),
      'lantern-off response has text without a false light effect',
    );
  } else {
    check(
      reactionElement(worldTree)?.props.reaction.id > id &&
        feedbackElement(worldTree)?.props.children !== oldText,
      `${action}: repeat intentionally replaces effect and rotates response`,
    );
  }
  check(noGameChange(before), `${action}: repeating never earns or spends resources`);
}

worldTree = setup();
press(worldTree, 'read');
const canceledRead = shared[1].animation;
press(worldTree, 'water');
end(canceledRead)(true);
worldTree = render();
check(
  !reactionElement(worldTree) && !feedbackElement(worldTree),
  'retargeted old read arrival cannot start any effect',
);
finishTravel();
worldTree = render();
check(
  reactionElement(worldTree)?.props.reaction.kind === 'water',
  'retargeted water arrival is the only response',
);
const oldReactionExpiry = [...timers.values()].find((timer) => timer.ms === 4600);
const oldFeedbackExpiry = [...timers.values()].find((timer) => timer.ms === 6500);
worldTree = perform(worldTree, 'read');
const replacementId = reactionElement(worldTree).props.reaction.id;
const replacementText = feedbackElement(worldTree).props.children;
oldReactionExpiry.fn();
oldFeedbackExpiry.fn();
worldTree = render();
check(
  reactionElement(worldTree)?.props.reaction.id === replacementId,
  'old reaction expiry cannot erase a newer response',
);
check(
  feedbackElement(worldTree)?.props.children === replacementText,
  'old status expiry cannot erase newer text',
);
const currentReactionExpiry = [...timers.values()].find((timer) => timer.ms === 4600);
const currentFeedbackExpiry = [...timers.values()].find((timer) => timer.ms === 6500);
currentReactionExpiry.fn();
worldTree = render();
check(
  !reactionElement(worldTree) && Boolean(feedbackElement(worldTree)),
  'reaction expires while readable text remains',
);
currentFeedbackExpiry.fn();
worldTree = render();
check(!feedbackElement(worldTree), 'current readable status expires normally');

worldTree = setup();
press(worldTree, 'shop');
const canceledShop = shared[1].animation;
guardianElement(worldTree).props.onPress();
worldTree = render();
end(canceledShop)(true);
check(
  reactionElement(worldTree)?.props.reaction.kind === 'pat' && routes.length === 0,
  'pat cancels a pending shop trip and responds immediately',
);
check(
  shared.every((value) => value.animation === null),
  'pat stops both movement axes',
);
check(noGameChange(JSON.stringify(game.player)), 'pat has no reward/resource side effects');
worldTree = setup();
press(worldTree, 'nap');
finishTravel();
const canceledNap = [...timers.values()].find((timer) => timer.ms === 500);
guardianElement(worldTree).props.onPress();
canceledNap.fn();
worldTree = render();
check(
  sleeps === 0 && reactionElement(worldTree)?.props.reaction.kind === 'pat',
  'pat also cancels a queued nap intent',
);

for (const action of ['read', 'water', 'pond', 'lantern']) {
  worldTree = setup();
  press(worldTree, action);
  const canceled = shared[1].animation;
  render(false, { active: false });
  end(canceled)(true);
  worldTree = render(false, { active: false });
  check(
    !reactionElement(worldTree) && !feedbackElement(worldTree),
    `${action}: blur blocks queued cosmetic arrival`,
  );
  worldTree = render();
  end(canceled)(true);
  worldTree = render();
  check(
    !reactionElement(worldTree) && !feedbackElement(worldTree),
    `${action}: refocus cannot resurrect canceled effect`,
  );
  worldTree = perform(worldTree, action);
  render(false, { active: false });
  worldTree = render();
  check(
    !reactionElement(worldTree) && !feedbackElement(worldTree),
    `${action}: blur clears a response already showing`,
  );
  worldTree = setup(true);
  press(worldTree, action);
  guardianElement(worldTree).props.onPress();
  check(
    shared[0].animation === null && routes.length === 0 && sleeps === 0,
    `${action}: decorative nap scenery rejects object/pat actions`,
  );
}

worldTree = setup();
press(worldTree, 'water');
const motionQueued = shared[1].animation;
reduced = true;
worldTree = render();
// Snapshot entries because callbacks can mutate the timer map.
for (const [id, timer] of Array.from(timers)) {
  if (timer.ms === 0) {
    timers.delete(id);
    timer.fn();
  }
}
worldTree = render();
check(
  reactionElement(worldTree)?.props.reduced === true &&
    reactionElement(worldTree)?.props.reaction.kind === 'water',
  'motion change during walk arrives with static successful response',
);
const staticId = reactionElement(worldTree).props.reaction.id;
end(motionQueued)(true);
worldTree = render();
check(
  reactionElement(worldTree)?.props.reaction.id === staticId,
  'motion change cannot duplicate cosmetic response',
);

deps['react-native'].Platform.OS = 'ios';
worldTree = setup();
worldTree = perform(worldTree, 'read');
check(
  announcements.length === 1 && announcements[0] === feedbackElement(worldTree).props.children,
  'native feedback announces successful response exactly once',
);
deps['react-native'].Platform.OS = 'web';
const cosmeticChecks = count - cosmeticStart;

// Execute the actual child effect component with independent hook boundaries.
const childStart = count;
function resetChild() {
  hooks = [];
  index = 0;
  effects = [];
  timers = new Map();
  intervals = new Map();
  serial = 0;
}
function renderReaction(reaction, reduce = false, projection = flatProjection) {
  index = 0;
  effects = [];
  const result = reactionsModule.exports.GardenReactions({
    reaction,
    scale: projection.scale,
    reduced: reduce,
    place: (x, y, groundY = y) => projectionModule.exports.lift(projection, x, y, groundY),
    signature: reaction.signature,
    actor: reaction.actor,
  });
  effects.forEach((fn) => fn());
  return result;
}
for (const kind of ['read', 'water', 'pond', 'pat', 'lantern']) {
  const reaction = { kind, id: 1, x: 96, y: 112 };
  resetChild();
  let child = renderReaction(reaction);
  check(
    child.props.pointerEvents === 'none' &&
      !allElements(child).some((element) => element.type === 'Pressable'),
    `${kind}: effect cannot intercept interaction`,
  );
  const tick = [...intervals.values()].find((timer) => timer.ms === 120);
  check(Boolean(tick), `${kind}: ordinary motion starts finite effect clock`);
  for (let frame = 0; frame < 32; frame++) {
    tick.fn();
    child = renderReaction(reaction);
  }
  check(intervals.size === 0, `${kind}: effect clock stops after32frames`);
  resetChild();
  child = renderReaction(reaction, true);
  check(
    intervals.size === 0 && allElements(child).length > 1,
    `${kind}: reduced motion has static visible result without a clock`,
  );
  const staticTree = JSON.stringify(child);
  check(
    JSON.stringify(renderReaction(reaction, true)) === staticTree,
    `${kind}: static feedback remains stable`,
  );
  resetChild();
  child = renderReaction(reaction);
  const oldTick = [...intervals.values()][0];
  oldTick.fn();
  const priorMotion = JSON.stringify(renderReaction(reaction));
  child = renderReaction(reaction, true);
  check(intervals.size === 0, `${kind}: enabling reduced motion stops existing effect clock`);
  const stoppedTree = JSON.stringify(child);
  oldTick.fn();
  check(
    JSON.stringify(renderReaction(reaction, true)) === stoppedTree,
    `${kind}: queued old frame cannot animate reduced result`,
  );
  check(
    JSON.stringify(renderReaction(reaction)) === priorMotion,
    `${kind}: paused clock cannot advance hidden phase and resumes monotonically`,
  );
}
const childChecks = count - childStart;
const groundStart = count;
deps['react-native'].Platform.OS = 'web';
worldTree = setup();
const groundAsset = (tree) =>
  allElements(tree).find(
    (element) =>
      element.type === 'Image' &&
      element.props.source?.asset?.startsWith('@/assets/garden/ground-'),
  ).props.source.asset;
const groundClock = [...intervals.values()].find((timer) => timer.ms === 400);
check(Boolean(groundClock), 'ground uses its single400msclock');
const frames = [groundAsset(worldTree)];
for (let i = 0; i < 4; i++) {
  groundClock.fn();
  worldTree = render();
  frames.push(groundAsset(worldTree));
}
check(
  new Set(frames.slice(0, 4)).size === 4 && frames[4] === frames[0],
  'ground cycles allfouractualassets thenreturns to first',
);
groundClock.fn();
render();
reduced = true;
worldTree = render();
check(
  groundAsset(worldTree) === frames[0] &&
    ![...intervals.values()].some((timer) => timer.ms === 400),
  'reduced motion immediately shows ground0 and clears ground clock',
);
const groundChecks = count - groundStart;
const coordinateStart = count;
const groundElement = (tree) =>
  find(tree, `Your garden. Tap to walk ${game.player.pet_name} around.`);
worldTree = setup();
groundElement(worldTree).props.onPress({ nativeEvent: { offsetX: 240, offsetY: 264 } });
const domExpected = mod.exports.findPath({ x: 96, y: 112 }, { x: 120, y: 132 });
check(
  same(
    shared[0].animation.steps.map((step) => step.to),
    domExpected.map((point) => point.x),
  ),
  'DOM offsetX is scaled into the actual horizontal path',
);
check(
  same(
    shared[1].animation.steps.slice(0, -1).map((step) => step.to),
    domExpected.map((point) => point.y),
  ),
  'DOM offsetY is scaled into the actual vertical path',
);
finishTravel();
check(
  routes.length === 0 && sleeps === 0 && feeds === 0 && gameWrites.length === 0,
  'DOM ground click only walks without a game action',
);
worldTree = setup();
groundElement(worldTree).props.onPress({
  nativeEvent: { locationX: 0, locationY: 0, offsetX: 240, offsetY: 264 },
});
const nativeExpected = mod.exports.findPath({ x: 96, y: 112 }, { x: 0, y: 0 });
check(
  same(
    shared[0].animation.steps.map((step) => step.to),
    nativeExpected.map((point) => point.x),
  ),
  'finite zero-valued native coordinates take precedence over DOM offsets',
);

const invalidCoordinates = [
  { locationX: NaN, locationY: 1 },
  { offsetX: Infinity, offsetY: 4 },
  { locationX: 4, locationY: -Infinity },
  { offsetX: 2 },
  { offsetY: 2 },
  {},
  { locationX: '2', locationY: 2 },
  { locationX: 2, locationY: '2' },
];
for (const [caseIndex, nativeEvent] of invalidCoordinates.entries()) {
  worldTree = setup();
  press(worldTree, 'shop');
  const pendingX = shared[0].animation;
  const pendingY = shared[1].animation;
  const before = JSON.stringify(game.player);
  groundElement(worldTree).props.onPress({ nativeEvent });
  check(
    shared[0].animation === pendingX && shared[1].animation === pendingY,
    `invalid coordinate case${caseIndex}: leaves pending journey unchanged`,
  );
  check(
    noGameChange(before),
    `invalid coordinate case${caseIndex}: causes no action or resource write`,
  );
  finishTravel();
  check(
    routes.length === 1 && routes[0] === '/shop',
    `invalid coordinate case${caseIndex}: preserves the original once-only arrival`,
  );
}
worldTree = setup();
worldTree = perform(worldTree, 'read');
const preservedReaction = reactionElement(worldTree).props.reaction.id;
const preservedFeedback = feedbackElement(worldTree).props.children;
groundElement(worldTree).props.onPress({ nativeEvent: {} });
worldTree = render();
check(
  reactionElement(worldTree)?.props.reaction.id === preservedReaction &&
    feedbackElement(worldTree)?.props.children === preservedFeedback,
  'missing ground coordinates do not clear existing reaction or feedback',
);
for (const [from, to] of [
  [
    { x: NaN, y: 112 },
    { x: 120, y: 132 },
  ],
  [
    { x: 96, y: 112 },
    { x: Infinity, y: 132 },
  ],
  [
    { x: 96, y: -Infinity },
    { x: 120, y: 132 },
  ],
])
  check(mod.exports.findPath(from, to).length === 0, 'nonfinite path endpoints return no route');

// The tilt tap surface begins at the horizon. Feed actual projected coordinates
// through both event formats, then compare the emitted route with the real path
// module's route to that native point. This catches a missing/double horizon offset.
for (const viewportWidth of [320, 390, 430, 640]) {
  const tiltProjection = projectionModule.exports.makeProjection(
    'tilt',
    viewportWidth,
    map.GARDEN,
    Math.round(viewportWidth * 0.14),
  );
  for (const coordinateKind of ['offset', 'location']) {
    // Use a cell centre: an exact grid boundary is ambiguous after floating-point
    // project/unproject round trips and can select either neighbouring cell.
    const nativePoint = { x: 122, y: 134 };
    const projectedPoint = projectionModule.exports.project(
      tiltProjection,
      nativePoint.x,
      nativePoint.y,
    );
    worldTree = setup(false, { width: viewportWidth, view: 'tilt' });
    const tap = groundElement(worldTree);
    check(
      Math.abs(tap.props.style.top - tiltProjection.horizon) < 1e-8,
      `${viewportWidth}/${coordinateKind}: tap surface begins at actual projected horizon`,
    );
    tap.props.onPress({
      nativeEvent: {
        [`${coordinateKind}X`]: projectedPoint.sx,
        [`${coordinateKind}Y`]: projectedPoint.sy - tap.props.style.top,
      },
    });
    const expectedRoute = pathModule.exports.findPath(pathModule.exports.GARDEN_START, nativePoint);
    check(
      same(
        shared[0].animation.steps.map((step) => step.to),
        expectedRoute.map((point) => point.x),
      ) &&
        same(
          shared[1].animation.steps.slice(0, -1).map((step) => step.to),
          expectedRoute.map((point) => point.y),
        ),
      `${viewportWidth}/${coordinateKind}: projected tap emits actual native route`,
    );
  }
}
for (const nativeEvent of [
  { offsetX: Infinity, offsetY: 2 },
  { locationX: 2, locationY: -Infinity },
  {},
]) {
  worldTree = setup(false, { view: 'tilt' });
  press(worldTree, 'shop');
  const pendingX = shared[0].animation;
  const pendingY = shared[1].animation;
  groundElement(worldTree).props.onPress({ nativeEvent });
  check(
    shared[0].animation === pendingX && shared[1].animation === pendingY,
    'invalid projected tap preserves current journey',
  );
}
const coordinateChecks = count - coordinateStart;

// Platform backgrounding differs from navigation blur: focus can stay true.
// The actual foreground hook is exercised separately in check-app-active.cjs.
const backgroundStart = count;
worldTree = setup();
press(worldTree, 'shop');
const backgroundJourney = shared[1].animation;
shared[0].value = 97;
shared[1].value = 121;
appActive = false;
worldTree = render();
check(
  shared.every((value) => value.animation === null),
  'background state cancels both movement axes while tab remains focused',
);
check(
  same([shared[0].value, shared[1].value], [97, 121]),
  'background state preserves the displayed position',
);
check(intervals.size === 0 && timers.size === 0, 'background state clears garden clocks');
check(worldTree.props.inert === true, 'background garden is inert');
end(backgroundJourney)(true);
press(worldTree, 'shop');
check(
  routes.length === 0 && shared[0].animation === null,
  'background callbacks and direct actions are ignored',
);
appActive = true;
worldTree = render();
end(backgroundJourney)(true);
check(routes.length === 0, 'returning to foreground cannot resurrect canceled navigation');
worldTree = setup();
press(worldTree, 'nap');
finishTravel();
const backgroundNap = [...timers.values()].find((timer) => timer.ms === 500);
appActive = false;
render();
backgroundNap.fn();
check(sleeps === 0, 'background state invalidates pending nap');
appActive = true;
render();
backgroundNap.fn();
check(sleeps === 0, 'old background nap remains invalid after foregrounding');
const backgroundChecks = count - backgroundStart;

// Kept memories are view inputs, never new targets or progress transactions.
// Identity, latest-memory selection and responses execute the actual domain helpers above.
const lifeStart = count;
const starterPlayer = game.player;
const makeKeptMemory = (id, intention, completedAt, name) =>
  Object.freeze({
    id,
    intention,
    companion: Object.freeze({ key: 'starter', name, species: 'BLOB' }),
    completedAt,
    recordedAt: completedAt + 1,
    minutes: 5,
    mission: null,
    early: false,
    source: 'self-reported',
  });
const keptMemories = Object.freeze([
  makeKeptMemory('older-read', 'read', 100, 'FERN ON AN EARLIER DAY'),
  makeKeptMemory('rest', 'rest', 120, 'FERN AT REST'),
  makeKeptMemory('newer-read', 'read', 200, 'FERN AT THE TIME'),
  makeKeptMemory('move', 'move', 150, 'FERN ON A WALK'),
  makeKeptMemory('create', 'create', 160, 'FERN SKETCHING'),
]);
const originalMemories = JSON.stringify(keptMemories);
const keepsakeElements = (tree) =>
  allElements(tree).filter((node) => node.props?.testID?.startsWith('garden-keepsake-'));
const targetSet = (tree) =>
  allElements(tree)
    .filter((node) => node.type === 'Pressable')
    .map((node) => `${node.key ?? ''}|${node.props.accessibilityLabel ?? ''}`)
    .sort();
const keepsakePlaces = {
  rest: { x: 130, y: 82 },
  read: { x: 100, y: 50 },
  move: { x: 154, y: 118 },
  create: { x: 44, y: 100 },
};
worldTree = setup();
check(keepsakeElements(worldTree).length === 0, 'no kept memories means no world ornaments');
for (const viewMode of ['flat', 'tilt']) {
  for (const sceneWidth of [320, 390, 430, 640]) {
    const options = { width: sceneWidth, view: viewMode, memories: keptMemories };
    const emptyTargets = targetSet(setup(false, { width: sceneWidth, view: viewMode }));
    const beforePlayer = JSON.stringify(game.player);
    worldTree = setup(false, options);
    const ornaments = keepsakeElements(worldTree);
    check(
      ornaments.length === 4 && new Set(ornaments.map((node) => node.props.testID)).size === 4,
      `${viewMode}/${sceneWidth}: kept memories produce one ornament per intention`,
    );
    check(
      same(targetSet(worldTree), emptyTargets),
      `${viewMode}/${sceneWidth}: keepsakes do not add or replace interaction targets`,
    );
    const expectedProjection = projectionModule.exports.makeProjection(
      viewMode,
      sceneWidth,
      map.GARDEN,
      viewMode === 'tilt' ? Math.round(sceneWidth * 0.14) : 0,
    );
    for (const [intention, location] of Object.entries(keepsakePlaces)) {
      const ornament = ornaments.find(
        (node) => node.props.testID === `garden-keepsake-${intention}`,
      );
      const box = ornament.props.style;
      const expectedFoot = projectionModule.exports.project(
        expectedProjection,
        location.x + 8,
        location.y + 16,
      );
      check(
        ornament.props.pointerEvents === 'none' &&
          ornament.props['aria-hidden'] === true &&
          ornament.props.accessibilityElementsHidden === true &&
          !allElements(ornament).some((node) => node.type === 'Pressable'),
        `${viewMode}/${sceneWidth}/${intention}: ornament is passive and hidden from accessibility`,
      );
      check(
        Number.isInteger(box.width) &&
          box.width >= 16 &&
          box.width % 16 === 0 &&
          box.height === box.width &&
          box.left === Math.round(expectedFoot.sx - box.width / 2) &&
          box.top === Math.round(expectedFoot.sy - box.height),
        `${viewMode}/${sceneWidth}/${intention}: integer artwork stays anchored to its actual projected feet`,
      );
      check(
        box.left >= 0 &&
          box.top >= 0 &&
          box.left + box.width <= sceneWidth &&
          box.top + box.height <= worldTree.props.style.height,
        `${viewMode}/${sceneWidth}/${intention}: ornament remains inside the scene`,
      );
    }
    check(
      noGameChange(beforePlayer) && JSON.stringify(keptMemories) === originalMemories,
      `${viewMode}/${sceneWidth}: rendering keepsakes changes neither progress nor memory records`,
    );
  }
}

const selectedInkling = {
  ...starterPlayer,
  guardian: 'inkling',
  collection: [{ id: 'inkling', metAt: 100, minutes: 15, befriendedAt: 101 }],
};
for (const identity of [starterPlayer, selectedInkling]) {
  game.player = identity;
  const options = { memories: keptMemories };
  const beforePlayer = JSON.stringify(game.player);
  worldTree = setup(false, options);
  const effective = deps['@/lib/visitors'].guardianPlayer(identity);
  for (const action of ['read', 'water', 'pond', 'lantern']) {
    press(worldTree, action);
    worldTree = render(false, options);
    check(
      !guardianElement(worldTree).props.gardenPose,
      `${effective.pet_name}/${action}: walking never holds an interaction pose`,
    );
    finishTravel();
    worldTree = render(false, options);
    const response = reactionElement(worldTree);
    const expectedSignature = deps['@/lib/garden-life'].gardenSignature(identity);
    check(
      same(response?.props.signature, expectedSignature) &&
        same(response?.props.actor, { x: shared[0].value, y: shared[1].value }),
      `${effective.pet_name}/${action}: actual identity signature and arrival feet reach the effect`,
    );
    check(
      guardianElement(worldTree).props.gardenPose?.id === response.props.reaction.id &&
        guardianElement(worldTree).props.gardenPose?.kind === expectedSignature.pose &&
        feedbackElement(worldTree).props.children ===
          deps['@/lib/garden-life'].gardenResponse(identity, action, 0, keptMemories),
      `${effective.pet_name}/${action}: actual companion response and idle pose reach the world`,
    );
  }
  press(worldTree, 'read');
  finishTravel();
  worldTree = render(false, options);
  check(
    feedbackElement(worldTree).props.children.startsWith(`${effective.pet_name} `),
    `${effective.pet_name}: repeated reading reveals the current companion's own behaviour`,
  );
  press(worldTree, 'read');
  finishTravel();
  worldTree = render(false, options);
  check(
    feedbackElement(worldTree).props.children.includes('FERN AT THE TIME') &&
      !feedbackElement(worldTree).props.children.includes('FERN ON AN EARLIER DAY') &&
      (identity === starterPlayer ||
        !feedbackElement(worldTree).props.children.includes('INKLING')),
    `${effective.pet_name}: repeated reading recalls the latest kept memory's original companion`,
  );
  check(
    noGameChange(beforePlayer),
    `${effective.pet_name}: keepsake interactions write no progress`,
  );
  press(worldTree, 'water');
  const pendingSignature = shared[1].animation;
  worldTree = render(false, options);
  check(
    !reactionElement(worldTree) && !guardianElement(worldTree).props.gardenPose,
    `${effective.pet_name}: retargeting clears the old signature and pose`,
  );
  render(false, { ...options, active: false });
  end(pendingSignature)(true);
  worldTree = render(false, { ...options, active: false });
  check(
    !reactionElement(worldTree) && !guardianElement(worldTree).props.gardenPose,
    `${effective.pet_name}: blur rejects a queued signature arrival`,
  );
  worldTree = render(false, options);
  end(pendingSignature)(true);
  worldTree = render(false, options);
  check(
    !reactionElement(worldTree) && !guardianElement(worldTree).props.gardenPose,
    `${effective.pet_name}: refocus cannot resurrect a canceled signature`,
  );

  worldTree = setup(false, options);
  press(worldTree, 'read');
  reduced = true;
  render(false, options);
  // Snapshot entries because arrival callbacks may replace pending timers.
  for (const [timerId, timer] of Array.from(timers)) {
    if (timer.ms === 0) {
      timers.delete(timerId);
      timer.fn();
    }
  }
  worldTree = render(false, options);
  const staticResponse = reactionElement(worldTree);
  check(
    staticResponse?.props.reduced === true &&
      staticResponse?.props.signature.animated === false &&
      guardianElement(worldTree).props.gardenPose?.kind === staticResponse.props.signature.pose,
    `${effective.pet_name}: reduced-motion arrival carries a static identity signature`,
  );
  const staticResponseId = staticResponse.props.reaction.id;
  reduced = false;
  worldTree = render(false, options);
  check(
    reactionElement(worldTree)?.props.reaction.id === staticResponseId,
    `${effective.pet_name}: motion preference changes do not create a second signature`,
  );
  worldTree = setup(true, options);
  check(
    keepsakeElements(worldTree).length === 4 &&
      !reactionElement(worldTree) &&
      !guardianElement(worldTree).props.gardenPose,
    `${effective.pet_name}: the nap garden keeps passive memories without interaction poses`,
  );
}
game.player = starterPlayer;
check(
  JSON.stringify(keptMemories) === originalMemories,
  'all world interactions preserve memory inputs',
);
const lifeChecks = count - lifeStart;
const signatureStart = count;
for (const [identity, motifColor] of [
  [starterPlayer, '#F7EDCB'],
  [selectedInkling, '#D8C5E7'],
]) {
  for (const viewMode of ['flat', 'tilt']) {
    const projection = projectionModule.exports.makeProjection(
      viewMode,
      384,
      map.GARDEN,
      viewMode === 'tilt' ? 54 : 0,
    );
    const signature = deps['@/lib/garden-life'].gardenSignature(identity);
    const identityReaction = {
      id: 1,
      kind: 'read',
      x: 84,
      y: 70,
      actor: { x: 86, y: 70 },
      signature,
    };
    resetChild();
    renderReaction(identityReaction, false, projection);
    const ticks = [...intervals.values()];
    check(
      ticks.length === 1 && ticks[0].ms === 120,
      `${signature.family}/${viewMode}: family motif shares the single finite reaction clock`,
    );
    for (let frame = 0; frame < 6; frame++) ticks[0].fn();
    let signatureTree = renderReaction(identityReaction, false, projection);
    check(
      allElements(signatureTree).some((node) => node.props.style?.backgroundColor === motifColor),
      `${signature.family}/${viewMode}: actual family motif appears during the reaction`,
    );
    signatureTree = renderReaction(identityReaction, true, projection);
    check(
      intervals.size === 0 &&
        signatureTree.props.pointerEvents === 'none' &&
        !allElements(signatureTree).some((node) => node.type === 'Pressable') &&
        allElements(signatureTree).some((node) => node.props.style?.backgroundColor === motifColor),
      `${signature.family}/${viewMode}: reduced motif remains visible and passive without a clock`,
    );
    const stoppedSignature = JSON.stringify(signatureTree);
    ticks[0].fn();
    check(
      JSON.stringify(renderReaction(identityReaction, true, projection)) === stoppedSignature,
      `${signature.family}/${viewMode}: a queued old frame cannot move the static motif`,
    );
  }
}
const signatureChecks = count - signatureStart;
const homeNapStart = count;
let plannedNaps = 0;
const plannedNap = () => {
  plannedNaps++;
};
worldTree = setup(false, { onNap: plannedNap });
reduced = true;
worldTree = render(false, { onNap: plannedNap });
let timerIdsBeforeNap = new Set(timers.keys());
press(worldTree, 'nap');
let plannedTimer = [...timers.entries()].find(
  ([id, timer]) => !timerIdsBeforeNap.has(id) && timer.ms === 0,
)?.[1];
check(Boolean(plannedTimer), 'Home nap delegation keeps the arrival pause');
plannedTimer.fn();
check(
  plannedNaps === 1 && sleeps === 0,
  'bed arrival delegates once instead of losing the Home break idea',
);
worldTree = setup(false, { onNap: plannedNap });
reduced = true;
worldTree = render(false, { onNap: plannedNap });
timerIdsBeforeNap = new Set(timers.keys());
press(worldTree, 'nap');
plannedTimer = [...timers.entries()].find(
  ([id, timer]) => !timerIdsBeforeNap.has(id) && timer.ms === 0,
)?.[1];
check(Boolean(plannedTimer), 'covered Home fixture has a pending delegated nap');
worldTree = render(false, { active: false, onNap: plannedNap });
plannedTimer.fn();
check(plannedNaps === 1 && sleeps === 0, 'coverage invalidates a retained delegated nap callback');
worldTree = setup();
reduced = true;
worldTree = render();
timerIdsBeforeNap = new Set(timers.keys());
press(worldTree, 'nap');
plannedTimer = [...timers.entries()].find(
  ([id, timer]) => !timerIdsBeforeNap.has(id) && timer.ms === 0,
)?.[1];
check(Boolean(plannedTimer), 'unconfigured worlds retain the default nap arrival');
plannedTimer.fn();
check(sleeps === 1, 'unconfigured worlds still call the existing ordinary nap');
const homeNapChecks = count - homeNapStart;
console.log(
  `${count} source assertions passed: ${originalChecks} movement/nap, ${activityChecks} activity/clock, ${geometryChecks} geometry, ${reachabilityChecks} reachability, ${cosmeticChecks} cosmetic/cancellation, ${childChecks} reaction-clock, ${groundChecks} ground-frame, ${coordinateChecks} event-coordinate, ${backgroundChecks} background-state, ${lifeChecks} keepsake/identity, ${signatureChecks} signature-motion, ${homeNapChecks} Home-nap delegation (${walkableCount} connected actor-safe cells, ${Object.keys(map.gardenHotspots).length} hotspots).`,
);
