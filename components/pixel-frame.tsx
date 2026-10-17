import { useState, type KeyboardEvent, type ReactNode, type Ref } from 'react';
import {
  Platform,
  Pressable,
  TextInput,
  View,
  useWindowDimensions,
  type StyleProp,
  type TextInputProps,
  type TextStyle,
  type ViewStyle,
} from 'react-native';
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
  /** a recessed well: the rim shades the top and left, light catches the bottom */
  field: {
    fill: '#FFFBF0',
    light: '#E1D2B6',
    dark: c.highlight,
    base: c.depth,
    outline: artOutline,
  },
  /** the same well with a gold inner ring, so keyboard focus is always visible */
  fieldFocus: {
    fill: '#FFFBF0',
    light: '#E6BC5C',
    dark: '#E6BC5C',
    base: c.depth,
    outline: artOutline,
  },
  /** night panels on the nap screen, with a lantern-gold rim */
  lantern: {
    fill: '#3C4168',
    light: '#5A608F',
    dark: '#2B2F50',
    base: '#191B30',
    outline: '#C9A24F',
  },
} satisfies Record<string, FrameTone>;
export type FrameToneName = keyof typeof frameTones;

const hex = (color: string) => {
  const match = /^#([0-9a-f]{6})$/i.exec(color);
  return match ? [0, 2, 4].map((i) => parseInt(match[1].slice(i, i + 2), 16)) : null;
};

/** Mixes two #RRGGBB colours; anything else is returned unchanged. */
export function mixColor(a: string, b: string, amount: number) {
  const from = hex(a);
  const to = hex(b);
  if (!from || !to) return a;
  return (
    '#' +
    from
      .map((value, i) =>
        Math.round(value + (to[i] - value) * amount)
          .toString(16)
          .padStart(2, '0'),
      )
      .join('')
  );
}

/** A frame tone for any fill: lit top edge, shaded bottom edge, darker base. */
export function toneFrom(fill: string, outline: string = artOutline): FrameTone {
  return {
    fill,
    light: mixColor(fill, c.highlight, 0.55),
    dark: mixColor(fill, '#4A3B35', 0.16),
    base: mixColor(fill, artOutline, 0.45),
    outline,
  };
}

const resolveTone = (tone: FrameToneName | FrameTone) =>
  typeof tone === 'string' ? frameTones[tone] : tone;

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
  const t = resolveTone(tone);
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

/**
 * The frame alone, drawn behind the content of an existing View, Pressable or
 * Animated.View. Put it first among the children and drop the parent's border
 * and background. `fill` and `outline` derive a tone for one-off colours.
 */
export function FrameFill({
  tone = 'paper',
  fill,
  outline,
  depth = 0,
  inset = false,
}: {
  tone?: FrameToneName | FrameTone;
  fill?: string;
  outline?: string;
  /** a raised base below the frame, in pixel units (it does not take layout space) */
  depth?: number;
  /** recessed: swap the lit and shaded edges */
  inset?: boolean;
}) {
  const u = usePixelUnit();
  const picked = fill ? toneFrom(fill, outline) : resolveTone(tone);
  const outlined = outline && !fill ? { ...picked, outline } : picked;
  const t = inset ? { ...outlined, light: outlined.dark, dark: outlined.light } : outlined;
  return (
    <>
      {depth > 0 && (
        <FrameShape
          tone={{ ...t, fill: t.base, light: t.base, dark: t.base }}
          unit={u}
          offset={depth * u}
          bevel={false}
        />
      )}
      <FrameShape tone={t} unit={u} />
    </>
  );
}

/** A stepped speech-bubble tail that opens into the bottom edge of its parent frame. */
export function PixelTail({
  fill = c.paper,
  outline = artOutline,
}: {
  fill?: string;
  outline?: string;
}) {
  const u = usePixelUnit();
  return (
    <View
      pointerEvents="none"
      aria-hidden
      style={{
        position: 'absolute',
        bottom: -2 * u,
        left: '50%',
        marginLeft: -3 * u,
        width: 6 * u,
        height: 3 * u,
      }}
    >
      {[0, 1, 2].map((row) => (
        <View
          key={row}
          style={abs({
            top: row * u,
            left: row * u,
            right: row * u,
            height: u,
            backgroundColor: outline,
          })}
        >
          {row < 2 && (
            <View
              style={abs({
                top: 0,
                bottom: 0,
                left: u,
                right: u,
                backgroundColor: fill,
              })}
            />
          )}
        </View>
      ))}
    </View>
  );
}

/** An on/off toggle drawn on the pixel grid; a 52 by 44 target around a small track. */
export function PixelSwitch({
  value,
  onValueChange,
  disabled = false,
  accessibilityLabel,
  accessibilityHint,
}: {
  value: boolean;
  onValueChange: (value: boolean) => void;
  disabled?: boolean;
  accessibilityLabel: string;
  accessibilityHint?: string;
}) {
  const u = usePixelUnit();
  const width = 20 * u;
  const height = 11 * u;
  const knob = 7 * u;
  // RN Web's Pressable handles Enter for a switch, but only handles Space for
  // button/menuitem roles. Keep the switch semantics and fill that web-only gap.
  const webKeys =
    Platform.OS === 'web'
      ? {
          onKeyDown: (event: KeyboardEvent<HTMLElement>) => {
            if (
              (event.key !== ' ' && event.key !== 'Spacebar') ||
              event.target !== event.currentTarget ||
              event.altKey ||
              event.ctrlKey ||
              event.metaKey
            )
              return;
            event.preventDefault();
            if (!disabled && !event.repeat) onValueChange(!value);
          },
        }
      : {};
  return (
    <Pressable
      {...webKeys}
      accessibilityRole="switch"
      accessibilityLabel={accessibilityLabel}
      accessibilityHint={accessibilityHint}
      accessibilityState={{ checked: value, disabled }}
      aria-checked={value}
      disabled={disabled}
      onPress={() => onValueChange(!value)}
      style={{
        minWidth: 52,
        minHeight: 44,
        alignItems: 'center',
        justifyContent: 'center',
        opacity: disabled ? 0.55 : 1,
      }}
    >
      <View style={{ width, height }}>
        <FrameShape tone={value ? frameTones.leaf : frameTones.disabled} unit={u} />
        <View
          style={{
            position: 'absolute',
            top: 2 * u,
            left: value ? width - knob - 2 * u : 2 * u,
            width: knob,
            height: knob,
          }}
        >
          <FrameShape tone={frameTones.paper} unit={u} />
        </View>
      </View>
    </Pressable>
  );
}

const inputText: TextStyle = {
  fontFamily: 'PixelifySans_500Medium',
  color: c.ink,
  fontSize: 15,
  minHeight: 52,
  paddingHorizontal: 16,
  paddingVertical: 12,
  backgroundColor: c.transparent,
  borderWidth: 0,
  // the browser ring is replaced by the frame's gold focus ring
  outlineWidth: 0,
};

/** A text field in a recessed pixel well. Focus swaps in a gold inner ring. */
export function PixelInput({
  ref,
  style,
  onFocus,
  onBlur,
  ...props
}: TextInputProps & { ref?: Ref<TextInput> }) {
  const u = usePixelUnit();
  const [focused, setFocused] = useState(false);
  return (
    <View
      style={{
        minHeight: 52,
        justifyContent: 'center',
        opacity: props.editable === false ? 0.6 : 1,
      }}
    >
      <FrameShape tone={focused ? frameTones.fieldFocus : frameTones.field} unit={u} />
      <TextInput
        ref={ref}
        {...props}
        onFocus={(event) => {
          setFocused(true);
          onFocus?.(event);
        }}
        onBlur={(event) => {
          setFocused(false);
          onBlur?.(event);
        }}
        style={[inputText, style]}
      />
    </View>
  );
}
