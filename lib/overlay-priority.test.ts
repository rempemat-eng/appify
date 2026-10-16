import assert from 'node:assert/strict';
import { topGameOverlay } from './overlay-priority';

const quiet = {
  ready: true,
  hasPlayer: true,
  napping: false,
  welcome: false,
  recap: false,
  battle: false,
  alert: false,
  growth: false,
  guide: false,
  deck: false,
};
assert.equal(topGameOverlay(quiet), null);
assert.equal(
  topGameOverlay({ ...quiet, alert: true, guide: true, deck: true }),
  'alert',
  'Back should act on the visible raid alert, preserving a hidden guide and deck',
);
assert.equal(
  topGameOverlay({ ...quiet, battle: true, alert: true, deck: true }),
  'battle',
  'A battle cannot be dismissed by closing the deck behind it',
);
assert.equal(
  topGameOverlay({ ...quiet, welcome: true, recap: true, battle: true, alert: true, guide: true }),
  'welcome',
  'Return rewards remain the visible layer until acknowledged',
);
assert.equal(
  topGameOverlay({ ...quiet, napping: true, welcome: true }),
  'nap',
  'An active break remains visible above a previous reward',
);
assert.equal(topGameOverlay({ ...quiet, guide: true, deck: true }), 'guide');
assert.equal(topGameOverlay({ ...quiet, growth: true, guide: true }), 'growth');
assert.equal(topGameOverlay({ ...quiet, recap: true, deck: true }), 'recap');
assert.equal(
  topGameOverlay({ ...quiet, ready: false, hasPlayer: false, napping: true }),
  'loading',
);
assert.equal(topGameOverlay({ ...quiet, hasPlayer: false, napping: true }), 'onboarding');
assert.equal(topGameOverlay({ ...quiet, deck: true }), 'deck');
assert.deepEqual(quiet, {
  ready: true,
  hasPlayer: true,
  napping: false,
  welcome: false,
  recap: false,
  battle: false,
  alert: false,
  growth: false,
  guide: false,
  deck: false,
});
console.log(
  'PASS: visible overlay priority preserves hidden layers across alerts, battles, returns, guides and loading.',
);
