import { WORLD_CANVAS_DEFAULT } from './world-flag-default';

/**
 * The world canvas switch (docs/vision/region-canvas.md, step 2). Off: the world is drawn
 * and walked from its zones, as before. On: from the world tiles (lib/world-canvas.ts),
 * mounted around the camera, with the walk read from the tiles in search windows. Both
 * paths are kept working until step 3 (saves) lets the zones retire.
 *
 * Native reads only the default (lib/world-flag-default.ts). On the web, `?world=canvas` or
 * `?world=zones` in the address overrides it for a play-test (lib/world-flag.web.ts).
 */
export const WORLD_CANVAS: boolean = WORLD_CANVAS_DEFAULT;
