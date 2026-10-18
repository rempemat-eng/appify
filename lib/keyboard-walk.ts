import { useEffect, useRef } from 'react';
import { Platform } from 'react-native';

/**
 * Walk the companion with the arrow keys or WASD (web builds; touch stays the main
 * control, this is an extra). While keys are held, `step(dx, dy)` is called every
 * STEP_MS with a unit direction (diagonals normalised); when the last key is released
 * `stop()` is called once. Keys typed into a text field are ignored, and nothing runs
 * while `enabled` is false (an inactive screen, a nap, a card that owns the keys).
 */
export const STEP_MS = 120;

const KEYS: Record<string, readonly [number, number]> = {
  ArrowUp: [0, -1],
  ArrowDown: [0, 1],
  ArrowLeft: [-1, 0],
  ArrowRight: [1, 0],
  w: [0, -1],
  s: [0, 1],
  a: [-1, 0],
  d: [1, 0],
  W: [0, -1],
  S: [0, 1],
  A: [-1, 0],
  D: [1, 0],
};

/** The direction the held keys point in, or null when they cancel out or none are held. */
export function heldDirection(held: Iterable<string>): { dx: number; dy: number } | null {
  let x = 0;
  let y = 0;
  const seen = new Set<string>();
  for (const key of held) {
    const v = KEYS[key];
    if (!v) continue;
    const id = `${v[0]},${v[1]}`;
    if (seen.has(id)) continue; // 'w' and 'ArrowUp' together still mean one step up
    seen.add(id);
    x += v[0];
    y += v[1];
  }
  if (!x && !y) return null;
  const n = Math.hypot(x, y);
  return { dx: x / n, dy: y / n };
}

const typing = (target: EventTarget | null) => {
  if (!target || typeof target !== 'object') return false;
  const tag = 'tagName' in target ? target.tagName : undefined;
  const editable = 'isContentEditable' in target ? target.isContentEditable : false;
  return tag === 'INPUT' || tag === 'TEXTAREA' || editable === true;
};

export function useKeyboardWalk(
  enabled: boolean,
  step: (dx: number, dy: number) => void,
  stop: () => void,
) {
  const calls = useRef({ step, stop });
  useEffect(() => {
    calls.current = { step, stop };
  });
  useEffect(() => {
    if (!enabled || Platform.OS !== 'web' || typeof window === 'undefined') return undefined;
    const held = new Set<string>();
    let timer: ReturnType<typeof setInterval> | null = null;
    const halt = () => {
      if (timer) clearInterval(timer);
      timer = null;
      calls.current.stop();
    };
    const tick = () => {
      const dir = heldDirection(held);
      if (!dir) {
        halt();
        return;
      }
      calls.current.step(dir.dx, dir.dy);
    };
    const down = (e: KeyboardEvent) => {
      if (!KEYS[e.key] || e.altKey || e.ctrlKey || e.metaKey || typing(e.target)) return;
      e.preventDefault(); // the arrows would otherwise scroll the page
      held.add(e.key);
      if (!timer) {
        tick();
        timer = setInterval(tick, STEP_MS);
      }
    };
    const up = (e: KeyboardEvent) => {
      held.delete(e.key);
      held.delete(e.key.length === 1 ? e.key.toLowerCase() : e.key);
      held.delete(e.key.length === 1 ? e.key.toUpperCase() : e.key);
      if (!heldDirection(held) && timer) halt();
    };
    const clear = () => {
      held.clear();
      if (timer) halt();
    };
    window.addEventListener('keydown', down);
    window.addEventListener('keyup', up);
    window.addEventListener('blur', clear);
    return () => {
      window.removeEventListener('keydown', down);
      window.removeEventListener('keyup', up);
      window.removeEventListener('blur', clear);
      if (timer) clearInterval(timer);
    };
  }, [enabled]);
}
