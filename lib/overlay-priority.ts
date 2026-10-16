export type GameOverlay =
  | 'loading'
  | 'onboarding'
  | 'nap'
  | 'welcome'
  | 'recap'
  | 'battle'
  | 'alert'
  | 'growth'
  | 'guide'
  | 'deck';

// Rendering and Back must agree about which layer the player can see.
export function topGameOverlay(state: {
  ready: boolean;
  hasPlayer: boolean;
  napping: boolean;
  welcome: boolean;
  recap: boolean;
  battle: boolean;
  alert: boolean;
  growth: boolean;
  guide: boolean;
  deck: boolean;
}): GameOverlay | null {
  if (!state.ready) return 'loading';
  if (!state.hasPlayer) return 'onboarding';
  if (state.napping) return 'nap';
  if (state.welcome) return 'welcome';
  if (state.recap) return 'recap';
  if (state.battle) return 'battle';
  if (state.alert) return 'alert';
  if (state.growth) return 'growth';
  if (state.guide) return 'guide';
  if (state.deck) return 'deck';
  return null;
}
