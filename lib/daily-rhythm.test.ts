import assert from 'node:assert/strict';
import {
  freshRhythm,
  ownTimeMinutes,
  parseRhythmTime,
  plannedMinutes,
  restoreRhythm,
  rhythmStatus,
  validateRhythm,
} from './daily-rhythm';

process.env.TZ = 'Europe/London';
const at = (day: number, hour: number, minute = 0, month = 9) =>
  new Date(2026, month, day, hour, minute).getTime();
const plan = { ...freshRhythm(), enabled: true };
assert.deepEqual(validateRhythm(plan), []);
assert.equal(freshRhythm().enabled, false);
assert.equal(parseRhythmTime('00:00'), 0);
assert.equal(parseRhythmTime('23:59'), 1439);
for (const bad of ['24:00', '12:60', '7:00', '07:0', '-1:00', 'aa:bb', ''])
  assert.equal(parseRhythmTime(bad), null);
assert.equal(plannedMinutes(plan.weekdays.rest), 480);
assert.equal(ownTimeMinutes(plan.weekdays), 480);
assert.equal(ownTimeMinutes(plan.weekends), 930);
assert.deepEqual(rhythmStatus(freshRhythm(), at(16, 10)), { current: null, next: null });
assert.equal(rhythmStatus(plan, at(16, 10)).current, 'focus');
assert.deepEqual(rhythmStatus(plan, at(16, 10)).next, { period: 'own', at: at(16, 17) });
assert.equal(rhythmStatus(plan, at(16, 23)).current, 'rest');
// Early Saturday still belongs to Friday's 23:00–07:00 Rest window.
assert.deepEqual(rhythmStatus(plan, at(17, 1)).next, { period: 'own', at: at(17, 7) });
assert.equal(rhythmStatus(plan, at(17, 7, 30)).current, 'own');
assert.deepEqual(rhythmStatus(plan, at(17, 10)).next, { period: 'rest', at: at(17, 23, 30) });
// Monday morning still uses Sunday's weekend Rest window.
assert.equal(rhythmStatus(plan, at(19, 7, 30)).current, 'rest');
assert.deepEqual(rhythmStatus(plan, at(19, 7, 30)).next, { period: 'own', at: at(19, 8) });

const sameTime = freshRhythm();
sameTime.weekdays.rest.end = sameTime.weekdays.rest.start;
assert.match(validateRhythm(sameTime)[0], /under 24 hours/);
const overlap = freshRhythm();
overlap.weekdays.focus.start = '06:30';
assert.match(validateRhythm(overlap)[0], /overlaps/);
const crossBoundary = freshRhythm();
crossBoundary.weekends.focus = { enabled: true, start: '06:00', end: '08:00' };
assert.match(validateRhythm(crossBoundary)[0], /Friday Rest overlaps Saturday Focus/);
const weekBoundary = freshRhythm();
weekBoundary.weekdays.focus.start = '07:30';
assert.match(validateRhythm(weekBoundary)[0], /Sunday Rest overlaps Monday Focus/);
const touching = freshRhythm();
touching.weekdays.focus.start = '07:00';
touching.weekends.rest.end = '07:00';
assert.deepEqual(validateRhythm(touching), []);

assert.deepEqual(restoreRhythm(JSON.parse(JSON.stringify(plan))), plan);
assert.equal(restoreRhythm(undefined), null);
assert.equal(restoreRhythm({ ...plan, version: 2 }), null);
assert.equal(restoreRhythm({ ...plan, timezone: 'UTC' }), null);
assert.equal(restoreRhythm({ ...plan, weekdays: { rest: null } }), null);
assert.equal(restoreRhythm(overlap), null);
// Clock changes use calendar-local endpoints rather than fixed elapsed hours.
const autumn = rhythmStatus(plan, at(25, 1, 30));
assert.equal(autumn.current, 'rest');
assert.equal(autumn.next?.at, at(25, 8));
const spring = rhythmStatus(plan, at(29, 0, 30, 2));
assert.equal(spring.current, 'rest');
assert.equal(spring.next?.at, at(29, 8, 0, 2));
// No windows means unrestricted Own time, not a 24-hour lock or undefined status.
const noWindows = freshRhythm();
noWindows.enabled = true;
for (const group of ['weekdays', 'weekends'] as const)
  for (const period of ['rest', 'focus'] as const) noWindows[group][period].enabled = false;
assert.deepEqual(rhythmStatus(noWindows, at(16, 10)), { current: 'own', next: null });
assert.equal(ownTimeMinutes(noWindows.weekdays), 1440);
console.log(
  'PASS: rhythm validation, overnight weekday/weekend ownership, overlaps, week wrap, local DST, opt-in defaults and safe restore.',
);
