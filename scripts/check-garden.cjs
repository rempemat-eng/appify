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
// The window the garden is rendered into (width in CSS px and device pixel ratio).
const screen = { width: 384, dpr: 2 };
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
// Layering: flat decals (the bridge) live in the ground layer. No object may be
// drawn over a walkable spot on them, so a crossing companion is always visible.
{
  const flat = map.gardenFlat;
  assert.ok(
    flat.some((decal) => decal.id === 'bridge'),
    'the bridge is ground',
  );
  assert.ok(
    !map.gardenObjects.some((object) => object.sprite === 'bridge'),
    'the bridge is not a layered object',
  );
  let walkableOnDecals = 0;
  for (const decal of flat)
    map.gardenWalk.forEach((row, r) =>
      [...row].forEach((cell, c) => {
        const x = c * map.GARDEN.cell + map.GARDEN.cell / 2;
        const y = r * map.GARDEN.cell + map.GARDEN.cell / 2;
        if (
          cell !== '.' ||
          x < decal.x ||
          x >= decal.x + decal.w ||
          y < decal.y ||
          y >= decal.y + decal.h
        )
          return;
        walkableOnDecals++;
        const cover = map.gardenObjects.find(
          (o) => o.y + o.h > y && x >= o.x && x < o.x + o.w && y >= o.y && y < o.y + o.h,
        );
        assert.ok(
          !cover,
          `${cover?.id} would draw over a companion on the ${decal.id} at ${x},${y}`,
        );
      }),
    );
  assert.ok(walkableOnDecals >= 6, 'the companion can actually walk on the bridge deck');
}
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
  sounds,
  appActive,
  dirty;
let fakeNow = Date.UTC(2026, 9, 16, 14);
class QAClock extends Date {
  static now() {
    return fakeNow;
  }
}
const game = {
  // no keepsakes set out in the garden (lib/decor.ts is checked in check:world)
  decor: [],
  // the hut as it first stands (its looks are checked in lib/hut-look.test.ts)
  hutLook: { door: 'oak', boxes: 'flowers', path: 'earth' },
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
  // where the companion walked in the hub (the map's record; it grants nothing)
  walkWorld(region, x, y, settle) {
    walks.push({ region, x, y, settle: !!settle });
  },
};
// spots the hub recorded with walkWorld (lib/game.ts)
let walks = [];
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
  useMemo(fn, deps) {
    const i = index++;
    const old = hooks[i];
    if (!old || !deps || deps.some((value, k) => value !== old.deps?.[k]))
      hooks[i] = { deps, value: fn() };
    return hooks[i].value;
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
  // (the hub's bubbles follow AtlasWalk's camera; nothing to react to in this harness)
  useAnimatedReaction() {},
  withTiming: (to, { duration }, callback) => ({ to, duration, callback }),
  withSequence: (...steps) => ({ steps }),
  cancelAnimation(value) {
    value.animation = null;
  },
  runOnJS: (fn) => fn,
  Easing: {
    linear: 'linear',
    quad: 'quad',
    in: (e) => `in-${e}`,
    out: (e) => `out-${e}`,
    inOut: (e) => `inOut-${e}`,
  },
};
const useGame = (select) => select(game);
useGame.getState = () => game;
useGame.setState = (patch) => {
  gameWrites.push(patch);
};
const jsxElement = (type, props, key) => ({ type, props, key });
const uiLink = { current: null };
const deps = {
  react,
  'react/jsx-runtime': { jsx: jsxElement, jsxs: jsxElement },
  'react-native': {
    Image: 'Image',
    Platform: { OS: 'web' },
    // The garden reads the window width and density for the shared pixel scale.
    PixelRatio: { get: () => screen.dpr },
    useWindowDimensions: () => ({ width: screen.width, height: 800 }),
    Pressable: 'Pressable',
    View: 'View',
    AccessibilityInfo: { announceForAccessibility: (text) => announcements.push(text) },
  },
  'react-native-reanimated': { ...anim, default: { View: 'Animated.View' } },
  'expo-router': {
    router: {
      // a route given as an object is recorded as its URL; the world's link (lib/ui.ts,
      // set just before) is recorded as that URL's query
      push: (route) => {
        const link = route === '/world' ? uiLink.current : null;
        uiLink.current = null;
        routes.push(
          typeof route === 'string'
            ? link
              ? `${route}?${new URLSearchParams(link).toString()}`
              : route
            : `${route.pathname}?${new URLSearchParams(route.params).toString()}`,
        );
      },
    },
  },
  '@/lib/ui': {
    useUi: {
      setState: (patch) => {
        if ('worldLink' in patch) uiLink.current = patch.worldLink;
      },
    },
  },
  'expo-haptics': { selectionAsync: async () => {} },
  '@/lib/cozy': { cozy: {} },
  '@/lib/motion': { useReducedMotion: () => reduced },
  '@/lib/app-active': { useAppActive: () => appActive },
  '@/lib/sound': { playSound: (id) => sounds.push(id) },
  '@/lib/game': {
    useGame,
    playPaused: () => false,
    feedback: () => {},
    missions: [{ id: 'book', level: 1 }],
  },
  'react-native-safe-area-context': {
    useSafeAreaInsets: () => ({ top: 0, bottom: 0, left: 0, right: 0 }),
  },
  // the hub's stage, card and keepsakes are leaf boundaries (their props are inspected)
  '@/components/atlas-walk': { AtlasWalk: 'AtlasWalk' },
  '@/components/place-card': { PlaceCardBody: 'PlaceCardBody' },
  '@/components/scene-decor': { decorExtras: () => [] },
  '@/lib/garden-map': map,
  './garden-map': map,
  '@/components/guardian-pet': { GuardianPet: 'GuardianPet' },
  '@/components/garden-keepsakes': { GardenKeepsakeArt: 'GardenKeepsakeArt' },
  '@/components/game-ui': { FloatingZ: 'FloatingZ', Pet: 'Pet' },
  '@/components/pixel-feedback': { BodyText: 'BodyText' },
  '@/components/pixel-frame': {
    FrameShape: 'FrameShape',
    PixelFrame: 'PixelFrame',
    PixelTail: 'PixelTail',
    frameTones: { gold: {}, paper: {} },
  },
  '@/lib/ui-tokens': {
    contentInset: (u) => 4 * u,
    type: { body: {}, label: { lineHeight: 16 }, caption: {} },
  },
  '@/lib/garden-growth-assets': {
    growthImages: new Proxy({}, { get: (_, key) => ({ asset: key }) }),
  },
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
  'garden-growth',
]) {
  const domainModule = { exports: {} };
  evaluate(`lib/${name}.ts`, domainModule);
  deps[`@/lib/${name}`] = domainModule.exports;
}
deps['@/lib/layout'] = { gameLayout: { maxWidth: 640 }, hudClearance: (top) => top + 60 };
const scaleModule = { exports: {} };
evaluate('lib/pixel-scale.ts', scaleModule);
deps['@/lib/pixel-scale'] = scaleModule.exports;
const { pixelScale, snapToDevice } = scaleModule.exports;
const snap = (value) => snapToDevice(value, screen.dpr);
// The garden's world width at a window width (the map is wider than a phone).
const worldWidthAt = (width) => Math.round(map.GARDEN.width * pixelScale(width, screen.dpr));
const START = map.gardenAnchors.start;
const EDGE = { min: 16, max: map.GARDEN.width - 16 };
const pathModule = { exports: {} };
evaluate('lib/garden-path.ts', pathModule);
deps['@/lib/garden-path'] = pathModule.exports;
// keyboard walking is a web-only extra (lib/keyboard-walk.ts): inert in this harness
// keepsakes (C12): none are set out here, so the garden's own walk stands; the model
// itself is tested in lib/world-save.test.ts
deps['@/lib/decor'] = {
  areaOf: (p) => p.area ?? 'hut',
  decorBox: () => ({ left: 0, top: 0, w: 1, h: 1, flat: true, cells: [] }),
  decorFootprint: () => ({ x: 0, y: 0, w: 4, h: 4 }),
  walkWithDecor: (rows) => rows,
  hutImageKey: (look) => `${look.door}-${look.boxes}`,
  // no new places are walked in this harness, so no keepsake is ever found
  newKeepsakes: () => [],
  keepsake: (id) => ({ id, name: id }),
};
deps['@/lib/decor-assets'] = { decorImages: {} };
deps['@/lib/garden-hut-assets'] = { hutImages: {}, hutPathImages: {} };
deps['@/lib/keyboard-walk'] = {
  STEP_MS: 120,
  keySteps: (dx, dy) => [[dx, dy]],
  useKeyboardWalk() {},
};
// the outline behind tall props is pure geometry: the real module
const occlusionModule = { exports: {} };
evaluate('lib/occlusion.ts', occlusionModule);
deps['@/lib/occlusion'] = occlusionModule.exports;
const projectionModule = { exports: {} };
evaluate('lib/garden-projection.ts', projectionModule);
deps['@/lib/garden-projection'] = projectionModule.exports;
const flatProjection = projectionModule.exports.makeProjection('flat', 384, map.GARDEN);
const flatPlace = (x, y, groundY = y) =>
  projectionModule.exports.lift(flatProjection, x, y, groundY);
evaluate('components/garden-reactions.tsx', reactionsModule);
deps['@/components/garden-reactions'] = reactionsModule.exports;
// The home hub's real geometry (docs/vision/home-hub.md): the valley's zones and walk,
// its places and cards, and the hub's conversions, evaluated from source.
for (const [name, ...ids] of [
  ['zone-maps', '@/lib/zone-maps', './zone-maps'],
  ['region-walk', '@/lib/region-walk'],
  ['world-places', '@/lib/world-places'],
  ['resident-routes', '@/lib/resident-routes'],
  ['world-cards', '@/lib/world-cards'],
  ['home-hub', '@/lib/home-hub'],
]) {
  const hubModule = { exports: {} };
  evaluate(`lib/${name}.ts`, hubModule);
  for (const id of ids) deps[id] = hubModule.exports;
}
const hubLib = deps['@/lib/home-hub'];
evaluate('components/garden-world.tsx', mod, '\nmodule.exports.Ambient = Ambient;');
mod.exports.findPath = pathModule.exports.findPath;

function render(napping = false, options = {}) {
  let tree;
  let attempts = 0;
  do {
    dirty = false;
    index = 0;
    effects = [];
    screen.width = options.width ?? 384;
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
      // a camera window: the Home tab's hub (docs/vision/home-hub.md)
      viewportHeight: options.viewportHeight,
      padBottom: options.padBottom ?? 0,
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
  walks = [];
  announcements = [];
  sounds = [];
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
  // (the hut is walked into by its door; the bed beside it is the nap)
  const actionObject = map.gardenObjects.find(
    (object) => object.action === action && object.id !== 'hut',
  );
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

// Expected arrival points come from the generated map, not fixed coordinates.
const arrival = (action) => {
  const route = pathModule.exports.findPath(START, map.gardenHotspots[action]);
  const last = route[route.length - 1];
  return [last.x, last.y];
};
const safeY = { min: 48, max: map.GARDEN.fenceY - 4 };
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
check(same([shared[0].value, shared[1].value], arrival('arena')), 'both visual axes arrive');

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
// (the first leg sets off gently: a quarter longer than the stroll's pace)
check(
  Math.abs(
    horizontalSequence.steps[0].duration -
      Math.max(
        60,
        (Math.hypot(plannedPath[0].x - actualOrigin.x, plannedPath[0].y - actualOrigin.y) / 34) *
          1000,
      ) *
        1.25,
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
  same([shared[0].value, shared[1].value], arrival('arena')),
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

// The hut is walked into: up to its door, then the room inside (app/world.tsx).
worldTree = setup();
allElements(worldTree)
  .find((element) => element.type === 'Pressable' && element.key === 'hut')
  .props.onPress();
complete(shared[0], shared[0].animation);
complete(shared[1], shared[1].animation);
check(same(routes, ['/world?from=hut']) && sleeps === 0, 'the hut door leads inside, not to a nap');

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
      const scale = pixelScale(width, screen.dpr);
      const worldWidth = worldWidthAt(width);
      const expectedProjection = projectionModule.exports.makeProjection(
        viewMode,
        worldWidth,
        map.GARDEN,
        viewMode === 'tilt' ? Math.round(worldWidth * 0.14) : 0,
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
            box.left + box.width <= worldWidth &&
            box.top + box.height <= height,
          `${platform}/${width}/${object.id}: target stays in scene`,
        );
        check(
          Math.abs(
            (split ? art.left : box.left + art.left) -
              snap(viewMode === 'flat' ? object.x * scale : expectedArt.left),
          ) < 1e-9 &&
            Math.abs(
              (split ? art.top : box.top + art.top) -
                snap(viewMode === 'flat' ? object.y * scale : expectedArt.top),
            ) < 1e-9 &&
            art.width === snap(viewMode === 'flat' ? object.w * scale : expectedArt.width) &&
            art.height === snap(viewMode === 'flat' ? object.h * scale : expectedArt.height),
          `${viewMode}/${platform}/${width}/${object.id}: art follows its actual projection, preserving flat identity`,
        );
        if (split)
          check(
            box.zIndex > map.GARDEN.fenceY - 4 &&
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
          pond.left + pond.width <= worldWidth &&
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
  x * 4 + 2 >= EDGE.min &&
  x * 4 + 2 <= EDGE.max &&
  y * 4 + 2 >= 48 &&
  y * 4 + 2 <= map.GARDEN.fenceY - 4 &&
  map.gardenWalk[y][x] === '.';
const cellKey = (x, y) => `${x},${y}`;
const queue = [[Math.floor(START.x / 4), Math.floor(START.y / 4)]]; // START in 4px cells
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
  const route = mod.exports.findPath(START, spot);
  check(
    route.length > 0 &&
      route.every(
        (point) =>
          point.x >= EDGE.min &&
          point.x <= EDGE.max &&
          point.y >= safeY.min &&
          point.y <= safeY.max,
      ),
    `${action}: actual path uses safe actor cells`,
  );
}
for (const edge of [
  { x: 0, y: 0 },
  { x: map.GARDEN.width, y: 0 },
  { x: 0, y: map.GARDEN.height },
  { x: map.GARDEN.width, y: map.GARDEN.height },
]) {
  const route = mod.exports.findPath(START, edge);
  check(
    route.length > 0 &&
      route.every(
        (point) =>
          point.x >= EDGE.min &&
          point.x <= EDGE.max &&
          point.y >= safeY.min &&
          point.y <= safeY.max,
      ),
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
const arrivalSound = { read: 'page', water: 'water', pond: 'splash', lantern: 'lantern' };
for (const action of ['read', 'water', 'pond', 'lantern']) {
  worldTree = setup();
  const before = JSON.stringify(game.player);
  press(worldTree, action);
  worldTree = render();
  check(
    !reactionElement(worldTree) && !feedbackElement(worldTree),
    `${action}: effect waits for visual arrival`,
  );
  check(sounds.join() === 'steps', `${action}: the tap plays footsteps; its sound waits too`);
  const completed = finishTravel();
  worldTree = render();
  check(
    sounds.join() === `steps,${arrivalSound[action]}`,
    `${action}: arrival plays its own sound once (${sounds.join()})`,
  );
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
  check(sounds.length === 2, `${action}: duplicate arrival cannot replay its sound`);
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

{
  // Idle life is ambient: the companion may stroll, but only the player's taps make sound.
  worldTree = setup();
  const realRandom = Math.random;
  const realNow = fakeNow;
  fakeNow += 10000;
  Math.random = () => 0.1;
  const idleTick = [...timers.entries()].find(([, timer]) => timer.ms === 2500);
  timers.delete(idleTick[0]);
  idleTick[1].fn();
  Math.random = realRandom;
  worldTree = render();
  check(
    shared.some((value) => value.animation !== null) &&
      [...timers.values()].some((timer) => timer.ms >= 4000) &&
      sounds.length === 0,
    'idle wandering walks silently and schedules the next idle beat',
  );
  fakeNow = realNow;
}
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
check(sounds.join() === 'steps,boop', 'pat boops at once; the canceled shop trip stays silent');
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
  check(!sounds.includes(arrivalSound[action]), `${action}: a canceled arrival plays no sound`);
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
  const reaction = { kind, id: 1, x: START.x, y: START.y };
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
      element.props.source?.asset?.startsWith('@/assets/garden/water-stream-'),
  ).props.source.asset;
const groundClock = [...intervals.values()].find((timer) => timer.ms === 400);
check(Boolean(groundClock), 'water uses its single 400 ms clock');
check(
  allElements(worldTree).some(
    (element) =>
      element.type === 'Image' && element.props.source?.asset === '@/assets/garden/ground.png',
  ),
  'the ground is one still image under the water overlays',
);
const frames = [groundAsset(worldTree)];
for (let i = 0; i < 4; i++) {
  groundClock.fn();
  worldTree = render();
  frames.push(groundAsset(worldTree));
}
check(
  new Set(frames.slice(0, 4)).size === 4 && frames[4] === frames[0],
  'water cycles all four actual frames, then returns to the first',
);
groundClock.fn();
render();
reduced = true;
worldTree = render();
check(
  groundAsset(worldTree) === frames[0] &&
    ![...intervals.values()].some((timer) => timer.ms === 400),
  'reduced motion immediately shows the first water frame and clears the clock',
);
const groundChecks = count - groundStart;
const coordinateStart = count;
const groundElement = (tree) =>
  find(tree, `Your garden. Tap to walk ${game.player.pet_name} around.`);
worldTree = setup();
const TAP = { x: 160, y: 236 }; // on the main path, south of the plaza
const tapScale = pixelScale(384, screen.dpr);
groundElement(worldTree).props.onPress({
  nativeEvent: { offsetX: TAP.x * tapScale, offsetY: TAP.y * tapScale },
});
const domExpected = mod.exports.findPath(START, TAP);
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
  nativeEvent: { locationX: 0, locationY: 0, offsetX: TAP.x * tapScale, offsetY: TAP.y * tapScale },
});
const nativeExpected = mod.exports.findPath(START, { x: 0, y: 0 });
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
  [{ x: NaN, y: START.y }, TAP],
  [START, { x: Infinity, y: TAP.y }],
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
    worldWidthAt(viewportWidth),
    map.GARDEN,
    Math.round(worldWidthAt(viewportWidth) * 0.14),
  );
  for (const coordinateKind of ['offset', 'location']) {
    // Use a cell centre: an exact grid boundary is ambiguous after floating-point
    // project/unproject round trips and can select either neighbouring cell.
    const nativePoint = { x: 162, y: 238 };
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
const keepsakePlaces = map.gardenAnchors.keepsakes;
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
      worldWidthAt(sceneWidth),
      map.GARDEN,
      viewMode === 'tilt' ? Math.round(worldWidthAt(sceneWidth) * 0.14) : 0,
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
        box.width === snap(16 * pixelScale(sceneWidth, screen.dpr) * expectedFoot.f) &&
          box.height === box.width &&
          box.left === snap(expectedFoot.sx - box.width / 2) &&
          box.top === snap(expectedFoot.sy - box.height),
        `${viewMode}/${sceneWidth}/${intention}: 16-pixel artwork on the shared grid stays anchored to its actual projected feet`,
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
      x: map.gardenHotspots.read.x,
      y: map.gardenHotspots.read.y,
      actor: { x: map.gardenHotspots.read.x + 2, y: map.gardenHotspots.read.y },
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

// Exercise the actual world's route actions, not a second model of travel. Every
// map exit must reject callbacks retained across interruption and still work on
// a fresh trip. These are source-boundary checks, not real browser scheduling.
const placeNavigationStart = count;
const placeRoutes = [
  ['missions', '/missions'],
  ['shop', '/shop'],
  // the gate opens on the valley (living-world plan W1): out into the walkable world,
  // picking up where the companion stands at the gate
  [
    'arena',
    `/world?from=gate&ex=${Math.round(arrival('arena')[0])}&ey=${Math.round(arrival('arena')[1])}`,
  ],
];
for (const [routeIndex, [action, expectedRoute]] of placeRoutes.entries()) {
  const [replacement, replacementRoute] = placeRoutes[(routeIndex + 1) % placeRoutes.length];
  worldTree = setup();
  press(worldTree, action);
  const replacedArrival = end(shared[1].animation);
  press(worldTree, replacement);
  replacedArrival(true);
  check(routes.length === 0, `${action}: retargeted arrival cannot navigate`);
  finishTravel();
  replacedArrival(true);
  check(
    same(routes, [replacementRoute]) && sleeps === 0,
    `${action}: only the replacement trip opens its screen, without starting a nap`,
  );

  worldTree = setup();
  press(worldTree, action);
  const blurredArrival = end(shared[1].animation);
  render(false, { active: false });
  blurredArrival(true);
  check(routes.length === 0, `${action}: arrival after blur cannot navigate`);
  worldTree = render();
  blurredArrival(true);
  check(routes.length === 0, `${action}: refocus cannot revive the interrupted trip`);
  press(worldTree, action);
  finishTravel();
  check(
    same(routes, [expectedRoute]),
    `${action}: a fresh trip after blur still reaches its screen`,
  );

  worldTree = setup();
  press(worldTree, action);
  const unmountedArrival = end(shared[1].animation);
  hooks.forEach((hook) => hook?.cleanup?.());
  unmountedArrival(true);
  check(routes.length === 0, `${action}: arrival after unmount cannot navigate`);

  worldTree = setup();
  press(worldTree, action);
  const backgroundedArrival = end(shared[1].animation);
  appActive = false;
  render();
  backgroundedArrival(true);
  check(routes.length === 0, `${action}: background arrival cannot navigate`);
  appActive = true;
  worldTree = render();
  backgroundedArrival(true);
  check(routes.length === 0, `${action}: foreground cannot revive the interrupted trip`);
  press(worldTree, action);
  finishTravel();
  check(same(routes, [expectedRoute]), `${action}: a fresh foreground trip reaches its screen`);

  worldTree = setup();
  press(worldTree, action);
  const animatedArrival = end(shared[1].animation);
  reduced = true;
  render();
  for (const [timerId, timer] of timers)
    if (timer.ms === 0) {
      timers.delete(timerId);
      timer.fn();
    }
  animatedArrival(true);
  check(
    same(routes, [expectedRoute]) && sleeps === 0,
    `${action}: switching to reduced motion reaches its screen exactly once`,
  );
}
const placeNavigationChecks = count - placeNavigationStart;

// The home hub (docs/vision/home-hub.md): the Home tab's garden is a place in the valley,
// drawn by AtlasWalk. The same journeys and actions run in garden pixels that carry on
// past the garden's edges. Walking out of any way out of the yard and back must never
// navigate (that swap was the pop), places keep their actions, and interrupted walks stay
// dead. Uses the real valley grid, places and cards (lib/home-hub.ts and its imports).
const hubCheckStart = count;
const places = deps['@/lib/world-places'];
function hubElements(tree) {
  const out = [];
  const visit = (node) => {
    if (!node || typeof node !== 'object') return;
    if (Array.isArray(node)) return node.forEach(visit);
    out.push(node);
    for (const key of ['children', 'scene', 'hits']) visit(node.props?.[key]);
  };
  visit(tree);
  return out;
}
const hubSetup = (options = {}) => setup(false, { viewportHeight: 800, ...options });
const hubRender = (options = {}) => render(false, { viewportHeight: 800, ...options });
const stageOf = (tree) => hubElements(tree).find((element) => element.type === 'AtlasWalk');
const labelled = (tree, label) =>
  hubElements(tree).find(
    (element) => element.type === 'Pressable' && element.props.accessibilityLabel === label,
  );
const at = () => ({ x: shared[0].value, y: shared[1].value });
const tapValley = (tree, garden) => stageOf(tree).props.onTap(hubLib.toRegion(garden));
const gardenPin = (tree) => (stageOf(tree).props.markers ?? []).some((m) => m.id === 'garden');

worldTree = hubSetup();
let stage = stageOf(worldTree);
check(
  stage?.props.region === 'valley' && stage.props.homeLayer === true,
  'the Home tab draws the garden as a place in the valley (AtlasWalk), not as its own screen',
);
check(
  stage.props.follow.px === shared[0] && stage.props.follow.py === shared[1],
  'one companion: AtlasWalk follows the garden companion itself',
);
check(
  !hubElements(worldTree).some((element) =>
    element.props?.accessibilityLabel?.startsWith('Your garden. Tap to walk'),
  ),
  "the hub has one tap layer (AtlasWalk), not the garden screen's own ground",
);
check(!gardenPin(worldTree), 'at home the garden needs no pin of its own');

// every way out of the yard, out and back in again, with no screen change
const ways = {
  gate: hubLib.GATE_OUT,
  trail: { x: 200, y: -60 },
  west: { x: -60, y: 300 },
  east: { x: map.GARDEN.width + 60, y: 300 },
};
for (const [way, outside] of Object.entries(ways)) {
  worldTree = hubSetup();
  check(tapValley(worldTree, outside) === true, `${way}: the hub takes the tap`);
  check(Boolean(shared[1].animation), `${way}: a walk out is planned on the valley's grid`);
  finishTravel();
  worldTree = hubRender();
  const out = at();
  check(
    routes.length === 0,
    `${way}: walking out of the garden opens no other screen (routes: ${routes.join()})`,
  );
  check(
    hubLib.homeSide('home', out) === 'out' && Math.hypot(out.x - outside.x, out.y - outside.y) < 16,
    `${way}: the companion walks on out into the valley (${Math.round(out.x)},${Math.round(out.y)})`,
  );
  check(gardenPin(worldTree), `${way}: out in the valley, the garden shows its pin`);
  check(
    walks.some((w) => w.settle && w.region === 'valley'),
    `${way}: where it stopped is recorded for the map, as on the world screen`,
  );
  tapValley(worldTree, START);
  finishTravel();
  worldTree = hubRender();
  check(routes.length === 0, `${way}: walking back into the yard opens no screen either`);
  check(
    Math.hypot(at().x - START.x, at().y - START.y) < 8 && !gardenPin(worldTree),
    `${way}: home again, at the same spot, with no pin`,
  );
}

// no ping-pong at the yard's edge: steps either side of it change nothing
worldTree = hubSetup();
const edge = { x: 160, y: places.GARDEN_YARD.maxY + hubLib.YARD_MARGIN / 2 };
for (let i = 0; i < 3; i++) {
  tapValley(worldTree, edge);
  finishTravel();
  worldTree = hubRender();
  check(!gardenPin(worldTree), `edge ${i}: just over the yard's edge still counts as home`);
  tapValley(worldTree, { x: 160, y: places.GARDEN_YARD.maxY - 8 });
  finishTravel();
  worldTree = hubRender();
}
check(routes.length === 0, "back and forth over the yard's edge never navigates");

// the garden's places keep their actions in the hub
worldTree = hubSetup();
labelled(worldTree, map.gardenHotspots.mail.label).props.onPress();
check(routes.length === 0, 'mail: nothing opens before the companion arrives');
finishTravel();
check(same(routes, ['/journal?tab=postcards']), 'mail: arriving opens the postcards, once');

worldTree = hubSetup();
labelled(worldTree, 'go inside the hut').props.onPress();
finishTravel();
check(same(routes, ['/world?from=hut']), 'the hut door still leads inside (a door is a real cut)');

worldTree = hubSetup();
labelled(worldTree, map.gardenHotspots.arena.label).props.onPress();
finishTravel();
check(routes.length === 0, 'the ring hotspot opens no screen: the valley is right there');
check(Boolean(shared[1].animation), 'the ring hotspot walks on out through the gate');
finishTravel();
check(
  Math.hypot(at().x - hubLib.GATE_OUT.x, at().y - hubLib.GATE_OUT.y) < 8,
  'the ring hotspot ends in the town lane, where the world screen used to open',
);

// interrupted walks stay dead in the hub too
worldTree = hubSetup();
labelled(worldTree, 'go inside the hut').props.onPress();
const hutArrival = end(shared[1].animation);
hubRender({ active: false });
hutArrival(true);
worldTree = hubRender();
hutArrival(true);
check(routes.length === 0, 'a hut walk interrupted by a sheet or blur never opens the hut later');

worldTree = hubSetup();
labelled(worldTree, map.gardenHotspots.mail.label).props.onPress();
const mailArrival = end(shared[1].animation);
tapValley(worldTree, hubLib.GATE_OUT);
mailArrival(true);
check(routes.length === 0, 'a tap on the valley replaces a pending place visit');

// a valley place shows its card where the companion stops; walking on closes it
worldTree = hubSetup();
const stall = hubLib.toGarden(places.regionPoint(places.missionPlaces.shop));
tapValley(worldTree, stall);
finishTravel();
worldTree = hubRender();
const card = hubElements(worldTree).find((element) => element.type === 'PlaceCardBody');
check(card?.props.card.kind === 'shop', "at Moss's stall the hub shows the stall's card");
check(
  stageOf(worldTree).props.padBottom > 0 && stageOf(worldTree).props.focusY < 0.55,
  'the camera keeps the companion above the card',
);
card.props.act.openShop();
check(same(routes, ['/shop']), "the stall's card opens the shop, as on the world screen");
routes = [];
tapValley(worldTree, START);
worldTree = hubRender();
check(
  !hubElements(worldTree).some((element) => element.type === 'PlaceCardBody'),
  'walking on closes the card',
);

// reduced motion: walks are instant, and still never navigate
worldTree = hubSetup();
reduced = true;
worldTree = hubRender();
tapValley(worldTree, hubLib.GATE_OUT);
check(
  shared[1].animation === null &&
    Math.hypot(at().x - hubLib.GATE_OUT.x, at().y - hubLib.GATE_OUT.y) < 8,
  'reduced motion: the walk out of the gate is instant',
);
check(routes.length === 0, 'reduced motion: and opens no screen');
const hubChecks = count - hubCheckStart;
console.log(
  `${count} source assertions passed: ${originalChecks} movement/nap, ${activityChecks} activity/clock, ${geometryChecks} geometry, ${reachabilityChecks} reachability, ${cosmeticChecks} cosmetic/cancellation, ${childChecks} reaction-clock, ${groundChecks} ground-frame, ${coordinateChecks} event-coordinate, ${backgroundChecks} background-state, ${lifeChecks} keepsake/identity, ${signatureChecks} signature-motion, ${homeNapChecks} Home-nap delegation, ${placeNavigationChecks} place-navigation, ${hubChecks} home-hub (${walkableCount} connected actor-safe cells, ${Object.keys(map.gardenHotspots).length} hotspots).`,
);
