import { palette as c, type Player } from '@/lib/game';
import { PET_INDEX, hatSprites, petPalette, petSprites, visitorSprites } from '@/lib/pet-sprites';

export type ArtPixel = { x: number; y: number; color: string };

// Original integer-grid plant-animal silhouettes; species codes remain save-compatible.
export function petPixels(
  species: Player['species'],
  level: number,
  hat: string | null,
  sleeping: boolean,
  grumpy: boolean,
  dave = false,
  groundShadow = true,
): ArtPixel[] {
  const stage: 1 | 2 | 3 = level >= 3 ? 3 : level >= 2 ? 2 : 1;
  const pixels = new Map<string, ArtPixel>();
  function dot(x: number, y: number, color: string) {
    if (x >= 0 && y >= 0 && x < 32 && y < 32) pixels.set(`${x},${y}`, { x, y, color });
  }
  function rect(x: number, y: number, w: number, h: number, color: string) {
    for (let yy = y; yy < y + h; yy++) for (let xx = x; xx < x + w; xx++) dot(xx, yy, color);
  }
  if (groundShadow) {
    rect(8, 30, 20, 1, c.stone);
    rect(11, 31, 14, 1, c.stone);
  }
  if (dave) {
    visitorSprites.dave[sleeping ? 'closed' : 'open'].forEach((row, y) => {
      for (let x = 0; x < row.length; x++) {
        const ch = row[x];
        if (ch !== '.') dot(x, y, petPalette[PET_INDEX.indexOf(ch)]);
      }
    });
    return [...pixels.values()];
  }
  // Redrawn Grasslings (scripts/art/pets.py): shaded 32x32 sprites per species/stage.
  const sprite = petSprites[species][stage];
  const state = sleeping ? (grumpy ? 'grumpy-closed' : 'closed') : grumpy ? 'grumpy' : 'open';
  sprite[state].forEach((row, y) => {
    for (let x = 0; x < row.length; x++) {
      const ch = row[x];
      if (ch !== '.') dot(x, y, petPalette[PET_INDEX.indexOf(ch)]);
    }
  });
  const hatArt = hat ? hatSprites[hat] : undefined;
  if (hatArt) {
    const left = sprite.hat[0] - 8;
    const top = sprite.hat[1] - hatArt.bottom;
    hatArt.rows.forEach((row, y) => {
      for (let x = 0; x < row.length; x++) {
        const ch = row[x];
        if (ch !== '.') dot(left + x, top + y, petPalette[PET_INDEX.indexOf(ch)]);
      }
    });
  }
  if (hat === 'SHADES') {
    const [ex, ey] = sprite.eyes;
    rect(ex - 2, ey - 1, 12, 1, c.night);
    rect(ex - 1, ey, 4, 3, c.night);
    rect(ex + 5, ey, 4, 3, c.night);
    dot(ex, ey, c.slate);
    dot(ex + 6, ey, c.slate);
  }
  return [...pixels.values()];
}
