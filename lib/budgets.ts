import type { ArtDensity } from './art-density';

/**
 * Phone budgets at each art density (Claude M, 21 Oct; docs/native-build.md), checked by
 * `npm run check:budgets` (lib/budgets.test.ts). Pure data.
 *
 * - **World tiles in view** (decoded RGBA, the `WORLD_CANVAS` path): at density 1 the 12 tiles
 *   and 25 MiB of `TILE_BUDGET` (lib/world-walk.ts). At density 2 a 2x phone (iPhone SE) and an
 *   S25 Ultra at QHD+ see a wider view (#183), so the budget rises to 15 tiles and 31 MiB; every
 *   other phone keeps today's view. Moving water stays at 1x under a 2x grid (drawn 2 x 2) or is
 *   stored as deltas; at 1 image px a texel it would cost 4x (#183).
 * - **Pictures on disk** (every PNG under assets/): 16.3 MB today; #183 estimates 24 to 50 MB
 *   for a whole 2x art set. The download budget is the ceiling, not the target.
 * - **Sound on disk**: the palette's own budget (scripts/check-sound.cjs).
 */
export type Budget = {
  /** world tiles mounted for a view, and their decoded bytes */
  tiles: number;
  tileBytes: number;
  /** every PNG under assets/, in bytes on disk */
  pictures: number;
};

const MiB = 1024 * 1024;
const MB = 1000 * 1000;

export const BUDGETS: Readonly<Record<ArtDensity, Budget>> = {
  1: { tiles: 12, tileBytes: 25 * MiB, pictures: 20 * MB },
  1.5: { tiles: 15, tileBytes: 31 * MiB, pictures: 40 * MB },
  2: { tiles: 15, tileBytes: 31 * MiB, pictures: 50 * MB },
};

/** The sound palette's budget on disk (kept in step with scripts/check-sound.cjs). */
export const SOUND_BUDGET = 2.75 * MiB;
