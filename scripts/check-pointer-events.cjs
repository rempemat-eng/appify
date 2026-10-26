/**
 * pointerEvents stays a prop (npm run check:pointer-events, in check).
 *
 * react-native-web 0.21 warns in development that `props.pointerEvents` is deprecated, but it
 * honours `style.pointerEvents` only in styles compiled by StyleSheet.create: an inline style
 * object (`style={{ ..., pointerEvents: 'none' }}`) drops it, so an overlay meant to let
 * touches through starts catching them. #205 moved every prop into inline styles and the
 * world stopped taking taps under the place card and other overlays (found by
 * `npm run playtest`'s interrupted walk, fixed by the PR that added this check). Until the
 * game uses StyleSheet for these, keep `pointerEvents` as a prop; the dev warning is
 * harmless.
 */
const fs = require('node:fs');
const path = require('node:path');

const root = path.join(__dirname, '..');
const walk = (dir) =>
  fs.existsSync(dir)
    ? fs
        .readdirSync(dir, { withFileTypes: true })
        .flatMap((e) =>
          e.isDirectory()
            ? walk(path.join(dir, e.name))
            : /\.tsx?$/.test(e.name)
              ? [path.join(dir, e.name)]
              : [],
        )
    : [];
const files = ['app', 'components', 'hooks'].flatMap((d) => walk(path.join(root, d)));
const found = [];
for (const file of files) {
  fs.readFileSync(file, 'utf8')
    .split('\n')
    .forEach((line, i) => {
      if (/\bpointerEvents\s*:/.test(line))
        found.push(`${path.relative(root, file)}:${i + 1}: ${line.trim()}`);
    });
}
if (found.length) {
  console.error(
    'pointerEvents in a style object is ignored by react-native-web for inline styles; ' +
      'use the pointerEvents prop:\n' +
      found.join('\n'),
  );
  process.exit(1);
}
console.log(`pointerEvents: a prop everywhere (${files.length} files, none in a style object)`);
