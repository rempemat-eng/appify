import { Platform } from 'react-native';
import { ART_DENSITY_DEFAULT, densityFromQuery, type ArtDensity } from './art-density';

/** The art density on the web: `?density=1`, `1.5` or `2` in the address overrides the
 *  default for a pilot side by side (lib/art-density-setting.ts). */
function fromAddress(): ArtDensity | null {
  if (Platform.OS !== 'web') return null;
  return densityFromQuery(window.location?.search ?? '');
}

export const ART_DENSITY: ArtDensity = fromAddress() ?? ART_DENSITY_DEFAULT;
