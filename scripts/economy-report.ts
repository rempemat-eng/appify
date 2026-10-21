import type { EconomyInputs, PlayerPolicy, Scenario, Session } from './economy-inputs';
import { total, type Simulation } from './economy-model';
import { restRecognitionRules } from '../lib/rest-recognition';

const number = (value: number) => value.toLocaleString('en-GB', { maximumFractionDigits: 2 });
const time = (minute: number) =>
  `${String(Math.floor(minute / 60)).padStart(2, '0')}:${String(minute % 60).padStart(2, '0')}`;
const weekdays = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
const dayNames = (days: readonly number[]) => days.map((day) => weekdays[day]).join(', ');
const escapeXml = (value: string) =>
  value
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;');
const weeklyWallets = (input: EconomyInputs, result: Simulation) =>
  Array.from(
    { length: input.weeks },
    (_, week) => result.days[(week + 1) * input.daysPerWeek - 1].balance,
  );
const scenarioFor = (input: EconomyInputs, result: Simulation) =>
  input.scenarios.find((scenario) => scenario.name === result.scenario)!;
const scenarioLabel = (input: EconomyInputs, result: Simulation) =>
  scenarioFor(input, result).id.toUpperCase();

function sessionLabel(session: Session) {
  return `${dayNames(session.days)} ${time(session.at)}: ${number(session.minutes)} min ${session.mission ?? 'plain nap'}${session.foregroundMinutes ? ` (${number(session.foregroundMinutes)} min initially foreground)` : ''}`;
}

function playerRow(player: PlayerPolicy) {
  return `| ${player.name} | ${player.sessions.map(sessionLabel).join('<br>')} | ${dayNames(player.visitDays)} ${time(player.visitAt)}; ${number(player.activeSeconds)} s active | ${player.feedsPerVisit} attempted / visit; ${player.sparWins.join('/')} wins Mon–Sun | ${player.targetLevel} |`;
}

function scenarioRow(input: EconomyInputs, scenario: Scenario) {
  const daytime =
    scenario.ceiling === null
      ? scenario.tier0
        ? `${number(restRecognitionRules.maxNapMinutes / 60)} h / nap; ${number(restRecognitionRules.maxDayMinutes / 60)} h / day (credited)`
        : 'Uncapped'
      : `${number(scenario.ceiling)} in full, then ${number(scenario.excessRate * 100)}%`;
  const night =
    scenario.nightGift === null
      ? 'Per minute at the applicable window rate'
      : `${number(scenario.nightGift)} per qualifying night, outside daytime ceiling`;
  return `| ${scenario.name} | ${number(scenario.creditedMinutesPerRealMinute)} | ${number(input.rules.napPerMinute)} | ${number(scenario.restMultiplier)}× | ${number(scenario.focusMultiplier)}× | ${daytime} | ${night} | ${number(scenario.wellKeptGift)} |`;
}

/** Generated ledger: assumptions and proposed rules are separate from live behaviour. */
export function renderEconomyReport(input: EconomyInputs, simulations: Simulation[]): string {
  const base = 'https://github.com/rempemat-eng/appify';
  const runtime = `${base}/blob/${input.source.main}`;
  const mechanics = `${base}/blob/${input.source.mechanics}`;
  const label = (r: Simulation) => `${scenarioLabel(input, r)} / ${r.player}`;
  const rows = simulations.map(
    (r) =>
      `| ${label(r)} | ${number(total(r.earned))} | ${number(total(r.spent))} | ${number(r.lostToRaids)} | ${number(r.balance)} | ${r.level} | ${r.boughtHats.length} / ${r.freeHats.length} |`,
  );
  const milestones = simulations.map((r) => {
    const policy = input.players.find((p) => p.name === r.player)!;
    const day = (level: 5 | 8 | 12) =>
      r.levelDays[level] ??
      (policy.targetLevel < level
        ? `Policy stops at L${policy.targetLevel}`
        : `Not reached in ${input.weeks * 7} days`);
    return `| ${label(r)} | ${day(5)} | ${day(8)} | ${day(12)} | ${r.allHatsDay ?? 'Not reached'} |`;
  });
  const flows = simulations.map(
    (r) =>
      `| ${label(r)} | ${number(r.earned.naps)} | ${number(r.earned.outings)} | ${number(r.earned.nights)} | ${number(r.earned.spars)} | ${number(r.earned.wellKept)} | ${number(r.earned.incomingDefense)} | ${number(r.spent.feeding)} | ${number(r.spent.levels)} | ${number(r.spent.hats)} |`,
  );
  const raids = simulations.map(
    (r) =>
      `| ${label(r)} | ${r.incomingAttempts} | ${r.defendedRaids} | ${number(r.earned.incomingDefense)} | ${number(r.lostToRaids)} |`,
  );
  const activity = simulations.map(
    (r) =>
      `| ${label(r)} | ${r.completedOutings} | ${r.gatedOutings} | ${r.earlyOutings} | ${number(r.creditedMinutes)} | ${r.cards} | ${[...r.boughtHats, ...r.freeHats].join(', ') || 'None'} |`,
  );
  const wallets = simulations.map(
    (r) => `| ${label(r)} | ${weeklyWallets(input, r).map(number).join(' | ')} |`,
  );
  const exclusions = simulations
    .filter((r) => scenarioFor(input, r).tier0)
    .map(
      (r) =>
        `${r.player}: ${number(r.rejectedForegroundMinutes)} foreground / ${number(r.rejectedCapMinutes)} cap minutes`,
    )
    .join('; ');
  return `# Dream Dust economy simulation (C33 / C40)

A deterministic solo ledger over ${input.weeks} weeks (${input.weeks * input.daysPerWeek} fixed civil days). All durations below are real minutes. These are simulated policies and proposed scenarios, not changes to the game or forecasts of player behaviour. The saved balance field remains \`grass\`.

## Sources and assumptions

- Live catalogue and rules: [main \`${input.source.main}\`](${base}/commit/${input.source.main}), [game.ts](${runtime}/lib/game.ts), [offline-rules.ts](${runtime}/lib/offline-rules.ts) and [cards.ts](${runtime}/lib/cards.ts).
- L2 multipliers come from [living-world-plan.md](${runtime}/docs/vision/living-world-plan.md). G10 is the [PR #143 proposal](${base}/blob/${input.source.proposal}/docs/vision/gameplay-regions.md); regional outings, ways, comforts and new sinks are excluded.
- C40 uses [the Dream Dust source/sink map](${mechanics}/docs/mechanics/dream-dust.md) and imports limits directly from [rest-recognition.ts](${mechanics}/lib/rest-recognition.ts) at \`${input.source.mechanics}\` (#195). The new rate is an explicit assumption for Matt to judge.
- Schedules, spending targets, exposure and button presses are assumptions, not observations. Weeks start Monday; civil-day arithmetic has no host clock, timezone or DST. Only declared sessions earn rest rewards.

All profiles start with ${input.initial.dust} Dust, level ${input.initial.level}, mood ${input.initial.mood} and no hats.

| Player | Repeating rest and outing schedule | Shopping / play visit | Feeding and spars | Target level |
| --- | --- | --- | --- | --- |
${input.players.map(playerRow).join('\n')}

Protected rhythm: ${input.rhythm.enabled ? 'enabled' : 'disabled'}. Rest: ${dayNames(input.rhythm.rest.days)}, ${time(input.rhythm.rest.start)}–${time(input.rhythm.rest.end)}. Focus: ${dayNames(input.rhythm.focus.days)}, ${time(input.rhythm.focus.start)}–${time(input.rhythm.focus.end)}. Overnight windows belong to their starting weekday.

| Scenario | Credited min / real min | Nap Dust / credited min | Rest | Focus | Daytime payment | Qualifying night | Well-kept gift / eligible visit |
| --- | --- | --- | --- | --- | --- | --- | --- |
${input.scenarios.map((scenario) => scenarioRow(input, scenario)).join('\n')}

TODAY retains the demo clock: one real second pays one Dust, so an eight-hour plain nap pays **28,800**. L2 pays **960** for that nap (Rest 2×); G10 pays **60** as its qualifying-night gift. The new real-rate tier-0 assumption pays **480** (one Dust per credited real minute, no protected-hour multiplier or night gift). All four current hats together cost ${input.hats.reduce((sum, hat) => sum + hat.cost, 0)}.

### Real rate + tier 0

The imported limits allow ${restRecognitionRules.maxNapMinutes} credited real minutes per nap and ${restRecognitionRules.maxDayMinutes} per civil day. Foreground time beyond the initial ${restRecognitionRules.foregroundGraceMs / 1000} s grace is excluded; the grace still counts. A nap crossing midnight retains its per-nap total while daily room resets. The prototype currently returns demo-second credit, so this simulator uses its limits with an explicit real-minute adapter rather than treating those raw credits as real minutes.

Profiles assume the phone is put away immediately (zero initial foreground minutes). A session can instead specify \`foregroundMinutes\`; after that interval it is away. Exclusions in these profiles: ${exclusions}. Their schedules do not reach the caps; independent boundary fixtures, including long/split naps, midnight and foreground grace, test those limits. This continuous-minute ledger does not emulate timer rounding, clock changes or native lifecycle.

Caps/foreground exclusions affect plain naps, including a locked outing replaced by a nap. Missions retain their existing duration and fixed reward; there is no passive nap Dust on top, nor earning after the mission deadline. An early return retains credited minutes/cards but grants no completion reward. These conventions are identical across the comparisons apart from the labelled clock rates.

### Other scenario and shopping conventions

G10 nights need at least ${input.rules.nightMinimumMinutes} real minutes and start in Rest (or ${time(input.rhythm.fallbackNightStart)}–${time(input.rhythm.fallbackNightEnd)} if rhythm is disabled). One gift per wake day prevents split-night duplication. The daytime taper combines naps and outings: 240 Dust in full, then 25% of the excess; night gifts and spars sit outside it. This is a taper, not a hard maximum. L2/G10 outing multipliers are weighted by time in each window, including Mountain's all-hats bonus, as an explicit interpretation of the proposals.

The well-kept gift is zero: neither its amount nor health threshold is agreed. No invented medicine, repair, decoration or #146 home-base costs are added. At each visit, configured spar wins (first ${input.rules.paidSparWinsPerDay} daily wins × ${input.rules.sparReward}) and any gift settle, feeding is attempted, then at most one level and one unowned hat are bought if affordable. Active visits reduce mood at one per ${input.rules.awakeSecondsPerMood} s; each ${input.rules.feedCost}-Dust feed restores ${input.rules.feedMood}, capped at ${input.rules.maxMood}. Rest restores one mood per credited minute.

Levels cost ${input.rules.levelCostFactor} × current level. Targets are shopping policy, not game caps. Mountain uniformly draws from the unowned catalogue, matching the game's selection rule; once all hats are owned it pays ${input.rules.mountainHatBonus} extra Dust. Seed ${input.seeds.mountainHats} is mixed with the player ID. The independent raid stream uses ${input.seeds.incomingRaids}; enabling raids cannot consume hat draws, although changed affordability can change which hats remain. A single seed path is illustrative, not an expectation or uncertainty interval.

## ${input.weeks}-week results

Earned excludes the starting balance; Spent is successful purchases only. **Wallet = ${input.initial.dust} + earned − spent − raid losses.** Hat counts distinguish purchases and free grants.

| Scenario / player | Earned | Spent | Raid losses | Ending wallet | Level | Bought / free hats |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
${rows.join('\n')}

## Days to levels and all hats

First simulation day owning the item (day 1 is Monday; day 0 means already owned initially). A policy stopping below a level is distinguished from an unaffordable milestone. These are actual purchases under the stated policy, not earliest affordable unlocks or an optimised path.

| Scenario / player | Level 5 | Level 8 | Level 12 | All hats |
| --- | ---: | ---: | ---: | ---: |
${milestones.join('\n')}

## Source and spending ledger

| Scenario / player | Naps | Outings | Night gifts | Spars | Well-kept | Defense gains | Feeding | Levels | Hats |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
${flows.join('\n')}

| Scenario / player | Completed outings | Gated → nap | Early outings | Credited minutes | Card grants | Hats owned |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
${activity.join('\n')}

Card grants are not unique cards or final deck size: one common grant per ${input.rules.cardEveryMinutes} credited minutes, one per completed outing and the level-three grant. Deck composition/combat is not simulated. Eight weeks is 56 days, not two calendar months; these numbers need not reproduce #143's monthly sketch.

## Optional SIMULATE INCOMING RAID line

**${input.incomingRaids.enabled ? 'ON for this sensitivity run' : 'OFF by default in this report'}.** Run \`npm run sim:economy -- --incoming-raids\` to enable it; this rewrites the same generated report/chart. Rerun without the switch to restore the baseline; \`--check\` must use the same switch as the generated output.

Assume exposure at each visit's start and ${input.incomingRaids.attemptsPerVisit} attempted button press(es), spaced by the ${input.incomingRaids.recoverySeconds} s recovery and only while the visit is still active. No extra visit or screen time is added and none occur during rests/missions. Care/exposure and press frequency are external assumptions, not a full status emulator. The initial press settles before shopping; any later press sees the remaining wallet.

Today's local button rules are a ${input.incomingRaids.attackerWinProbability * 100}% attacker-win chance: lose min(wallet, max(${input.incomingRaids.minimumLoss}, floor(wallet × ${input.incomingRaids.lossShare}))); otherwise defend and gain ${input.incomingRaids.defendedReward} Dust. Gains and losses are separate. This is an isolated sensitivity using current button rules even for proposals; it does not implement L2's proposed removal of raid losses. Neither raids nor defense gains are included in the G10 daytime taper.

| Scenario / player | Landed attempts | Defended | Defense gains | Raid losses |
| --- | ---: | ---: | ---: | ---: |
${raids.join('\n')}

## Weekly ending wallets

![Four scenario panels with independent labelled vertical scales compare weekly wallets for light, regular and committed players.](economy-sim.svg)

Player colours and week positions match; vertical scales differ by scenario. Compare labelled amounts, not apparent slopes across panels. Rest earnings are attributed to their civil accrual days but become spendable on return; end-of-day wallets are accrual summaries, not permission to shop mid-nap.

| Scenario / player | ${Array.from({ length: input.weeks }, (_, week) => `W${week + 1}`).join(' | ')} |
| --- | ${Array.from({ length: input.weeks }, () => '---:').join(' | ')} |
${wallets.join('\n')}

## Limits and reproduction

- Live rules, payouts, saves, UI and art are unchanged. The app never imports this simulator.
- Real backend raids, Together bonuses, multiplayer, visitors, device use and timer/clock faults are excluded. The optional local button is off in baseline results.
- The authored policies deliberately limit purchases. Different hat/raid seeds can change spending and milestones; no outcome distribution or causal behavioural claim is estimated.
- Reproduce with \`npm run sim:economy\`; validate fixtures and generated Markdown/SVG with \`npm run check:economy-sim\`. Both use only pinned source inputs and fixed seeds.
`;
}

/** Standalone, accessible SVG; each panel declares its independent wallet scale. */
export function renderEconomyChart(input: EconomyInputs, simulations: Simulation[]): string {
  const width = 960;
  const panelHeight = 290;
  const top = 75;
  const height = top + input.scenarios.length * panelHeight + 26;
  const left = 105;
  const right = width - 35;
  const colors = ['#176B58', '#315DA8', '#B14C32'];
  const plots = input.scenarios
    .map((scenario, index) => {
      const panelTop = top + index * panelHeight;
      const plotTop = panelTop + 48;
      const plotBottom = panelTop + 236;
      const rows = simulations.filter((result) => result.scenario === scenario.name);
      const largest = Math.max(
        input.initial.dust,
        ...rows.flatMap((result) => weeklyWallets(input, result)),
      );
      const magnitude = 10 ** Math.floor(Math.log10(Math.max(1, largest)));
      const maximum = Math.max(1, Math.ceil(largest / magnitude) * magnitude);
      const x = (week: number) => left + ((right - left) * week) / input.weeks;
      const y = (wallet: number) => plotBottom - ((plotBottom - plotTop) * wallet) / maximum;
      const ticks = Array.from({ length: 5 }, (_, tick) => {
        const value = (maximum * tick) / 4;
        const at = y(value);
        return `<line x1="${left}" y1="${at}" x2="${right}" y2="${at}" stroke="#DCE3E9"/><text x="${left - 12}" y="${at + 5}" text-anchor="end">${number(value)}</text>`;
      }).join('');
      const weeks = Array.from(
        { length: input.weeks + 1 },
        (_, week) =>
          `<text x="${x(week)}" y="${plotBottom + 23}" text-anchor="middle">${week}</text>`,
      ).join('');
      const lines = rows
        .map((result) => {
          const playerIndex = input.players.findIndex((player) => player.name === result.player);
          const color = colors[playerIndex % colors.length];
          const values = [input.initial.dust, ...weeklyWallets(input, result)];
          const points = values.map((wallet, week) => `${x(week)},${y(wallet)}`).join(' ');
          return `<g><title>${escapeXml(result.player)}: ${values.map((wallet, week) => `week ${week} ${number(wallet)} Dust`).join('; ')}</title><polyline points="${points}" fill="none" stroke="${color}" stroke-width="3"/>${values.map((wallet, week) => `<circle cx="${x(week)}" cy="${y(wallet)}" r="3.5" fill="${color}"/>`).join('')}</g>`;
        })
        .join('');
      return `<g role="group" aria-labelledby="panel-${index}"><title id="panel-${index}">${escapeXml(scenario.name)}, independent scale zero to ${number(maximum)} Dust</title><text x="${left}" y="${panelTop + 13}" class="panel-title">${escapeXml(scenario.name)}</text><text x="${right}" y="${panelTop + 13}" text-anchor="end">Wallet: 0–${number(maximum)} Dust</text>${ticks}<line x1="${left}" y1="${plotTop}" x2="${left}" y2="${plotBottom}" stroke="#596A78"/><line x1="${left}" y1="${plotBottom}" x2="${right}" y2="${plotBottom}" stroke="#596A78"/>${weeks}${lines}<text x="${(left + right) / 2}" y="${plotBottom + 46}" text-anchor="middle">Simulation week</text></g>`;
    })
    .join('\n');
  const legend = input.players
    .map(
      (player, index) =>
        `<g transform="translate(${left + index * 220},47)"><line x1="0" y1="0" x2="24" y2="0" stroke="${colors[index % colors.length]}" stroke-width="3"/><text x="32" y="5">${escapeXml(player.name)}</text></g>`,
    )
    .join('');
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${width} ${height}" width="${width}" height="${height}" role="img" aria-labelledby="chart-title chart-desc">
<title id="chart-title">Dream Dust ending wallets over ${input.weeks} weeks</title>
<desc id="chart-desc">Four scenario panels with independent labelled vertical scales. ${input.players.map((player) => player.name).join(', ')} keep the same colors. Lines include starting wallets and each week's ending wallet; exact values are in the accompanying Markdown table.</desc>
<style>text{font:14px system-ui,sans-serif;fill:#263846}.title{font-size:22px;font-weight:700}.panel-title{font-size:17px;font-weight:700}</style>
<rect width="100%" height="100%" fill="#FFFFFF"/>
<text x="${left}" y="26" class="title">Dream Dust wallets · independent scale per scenario</text>
${legend}
${plots}
</svg>\n`;
}
