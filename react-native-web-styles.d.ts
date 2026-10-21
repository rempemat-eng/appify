// Style keys react-native-web reads that React Native's types do not list. Use them only
// on the web (behind Platform.OS === 'web'); native ignores them.
import type { TextStyle as _TextStyle } from 'react-native';
export type WebTextStyle = _TextStyle;

declare module 'react-native' {
  interface TextStyle {
    /** CSS text-shadow shorthand; react-native-web 0.21 deprecates the textShadow* trio */
    textShadow?: string;
  }
}
