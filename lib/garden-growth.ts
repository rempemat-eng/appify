// The meadow grows from time away: lifetime simulated break minutes decide what
// each bed and orchard pit shows. This is presentation only: it reads progress,
// never changes rewards, and nothing wilts when the player takes a while off.

/** Lifetime break minutes at which each meadow bed is sown, in bed order. */
export const plotSownAt = [10, 30, 60, 100, 150, 220] as const;
/** Minutes of further breaks between a bed's stages (sown, sprout, leaves, bud, bloom). */
export const PLOT_STAGE_MIN = 15;
/** Lifetime break minutes at which each orchard pit gets its seedling marker. */
export const orchardSownAt = [90, 240, 480] as const;
/** Minutes after sowing at which a tree becomes a sapling, young, grown and fruiting. */
export const orchardStageAt = [0, 30, 120, 300, 600] as const;

export const PLOT_STAGES = 5;
export const TREE_STAGES = 5;

const minutesOf = (value: number) => (Number.isFinite(value) ? Math.max(0, Math.floor(value)) : 0);

/** -1 for an empty bed, then 0 (sown) to 4 (in bloom). */
export function plotStage(minutes: number, index: number): number {
  const sown = plotSownAt[index];
  if (sown === undefined) return -1;
  const since = minutesOf(minutes) - sown;
  if (since < 0) return -1;
  return Math.min(PLOT_STAGES - 1, Math.floor(since / PLOT_STAGE_MIN));
}

/** -1 for an empty pit, then 0 (marker) to 4 (fruiting). */
export function orchardStage(minutes: number, index: number): number {
  const sown = orchardSownAt[index];
  if (sown === undefined) return -1;
  const since = minutesOf(minutes) - sown;
  if (since < 0) return -1;
  let stage = 0;
  for (let i = 0; i < orchardStageAt.length; i++) if (since >= orchardStageAt[i]) stage = i;
  return stage;
}

/** Every future minute at which something in the meadow changes, ascending. */
function milestones(): number[] {
  const all = new Set<number>();
  for (const sown of plotSownAt)
    for (let s = 0; s < PLOT_STAGES; s++) all.add(sown + s * PLOT_STAGE_MIN);
  for (const sown of orchardSownAt) for (const at of orchardStageAt) all.add(sown + at);
  return [...all].sort((a, b) => a - b);
}
const MILESTONES = milestones();

export type MeadowSummary = {
  /** beds in full bloom */
  blooming: number;
  /** trees bearing fruit */
  fruiting: number;
  /** beds or pits with anything in them */
  planted: number;
  /** minutes of breaks until the next visible change, or null when fully grown */
  nextIn: number | null;
};

export function meadowSummary(minutes: number): MeadowSummary {
  const m = minutesOf(minutes);
  const beds = plotSownAt.map((_, i) => plotStage(m, i));
  const trees = orchardSownAt.map((_, i) => orchardStage(m, i));
  const next = MILESTONES.find((at) => at > m);
  return {
    blooming: beds.filter((s) => s === PLOT_STAGES - 1).length,
    fruiting: trees.filter((s) => s === TREE_STAGES - 1).length,
    planted: [...beds, ...trees].filter((s) => s >= 0).length,
    nextIn: next === undefined ? null : next - m,
  };
}

/** One short, cosy line for the meadow sign. Never a target or a nag. */
export function meadowLine(minutes: number): string {
  const s = meadowSummary(minutes);
  if (s.planted === 0)
    return `the meadow is resting. about ${s.nextIn} min of breaks and the first bed is sown.`;
  if (s.nextIn === null)
    return 'the whole meadow is in bloom, and the orchard is heavy with fruit.';
  const now =
    s.fruiting > 0
      ? `${s.blooming} beds in bloom and ${s.fruiting} tree${s.fruiting === 1 ? '' : 's'} with fruit.`
      : s.blooming > 0
        ? `${s.blooming} bed${s.blooming === 1 ? '' : 's'} in bloom.`
        : 'little green shoots everywhere.';
  return `${now} something new grows in about ${s.nextIn} min of breaks.`;
}
