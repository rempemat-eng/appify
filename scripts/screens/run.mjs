import { spawn } from 'node:child_process';
import { mkdir, rm } from 'node:fs/promises';

// Export a local-only build even if the developer's shell has backend settings.
const env = {
  ...process.env,
  TZ: 'UTC',
  EXPO_OFFLINE: '1',
  EXPO_NO_DOTENV: '1',
  EXPO_PUBLIC_BILT_URL: '',
  EXPO_PUBLIC_BILT_ANON_KEY: '',
};
const run = (args) =>
  new Promise((resolve, reject) => {
    const child = spawn(process.execPath, args, { env, stdio: 'inherit' });
    const stop = (signal) => child.kill(signal);
    const interrupt = () => stop('SIGINT');
    const terminate = () => stop('SIGTERM');
    process.once('SIGINT', interrupt);
    process.once('SIGTERM', terminate);
    child.once('error', reject);
    child.once('exit', (code, signal) => {
      process.removeListener('SIGINT', interrupt);
      process.removeListener('SIGTERM', terminate);
      resolve(signal ? 1 : (code ?? 1));
    });
  });

// This directory contains generated review output only; never mix old captures.
await rm('artifacts/screens', { recursive: true, force: true });
await mkdir('artifacts/screens', { recursive: true });
const build = await run(['node_modules/expo/bin/cli', 'export', '-p', 'web', '--clear']);
process.exitCode =
  build ||
  (await run([
    'node_modules/@playwright/test/cli.js',
    'test',
    '--config=playwright.screens.config.ts',
    ...process.argv.slice(2),
  ]));
