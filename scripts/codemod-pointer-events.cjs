/**
 * Moves the deprecated `pointerEvents` prop into `style` (react-native-web 0.21 warns
 * "props.pointerEvents is deprecated. Use style.pointerEvents"; React Native has read
 * `style.pointerEvents` since 0.71). Claude M, 21 Oct (C25, from #141).
 *
 *   node scripts/codemod-pointer-events.cjs <file.tsx> [...]      rewrite in place
 *   node scripts/codemod-pointer-events.cjs --check [<file.tsx> ...]  list and fail, change nothing
 *     (with no files: every .tsx under app/, components/ and hooks/; `npm run check:pointer-events`)
 *
 * For each JSX element with a `pointerEvents` attribute it removes the attribute and puts
 * the value in the element's style: an object style gains the key, an array gains
 * `{ pointerEvents: V }` last, any other `style={X}` becomes `style={[X, { pointerEvents: V }]}`,
 * and an element without a style gets `style={{ pointerEvents: V }}`. A later style entry
 * wins in React Native, so the value stays the element's. It is idempotent and leaves
 * elements with a spread style prop (`{...props}`) alone, reporting them.
 */
const fs = require('node:fs');
const ts = require('typescript');

const args = process.argv.slice(2);
const check = args.includes('--check');
const path = require('node:path');
const walk = (dir) =>
  fs.existsSync(dir)
    ? fs
        .readdirSync(dir, { withFileTypes: true })
        .flatMap((e) =>
          e.isDirectory()
            ? walk(path.join(dir, e.name))
            : e.name.endsWith('.tsx')
              ? [path.join(dir, e.name)]
              : [],
        )
    : [];
const named = args.filter((a) => a !== '--check');
const files = named.length ? named : check ? ['app', 'components', 'hooks'].flatMap(walk) : [];
let total = 0;

for (const file of files) {
  const text = fs.readFileSync(file, 'utf8');
  const source = ts.createSourceFile(file, text, ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
  const edits = [];
  const skipped = [];
  const visit = (node) => {
    if (ts.isJsxOpeningElement(node) || ts.isJsxSelfClosingElement(node)) {
      const props = node.attributes.properties;
      const pe = props.find(
        (p) => ts.isJsxAttribute(p) && p.name.getText(source) === 'pointerEvents',
      );
      if (pe) {
        const value = !pe.initializer
          ? "'auto'"
          : ts.isStringLiteral(pe.initializer)
            ? `'${pe.initializer.text}'`
            : pe.initializer.expression.getText(source);
        const style = props.find((p) => ts.isJsxAttribute(p) && p.name.getText(source) === 'style');
        const line = source.getLineAndCharacterOfPosition(pe.getStart(source)).line + 1;
        if (!style && props.some((p) => ts.isJsxSpreadAttribute(p))) {
          skipped.push(line);
        } else {
          // remove the attribute and the whitespace before it
          edits.push({ start: pe.getFullStart(), end: pe.getEnd(), text: '' });
          const entry = `{ pointerEvents: ${value} }`;
          if (style && style.initializer && ts.isJsxExpression(style.initializer)) {
            const expr = style.initializer.expression;
            if (ts.isObjectLiteralExpression(expr)) {
              // { ... } gains the key at its end
              const last = expr.properties[expr.properties.length - 1];
              const at = last ? last.getEnd() : expr.getStart(source) + 1;
              edits.push({
                start: at,
                end: at,
                text: `${last ? ',' : ''} pointerEvents: ${value}`,
              });
            } else if (ts.isArrayLiteralExpression(expr)) {
              // [a, b] gains the entry last, so it wins
              const last = expr.elements[expr.elements.length - 1];
              const at = last ? last.getEnd() : expr.getStart(source) + 1;
              edits.push({ start: at, end: at, text: `${last ? ', ' : ''}${entry}` });
            } else {
              edits.push({
                start: expr.getStart(source),
                end: expr.getEnd(),
                text: `[${expr.getText(source)}, ${entry}]`,
              });
            }
          } else {
            const at = node.tagName.getEnd();
            const after = node.typeArguments ? node.typeArguments.end + 1 : at;
            edits.push({ start: after, end: after, text: ` style={${entry}}` });
          }
          total++;
          if (check) console.log(`${file}:${line}`);
        }
      }
    }
    ts.forEachChild(node, visit);
  };
  visit(source);
  for (const line of skipped)
    console.log(`${file}:${line}: skipped (spread props and no style; move it by hand)`);
  if (check || !edits.length) continue;
  edits.sort((a, b) => b.start - a.start);
  let out = text;
  for (const e of edits) out = out.slice(0, e.start) + e.text + out.slice(e.end);
  fs.writeFileSync(file, out);
}
if (check && total) {
  console.error(
    `${total} pointerEvents props: move them into style (node scripts/codemod-pointer-events.cjs <file>)`,
  );
  process.exit(1);
}
console.log(
  check
    ? `pointerEvents: no deprecated props in ${files.length} files`
    : `moved ${total} pointerEvents props into style`,
);
