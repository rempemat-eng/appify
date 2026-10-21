import { Platform } from 'react-native';
import { REST_RECOGNITION_DEFAULT } from './rest-flag-default';

/** On the web, `?rest=recognise` or `?rest=today` in the address overrides the default for
 *  a play-test (lib/rest-flag.ts). */
function fromAddress(): boolean | null {
  if (Platform.OS !== 'web') return null;
  const query = window.location?.search ?? '';
  if (/[?&]rest=recognise\b/.test(query)) return true;
  if (/[?&]rest=today\b/.test(query)) return false;
  return null;
}

export const REST_RECOGNITION: boolean = fromAddress() ?? REST_RECOGNITION_DEFAULT;
