import assert from 'node:assert/strict';
import { recogniseNap, restRecognitionRules as R } from '@/lib/rest-recognition';
import { REST_RECOGNITION_DEFAULT } from '@/lib/rest-flag-default';

assert.equal(REST_RECOGNITION_DEFAULT, false, 'rest recognition stays off until Matt decides');

const base = { foreground: false, foregroundForMs: 0, creditedThisNap: 0, creditedToday: 0 };

// The phone was put down: the whole gap counts, as today (5 real minutes on the demo clock).
assert.deepEqual(recogniseNap({ ...base, wallMs: 5 * 60_000 }), {
  minutes: 300,
  reanchor: false,
  reason: 'rest',
});
// A live tick in the grace after starting the nap counts.
assert.equal(
  recogniseNap({ ...base, wallMs: 1000, foreground: true, foregroundForMs: 10_000 }).minutes,
  1,
);
// The game left open on the nap screen past the grace does not.
assert.deepEqual(
  recogniseNap({
    ...base,
    wallMs: 1000,
    foreground: true,
    foregroundForMs: R.foregroundGraceMs + 1,
  }),
  {
    minutes: 0,
    reanchor: true,
    reason: 'foreground',
  },
);
// Coming back after a long rest: the app has only just come to the front, so the gap counts.
assert.equal(
  recogniseNap({ ...base, wallMs: 3 * 3600_000, foreground: true, foregroundForMs: 0 }).reason,
  'nap-cap',
  'a three-hour demo gap meets the per-nap cap on the demo clock',
);
// A clock set back re-anchors instead of freezing the nap.
assert.deepEqual(recogniseNap({ ...base, wallMs: -60_000 }), {
  minutes: 0,
  reanchor: true,
  reason: 'clock-back',
});
// A clock set forward with the app open moves the foreground timer too: nothing is paid.
assert.equal(
  recogniseNap({ ...base, wallMs: 3600_000, foreground: true, foregroundForMs: 3600_000 + 20_000 })
    .minutes,
  0,
);
// Caps: per nap and per day, never negative.
assert.equal(
  recogniseNap({ ...base, wallMs: 100_000, creditedThisNap: R.maxNapMinutes - 10 }).minutes,
  10,
);
assert.equal(
  recogniseNap({ ...base, wallMs: 100_000, creditedToday: R.maxDayMinutes - 4 }).minutes,
  4,
);
assert.equal(
  recogniseNap({ ...base, wallMs: 100_000, creditedToday: R.maxDayMinutes + 50 }).minutes,
  0,
);
console.log('Rest recognition checks passed.');
