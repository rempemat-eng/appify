import type { Point } from './garden-path';
import { regionBounds, regionTiles, TILE, type RegionId, type RegionTile } from './region-walk';
import { regionPoint, travelPoints, travelRoute } from './world-places';
import { moveTo, type WorldSpot } from './world-save';

/** Same viewport-aware preload reach as AtlasWalk, never a second zone catalogue. */
export function mountedNeighbours(
  region: RegionId,
  here: string,
  view: Pick<CameraWindow, 'width' | 'height' | 'scale'>,
): RegionTile[] {
  validateViewport(view);
  const tiles = regionTiles(region);
  const centre = tiles.find((tile) => tile.id === here);
  const reachX = 1 + Math.ceil(view.width / (2 * TILE.width * view.scale));
  const reachY = 1 + Math.ceil(view.height / (2 * TILE.height * view.scale));
  return centre
    ? tiles.filter(
        (tile) =>
          Math.abs(tile.col - centre.col) <= reachX && Math.abs(tile.row - centre.row) <= reachY,
      )
    : [];
}

/** Each physical border once. Distant regions and the hut door are not foot edges. */
export function regionEdges(
  region: RegionId,
): { a: RegionTile; b: RegionTile; direction: 'east' | 'south' }[] {
  const tiles = regionTiles(region);
  return tiles.flatMap((a) =>
    tiles.flatMap((b) => {
      const direction =
        b.col === a.col + 1 && b.row === a.row
          ? 'east'
          : b.row === a.row + 1 && b.col === a.col
            ? 'south'
            : null;
      return direction ? [{ a, b, direction }] : [];
    }),
  );
}

export type CameraWindow = Readonly<{
  width: number;
  height: number;
  scale: number;
  focusY?: number;
  padBottom?: number;
}>;

function validateViewport(view: Pick<CameraWindow, 'width' | 'height' | 'scale'>): void {
  if (
    ![view.width, view.height, view.scale].every(Number.isFinite) ||
    view.width <= 0 ||
    view.height <= 0 ||
    view.scale <= 0
  )
    throw new RangeError('Invalid world viewport');
}

/** Same continuous region-space camera as AtlasWalk; the renderer snaps pixels. */
export function cameraOffset(region: RegionId, point: Point, view: CameraWindow): Point {
  validateViewport(view);
  const focusY = view.focusY ?? 0.55;
  const padBottom = view.padBottom ?? 0;
  if (
    ![point.x, point.y, focusY, padBottom].every(Number.isFinite) ||
    focusY < 0 ||
    focusY > 1 ||
    padBottom < 0
  )
    throw new RangeError('Invalid world camera geometry');
  const bounds = regionBounds(region);
  const regionW = bounds.width * view.scale;
  const regionH = bounds.height * view.scale;
  return {
    x:
      regionW <= view.width
        ? (regionW - view.width) / 2
        : Math.max(0, Math.min(regionW - view.width, point.x * view.scale - view.width / 2)),
    y:
      regionH <= view.height - padBottom
        ? (regionH - view.height + padBottom) / 2
        : Math.max(
            0,
            Math.min(
              regionH - view.height + padBottom,
              point.y * view.scale - view.height * focusY,
            ),
          ),
  };
}

/** Taps and drawing share the same camera origin, including a raised place card. */
export function screenToWorld(
  region: RegionId,
  point: Point,
  view: CameraWindow,
  screen: Point,
): Point {
  if (![screen.x, screen.y].every(Number.isFinite)) throw new RangeError('Invalid screen point');
  const camera = cameraOffset(region, point, view);
  return { x: (screen.x + camera.x) / view.scale, y: (screen.y + camera.y) / view.scale };
}

// Tickets are ephemeral identities, not save fields, counters or navigation effects.
export type JourneyTicket = Readonly<{
  /** The scene stays in its origin region until the whole trip arrives. */
  from: RegionId;
  to: RegionId;
  at: Readonly<Point>;
  /** Authored line stops, excluding the origin and including the destination. */
  legs: readonly RegionId[];
  leg: number;
}>;
export type JourneyState = Readonly<{ pending: JourneyTicket | null }>;
export const idleJourney = (): JourneyState => ({ pending: null });

/** Caller supplies the existing live focused/active/awake guards, not a new rule. */
export function beginJourney(
  state: JourneyState,
  from: RegionId,
  to: RegionId,
  enabled: boolean,
): JourneyState {
  const source = travelPoints[from];
  const destination = travelPoints[to];
  if (!enabled || from === to || !source || !destination) return state;
  const legs = travelRoute(from, to);
  if (!legs.length) return state;
  return {
    pending: Object.freeze({
      from,
      to,
      at: Object.freeze(regionPoint(destination)),
      legs: Object.freeze([...legs]),
      leg: 0,
    }),
  };
}

/**
 * Back/blur/background cancels the whole trip. An individual leg's cleanup passes
 * its captured ticket so an old cleanup cannot cancel the next leg or a new trip.
 */
export function cancelJourney(state: JourneyState, ticket?: JourneyTicket): JourneyState {
  return ticket && state.pending !== ticket ? state : idleJourney();
}

type JourneyResult = Readonly<{ state: JourneyState; arrival: WorldSpot | null }>;
type JourneyEligibility = Readonly<{ region: RegionId; enabled: boolean }>;

function resolveJourney(
  state: JourneyState,
  ticket: JourneyTicket,
  current: JourneyEligibility,
  saved: WorldSpot | null,
  skip: boolean,
): JourneyResult {
  if (state.pending !== ticket) return { state, arrival: null };
  const next = cancelJourney(state);
  if (!current.enabled || current.region !== ticket.from) return { state: next, arrival: null };
  if (!skip && ticket.leg + 1 < ticket.legs.length) {
    return {
      state: { pending: Object.freeze({ ...ticket, leg: ticket.leg + 1 }) },
      arrival: null,
    };
  }
  const arrival = moveTo(saved, ticket.to, ticket.at.x, ticket.at.y);
  return { state: next, arrival: { ...arrival, visited: [...arrival.visited] } };
}

/**
 * Finish only this captured leg. Publish result.state synchronously before applying
 * an arrival or mounting the next leg; every advance has a fresh ticket identity.
 */
export function finishJourney(
  state: JourneyState,
  ticket: JourneyTicket,
  current: JourneyEligibility,
  saved: WorldSpot | null,
): JourneyResult {
  return resolveJourney(state, ticket, current, saved, false);
}

/** SKIP consumes the current leg and arrives once at the whole trip's destination. */
export function skipJourney(
  state: JourneyState,
  ticket: JourneyTicket,
  current: JourneyEligibility,
  saved: WorldSpot | null,
): JourneyResult {
  return resolveJourney(state, ticket, current, saved, true);
}
