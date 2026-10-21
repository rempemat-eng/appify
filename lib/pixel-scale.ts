import { gameLayout } from '@/lib/layout';
import { ART_DENSITY } from '@/lib/art-density-setting';
import type { ArtDensity } from '@/lib/art-density';

/**
 * The game's one pixel grid (docs/vision/coherence-plan.md, step 6), at an art density
 * (lib/art-density.ts).
 *
 * The world is measured in world pixels, and about WORLD_ACROSS of them fit across the play
 * area at every density. The art is drawn on a finer grid of texels, `density` to a world
 * pixel. About ART_ACROSS_AT[density] texels fit across, and one texel is a whole number of
 * device pixels (k = round(device px across / texels across)), so every texel stays crisp:
 *
 * - Density 1 (today): 300 across. A texel is a world pixel: 4 device pixels (1.33 CSS px)
 *   on a 3x phone, 3 on most 2x phones, 2 on a desktop.
 * - Density 2: 600 across. Every phone from 1080 to 1440 device px wide gets 2 device
 *   pixels a texel, so a world pixel is 4 on a 3x phone and the view is today's; 1x art is
 *   drawn 2 x 2 texels a pixel, exactly as it looks today. A 2x phone (iPhone SE, 750 px)
 *   gets 1, so it sees its full 375 px width instead of 250.
 * - Density 1.5 (second choice): 420 across, so 1080 to 1440 px phones all get 3 device
 *   pixels a texel (450 would split iPhones at 3 from 1080 Androids at 2). A world pixel is
 *   then 4.5 device pixels, so 1x art is uneven (4 and 5) on every phone: 1.5 suits a whole
 *   redraw, not a region-by-region one. 1.5x art and 2x art never share a grid.
 *
 * A window too narrow for its density's whole-pixel texel (fewer than 225 world px across)
 * steps down one device pixel a texel, and where that is not possible (a 1x screen under
 * 450 px at density 2) falls back to density 1, so the interface still fits; finer art is
 * then drawn smaller than its texels.
 *
 * The world, the characters, the frames and the icons all use this one grid (`usePixelUnit`
 * and `usePixelGrid` in components/pixel-frame.tsx read it for the current window). Pure,
 * so it can be tested.
 */
export const WORLD_ACROSS = 300;

/** Texels across the play area at each density (see above for 1.5). */
export const ART_ACROSS_AT: Readonly<Record<ArtDensity, number>> = { 1: 300, 1.5: 420, 2: 600 };

/** Texels across the play area at the game's density. */
export const ART_ACROSS = ART_ACROSS_AT[ART_DENSITY];

/** The fewest world px across, as a share of WORLD_ACROSS, before a finer step or the
 *  fall back to density 1 (density 1 itself goes down to 225, in a 450 px window at 1x). */
const MIN_ACROSS = 0.75;

export type PixelGrid = {
  /** the density drawn at: the one asked for, or 1 in a narrow 1x window */
  density: ArtDensity;
  /** device pixels per texel, a whole number */
  deviceTexel: number;
  /** CSS pixels per texel */
  texel: number;
  /** CSS pixels per world pixel: what positions, sizes and hit areas are multiplied by */
  unit: number;
};

function gridAt(
  across: number,
  ratio: number,
  density: ArtDensity,
  deviceTexel = Math.max(1, Math.round((across * ratio) / ART_ACROSS_AT[density])),
): PixelGrid {
  return {
    density,
    deviceTexel,
    texel: deviceTexel / ratio,
    unit: (deviceTexel * density) / ratio,
  };
}

/** The pixel grid for a play area this wide on a screen of this density. */
export function pixelGrid(width: number, dpr: number, density: ArtDensity = ART_DENSITY) {
  const across = Math.min(width, gameLayout.maxWidth);
  const ratio = dpr > 0 ? dpr : 1;
  const grid = gridAt(across, ratio, density);
  const fits = (g: PixelGrid) => across / g.unit >= WORLD_ACROSS * MIN_ACROSS;
  if (density === 1 || fits(grid)) return grid;
  if (grid.deviceTexel > 1) {
    const finer = gridAt(across, ratio, density, grid.deviceTexel - 1);
    if (fits(finer)) return finer;
  }
  return gridAt(across, ratio, 1);
}

/** CSS pixels per world pixel for a play area this wide on a screen of this density. */
export function pixelScale(width: number, dpr: number, density: ArtDensity = ART_DENSITY) {
  return pixelGrid(width, dpr, density).unit;
}

/** CSS pixels per pixel of a picture drawn at `assetDensity` texels per world pixel: what a
 *  frame or icon drawn in code multiplies its own pixels by. */
export function assetUnit(grid: PixelGrid, assetDensity: ArtDensity) {
  return grid.unit / assetDensity;
}

/** Whether a picture of this density lands on whole device pixels on this grid: always for
 *  1x art at density 1 or 2 and for art of the grid's own density; 1x art at density 1.5
 *  only where a texel is an even number of device pixels. */
export function crispOn(grid: PixelGrid, assetDensity: ArtDensity) {
  const device = (grid.deviceTexel * grid.density) / assetDensity;
  return device >= 1 && Math.abs(device - Math.round(device)) < 1e-9;
}

/** Round a CSS length to whole device pixels, so an art pixel never straddles two. */
export function snapToDevice(value: number, dpr: number) {
  const ratio = dpr > 0 ? dpr : 1;
  return Math.round(value * ratio) / ratio;
}
