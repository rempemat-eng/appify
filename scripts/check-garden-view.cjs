/**
 * Checks the actual shared garden-view preference through its exported hook.
 * Run: node scripts/check-garden-view.cjs
 *
 * useSyncExternalStore captures the real subscribe/snapshot functions, while
 * AsyncStorage uses explicitly deferred reads and writes. This checks shared
 * state, race handling and persistence order, not React scheduling, DOM/native
 * rendering, real device storage or visual hydration behavior.
 */
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const ts = require('typescript');

const sourcePath = path.join(__dirname, '..', 'lib', 'garden-view.ts');
const source = ts.transpileModule(fs.readFileSync(sourcePath, 'utf8'), {
  compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
}).outputText;
const key = 'napattack-garden-view';
let checks = 0;
const check = (condition, message) => {
  assert.ok(condition, message);
  checks++;
};
const settle = () => new Promise((resolve) => setImmediate(resolve));
function deferred() {
  let resolve;
  let reject;
  const promise = new Promise((resolvePromise, rejectPromise) => {
    resolve = resolvePromise;
    reject = rejectPromise;
  });
  return { promise, resolve, reject };
}

function fixture() {
  const read = deferred();
  const readKeys = [];
  const writeCalls = [];
  let persisted = null;
  let captured;
  const storage = {
    getItem(storageKey) {
      readKeys.push(storageKey);
      return read.promise;
    },
    setItem(storageKey, value) {
      const completion = deferred();
      writeCalls.push({ key: storageKey, value, completion });
      return completion.promise.then(() => {
        persisted = value;
      });
    },
  };
  const moduleFixture = { exports: {} };
  vm.runInNewContext(
    source,
    {
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
        if (id === '@react-native-async-storage/async-storage')
          return { __esModule: true, default: storage };
        throw new Error(`Unexpected import: ${id}`);
      },
    },
    { filename: sourcePath },
  );
  return {
    read,
    readKeys,
    writeCalls,
    persisted: () => persisted,
    consumer() {
      const [initial, choose] = moduleFixture.exports.useGardenView();
      return { initial, choose, ...captured };
    },
  };
}

async function sharedConsumers() {
  const shared = fixture();
  const home = shared.consumer();
  const nap = shared.consumer();
  check(
    home.initial === 'flat' && nap.initial === 'flat',
    'consumers begin with the same flat snapshot',
  );
  check(shared.readKeys.length === 0, 'rendering the hook does not start storage hydration');
  check(home.choose === nap.choose, 'all consumers share the same choose function');
  const homeStates = [];
  const napStates = [];
  const stopHome = home.subscribe(() => homeStates.push(home.snapshot()));
  const stopNap = nap.subscribe(() => napStates.push(nap.snapshot()));
  check(
    shared.readKeys.length === 1 && shared.readKeys[0] === key,
    'subscriptions share one lazy storage read',
  );
  shared.read.resolve('tilt');
  await settle();
  check(
    home.snapshot() === 'tilt' && nap.snapshot() === 'tilt',
    'saved tilt hydrates every consumer',
  );
  check(
    homeStates.join() === 'tilt' && napStates.join() === 'tilt',
    'hydration notifies each active consumer once',
  );
  const later = shared.consumer();
  check(
    later.initial === 'tilt',
    'a later nap consumer immediately sees the shared loaded preference',
  );
  check(later.serverSnapshot() === 'flat', 'server snapshot remains flat after tilt hydration');
  home.choose('flat');
  check(
    home.snapshot() === 'flat' && nap.snapshot() === 'flat',
    'manual choice changes shared snapshots synchronously',
  );
  const notificationCount = homeStates.length;
  home.choose('flat');
  check(
    homeStates.length === notificationCount,
    'choosing the same value does not emit a redundant update',
  );
  stopNap();
  home.choose('tilt');
  check(
    homeStates.at(-1) === 'tilt' && napStates.at(-1) === 'flat',
    'unsubscribed consumer stops receiving preference notifications',
  );
  stopHome();
  const stoppedCount = homeStates.length;
  home.choose('flat');
  check(
    homeStates.length === stoppedCount,
    'no listeners receive updates after all consumers unsubscribe',
  );
  const returning = shared.consumer();
  const stopReturning = returning.subscribe(() => {});
  check(
    returning.initial === 'flat' && shared.readKeys.length === 1,
    'resubscribing preserves shared memory without rehydrating stale storage',
  );
  stopReturning();
}

async function hydrationRaces() {
  for (const [manual, stored] of [
    ['tilt', 'flat'],
    ['flat', 'tilt'],
  ]) {
    const race = fixture();
    const consumer = race.consumer();
    const states = [];
    const stop = consumer.subscribe(() => states.push(consumer.snapshot()));
    consumer.choose(manual);
    check(
      consumer.snapshot() === manual,
      `${manual}: manual choice is immediate while hydration is pending`,
    );
    race.read.resolve(stored);
    await settle();
    check(
      consumer.snapshot() === manual,
      `${manual}: late conflicting hydration cannot overwrite a manual choice`,
    );
    check(
      states.length === (manual === 'flat' ? 0 : 1),
      `${manual}: ignored hydration emits no extra notification`,
    );
    check(
      race.writeCalls.length === 1 && race.writeCalls[0].value === manual,
      `${manual}: even an unchanged explicit choice is persisted`,
    );
    check(
      consumer.serverSnapshot() === 'flat',
      `${manual}: manual choice never changes the server snapshot`,
    );
    race.writeCalls[0].completion.resolve();
    await settle();
    stop();
  }
}

async function unknownStoredValues() {
  for (const stored of [null, '', '2.5D', 'TILT', '"tilt"', 'flat']) {
    const unknown = fixture();
    const consumer = unknown.consumer();
    let notifications = 0;
    const stop = consumer.subscribe(() => {
      notifications++;
    });
    unknown.read.resolve(stored);
    await settle();
    check(
      consumer.snapshot() === 'flat',
      `${String(stored)}: unsupported or flat stored value preserves the flat default`,
    );
    check(
      notifications === 0 && unknown.writeCalls.length === 0,
      `${String(stored)}: ignored hydration neither emits nor rewrites storage`,
    );
    stop();
  }
}

async function storageFailures() {
  const failure = fixture();
  const consumer = failure.consumer();
  const states = [];
  const stop = consumer.subscribe(() => states.push(consumer.snapshot()));
  failure.read.reject(new Error('Test-only unavailable storage'));
  await settle();
  check(
    consumer.snapshot() === 'flat' && states.length === 0,
    'read failure leaves a stable flat preference',
  );
  consumer.choose('tilt');
  await settle();
  check(
    consumer.snapshot() === 'tilt' && failure.writeCalls.length === 1,
    'manual preference remains usable after read failure',
  );
  failure.writeCalls[0].completion.reject(new Error('Test-only failed write'));
  await settle();
  check(
    consumer.snapshot() === 'tilt' && states.join() === 'tilt',
    'failed persistence does not revert the visible preference or emit extra updates',
  );
  consumer.choose('flat');
  await settle();
  check(
    failure.writeCalls.length === 2 && failure.writeCalls[1].value === 'flat',
    'a failed write does not block the next explicit choice',
  );
  failure.writeCalls[1].completion.resolve();
  await settle();
  check(failure.persisted() === 'flat', 'the next successful choice persists normally');
  const another = failure.consumer();
  const stopAnother = another.subscribe(() => {});
  check(
    failure.readKeys.length === 1 && failure.writeCalls.length === 2,
    'new consumer does not automatically retry failed storage operations',
  );
  stop();
  stopAnother();
}

async function orderedWrites() {
  const ordered = fixture();
  const consumer = ordered.consumer();
  const stop = consumer.subscribe(() => {});
  ordered.read.resolve('flat');
  await settle();
  consumer.choose('tilt');
  consumer.choose('flat');
  consumer.choose('tilt');
  check(consumer.snapshot() === 'tilt', 'rapid choices immediately expose the latest preference');
  await settle();
  check(
    ordered.writeCalls.length === 1 && ordered.writeCalls[0].value === 'tilt',
    'only the first queued write starts while storage is deferred',
  );
  ordered.writeCalls[0].completion.resolve();
  await settle();
  check(
    ordered.persisted() === 'tilt' &&
      ordered.writeCalls.length === 2 &&
      ordered.writeCalls[1].value === 'flat',
    'second write starts only after the first settles',
  );
  ordered.writeCalls[1].completion.resolve();
  await settle();
  check(
    ordered.persisted() === 'flat' &&
      ordered.writeCalls.length === 3 &&
      ordered.writeCalls[2].value === 'tilt',
    'third write starts only after the second settles',
  );
  ordered.writeCalls[2].completion.resolve();
  await settle();
  check(
    ordered.persisted() === consumer.snapshot(),
    'final persisted preference agrees with the latest rapid choice',
  );
  check(
    ordered.writeCalls.every((write) => write.key === key),
    'every queued write uses the shared preference storage key',
  );
  stop();
}

async function main() {
  await sharedConsumers();
  await hydrationRaces();
  await unknownStoredValues();
  await storageFailures();
  await orderedWrites();
  console.log(
    `PASS: ${checks} actual garden-view shared-state, hydration, persistence-order and cleanup assertions.`,
  );
}
main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
