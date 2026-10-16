const assert = require('node:assert/strict');
const { rules } = require('../eslint-rules/no-ref-postfix-value');

const reports = [];
const visitor = rules['no-ref-postfix-value'].create({
  report: (diagnostic) => reports.push(diagnostic),
});
const id = (name) => ({ type: 'Identifier', name });
const member = (object, property, computed = false) => ({
  type: 'MemberExpression',
  object,
  property,
  computed,
});
const refCount = member(member(id('counts'), id('current')), id('kind'), true);
const update = (argument, parent, prefix = false) => {
  const node = { type: 'UpdateExpression', operator: '++', prefix, argument, parent };
  visitor.UpdateExpression(node);
};

update(refCount, { type: 'VariableDeclarator' });
assert.equal(reports.length, 1, 'A used postfix value on ref.current is reported');
update(member(id('timer'), id('current')), { type: 'ReturnStatement' });
assert.equal(reports.length, 2, 'Returning ref.current++ is reported');
update(refCount, { type: 'ExpressionStatement' });
assert.equal(reports.length, 2, 'A standalone postfix statement is fine');
update(refCount, { type: 'VariableDeclarator' }, true);
assert.equal(reports.length, 2, 'A prefix update already has the compiled meaning');
update(member(id('counts'), id('kind')), { type: 'VariableDeclarator' });
assert.equal(reports.length, 2, 'Plain objects are outside this ref rule');
console.log('PASS: ref postfix rule reports used ref.current++ values and allows statements.');
