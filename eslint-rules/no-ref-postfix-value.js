// React Compiler (as of this build) compiles a postfix update on a ref member
// as a pre-increment when its value is used: `const n = ref.current[k]++`
// yields the new value. That silently skipped the first garden memory line.
// Standalone `ref.current++;` statements are fine; only used values are flagged.
function readsRefCurrent(node) {
  let current = node;
  while (current && current.type === 'MemberExpression') {
    if (
      !current.computed &&
      current.property.type === 'Identifier' &&
      current.property.name === 'current'
    )
      return true;
    current = current.object;
  }
  return false;
}

const rule = {
  meta: {
    type: 'problem',
    docs: {
      description:
        'Disallow using the value of a postfix ++/-- on ref.current (React Compiler treats it as prefix)',
    },
    schema: [],
  },
  create(context) {
    return {
      UpdateExpression(node) {
        if (node.prefix || !readsRefCurrent(node.argument)) return;
        const parent = node.parent;
        const valueUnused =
          parent &&
          (parent.type === 'ExpressionStatement' ||
            (parent.type === 'ForStatement' && parent.update === node));
        if (valueUnused) return;
        context.report({
          node,
          message:
            'Read ref.current first, then write it: React Compiler turns a used postfix update into a prefix one.',
        });
      },
    };
  },
};

module.exports = {
  meta: { name: 'refs' },
  rules: {
    'no-ref-postfix-value': rule,
  },
};
