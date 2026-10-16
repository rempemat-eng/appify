import { palette as c, type Player } from '@/lib/game';

type Material = { outline: string; shadow: string; base: string; light: string };
const leaf: Material = { outline: '#315F39', shadow: c.moss, base: c.positive, light: '#94BD70' };
const rock: Material = { outline: c.ink, shadow: '#7D8077', base: '#A9AD98', light: '#D7DAC3' };
const wood: Material = { outline: c.ink, shadow: '#795548', base: c.body, light: c.paper };
const flower: Material = { outline: c.error, shadow: '#BD7564', base: '#D8A29A', light: c.paper };
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
  if (species === 'BLOB') {
    shape(
      [
        [5, 20],
        [7, 15],
        [11, 12],
        [21, 11],
        [26, 15],
        [28, 21],
        [26, 26],
        [20, 28],
        [10, 27],
        [5, 24],
      ],
      leaf,
    );
    rect(9, 27, 4, 2, leaf.shadow);
    rect(22, 27, 4, 2, leaf.shadow);
    rect(8, 20, 3, 2, leaf.shadow);
    rect(11, 14, 4, 1, leaf.light);
    rect(12, 8, 3, 5, c.paper);
    rect(9, 7, 9, 3, c.ink);
    rect(10, 5, 7, 4, c.error);
    rect(12, 6, 2, 1, c.paper);
    rect(16, 8, 1, 1, c.paper);
  } else if (species === 'RAT') {
    // Long stem legs, a curled vine tail and two pointed leaf ears.
    rect(10, 21, 2, 8, leaf.outline);
    rect(12, 28, 3, 1, leaf.shadow);
    rect(22, 21, 2, 8, leaf.outline);
    rect(24, 28, 3, 1, leaf.shadow);
    rect(3, 18, 2, 7, leaf.outline);
    rect(4, 24, 6, 2, leaf.outline);
    rect(7, 21, 2, 4, leaf.outline);
    rect(4, 20, 4, 2, leaf.outline);
    rect(4, 19, 1, 4, leaf.light);
    shape(
      [
        [10, 15],
        [6, 9],
        [6, 4],
        [11, 6],
        [15, 12],
      ],
      leaf,
    );
    shape(
      [
        [20, 12],
        [22, 5],
        [28, 3],
        [27, 10],
        [24, 15],
      ],
      leaf,
    );
    shape(
      [
        [9, 16],
        [13, 12],
        [21, 12],
        [26, 16],
        [27, 20],
        [24, 24],
        [14, 24],
        [9, 21],
      ],
      leaf,
    );
    rect(13, 16, 3, 1, leaf.light);
  } else {
    shape(
      [
        [7, 18],
        [10, 13],
        [16, 11],
        [23, 12],
        [27, 17],
        [28, 23],
        [24, 27],
        [12, 28],
        [7, 24],
      ],
      rock,
    );
    rect(11, 27, 3, 2, rock.shadow);
    rect(22, 27, 3, 2, rock.shadow);
    // Reading lamp grows from the back, leaving the crown free for hats.
    rect(5, 11, 2, 14, leaf.outline);
    rect(6, 9, 5, 2, leaf.outline);
    rect(8, 7, 7, 2, c.ink);
    rect(7, 9, 9, 3, c.gold);
    rect(9, 10, 5, 1, c.paper);
    rect(10, 17, 5, 1, c.ink);
    rect(9, 18, 1, 3, c.ink);
    rect(15, 18, 1, 3, c.ink);
    rect(10, 21, 5, 1, c.ink);
    rect(20, 17, 5, 1, c.ink);
    rect(19, 18, 1, 3, c.ink);
    rect(25, 18, 1, 3, c.ink);
    rect(20, 21, 5, 1, c.ink);
    rect(16, 19, 3, 1, c.ink);
  }
  // Every Grassling starts leafy, buds at level 2 and flowers at level 3.
  rect(4, 23, 4, 2, leaf.shadow);
  rect(5, 21, 3, 2, leaf.base);
  if (stage >= 2) {
    rect(4, 12, 1, 10, leaf.outline);
    rect(2, 15, 3, 2, leaf.base);
    if (stage === 2) {
      rect(3, 8, 3, 5, leaf.outline);
      rect(4, 9, 1, 3, flower.base);
    } else {
      rect(2, 5, 5, 8, flower.shadow);
      rect(0, 7, 9, 4, flower.base);
      rect(3, 7, 3, 3, c.gold);
      dot(2, 6, flower.light);
      dot(1, 8, flower.light);
    }
  }
  const eyeY = species === 'RAT' ? 17 : 18;
  if (sleeping || species === 'BLOB') {
    rect(16, eyeY, 3, 1, c.ink);
    rect(23, eyeY, 3, 1, c.ink);
  } else {
    rect(species === 'CUBE' ? 12 : 17, eyeY, 1, 2, c.ink);
    rect(23, eyeY, 1, 2, c.ink);
  }
  if (grumpy) {
    rect(16, eyeY - 1, 3, 1, c.ink);
    rect(23, eyeY - 1, 3, 1, c.ink);
  }
  rect(19, 23, 4, 1, c.ink);
  const top = 11;
  if (hat === 'CAP') {
    rect(12, top - 2, 12, 3, c.night);
    rect(13, top - 3, 9, 3, c.slate);
    rect(20, top, 8, 1, c.paper);
  }
  if (hat === 'TOP HAT') {
    rect(12, top - 1, 15, 2, c.ink);
    rect(15, top - 6, 8, 5, c.ink);
    rect(16, top - 5, 2, 3, wood.shadow);
    rect(15, top - 2, 8, 1, c.error);
  }
  if (hat === 'CROWN') {
    rect(13, top - 2, 11, 3, c.gold);
    rect(13, top - 5, 2, 4, c.gold);
    rect(18, top - 6, 2, 5, c.gold);
    rect(22, top - 5, 2, 4, c.gold);
    dot(18, top - 1, c.error);
  }
  if (hat === 'SHADES') {
    rect(15, eyeY - 1, 11, 1, c.night);
    rect(16, eyeY, 4, 3, c.night);
    rect(22, eyeY, 4, 3, c.night);
    dot(17, eyeY, c.slate);
    dot(23, eyeY, c.slate);
  }
  return [...pixels.values()];
}
