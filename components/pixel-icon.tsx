import { View, type StyleProp, type ViewStyle } from 'react-native';
import Svg, { Rect } from 'react-native-svg';
import { iconPalette, iconRows, type IconName } from '@/lib/icon-art';

export type { IconName };

type Run = { x: number; y: number; w: number; fill: string };

const KEYS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
const cache = new Map<IconName, Run[]>();

/** Each row's same-colour pixels merged into runs, computed once per icon. */
function runsOf(name: IconName): Run[] {
  const known = cache.get(name);
  if (known) return known;
  const runs: Run[] = [];
  iconRows[name].forEach((row, y) => {
    let x = 0;
    while (x < row.length) {
      const key = row[x];
      let end = x + 1;
      while (end < row.length && row[end] === key) end++;
      if (key !== '.') runs.push({ x, y, w: end - x, fill: iconPalette[KEYS.indexOf(key)] });
      x = end;
    }
  });
  cache.set(name, runs);
  return runs;
}

/** An icon's grid: 16 rows at 1x, 32 at 2x. It is shown at the same size either way (16
 *  world px, ui-tokens `iconSize`), so a 2x icon draws two texels to a world pixel. */
const gridOf = (name: IconName) => iconRows[name].length;

/**
 * An icon from the generated set (scripts/art/icons.py, coherence plan step 4): 16x16
 * pixel art with the garden's lighting and tinted outlines. Decorative: the control
 * that holds it carries the label, unless `label` is given. `muted` greys it for an
 * inactive state.
 */
export function PixelIcon({
  name,
  size = 16,
  muted = false,
  label,
  style,
}: {
  name: IconName;
  size?: number;
  muted?: boolean;
  /** only for an icon that carries meaning on its own (a status); otherwise decorative */
  label?: string;
  style?: StyleProp<ViewStyle>;
}) {
  // The View keeps the icon in normal stacking order: on web a bare SVG paints
  // beneath absolutely positioned siblings such as pixel frames.
  return (
    <View
      pointerEvents="none"
      {...(label
        ? { accessible: true, accessibilityRole: 'image' as const, accessibilityLabel: label }
        : {
            'aria-hidden': true,
            accessibilityElementsHidden: true,
            importantForAccessibility: 'no-hide-descendants' as const,
          })}
      style={[{ width: size, height: size, opacity: muted ? 0.45 : 1 }, style]}
    >
      <Svg width={size} height={size} viewBox={`0 0 ${gridOf(name)} ${gridOf(name)}`}>
        {runsOf(name).map((run) => (
          <Rect
            key={`${run.x},${run.y}`}
            x={run.x}
            y={run.y}
            width={run.w}
            height={1}
            fill={run.fill}
          />
        ))}
      </Svg>
    </View>
  );
}
