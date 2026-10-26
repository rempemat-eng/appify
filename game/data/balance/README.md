# Balance data (Claude L, a proposal)

Claude A's assignment (25 Oct): "balance as data, no code. Enemy stats, loot tables, Glint sources and sinks, and levelling curves in game/data/balance/**, with a short rationale." These are **first values for the sim, not settings\*\*. Codex owns the formulas as code and tests: C60 owns the abilities and runner, and C61 owns enemy behaviour. Nothing here is read by the game until they wire it in.

| File           | What                                                                                                                                     |
| -------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| `enemies.json` | Health, damage, wind-up, XP, Glint and item chance for the six roles; elite and boss budgets; difficulty; the targets the numbers aim at |
| `levels.json`  | Character level 1 to 30 (health, XP curve, XP sources), gear level, familiar bond, and each region's level band                          |
| `loot.json`    | Rarity weights by source, chests, bosses, bad-luck protection, seeds, materials and salvage                                              |
| `glint.json`   | Every Glint source and sink (game-design 10.2) with first values by act, and the defeat cache                                            |

The sources are game-design v2: §4.4 and §4.6 for enemies and difficulty, §5 for loot, §6 for levelling, §10 for Glint, and the "first values" appendix. The canonical damage comes from MyGame's `abilities-v1.json` (#245).

## Aligned with Claude A's progression (#279)

Matt decided on 25 Oct that levels buy skill points in a tree per folk, Glint buys things but never points, each folk has one signature weapon with loot as fittings, and only trinkets carry small perks, never damage. These files follow that: `levels.json` gives skill points instead of perk cards, `loot.json`'s rarities apply to fittings, and `glint.json` points at #279 for weapon tiers, respecs and outfits instead of setting its own prices.

## One unit for health and damage

**Health is counted in the same points as the canonical damage values: 1 point of health per point of damage.** A Bramble arrow does 22 and a Cairn punch 35, so a level-1 grunt has 100 health. This answers C60's open question on #261, where canonical damage of 9 to 49 had to be mapped to a foundation HP of 3 to 12. Claude A confirms or overrides it. With this rule, C61's placeholder HP (4, 8, 12) and the foundation's 5-HP player are replaced by these tables, and nothing is divided or rounded on the way.

## Why these numbers

- **Grunt health is 100, not the appendix's 60.**
  - The mean primary damage per second across the fourteen kits is 50.6 (damage over cooldown). It ranges from 22.6 for Morel's primary alone to 61.8 for Velvet.
  - The appendix targets a grunt freed in 3 to 5 s with about 4 melee hits. Assuming half uptime in a real fight (dodging, repositioning), time to free = health / (DPS × 0.5). That makes 100 health about 4.0 s, and 60 would be 2.4 s, too quick.
  - The other roles keep the appendix's ratios to the grunt, multiplied by about 1.67: swarmer 35 (1.4 s), shooter 75 (3.0 s), caster 85 (3.4 s), lunger 115 (4.5 s), tank 235 (9.3 s from behind, twice that through its front).
- **Enemy health grows ×1.11 a level and weapon power ×1.09.** At equal level, time to free therefore lengthens slowly: about ×1.7 by level 30. Perks and affixes, about +60 % by then, close most of that gap, so fights feel the same length across the story without levels inflating.
- **Enemy damage grows linearly, +12 % of base a level.** That is the same rate as the player's health (100 + 12 a level), so a grunt's hit takes the same share of the bar at every equal level: 12 points of 100 at level 1, about 8 hits to defeat you on Normal. A ×1.08 compound rate, the obvious alternative, would make late hits twice as heavy compared with your health.
- **XP:** 100 × level^1.5 to the next level, 189,030 in all to level 30. A main quest pays 40 % of the current level's need and a grunt 1 %. Fights against enemies below your level pay 15 % less per level down, with a floor of 10 %, so the story leads, as game-design §6 asks.
- **Region bands** follow the road order of Claude K's arc, about three levels a region, ending at 30 on Lumen.
- **Loot** keeps the appendix's normal-enemy weights (60/28/10/2) and bad-luck counter (8), and adds tables for elites, chests and bounties that are richer in that order. Chests have a Fine floor, and the share of the region's weapon family stays at 60 %.
- **Glint pacing.** Act 1 has one region's worth of income: four main quests at 150, four side quests at 60, two bounties at 80, the boss at 300, six camps (a 40-Glint chest plus about 25 enemies at 3), three dungeon chests at 80 and a siege at 120. That comes to about 2,350 Glint. Spending is three building tiers at about 500 each plus three forge upgrades at about 120. Income is about 1.3 times the sinks, the rule in glint.json, so the village keeps pace without farming. Later acts scale the same way. Codex's economy sim scaffolding (#211) can run this per region once the arc's quest counts are fixed.
- **Kept from the pillars:** nothing runs on real time, nothing expires, there is no gambling, and loot and XP are the same on every difficulty.

## Open for the owners

- **C60** (#149): field names. These files use `health`, `damage` and `windup_s` per role, and the level formulas as strings. Say if the runner wants other names or numeric coefficients only.
- **C61:** the role set. Today's code has rusher, shooter, shield and elite; the design has swarmer, grunt, shooter, lunger, caster and tank. This proposal maps rusher to lunger, shield to tank, and elite to a multiplier on any role.
- **Claude K:** quest counts per region, which set the Glint and XP totals.
- **Not measured yet:** fight feel, uptime in real play (the 0.5 is an assumption), and every value in a running build. The next step is the harness proposed on #149, if MyGame and C60 want it.
