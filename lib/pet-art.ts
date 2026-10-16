import { palette as c, type Player } from '@/lib/game';
import { PET_INDEX, hatSprites, petPalette, petSprites } from '@/lib/pet-sprites';

type Material = { outline: string; shadow: string; base: string; light: string };
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
  const stage = Math.min(3, Math.max(1, level));
  const pixels = new Map<string, ArtPixel>();
  function dot(x: number, y: number, color: string) {
    if (x >= 0 && y >= 0 && x < 32 && y < 32) pixels.set(`${x},${y}`, { x, y, color });
  }
  function rect(x: number, y: number, w: number, h: number, color: string) {
    for (let yy = y; yy < y + h; yy++) for (let xx = x; xx < x + w; xx++) dot(xx, yy, color);
  }
  function shape(points: [number, number][], m: Material) {
    const filled = new Set<string>();
    for (let y = 0; y < 32; y++)
      for (let x = 0; x < 32; x++) {
        let inside = false;
        for (let i = 0, j = points.length - 1; i < points.length; j = i++) {
          const [xi, yi] = points[i];
          const [xj, yj] = points[j];
          if (
            yi > y + 0.5 !== yj > y + 0.5 &&
            x + 0.5 < ((xj - xi) * (y + 0.5 - yi)) / (yj - yi) + xi
          )
            inside = !inside;
        }
        if (inside) filled.add(`${x},${y}`);
      }
    filled.forEach((key) => {
      const [x, y] = key.split(',').map(Number);
      const edge = [
        [x - 1, y],
        [x + 1, y],
        [x, y - 1],
        [x, y + 1],
      ].some(([xx, yy]) => !filled.has(`${xx},${yy}`));
      dot(
        x,
        y,
        edge ? m.outline : y < 16 && x < 19 ? m.light : y > 23 || x > 24 ? m.shadow : m.base,
      );
    });
  }
  if (groundShadow) {
    rect(8, 30, 20, 1, c.stone);
    rect(11, 31, 14, 1, c.stone);
  }
  if (dave) {
    const weed: Material = { outline: c.night, shadow: '#606873', base: c.weed, light: '#B5BAB0' };
    shape(
      [
        [5, 27],
        [9, 18],
        [5, 10],
        [10, 12],
        [11, 5],
        [15, 10],
        [18, 3],
        [20, 10],
        [26, 7],
        [24, 15],
        [29, 20],
        [25, 28],
        [18, 26],
        [13, 29],
      ],
      weed,
    );
    rect(12, 13, 13, 11, c.night);
    rect(14, 15, 9, 7, '#71C8DD');
    rect(15, 17, 2, 2, c.night);
    rect(20, 17, 2, 2, c.night);
    rect(17, 21, 3, 1, c.night);
    rect(3, 16, 5, 1, c.slate);
    rect(25, 12, 5, 1, c.slate);
    rect(8, 25, 4, 1, c.paper);
    rect(26, 23, 4, 1, c.night);
    return [...pixels.values()];
  }
  // Redrawn Grasslings (scripts/art/pets.py): shaded 32x32 sprites per species/stage.
  const sprite = petSprites[species][stage as 1 | 2 | 3];
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
