import { palette as c, type Player } from '@/lib/game';

type Material = { outline: string; shadow: string; base: string; light: string };
const cream: Material = { outline: '#92745C', shadow: c.body, base: c.paper, light: '#FFF3DB' };
const clay: Material = { outline: c.ink, shadow: '#804735', base: c.error, light: '#C77E59' };
const rock: Material = { outline: c.night, shadow: '#65738E', base: c.slate, light: '#BBC9D8' };
const leaf: Material = { outline: '#315F39', shadow: c.moss, base: c.positive, light: '#94BD70' };
const wood: Material = { outline: '#392F2C', shadow: c.ink, base: '#795548', light: '#A77C5E' };
export type ArtPixel = { x: number; y: number; color: string };

// Rasterize hand-authored silhouettes onto a 32 x 32 canvas. All edges are integer pixels.
export function petPixels(
  species: Player['species'],
  level: number,
  hat: string | null,
  sleeping: boolean,
  grumpy: boolean,
): ArtPixel[] {
  const stage = Math.min(3, Math.max(1, level));
  const pixels = new Map<string, ArtPixel>();
  function dot(x: number, y: number, color: string) {
    if (x >= 0 && y >= 0 && x < 32 && y < 32) pixels.set(`${x},${y}`, { x, y, color });
  }
  function rect(x: number, y: number, w: number, h: number, color: string) {
    for (let yy = y; yy < y + h; yy++) for (let xx = x; xx < x + w; xx++) dot(xx, yy, color);
  }
  function shape(points: [number, number][], material: Material) {
    const filled = new Set<string>();
    for (let y = 0; y < 31; y++)
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
    const top = Math.min(...points.map((p) => p[1]));
    const bottom = Math.max(...points.map((p) => p[1]));
    const left = Math.min(...points.map((p) => p[0]));
    const right = Math.max(...points.map((p) => p[0]));
    filled.forEach((key) => {
      const [x, y] = key.split(',').map(Number);
      const edge = [
        [x - 1, y],
        [x + 1, y],
        [x, y - 1],
        [x, y + 1],
      ].some(([xx, yy]) => !filled.has(`${xx},${yy}`));
      const shade = (y - top) / (bottom - top) + (0.4 * (x - left)) / (right - left);
      dot(
        x,
        y,
        edge
          ? material.outline
          : shade < 0.5
            ? material.light
            : shade > 0.95
              ? material.shadow
              : material.base,
      );
    });
  }
  rect(9, 29, 16, 1, c.stone);
  rect(6, 30, 22, 1, c.stone);
  rect(9, 31, 16, 1, c.stone);
  const grow = stage - 1;
  const top = 10 - grow;
  // Feet stay stubby at every evolution.
  shape(
    [
      [10, 24],
      [14, 24],
      [14, 29],
      [9, 29],
      [9, 27],
    ],
    species === 'RAT' ? wood : species === 'CUBE' ? rock : cream,
  );
  shape(
    [
      [21, 24],
      [25, 24],
      [25, 29],
      [20, 29],
      [20, 27],
    ],
    species === 'RAT' ? wood : species === 'CUBE' ? rock : cream,
  );
  if (species === 'BLOB') {
    shape(
      [
        [8 - grow, 14],
        [11 - grow, top],
        [20, top - 1],
        [24, top + 2],
        [27, 16],
        [28, 22],
        [25, 26],
        [11, 27],
        [6 - grow, 23],
        [6 - grow, 18],
      ],
      cream,
    );
    // A warm flank and asymmetrical cheek give a three-quarter view.
    rect(8, 19, 2, 4, c.body);
    rect(10, 24, 9, 1, c.body);
    rect(24, 22, 2, 2, c.body);
    if (stage >= 3) {
      shape(
        [
          [4, 13],
          [7, 9],
          [12, 7],
          [17, 9],
          [19, 15],
          [17, 24],
          [8, 25],
          [4, 21],
        ],
        leaf,
      );
      rect(7, 12, 3, 1, leaf.light);
      rect(9, 10, 3, 1, leaf.light);
      rect(7, 20, 2, 2, leaf.shadow);
    }
    if (stage >= 2) {
      rect(17, 6, 1, 5, leaf.outline);
      shape(
        [
          [17, 7],
          [18, 3],
          [23, 2],
          [22, 6],
          [19, 8],
        ],
        leaf,
      );
      dot(20, 4, leaf.light);
    }
  } else if (species === 'RAT') {
    // Curled cable tail, ears, then body and forward snout.
    rect(2, 20, 2, 7, wood.outline);
    rect(3, 26, 6, 2, wood.outline);
    rect(7, 23, 2, 4, wood.outline);
    rect(4, 22, 4, 2, wood.outline);
    rect(3, 21, 1, 5, wood.light);
    rect(4, 26, 3, 1, wood.base);
    shape(
      [
        [9, top + 3],
        [7, top - 3],
        [8, top - 6],
        [13, top - 6],
        [16, top],
        [21, top - 4],
        [25, top - 3],
        [25, top + 5],
        [28, 17],
        [30, 20],
        [27, 23],
        [25, 26],
        [11, 27],
        [7, 23],
        [7, 18],
      ],
      clay,
    );
    shape(
      [
        [9, top - 4],
        [12, top - 4],
        [14, top + 1],
        [10, top + 2],
      ],
      cream,
    );
    shape(
      [
        [21, top - 2],
        [23, top - 1],
        [23, top + 3],
        [20, top + 3],
      ],
      cream,
    );
    rect(10, 22, 3, 2, wood.base);
    dot(29, 20, wood.outline);
    if (stage >= 2) {
      rect(25, 16, 5, 1, wood.outline);
      rect(29, 14, 1, 3, wood.outline);
      dot(29, 13, rock.light);
      rect(25, 23, 5, 1, wood.outline);
      rect(29, 24, 1, 2, wood.outline);
      dot(29, 26, rock.light);
    }
    if (stage >= 3) {
      shape(
        [
          [1, 20],
          [2, 16],
          [4, 17],
          [5, 19],
          [4, 23],
          [2, 23],
        ],
        clay,
      );
      rect(2, 19, 2, 3, c.gold);
      dot(2, 19, c.paper);
    }
  } else {
    if (stage >= 3) {
      shape(
        [
          [3, 18],
          [5, 11],
          [9, 7],
          [15, 8],
          [19, 13],
          [17, 24],
          [7, 26],
          [3, 23],
        ],
        rock,
      );
      shape(
        [
          [4, 16],
          [6, 10],
          [10, 8],
          [15, 10],
          [17, 13],
          [13, 16],
          [8, 15],
          [6, 18],
        ],
        leaf,
      );
      rect(6, 12, 2, 1, leaf.light);
      rect(9, 10, 3, 1, leaf.light);
    }
    if (stage >= 2) {
      shape(
        [
          [10, top + 3],
          [11, top - 4],
          [16, top + 2],
        ],
        rock,
      );
      shape(
        [
          [19, top + 2],
          [21, top - 3],
          [24, top + 3],
        ],
        rock,
      );
      shape(
        [
          [8, 19],
          [4, 17],
          [8, 14],
        ],
        rock,
      );
    }
    shape(
      [
        [10, top],
        [22, top - 1],
        [27, top + 3],
        [27, 24],
        [23, 27],
        [9, 26],
        [7, 22],
        [7, top + 3],
      ],
      rock,
    );
    rect(9, top + 3, 2, 13, rock.light);
    rect(24, top + 5, 2, 13, rock.shadow);
    rect(12, top + 2, 9, 1, rock.light);
    rect(12, 25, 10, 1, rock.shadow);
    dot(13, 13, rock.shadow);
    dot(14, 14, rock.shadow);
    dot(22, 24, rock.outline);
  }
  const eyeY = species === 'RAT' ? 16 : 17;
  const eye = species === 'CUBE' ? rock.outline : wood.outline;
  if (sleeping) {
    rect(17, eyeY + 1, 3, 1, eye);
    rect(23, eyeY + 1, 3, 1, eye);
  } else {
    rect(17, eyeY, 2, 3, eye);
    rect(23, eyeY, 2, 3, eye);
    dot(17, eyeY, c.paper);
    dot(23, eyeY, c.paper);
    if (grumpy) {
      rect(16, eyeY - 1, 3, 1, eye);
      rect(22, eyeY - 1, 3, 1, eye);
    }
  }
  rect(20, 22, 4, 1, eye);
  // Hats are drawn in the same pixel materials, not platform emoji.
  if (hat === 'CAP') {
    rect(12, top - 2, 12, 3, rock.outline);
    rect(13, top - 3, 9, 3, rock.base);
    rect(20, top, 8, 1, rock.light);
  }
  if (hat === 'TOP HAT') {
    rect(12, top - 1, 15, 2, wood.outline);
    rect(15, top - 6, 8, 5, wood.outline);
    rect(16, top - 5, 2, 3, wood.base);
    rect(15, top - 2, 8, 1, clay.base);
  }
  if (hat === 'CROWN') {
    rect(13, top - 2, 11, 3, c.gold);
    rect(13, top - 5, 2, 4, c.gold);
    rect(18, top - 6, 2, 5, c.gold);
    rect(22, top - 5, 2, 4, c.gold);
    rect(14, top - 1, 9, 1, wood.base);
    dot(18, top - 1, clay.base);
  }
  if (hat === 'SHADES') {
    rect(15, eyeY - 1, 11, 1, rock.outline);
    rect(16, eyeY, 4, 3, rock.outline);
    rect(22, eyeY, 4, 3, rock.outline);
    dot(17, eyeY, rock.light);
    dot(23, eyeY, rock.light);
  }
  return [...pixels.values()];
}
