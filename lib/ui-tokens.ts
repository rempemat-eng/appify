import type { TextStyle } from 'react-native';

/**
 * Interface tokens (docs/vision/coherence-plan.md, step 3).
 *
 * Spacing is in art pixels (the game's one pixel grid, `usePixelUnit()`, about 1.33 CSS
 * px on a 3x phone), so every bar, panel and button sits on the same grid as the world.
 *
 * The symmetry rule: every bar, panel and slot has ONE inset, used on all four
 * sides and between its children. Nothing touches a frame's edge.
 */
export const space = {
  /** a frame's own edge: the outline plus the bevel */
  border: 2,
  /** the one inset inside every bar, panel and slot, and the gap between siblings */
  inset: 3,
  /** the roomier inset inside sheets and panels that hold reading text */
  panel: 6,
} as const;

/** Where content starts inside a frame, measured from its outer edge. */
export const contentInset = (u: number) => (space.border + space.inset) * u;
/** Where content starts inside a sheet's paper panel: the same on all four sides. */
export const panelInset = (u: number) => (space.border + space.panel) * u;
/** The gap between sections in a sheet (equal to the panel inset's spacing). */
export const panelGap = (u: number) => space.panel * u;
/** The gap between siblings in a bar or panel (equal to the inset). */
export const siblingGap = (u: number) => space.inset * u;

/** One square control size shared by bars: portrait, menu button, stat chips. */
export const barControl = (u: number) => 27 * u;
/** Hotbar slot height (icon plus label): 36 art pixels, and never under a 44 px target. */
export const hotbarSlot = (u: number) => Math.max(36, Math.ceil(44 / u)) * u;

/** Icons are drawn on a 16x16 grid and shown at 1x on the shared grid (2x for a feature
 * button), so an icon's pixels are the world's pixels. */
export const iconSize = {
  small: (u: number) => 16 * u,
  medium: (u: number) => 16 * u,
  large: (u: number) => 32 * u,
} as const;

/** HUD bar outer height, including its one-unit raised base. */
export const hudBarHeight = (u: number) => barControl(u) + 2 * contentInset(u) + u;
/** Hotbar outer height, including its one-unit raised base. */
export const hotbarHeight = (u: number) => hotbarSlot(u) + 2 * contentInset(u) + u;

/**
 * The type hierarchy. Pixelify Sans everywhere; Press Start 2P only for sheet titles and
 * big numbers. Line heights are multiples of 4, so single-line labels centre cleanly.
 * Colour comes from the text component (ink by default).
 */
export const type = {
  /** sheet and page titles: the chunky display face, one size everywhere */
  title: { fontFamily: 'PressStart2P_400Regular', fontSize: 16, lineHeight: 24 },
  /** panel headings, the selected item's name */
  heading: { fontFamily: 'PixelifySans_700Bold', fontSize: 16, lineHeight: 24 },
  /** descriptions */
  body: { fontFamily: 'PixelifySans_500Medium', fontSize: 14, lineHeight: 20 },
  /** tabs, buttons, stat names and values, section labels (write them in capitals) */
  label: { fontFamily: 'PixelifySans_700Bold', fontSize: 12, lineHeight: 16 },
  /** hints and small print */
  caption: { fontFamily: 'PixelifySans_500Medium', fontSize: 11, lineHeight: 16 },
} as const satisfies Record<string, TextStyle>;

/** Separation layers: a well sits darker than the panel it is cut into. */
export const layers = {
  well: '#EADDC2',
} as const;
