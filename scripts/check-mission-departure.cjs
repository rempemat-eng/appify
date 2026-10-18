/** Actual departure components with substituted React/native/store boundaries.
 * Checks source decisions and emitted geometry, not React scheduling, phone
 * layout, native events, animation, or actual mission settlement.
 */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const ts = require('typescript');
const root = path.join(__dirname, '..');
const read = (file) => fs.readFileSync(path.join(root, file), 'utf8');
let checks = 0;
const check = (condition, message) => {
  assert.ok(condition, message);
  checks++;
};
const jsx = (type, props) => ({ type, props });
const compile = (source) =>
  ts.transpileModule(source, {
    compilerOptions: {
      module: ts.ModuleKind.CommonJS,
      target: ts.ScriptTarget.ES2022,
      jsx: ts.JsxEmit.ReactJSX,
    },
  }).outputText;
function evaluate(
  source,
  requireBoundary = () => {
    throw new Error('Unexpected import');
  },
) {
  const destination = { exports: {} };
  vm.runInNewContext(compile(source), {
    module: destination,
    exports: destination.exports,
    require: requireBoundary,
  });
  return destination.exports;
}
const declaration = read('lib/game.ts').match(/export const missions = \[[\s\S]*?\n\];/)?.[0];
assert.ok(declaration, 'read the actual mission rules');
const { missions } = evaluate(declaration);
const maps = evaluate(read('lib/world-maps.ts'));
const catalogue = evaluate(read('lib/world-catalogue.ts'));
const missionMap = evaluate(read('lib/mission-map.ts'), (id) => {
  assert.equal(id, '@/assets/missions/map.png', 'the map module only loads its image');
  return 'map.png';
});
function nodes(tree) {
  if (!tree || typeof tree !== 'object') return [];
  if (Array.isArray(tree)) return tree.flatMap(nodes);
  return [tree, ...nodes(tree.props?.children)];
}
const find = (tree, predicate) => {
  const found = nodes(tree).find(predicate);
  assert.ok(found, 'expected emitted control');
  return found;
};
const byType = (tree, type) => find(tree, (node) => node.type === type);
const button = (tree, label) =>
  find(tree, (node) => node.type === 'PixelButton' && node.props.label === label);
function fixture() {
  const control = {
    focused: true,
    active: true,
    width: 402,
    height: 874,
    values: [],
    index: 0,
    calls: [],
    pushed: [],
    unit: 4 / 3,
  };
  const state = {
    player: { mode: 'awake', level: 1 },
    battle: null,
    missionReturnPending: false,
    sleep(id, intention) {
      control.calls.push({ id, intention });
      state.player.mode = 'mission';
    },
  };
  const useGame = (select) => select(state);
  useGame.getState = () => state;
  const boundaries = {
    react: {
      useState(initial) {
        const index = control.index++;
        if (!(index in control.values)) control.values[index] = initial;
        return [
          control.values[index],
          (next) => {
            control.values[index] = typeof next === 'function' ? next(control.values[index]) : next;
          },
        ];
      },
      useEffect() {},
      useRef: (current) => ({ current }),
    },
    'react/jsx-runtime': { jsx, jsxs: jsx, Fragment: 'Fragment' },
    'react-native': {
      Image: 'Image',
      Modal: 'Modal',
      PixelRatio: { get: () => 3 },
      Pressable: 'Pressable',
      ScrollView: 'ScrollView',
      View: 'View',
      useWindowDimensions: () => control,
    },
    'expo-router': {
      useNavigation: () => ({ isFocused: () => control.focused }),
      router: { push: (route) => control.pushed.push(route) },
    },
    'react-native-reanimated': {
      __esModule: true,
      default: { View: 'Animated.View' },
      Easing: { linear: 'linear', cubic: 'cubic', inOut: (e) => e },
      useAnimatedStyle: () => ({}),
      useSharedValue: (value) => ({ value, set() {} }),
      withSequence: (...steps) => steps,
      withTiming: (to) => to,
    },
    '@/lib/motion': { useReducedMotion: () => false },
    // WALK THERE leaves the world's link here (presentation only)
    '@/lib/ui': { useUi: { setState: () => {} } },
    '@/lib/mission-map': missionMap,
    '@/lib/world-places': {
      missionPlaces: Object.fromEntries(
        ['book', 'park', 'mountain', 'shop', 'arena', 'garden'].map((id) => [id, { id }]),
      ),
      regionPoint: () => ({ x: 480, y: 900 }),
    },
    '@/components/atlas-walk': { AtlasWalk: 'AtlasWalk' },
    '@/components/guardian-pet': { GuardianPet: 'GuardianPet' },
    'react-native-safe-area-context': { useSafeAreaInsets: () => ({ top: 0, bottom: 0 }) },
    'react-native-svg': { __esModule: true, default: 'Svg', Polyline: 'Polyline' },
    '@/lib/game': { missions, useGame, feedback() {} },
    '@/lib/app-active': { useAppActive: () => control.active },
    '@/lib/art-direction': { artMaterials: JSON.parse(read('art/materials.json')).materials },
    '@/lib/cozy': { cozy: {} },
    '@/lib/layout': {
      gameColumn: {},
      gameLayout: { maxWidth: 640, gutter: 16 },
      hudClearance: () => 70,
      hotbarClearance: () => 90,
    },
    '@/lib/world-maps': maps,
    '@/lib/world-catalogue': catalogue,
    '@/lib/world-assets': { worldProps: new Proxy({}, { get: (_target, key) => key }) },
    '@/components/companion-memories': { BreakIntentionPicker: 'BreakIntentionPicker' },
    '@/components/cozy-ui': { CozyBackground: 'CozyBackground', CozySheet: 'CozySheet' },
    '@/components/pixel-feedback': { BodyText: 'BodyText' },
    '@/components/game-ui': { PixelButton: 'PixelButton' },
    '@/components/pixel-frame': { PixelFrame: 'PixelFrame', usePixelUnit: () => control.unit },
  };
  const components = evaluate(read('components/mission-departure.tsx'), (id) => {
    assert.ok(id in boundaries, `Known boundary ${id}`);
    return boundaries[id];
  });
  return {
    state,
    control,
    components,
    render() {
      control.index = 0;
      return components.MissionDeparture();
    },
  };
}

const f = fixture();
let tree = f.render();
check(
  byType(tree, f.components.MissionDestinationMap).props.selected === 'park',
  'Park is selected initially',
);
check(f.control.calls.length === 0, 'rendering never starts or settles a mission');
button(tree, 'BREAK IDEA').props.onPress();
tree = f.render();
byType(tree, 'BreakIntentionPicker').props.onChange('read');
tree = f.render();
button(tree, 'BACK TO MAP').props.onPress();
tree = f.render();
check(!nodes(tree).some((n) => n.type === 'Modal'), 'idea Done returns to the map');
check(f.control.calls.length === 0, 'choosing/closing an idea grants nothing');
byType(tree, f.components.MissionDestinationMap).props.onSelect('mountain');
tree = f.render();
check(button(tree, 'LEVEL 2 NEEDED').props.disabled, 'Mountain retains its level gate');
button(tree, 'LEVEL 2 NEEDED').props.onPress();
check(f.control.calls.length === 0, 'a forced locked callback cannot launch');
f.state.player.level = 2;
tree = f.render();
const launch = button(tree, 'START MOUNTAIN RETREAT').props.onPress;
f.control.focused = false;
launch();
check(f.control.calls.length === 0, 'stale callback after tab blur cannot launch');
f.control.focused = true;
f.state.missionReturnPending = true;
launch();
check(f.control.calls.length === 0, 'pending protected return blocks another outing');
f.state.missionReturnPending = false;
f.state.battle = {};
launch();
check(f.control.calls.length === 0, 'live battle blocks launch');
f.state.battle = null;
launch();
launch();
check(f.control.calls.length === 1, 'rapid launch callbacks start only one outing');
check(
  f.control.calls[0].id === 'mountain' && f.control.calls[0].intention === 'read',
  'departure delegates selected place and optional idea to the existing store',
);
check(
  f.control.values[1] === null && f.control.values[2] === false,
  'successful launch clears the draft and idea panel',
);
const background = fixture();
background.control.active = false;
tree = background.render();
check(button(tree, 'ON A BREAK').props.disabled, 'background presentation cannot launch');
button(tree, 'ON A BREAK').props.onPress();
check(background.control.calls.length === 0, 'inactive callback is harmless');

const routes = fixture();
tree = routes.render();
byType(tree, routes.components.MissionDestinationMap).props.onSelect('arena');
tree = routes.render();
check(
  !nodes(tree).some((n) => n.type === 'PixelButton' && /^START|BREAK IDEA/.test(n.props.label)),
  'the sparring ring shows no mission departure',
);
const toRing = button(tree, 'TO THE SPARRING RING').props.onPress;
routes.control.focused = false;
toRing();
check(routes.control.pushed.length === 0, 'stale tap after leaving the tab opens nothing');
routes.control.focused = true;
toRing();
check(routes.control.pushed.join() === '/arena', 'the ring opens the battle zone');
byType(tree, routes.components.MissionDestinationMap).props.onSelect('shop');
tree = routes.render();
button(tree, "VISIT MOSS'S STALL").props.onPress();
check(routes.control.pushed.join() === '/arena,/shop', 'the stall opens the shop');
check(routes.control.calls.length === 0, 'route places never start a mission');

const places = missionMap.missionMapPlaces;
for (const mission of missions) check(mission.id in places, `${mission.id} has a place on the map`);
// The map is now the valley itself (components/atlas-walk.tsx): where each place
// stands in the world, and that it is open, reachable ground, is checked in
// lib/world-save.test.ts.

for (const compact of [false, true]) {
  const map = f.components.MissionDestinationMap({
    selected: 'park',
    level: 1,
    compact,
    onSelect() {},
  });
  const choices = nodes(map).filter((n) => n.type === 'PixelButton');
  check(choices.length === Object.keys(places).length, 'one choice for each place on the map');
  const tags = choices.filter((n) => /LV 2/.test(n.props.label));
  check(tags.length === 1, 'the locked mountain carries its level on its button');
  let picked = null;
  const pick = f.components.MissionDestinationMap({
    selected: 'park',
    level: 1,
    compact,
    onSelect(id) {
      picked = id;
    },
  });
  nodes(pick)
    .filter((n) => n.type === 'PixelButton')
    .find((n) => /BOOK|LIBRARY/i.test(n.props.label) || n.props.label)
    .props.onPress();
  check(picked !== null, 'a place button picks its place');
  check(!nodes(map).some((n) => n.type === 'WorldScene'), 'map does not mount animated worlds');
}
check(
  /return focused \? <MissionDeparture \/> : null/.test(read('components/game-screens.tsx')),
  'tab blur unmounts departure and discards unfinished state',
);
console.log(
  `Mission departure: ${checks} source-level checks passed; no phone or native rendering claim.`,
);
