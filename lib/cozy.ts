import { palette } from '@/lib/game';
import { artSurface } from '@/lib/art-direction';

// Field-journal surfaces share their materials with the world art.
export const cozy = {
  ...palette,
  ...artSurface,
  error: '#C0634A',
  outline: artSurface.edge,
  shadow: 'rgba(74,59,53,0.25)',
  ambient: 'rgba(0,0,0,0.08)',
  sage: '#E4EBD9',
  highlight: '#FFFDF5',
  faded: '#DED8C8',
  rest: '#CDBFE3',
  nap: '#8E7CC3',
  napOutline: '#5C4E83',
  leafOutline: '#386334',
  roam: '#5FA35A',
  focus: '#D8AF5E',
  silver: '#A0ABB2',
  goldFrame: '#B08B39',
  glass: 'rgba(251,244,228,0.86)',
  transparent: 'transparent',
};
