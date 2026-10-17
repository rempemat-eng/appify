import type { Player, Raid, Saved } from './game';

// The storage key stays stable. Versions describe its JSON payload, not a new
// account or storage location. Releases before this module were unversioned.
export const GAME_SAVE_KEY = 'screenagotchi-v1';
export const SAVE_VERSION = 1;

type RecordValue = Record<string, unknown>;
type Shape =
  | true
  | { fields: Record<string, Shape>; identity?: string[] }
  | { items: Shape; identity?: string[] }
  | { values: Shape };
const object = (fields: Record<string, Shape>, identityPaths?: string[]): Shape => ({
  fields,
  identity: identityPaths,
});
const list = (items: Shape, identityPaths?: string[]): Shape => ({
  items,
  identity: identityPaths,
});
const strings = list(true);
const companion = object({ key: true, name: true, species: true }, ['key']);
const offerFields = {
  id: true,
  intention: true,
  companion,
  completedAt: true,
  minutes: true,
  mission: true,
  early: true,
} satisfies Record<string, Shape>;
const postcard = object({ id: true, mission: true, at: true }, ['id']);
const player = object(
  {
    id: true,
    code: true,
    name: true,
    pet_name: true,
    species: true,
    level: true,
    grass: true,
    mood: true,
    hat: true,
    owned_hats: strings,
    mode: true,
    care_until: true,
    recovery_until: true,
    mission_id: true,
    mission_ends_at: true,
    offline_seconds: true,
    last_seen: true,
    deck: strings,
    collection: list(object({ id: true, metAt: true, minutes: true, befriendedAt: true }), ['id']),
    guardian: true,
    postcards: list(postcard, ['id']),
  } satisfies Record<keyof Player, Shape>,
  ['id'],
);
const raid = object({
  id: true,
  attacker_id: true,
  defender_id: true,
  created_at: true,
  attacker_won: true,
  grass_amount: true,
  seen_by_defender: true,
} satisfies Record<keyof Raid, Shape>);
const incoming = list(object({ raid, attacker: player }), ['raid.id']);
// This is the persistence boundary only: unknown fields are kept outside the
// runtime store, including names that happen to match store actions.
const saveShape = object(
  {
    missionReturnPending: true,
    quietView: true,
    recentBreaks: list(
      object({
        id: true,
        completedAt: true,
        mission: true,
        early: true,
        minutes: true,
        grass: true,
        cards: true,
        sessionId: true,
      }),
      ['id'],
    ),
    breakId: true,
    activeBreakContext: object(
      { breakId: true, playerId: true, intention: true, companion, startedAt: true },
      ['breakId'],
    ),
    pendingMemories: list(object(offerFields), ['id']),
    companionMemories: list(object({ ...offerFields, recordedAt: true, source: true }), ['id']),
    memoryResolvedIds: strings,
    lastActiveAt: true,
    tips: strings,
    firstWake: true,
    rules: object({
      budget: object({ startedAt: true, usedMs: true }),
      days: {
        values: object({
          offline: true,
          cards: true,
          grass: true,
          blocked: true,
          raids: true,
          sparringWins: true,
        }),
      },
      recapDay: true,
      checkedDay: true,
      togetherBadges: true,
    }),
    togetherId: true,
    pendingTogetherWakes: list(object({ sid: true, at: true, minutes: true }), ['sid', 'at']),
    togetherSettled: strings,
    seenSessions: strings,
    player,
    identity: true,
    tickAt: true,
    offStart: true,
    offDeck: strings,
    offGrass: true,
    outgoing: list(raid, ['id']),
    staged: incoming,
    applied: strings,
    alerts: incoming,
    collectedCards: strings,
    waitingVisitor: object({ id: true, expiresAt: true }, ['id']),
    cardReward: object(
      {
        settlementId: true,
        deckBefore: strings,
        sessionId: true,
        cards: strings,
        minutes: true,
        mission: true,
        grass: true,
        visitor: true,
        postcard,
        hat: true,
        early: true,
      },
      ['settlementId'],
    ),
  } satisfies Record<keyof Saved, Shape>,
  ['identity'],
);

function isRecord(value: unknown): value is RecordValue {
  return typeof value === 'object' && value !== null && !Array.isArray(value);
}
function atPath(value: unknown, path: string): unknown {
  return path.split('.').reduce<unknown>((at, key) => {
    return isRecord(at) && Object.hasOwn(at, key) ? at[key] : undefined;
  }, value);
}
function identity(value: unknown, paths: string[]): string {
  return JSON.stringify(paths.map((path) => atPath(value, path)));
}

function project(value: unknown, shape: Shape): unknown {
  if (shape === true || value === null) return value;
  if ('items' in shape)
    return Array.isArray(value) ? value.map((item) => project(item, shape.items)) : value;
  if (!isRecord(value)) return value;
  if ('values' in shape)
    return Object.fromEntries(
      Object.entries(value).map(([key, item]) => [key, project(item, shape.values)]),
    );
  return Object.fromEntries(
    Object.entries(shape.fields)
      .filter(([key]) => Object.hasOwn(value, key))
      .map(([key, field]) => [key, project(value[key], field)]),
  );
}

function retainUnknown(previous: unknown, current: unknown, shape: Shape): unknown {
  if (shape === true || current === null) return current;
  if ('items' in shape) {
    if (!Array.isArray(current)) return current;
    const old = Array.isArray(previous) ? previous : [];
    // Only current members survive. Never restore a dismissed offer, an archived
    // receipt or a removed collection item while carrying its extra fields.
    return current.map((item) => {
      const before = shape.identity
        ? old.find((entry) => identity(entry, shape.identity!) === identity(item, shape.identity!))
        : undefined;
      return retainUnknown(before, item, shape.items);
    });
  }
  if (!isRecord(current)) return current;
  let old = isRecord(previous) ? previous : {};
  if ('values' in shape)
    return Object.fromEntries(
      Object.entries(current).map(([key, item]) => [
        key,
        retainUnknown(old[key], item, shape.values),
      ]),
    );
  if (shape.identity && identity(old, shape.identity) !== identity(current, shape.identity))
    old = {};
  return Object.fromEntries([
    ...Object.entries(old).filter(([key]) => !Object.hasOwn(shape.fields, key)),
    ...Object.entries(current).map(([key, item]) => [
      key,
      Object.hasOwn(shape.fields, key) ? retainUnknown(old[key], item, shape.fields[key]) : item,
    ]),
  ]);
}

export class FutureSaveError extends Error {}

/** Parse an isolated known projection; the original snapshot is never mutated. */
export function readSave(
  raw: string | null,
  restore: (value: unknown) => unknown,
): { data: unknown; source: unknown } {
  if (raw === null) return { data: null, source: null };
  const source: unknown = JSON.parse(raw);
  if (!isRecord(source)) throw new Error('Invalid saved game');
  const version = Object.hasOwn(source, 'saveVersion') ? source.saveVersion : 0;
  if (typeof version !== 'number' || !Number.isInteger(version) || version < 0)
    throw new Error('Invalid save version');
  if (version > SAVE_VERSION) throw new FutureSaveError('Newer save version');
  let data = project(source, saveShape);
  // v0 -> v1: the existing legacy defaults and starter-deck upgrade. Current
  // saves retain the same optional-field restoration/validation on each load.
  const migrations = [restore];
  for (let step = version; step < SAVE_VERSION; step++) data = migrations[step](data);
  if (version === SAVE_VERSION) data = restore(data);
  return { data, source };
}

/** Known values win; unrecognised JSON fields round-trip outside store actions. */
export function writeSave(current: object, source: unknown): { raw: string; source: unknown } {
  const merged = retainUnknown(source, current, saveShape);
  const raw = JSON.stringify({ ...(isRecord(merged) ? merged : {}), saveVersion: SAVE_VERSION });
  return { raw, source: JSON.parse(raw) as unknown };
}
