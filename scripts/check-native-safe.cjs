/**
 * Native readiness (npm run check:native). NapAttack runs as a web app today and is
 * meant to ship as an iOS and Android app later (docs/native-readiness.md), so the app
 * code must keep working where there is no browser.
 *
 * The browser's objects (window.*, document.*, navigator.*, localStorage, matchMedia)
 * do not exist in the native app, or exist only in part: React Native defines `window`
 * as its global object, so `typeof window !== 'undefined'` is true there and is not a
 * guard. Only `Platform.OS === 'web'` or a `.web.ts(x)` file keeps code off the phone.
 *
 * 1. Every file in app/, components/, lib/ and hooks/ that uses a browser object is
 *    listed in scripts/native-safe.json with how many uses it has and how they are
 *    kept off native. A new file, or a new use in a listed file, fails until someone
 *    guards it and records how (the list is a review, not an exemption).
 * 2. Web-only packages (react-dom, pigeon-maps, workbox, posthog-js) are imported
 *    statically only from .web.ts(x) files; a dynamic import() is allowed in a file
 *    that checks Platform.OS.
 * 3. Every .web.ts(x) file has a native sibling (.ts(x), .native.ts(x) or .ios and
 *    .android), so the native bundle can resolve the same import.
 *
 * It reads source only. `npm run export:ios` bundles the app for iOS (part of verify);
 * only a simulator or device build shows how it behaves.
 */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');

const root = path.join(__dirname, '..');
const DIRS = ['app', 'components', 'lib', 'hooks'];
const listFile = path.join(__dirname, 'native-safe.json');
const reviewed = JSON.parse(fs.readFileSync(listFile, 'utf8'));

const USE =
  /\b(?:window|document|navigator)\s*\.\s*[A-Za-z_$][\w$]*|\b(?:localStorage|sessionStorage)\b|\bmatchMedia\s*\(/g;
// a file whose own variable is called `window` (a time window, say) is not using the browser's
const SHADOWS_WINDOW = /\b(?:const|let|var)\s+window\b|[(,]\s*window\s*[,):=]|\bwindow\s+of\b/;
const WEB_ONLY =
  /(?:^|\n)\s*import\b[^;]*?\bfrom\s*['"](react-dom(?:\/[^'"]*)?|pigeon-maps|posthog-js|workbox[^'"]*)['"]|\brequire\(\s*['"](react-dom|pigeon-maps|posthog-js|workbox[^'"]*)['"]\s*\)/g;
const DYNAMIC_WEB_ONLY =
  /\bimport\(\s*['"](react-dom|pigeon-maps|posthog-js|workbox[^'"]*)['"]\s*\)/g;

const stripComments = (src) =>
  src
    .replace(/\/\*[\s\S]*?\*\//g, (m) => m.replace(/[^\n]/g, ' '))
    .replace(/(^|[^:'"`])\/\/.*$/gm, '$1');

function walk(dir, out) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      if (entry.name !== 'fixtures' && entry.name !== 'node_modules') walk(full, out);
    } else if (
      /\.(ts|tsx)$/.test(entry.name) &&
      !/\.(test|qa)\.tsx?$/.test(entry.name) &&
      !entry.name.endsWith('.d.ts')
    ) {
      out.push(path.relative(root, full).split(path.sep).join('/'));
    }
  }
  return out;
}

const files = DIRS.filter((d) => fs.existsSync(path.join(root, d))).flatMap((d) =>
  walk(path.join(root, d), []),
);
const problems = [];
const seen = new Set();
let checks = 0;

for (const file of files) {
  const src = stripComments(fs.readFileSync(path.join(root, file), 'utf8'));
  const webFile = /\.web\.tsx?$/.test(file);

  // 3. a web file needs a native sibling
  if (webFile) {
    const base = file.replace(/\.web\.tsx?$/, '');
    const siblings = ['.ts', '.tsx', '.native.ts', '.native.tsx'].map((ext) => base + ext);
    const pair =
      ['.ios.ts', '.ios.tsx'].some((e) => fs.existsSync(path.join(root, base + e))) &&
      ['.android.ts', '.android.tsx'].some((e) => fs.existsSync(path.join(root, base + e)));
    checks++;
    if (!pair && !siblings.some((s) => fs.existsSync(path.join(root, s)))) {
      problems.push(
        `${file} has no native sibling (${path.basename(base)}.tsx or .native.tsx), so the iOS and Android bundles cannot resolve its import`,
      );
    }
    continue; // a .web file may use the browser freely
  }

  // 2. web-only packages
  for (const m of src.matchAll(WEB_ONLY)) {
    problems.push(
      `${file} imports '${m[1] || m[2]}', a web-only package: import it from a .web.tsx file (with a native sibling), or with import() behind Platform.OS === 'web'`,
    );
  }
  for (const m of src.matchAll(DYNAMIC_WEB_ONLY)) {
    if (!/Platform\.OS\s*[!=]==?\s*['"]web['"]/.test(src)) {
      problems.push(
        `${file} loads '${m[1]}' (web-only) without a Platform.OS === 'web' check in the file`,
      );
    }
  }
  checks++;

  // 1. browser objects, each file reviewed
  let uses = [...src.matchAll(USE)].map((m) => m[0]);
  if (SHADOWS_WINDOW.test(src)) uses = uses.filter((u) => !/^window\b/.test(u));
  checks++;
  if (!uses.length) continue;
  seen.add(file);
  const entry = reviewed[file];
  if (!entry) {
    problems.push(
      `${file} uses ${[...new Set(uses.map((u) => u.replace(/\s/g, '')))].join(', ')} (${uses.length}), which the native app does not have. ` +
        `Put it behind Platform.OS === 'web' (typeof window is not enough: React Native defines window) or in a .web.tsx file, ` +
        `then add the file to scripts/native-safe.json with its count and how it is guarded.`,
    );
  } else if (uses.length > entry.uses) {
    problems.push(
      `${file} now has ${uses.length} uses of browser objects (reviewed: ${entry.uses}, "${entry.guard}"). ` +
        `Check the new ones are kept off native the same way, then raise the count in scripts/native-safe.json.`,
    );
  } else if (uses.length < entry.uses) {
    console.log(
      `note: ${file} has ${uses.length} browser-object uses, fewer than the ${entry.uses} reviewed; lower the count in scripts/native-safe.json`,
    );
  }
}

for (const file of Object.keys(reviewed)) {
  checks++;
  if (!seen.has(file)) {
    problems.push(
      `scripts/native-safe.json lists ${file}, which no longer uses browser objects (or no longer exists): remove it`,
    );
  }
  assert.ok(
    typeof reviewed[file].guard === 'string' && reviewed[file].guard.length > 10,
    `${file}: say how it is kept off native`,
  );
}

if (problems.length) {
  console.error(
    'Native readiness check failed (docs/native-readiness.md):\n- ' + problems.join('\n- '),
  );
  process.exit(1);
}
console.log(
  `Native readiness: ${files.length} source files, ${seen.size} reviewed users of browser objects, ${checks} checks (source only; npm run export:ios bundles it for iOS).`,
);
