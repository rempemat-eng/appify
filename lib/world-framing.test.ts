import assert from 'node:assert/strict';
import { worldPreviewFrame } from './world-framing';
import { worldIds } from './world-maps';

// Layout geometry only: this does not substitute for visual or device testing.
for (const [width, height] of [
  [320, 132],
  [600, 176],
  [600, 132],
  [320, 176],
] as const) {
  const innerWidth = width - 4;
  const innerHeight = height - 4;
  for (const world of worldIds) {
    const frame = worldPreviewFrame(world, innerWidth, innerHeight);
    assert.ok(frame.landmark, `${world} has an existing preview landmark`);
    assert.ok(
      frame.height >= innerHeight,
      `${world} preview preserves its requested minimum height`,
    );
    assert.ok(frame.top >= 0, `${world} camera stays above world origin`);
    assert.ok(frame.top + frame.height <= frame.worldHeight + 1, `${world} camera stays in world`);
    const landmarkTop = frame.landmark.top - frame.top;
    const landmarkBottom = landmarkTop + frame.landmark.height;
    assert.ok(landmarkTop >= 0, `${world} landmark roof fits at ${width}`);
    assert.ok(landmarkBottom <= frame.height, `${world} landmark base fits at ${width}`);
    assert.ok(frame.landmark.left >= 0, `${world} landmark left fits at ${width}`);
    assert.ok(
      frame.landmark.left + frame.landmark.width <= innerWidth,
      `${world} landmark right fits`,
    );
  }
}
for (const world of worldIds) {
  const short = worldPreviewFrame(world, 316, 20);
  assert.ok(
    short.top >= 0 && short.top + short.height <= short.worldHeight + 1,
    'short crop stays in world',
  );
  const tall = worldPreviewFrame(world, 316, 1000);
  assert.equal(tall.top, 0, 'a viewport taller than the world starts at the world origin');
}
console.log('PASS: mission previews keep complete landmarks visible at supported layout sizes.');
