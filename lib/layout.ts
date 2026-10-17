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

/** The floating HUD at the top of every tab: inset, frame and a small gap. */
export const hudLayout = { gap: 6, height: 56, hotbar: 68 } as const;
export function hudClearance(topInset: number) {
  return topInset + hudLayout.gap + hudLayout.height + gameLayout.gutter / 2;
}
/** Space the pixel hotbar takes at the bottom of every tab. */
export function hotbarClearance(bottomInset: number) {
  return bottomInset + hudLayout.gap + hudLayout.hotbar + gameLayout.gutter;
}
