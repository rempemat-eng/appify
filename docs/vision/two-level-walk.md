# Two walk levels: streets and decks

Matt, 19 Oct: "a bigger bustling city with lots and lots of high buildings and possibly verticality would be nice"; "i want to add a city that has verticality: some of the games i mentioned handle this well". This is the design for walking on two levels in one zone (the ground street and a deck above it: skybridges, terraces, elevated walkways). It follows `research/placement-paths-verticality.md`, section 3 (A Link Between Worlds shows the lower floor under the upper one; Solarus and RPG Maker give each level its own ground and change level at stairs; Pokémon enters its stacked road through gatehouses; CrossCode found stacked heights confusing and marks them by colour; Stardew fades buildings the player walks behind). Claude A builds it; the city's zones (Claude C) use it.

## Rules

1. **Two levels at most per zone**: level 0, the street, and level 1, the deck. Rooftops you can walk on belong to their own zone or an interior.
2. **The street stays readable under the deck.** Decks are narrow (about 24 to 32 px deep, face included), the street under a deck is one palette step darker, and the deck casts its shadow down and to the right. A street passes under a deck for 40 px or less, so the companion is rarely hidden; the `Ghost` outline shows it when it is.
3. **Each level has its own materials**: level 0 cobbles or asphalt with warm lamps, level 1 timber or steel decking a shade lighter, with railings.
4. **Few, obvious connectors**: a stair, a ramp or a lift at each end of a deck, so every deck has two ways up where it fits. A deck lands in a doorway or on a stair, never in the air.
5. **Changing level is automatic on stairs and a choice at a lift.** Walking up a stair changes level at its top and bottom cells, with a neutral cell in the middle so the level cannot flicker. A lift is a tap on the lift (a walk to it, then the ride); an interrupted walk never rides it (AGENTS.md: no stale actions).
6. **Tall buildings stand north of their street.** In the three-quarter view a building's height takes screen space above its foot, so a tall building south of a street hides the street. South of a street, keep buildings low, or let their roofs fade when the companion walks behind.

## Data

The generator (`zones.py`, `build()`) takes an optional deck from a zone function: `deck = {'walk': set_of_pixels, 'height': 28, 'connectors': [...]}`.

- `walk` is the deck's walkable surface **in the coordinates of the ground it stands over** (its foot), so the deck and the street share one grid; it is drawn raised by `height` px.
- `connectors`: `{'kind': 'stair' | 'ramp' | 'lift', 'cells': [(x, y), ...], 'bottom': (x, y), 'top': (x, y)}`, the bottom on level 0's walk, the top on the deck's. A stair's cells are walkable on both levels; the level changes at its two ends.

Exported in `lib/zone-maps.ts` beside each zone's `walk`:

```ts
export type ZoneDeck = {
  height: number;                 // art px the deck is raised by
  walk: readonly string[];        // the deck's walk grid, same size as the zone's
  connectors: readonly { kind: 'stair' | 'ramp' | 'lift'; bottom: readonly [number, number]; top: readonly [number, number] }[];
};
export const zoneDecks: Partial<Record<ZoneId, ZoneDeck>>;
```

The ground's own `walk` blocks a deck's supports (columns, stair stringers) but not the space under the deck: the street goes on under it.

## Walking

`lib/region-walk.ts` builds a graph over (level, cell): each level's own walk grid, joined only at connectors (a stair's top cell on level 1 to its bottom cell on level 0, with the cost of its length; a lift as an edge that needs a tap). The companion's position carries its level. A tap picks the level from what is drawn under the finger: the deck's surface where a deck is drawn, else the street. Paths are found over the graph, so a tap on a deck from the street walks to the nearest stair and up.

Residents get their own level too (no global switch, so a resident under a skybridge is not affected by the companion on it).

## Drawing order (`components/atlas-walk.tsx`)

1. Level 0: ground, then its props and actors sorted by foot y (deck supports sort here by their own foot).
2. The deck's shadow on the street (down and to the right).
3. The deck: its front face and railings, then its surface, raised by `height`.
4. Level 1's props and actors, sorted by foot y on the deck.
5. Overhead props (bunting, cables, signs over the street).
6. Roofs that fade to about 55 % in a 20 px radius round the companion when it walks behind them.

An actor on level 1 draws after everything on level 0, whatever its y; an actor on level 0 under a deck draws before the deck, so the deck covers it and the `Ghost` outline shows it.

## Checks

- **deck-support**: every deck pixel lies within reach of a drawn support (column, wall, building front) or the deck's own end; nothing floats.
- **deck-reach**: every deck component has at least one connector, and every stand on it is reachable from the zone's exits over the two-level graph.
- **deck-occlusion**: no walkable street cell is hidden by a deck for a run longer than 40 px; no door on level 0 sits under a deck's face.
- The existing checks run per level (paths lead somewhere, doors open onto walkable cells, nothing natural on a path).

## Order of work

1. Data and export (`zones.py`, `lib/zone-maps.ts`), with an empty `zoneDecks` so nothing changes.
2. The two-level graph in `region-walk.ts` with tests (stairs, the neutral cell, lifts by tap only, residents on their own level).
3. Drawing in `atlas-walk.tsx` (the order above, the darkened street, fading roofs).
4. One deck in the city's first zone as the proof (Claude C), then the rest of the city.

## Status (19 Oct)

Built, with nothing using it yet (no zone has a deck, so every region walks on one level exactly as before):

- **Generator**: a zone function may return a fifth value, its deck: `return cv, objects, stands, blocked, {'walk': deck_pixels, 'height': 28, 'connectors': [{'kind': 'stair', 'bottom': (x, y), 'top': (x, y)}]}`. `zones.deck_grid()` turns it into walk rows and checks it: at least one connector, every connector's bottom on open ground and its top on the deck, every deck cell reached from a connector. It is exported as `zoneDecks` in `lib/zone-maps.ts`.
- **Walking**: `regionLevels()` in `lib/region-walk.ts` lays the deck level beside the ground level, `offset` pixels to the right, with each stair and ramp a link between a ground cell and a deck cell; `makeWalkGrid` (lib/garden-path.ts) walks across links and keeps both ends of each in the path. Tested in `lib/region-walk.test.ts`.
- **Drawing** (`components/atlas-walk.tsx`): the feet are drawn in screen terms (a deck point raised by its deck's height), so a stair is walked as one straight climb on screen; on a deck the companion draws above the ground and the deck; a tap picks the deck where a deck's surface is drawn under the finger.

- **Lifts**: a walk to the other level with no stair on the way walks to the nearest lift, rides it (the cab carries the feet between its two ends as drawn, 0.9 s; at once with reduced motion), then walks on. Each part starts only when the one before finished, so an interrupted walk never rides a stale lift.

- **Levels meet only at connectors** (Claude C's review, 19 Oct): the deck level lies past one blocked column, so no cell of one level neighbours a cell of the other, diagonals included; a ground walk reaches a deck only by its stairs, ramps or lifts.
- **A logical address**: the walk reports where the companion stands as the ground point under its feet plus `level: 1` on a deck (`WalkSpot`), never the raised drawn point. The world screen saves it (`WorldSpot.level`, absent on the ground, so every older save loads as before; a deck spot whose deck is gone loads on the ground below) and reads places, doors and passes only on the ground: a deck has none of its own yet, so on a deck no card opens and no door or pass fires. Places on decks will carry a level when the first one is added.

Still to do: the deck's surface and shadow drawn by the renderer from its walk rows (until then the zone draws its deck as props, overhead), residents on decks, the deck checks in the world lint, and the first deck in the city (Claude C).
