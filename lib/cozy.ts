import { palette } from '@/lib/game';

// Presentation-only colors. The original sprite and scene palettes remain untouched.
export const cozy = {
  ...palette,
  paper: '#FBF4E4',
  body: '#F7EDD9',
  error: '#C0634A',
  outline: 'rgba(74,59,53,0.7)',
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
export const panelStyle = {
  borderRadius: 14,
  borderWidth: 2,
  borderColor: cozy.outline,
  backgroundColor: cozy.paper,
  boxShadow: '0 3px 0 rgba(74,59,53,.25), 0 8px 16px rgba(0,0,0,.08)',
} as const;
