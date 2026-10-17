/** Render the real journal with substituted React/native/router boundaries.
 * Verifies emitted content and controls, not browser layout or native events.
 */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const ts = require('typescript');
const root = path.join(__dirname, '..');
let checks = 0;
function check(value, message) {
  assert.ok(value, message);
  checks++;
}
function evaluate(file, boundaries) {
  const destination = { exports: {} };
  const source = ts.transpileModule(fs.readFileSync(path.join(root, file), 'utf8'), {
    compilerOptions: {
      module: ts.ModuleKind.CommonJS,
      target: ts.ScriptTarget.ES2022,
      jsx: ts.JsxEmit.ReactJSX,
    },
  }).outputText;
  vm.runInNewContext(source, {
    module: destination,
    exports: destination.exports,
    require(id) {
      assert.ok(id in boundaries, `Known journal boundary: ${id}`);
      return boundaries[id];
    },
  });
  return destination.exports;
}
const catalogue = evaluate('lib/visitors.ts', { '@/lib/offline-rules': {} });
function nodes(tree) {
  if (!tree || typeof tree !== 'object') return [];
  if (Array.isArray(tree)) return tree.flatMap(nodes);
  return [tree, ...nodes(tree.props?.children)];
}
function text(tree) {
  if (tree === null || tree === undefined || typeof tree === 'boolean') return '';
  if (typeof tree !== 'object') return String(tree);
  if (Array.isArray(tree)) return tree.map(text).join('');
  return text(tree.props?.children);
}
const jsx = (type, props) => ({ type, props });
function fixture(request = 'visitors') {
  const control = { params: { tab: request }, values: [], index: 0, routes: [], feedback: 0 };
  const state = {
    player: { collection: [], postcards: [] },
    companionMemories: [],
    pendingMemories: [],
  };
  const useGame = (select) => select(state);
  useGame.getState = () => {
    throw new Error('Journal summary must not mutate game state');
  };
  const Tabs = Object.assign(() => {}, {
    List: 'TabList',
    Indicator: 'TabIndicator',
    Trigger: 'TabTrigger',
    Label: 'TabLabel',
  });
  const components = evaluate('app/journal.tsx', {
    react: {
      useEffect() {},
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
    },
    'react/jsx-runtime': { jsx, jsxs: jsx, Fragment: 'Fragment' },
    'react-native': {
      View: 'View',
      FlatList: 'FlatList',
      ScrollView: 'ScrollView',
      useWindowDimensions: () => ({ width: 402, height: 874 }),
    },
    'expo-router': {
      Stack: { Screen: 'StackScreen' },
      router: { dismissTo: (route) => control.routes.push(route) },
      useLocalSearchParams: () => control.params,
    },
    'heroui-native': { Tabs },
    'react-native-safe-area-context': { useSafeAreaInsets: () => ({ top: 24, bottom: 12 }) },
    'react-native-svg': { __esModule: true, default: 'Svg', Rect: 'Rect' },
    '@/components/pixel-icon': { PixelIcon: 'PixelIcon' },
    '@/lib/cozy': { cozy: {} },
    '@/lib/layout': { gameLayout: { gutter: 16, maxWidth: 640 } },
    '@/lib/game': {
      useGame,
      startGame() {},
      feedback() {
        control.feedback++;
      },
    },
    '@/lib/visitors': catalogue,
    '@/lib/visitor-art': { visitorPixels: () => [] },
    '@/components/cozy-ui': { CozyBackground: 'CozyBackground', CozyPanel: 'CozyPanel' },
    '@/components/game-ui': { Pet: 'Pet', PixelButton: 'PixelButton', PixelText: 'PixelText' },
    '@/components/pixel-feedback': { BodyText: 'BodyText' },
    '@/components/pixel-frame': { FrameFill: 'FrameFill', usePixelUnit: () => 2 },
    '@/components/game-hud': { PixelBar: 'PixelBar' },
    '@/components/visitors': { JournalEmpty: 'JournalEmpty', PostcardArt: 'PostcardArt' },
    '@/components/companion-memories': {
      CompanionMemories: 'CompanionMemories',
      MemoryReflection: 'MemoryReflection',
    },
  });
  return {
    control,
    state,
    Tabs,
    render() {
      control.index = 0;
      return components.default();
    },
  };
}
function summary(tree) {
  return text(nodes(tree).find((node) => node.type === 'PixelText'));
}
function progress(tree) {
  return nodes(tree).filter((node) => node.props?.accessibilityRole === 'progressbar');
}

for (const request of ['postcards', 'visitors', 'memories', 'invalid']) {
  const f = fixture(request);
  let tree = f.render();
  const tab = request === 'invalid' ? 'visitors' : request;
  const expected =
    tab === 'postcards'
      ? 'POSTCARDS 0'
      : tab === 'memories'
        ? 'MEMORIES 0'
        : `FRIENDS 0 / ${catalogue.visitors.length}`;
  check(summary(tree) === expected, `${request}: correct empty collection heading`);
  check(
    progress(tree).length === (tab === 'visitors' ? 1 : 0),
    `${request}: only Visitors has friend progress`,
  );
  check(
    nodes(tree).find((node) => node.type === 'TabList').props.style.alignSelf === 'stretch',
    'tab strip aligns with the journal column rather than its intrinsic label width',
  );
  for (const trigger of nodes(tree).filter((node) => node.type === 'TabTrigger')) {
    check(
      trigger.props.style?.minHeight >= 44 && trigger.props.style?.minWidth >= 44,
      'journal tabs meet source-level 44px minimum',
    );
  }
  check(
    nodes(tree).find((node) => node.type === 'StackScreen').props.options.headerShown === false,
    'preserve Claude pixel-title navigation',
  );
  const back = tree.props.children.find(
    (node) => node?.type === 'PixelButton' && node.props.label === 'BACK TO THE GARDEN',
  );
  check(!!back, 'Back stays outside scrolling collection content');
  back.props.onPress();
  check(f.control.routes[0] === '/', 'Back dismisses to the existing garden navigator');
  if (tab === 'postcards') {
    const empty = nodes(tree).find((node) => node.type === 'FlatList').props.ListEmptyComponent;
    empty.props.onPress();
    check(
      f.control.routes.at(-1) === '/missions',
      'empty postcards dismisses to Missions without pushing a second tab navigator',
    );
  }
  if (tab === 'memories') {
    nodes(tree)
      .find((node) => node.props?.label === 'PLAN ANOTHER BREAK')
      .props.onPress();
    check(
      f.control.routes.at(-1) === '/missions',
      'memory break action uses the same dismiss-to route',
    );
  }
  f.state.player = {
    collection: [{ id: catalogue.visitors[0].id, metAt: 1, minutes: 15, befriendedAt: 2 }],
    postcards: [
      { id: 'p1', mission: 'book', at: 1 },
      { id: 'p2', mission: 'park', at: 2 },
      { id: 'bad', mission: 'unknown', at: 3 },
    ],
  };
  f.state.companionMemories = [{ id: 'm1', completedAt: 1, recordedAt: 1 }];
  tree = f.render();
  check(
    summary(tree) ===
      (tab === 'postcards'
        ? 'POSTCARDS 2'
        : tab === 'memories'
          ? 'MEMORIES 1'
          : `FRIENDS 1 / ${catalogue.visitors.length}`),
    'summary counts validated current save data',
  );
  const tabs = nodes(tree).find((node) => node.type === f.Tabs);
  tabs.props.onValueChange('postcards');
  tree = f.render();
  check(
    summary(tree) === 'POSTCARDS 2' && progress(tree).length === 0,
    'switching updates heading and removes unrelated friend progress',
  );
  const list = nodes(tree).find((node) => node.type === 'FlatList');
  check(
    list.props.data[0].id === 'p2' && list.props.data[1].id === 'p1',
    'preserve newest-first postcard ordering',
  );
  check(
    text(tree).includes('Places your companion visited while you took a break.'),
    'postcards describe outings, not friendship',
  );
  f.control.params.tab = 'postcards';
  f.render();
  f.control.params.tab = 'memories';
  tree = f.render();
  check(summary(tree) === 'MEMORIES 1', 'a new requested tab still overrides the old choice');
  f.state.player = null;
  f.control.params.tab = 'postcards';
  tree = f.render();
  check(
    summary(tree) === 'POSTCARDS 0',
    'missing player safely shows an empty postcard collection',
  );
}
console.log(`Journal: ${checks} source-level checks passed; no native or phone rendering claim.`);
