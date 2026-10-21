import { create } from 'zustand';

// Interface-only state for the game's sheets. Nothing here is saved or synced:
// it decides which menu is open, never anything about the garden or rewards.
export type GameSheet = 'nap' | 'menu' | 'companions' | 'rhythm' | 'map';

/** The game menu's pages (coherence plan, step 5). */
export type MenuTab = 'companion' | 'bag' | 'journal' | 'garden' | 'map' | 'rhythm' | 'settings';

/** How the game opens the world screen: walking out of the garden (where, which way),
 *  at a place, or at a station. Read once by the world when it opens; not in the page's
 *  address, so a reload resumes from where the companion last stood (the save). */
export type WorldLink = {
  from?: 'gate' | 'trail' | 'west' | 'east' | 'hut';
  place?: string;
  station?: string;
  ex?: number;
  ey?: number;
  /** open the hut already decorating (from the garden's decorate panel) */
  decorate?: boolean;
  /** a journey chosen at a station in the home hub: it plays on the world screen, and
   *  one back to the valley lands in the hub again (docs/vision/home-hub.md) */
  trip?: { from: string; to: string };
};

type UiState = {
  sheet: GameSheet | null;
  /** A sheet opened from the menu returns to the menu when it closes. */
  back: GameSheet | null;
  menuTab: MenuTab;
  open: (sheet: GameSheet) => void;
  close: () => void;
  closeAll: () => void;
  openMenu: (tab?: MenuTab) => void;
  /** Where the next spar happens (a region's ring in the world), for the battle's backdrop
   * only; null is the garden's own field. Presentation, never a rule. */
  battlePlace: string | null;
  worldLink: WorldLink | null;
  /** Walked back into the garden from the valley: where its companion stands (garden
   *  pixels); a new key moves it again. */
  homeArrival: { x: number; y: number; key: string } | null;
  /** Decorating the garden (C12): the home screen shows the keepsakes and takes taps. */
  gardenDecorating: boolean;
};

export const useUi = create<UiState>((set) => ({
  sheet: null,
  back: null,
  menuTab: 'companion',
  battlePlace: null,
  worldLink: null,
  homeArrival: null,
  gardenDecorating: false,
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
