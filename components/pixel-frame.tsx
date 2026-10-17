import type { ReactNode } from 'react';
import { View, useWindowDimensions, type StyleProp, type ViewStyle } from 'react-native';
import { cozy as c } from '@/lib/cozy';
import { artOutline } from '@/lib/art-direction';
import { gameLayout } from '@/lib/layout';

/**
 * Pixel-art frames for every surface: notched corners, a one-pixel outline, a
 * lit top edge, a shaded bottom edge and an optional raised base. The unit is
 * the same screen size as one garden pixel, so the HUD and world share a grid.
 */
export type FrameTone = {
  fill: string;
  light: string;
  dark: string;
  base: string;
  outline: string;
};

export const frameTones = {
  paper: { fill: c.paper, light: c.highlight, dark: c.inset, base: c.depth, outline: artOutline },
  parchment: {
    fill: '#F3E6C8',
    light: '#FFF7E2',
    dark: '#DCC9A2',
    base: '#B39A70',
    outline: artOutline,
  },
  leaf: { fill: '#6FB35E', light: '#A5D77F', dark: '#4F8D45', base: '#2F5A2C', outline: '#24361F' },
  gold: { fill: '#E6BC5C', light: '#F8DD8F', dark: '#BF8F36', base: '#7F5B1E', outline: '#3B2A14' },
  nap: { fill: '#9F8CD3', light: '#CBBDF0', dark: '#7663B0', base: '#4C3F80', outline: '#2A2244' },
  danger: {
    fill: '#D47A5C',
    light: '#F0A688',
    dark: '#AE5A40',
    base: '#6E3424',
    outline: '#3A1B13',
  },
  night: {
    fill: '#3C4168',
    light: '#5A608F',
    dark: '#2B2F50',
    base: '#191B30',
    outline: '#0F1020',
  },
  glass: {
    fill: 'rgba(251,244,228,0.92)',
    light: '#FFFDF5',
    dark: '#E1D2B6',
    base: 'rgba(42,36,33,0.35)',
    outline: artOutline,
  },
  disabled: {
    fill: '#D9D1BF',
    light: '#ECE6D8',
    dark: '#C1B7A2',
    base: '#9C927C',
    outline: '#5E544A',
  },
} satisfies Record<string, FrameTone>;
export type FrameToneName = keyof typeof frameTones;

/** One garden pixel on screen: 2 on phones, 3 in the wider column. */
export function usePixelUnit() {
  const { width } = useWindowDimensions();
  return Math.max(2, Math.round(Math.min(width, gameLayout.maxWidth) / 192));
}

const abs = (style: ViewStyle): ViewStyle => ({ position: 'absolute', ...style });

/** The notched shape alone, filling its parent. Decorative and never focusable. */
export function FrameShape({
  tone,
  unit: u,
  offset = 0,
  bevel = true,
}: {
  tone: FrameTone;
  unit: number;
  /** shifts the whole shape down (used for a button's raised base) */
  offset?: number;
  bevel?: boolean;
}) {
  const top = offset;
  const bottom = -offset;
  return (
    <View
      pointerEvents="none"
      aria-hidden
      accessibilityElementsHidden
      importantForAccessibility="no-hide-descendants"
      style={abs({ left: 0, right: 0, top, bottom })}
    >
      {/* fill: two overlapping rectangles leave the corner pixels open */}
      <View
        style={abs({ left: 2 * u, right: 2 * u, top: u, bottom: u, backgroundColor: tone.fill })}
      />
      <View
        style={abs({ left: u, right: u, top: 2 * u, bottom: 2 * u, backgroundColor: tone.fill })}
      />
      {bevel && (
        <>
          <View
            style={abs({
              left: 2 * u,
              right: 2 * u,
              top: u,
              height: u,
              backgroundColor: tone.light,
            })}
          />
          <View
            style={abs({
              left: u,
              top: 2 * u,
              bottom: 3 * u,
              width: u,
              backgroundColor: tone.light,
            })}
          />
          <View
            style={abs({
              left: 2 * u,
              right: 2 * u,
              bottom: u,
              height: u,
              backgroundColor: tone.dark,
            })}
          />
          <View
            style={abs({
              right: u,
              top: 3 * u,
              bottom: 2 * u,
              width: u,
              backgroundColor: tone.dark,
            })}
          />
        </>
      )}
      {/* outline */}
      <View
        style={abs({ left: 2 * u, right: 2 * u, top: 0, height: u, backgroundColor: tone.outline })}
      />
      <View
        style={abs({
          left: 2 * u,
          right: 2 * u,
          bottom: 0,
          height: u,
          backgroundColor: tone.outline,
        })}
      />
      <View
        style={abs({ left: 0, top: 2 * u, bottom: 2 * u, width: u, backgroundColor: tone.outline })}
      />
      <View
        style={abs({
          right: 0,
          top: 2 * u,
          bottom: 2 * u,
          width: u,
          backgroundColor: tone.outline,
        })}
      />
      <View style={abs({ left: u, top: u, width: u, height: u, backgroundColor: tone.outline })} />
      <View style={abs({ right: u, top: u, width: u, height: u, backgroundColor: tone.outline })} />
      <View
        style={abs({ left: u, bottom: u, width: u, height: u, backgroundColor: tone.outline })}
      />
      <View
        style={abs({ right: u, bottom: u, width: u, height: u, backgroundColor: tone.outline })}
      />
    </View>
  );
}

/** A framed surface. `style` lays out the content inside the frame. */
export function PixelFrame({
  children,
  tone = 'paper',
  depth = 0,
  style,
  unit,
}: {
  children?: ReactNode;
  tone?: FrameToneName | FrameTone;
  /** raised base below the frame, in pixel units */
  depth?: number;
  style?: StyleProp<ViewStyle>;
  unit?: number;
}) {
  const fallback = usePixelUnit();
  const u = unit ?? fallback;
  const t = typeof tone === 'string' ? frameTones[tone] : tone;
  return (
    <View style={[{ marginBottom: depth * u, padding: 3 * u }, style]}>
      {depth > 0 && (
        <FrameShape
          tone={{ ...t, fill: t.base, light: t.base, dark: t.base }}
          unit={u}
          offset={depth * u}
          bevel={false}
        />
      )}
      <FrameShape tone={t} unit={u} />
      {children}
    </View>
  );
}
