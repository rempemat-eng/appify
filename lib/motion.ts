import { useSyncExternalStore } from 'react';
import { AccessibilityInfo } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { create } from 'zustand';

const key = 'screenagotchi-reduced-motion';
// This callable Zustand store is a Hook: the use-prefix keeps compiler calls unconditional.
export const useMotionPreference = create<{
  reduced: boolean;
  system: boolean;
  loaded: boolean;
  setReduced: (value: boolean) => Promise<void>;
}>((set) => ({
  reduced: false,
  system: false,
  loaded: false,
  setReduced: async (reduced) => {
    await AsyncStorage.setItem(key, JSON.stringify(reduced));
    set({ reduced, loaded: true });
  },
}));
export async function loadMotionPreference() {
  const [saved, system] = await Promise.allSettled([
    AsyncStorage.getItem(key),
    AccessibilityInfo.isReduceMotionEnabled(),
  ]);
  useMotionPreference.setState((state) => ({
    reduced: state.loaded ? state.reduced : saved.status === 'fulfilled' && saved.value === 'true',
    system: system.status === 'fulfilled' ? system.value : state.system,
    loaded: true,
  }));
}
export function watchSystemMotion() {
  const subscription = AccessibilityInfo.addEventListener('reduceMotionChanged', (system) => {
    useMotionPreference.setState({ system });
  });
  return () => subscription.remove();
}
const reducedSnapshot = () => {
  const state = useMotionPreference.getState();
  return !state.loaded || state.system || state.reduced;
};
// One unconditional subscription on every render, including saved-game hydration.
// An app preference can reduce motion further, but never override the OS preference.
export function useReducedMotion() {
  return useSyncExternalStore(useMotionPreference.subscribe, reducedSnapshot, reducedSnapshot);
}
