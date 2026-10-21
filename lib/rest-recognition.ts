/**
 * Rest recognition, tier 0: a PROTOTYPE behind REST_RECOGNITION (lib/rest-flag.ts), off by
 * default. Claude L, 21 Oct; docs/mechanics/rest-recognition.md.
 *
 * Today a declared nap pays for every second the device clock moves, whatever the phone
 * does: the game left open on the nap screen pays, a clock set forward pays the jump, a
 * clock set back freezes the nap. This keeps the declared nap (the player choosing to rest
 * is the honest core) and only measures it more truthfully. It needs no permission, reads
 * nothing about other apps and sends nothing anywhere. It never takes Dream Dust away.
 *
 * Units: "credited minutes", the unit `offline_seconds` counts (one real second on the
 * demo clock, `lib/offline-rules.ts`). Every number is a proposal for Matt.
 */
export const restRecognitionRules = {
  /** After starting a nap or opening the game during one, this long in the foreground
   *  still counts, so the player can put the phone down. Real milliseconds. */
  foregroundGraceMs: 60_000,
  /** A forgotten nap settles: at most this much is credited in one nap. 12 h. */
  maxNapMinutes: 12 * 60,
  /** At most this much rest is credited in one local day. 16 h. */
  maxDayMinutes: 16 * 60,
} as const;

export type NapTick = {
  /** Wall-clock milliseconds since the last credited tick (may be negative). */
  wallMs: number;
  /** Whether the game is in the foreground now, and since when (wall ms ago). */
  foreground: boolean;
  foregroundForMs: number;
  /** Minutes already credited in this nap and in this local day. */
  creditedThisNap: number;
  creditedToday: number;
};

export type NapCredit = {
  /** Minutes to credit for this tick. */
  minutes: number;
  /** Move the anchor to now without crediting (a clock set back, or foreground time). */
  reanchor: boolean;
  reason: 'rest' | 'clock-back' | 'foreground' | 'nap-cap' | 'day-cap';
};

export function recogniseNap(t: NapTick, rules = restRecognitionRules): NapCredit {
  if (t.wallMs < 0) return { minutes: 0, reanchor: true, reason: 'clock-back' };
  // The game open past the grace: time spent looking at the nap screen is not rest.
  if (t.foreground && t.foregroundForMs > rules.foregroundGraceMs)
    return { minutes: 0, reanchor: true, reason: 'foreground' };
  // A clock set forward with the app open moves foregroundForMs too (it is measured on
  // the same wall clock), so the rule above already pays nothing for it. A jump while the
  // app is away is limited only by the caps; a monotonic clock (a native module) closes it.
  const raw = Math.floor(t.wallMs / 1000);
  const napRoom = Math.max(0, rules.maxNapMinutes - t.creditedThisNap);
  const dayRoom = Math.max(0, rules.maxDayMinutes - t.creditedToday);
  const minutes = Math.min(raw, napRoom, dayRoom);
  if (minutes < raw)
    return { minutes, reanchor: true, reason: napRoom <= dayRoom ? 'nap-cap' : 'day-cap' };
  return { minutes, reanchor: false, reason: 'rest' };
}
