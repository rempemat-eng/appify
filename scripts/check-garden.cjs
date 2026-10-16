/**
 * Source-level GardenWorld regression harness.
 * Run: npm run check:garden
 * Direct use: node scripts/check-garden.cjs [appify-directory]
 *
 * Transpiles the actual GardenWorld and garden-map source. React hooks, timers,
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
  dirty;
let fakeNow = Date.UTC(2026, 9, 16, 14);
class QAClock extends Date {
  static now() {
    return fakeNow;
  }
}
const game = {
  player: { mode: 'awake', mood: 50, grass: 20, pet_name: 'Fern' },
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
  '@/lib/game': { useGame, playPaused: () => false },
  '@/lib/visitors': {
    collectionOf: () => [],
    guardianPlayer: (player) => player,
    visitorInfo: () => ({ name: 'Friend' }),
  },
  '@/lib/garden-map': map,
  '@/components/guardian-pet': { GuardianPet: 'GuardianPet' },
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
evaluate('components/garden-reactions.tsx', reactionsModule);
deps['@/components/garden-reactions'] = reactionsModule.exports;
evaluate(
  'components/garden-world.tsx',
  mod,
  '\nmodule.exports.findPath = findPath; module.exports.Ambient = Ambient;',
);

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
      onFeed: () => {
        feeds++;
      },
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
for (const platform of ['web', 'ios']) {
  deps['react-native'].Platform.OS = platform;
  for (const width of [320, 390, 430, 640]) {
    worldTree = setup(false, { width });
    const elements = allElements(worldTree);
    const height = worldTree.props.style.height;
    const scale = width / map.GARDEN.width;
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
        (split ? art.left : box.left + art.left) === Math.round(object.x * scale) &&
          (split ? art.top : box.top + art.top) === Math.round(object.y * scale) &&
          art.width === Math.round(object.w * scale) &&
          art.height === Math.round(object.h * scale),
        `${platform}/${width}/${object.id}: world art positions and size are unchanged`,
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
      `${platform}/${width}/pond: target meets size and bounds`,
    );
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
function renderReaction(reaction, reduce = false) {
  index = 0;
  effects = [];
  const result = reactionsModule.exports.GardenReactions({ reaction, scale: 2, reduced: reduce });
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
  find(tree, `Your garden. Tap to walk ${game.player.pet_name} around.`).props.children.props.source
    .asset;
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
console.log(
  `${count} source assertions passed: ${originalChecks} movement/nap, ${activityChecks} activity/clock, ${geometryChecks} geometry, ${reachabilityChecks} reachability, ${cosmeticChecks} cosmetic/cancellation, ${childChecks} reaction-clock, ${groundChecks} ground-frame, ${count - coordinateStart} event-coordinate (${walkableCount} connected actor-safe cells, ${Object.keys(map.gardenHotspots).length} hotspots).`,
);
