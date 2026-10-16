import { useEffect, useRef, useState } from 'react';
import AsyncStorage from '@react-native-async-storage/async-storage';
import type { ViewMode } from '@/lib/garden-projection';

const KEY = 'napattack-garden-view';

// Device-local display preference for the garden (top-down or 2.5D). Not game
// state: it never syncs and has no effect on rules or rewards.
export function useGardenView(): [ViewMode, (v: ViewMode) => void] {
  const [view, setView] = useState<ViewMode>('flat');
  const chosen = useRef(false);
  useEffect(() => {
    let alive = true;
    AsyncStorage.getItem(KEY)
      .then((v) => {
        if (alive && !chosen.current && (v === 'flat' || v === 'tilt')) setView(v);
      })
      .catch(() => {});
    return () => {
      alive = false;
    };
  }, []);
  const choose = (v: ViewMode) => {
    chosen.current = true;
    setView(v);
    AsyncStorage.setItem(KEY, v).catch(() => {});
  };
  return [view, choose];
}
