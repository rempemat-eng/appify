/**
 * Exercises the actual app-active hook's snapshot and subscription functions.
 * Run: node scripts/check-app-active.cjs
 *
 * React's useSyncExternalStore boundary captures those functions; AppState and
 * document are event fixtures. This checks state transitions, listener wiring
 * and cleanup, not React scheduling or real browser/native lifecycle delivery.
 */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const ts = require('typescript');

const sourcePath = path.join(__dirname, '..', 'lib', 'app-active.ts');
const source = ts.transpileModule(fs.readFileSync(sourcePath, 'utf8'), {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
}).outputText;
let checks = 0;
const check = (condition, message) => {
  assert.ok(condition, message);
  checks++;
};

function fixture(platform, withDocument = true) {
  const appListeners = new Set();
  const documentListeners = new Set();
  let appRemovals = 0;
  let documentRemovals = 0;
  let captured;
  const appState = {
    currentState: 'active',
    addEventListener(type, notify) {
      assert.equal(type, 'change');
      appListeners.add(notify);
      return {
        remove() {
          appRemovals++;
          appListeners.delete(notify);
        },
      };
    },
  };
  const documentFixture = {
    visibilityState: 'visible',
    addEventListener(type, notify) {
      assert.equal(type, 'visibilitychange');
      documentListeners.add(notify);
    },
    removeEventListener(type, notify) {
      assert.equal(type, 'visibilitychange');
      documentRemovals++;
      documentListeners.delete(notify);
    },
  };
  const moduleFixture = { exports: {} };
  const context = {
    module: moduleFixture,
    exports: moduleFixture.exports,
    require(id) {
      if (id === 'react')
        return {
          useSyncExternalStore(subscribe, snapshot, serverSnapshot) {
            captured = { subscribe, snapshot, serverSnapshot };
            return snapshot();
          },
        };
      if (id === 'react-native') return { AppState: appState, Platform: { OS: platform } };
      throw new Error(`Unexpected import: ${id}`);
    },
    ...(withDocument ? { document: documentFixture } : {}),
  };
  vm.runInNewContext(source, context, { filename: sourcePath });
  const initial = moduleFixture.exports.useAppActive();
  return {
    initial,
    captured,
    appState,
    documentFixture,
    appListeners,
    documentListeners,
    removals: () => ({ app: appRemovals, document: documentRemovals }),
  };
}

const web = fixture('web');
check(web.initial === true, 'visible active web app is foreground');
check(web.captured.serverSnapshot() === false, 'server snapshot stays inactive');
const observed = [];
const stop = web.captured.subscribe(() => observed.push(web.captured.snapshot()));
check(
  web.appListeners.size === 1 && web.documentListeners.size === 1,
  'web subscribes to both native app state and document visibility',
);
web.documentFixture.visibilityState = 'hidden';
for (const notify of web.documentListeners) notify();
check(observed.at(-1) === false, 'hidden document notifies inactive state');
web.appState.currentState = 'background';
web.documentFixture.visibilityState = 'visible';
for (const notify of web.documentListeners) notify();
check(observed.at(-1) === false, 'visible document cannot override background app state');
web.appState.currentState = 'active';
for (const notify of web.appListeners) notify('active');
check(observed.at(-1) === true, 'foreground app and document notify active state');
web.appState.currentState = 'inactive';
check(web.captured.snapshot() === false, 'inactive app state is not foreground');
web.appState.currentState = null;
check(
  web.captured.snapshot() === true,
  'unknown initial native state permits a visible client document',
);
stop();
check(
  web.appListeners.size === 0 && web.documentListeners.size === 0,
  'cleanup removes both listeners',
);
check(
  web.removals().app === 1 && web.removals().document === 1,
  'cleanup removes each registered subscription once',
);
const observationCount = observed.length;
for (const notify of web.appListeners) notify('active');
for (const notify of web.documentListeners) notify();
check(observed.length === observationCount, 'cleaned subscriptions deliver no later events');

const first = () => {};
const second = () => {};
const stopFirst = web.captured.subscribe(first);
const stopSecond = web.captured.subscribe(second);
stopFirst();
check(
  web.appListeners.size === 1 && web.documentListeners.size === 1 && web.appListeners.has(second),
  'one consumer cleanup leaves the other consumer subscribed',
);
stopSecond();
check(
  web.appListeners.size === 0 && web.documentListeners.size === 0,
  'all consumer cleanup leaves no listeners',
);

const native = fixture('ios');
native.documentFixture.visibilityState = 'hidden';
check(native.captured.snapshot() === true, 'native foreground ignores document fixtures');
const stopNative = native.captured.subscribe(() => {});
check(
  native.appListeners.size === 1 && native.documentListeners.size === 0,
  'native subscribes only to AppState',
);
native.appState.currentState = 'background';
check(native.captured.snapshot() === false, 'native background snapshot is inactive');
native.appState.currentState = 'active';
check(native.captured.snapshot() === true, 'native foreground snapshot resumes');
stopNative();
check(
  native.appListeners.size === 0 && native.removals().document === 0,
  'native cleanup removes only its AppState listener',
);

const noDocument = fixture('web', false);
check(
  noDocument.initial === true && noDocument.captured.serverSnapshot() === false,
  'document-free client snapshot is safe and server snapshot remains inactive',
);
const stopNoDocument = noDocument.captured.subscribe(() => {});
check(
  noDocument.appListeners.size === 1 && noDocument.documentListeners.size === 0,
  'document-free subscription uses AppState only',
);
stopNoDocument();
check(noDocument.appListeners.size === 0, 'document-free subscription cleans up');

console.log(
  `PASS: ${checks} actual app-active snapshot, transition, subscription and cleanup assertions.`,
);
