import type { KeyboardEvent } from 'react';
import { Platform } from 'react-native';

/** The Space handler itself, for call sites that wire `onKeyDown` inline. */
export function onSwitchKey(
  event: KeyboardEvent<HTMLElement>,
  toggle: () => void,
  disabled = false,
) {
  if (
    (event.key !== ' ' && event.key !== 'Spacebar') ||
    event.target !== event.currentTarget ||
    event.altKey ||
    event.ctrlKey ||
    event.metaKey
  )
    return;
  event.preventDefault();
  if (!disabled && !event.repeat) toggle();
}

/**
 * Keyboard support for any Pressable with accessibilityRole="switch".
 *
 * React Native Web's Pressable activates a switch with Enter, but only treats
 * Space as activation for button and menuitem roles. Spread the result onto
 * the Pressable: Space then toggles once, never scrolls the page, ignores a
 * held key, modifier shortcuts and events from descendants. Native presses
 * stay with Pressable, so other platforms get no handler.
 */
export function switchKeys(toggle: () => void, disabled = false) {
  if (Platform.OS !== 'web') return {};
  return {
    onKeyDown: (event: KeyboardEvent<HTMLElement>) => onSwitchKey(event, toggle, disabled),
  };
}
