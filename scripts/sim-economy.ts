import assert from 'node:assert/strict';
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { format, type FormatConfig } from 'oxfmt';
import { economyInputs } from './economy-inputs';
import { simulate, total } from './economy-model';
import { renderEconomyChart, renderEconomyReport } from './economy-report';

async function main() {
  const root = new URL('../', import.meta.url);
  const simulations = economyInputs.scenarios.flatMap((scenario) =>
    economyInputs.players.map((player) => simulate(player, scenario)),
  );
  const config: FormatConfig = JSON.parse(readFileSync(new URL('.oxfmtrc.json', root), 'utf8'));
  const report = await format(
    'docs/codex/economy-sim.md',
    renderEconomyReport(economyInputs, simulations),
    config,
  );
  assert.equal(report.errors.length, 0, 'the generated report formats cleanly');
  const outputs = [
    ['docs/codex/economy-sim.md', report.code],
    ['docs/codex/economy-sim.svg', renderEconomyChart(economyInputs, simulations)],
  ] as const;
  if (process.argv.includes('--check')) {
    for (const [path, content] of outputs)
      assert.equal(
        readFileSync(new URL(path, root), 'utf8'),
        content,
        `${path} is stale; run npm run sim:economy`,
      );
    console.log('Economy report and chart match the typed inputs.');
    return;
  }
  mkdirSync(new URL('docs/codex/', root), { recursive: true });
  for (const [path, content] of outputs) writeFileSync(new URL(path, root), content);
  console.table(
    simulations.map((r) => ({
      scenario: r.scenario,
      player: r.player,
      earned: total(r.earned),
      spent: total(r.spent),
      balance: r.balance,
      level: r.level,
    })),
  );
  console.log('Wrote docs/codex/economy-sim.md and economy-sim.svg');
}
void main().catch((error: unknown) => {
  console.error(error);
  process.exitCode = 1;
});
