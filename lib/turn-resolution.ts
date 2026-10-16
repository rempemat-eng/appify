import type { Combat } from './battle';

export function combatTurnId(state: Combat) {
  return `${state.side}:${state[state.side].turns}`;
}

// An effect may be cancelled and restarted while its turn is still animating.
// Reuse that turn's result instead of spending another card or rolling damage again.
export function createTurnResolutionGate<T>() {
  const resolved = new Map<string, { value: T }>();
  return {
    resolve(turnId: string, resolve: () => T): { value: T; first: boolean } {
      const previous = resolved.get(turnId);
      if (previous) return { value: previous.value, first: false };
      const value = resolve();
      resolved.set(turnId, { value });
      return { value, first: true };
    },
  };
}
