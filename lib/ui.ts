import { create } from 'zustand';

// Interface-only state for the game's sheets. Nothing here is saved or synced:
// it decides which menu is open, never anything about the garden or rewards.
export type GameSheet = 'nap' | 'menu' | 'companions' | 'rhythm' | 'stats' | 'trail';

type UiState = {
  sheet: GameSheet | null;
  open: (sheet: GameSheet) => void;
  close: () => void;
};

export const useUi = create<UiState>((set) => ({
  sheet: null,
  open: (sheet) => set({ sheet }),
  close: () => set({ sheet: null }),
}));

export const openSheet = (sheet: GameSheet) => useUi.getState().open(sheet);
export const closeSheet = () => useUi.getState().close();
