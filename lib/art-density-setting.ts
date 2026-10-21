import { ART_DENSITY_DEFAULT, type ArtDensity } from './art-density';

/**
 * The game's art density (lib/art-density.ts): texels per world pixel on the shared grid
 * (lib/pixel-scale.ts). Native reads only the default; on the web, `?density=1`, `1.5` or
 * `2` in the address overrides it for a pilot (lib/art-density-setting.web.ts).
 */
export const ART_DENSITY: ArtDensity = ART_DENSITY_DEFAULT;
