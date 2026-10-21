import { View, type StyleProp, type ViewStyle } from 'react-native';
import Svg, { Rect } from 'react-native-svg';
import { iconPalette, iconRows, iconRows2x, type IconName } from '@/lib/icon-art';
import { useInterfaceGrid } from '@/components/pixel-frame';

export type { IconName };

type Run = { x: number; y: number; w: number; fill: string };

const KEYS = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
const cache = new Map<string, Run[]>();

/** The rows drawn: the 32x32 version where the interface draws 2x art and one exists
 *  (scripts/art/icons_2x.py), else the 16x16 one. Both show at the same size. */
const rowsOf = (name: IconName, fine: boolean): readonly string[] =>
  (fine && iconRows2x[name]) || iconRows[name];

/** Each row's same-colour pixels merged into runs, computed once per icon and grid. */
function runsOf(name: IconName, fine: boolean): Run[] {
  const rows = rowsOf(name, fine);
  const cacheKey = `${name}:${rows.length}`;
  const known = cache.get(cacheKey);
  if (known) return known;
  const runs: Run[] = [];
  rows.forEach((row, y) => {
    let x = 0;
    while (x < row.length) {
      const key = row[x];
      let end = x + 1;
      while (end < row.length && row[end] === key) end++;
      if (key !== '.') runs.push({ x, y, w: end - x, fill: iconPalette[KEYS.indexOf(key)] });
      x = end;
    }
  });
  cache.set(cacheKey, runs);
  return runs;
}

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
  // 2x rows where an interface pixel splits into whole device px at the game's density
  // (lib/pixel-scale.ts `interfaceGrid`); a 2x icon draws two texels an interface pixel
  const fine = useInterfaceGrid().density === 2;
  const grid = rowsOf(name, fine).length;
  // The View keeps the icon in normal stacking order: on web a bare SVG paints
  // beneath absolutely positioned siblings such as pixel frames.
  return (
    <View
      {...(label
        ? { accessible: true, accessibilityRole: 'image' as const, accessibilityLabel: label }
        : {
            'aria-hidden': true,
            accessibilityElementsHidden: true,
            importantForAccessibility: 'no-hide-descendants' as const,
          })}
      style={[
        { width: size, height: size, opacity: muted ? 0.45 : 1 },
        style,
        { pointerEvents: 'none' },
      ]}
    >
      <Svg width={size} height={size} viewBox={`0 0 ${grid} ${grid}`}>
        {runsOf(name, fine).map((run) => (
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
