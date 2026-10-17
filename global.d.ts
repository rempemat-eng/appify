declare module '*.css';
declare module '*.png' {
  const source: import('react-native').ImageSourcePropType;
  export default source;
}
declare module '*.wav' {
  // An asset module id; expo-audio resolves it (or a web URL) to a playable source.
  const source: number;
  export default source;
}
