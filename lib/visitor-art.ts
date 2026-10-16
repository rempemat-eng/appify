import { palette as c } from '@/lib/game';
import type { ArtPixel } from '@/lib/pet-art';
import type { VisitorId } from '@/lib/visitors';
import { PET_INDEX, hatSprites, petPalette, visitorSprites } from '@/lib/pet-sprites';

// Each visitor has its own integer-grid silhouette and plant-animal details.
export function visitorPixels(
  id: VisitorId,
  hat: string | null = null,
  sleeping = false,
  groundShadow = true,
): ArtPixel[] {
  const pixels = new Map<string, ArtPixel>();
  const dot = (x: number, y: number, color: string) => {
    if (x >= 0 && x < 32 && y >= 0 && y < 32) pixels.set(`${x},${y}`, { x, y, color });
  };
  const rect = (x: number, y: number, w: number, h: number, color: string) => {
    for (let yy = y; yy < y + h; yy++) for (let xx = x; xx < x + w; xx++) dot(xx, yy, color);
  };
  if (groundShadow) rect(9, 30, 16, 1, c.stone);
  // Redrawn visitors (scripts/art/pets.py): shaded 32x32 sprites.
  const sprite = visitorSprites[id];
  const draw = (rows: readonly string[], left = 0, top = 0) =>
    rows.forEach((row, y) => {
      for (let x = 0; x < row.length; x++) {
        const ch = row[x];
        if (ch !== '.') dot(left + x, top + y, petPalette[PET_INDEX.indexOf(ch)]);
      }
    });
  draw(sleeping ? sprite.closed : sprite.open);
  const hatArt = hat ? hatSprites[hat] : undefined;
  if (hatArt) draw(hatArt.rows, sprite.hat[0] - 8, sprite.hat[1] - hatArt.bottom);
  if (hat === 'SHADES') {
    const [ex, ey] = sprite.eyes;
    rect(ex - 2, ey - 1, 12, 1, c.night);
    rect(ex - 1, ey, 4, 3, c.night);
    rect(ex + 5, ey, 4, 3, c.night);
  }
  return [...pixels.values()];
}
