import { palette as c } from '@/lib/game';
import type { ArtPixel } from '@/lib/pet-art';
import type { VisitorId } from '@/lib/visitors';

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
  const oval = (
    cx: number,
    cy: number,
    rx: number,
    ry: number,
    base = c.positive,
    light = c.paper,
  ) => {
    for (let y = cy - ry; y <= cy + ry; y++)
      for (let x = cx - rx; x <= cx + rx; x++) {
        const r = (x - cx) ** 2 / rx ** 2 + (y - cy) ** 2 / ry ** 2;
        if (r <= 1) dot(x, y, r > 0.72 ? c.ink : x < cx && y < cy ? light : base);
      }
  };
  const leaf = (x: number, y: number, flip = false) => {
    for (let row = 0; row < 7; row++)
      rect(x + (flip ? -row : row), y - row, 4, 2, row % 2 ? c.positive : c.moss);
  };
  const eyes = (y: number, closed = sleeping) => {
    rect(12, y, 2, closed ? 1 : 3, c.ink);
    rect(20, y, 2, closed ? 1 : 3, c.ink);
    if (!closed) {
      dot(12, y, c.paper);
      dot(20, y, c.paper);
    }
  };
  if (groundShadow) rect(9, 30, 16, 1, c.stone);
  switch (id) {
    case 'dozebud':
      rect(14, 23, 4, 6, c.moss);
      leaf(14, 27, true);
      leaf(18, 27);
      oval(16, 17, 9, 9, c.body);
      oval(16, 13, 6, 6, c.terracotta, c.body);
      rect(10, 20, 4, 1, c.ink);
      rect(20, 20, 4, 1, c.ink);
      rect(16, 23, 2, 1, c.ink);
      break;
    case 'mosspuff':
      for (const [x, y] of [
        [10, 17],
        [16, 12],
        [23, 16],
        [24, 23],
        [15, 25],
        [8, 23],
      ])
        oval(x, y, 6, 6, c.moss, c.positive);
      oval(16, 20, 8, 6);
      eyes(20);
      rect(16, 25, 2, 1, c.ink);
      break;
    case 'lullapine':
      rect(14, 23, 5, 7, c.shade);
      for (let row = 0; row < 17; row++)
        rect(
          16 - Math.floor(row / 2),
          7 + row,
          1 + 2 * Math.floor(row / 2),
          2,
          row % 4 === 0 ? c.ink : c.moss,
        );
      eyes(19);
      rect(13, 7, 9, 2, c.paper);
      rect(15, 4, 7, 3, c.night);
      rect(20, 2, 4, 3, c.night);
      rect(23, 4, 3, 3, c.paper);
      break;
    case 'trailhop':
      oval(9, 26, 6, 3, c.moss);
      oval(24, 26, 6, 3, c.moss);
      oval(16, 21, 10, 7);
      oval(10, 15, 4, 4);
      oval(23, 15, 4, 4);
      rect(10, 15, 2, 3, c.ink);
      rect(23, 15, 2, 3, c.ink);
      rect(13, 24, 8, 1, c.ink);
      rect(16, 8, 2, 7, c.moss);
      leaf(15, 10, true);
      leaf(18, 10);
      break;
    case 'burrbound':
      for (let row = 0; row < 17; row++) {
        rect(7 - (row % 3 === 0 ? 2 : 0), 10 + row, 20 + (row % 3 === 0 ? 4 : 0), 1, c.ink);
      }
      oval(16, 19, 10, 10, c.stone, c.gold);
      eyes(18);
      for (let x = 8; x < 26; x += 4) {
        rect(x, 11, 1, 3, c.shade);
        rect(x, 25, 1, 3, c.shade);
      }
      rect(7, 27, 8, 4, c.shade);
      rect(19, 27, 8, 4, c.shade);
      rect(8, 28, 5, 1, c.paper);
      rect(20, 28, 5, 1, c.paper);
      break;
    case 'skyfern':
      rect(15, 12, 3, 17, c.moss);
      oval(16, 23, 6, 6, c.positive);
      for (let y = 13; y < 23; y += 4) {
        leaf(13, y, true);
        leaf(19, y);
      }
      eyes(23);
      rect(24, 7, 1, 12, c.ink);
      for (let row = 0; row < 7; row++)
        rect(
          25 - Math.min(row, 6 - row),
          3 + row,
          1 + 2 * Math.min(row, 6 - row),
          1,
          row < 4 ? c.gold : c.terracotta,
        );
      break;
    case 'inkling':
      for (let row = 0; row < 14; row++)
        rect(16 - Math.floor(row / 2), 8 + row, 1 + 2 * Math.floor(row / 2), 1, c.night);
      oval(16, 22, 9, 7, c.night, c.slate);
      rect(11, 28, 4, 2, c.night);
      rect(20, 28, 4, 2, c.night);
      rect(12, 20, 2, 3, c.paper);
      rect(20, 20, 2, 3, c.paper);
      rect(14, 6, 3, 4, c.moss);
      leaf(17, 7);
      break;
    case 'pagemoth':
      oval(8, 17, 7, 9, c.paper, c.body);
      oval(24, 17, 7, 9, c.paper, c.body);
      for (const x of [4, 21]) for (let y = 13; y < 24; y += 3) rect(x, y, 7, 1, c.shade);
      oval(16, 20, 4, 9, c.shade, c.gold);
      rect(13, 6, 1, 8, c.ink);
      rect(19, 6, 1, 8, c.ink);
      rect(12, 5, 3, 2, c.moss);
      rect(18, 5, 3, 2, c.moss);
      rect(14, 18, 1, 2, c.paper);
      rect(18, 18, 1, 2, c.paper);
      break;
    case 'lanternroot':
      oval(13, 22, 7, 7, c.body);
      rect(9, 27, 3, 4, c.shade);
      rect(16, 27, 3, 4, c.shade);
      rect(10, 19, 2, 3, c.ink);
      rect(16, 19, 2, 3, c.ink);
      leaf(10, 14, true);
      leaf(15, 14);
      rect(19, 21, 6, 2, c.shade);
      rect(25, 11, 1, 8, c.ink);
      rect(22, 16, 7, 11, c.ink);
      rect(23, 18, 5, 7, c.gold);
      rect(24, 19, 2, 4, c.paper);
      rect(21, 15, 9, 2, c.shade);
      for (const [x, y] of [
        [28, 12],
        [20, 19],
        [30, 22],
      ])
        dot(x, y, c.gold);
      break;
  }
  if (hat === 'CAP') {
    rect(10, 8, 14, 3, c.terracotta);
    rect(19, 10, 9, 2, c.terracotta);
  }
  if (hat === 'SHADES') {
    rect(9, 19, 15, 1, c.ink);
    rect(10, 19, 5, 3, c.night);
    rect(19, 19, 5, 3, c.night);
  }
  if (hat === 'TOP HAT') {
    rect(12, 2, 10, 7, c.night);
    rect(8, 8, 18, 2, c.ink);
  }
  if (hat === 'CROWN') {
    rect(10, 6, 14, 4, c.gold);
    rect(10, 3, 3, 4, c.gold);
    rect(16, 2, 3, 5, c.gold);
    rect(21, 3, 3, 4, c.gold);
  }
  return [...pixels.values()];
}
