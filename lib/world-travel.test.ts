import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { runInNewContext } from 'node:vm';
import { regionLayout } from './zone-maps';
import { regionBounds, regionTiles, tileOrigin, TILE, type RegionId } from './region-walk';
import { regionPoint, travelPoints, travelRoute } from './world-places';
import {
  cameraOffset,
  mountedNeighbours,
  regionEdges,
  screenToWorld,
  beginJourney,
  cancelJourney,
  finishJourney,
  idleJourney,
  skipJourney,
  type JourneyTicket,
} from './world-travel';

let checks = 0;
const ok = (v: unknown, label: string) => {
  assert.ok(v, label);
  checks++;
};
const regions = Object.keys(regionLayout).filter((id): id is RegionId =>
  Object.prototype.hasOwnProperty.call(regionLayout, id),
);
// Execute only the actual pure camera worklet body at a substituted boundary.
// This catches drift while Claude's renderer still owns the inline calculation.
const cameraBody = readFileSync(
  new URL('../components/atlas-walk.tsx', import.meta.url),
  'utf8',
).match(/const cameraStyle = useAnimatedStyle\(\(\) => \{([\s\S]*?)\n  \}\);/)?.[1];
assert.ok(cameraBody, 'AtlasWalk camera worklet must be covered or its adapter updated');
for (const region of regions) {
  const tiles = regionTiles(region);
  const bounds = regionBounds(region);
  const all = JSON.stringify(tiles);
  for (const tile of tiles) {
    const neighbours = mountedNeighbours(region, tile.id);
    ok(
      neighbours.length > 0 && neighbours.length <= 9,
      `${region}/${tile.id}: bounded 3x3 neighbourhood`,
    );
    ok(
      neighbours.some((n) => n.id === tile.id),
      'current zone remains mounted',
    );
    for (const other of tiles)
      ok(
        neighbours.some((n) => n.id === other.id) ===
          (Math.abs(other.col - tile.col) <= 1 && Math.abs(other.row - tile.row) <= 1),
        'neighbours derive from the actual grid, including diagonals',
      );
    const o = tileOrigin(region, tile);
    ok(
      o.x >= 0 &&
        o.y >= 0 &&
        o.x + TILE.width <= bounds.width &&
        o.y + TILE.height <= bounds.height,
      'negative layout coordinates normalize into region pixels',
    );
  }
  ok(
    mountedNeighbours(region, 'not-a-zone').length === 0,
    'unknown zone does not mount unrelated art',
  );
  const edges = regionEdges(region);
  ok(
    new Set(edges.map(({ a, b }) => [a.id, b.id].sort().join(':'))).size === edges.length,
    'each physical edge occurs once',
  );
  if (tiles.length === 1) ok(edges.length === 0, 'singleton region has no imaginary foot edge');
  for (const { a, b, direction } of edges) {
    const o = tileOrigin(region, a);
    const border =
      direction === 'east'
        ? { x: o.x + TILE.width, y: o.y + TILE.height / 2 }
        : { x: o.x + TILE.width / 2, y: o.y + TILE.height };
    const axis = direction === 'east' ? 'x' : 'y';
    const other = axis === 'x' ? 'y' : 'x';
    ok(
      mountedNeighbours(region, a.id).some((t) => t.id === b.id) &&
        mountedNeighbours(region, b.id).some((t) => t.id === a.id),
      'both sides are pre-mounted across each border',
    );
    for (const width of [320, 402, 768])
      for (const scale of [1, 4 / 3, 2])
        for (const padBottom of [0, 240]) {
          const view = { width, height: 640, scale, padBottom, focusY: padBottom ? 0.3 : 0.55 };
          const left = cameraOffset(region, { ...border, [axis]: border[axis] - 0.01 }, view);
          const right = cameraOffset(region, { ...border, [axis]: border[axis] + 0.01 }, view);
          ok(
            Math.abs(right[axis] - left[axis]) <= 0.02 * scale + 1e-8 &&
              right[other] === left[other],
            'crossing a tile border cannot reset the camera origin',
          );
          const centre = cameraOffset(region, border, view);
          const rendered = runInNewContext(`(() => {${cameraBody}})()`, {
            regionW: bounds.width * scale,
            regionH: bounds.height * scale,
            width,
            height: view.height,
            padBottom,
            focusY: view.focusY,
            px: { value: border.x },
            py: { value: border.y },
            u: scale,
          });
          ok(
            rendered.transform[0].translateX === -Math.round(centre.x) &&
              rendered.transform[1].translateY === -Math.round(centre.y),
            'actual camera worklet and pure model agree after the renderer pixel snap',
          );
          const tap = screenToWorld(region, border, view, {
            x: border.x * scale - centre.x,
            y: border.y * scale - centre.y,
          });
          ok(
            Math.abs(tap.x - border.x) < 1e-8 && Math.abs(tap.y - border.y) < 1e-8,
            'tap conversion shares the rendered camera with card padding',
          );
        }
  }
  ok(JSON.stringify(tiles) === all, 'geometry inspection never mutates generated data');
}
for (const view of [
  { width: 0, height: 640, scale: 1 },
  { width: 320, height: 640, scale: 0 },
  { width: 320, height: 640, scale: NaN },
  { width: 320, height: 640, scale: 1, focusY: 2 },
  { width: 320, height: 640, scale: 1, padBottom: -1 },
]) {
  assert.throws(() => cameraOffset('valley', { x: 0, y: 0 }, view), RangeError);
  checks++;
}
const destinations = regions.filter((r) => travelPoints[r]);
for (const from of destinations)
  for (const to of destinations) {
    let state = beginJourney(idleJourney(), from, to, true);
    if (from === to) {
      ok(!state.pending, 'same-region selection is not a vehicle trip');
      continue;
    }
    const ticket = state.pending!;
    const saved = { region: from, ...regionPoint(travelPoints[from]!), visited: ['town'] };
    const original = JSON.stringify(saved);
    const expected = regionPoint(travelPoints[to]!);
    // SKIP always resolves the whole trip; natural completion is per leg below.
    const complete = skipJourney(state, ticket, { region: from, enabled: true }, saved);
    ok(
      complete.arrival?.region === to &&
        complete.arrival.x === Math.round(expected.x) &&
        complete.arrival.y === Math.round(expected.y),
      'journeys use the existing generated arrival station',
    );
    ok(
      complete.arrival?.visited.includes('town') && !complete.state.pending,
      'arrival keeps visits and consumes the ticket',
    );
    ok(
      !finishJourney(complete.state, ticket, { region: from, enabled: true }, saved).arrival,
      'late timer after finish cannot arrive twice',
    );
    ok(
      !skipJourney(complete.state, ticket, { region: from, enabled: true }, saved).arrival,
      'skip after timer cannot arrive twice',
    );
    ok(
      skipJourney(state, ticket, { region: from, enabled: true }, saved).arrival?.region === to,
      'skip uses the same arrival',
    );
    ok(
      !finishJourney(cancelJourney(state), ticket, { region: from, enabled: true }, saved).arrival,
      'Back/background/unmount cancellation rejects queued callbacks',
    );
    ok(
      !finishJourney(state, ticket, { region: from, enabled: false }, saved).arrival,
      'late completion rechecks active/focused/awake eligibility',
    );
    ok(
      !finishJourney(state, ticket, { region: to, enabled: true }, saved).arrival,
      'another region entry rejects a stale source',
    );
    ok(
      !finishJourney(state, { ...ticket }, { region: from, enabled: true }, saved).arrival,
      'a structural ticket copy cannot impersonate this trip',
    );
    const replacement = beginJourney(state, from, to, true);
    const stale = finishJourney(replacement, ticket, { region: from, enabled: true }, saved);
    ok(
      !stale.arrival && stale.state === replacement,
      'an old callback cannot cancel or complete a replacement trip',
    );
    ok(
      !finishJourney(
        beginJourney(idleJourney(), from, to, true),
        ticket,
        { region: from, enabled: true },
        saved,
      ).arrival,
      'remounting does not reuse a ticket identity',
    );
    ok(
      beginJourney(state, from, to, false) === state,
      'disabled requests leave an active trip unchanged',
    );
    ok(JSON.stringify(saved) === original, 'trip decisions never mutate existing world history');
  }
ok(
  !beginJourney(idleJourney(), 'home', 'valley', true).pending,
  'hut door is not a fabricated station',
);
ok(
  !beginJourney(idleJourney(), 'valley', 'home', true).pending,
  'hut remains a door, not a vehicle destination',
);
let legChecks = 0;
for (const from of destinations)
  for (const to of destinations) {
    if (from === to) continue;
    let state = beginJourney(idleJourney(), from, to, true);
    const route = travelRoute(from, to);
    const saved = {
      region: from,
      ...regionPoint(travelPoints[from]!),
      visited: ['town', travelPoints[to]!.zone],
    };
    Object.freeze(saved.visited);
    Object.freeze(saved);
    const savedBefore = JSON.stringify(saved);
    const live = { region: from, enabled: true };
    let arrivals = 0;
    const oldTickets: JourneyTicket[] = [];
    for (let leg = 0; leg < route.length; leg++) {
      legChecks++;
      const ticket = state.pending!;
      ok(ticket.leg === leg, 'current ticket identifies the authored leg');
      assert.deepEqual(ticket.legs, route, 'route is derived from current lines');
      checks++;
      ok(Object.isFrozen(ticket) && Object.isFrozen(ticket.legs), 'ticket and route immutable');
      ok(Object.isFrozen(ticket.at), 'arrival point immutable');
      ok(ticket.from === from && ticket.to === to, 'origin/final destination survive changes');

      for (const stale of oldTickets) {
        const ignored = finishJourney(state, stale, live, saved);
        ok(ignored.state === state && !ignored.arrival, 'previous leg cannot advance this leg');
        const ignoredSkip = skipJourney(state, stale, live, saved);
        ok(
          ignoredSkip.state === state && !ignoredSkip.arrival,
          'previous leg SKIP cannot complete the trip',
        );
        ok(cancelJourney(state, stale) === state, 'old leg cleanup cannot cancel current leg');
      }
      ok(
        !finishJourney(state, { ...ticket }, live, saved).arrival,
        'copied leg ticket cannot finish',
      );
      ok(
        finishJourney(state, { ...ticket }, live, saved).state === state,
        'copied leg ticket cannot advance either',
      );
      const cancelled = cancelJourney(state, ticket);
      ok(!cancelled.pending, 'leaving any leg consumes its ticket');
      ok(
        !finishJourney(cancelled, ticket, live, saved).arrival &&
          !finishJourney(cancelled, ticket, live, saved).state.pending,
        'queued completion after leaving cannot restore an intermediate trip or arrive',
      );
      for (const reason of ['background', 'blur', 'resting', 'battle', 'pending return']) {
        const blocked = finishJourney(state, ticket, { region: from, enabled: false }, saved);
        ok(!blocked.state.pending && !blocked.arrival, `${reason} invalidates every leg`);
        ok(
          !finishJourney(blocked.state, ticket, live, saved).state.pending,
          `${reason} cannot resume through an old callback`,
        );
        const skipped = skipJourney(state, ticket, { region: from, enabled: false }, saved);
        ok(!skipped.state.pending && !skipped.arrival, `${reason} also blocks SKIP`);
      }
      const moved = finishJourney(state, ticket, { region: to, enabled: true }, saved);
      ok(!moved.state.pending && !moved.arrival, 'changed live origin rejects current leg');
      const replacement = beginJourney(state, from, to, true);
      ok(replacement.pending !== ticket, 'same-destination replacement gets new identity');
      ok(
        finishJourney(replacement, ticket, live, saved).state === replacement,
        'replaced callback cannot advance the new trip',
      );
      ok(cancelJourney(replacement, ticket) === replacement, 'old cleanup preserves replacement');
      const other = destinations.find((r) => r !== from && r !== to)!;
      const rerouted = beginJourney(state, from, other, true);
      ok(
        skipJourney(rerouted, ticket, live, saved).state === rerouted &&
          finishJourney(rerouted, ticket, live, saved).state === rerouted,
        'old destination callbacks cannot affect a differently routed trip',
      );
      ok(
        skipJourney(rerouted, rerouted.pending!, live, saved).arrival?.region === other,
        'only the replacement destination can arrive',
      );
      const remounted = beginJourney(idleJourney(), from, to, true);
      ok(
        finishJourney(remounted, ticket, live, saved).state === remounted,
        'remount rejects every old leg callback',
      );

      // Both event orders: SKIP wins, or the natural completion wins first.
      const skip = skipJourney(state, ticket, live, saved);
      ok(skip.arrival?.region === to && !skip.state.pending, 'SKIP at any leg ends whole trip');
      ok(
        !finishJourney(skip.state, ticket, live, saved).arrival &&
          !finishJourney(skip.state, ticket, live, saved).state.pending,
        'completion delivered after SKIP cannot arrive again or restore trip',
      );
      ok(!skipJourney(skip.state, ticket, live, saved).arrival, 'duplicate SKIP is harmless');
      const natural = finishJourney(state, ticket, live, saved);
      if (leg < route.length - 1) {
        ok(!natural.arrival, 'intermediate leg never writes a world arrival');
        ok(
          natural.state.pending !== ticket && natural.state.pending?.leg === leg + 1,
          'advancing creates a new current-leg identity',
        );
        ok(
          skipJourney(natural.state, ticket, live, saved).state === natural.state,
          'SKIP queued by previous leg cannot finish the new leg',
        );
        const liveSkip = skipJourney(natural.state, natural.state.pending!, live, saved);
        ok(liveSkip.arrival?.region === to, 'the new leg can still SKIP the whole trip');
      } else {
        arrivals += natural.arrival ? 1 : 0;
        ok(natural.arrival?.region === to && !natural.state.pending, 'last leg arrives once');
        ok(
          !skipJourney(natural.state, ticket, live, saved).arrival,
          'SKIP after final completion cannot arrive twice',
        );
        assert.deepEqual(natural.arrival?.visited, skip.arrival?.visited);
        checks++;
        // Returned history is detached even when the destination was already visited.
        natural.arrival?.visited.push('consumer-only');
        ok(JSON.stringify(saved) === savedBefore, 'returned arrival cannot mutate saved history');
      }
      ok(
        finishJourney(natural.state, ticket, live, saved).state === natural.state,
        'duplicate completion cannot advance two legs',
      );
      ok(cancelJourney(natural.state, ticket) === natural.state, 'consumed cleanup cannot rewind');
      oldTickets.push(ticket);
      state = natural.state;
    }
    ok(arrivals === 1, 'one whole-trip arrival across all natural leg completions');
    ok(JSON.stringify(saved) === savedBefore, 'per-leg decisions never mutate saved history');
  }
console.log(
  `World travel model: ${checks} assertions, including ${legChecks} authored leg positions; renderer integration not claimed.`,
);
