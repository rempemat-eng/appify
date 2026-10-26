import { View } from 'react-native';
import Svg, { Rect } from 'react-native-svg';
import { cozy as c } from '@/lib/cozy';
import type { BreakIntention } from '@/lib/companion-memories';

// Small paper keepsakes share the garden's native grid and upper-left light.
// These are decorative SVG pixels, rather than another interactive pet.
const keepsakePixels: Record<BreakIntention, readonly string[]> = {
  rest: [
    '................',
    '......ooo.......',
    '.....o...o......',
    '.....o...o......',
    '....ooooooo.....',
    '....owyyyyo.....',
    '....owyhyyo.....',
    '....owhhhyo.....',
    '....owyhyyo.....',
    '....owyyyso.....',
    '....oyyysoo.....',
    '....ooooooo.....',
    '.....ossoo......',
    '....ooooooo.....',
    '................',
    '................',
  ],
  read: [
    '................',
    '....ooooooo.....',
    '....owwwhho.....',
    '....owwhhho.....',
    '....ohhhhho.....',
    '....ohhhhho.....',
    '....ohgggso.....',
    '....ohhghso.....',
    '....ohhhhso.....',
    '....ohhhhso.....',
    '....ohhhhso.....',
    '....ohhohso.....',
    '....oho.oso.....',
    '....oo...oo.....',
    '................',
    '................',
  ],
  move: [
    '................',
    '.........ooo....',
    '.......oolgo....',
    '.....oollggo....',
    '....ollglggo....',
    '...ollglggso....',
    '...olglggso.....',
    '...oggllgso.....',
    '...ogglgso......',
    '....ogso........',
    '....ogo.........',
    '...ogo..........',
    '..ooo...........',
    '................',
    '................',
    '................',
  ],
  create: [
    '................',
    '..ooooooooo.....',
    '..owwwwwhho.....',
    '..owhhhhhho.....',
    '..owhggghho.....',
    '..ohglhlhho.....',
    '..ohgglghho.oo..',
    '..ohhghhhhooyyo.',
    '..ohhhhhhooyyso.',
    '..ohhhhooyysoo..',
    '..ohhhooyyso....',
    '..ohhooyyso.....',
    '..oooossoo......',
    '....ooo.........',
    '................',
    '................',
  ],
};
const keepsakePalette: Record<string, string> = {
  o: c.ink,
  w: c.highlight,
  h: c.paper,
  s: c.stone,
  y: c.amber,
  l: c.positive,
  g: c.leafOutline,
};
function stampPixels(rows: readonly string[]) {
  return rows.flatMap((row, y) =>
    Array.from(row).flatMap((color, x) =>
      color === '.' ? [] : [{ key: `${x}-${y}`, x, y, color: keepsakePalette[color] }],
    ),
  );
}
const keepsakeArt = {
  rest: stampPixels(keepsakePixels.rest),
  read: stampPixels(keepsakePixels.read),
  move: stampPixels(keepsakePixels.move),
  create: stampPixels(keepsakePixels.create),
};

export function MemoryStamp({
  intention,
  size = 32,
}: {
  intention: BreakIntention;
  size?: number;
}) {
  return (
    <View
      pointerEvents="none"
      aria-hidden
      accessibilityElementsHidden
      importantForAccessibility="no-hide-descendants"
    >
      <Svg width={size} height={size} viewBox="0 0 16 16">
        {keepsakeArt[intention].map((pixel) => (
          <Rect key={pixel.key} x={pixel.x} y={pixel.y} width={1} height={1} fill={pixel.color} />
        ))}
      </Svg>
    </View>
  );
}
