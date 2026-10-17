import type { TextStyle } from 'react-native';

/**
 * Interface tokens (docs/vision/coherence-plan.md, step 3).
 *
 * Spacing is in pixel units (one garden pixel on screen, `usePixelUnit()`), so a
 * density change carries every bar, panel and button along with the world.
 *
 * The symmetry rule: every bar, panel and slot has ONE inset, used on all four
 * sides and between its children. Nothing touches a frame's edge.
 */
export const space = {
  /** a frame's own edge: the outline plus the bevel */
  border: 2,
  /** the one inset inside every bar, panel and slot, and the gap between siblings */
  inset: 2,
} as const;

/** Where content starts inside a frame, measured from its outer edge. */
export const contentInset = (u: number) => (space.border + space.inset) * u;
/** The gap between siblings in a bar or panel (equal to the inset). */
export const siblingGap = (u: number) => space.inset * u;

/** One square control size shared by bars: portrait, menu button, stat chips. */
export const barControl = (u: number) => 18 * u;
/** Hotbar slot height (icon plus label, at least a 44 px target on phones). */
export const hotbarSlot = (u: number) => 24 * u;

/** HUD bar outer height, including its one-unit raised base. */
export const hudBarHeight = (u: number) => barControl(u) + 2 * contentInset(u) + u;
/** Hotbar outer height, including its one-unit raised base. */
export const hotbarHeight = (u: number) => hotbarSlot(u) + 2 * contentInset(u) + u;

/**
 * The type hierarchy. Pixelify Sans everywhere; Press Start 2P (PixelText) only for
 * big numbers. Line heights are multiples of 4, so single-line labels centre cleanly.
 * Colour comes from the text component (ink by default).
 */
export const type = {
  /** sheet and page titles */
  title: { fontFamily: 'PixelifySans_700Bold', fontSize: 20, lineHeight: 28 },
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
