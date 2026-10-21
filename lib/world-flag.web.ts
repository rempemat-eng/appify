import { Platform } from 'react-native';
import { WORLD_CANVAS_DEFAULT } from './world-flag-default';

/** The world canvas switch on the web: `?world=canvas` or `?world=zones` in the address
 *  overrides the default for a play-test (lib/world-flag.ts). */
function fromAddress(): boolean | null {
  if (Platform.OS !== 'web') return null;
  const query = window.location?.search ?? '';
  if (/[?&]world=canvas\b/.test(query)) return true;
  if (/[?&]world=zones\b/.test(query)) return false;
  return null;
}

export const WORLD_CANVAS: boolean = fromAddress() ?? WORLD_CANVAS_DEFAULT;
