import { create } from 'zustand';

// Interface-only state for the game's sheets. Nothing here is saved or synced:
// it decides which menu is open, never anything about the garden or rewards.
export type GameSheet = 'nap' | 'menu' | 'companions' | 'rhythm';

/** The game menu's pages (coherence plan, step 5). */
export type MenuTab = 'companion' | 'bag' | 'journal' | 'garden' | 'rhythm' | 'settings';

type UiState = {
  sheet: GameSheet | null;
  /** A sheet opened from the menu returns to the menu when it closes. */
  back: GameSheet | null;
  menuTab: MenuTab;
  open: (sheet: GameSheet) => void;
  close: () => void;
  closeAll: () => void;
  openMenu: (tab?: MenuTab) => void;
};

export const useUi = create<UiState>((set) => ({
  sheet: null,
  back: null,
  menuTab: 'companion',
  open: (sheet) =>
    set((s) => ({ sheet, back: s.sheet === 'menu' && sheet !== 'menu' ? 'menu' : null })),
  close: () => set((s) => ({ sheet: s.back, back: null })),
  closeAll: () => set({ sheet: null, back: null }),
  openMenu: (tab) => set((s) => ({ sheet: 'menu', back: null, menuTab: tab ?? s.menuTab })),
}));

export const openSheet = (sheet: GameSheet) => useUi.getState().open(sheet);
export const closeSheet = () => useUi.getState().close();
export const closeAllSheets = () => useUi.getState().closeAll();
export const openMenu = (tab?: MenuTab) => useUi.getState().openMenu(tab);
