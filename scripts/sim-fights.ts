/**
 * The fight balance simulation (Claude L, 21 Oct). Writes docs/mechanics/fight-sim.md from
 * lib/fight-content.ts and lib/fight-sim.ts. Deterministic: the same inputs give the same
 * report byte for byte. `--check` compares a hash of the inputs with the one in the report
 * (cheap enough for CI); `--fast` uses fewer spars a cell for local iteration.
 */
import assert from 'node:assert/strict';
import { createHash } from 'node:crypto';
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { format, type FormatConfig } from 'oxfmt';
import {
  families,
  folk,
  habitDeckAt,
  restedSpecials,
  rivals,
  type Family,
  type Folk,
  type Rival,
} from '../lib/fight-content';
import {
  createFight,
  proposedRules,
  rivalSetup,
  runFight,
  todayRules,
  type FighterSetup,
  type Policy,
  type Rules,
} from '../lib/fight-sim';

const root = new URL('../', import.meta.url);
const inputs = ['lib/fight-content.ts', 'lib/fight-sim.ts', 'scripts/sim-fights.ts'];
const REPORT = 'docs/mechanics/fight-sim.md';

function inputHash() {
  const h = createHash('sha256');
  for (const path of inputs) h.update(readFileSync(new URL(path, root)));
  return h.digest('hex').slice(0, 16);
}

type Opts = {
  policy?: Policy;
  pips?: number;
  zen?: number;
  press?: boolean;
  variants?: ('a' | 'b')[];
  level?: number;
  rules?: Rules;
};

type Cell = { win: number; draw: number; turns: number; timeouts: number; n: number };

function spar(f: Folk | null, fam: Family, r: Rival, n: number, o: Opts = {}): Cell {
  const level = Math.max(o.level ?? 0, r.level);
  const me: FighterSetup = {
    name: f?.id ?? 'plain',
    family: fam,
    level,
    zen: o.zen ?? 0,
    deck: habitDeckAt(level),
    folk: f ?? undefined,
    variants: o.variants,
    pips: o.pips ?? 0,
    policy: o.policy ?? 'smart',
    press: o.press ? { attack: 1.05, brace: 1 } : undefined,
  };
  const rival = { ...rivalSetup(r, fam, true), level };
  const cell: Cell = { win: 0, draw: 0, turns: 0, timeouts: 0, n };
  for (let i = 0; i < n; i++) {
    const seed = (i + 1) * 2654435761 + fam.length * 97 + r.level * 13;
    const res = runFight(createFight(me, rival, o.rules ?? proposedRules, seed));
    if (res.result === 'win') cell.win++;
    if (res.result === 'draw') cell.draw++;
    if (res.timedOut) cell.timeouts++;
    cell.turns += res.turns;
  }
  return cell;
}

const pct = (c: Cell) => (100 * c.win) / c.n;
const mean = (xs: number[]) => xs.reduce((a, b) => a + b, 0) / xs.length;
const r0 = (x: number) => Math.round(x).toString();
const sign = (x: number) => (x >= 0 ? `+${Math.round(x)}` : `${Math.round(x)}`);

function folkRate(f: Folk, n: number, o: Opts = {}, rs: Rival[] = rivals) {
  const cells = rs.flatMap((r) => families.map((fam) => pct(spar(f, fam, r, n, o))));
  return mean(cells);
}

const pass = (ok: boolean) => (ok ? 'PASS' : '**FAIL**');

function run(n: number) {
  const out: string[] = [];
  const rails: [string, string, boolean][] = [];

  // Main matrix: smart play, no presses, no special, no variants, no zen.
  const matrix = new Map<string, Cell>();
  const cell = (key: string) => {
    const c = matrix.get(key);
    if (!c) throw new Error(`no cell ${key}`);
    return c;
  };
  for (const f of folk)
    for (const r of rivals)
      for (const fam of families) matrix.set(`${f.id}|${r.id}|${fam}`, spar(f, fam, r, n));
  const rate = (f: string, r: string, fam?: Family) =>
    fam ? pct(cell(`${f}|${r}|${fam}`)) : mean(families.map((x) => pct(cell(`${f}|${r}|${x}`))));

  out.push('## 1. Every folk against every ring (win %, the three families averaged)\n');
  out.push(
    `Smart play (the one-turn lookahead a careful player finds), presses OFF, no rested special, no variants, no zen; ${n} spars a family, so ${3 * n} a cell. Both sides at the ring's level; the player's habit deck is \`habitDeckAt(level)\`.\n`,
  );
  out.push(`| Folk | ${rivals.map((r) => `${r.id} (L${r.level})`).join(' | ')} | Mean |`);
  out.push(`| --- | ${rivals.map(() => '--:').join(' | ')} | --: |`);
  const folkMeans: Record<string, number> = {};
  for (const f of folk) {
    const row = rivals.map((r) => rate(f.id, r.id));
    folkMeans[f.id] = mean(row);
    out.push(`| ${f.name} | ${row.map(r0).join(' | ')} | ${r0(folkMeans[f.id])} |`);
  }
  const ringMeans = rivals.map((r) => mean(folk.map((f) => rate(f.id, r.id))));
  out.push(`| **Cast mean** | ${ringMeans.map(r0).join(' | ')} | ${r0(mean(ringMeans))} |`);
  out.push('');

  // Family table.
  out.push('### By family (all folk, all rings)\n');
  out.push('| Family | Win % | Mean of your turns | Reached the round limit |');
  out.push('| --- | --: | --: | --: |');
  for (const fam of families) {
    const cells = folk.flatMap((f) => rivals.map((r) => cell(`${f.id}|${r.id}|${fam}`)));
    const games = cells.reduce((a, c) => a + c.n, 0);
    out.push(
      `| ${fam} | ${r0((100 * cells.reduce((a, c) => a + c.win, 0)) / games)} | ${(cells.reduce((a, c) => a + c.turns, 0) / games).toFixed(1)} | ${((100 * cells.reduce((a, c) => a + c.timeouts, 0)) / games).toFixed(1)} % |`,
    );
  }
  out.push('');

  // GR1 and GR3: starters.
  const starters = folk.filter((f) => f.night <= 3);
  let worst = { v: 101, at: '' };
  for (const f of starters)
    for (const r of rivals)
      for (const fam of families) {
        const v = rate(f.id, r.id, fam);
        if (v < worst.v) worst = { v, at: `${f.name} ${fam} against ${r.id}` };
      }
  rails.push([
    '1. A starter, any family, wins at least 40 % against every rival',
    `worst ${r0(worst.v)} % (${worst.at})`,
    worst.v >= 40,
  ]);
  // GR1 under the casual player (fights.md asks for AUTO play; casual is closer to it).
  let worstCasual = { v: 101, at: '' };
  for (const f of starters)
    for (const r of rivals)
      for (const fam of families) {
        const v = pct(spar(f, fam, r, Math.max(10, Math.floor(n / 2)), { policy: 'casual' }));
        if (v < worstCasual.v) worstCasual = { v, at: `${f.name} ${fam} against ${r.id}` };
      }
  rails.push([
    '1b. ... the same with the casual player (a third of turns by `chooseAI`)',
    `worst ${r0(worstCasual.v)} % (${worstCasual.at})`,
    worstCasual.v >= 40,
  ]);
  // GR2.
  let spreadWorst = { v: 0, at: '' };
  const bestAt = new Map<string, number>();
  rivals.forEach((r, i) => {
    let best = { v: -1, f: '' };
    for (const f of folk) {
      const v = rate(f.id, r.id);
      const d = Math.abs(v - ringMeans[i]);
      if (d > spreadWorst.v) spreadWorst = { v: d, at: `${f.name} at ${r.id}` };
      if (v > best.v) best = { v, f: f.id };
    }
    bestAt.set(best.f, (bestAt.get(best.f) ?? 0) + 1);
  });
  const castMean = mean(Object.values(folkMeans));
  const overall = Object.entries(folkMeans).map(([id, v]) => [id, v - castMean] as const);
  const overallWorst = overall.reduce((a, b) => (Math.abs(b[1]) > Math.abs(a[1]) ? b : a));
  const dominant = [...bestAt.entries()].find(([, k]) => k === rivals.length);
  rails.push([
    '2a. Every folk within 12 points of the cast mean (over all rings)',
    `widest ${overallWorst[0]} ${sign(overallWorst[1])}`,
    Math.abs(overallWorst[1]) <= 12,
  ]);
  rails.push([
    '2b. ... and at each ring',
    `widest ${r0(spreadWorst.v)} points (${spreadWorst.at})`,
    spreadWorst.v <= 12,
  ]);
  rails.push([
    '2c. No folk is the best against every rival',
    dominant
      ? `${dominant[0]} is`
      : `best at most rings: ${[...bestAt.entries()].sort((a, b) => b[1] - a[1])[0].join(', ')}`,
    !dominant,
  ]);
  // GR3.
  let worstFam = { v: 101, at: '' };
  for (const f of starters)
    for (const fam of families) {
      const v = mean(rivals.map((r) => rate(f.id, r.id, fam)));
      if (v < worstFam.v) worstFam = { v, at: `${f.name} with ${fam}` };
    }
  rails.push([
    '3. The worst family pairing still wins at least 35 % with each starter',
    `worst ${r0(worstFam.v)} % (${worstFam.at})`,
    worstFam.v >= 35,
  ]);
  // GR5.
  const all = [...matrix.values()];
  const games = all.reduce((a, c) => a + c.n, 0);
  const turns = all.reduce((a, c) => a + c.turns, 0) / games;
  const timeouts = (100 * all.reduce((a, c) => a + c.timeouts, 0)) / games;
  rails.push([
    '5. 5 to 10 of your turns on average, under 5 % at the round limit',
    `${turns.toFixed(1)} turns, ${timeouts.toFixed(1)} % at the limit`,
    turns >= 5 && turns <= 10 && timeouts < 5,
  ]);

  // GR4, GR6, GR8 per folk (a lighter sample).
  const m = Math.max(10, Math.floor(n / 2));
  const perFolk: string[] = [];
  let press = { v: 0, at: '' };
  let line = { v: 0, at: '' };
  let special = { v: 0, at: '' };
  let zen = { v: 0, at: '' };
  let zenProposed = { v: 0, at: '' };
  for (const f of folk) {
    const base = folkRate(f, m);
    const p = folkRate(f, m, { press: true }) - base;
    const s = base - folkRate(f, m, { policy: 'casual' });
    const sp = folkRate(f, m, { pips: 3 }) - base;
    const z = folkRate(f, m, { zen: 0.3, rules: { ...proposedRules, zenScale: 1 } }) - base;
    const zp = folkRate(f, m, { zen: 0.3 }) - base;
    if (Math.abs(zp) > Math.abs(zenProposed.v)) zenProposed = { v: zp, at: f.name };
    if (Math.abs(p) > Math.abs(press.v)) press = { v: p, at: f.name };
    if (Math.abs(s) > Math.abs(line.v)) line = { v: s, at: f.name };
    if (Math.abs(sp) > Math.abs(special.v)) special = { v: sp, at: f.name };
    if (Math.abs(z) > Math.abs(zen.v)) zen = { v: z, at: f.name };
    perFolk.push(
      `| ${f.name} | ${r0(base)} | ${sign(p)} | ${sign(s)} | ${sign(sp)} | ${sign(z)} |`,
    );
  }
  rails.push([
    '4. Always NICE (x 1.05 on your hit) beats never pressed by at most 15 points',
    `largest ${sign(press.v)} (${press.at})`,
    Math.abs(press.v) <= 15,
  ]);
  rails.push([
    "6. No folk's best line wins more than 10 points above its average line (casual: one turn in three by today's rule)",
    `largest ${sign(line.v)} (${line.at})`,
    line.v <= 10,
  ]);
  rails.push([
    '8a. A full rested special moves a spar by at most 10 points',
    `largest ${sign(special.v)} (${special.at})`,
    Math.abs(special.v) <= 10,
  ]);
  rails.push([
    '8b. Zen 30 % on your side moves a spar by at most 15',
    `${sign(zenProposed.v)} with zen off in spars (proposed); at full strength it would be ${sign(zen.v)} (${zen.at})`,
    Math.abs(zenProposed.v) <= 15,
  ]);

  // GR7 variants.
  const varRows: string[] = [];
  let variant = { v: 0, at: '' };
  for (const f of folk)
    f.variants.forEach((v, i) => {
      const picks = (p: 'a' | 'b') => [0, 1, 2].map((j) => (j === i ? p : 'a'));
      const a = folkRate(f, m, { variants: picks('a'), level: v.level });
      const b = folkRate(f, m, { variants: picks('b'), level: v.level });
      if (Math.abs(a - b) > Math.abs(variant.v))
        variant = { v: a - b, at: `${f.name} L${v.level}` };
      varRows.push(
        `| ${f.name} | ${v.level} | ${v.a.name} ${r0(a)} | ${v.b.name} ${r0(b)} | ${sign(a - b)} |`,
      );
    });
  rails.push([
    '7. Each level 4, 8 and 12 choice is within 5 points of its pair',
    `widest ${sign(variant.v)} (${variant.at})`,
    Math.abs(variant.v) <= 5,
  ]);

  const head: string[] = [];
  head.push('## 0. Guard rails (fights.md section 4.8)\n');
  head.push('| Guard rail | Result | |');
  head.push('| --- | --- | --- |');
  for (const [name, res, ok] of rails) head.push(`| ${name} | ${res} | ${pass(ok)} |`);
  head.push('');

  out.push('## 2. What presses, careful play, the special and zen are worth\n');
  out.push(
    `Change in each folk's mean win % against all rings and families (${m} spars a family): presses always NICE (x 1.05 on your hit; BRACED is a stamp only); the smart line minus the casual line (a third of its turns played by today's \`chooseAI\` rule: heal under 35 %, else the strongest attack); a full special (3 pips); zen 30 % on your side (the proposal counts none of it in a spar, as today's copy to Dave cancels it; the column shows it at full strength for comparison).\n`,
  );
  out.push('| Folk | Base | Presses | Smart over casual | Full special | Zen 30 % |');
  out.push('| --- | --: | --: | --: | --: | --: |');
  out.push(...perFolk, '');
  out.push('## 3. Card variants (guard rail 7)\n');
  out.push(
    `Both sides at the variant's level or the ring's, whichever is higher; ${m} spars a family.\n`,
  );
  out.push('| Folk | Level | Variant A | Variant B | A minus B |');
  out.push('| --- | --: | --- | --- | --: |');
  out.push(...varRows, '');

  // Matchup options (the evidence for M1/M2).
  out.push('## 4. Families against fixed-family rivals: the matchup options\n');
  out.push(
    "Every folk and family against the nine rivals with a fixed family. \"Spread\" is, at each ring, the best family's win % minus the worst family's, averaged over rings (and its largest). Today's 1.5 / 0.67 is in the first row.\n",
  );
  out.push('| Option | REST | ROAM | FOCUS | Spread, mean | Spread, largest |');
  out.push('| --- | --: | --: | --: | --: | --: |');
  const options: [string, Rules][] = [
    ['A. Today: x 1.5 / x 0.67', { ...proposedRules, matchup: [1.5, 0.67], advantageFirstHit: 1 }],
    ['x 1.25 / x 0.8', { ...proposedRules, matchup: [1.25, 0.8], advantageFirstHit: 1 }],
    ['x 1.1 / x 0.91', { ...proposedRules, matchup: [1.1, 0.91], advantageFirstHit: 1 }],
    ['D. x 1.05 / x 0.95', { ...proposedRules, matchup: [1.05, 0.95], advantageFirstHit: 1 }],
    [
      'C. No multiplier, +1 starting energy with the advantage',
      { ...proposedRules, advantageFirstHit: 1, advantageEnergy: 1 },
    ],
    ['B. No multiplier in spars (proposed)', proposedRules],
    [
      'E. No multiplier; the first damaging card x 1.5 with the advantage',
      { ...proposedRules, advantageFirstHit: 1.5 },
    ],
  ];
  const fixed = rivals.filter((r) => r.family !== 'mirror');
  const k = Math.max(6, Math.floor(n / 8));
  for (const [label, rules] of options) {
    const byFam: Record<string, number[]> = {};
    const spreads: number[] = [];
    for (const r of fixed) {
      const famRates = families.map((fam) => {
        const v = mean(folk.map((f) => pct(spar(f, fam, r, k, { rules }))));
        (byFam[fam] ??= []).push(v);
        return v;
      });
      spreads.push(Math.max(...famRates) - Math.min(...famRates));
    }
    out.push(
      `| ${label} | ${families.map((fam) => r0(mean(byFam[fam]))).join(' | ')} | ${r0(mean(spreads))} | ${r0(Math.max(...spreads))} |`,
    );
  }
  out.push('');

  // F3 to F5 on today's engine, habit cards only, against Dave.
  out.push("## 5. Today's spar against Dave, and F1, F3 to F5\n");
  out.push(
    `Habit cards only (no folk), the starter deck plus what \`habitDeckAt\` adds, \`chooseAI\` on both sides, ${n * 2} spars a cell, your every press a plain x 1 (the bar's middle band) unless the row says late, Dave's timing rolled as \`computerTiming\` rolls it today (20 % x 1.5, 20 % x 0.6); your block button is not modelled. Rested: zen 30 % on your side; today Dave copies it (\`bot()\`).\n`,
  );
  const dave = rivals.find((r) => r.id === 'dave');
  if (!dave) throw new Error('Dave is a rival');
  type Fix = {
    label: string;
    late?: boolean;
    f3?: boolean;
    f4?: boolean;
    zenOff?: boolean;
    f5?: boolean;
  };
  const rows: Fix[] = [
    { label: 'Today' },
    { label: 'Today, every press late (x 0.6; F1 makes it x 1)', late: true },
    { label: 'F3: a draw at the round limit', f3: true },
    { label: 'F5: Dave mirrors your family', f5: true },
    { label: 'F3 + F5', f3: true, f5: true },
    { label: 'F3 + F4 (Dave has no zen) + F5', f3: true, f4: true, f5: true },
    {
      label: "F3 + F4' (zen does not count in spars) + F5, recommended",
      f3: true,
      zenOff: true,
      f5: true,
    },
  ];
  out.push('| Rules | Level | Rested | REST win / draw | ROAM win / draw | FOCUS win / draw |');
  out.push('| --- | --: | --- | --: | --: | --: |');
  for (const fx of rows)
    for (const level of [1, 3])
      for (const rested of [false, true]) {
        const cells = families.map((fam) => {
          const c: Cell = { win: 0, draw: 0, turns: 0, timeouts: 0, n: n * 2 };
          const me: FighterSetup = {
            name: 'you',
            family: fam,
            level,
            zen: rested ? 0.3 : 0,
            deck: habitDeckAt(level),
            pips: 0,
            policy: 'simple',
            press: { attack: fx.late ? 0.6 : 1, brace: 1 },
          };
          const rival: FighterSetup = {
            ...rivalSetup(dave, fam, !!fx.f5),
            level,
            zen: rested && !fx.f4 ? 0.3 : 0,
            autoTiming: true,
          };
          const rules: Rules = { ...todayRules, drawAtLimit: !!fx.f3, zenScale: fx.zenOff ? 0 : 1 };
          for (let i = 0; i < c.n; i++) {
            const res = runFight(createFight(me, rival, rules, (i + 1) * 40503 + level));
            if (res.result === 'win') c.win++;
            if (res.result === 'draw') c.draw++;
          }
          return `${r0(pct(c))} / ${r0((100 * c.draw) / c.n)}`;
        });
        out.push(`| ${fx.label} | ${level} | ${rested ? 'yes' : 'no'} | ${cells.join(' | ')} |`);
      }
  out.push('');

  // Raids: banking against the raid AI, today's rules.
  out.push("## 6. Raids keep today's rules: banking against the raid AI\n");
  out.push(
    `Each folk (smart) against a raid defender played by \`chooseAI\` with the same level and deck, today's x 1.5 / x 0.67, the round limit a loss, and Puffcap's doze replaced by the softening (an absent player). Level 5, every family pairing, ${m} raids each. Flag: more than 12 points from the cast mean.\n`,
  );
  const raidRules: Rules = { ...todayRules, raid: true };
  const raider = (f: Folk) =>
    mean(
      families.flatMap((fam) =>
        families.map((def) => {
          const defender: Rival = {
            id: 'defender',
            region: '',
            ring: '',
            who: '',
            family: def,
            level: 5,
            zen: 0.1,
            deck: habitDeckAt(5),
            status: 'today',
          };
          return pct(spar(f, fam, defender, m, { rules: raidRules }));
        }),
      ),
    );
  const raidRates = folk.map((f) => [f, raider(f)] as const);
  const raidMean = mean(raidRates.map(([, v]) => v));
  out.push('| Folk | Raid win % | From the mean |');
  out.push('| --- | --: | --: |');
  for (const [f, v] of raidRates)
    out.push(
      `| ${f.name} | ${r0(v)} | ${sign(v - raidMean)}${Math.abs(v - raidMean) > 12 ? ' (flag)' : ''} |`,
    );
  out.push('');

  return { head, body: out };
}

async function main() {
  const fast = process.argv.includes('--fast');
  const hash = inputHash();
  const path = new URL(REPORT, root);
  if (process.argv.includes('--check')) {
    const current = readFileSync(path, 'utf8');
    assert.ok(
      current.includes(`Input hash: \`${hash}\``),
      `${REPORT} is stale; run npm run sim:fights`,
    );
    console.log('Fight report matches lib/fight-content.ts and lib/fight-sim.ts.');
    return;
  }
  const n = fast ? 30 : 120;
  const t0 = Date.now();
  const { head, body } = run(n);
  const doc = [
    '# Fight balance simulation',
    '',
    `**A proposal, generated by \`npm run sim:fights\`. Do not edit by hand.** Input hash: \`${hash}\` (lib/fight-content.ts, lib/fight-sim.ts, scripts/sim-fights.ts). ${n} spars a family in the main table. Deterministic: seeded spars, no clock. What the numbers mean and the decisions they support: [fight-content.md](fight-content.md).`,
    '',
    'Limits: the "smart" player looks one turn ahead with rolls at their mean; rivals play today\'s `chooseAI`; intents (F2) are not modelled; specials are used by a fixed rule in the simple line; decks are a fixed middling deck per level, not a rested player\'s random one. Win rates against these rivals measure the content against itself, not what a person will feel.',
    '',
    `Rested specials: ${restedSpecials.map((s) => `${s.family} ${s.name} (${s.text})`).join('; ')}.`,
    '',
    ...head,
    ...body,
  ].join('\n');
  const config: FormatConfig = JSON.parse(readFileSync(new URL('.oxfmtrc.json', root), 'utf8'));
  const formatted = await format(REPORT, doc, config);
  assert.equal(formatted.errors.length, 0, 'the generated report formats cleanly');
  mkdirSync(new URL('docs/mechanics/', root), { recursive: true });
  writeFileSync(path, formatted.code);
  console.log(head.join('\n'));
  console.log(`Wrote ${REPORT} in ${((Date.now() - t0) / 1000).toFixed(0)} s.`);
}

void main().catch((error: unknown) => {
  console.error(error);
  process.exitCode = 1;
});
