import { palette as c } from '@/lib/game';

export const sceneColors = {
  ...c,
  sky: '#B5CBD0',
  skyLight: '#D7DECF',
  dawn: '#E8D39B',
  pink: '#D8A29A',
  orange: '#CA8D65',
  midnight: '#242C43',
  nightMid: '#303852',
  nightLow: '#464B65',
  cloud: '#EEE5D2',
  rain: '#728798',
  root: '#89664B',
  dirt: '#B18B66',
  leafLight: '#91B573',
  wood: '#9B7654',
  crystal: '#B5D2CE',
  red: '#BD594A',
  frog: '#79965A',
};
export type PropKind =
  | 'grass'
  | 'mushroom'
  | 'root'
  | 'lamp'
  | 'cable'
  | 'rock'
  | 'crystal'
  | 'tree'
  | 'bench'
  | 'library'
  | 'mountain'
  | 'shelf'
  | 'moon'
  | 'sun'
  | 'cloud'
  | 'heart'
  | 'shield'
  | 'house'
  | 'map'
  | 'swords'
  | 'bag'
  | 'lock'
  | 'frog'
  | 'egg'
  | 'nest';
const colors: Record<string, string> = {
  K: c.ink,
  B: c.paper,
  T: c.body,
  G: c.positive,
  M: c.moss,
  L: sceneColors.leafLight,
  R: c.error,
  N: c.night,
  S: c.slate,
  D: sceneColors.dirt,
  W: sceneColors.wood,
  C: sceneColors.crystal,
  Y: c.gold,
  F: sceneColors.frog,
  P: sceneColors.pink,
};
function make(kind: PropKind) {
  const grid = Array.from({ length: 16 }, () => Array<string>(16).fill('.'));
  const rect = (x: number, y: number, w: number, h: number, color: string) => {
    for (let py = y; py < Math.min(16, y + h); py++)
      for (let px = x; px < Math.min(16, x + w); px++) if (py >= 0 && px >= 0) grid[py][px] = color;
  };
  const box = (x: number, y: number, w: number, h: number, color: string) => {
    rect(x, y, w, h, 'K');
    rect(x + 1, y + 1, w - 2, h - 2, color);
  };
  switch (kind) {
    case 'grass':
      rect(3, 10, 1, 4, 'K');
      rect(4, 7, 2, 7, 'M');
      rect(7, 5, 2, 9, 'G');
      rect(10, 9, 2, 5, 'M');
      rect(6, 12, 6, 2, 'G');
      rect(2, 14, 12, 1, 'K');
      break;
    case 'mushroom':
      box(6, 8, 4, 7, 'T');
      rect(3, 5, 10, 4, 'K');
      rect(4, 3, 8, 4, 'K');
      rect(5, 2, 6, 4, 'K');
      rect(4, 5, 8, 3, 'R');
      rect(5, 3, 6, 3, 'R');
      rect(5, 4, 2, 1, 'B');
      rect(9, 6, 2, 1, 'B');
      break;
    case 'root':
      rect(7, 0, 3, 8, 'K');
      rect(8, 0, 1, 9, 'W');
      rect(4, 7, 5, 2, 'W');
      rect(3, 8, 2, 5, 'W');
      rect(9, 8, 4, 2, 'W');
      rect(12, 9, 2, 5, 'W');
      rect(6, 9, 2, 6, 'D');
      break;
    case 'lamp':
      box(6, 1, 4, 2, 'Y');
      box(4, 3, 8, 7, 'Y');
      rect(6, 4, 4, 5, 'B');
      rect(7, 10, 2, 4, 'K');
      box(4, 13, 8, 3, 'W');
      break;
    case 'cable':
      rect(1, 9, 6, 2, 'K');
      rect(5, 5, 2, 5, 'K');
      rect(6, 4, 7, 2, 'K');
      rect(12, 5, 2, 6, 'K');
      rect(8, 10, 5, 2, 'K');
      rect(7, 10, 2, 5, 'K');
      box(1, 7, 3, 5, 'N');
      rect(9, 14, 6, 1, 'R');
      break;
    case 'rock':
      rect(2, 7, 12, 7, 'K');
      rect(4, 4, 8, 10, 'K');
      rect(5, 3, 6, 9, 'K');
      rect(3, 8, 10, 5, 'S');
      rect(5, 5, 6, 7, 'S');
      rect(5, 5, 5, 2, 'B');
      rect(3, 11, 6, 2, 'M');
      break;
    case 'crystal':
      rect(7, 1, 2, 13, 'K');
      rect(5, 3, 6, 11, 'K');
      rect(3, 8, 10, 6, 'K');
      rect(6, 4, 4, 9, 'C');
      rect(7, 2, 1, 10, 'B');
      rect(4, 9, 2, 4, 'S');
      rect(10, 9, 2, 4, 'S');
      break;
    case 'tree':
      box(7, 9, 3, 7, 'W');
      rect(2, 5, 12, 6, 'K');
      rect(4, 2, 8, 9, 'K');
      rect(6, 0, 4, 10, 'K');
      rect(3, 6, 10, 4, 'M');
      rect(5, 3, 6, 6, 'G');
      rect(7, 1, 2, 5, 'L');
      break;
    case 'bench':
      box(1, 5, 14, 5, 'W');
      rect(2, 6, 12, 1, 'T');
      box(0, 10, 16, 3, 'W');
      rect(2, 13, 2, 3, 'K');
      rect(12, 13, 2, 3, 'K');
      break;
    case 'library':
      rect(1, 4, 14, 11, 'K');
      rect(4, 1, 8, 3, 'K');
      rect(2, 5, 12, 9, 'T');
      rect(3, 3, 10, 2, 'R');
      rect(7, 9, 3, 6, 'K');
      rect(3, 7, 3, 4, 'N');
      rect(11, 7, 2, 4, 'N');
      rect(4, 7, 1, 2, 'B');
      break;
    case 'mountain':
      for (let y = 1; y < 15; y++) {
        const w = Math.min(16, 2 + Math.floor(y / 2) * 2);
        rect(8 - w / 2, y, w, 1, 'K');
        rect(9 - w / 2, y, w - 2, 1, y < 6 ? 'B' : 'S');
      }
      rect(2, 13, 12, 2, 'M');
      break;
    case 'shelf':
      box(0, 1, 16, 15, 'W');
      for (let y = 3; y < 14; y += 5) {
        rect(1, y, 14, 3, 'K');
        for (let x = 2; x < 14; x += 3) rect(x, y, 2, 3, x % 2 ? 'R' : 'N');
        rect(1, y + 3, 14, 1, 'T');
      }
      break;
    case 'moon':
      rect(5, 1, 6, 14, 'B');
      rect(2, 4, 10, 8, 'B');
      rect(3, 3, 9, 10, 'B');
      rect(8, 1, 6, 9, 'N');
      rect(11, 8, 4, 5, 'N');
      break;
    case 'sun':
      box(4, 4, 8, 8, 'Y');
      rect(6, 5, 4, 6, 'B');
      rect(7, 0, 2, 3, 'Y');
      rect(7, 13, 2, 3, 'Y');
      rect(0, 7, 3, 2, 'Y');
      rect(13, 7, 3, 2, 'Y');
      rect(2, 2, 2, 2, 'Y');
      rect(12, 12, 2, 2, 'Y');
      break;
    case 'cloud':
      rect(1, 7, 14, 5, 'B');
      rect(3, 4, 10, 7, 'B');
      rect(5, 2, 6, 9, 'B');
      break;
    case 'heart':
      rect(2, 3, 5, 7, 'K');
      rect(9, 3, 5, 7, 'K');
      rect(1, 4, 14, 5, 'K');
      rect(3, 8, 10, 4, 'K');
      rect(5, 11, 6, 2, 'K');
      rect(7, 13, 2, 2, 'K');
      rect(3, 4, 3, 5, 'R');
      rect(10, 4, 3, 5, 'R');
      rect(2, 5, 12, 3, 'R');
      rect(4, 8, 8, 3, 'R');
      rect(6, 11, 4, 1, 'R');
      rect(4, 5, 2, 1, 'P');
      break;
    case 'shield':
      box(3, 2, 10, 8, 'G');
      rect(4, 9, 8, 3, 'K');
      rect(5, 11, 6, 2, 'K');
      rect(7, 13, 2, 1, 'K');
      rect(5, 9, 6, 2, 'M');
      rect(7, 5, 2, 5, 'B');
      rect(5, 7, 6, 2, 'B');
      break;
    case 'house':
      rect(2, 7, 12, 8, 'K');
      for (let y = 1; y < 8; y++) rect(8 - y, y, y * 2, 1, 'K');
      rect(3, 8, 10, 6, 'T');
      rect(6, 10, 4, 5, 'K');
      rect(3, 5, 10, 2, 'R');
      break;
    case 'map':
      box(1, 2, 14, 12, 'T');
      rect(5, 3, 1, 10, 'K');
      rect(10, 3, 1, 10, 'K');
      rect(2, 7, 2, 2, 'G');
      rect(7, 5, 2, 2, 'G');
      rect(11, 9, 2, 2, 'R');
      break;
    case 'swords':
      for (let n = 2; n < 12; n++) {
        rect(n, n, 2, 2, 'K');
        rect(14 - n, n, 2, 2, 'K');
      }
      rect(2, 11, 4, 2, 'W');
      rect(10, 11, 4, 2, 'W');
      rect(3, 12, 2, 3, 'K');
      rect(11, 12, 2, 3, 'K');
      break;
    case 'bag':
      box(5, 1, 6, 5, 'T');
      box(2, 5, 12, 10, 'T');
      rect(7, 6, 2, 6, 'W');
      rect(3, 7, 2, 2, 'B');
      break;
    case 'lock':
      box(5, 1, 6, 7, 'T');
      box(3, 6, 10, 9, 'Y');
      rect(7, 9, 2, 4, 'K');
      break;
    case 'frog':
      box(2, 2, 5, 5, 'F');
      box(9, 2, 5, 5, 'F');
      box(1, 6, 14, 7, 'F');
      rect(4, 4, 2, 1, 'K');
      rect(10, 4, 2, 1, 'K');
      rect(4, 9, 8, 1, 'K');
      rect(3, 12, 3, 3, 'M');
      rect(10, 12, 3, 3, 'M');
      rect(3, 7, 2, 1, 'L');
      break;
    case 'egg':
      rect(4, 2, 8, 12, 'K');
      rect(2, 5, 12, 6, 'K');
      rect(5, 1, 6, 14, 'K');
      rect(5, 3, 6, 10, 'B');
      rect(3, 6, 10, 4, 'B');
      rect(5, 5, 2, 2, 'T');
      rect(9, 9, 2, 2, 'T');
      break;
    case 'nest':
      rect(0, 8, 16, 5, 'K');
      rect(2, 12, 12, 3, 'K');
      rect(1, 9, 14, 3, 'W');
      rect(3, 12, 10, 2, 'W');
      rect(3, 10, 10, 1, 'T');
      rect(0, 6, 3, 3, 'W');
      rect(13, 6, 3, 3, 'W');
      break;
  }
  return grid.flatMap((row, y) =>
    row.flatMap((pixel, x) => (pixel === '.' ? [] : [{ x, y, color: colors[pixel] }])),
  );
}
export const propPixels: Record<PropKind, ReturnType<typeof make>> = {
  grass: make('grass'),
  mushroom: make('mushroom'),
  root: make('root'),
  lamp: make('lamp'),
  cable: make('cable'),
  rock: make('rock'),
  crystal: make('crystal'),
  tree: make('tree'),
  bench: make('bench'),
  library: make('library'),
  mountain: make('mountain'),
  shelf: make('shelf'),
  moon: make('moon'),
  sun: make('sun'),
  cloud: make('cloud'),
  heart: make('heart'),
  shield: make('shield'),
  house: make('house'),
  map: make('map'),
  swords: make('swords'),
  bag: make('bag'),
  lock: make('lock'),
  frog: make('frog'),
  egg: make('egg'),
  nest: make('nest'),
};
