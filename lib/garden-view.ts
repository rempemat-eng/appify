import { useSyncExternalStore } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import type { ViewMode } from '@/lib/garden-projection';

const KEY = 'napattack-garden-view';
let current: ViewMode = 'flat';
let chosen = false;
let loading: Promise<void> | null = null;
let writes: Promise<void> = Promise.resolve();
const listeners = new Set<() => void>();
const snapshot = () => current;
const serverSnapshot = (): ViewMode => 'flat';
const emit = () => listeners.forEach((listener) => listener());

function hydrate() {
  loading ??= AsyncStorage.getItem(KEY)
    .then((value) => {
      if (!chosen && (value === 'flat' || value === 'tilt') && value !== current) {
        current = value;
        emit();
      }
    })
    .catch(() => {});
}
function subscribe(listener: () => void) {
  listeners.add(listener);
  hydrate();
  return () => listeners.delete(listener);
}
function choose(value: ViewMode) {
  chosen = true;
  if (value !== current) {
    current = value;
    emit();
  }
  // Preserve the order of quick choices even on a slow storage backend.
  writes = writes.then(() => AsyncStorage.setItem(KEY, value)).catch(() => {});
}

// Shared device-local display preference: Home and the nap scene agree
// immediately, including while a saved preference is still loading.
export function useGardenView(): [ViewMode, (view: ViewMode) => void] {
  return [useSyncExternalStore(subscribe, snapshot, serverSnapshot), choose];
}
