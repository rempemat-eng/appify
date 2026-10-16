const assert = require('node:assert/strict');
const { rules } = require('../eslint-rules/no-unstable-zustand-selector');

const reports = [];
const visitor = rules['no-unstable-zustand-selector'].create({
  report: (diagnostic) => reports.push(diagnostic),
});
const visit = (node) => visitor.CallExpression(node);
const identifier = (name) => ({ type: 'Identifier', name });
const call = (name, argument) => ({
  type: 'CallExpression',
  callee: identifier(name),
  arguments: [argument],
});
visit(call('useSyncExternalStore', identifier('subscribe')));
assert.equal(reports.length, 0, 'React subscriptions are not Zustand selectors');
visit(call('useGardenStore', identifier('selectGarden')));
assert.equal(reports.length, 1, 'Unanalysed Zustand selector references remain checked');
visit(
  call('useGardenStore', { type: 'ArrowFunctionExpression', body: { type: 'ObjectExpression' } }),
);
assert.equal(reports.length, 2, 'Fresh Zustand object selections remain checked');
visit(
  call('useGardenStore', {
    type: 'CallExpression',
    callee: identifier('useShallow'),
    arguments: [identifier('selectGarden')],
  }),
);
assert.equal(reports.length, 2, 'Explicit shallow selections remain valid');
console.log(
  'PASS: selector lint rule accepts React subscriptions and still detects unstable Zustand selections.',
);
