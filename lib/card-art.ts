import type { CardId } from './cards';
import { artMaterials as m, artOutline } from '@/lib/art-direction';

// Sixteen native pixels, lit from the upper left. These small objects use the
// garden's leaf, timber, water, parchment and lavender material ramps.
const material = {
  ink: artOutline,
  woodShade: m.wood[1],
  wood: m.wood[2],
  woodLight: m.wood[3],
  woodGlow: m.wood[4],
  leafShade: m.leaf[0],
  leaf: m.leaf[2],
  leafLight: m.leaf[3],
  leafGlow: m.leaf[4],
  waterShade: m.water[0],
  water: m.water[1],
  waterLight: m.water[2],
  waterGlow: m.water[3],
  mist: m.water[4],
  paperShade: m.cream[1],
  paper: m.cream[2],
  cream: m.cream[3],
  lavenderShade: m.nap[0],
  lavender: m.nap[2],
  lavenderLight: m.nap[3],
  lavenderGlow: m.nap[4],
  clayShade: m.red[1],
  clay: m.red[3],
  clayLight: m.red[4],
  goldShade: m.sand[0],
  gold: m.sand[1],
  goldGlow: m.sand[2],
} as const;
type Material = keyof typeof material;
export type CardArtPixel = { x: number; y: number; color: string };

function illustration(draw: (dot: Dot, rect: Rect) => void): readonly CardArtPixel[] {
  const pixels = new Map<string, CardArtPixel>();
  const dot: Dot = (x, y, color) => {
    if (x >= 0 && x < 16 && y >= 0 && y < 16)
      pixels.set(`${x},${y}`, { x, y, color: material[color] });
  };
  const rect: Rect = (x, y, width, height, color) => {
    for (let py = y; py < y + height; py++)
      for (let px = x; px < x + width; px++) dot(px, py, color);
  };
  draw(dot, rect);
  return [...pixels.values()];
}
type Dot = (x: number, y: number, color: Material) => void;
type Rect = (x: number, y: number, width: number, height: number, color: Material) => void;

// Shared tiny faces and leaves tie these illustrations to the companions without
// putting the same silhouette on every card.
function leaf(dot: Dot, x: number, y: number, right = false) {
  dot(x, y, 'leafShade');
  dot(x + (right ? 1 : -1), y - 1, 'leaf');
  dot(x + (right ? 2 : -2), y - 1, 'leafLight');
  dot(x + (right ? 1 : -1), y - 2, 'leafGlow');
}

export const cardIllustrations: Record<CardId, readonly CardArtPixel[]> = {
  stretch: illustration((dot, rect) => {
    // A wide, grounded stretch, with a rolled edge on the woven mat.
    rect(1, 13, 14, 2, 'lavenderShade');
    rect(2, 12, 12, 2, 'lavender');
    rect(2, 12, 12, 1, 'lavenderGlow');
    dot(1, 13, 'lavenderLight');
    rect(6, 3, 4, 4, 'leafShade');
    rect(5, 4, 6, 2, 'leafShade');
    rect(6, 3, 3, 3, 'leafLight');
    dot(6, 3, 'leafGlow');
    dot(9, 5, 'ink');
    rect(6, 7, 4, 4, 'leaf');
    rect(6, 7, 2, 3, 'leafLight');
    rect(3, 6, 3, 2, 'leafShade');
    rect(10, 6, 3, 2, 'leafShade');
    rect(2, 5, 2, 2, 'leafLight');
    rect(12, 5, 2, 2, 'leaf');
    dot(2, 4, 'leafGlow');
    dot(13, 4, 'leafLight');
    rect(5, 10, 2, 3, 'leafShade');
    rect(9, 10, 2, 3, 'leafShade');
    dot(4, 12, 'leafLight');
    dot(11, 12, 'leaf');
    leaf(dot, 7, 3);
  }),
  deep_breath: illustration((dot, rect) => {
    // A settled leaf bud and three curved, cool breaths.
    rect(3, 12, 8, 2, 'paperShade');
    rect(2, 9, 10, 3, 'leafShade');
    rect(3, 6, 8, 6, 'leaf');
    rect(4, 5, 6, 6, 'leafLight');
    rect(4, 6, 3, 3, 'leafGlow');
    rect(3, 10, 8, 2, 'leaf');
    dot(5, 8, 'leafShade');
    dot(6, 9, 'leafShade');
    dot(8, 9, 'leafShade');
    dot(9, 8, 'leafShade');
    dot(7, 11, 'leafShade');
    leaf(dot, 6, 5);
    leaf(dot, 7, 5, true);
    rect(11, 3, 3, 1, 'waterLight');
    dot(14, 4, 'water');
    rect(12, 5, 2, 1, 'waterGlow');
    rect(12, 7, 3, 1, 'waterLight');
    dot(14, 8, 'water');
    rect(12, 10, 2, 1, 'waterGlow');
  }),
  glass_of_water: illustration((dot, rect) => {
    // A faceted glass on a little timber coaster, with one reflected glint.
    rect(3, 13, 10, 2, 'woodShade');
    rect(2, 12, 12, 2, 'wood');
    rect(3, 12, 10, 1, 'woodGlow');
    rect(3, 2, 10, 2, 'waterShade');
    rect(4, 3, 8, 9, 'waterShade');
    rect(5, 4, 6, 7, 'waterGlow');
    rect(5, 6, 6, 5, 'water');
    rect(5, 6, 5, 1, 'waterLight');
    rect(5, 7, 2, 3, 'waterLight');
    rect(5, 4, 1, 5, 'cream');
    rect(6, 10, 4, 1, 'waterGlow');
    rect(4, 2, 8, 1, 'mist');
    dot(9, 7, 'mist');
    dot(10, 8, 'waterGlow');
    dot(13, 1, 'gold');
    dot(14, 2, 'goldGlow');
  }),
  short_walk: illustration((dot, rect) => {
    // Two different boot prints, rather than the morning walk's landscape.
    rect(2, 13, 12, 1, 'paperShade');
    rect(2, 9, 6, 4, 'woodShade');
    rect(3, 5, 4, 6, 'ink');
    rect(3, 6, 3, 4, 'clay');
    rect(4, 6, 2, 1, 'clayLight');
    rect(2, 10, 5, 2, 'woodLight');
    rect(2, 12, 6, 1, 'ink');
    rect(9, 5, 5, 4, 'woodShade');
    rect(10, 1, 3, 5, 'ink');
    rect(10, 2, 2, 4, 'clay');
    dot(10, 2, 'clayLight');
    rect(9, 6, 4, 2, 'woodLight');
    rect(9, 8, 5, 1, 'ink');
    dot(2, 4, 'leaf');
    dot(1, 3, 'leafLight');
    dot(14, 12, 'leaf');
    dot(13, 11, 'leafLight');
  }),
  morning_walk: illustration((dot, rect) => {
    // A small sunrise beyond a winding trail: landscape, not a second boot.
    rect(1, 2, 14, 10, 'waterGlow');
    rect(1, 2, 14, 4, 'mist');
    rect(6, 3, 5, 4, 'gold');
    rect(7, 2, 3, 5, 'gold');
    rect(7, 3, 2, 2, 'goldGlow');
    rect(1, 8, 14, 6, 'leaf');
    rect(2, 7, 5, 3, 'leafLight');
    rect(9, 7, 5, 3, 'leafShade');
    rect(1, 13, 14, 2, 'leafShade');
    rect(7, 8, 2, 2, 'paperShade');
    rect(6, 10, 3, 2, 'paper');
    rect(5, 12, 4, 3, 'paperShade');
    rect(6, 12, 3, 2, 'paper');
    dot(11, 11, 'leafGlow');
    dot(12, 11, 'goldGlow');
    dot(3, 12, 'leafGlow');
    dot(2, 11, 'leafLight');
  }),
  read_a_chapter: illustration((dot, rect) => {
    // An open cloth-bound book, unequal pages and a lavender ribbon.
    rect(1, 5, 14, 8, 'woodShade');
    rect(2, 3, 5, 9, 'paperShade');
    rect(9, 3, 5, 9, 'paperShade');
    rect(3, 2, 3, 10, 'cream');
    rect(10, 2, 3, 10, 'paper');
    rect(6, 3, 2, 10, 'paper');
    rect(8, 3, 2, 10, 'paperShade');
    rect(2, 12, 5, 1, 'woodLight');
    rect(9, 12, 5, 1, 'wood');
    rect(3, 5, 3, 1, 'paperShade');
    rect(3, 7, 3, 1, 'paperShade');
    rect(3, 9, 2, 1, 'paperShade');
    rect(10, 5, 3, 1, 'woodLight');
    rect(10, 7, 3, 1, 'paperShade');
    rect(10, 9, 2, 1, 'paperShade');
    rect(7, 4, 1, 10, 'lavender');
    dot(7, 4, 'lavenderGlow');
    dot(7, 14, 'lavenderShade');
  }),
  early_night: illustration((dot, rect) => {
    // The same lavender bedding and warm wood as the garden's nap hut.
    rect(1, 7, 2, 8, 'woodShade');
    rect(2, 7, 1, 7, 'woodLight');
    rect(3, 9, 11, 5, 'woodShade');
    rect(3, 9, 4, 2, 'cream');
    rect(3, 11, 4, 1, 'paperShade');
    rect(7, 9, 7, 4, 'lavenderShade');
    rect(7, 9, 6, 2, 'lavenderLight');
    rect(7, 11, 6, 2, 'lavender');
    rect(3, 13, 12, 1, 'woodLight');
    rect(13, 10, 2, 5, 'woodShade');
    dot(13, 10, 'woodGlow');
    rect(9, 1, 3, 1, 'goldGlow');
    rect(8, 2, 2, 3, 'goldGlow');
    rect(9, 5, 3, 1, 'gold');
    dot(10, 4, 'gold');
    dot(13, 3, 'goldGlow');
    dot(5, 3, 'lavenderLight');
  }),
  call_a_friend: illustration((dot, rect) => {
    // Two different garden friends share one bench; no phone is required.
    rect(1, 12, 14, 2, 'woodShade');
    rect(2, 11, 12, 2, 'wood');
    rect(2, 11, 12, 1, 'woodGlow');
    dot(2, 14, 'woodShade');
    dot(13, 14, 'woodShade');
    rect(2, 5, 5, 6, 'leafShade');
    rect(3, 4, 3, 7, 'leafLight');
    rect(3, 5, 2, 2, 'leafGlow');
    dot(4, 7, 'leafShade');
    dot(6, 7, 'leafShade');
    rect(9, 5, 5, 6, 'lavenderShade');
    rect(10, 4, 3, 6, 'lavender');
    rect(10, 5, 2, 2, 'lavenderLight');
    dot(10, 7, 'lavenderShade');
    dot(12, 7, 'lavenderShade');
    leaf(dot, 4, 4);
    dot(10, 3, 'gold');
    dot(12, 3, 'gold');
    dot(11, 4, 'goldGlow');
    dot(7, 1, 'clay');
    dot(9, 1, 'clay');
    rect(7, 2, 3, 1, 'clayLight');
    dot(8, 3, 'clayShade');
  }),
  digital_sunset: illustration((dot, rect) => {
    // A warm sun over the pond, with a little closed device in the foreground.
    rect(1, 1, 14, 8, 'lavenderGlow');
    rect(1, 5, 14, 3, 'clayLight');
    rect(5, 3, 6, 5, 'clay');
    rect(6, 2, 4, 6, 'gold');
    rect(7, 3, 2, 2, 'goldGlow');
    rect(1, 8, 14, 6, 'waterShade');
    rect(2, 9, 12, 1, 'waterLight');
    rect(5, 11, 7, 1, 'water');
    rect(7, 9, 3, 1, 'goldGlow');
    rect(6, 11, 4, 1, 'clayLight');
    rect(8, 13, 3, 1, 'waterGlow');
    rect(1, 13, 6, 2, 'woodShade');
    rect(2, 12, 4, 2, 'lavenderShade');
    rect(2, 12, 4, 1, 'lavenderLight');
    dot(5, 13, 'lavenderGlow');
    rect(12, 13, 3, 2, 'leafShade');
    dot(13, 12, 'leafLight');
  }),
};
