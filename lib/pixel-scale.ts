import { gameLayout } from '@/lib/layout';

/**
 * The game's one pixel grid (docs/vision/coherence-plan.md, step 6).
 *
 * One art pixel is a whole number of device pixels, chosen so that about
 * ART_ACROSS art pixels fit across the play area: 4 device pixels (1.33 CSS px)
 * on a 3x phone, 3 on most 2x phones, 2 on a desktop. A narrow window on a 1x screen
 * falls back to one device pixel, so the interface still fits (a 320 px window at 1x
 * would otherwise show only 160 art pixels across). The world, the characters,
 * the frames and the icons all use this one scale (`usePixelUnit` in
 * components/pixel-frame.tsx reads it for the current window). Pure, so it can be tested.
 */
export const ART_ACROSS = 300;

/** CSS pixels per art pixel for a play area this wide on a screen of this density. */
export function pixelScale(width: number, dpr: number) {
  const across = Math.min(width, gameLayout.maxWidth);
  const ratio = dpr > 0 ? dpr : 1;
  const device = Math.max(1, Math.round((across * ratio) / ART_ACROSS));
  return device / ratio;
}

/** Round a CSS length to whole device pixels, so an art pixel never straddles two. */
export function snapToDevice(value: number, dpr: number) {
  const ratio = dpr > 0 ? dpr : 1;
  return Math.round(value * ratio) / ratio;
}
