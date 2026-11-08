/** Bounded orchestration: wait for every started task and retain every failure. */
const { spawn } = require('node:child_process');
const os = require('node:os');

function concurrency(value = Math.min(2, os.availableParallelism())) {
  const jobs = Number(String(value));
  if (!Number.isSafeInteger(jobs) || jobs < 1 || jobs > 32)
    throw new Error('jobs must be an integer between 1 and 32');
  return jobs;
}
async function mapLimit(items, jobs, action) {
  const results = Array.from({ length: items.length });
  let next = 0;
  await Promise.all(
    Array.from({ length: Math.min(concurrency(jobs), items.length) }, async () => {
      while (next < items.length) {
        const index = next++;
        try {
          results[index] = { status: 'fulfilled', value: await action(items[index], index) };
        } catch (reason) {
          results[index] = { status: 'rejected', reason };
        }
      }
    }),
  );
  return results;
}
function runProcess(command, args, options = {}) {
  return new Promise((resolve) => {
    let child;
    try {
      child = spawn(command, args, {
        ...options,
        detached: process.platform !== 'win32',
        stdio: ['ignore', 'pipe', 'pipe'],
      });
    } catch (error) {
      resolve({ status: null, error, stdout: '', stderr: '' });
      return;
    }
    let stdout = '',
      stderr = '',
      error;
    let killTimer;
    function terminate() {
      if (!child.pid) return;
      const kill = (signal) => {
        try {
          if (process.platform === 'win32') child.kill(signal);
          else process.kill(-child.pid, signal);
        } catch (got) {
          if (got.code !== 'ESRCH') error = got;
        }
      };
      kill('SIGTERM');
      killTimer ??= setTimeout(() => kill('SIGKILL'), 250);
    }
    let bytes = 0;
    const limit = options.maxBuffer ?? 8 * 1024 * 1024;
    const append = (key, chunk) => {
      bytes += chunk.length;
      if (bytes > limit) {
        error = new Error('command output exceeded maxBuffer');
        terminate();
        return;
      }
      if (key === 'stdout') stdout += chunk;
      else stderr += chunk;
    };
    child.stdout.on('data', (chunk) => append('stdout', chunk));
    child.stderr.on('data', (chunk) => append('stderr', chunk));
    child.on('error', (got) => {
      error = got;
    });
    const timer = setTimeout(() => {
      error = new Error('command timed out');
      terminate();
    }, options.timeout ?? 900_000);
    child.on('close', (status, signal) => {
      clearTimeout(timer);
      clearTimeout(killTimer);
      resolve({ status, signal, error, stdout, stderr });
    });
  });
}
module.exports = { concurrency, mapLimit, runProcess };
