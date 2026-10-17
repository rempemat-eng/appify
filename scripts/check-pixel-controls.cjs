/**
 * Shared pixel-switch handler checks. React and RN are boundary substitutes:
 * this exercises the actual emitted props, not DOM/native event dispatch,
 * layout, focus visibility or physical-device accessibility.
 */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const ts = require('typescript');

let checks = 0;
const check = (condition, message) => {
  assert.ok(condition, message);
  checks++;
};
const platform = { OS: 'web' };
const element = (type, props) => ({ type, props });
const source = ts.transpileModule(
  fs.readFileSync(path.join(__dirname, '..', 'components', 'pixel-frame.tsx'), 'utf8'),
  {
    compilerOptions: {
      module: ts.ModuleKind.CommonJS,
      target: ts.ScriptTarget.ES2022,
      jsx: ts.JsxEmit.ReactJSX,
    },
  },
).outputText;
// The real shared Space handler, reading the same mutable platform object.
const switchKeysModule = { exports: {} };
vm.runInNewContext(
  ts.transpileModule(fs.readFileSync(path.join(__dirname, '..', 'lib', 'switch-keys.ts'), 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
  }).outputText,
  {
    module: switchKeysModule,
    exports: switchKeysModule.exports,
    require: (id) => {
      assert.equal(id, 'react-native', `Unexpected switch-keys boundary: ${id}`);
      return { Platform: platform };
    },
  },
);
const destination = { exports: {} };
const boundaries = {
  react: { useState: (value) => [value, () => {}] },
  'react/jsx-runtime': { jsx: element, jsxs: element, Fragment: 'Fragment' },
  'react-native': {
    Platform: platform,
    Pressable: 'Pressable',
    TextInput: 'TextInput',
    View: 'View',
    useWindowDimensions: () => ({ width: 402, height: 874 }),
  },
  '@/lib/cozy': { cozy: {} },
  '@/lib/art-direction': { artOutline: '#1E1917' },
  '@/lib/layout': { gameLayout: { maxWidth: 576 } },
  '@/lib/switch-keys': switchKeysModule.exports,
};
vm.runInNewContext(source, {
  module: destination,
  exports: destination.exports,
  require(id) {
    assert.ok(id in boundaries, `Unexpected boundary: ${id}`);
    return boundaries[id];
  },
});

function fixture(value = false, disabled = false) {
  const changes = [];
  const { props } = destination.exports.PixelSwitch({
    value,
    disabled,
    accessibilityLabel: 'Reduce decorative motion',
    onValueChange: (next) => changes.push(next),
  });
  return { props, changes };
}
function key(subject, overrides = {}) {
  const target = {};
  let prevented = 0;
  subject.props.onKeyDown({
    key: ' ',
    target,
    currentTarget: target,
    repeat: false,
    preventDefault: () => prevented++,
    ...overrides,
  });
  return prevented;
}

for (const value of [false, true]) {
  const switchFixture = fixture(value);
  const { props, changes } = switchFixture;
  check(props.accessibilityRole === 'switch', 'switch semantics survive custom keys');
  check(props['aria-checked'] === value, 'web checked state matches value');
  check(props.accessibilityState.checked === value, 'native checked state matches value');
  check(props.accessibilityLabel === 'Reduce decorative motion', 'accessible name survives');
  check(props.style.minWidth >= 44 && props.style.minHeight >= 44, '44px minimum target');
  check(key(switchFixture) === 1, 'Space prevents sheet scrolling');
  check(changes.length === 1 && changes[0] === !value, 'Space toggles once in either direction');
  key(switchFixture, { repeat: true });
  check(changes.length === 1, 'holding Space does not repeatedly toggle');
  key(switchFixture, { key: 'Spacebar' });
  check(changes.length === 2 && changes[1] === !value, 'legacy Spacebar key toggles once');
  for (const other of ['Enter', 'Escape', 'Tab', 'ArrowDown', 'a']) {
    check(key(switchFixture, { key: other }) === 0, `${other} stays with Pressable/browser`);
  }
  check(changes.length === 2, 'other keys do not cause a second activation');
  for (const modifier of ['altKey', 'ctrlKey', 'metaKey']) {
    check(key(switchFixture, { [modifier]: true }) === 0, `${modifier} shortcut is untouched`);
  }
  check(key(switchFixture, { target: {} }) === 0, 'descendant keyboard events are ignored');
  check(changes.length === 2, 'shortcuts and descendant events do not toggle');
  props.onPress();
  check(changes.length === 3 && changes[2] === !value, 'pointer/Enter still use onPress');
}
const disabled = fixture(false, true);
key(disabled);
key(disabled, { repeat: true });
check(disabled.changes.length === 0, 'disabled switch ignores Space and repeats');
check(
  disabled.props.disabled && disabled.props.accessibilityState.disabled,
  'disabled is announced',
);

for (const os of ['ios', 'android']) {
  platform.OS = os;
  const native = fixture();
  check(!('onKeyDown' in native.props), `${os} receives no web event handler`);
  native.props.onPress();
  check(native.changes.length === 1 && native.changes[0], `${os} native press still toggles`);
}
console.log(`Pixel controls: ${checks} checks passed (source-level boundary harness).`);
