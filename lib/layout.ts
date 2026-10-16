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
