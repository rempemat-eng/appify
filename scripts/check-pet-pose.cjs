/**
 * Source-level Pet garden-pose regression checks.
 * Run: node scripts/check-pet-pose.cjs [appify-directory]
 *
 * Transpiles the actual Pet function, actual pixel-art renderer and sprite data.
 * React hooks, native/SVG elements, timers and Reanimated scheduling are boundary
 * substitutes. Animation plans are recorded; selected shared values are sampled
 * at their native-pixel extrema. No saved app state or network service is used.
 *
 * These checks verify emitted pixels, geometry and cancellation plans. They do
 * not validate React scheduling, real Reanimated interpolation/worklets, browser
 * appearance, physical-device rendering or native accessibility behavior.
 */
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const assert = require('node:assert/strict');
const { createRequire } = require('node:module');

const appDir = path.resolve(process.argv[2] ?? path.join(__dirname, '..'));
const appRequire = createRequire(path.join(appDir, 'package.json'));
const ts = appRequire('typescript');
const read = (file) => fs.readFileSync(path.join(appDir, file), 'utf8');
const compile = (source) =>
  ts.transpileModule(source, {
    compilerOptions: {
      module: ts.ModuleKind.CommonJS,
      jsx: ts.JsxEmit.ReactJSX,
      target: ts.ScriptTarget.ES2022,
    },
  }).outputText;
const modules = {};
function requireBoundary(id) {
  if (!(id in modules)) throw new Error(`Unsubstituted import: ${id}`);
  return modules[id];
}
function evaluate(source) {
  const destination = { exports: {} };
  vm.runInNewContext(compile(source), {
    module: destination,
    exports: destination.exports,
    require: requireBoundary,
  });
  return destination.exports;
}

// Read the real presentation palette without initializing the game store or its
// storage/network boundaries. Both declarations come directly from game.ts.
const gameSource = read('lib/game.ts');
const inkDeclaration = gameSource.match(/export const ink = [^;]+;/)?.[0];
const paletteDeclaration = gameSource.match(/export const palette = \{[\s\S]*?\n\};/)?.[0];
assert(inkDeclaration && paletteDeclaration, 'game presentation palette declarations exist');
const palette = evaluate(`${inkDeclaration}\n${paletteDeclaration}`).palette;
modules['@/lib/game'] = { palette };
modules['../art/materials.json'] = JSON.parse(read('art/materials.json'));
modules['@/lib/art-direction'] = evaluate(read('lib/art-direction.ts'));
const cozy = evaluate(read('lib/cozy.ts')).cozy;
modules['@/lib/pet-sprites'] = evaluate(read('lib/pet-sprites.ts'));
const petArt = evaluate(read('lib/pet-art.ts'));
const { petPixels, GROUND_SHADOW } = petArt;
modules['@/lib/pet-art'] = petArt; // visitor-art draws its shadow with pet-art's helper
const { visitorPixels } = evaluate(read('lib/visitor-art.ts'));
const grasslings = evaluate(read('lib/grasslings.ts'));

let hooks;
let hookIndex;
let effects;
let shared;
let timers;
let serial;
let dirty;
let reduced = false;
const react = {
  useState(initial) {
    const index = hookIndex++;
    hooks[index] ??= { value: typeof initial === 'function' ? initial() : initial };
    return [
      hooks[index].value,
      (next) => {
        const value = typeof next === 'function' ? next(hooks[index].value) : next;
        dirty ||= value !== hooks[index].value;
        hooks[index].value = value;
      },
    ];
  },
  useRef(initial) {
    return (hooks[hookIndex++] ??= { current: initial });
  },
  useEffect(effect, dependencies) {
    const index = hookIndex++;
    const old = hooks[index];
    if (!old || dependencies.some((value, i) => value !== old.dependencies[i])) {
      effects.push(() => {
        old?.cleanup?.();
        hooks[index] = { dependencies, cleanup: effect() };
      });
    }
  },
};
const animations = {
  useSharedValue(initial) {
    const ref = react.useRef(null);
    if (!ref.current) {
      ref.current = {
        value: initial,
        animation: null,
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
  useAnimatedStyle: (style) => style(),
  cancelAnimation(value) {
    value.animation = null;
  },
  withSequence: (...steps) => ({ steps }),
  withTiming: (to, options) => ({ to, ...options }),
};
const element = (type, props, key) => ({ type, props, key });
modules['react/jsx-runtime'] = { jsx: element, jsxs: element };

// Isolate the real function through its syntax tree. This avoids executing
// unrelated screen components and follows Pet if neighboring functions move.
const uiSource = read('components/game-ui.tsx');
const uiTree = ts.createSourceFile(
  'game-ui.tsx',
  uiSource,
  ts.ScriptTarget.Latest,
  true,
  ts.ScriptKind.TSX,
);
const petFunction = uiTree.statements.find(
  (statement) => ts.isFunctionDeclaration(statement) && statement.name?.text === 'Pet',
);
assert(petFunction, 'Pet function exists');
const petModule = { exports: {} };
vm.runInNewContext(compile(petFunction.getText(uiTree)), {
  module: petModule,
  exports: petModule.exports,
  require: requireBoundary,
  ...react,
  ...animations,
  Animated: { View: 'Animated.View' },
  Svg: 'Svg',
  Rect: 'Rect',
  Pressable: 'Pressable',
  View: 'View',
  PixelRatio: { get: () => 1 },
  PixelProp: 'PixelProp',
  useReducedMotion: () => reduced,
  c: cozy,
  petPixels,
  GROUND_SHADOW,
  visitorPixels,
  // the 44 px touch area helper (lib/layout.ts): layout only, outside these pose checks
  touchReach: () => ({}),
  ...grasslings,
  // This matrix covers the three starters. Visitor identity remains a leaf
  // boundary here; actual visitor rendering is loaded for the function contract.
  isVisitorId: () => false,
  visitorInfo: (id) => ({ name: id }),
  Haptics: { impactAsync: async () => {}, ImpactFeedbackStyle: { Light: 0 } },
  setTimeout: (callback, ms) => {
    const id = ++serial;
    timers.set(id, { callback, ms, interval: false });
    return id;
  },
  setInterval: (callback, ms) => {
    const id = ++serial;
    timers.set(id, { callback, ms, interval: true });
    return id;
  },
  clearTimeout: (id) => timers.delete(id),
  clearInterval: (id) => timers.delete(id),
  Math,
});

function reset(isReduced = false) {
  hooks = [];
  hookIndex = 0;
  effects = [];
  shared = [];
  timers = new Map();
  serial = 0;
  dirty = false;
  reduced = isReduced;
}
function render(props) {
  let tree;
  let attempts = 0;
  do {
    dirty = false;
    hookIndex = 0;
    effects = [];
    tree = petModule.exports.Pet(props);
    effects.forEach((effect) => effect());
    assert(++attempts < 5, 'source render settles');
  } while (dirty);
  return tree;
}
function elements(node, result = []) {
  if (Array.isArray(node)) node.forEach((child) => elements(child, result));
  else if (node && typeof node === 'object') {
    result.push(node);
    elements(node.props?.children, result);
  }
  return result;
}
function pixels(node) {
  return elements(node)
    .filter((entry) => entry.type === 'Rect')
    .map((entry) => ({ x: entry.props.x, y: entry.props.y, color: entry.props.fill }));
}
function samePixels(actual, expected, label) {
  // Pixel values cross vm realms, whose object prototypes are different.
  assert.equal(JSON.stringify(actual), JSON.stringify(expected), label);
}
function unmount() {
  hooks.forEach((hook) => hook?.cleanup?.());
}
function poseParts(tree) {
  const entries = elements(tree);
  const body = entries.find(
    (entry) =>
      entry.type === 'Animated.View' &&
      entry.props.style?.transform?.length === 2 &&
      entry.props.style.transform[1].translateY !== undefined,
  );
  const fixed = entries.find(
    (entry) => entry.type === 'Svg' && entry.props.style?.position === 'absolute',
  );
  assert(body && fixed, 'pose separates moving body from its fixed ground pixels');
  return { body, fixed };
}
function activePoseValues() {
  const values = shared.filter((value) => value.animation !== null);
  assert.equal(values.length, 2, 'only horizontal and vertical finite pose plans are active');
  return values;
}
function assertStopped(label) {
  assert(
    shared.every((value) => value.animation === null),
    `${label}: animations cancelled`,
  );
  assert.equal(timers.size, 0, `${label}: timers cleared`);
}

let posedVariants = 0;
let canonicalVariants = 0;
for (const species of ['BLOB', 'RAT', 'CUBE']) {
  for (const level of [1, 2, 3]) {
    for (const hat of [null, 'CAP', 'TOP HAT', 'CROWN', 'SHADES']) {
      for (const facing of ['left', 'right']) {
        const props = { species, level, hat, facing, bob: false };
        const canonical = petPixels(species, level, hat, false, false);
        reset();
        samePixels(
          pixels(render(props)),
          canonical,
          'unset pose preserves canonical sprite pixels',
        );
        canonicalVariants++;
        unmount();
        for (const kind of ['nestle', 'sniff', 'ponder']) {
          reset();
          const posed = { ...props, gardenPose: { id: 1, kind } };
          render(posed);
          const [poseX, poseY] = activePoseValues();
          for (const value of [poseX, poseY]) {
            assert(
              value.animation.steps.length > 2,
              'pose includes anticipation, action and settle',
            );
            assert.equal(value.animation.steps.at(-1).to, 0, 'finite pose settles at its origin');
            assert(
              value.animation.steps.every(
                (step) => Number.isFinite(step.duration) && step.duration >= 0,
              ),
              'durations are finite',
            );
          }
          for (const [x, y] of [
            [-1, -1],
            [1, 1],
            [0, 0],
          ]) {
            poseX.set(x);
            poseY.set(y);
            const { body, fixed } = poseParts(render(posed));
            samePixels(
              pixels(fixed),
              canonical.filter((pixel) => pixel.y >= 27),
              'feet and shadow retain canonical pixels at every sampled pose',
            );
            samePixels(
              pixels(body),
              canonical.filter((pixel) => pixel.y < 27),
              'body and hat keep their undeformed pixel relationships',
            );
            const dx = body.props.style.transform[0].translateX / 6;
            const dy = body.props.style.transform[1].translateY / 6;
            assert(Number.isInteger(dx) && Number.isInteger(dy), 'pose uses whole native pixels');
            for (const pixel of pixels(body)) {
              const visualX = facing === 'left' ? 31 - pixel.x : pixel.x;
              assert(
                visualX + dx >= 0 && visualX + dx <= 31 && pixel.y + dy >= 0 && pixel.y + dy <= 31,
                'body and hat remain inside the 32px sprite canvas',
              );
            }
          }
          unmount();
          assertStopped('unmount');
          posedVariants++;
        }
      }
    }
  }
}
assert.equal(posedVariants, 270);
assert.equal(canonicalVariants, 90);

const props = { bob: false, gardenPose: { id: 1, kind: 'sniff' } };
reset();
render(props);
const firstPlan = activePoseValues()[0].animation;
render({ ...props, gardenPose: { id: 2, kind: 'ponder' } });
assert.notEqual(
  activePoseValues()[0].animation,
  firstPlan,
  'a new pose replaces the old animation',
);
render({ ...props, active: false });
assertStopped('inactive');
render(props);
assert(
  shared.every((value) => value.animation === null),
  'refocus does not replay a cancelled pose',
);
render({ ...props, gardenPose: undefined });
assert(
  shared.every((value) => value.animation === null),
  'clearing the pose cancels its animation',
);
unmount();

// Each case interrupts a currently running sequence, rather than inspecting
// a sequence already stopped by the inactivity check above.
reset();
render(props);
activePoseValues();
render({ ...props, gardenPose: undefined });
assert(
  shared.every((value) => value.animation === null),
  'clear cancels a live pose',
);
unmount();
assertStopped('unmount after clear');

reset();
render(props);
const [walkingPoseX, walkingPoseY] = activePoseValues();
render({ ...props, walking: true });
assert(
  walkingPoseX.animation === null && walkingPoseY.animation === null,
  'walking cancels both live pose axes',
);
unmount();
assertStopped('unmount after walking');

reset();
render(props);
reduced = true;
const still = render(props);
assertStopped('reduced motion enabled during a pose');
assert(
  poseParts(still).body.props.style.transform.some(
    (transform) => (transform.translateX ?? transform.translateY) !== 0,
  ),
  'reduced motion presents a readable static pose',
);
reduced = false;
render(props);
assert(
  shared.every((value) => value.animation === null),
  'disabling reduced motion does not replay a pose',
);
unmount();

for (const kind of ['nestle', 'sniff', 'ponder']) {
  reset(true);
  const tree = render({ ...props, gardenPose: { id: 3, kind } });
  assertStopped(`initial reduced motion: ${kind}`);
  assert(poseParts(tree).body, `${kind} retains its static body layer`);
  unmount();
}
console.log(
  `Pet source checks passed: ${posedVariants} posed and ${canonicalVariants} canonical sprite/stage/hat/facing variants; fixed ground pixels, rigid bounded body/hat motion, finite replacement/cancellation and static reduced motion. React scheduling, real Reanimated and browser/native visuals are outside this harness.`,
);
