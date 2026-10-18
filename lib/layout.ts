import { hotbarHeight, hudBarHeight } from '@/lib/ui-tokens';
import type { ViewStyle } from 'react-native';

export const gameLayout = {
  maxWidth: 640,
  gutter: 16,
  dockHeight: 76,
  dockBottomGap: 12,
} as const;

export const gameColumn: ViewStyle = {
  width: '100%',
  maxWidth: gameLayout.maxWidth,
  alignSelf: 'center',
};

// Align floating controls with the padded content inside the centred game column.
export function gameSideInset(viewportWidth: number) {
  return Math.max(0, (viewportWidth - gameLayout.maxWidth) / 2) + gameLayout.gutter;
}

export function dockClearance(bottomInset: number) {
  return gameLayout.dockHeight + gameLayout.dockBottomGap + gameLayout.gutter + bottomInset;
}

/** The floating HUD and hotbar: their gap from the screen edge (heights come from ui-tokens). */
export const hudLayout = { gap: 6 } as const;
/** Space the HUD takes at the top of every tab. `u` is the pixel unit (2 on phones). */
export function hudClearance(topInset: number, u = 2) {
  return topInset + hudLayout.gap + hudBarHeight(u) + gameLayout.gutter / 2;
}
/** Space the pixel hotbar takes at the bottom of every tab. `u` is the pixel unit (2 on phones). */
export function hotbarClearance(bottomInset: number, u = 2) {
  return bottomInset + hudLayout.gap + hotbarHeight(u) + gameLayout.gutter;
}

/**
 * Grows a small control's touch area to 44 px on every platform (`hitSlop` is ignored on
 * the web): the pressable is padded outward and pulled back by the same negative margin,
 * so the layout and the drawing stay where they were. Put the drawing in a child view.
 */
export function touchReach(width: number, height = width) {
  const x = Math.max(0, Math.ceil((44 - width) / 2));
  const y = Math.max(0, Math.ceil((44 - height) / 2));
  return { paddingHorizontal: x, paddingVertical: y, marginHorizontal: -x, marginVertical: -y };
}
