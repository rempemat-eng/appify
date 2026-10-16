import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const modulePath = fileURLToPath(new URL('./bilt.ts', import.meta.url));
const withoutBackend = { ...process.env };
delete withoutBackend.EXPO_PUBLIC_BILT_URL;
delete withoutBackend.EXPO_PUBLIC_BILT_ANON_KEY;

// Import the actual startup module in a fresh process, not a replacement client.
// No backend credentials, saved game or network connection are needed.
const script = `
  const assert = require('node:assert/strict');
  let requests = 0;
  globalThis.fetch = () => {
    requests++;
    throw new Error('Unexpected network request in local startup');
  };
  const { bilt, backendConfigured, backendUnavailableMessage } = require(${JSON.stringify(modulePath)});
  assert.equal(bilt, null);
  assert.equal(backendConfigured, false);
  assert.ok(backendUnavailableMessage.includes('not configured'));
  setImmediate(() => {
    assert.equal(requests, 0);
    console.log('local startup imported without credentials or network requests');
  });
`;
for (const env of [
  withoutBackend,
  { ...withoutBackend, EXPO_PUBLIC_BILT_URL: '', EXPO_PUBLIC_BILT_ANON_KEY: '' },
  { ...withoutBackend, EXPO_PUBLIC_BILT_URL: '   ', EXPO_PUBLIC_BILT_ANON_KEY: '   ' },
  { ...withoutBackend, EXPO_PUBLIC_BILT_URL: 'https://unconfigured.example.invalid' },
  { ...withoutBackend, EXPO_PUBLIC_BILT_ANON_KEY: 'test-only-unused-key' },
  {
    ...withoutBackend,
    EXPO_PUBLIC_BILT_URL: 'not-a-url',
    EXPO_PUBLIC_BILT_ANON_KEY: 'test-only-unused-key',
  },
]) {
  const result = spawnSync(process.execPath, ['--import', 'tsx', '-e', script], {
    env,
    encoding: 'utf8',
    timeout: 10000,
  });
  assert.equal(result.status, 0, result.stderr || result.error?.message);
  assert.ok(result.stdout.includes('local startup imported'));
}
console.log(
  'PASS: actual backend startup imports safely with absent, empty, whitespace, partial and malformed settings.',
);
