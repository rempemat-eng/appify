import { useSyncExternalStore } from 'react';
import { AppState, Platform } from 'react-native';

// Navigation focus stays true when the app is backgrounded. Decorative worlds
// also need the platform's foreground state so a real-world break stays quiet.
const snapshot = () => {
  const state = AppState.currentState;
  const foreground = state === 'active' || state === null;
  return (
    foreground &&
    (Platform.OS !== 'web' ||
      typeof document === 'undefined' ||
      document.visibilityState !== 'hidden')
  );
};

const subscribe = (notify: () => void) => {
  const subscription = AppState.addEventListener('change', notify);
  const webDocument = Platform.OS === 'web' && typeof document !== 'undefined' ? document : null;
  webDocument?.addEventListener('visibilitychange', notify);
  return () => {
    subscription.remove();
    webDocument?.removeEventListener('visibilitychange', notify);
  };
};

const serverSnapshot = () => false;

export function useAppActive() {
  return useSyncExternalStore(subscribe, snapshot, serverSnapshot);
}
