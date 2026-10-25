# Character progression: skill trees, weapon tiers, outfits and accessories (25 Oct)

Matt, 25 Oct: "can you create new outfits/ accessories for the characters that they unlock some way and if i upgrade/ level up a character their weapons should become cooler as well/ they should learn new abilities". His decisions on the first draft, the same day: a "skill tree that you spend level points on and then a new weapons unlocked at specific levels. money can be spent on cosmetics and other things in the map"; one signature weapon per folk with loot as fittings set into it; each folk pays the forge cheaply, and a late joiner arrives at the highest open tier; only trinkets carry small perks, never damage.

**Status.** Matt's four decisions are built in; the rest is Claude A's proposal for all fourteen folk. The data is in `game/data/progression/` (`catalogue.json` plus one file per folk); this page explains it, and its per-character section mirrors the JSON. **Every number is a placeholder** until play-tests and Claude L's balance harness set it. Nothing here changes game code, art or the save.

**What it builds on.**

- **Codex's kits** (`game/data/abilities/<id>.json`, C60, PR #261): each folk's primary, secondary, block and special with its powered form. They are canonical: every tree node is a modifier layered over them at run time, and the kit files are never edited. Nodes that would change a count or rule inside a powered form are marked *(needs C60)* and raised on #149.
- **game-design.md** (PR #223): one shared level from 1 to 30, gear level and the forge, Glint, scrap and one material per region, sieges, arenas, the familiar's bond levels, and defeat that keeps everything. Its perk card of three per level is **replaced by the skill tree**, and its ideas are folded in as minor nodes.
- **The castwork cast** (the fourteen at 74 px, `CONTRACT.md`) and cast contract v2 on `claude-a/cast-v2` (8 facings; Bramble's bow is being redrawn larger there, so tier sizes are given relative to the tier-1 drawing).
- **The vertical slice** (`vertical-slice.md`): Hale's forge is the first restored service.

## 1. Rules

1. **Growth you can see.** Every step shows on the folk: a new move, a weapon that looks finer, a new look. Nothing is a hidden number.
2. **Levels buy skills; Glint buys things.** Skill points come only from levels. Glint pays for cosmetics, forge work, village restoration, shops, map services and respecs, and never for points, levels or XP.
3. **No grind wall, no gambling.** Weapon tiers are level milestones forged cheaply; cosmetics come from play you would do anyway, and rare drops have a bad-luck counter and published rates.
4. **Small, readable mechanics.** No tier multiplies damage (gear level does that, game-design appendix B: "no other multipliers"). A node is one line. A trinket perk is one line, never combat damage.
5. **Nothing on a clock.** No screen time, rest, naps, dailies, timers or expiring stock.
6. **No hand-drawn combinations.** Outfits and tiers are parameters of the castwork rig, rendered into every facing and clip by the exporter (section 6).

## 2. Levels and the skill tree

The shared level runs from 1 to 30 (about three per region). **Every level from 2 gives one skill point** (29 in all), spent in the folk's own tree. A folk starts with Codex's full kit; the tree grows it.

**Each folk's tree has three branches** that match its kit (Bramble: Bow, Blade, Woodcraft), with **five nodes a branch, fifteen in all**:

| Node | Cost | Unlocks at (branch 1 / 2 / 3) | What it is |
| --- | --- | --- | --- |
| Minor | 1 | level 2 / 2 / 4 | a small passive: a few per cent of cooldown, reach, guard cost or speed |
| Technique | 2 | 3 / 9 / 16 | a new move or behaviour built on the kit (the folk's signature growth) |
| Minor | 1 | 6 / 11 / 18 | a second small passive |
| Technique upgrade | 3 | 12 / 20 / 26 | the technique's stronger form |
| Keystone | 4 | 22 / 24 / 28 | a branch-defining change |

- **It cannot be rushed.** Each node needs its level and the node before it in its branch.
- **The build choice.** The whole tree costs 33 points and a folk has 29 at level 30, so a finished folk has everything except one keystone. On the way, the order you take nodes in is the choice (at level 12 you can afford about half the open nodes).
- **Points are per folk, the level is shared.** A late joiner arrives at the shared level with all its points to spend, and a "choose for me" button that follows the first branch (game-design 6: nothing is levelled twice).
- **Respec (proposal).** At your bed in the hut, for 50 Glint (the first one free), every point comes back. Never in a fight, siege or dungeon.
- **No new buttons.** Each technique binds to an existing input (primary, secondary, block, special, dodge), a short timing window after one ("primary within 0.4 s after the sweep"), a held guard, or a passive condition. None uses a hold on primary, because Codex's primary repeats while held.
- **Art cost.** Of the 42 techniques, 38 reuse existing drawings with a small effect sprite. Four need one new clip each: Bramble's `secondary_loose`, Velvet's `primary_waltz`, Mirra's `guard_wave` and Ashe's `guard_check`. Rook's Air Shot needs the airborne primary that #257 already lists as missing. Minors and keystones need no new body art.
- **Several techniques use the dodge and the perfect dodge** (game-design 4.2; Codex's kits have no dodge of their own). If the dodge changes, those bindings change with it.

## 3. Weapon tiers and fittings

Each folk keeps one **signature weapon**, the item its kit is built on: Bramble's bow, Iona's spear, Pendle's revolver, Cairn's fists, Morel's flask and catalyst, Velvet's sabre, Tam's wraps, Mirra's wrist bands and gem, Brine's harpoon gun, Ashe's sword, Clack's launcher, Nix's laser arm, Rook's carbine and Mote's core and glass. **Its tiers are level milestones**: a tier opens at its level, and Hale forges it cheaply, per folk.

| Tier | Name | Opens at | Sockets | Hale forges it for (placeholders) |
| --- | --- | --- | --- | --- |
| 1 | Made | level 1 | 1 | the starting look |
| 2 | Fitted | level 8, once the forge is restored | 2 | 60 Glint, 5 scrap, 2 of the folk's home material |
| 3 | Masterwork | level 16 | 2 | 150 Glint, 10 scrap, 4 home material |
| 4 | Starfall | level 24, at the great forge | 3 | 300 Glint, 20 scrap, 6 home material, 1 starshard |

- **Loot is fittings.** Weapon drops are fittings with game-design's rarity and affixes (5.3 and 5.4): a Fine fitting carries one affix, a Heroic three. Hale sets them into the signature weapon's sockets, and moves them between folk for a small Glint fee. Gear level and its forge upgrade (5.6) apply to the signature weapon. A fitting is a small visible part where it sits (a gem, a band, a scope).
- **What a tier changes.** The drawing (silhouette, material, glow, size; each tier is described for an artist in the folk's JSON and below), one more socket at tiers 2 and 4, and **one small handling change** (tiers 2 and 3: a few per cent of reload, reach, cooldown, speed or guard cost; tier 4: one named effect, such as Pendle's last round being a critical hit). Power stays with gear level.
- **Sizes are relative to the tier-1 drawing** (for example, +2 px per limb), so they hold when cast v2 redraws a weapon.
- **Readable at 74 px.** At 1x, each tier differs from the one before by at least 3 px of silhouette or one new 2 x 2 px colour cluster. Several tier 4 glows carry state the player needs: Pendle's six chamber glints go dark as he fires, Clack's rocket nose shows the reload, and Nix's seams brighten with heat.
- **Starshards** are fist-sized splinters of the moon: guaranteed on the first defeat of each boss from act 3 on and in the deep shards after the story, and sold by Moss at a fixed price after the story. Never random-priced.
- **Hale** shows the next tier on the folk before you pay ("Show me"). Forging never fails.
- **A late joiner** arrives at the highest tier any folk has reached, except Starfall, which is always a forge step.

## 4. Outfits and accessories

Each folk has its drawn **home** look plus **3 outfits** and **4 accessories**, one for each of the slots **head, back, neck and trinket**.

- **Outfits** change cloth and colours only: always cosmetic.
- **Accessories** are cosmetic, except each folk's **trinket**, which carries one small perk (a proposal): a pickup radius, a shorter burn, a defeat-cache marker seen from further away. Only the active folk's trinket counts, so perks never stack, and none adds combat damage.
- **Helmets come first.** Ashe, Brine and Rook wear helmets (Ashe and Rook put theirs on in the special), so their head slot dresses the one helmet (a crest, a fin, an antenna) instead of adding a hat that would have to vanish.
- **Back gear stays visible.** A back item never hides a tagged back piece (Bramble's quiver, Brine's pack and hose, Pendle's slung rifle, Clack's loader frame). Where it replaces a drawn part (Bramble's cloak replaces the mantle), the JSON says `replaces`.

**Unlock sources.** Every folk's seven items use all six, and each unlocks on an event the game already raises or plans:

| Source | Event | Notes |
| --- | --- | --- |
| Story | `quest:<id>:done` | the folk's own quest (game-design 8.3) or a named village or main quest; quest ids are Claude K's, placeholders here |
| Arena | `arena:<ring>:<rank>` | the first Bronze, Silver or Gold in a ring; never Star, which is Hard only |
| Village | `restore:<building>:<tier>` | a building restored to a tier: the loom gives wool, the glassworks lenses, the trophy hall heraldry |
| Familiar bond | `bond:any:<level>` | any familiar reaching that bond level |
| Rare drop | `drop:<region>` | camp chests (3 %) and elites (2 %) in one region; guaranteed by the 12th chest there; only drops what you do not own; rates in the journal |
| Glint | `buy:stall:<item>` | Moss's stall at a fixed price (200 to 1,000) once its tier stocks the item |

A drop for a folk you have not met yet waits in the wardrobe and shows when they join. Outfits and accessories are changed at the bed in your hut or the wardrobe screen, never in a fight, siege or dungeon (the AGENTS.md switching rule).

## 5. Per character

<!-- per-character: generated from game/data/progression; edit the JSON first -->

### Bramble

Older grassland ranger; left-handed archer: bow in the RIGHT hand, quiver over the LEFT shoulder, billhook at the RIGHT hip, folding buckler on the RIGHT forearm. Kit (Codex): Quickdraw, Billhook, Briar buckler, Briarshot.

| Branch | Lv 2 to 4 (1 pt) | Technique (2 pts) | Minor (1 pt) | Upgrade (3 pts) | Keystone (4 pts) |
| --- | --- | --- | --- | --- | --- |
| **Bow** (primary, special) | Fletcher (2): Arrows fly 6 % faster. | **Steady Aim** (3): Standing still and not firing builds Aim pips; the next arrow spends them for extra power. *How:* passive: stand still without firing. | Long Eye (6): Aim pips are kept while walking slowly for 0.5 s. | Steady Aim II (12): Pips build faster, and a full three-pip arrow pierces one foe. | Briar Volley (22): Briarshot's first arrow splits into two. *(needs C60)* |
| **Blade** (secondary) | Keen Hook (2): Billhook cooldown -8 %. | **Hook and Loose** (9): A point-blank arrow follows the sweep and knocks the nearest foe back. *How:* primary within 0.4 s after the billhook sweep. | Wide Sweep (11): Billhook arc +10 degrees. | Hook and Loose II (20): The sweep also staggers light foes, so the arrow lands. | Hedger (24): A billhook sweep that hits three foes refunds a dodge charge. |
| **Woodcraft** (block) | Bracer Hide (4): Buckler guard cost -8 %. | **Briar Snare** (16): A briar snare drops at your feet and roots the next ground foe that steps on it. *How:* lower the buckler within 0.5 s after it blocks a hit. | Forager (18): Freed woodland foes drop seeds a little more often. | Briar Snare II (26): Two snares at once; a foe rooted by Briarshot springs the nearest snare too. | Old Ranger (28): Snares and roots last 25 % longer. |

| Tier (level) | Bow | Changes |
| --- | --- | --- |
| 1 Yew bow (1) | the tier-1 drawing (being redrawn larger in cast v2): a plain shallow recurve with a leather grip wrap | starting look |
| 2 Carved recurve (8) | the limb tips curl back +3 px each into a clear recurve; the grip is wrapped in green cord over the whole grip | arrow speed +8 % |
| 3 Horn-tipped bow (16) | pale horn caps (3 px) on both tips; a 2 x 3 px shard set into the riser in a gold bezel | primary cooldown -6 % |
| 4 Starfall bow (24) | limbs of dark moonwood that flare into crescent tips (+2 px each end over tier 3); gold riser; the string is drawn in starlight | Starlit: a three-pip arrow also shows the foe's weak point for 2 s |

Outfits: Autumn forester (story: own quest); Sheepskin mantle (village: fold and loom tier 1); Ranger's pine (450 Glint).
Accessories: Feathered cap, head (rare drop: valley); Patched travelling cloak, back (arena: training yard, silver); Oak-leaf scarf, neck (bond 3); Acorn whistle, trinket (250 Glint, perk: pickup magnet radius +15 %).

### Iona

Grassland storm-lancer; one long spear in the RIGHT hand, the LEFT grips the same shaft for two-handed actions; long braid down the back, magenta scarf. Kit (Codex): Spearpoint, Wind lunge, Gust guard, Storm Mantle.

| Branch | Lv 2 to 4 (1 pt) | Technique (2 pts) | Minor (1 pt) | Upgrade (3 pts) | Keystone (4 pts) |
| --- | --- | --- | --- | --- | --- |
| **Spear** (primary) | Long Haft (2): Spearpoint reach +3. | **Gale Step** (3): The roll flows into a long thrust that reaches further than Spearpoint. *How:* primary within 0.3 s after a dodge. | Quick Recovery (6): Spearpoint recovers 6 % faster. | Gale Step II (12): A Gale Step that hits gives back half a dodge charge. | Thunderhead (22): Storm Mantle's arcs reach one tile further. *(needs C60)* |
| **Lunge** (secondary, special) | Windborne (2): Wind lunge cooldown -8 %. | **Static Charge** (9): The next Wind lunge into a charged foe discharges one small arc to a second foe. Smaller than Storm Mantle's arcs, and only from a lunge. *How:* passive: every third spear hit on the same foe charges it. | Follow-through (11): A lunge that hits refreshes Spearpoint at once. | Static Charge II (20): The discharge interrupts a shooter's wind-up, once per foe. | Gale Rider (24): Two Wind lunges can be chained before the cooldown. *(needs C60)* |
| **Gust** (block) | Steady Feet (4): Gust guard drain -10 %. | **Windbreak** (16): The projectile is turned back along its path instead of draining guard. *How:* raise Gust guard within 0.2 s of a projectile reaching you. | Crosswind (18): Shooters' projectiles slow near your raised guard. | Windbreak II (26): Deflected projectiles carry a storm arc. | Eye of the Storm (28): While guarding, foes in melee are pushed back once a second. |

| Tier (level) | Spear | Changes |
| --- | --- | --- |
| 1 Ash spear (1) | today's drawing: steel leaf blade, gold collar, gold-banded brass shaft, steel butt spike | starting look |
| 2 Windcut spear (8) | two swept barbs (4 px each) below the leaf blade; a magenta pennon (2 x 6 px) tied at the collar that trails like her scarf | primary reach +4 |
| 3 Stormwrought spear (16) | the blade reforged in blued steel with a bright edge; three copper coil rings below the collar; the butt spike becomes a weighted ring pommel | secondary cooldown -8 % |
| 4 Starfall lance (24) | a pale moonsilver blade with a 1 px storm-blue fuller; a gold crescent collar; the pennon becomes a ribbon of light 8 px long | Stormlit: the first hit after a Wind lunge arcs to one more foe for 30 % |

Outfits: Moor coat (story: own quest); Yard drill coat (village: training yard tier 2); Tempest (600 Glint).
Accessories: Kestrel hairpin, head (bond 4); Shoulder cloak, back (arena: training yard, gold); Moor tartan scarf, neck (rare drop: brackens); Weathervane charm, trinket (300 Glint, perk: the familiar's weak-point glint lasts 0.5 s longer).

### Pendle

Sunstone robot gunslinger; one revolver on the RIGHT hip, one marksman rifle slung across the back (stock at the right hip, barrel past the LEFT shoulder); cattleman hat; no clock motif. Kit (Codex): Revolver, Fan fire, Steel plate, Longshot.

| Branch | Lv 2 to 4 (1 pt) | Technique (2 pts) | Minor (1 pt) | Upgrade (3 pts) | Keystone (4 pts) |
| --- | --- | --- | --- | --- | --- |
| **Revolver** (primary) | Smooth Action (2): Revolver cooldown -5 %. | **Quick Hands** (3): Two rounds slip into the cylinder during the roll. *How:* a perfect dodge. | Speed Loader (6): Full reloads 10 % faster. | Quick Hands II (12): After a full reload from empty, the first shot is a critical hit. | High Noon (22): The sixth round of a cylinder knocks back. |
| **Fan fire** (secondary) | Wrist Flick (2): Fan fire cooldown -8 %. | **Ricochet** (9): Fan fire rounds that hit high cover bounce once. *How:* passive on Fan fire. | Tight Fan (11): Fan fire spread -10 %. | Ricochet II (20): A bounced round turns toward the nearest foe within 30 degrees. | Gunsmoke (24): Fan fire leaves smoke that makes shooters miss their next shot. |
| **Marksman** (special, block) | Plate Fold (4): Steel plate raises 15 % faster. | **Dead Eye** (16): The foe under the aim shows its weak point (the familiar's glint) for the next shot. *How:* during Longshot, hold still for 0.6 s. | Steady Stock (18): Longshot shots knock tanks back slightly. | Dead Eye II (26): A Longshot weak-point hit gives back 1 s of Longshot. *(needs C60)* | Bullseye (28): Longshot weak-point hits stagger elites. |

| Tier (level) | Revolver | Changes |
| --- | --- | --- |
| 1 Trail revolver (1) | today's drawing: gunmetal frame, walnut grip, visible cylinder and trigger guard | starting look |
| 2 Engraved revolver (8) | brass inlay lines on the cylinder; cream grip panels; the barrel 2 px longer | reload -8 % |
| 3 Brass-frame revolver (16) | a brass frame with two 1 px ports on the barrel; a red lanyard from the grip to the belt; the rifle's scope gains a brass sunshade to match | fan spread -10 % |
| 4 Six Suns (24) | the cylinder is sunstone glass lit from inside, with six 1 px chamber glints; a gold muzzle crown; a gold crescent front sight on the rifle | Six Suns: the last round in the cylinder is a critical hit |

Outfits: Gulch duster (story: own quest); Oasis whites (village: water tower tier 1); Midnight rider (arena: dusty corral, gold).
Accessories: Flat-brim hat, head (rare drop: sunstone); Serape, back (500 Glint); Star bandana, neck (bond 5); Lucky silver dollar, trinket (village: stall tier 2, perk: the first reload of each fight is 15 % faster).

### Cairn

Moss-covered granite golem from the woodland circle, about 90 px; great round fists, a sprout on the LEFT shoulder, two floating pebbles over the RIGHT shoulder. Kit (Codex): Stone fist, Boulder, Crossed arms, Old Growth.

| Branch | Lv 2 to 4 (1 pt) | Technique (2 pts) | Minor (1 pt) | Upgrade (3 pts) | Keystone (4 pts) |
| --- | --- | --- | --- | --- | --- |
| **Stone** (block) | Granite Skin (2): Guard maximum +10 % (a modifier on the canonical guard). | **Bedrock** (3): Once every few seconds the guard takes a whole hit with no guard cost. *How:* passive on Crossed arms. | Settled (6): Guard recovers 10 % faster. | Bedrock II (12): A Bedrock block shoves the attacker back. | Standing Stone (22): While guarding he cannot be knocked back. |
| **Throw** (secondary) | Strong Arm (2): Boulders fly 8 % faster. | **Stonebreak** (9): A boulder that hits a tank cracks its front armour for a few seconds. *How:* passive on Boulder. | Heavy Stone (11): Boulder knockback +20 %. | Stonebreak II (20): A boulder that hits any foe slows its next wind-up. | Landslide (24): A boulder hitting a wall breaks into three small stones. |
| **Moss** (primary, special) | Moss Fists (4): Stone fist recovers 5 % faster. | **Pebble Ward** (16): Each pebble catches one projectile and re-forms after a while. *How:* passive: the two pebbles over his right shoulder. | Deep Roots (18): Old Growth shockwave +10 % radius. | Pebble Ward II (26): A pebble that catches a shot flicks it back. | Circle's Blessing (28): Freed foes near Cairn heal him 1 %. |

| Tier (level) | Fists | Changes |
| --- | --- | --- |
| 1 Bare stone (1) | today's drawing: round granite fists with dark joint gaps | starting look |
| 2 Banded fists (8) | two iron knuckle bands round each fist, raised 2 px from the stone | boulder speed +8 % |
| 3 Rooted fists (16) | roots wrap the bands and end in small moss cushions on the knuckles; a fern curl on the right wrist | guard cost -10 % |
| 4 Moonvein fists (24) | seams of white-gold moonstone run through the fist cracks; a crescent shard set in each band | Moonvein: Stone fist staggers swarmers |

Outfits: Spring bloom (village: greenhouse tier 1); Circle runes (story: own quest); Basalt (arena: basalt ring, silver).
Accessories: Daisy crown, head (bond 2); Wren's nest, back (rare drop: valley); Festival ribbon, neck (200 Glint); Smooth river stone, trinket (rare drop: lull, perk: tonics are drunk 15 % faster).

### Morel

Older grassland alchemist; one blue flask in the RIGHT hand, a closed reagent case on the RIGHT hip, the catalyst apparatus at the LEFT hip, one mask on the chest (on the face in the special). Kit (Codex): Reagent flask, Catalyst, Mineral ward, Catalyst mask.

| Branch | Lv 2 to 4 (1 pt) | Technique (2 pts) | Minor (1 pt) | Upgrade (3 pts) | Keystone (4 pts) |
| --- | --- | --- | --- | --- | --- |
| **Reagents** (primary) | Good Arm (2): Flask range +8 %. | **Tacky Reagent** (3): Foes standing in a patch move slower. *How:* passive on reagent patches. | Long Brew (6): Patches last 15 % longer. | Tacky Reagent II (12): Slowed foes take more from a Catalyst spark. | Three Flasks (22): Every third flask leaves a patch twice the size. |
| **Remedies** (block) | Mineral Lining (2): Mineral ward guard cost -8 %. | **Mineral Skin** (9): Instead of a patch, a mineral skin softens the next hit you take. *How:* throw a flask at your own feet (aim within 1.5 tiles). | Field Medic (11): A light hit no longer interrupts drinking a tonic. | Mineral Skin II (20): The skin also clears burn, chill and shock. | Antidote (24): Burn, chill and shock on you wear off 25 % sooner. |
| **Catalysis** (secondary, special) | Spark Gap (4): Catalyst cooldown -8 %. | **Drowsy Fume** (16): A fume rises from the chain and makes foes in it attack half as often for a short time. *How:* Catalyst through three or more patches at once. | Close Burst (18): Catalyst's close burst +15 % radius. | Drowsy Fume II (26): The fume spreads to patches next to it. | Grand Reaction (28): Catalyst mask's chains jump one extra patch. *(needs C60)* |

| Tier (level) | Flask and catalyst | Changes |
| --- | --- | --- |
| 1 Field kit (1) | today's drawing: blue glass flask held by the neck; brass chamber, glass bulb and copper coil | starting look |
| 2 Caged flasks (8) | a copper wire cage (1 px grid) over the flask glass; a second coil on the catalyst | throw range +10 % |
| 3 Sealed flasks (16) | a brass cap with a red wax seal on each flask; brass corners on the reagent case; the catalyst bulb 2 px larger with a small gauge | patch lifetime +15 % |
| 4 Starglass kit (24) | pale violet-white glass with a 2 px mote of light floating inside each flask; the catalyst bulb holds a captive spark; gold rims on the mask lenses | Starglass: a foe in a patch shows its weak point when Catalyst sparks through it |

Outfits: Herbalist's apron (village: apothecary tier 2); Laboratory coat (story: own quest); Ember smock (rare drop: fire country).
Accessories: Bowler hat, head (300 Glint); Oilcloth cape, back (arena: gear floor, silver); Spectacles on a chain, neck (bond 4); Pocket mortar, trinket (story: apothecary first tonic, perk: tonics heal 5 % more).

### Velvet

Coastal duellist from Driftwood; one sabre in the LEFT hand (closed brass knuckle-bow), its empty scabbard on the RIGHT hip, one black lantern by its bail in the RIGHT hand. Kit (Codex): Sabre, Lantern flare, Sabre parry, Black Lantern.

| Branch | Lv 2 to 4 (1 pt) | Technique (2 pts) | Minor (1 pt) | Upgrade (3 pts) | Keystone (4 pts) |
| --- | --- | --- | --- | --- | --- |
| **Sabre** (primary, block) | Light Wrist (2): Sabre recovers 5 % faster. | **Riposte** (3): The next sabre cut comes faster. In the base form only; Black Lantern's long counter-thrust is unchanged. *How:* a parry in the first 0.2 s of a melee hit. | Duellist (6): Parry raises 15 % faster. | Riposte II (12): The riposte cut exposes the foe, as Lantern flare does. | En Garde (22): After a parry, the next hit you take is reduced by 20 %. |
| **Lantern** (secondary) | Trimmed Wick (2): Lantern flare cooldown -8 %. | **Dim** (9): The lantern shutters after the flare; for a moment shooters lose track of her and hold fire. *How:* passive after Lantern flare. | Wide Beam (11): Flare radius +10 %. | Dim II (20): A perfect dodge while dimmed takes time off the flare's cooldown. | Lighthouse (24): Exposed foes stay exposed 1 s longer. |
| **Dance** (special) | Light Step (4): Walk speed +4 %. | **Moth's Waltz** (16): The third cut becomes a stepping lunge-cut through the foe. *How:* the third sabre cut in a row. | Tails Fly (18): The third cut's reach +4. | Moth's Waltz II (26): The lunge leaves a pale echo that cuts once more half a second later. | Black Waltz (28): Black Lantern's echoes cut once as they fade. *(needs C60)* |

| Tier (level) | Sabre | Changes |
| --- | --- | --- |
| 1 Naval sabre (1) | today's drawing: curved steel blade, brass knuckle-bow guard | starting look |
| 2 Blackened sabre (8) | a blackened fuller with a bright edge; a second bar on the knuckle-bow | arc degrees +5 |
| 3 Basket-hilt sabre (16) | a full brass shell guard (5 x 5 px) round the fist; a violet sword knot (5 px) from the pommel | flare cooldown -8 % |
| 4 Moonlit sabre (24) | a moonsilver blade whose edge carries a pale light; the black lantern's cage turns gold and its flame pale blue-white | Moonlit: a perfect parry flashes the lantern and exposes foes within 2 tiles |

Outfits: Harbour blue (story: own quest); Keeper's oilskin (village: bell tower tier 2); Masquerade (arena: harbour jetty, gold).
Accessories: Tricorn, head (rare drop: valley); Boat cloak, back (550 Glint); Lace jabot, neck (bond 6); Moth brooch, trinket (arena: harbour jetty, bronze, perk: your defeat cache shows from twice as far).

### Tam

Mature Frostline ice monk in ochre and saffron robes; cool grey-blue wraps on both forearms, palms and shins; one mala round the neck; no weapon, the wraps are his. Kit (Codex): Frost palms, Ice ridge, Ice guard, Glacier Form.

| Branch | Lv 2 to 4 (1 pt) | Technique (2 pts) | Minor (1 pt) | Upgrade (3 pts) | Keystone (4 pts) |
| --- | --- | --- | --- | --- | --- |
| **Palm** (primary) | Quick Palms (2): Frost palms recover 5 % faster. | **Cold Breath** (3): The held breath steadies him: the next palm applies two frost instead of one. *How:* hold Ice guard for 1 s. | Deep Cold (6): Frost on foes lasts 20 % longer. | Cold Breath II (12): The steadied palm also slows the foe. | Hundred Palms (22): Every fifth palm in a row strikes twice. |
| **Ridge** (secondary, special) | Long Ridge (2): Ice ridge travels 10 % further. | **Ridge Wall** (9): The ridge ends in a low ice wall that stops projectiles for a moment. *How:* passive on Ice ridge. | Glacier Step (11): Glacier Form's glide +10 % speed. | Ridge Wall II (20): A wall that is hit shatters and chills foes beside it. | Avalanche (24): A ridge that hits three foes leaves an ice field. |
| **Stillness** (block) | Calm Guard (4): Ice guard drain -10 %. | **Still Water Step** (16): A frost patch is left where he rolled; foes on it slow. *How:* a perfect dodge. | Bothy Warmth (18): Chill on you wears off 20 % sooner. | Still Water Step II (26): Palms on a foe standing on the patch add one more frost. | Unmoved (28): Holding guard for 2 s makes the next block cost nothing. |

| Tier (level) | Wraps | Changes |
| --- | --- | --- |
| 1 Plain wraps (1) | today's drawing: grey-blue cloth wraps on forearms, palms and shins | starting look |
| 2 Frost-stitched wraps (8) | white zigzag stitching (1 px) along the wraps and a second wind at the wrists; three ice-blue beads added to the mala | ridge speed +10 % |
| 3 Hoarfrost guards (16) | pale ice plates (3 px) on the backs of both hands and the shins, tied over the wraps | guard drain -10 % |
| 4 Moonbead wraps (24) | the ice plates turn to clear starglass lit from inside; the guru bead becomes a small glowing moon (2 x 2 px) | Moonbead: a frost shatter also chills foes beside the target |

Outfits: Snow robes (village: training yard tier 1); Pilgrim (story: own quest); Temple gold (700 Glint).
Accessories: Straw rain hat, head (arena: castle courtyard, gold); Straw rain cape, back (rare drop: frostline); Winter mala, neck (bond 3); Kettle charm, trinket (300 Glint, perk: your first tonic of each outing refills at the next camp you free).

### Mirra

Oasis water diviner; hands empty and open in every clip (water is a scene effect); ivory headwrap with a turquoise gem above the RIGHT ear; turquoise wrist bands; shawl end over the LEFT shoulder. Kit (Codex): Water bolt, Spring seal, Water curtain, Oasis Unbound.

| Branch | Lv 2 to 4 (1 pt) | Technique (2 pts) | Minor (1 pt) | Upgrade (3 pts) | Keystone (4 pts) |
| --- | --- | --- | --- | --- | --- |
| **Springs** (secondary) | Deep Well (2): Spring seals last 10 % longer. | **Seep** (3): The spring heals her a little each second, for a few seconds per seal. *How:* passive: stand in one of your own spring seals. | Wide Seal (6): Seal radius +8 %. | Seep II (12): Dodges recharge faster while she stands in a seal. | Oasis (22): You may keep one more seal at a time. |
| **Currents** (primary, special) | Swift Water (2): Water bolts fly 8 % faster. | **Undertow** (9): The widened bolt pulls light foes one step toward the seal. *How:* passive: a water bolt fired through a seal. | Strong Current (11): Bolts through a seal +10 % width. | Undertow II (20): Pulled foes are soaked: their next hit taken is stronger. | Riverbed (24): Oasis Unbound's currents slow foes they cross. |
| **Curtain** (block) | Flowing Guard (4): Water curtain guard cost -8 %. | **Curtain Wave** (16): The curtain rolls forward as a wave that pushes foes and projectiles back. *How:* hold Water curtain for 0.8 s, then let go. | Spray (18): Blocked projectiles splash and soak the nearest foe. | Curtain Wave II (26): A spring seal is left where the wave breaks. | Still Pool (28): Seep also clears burn on you. |

| Tier (level) | Wrist bands and gem | Changes |
| --- | --- | --- |
| 1 Turquoise bands (1) | today's drawing: turquoise wrist bands with gold studs; the gem in a gold setting above the right ear | starting look |
| 2 Wave bands (8) | the bands 1 px wider with a carved gold wave line; a teardrop pendant (2 x 3 px) under the gem | bolt speed +8 % |
| 3 Paired bands (16) | a second band high on each forearm, joined to the wrist band by two fine gold chains; the gem +1 px each way | seal radius +10 % |
| 4 Starspring bands (24) | the turquoise turns to clear water-glass lit from inside; the gem becomes starlit oasis glass | Starspring: your seals last 1 s longer |

Outfits: Dusk caravan (story: own quest); Garden linen (village: water tower tier 2); Festival red (rare drop: sunstone).
Accessories: Gold head chain, head (400 Glint); Travelling shawl, back (arena: dusty corral, silver); Shell necklace, neck (rare drop: isles); Dowsing pendant, trinket (bond 5, perk: regional seeds drop 10 % more often).

### Brine

Coastal diver in a sealed copper helmet; one harpoon gun (wooden stock, gunmetal body, brass reel on the right side); an olive air pack with ONE hose to the helmet's right rear. Kit (Codex): Harpoon gun, Reel, Dive brace, Abyssal Drive.

| Branch | Lv 2 to 4 (1 pt) | Technique (2 pts) | Minor (1 pt) | Upgrade (3 pts) | Keystone (4 pts) |
| --- | --- | --- | --- | --- | --- |
| **Line** (secondary) | Oiled Reel (2): Reel 10 % faster. | **Anchor Line** (3): He arrives with a gun-butt strike. *How:* Reel toward an anchored heavy target. | Long Line (6): Tether length +10 %. | Anchor Line II (12): The arrival strike staggers the target. | Kraken (22): Reeling a heavy foe drags it one step toward you. |
| **Harpoon** (primary, special) | Quick Winch (2): Harpoon reload 8 % faster. | **Barbed Line** (9): A tethered foe takes a little damage each second. *How:* passive while a foe is tethered. | Heavy Head (11): Harpoon knockback +15 %. | Barbed Line II (20): Reeling a light foe into a wall stuns it. | Leviathan (24): Abyssal Drive's shots pierce one more foe. *(needs C60)* |
| **Brace** (block) | Weighted Boots (4): Dive brace guard cost -8 %. | **Pressure Brace** (16): Pressure builds in the pack: the next harpoon flies faster and passes through one foe. *How:* hold Dive brace for 1 s. | Sea Legs (18): Knockback on you -20 %. | Pressure Brace II (26): For its first 0.3 s the brace blocks from every side. | Ironclad (28): Dive brace blocks from both sides. |

| Tier (level) | Harpoon gun | Changes |
| --- | --- | --- |
| 1 Dock harpoon (1) | today's drawing: wooden stock, gunmetal body, brass reel under the barrel, harpoon in the muzzle | starting look |
| 2 Sheathed harpoon (8) | a copper sheath with three rivets over the barrel; the reel drum 2 px wider; a barbed harpoon head | reel speed +10 % |
| 3 Pressure harpoon (16) | a brass pressure bottle with a round gauge under the barrel; a fin vane on the harpoon | range +8 % |
| 4 Abyssal harpoon (24) | a moonsilver harpoon head with a bioluminescent teal line; a navy lacquered stock; the reel's spokes glow while reeling | Abyss light: a tethered foe shows its weak point while the line holds |

Outfits: Reef suit (story: own quest); Naturalist's suit (village: menagerie tier 1); Deep black (arena: basalt ring, gold).
Accessories: Copper crest fin, head (bond 6); Net bag, back (rare drop: isles); Diver's medal, neck (350 Glint); Lucky shell, trinket (250 Glint, perk: loot bursts land 30 % closer to you).

### Ashe

Ember knight in brass-edged steel plate; ONE sword in the RIGHT hand; ONE barred-visor helm with a crimson crest, carried under the LEFT arm and worn only in Cinderhelm; crimson cape and tabard. Kit (Codex): Ember blade, Ember thrust, Armoured guard, Cinderhelm.

| Branch | Lv 2 to 4 (1 pt) | Technique (2 pts) | Minor (1 pt) | Upgrade (3 pts) | Keystone (4 pts) |
| --- | --- | --- | --- | --- | --- |
| **Blade** (primary) | Swordwork (2): Ember blade recovers 5 % faster. | **Banked Fire** (3): Heat builds in the blade; Ember thrust spends it for extra power. *How:* passive: each Ember blade hit. | Stoked (6): Banked Fire builds one heat on a blocked hit too. | Banked Fire II (12): At full heat the guard costs less. | Inferno (22): At full heat, sweeps burn what they hit. |
| **Plate** (block) | Heavy Pauldron (2): Armoured guard cost -8 %. | **Shoulder Check** (9): She drives the pauldron forward in a short shove. *How:* lower Armoured guard within 0.5 s after it blocks a hit. | Hearthold Drill (11): Guard raises 15 % faster. | Shoulder Check II (20): The check breaks a tank's shield guard. | Bulwark (24): Ember thrust breaks a tank's front guard. |
| **Ember** (secondary, special) | Long Thrust (4): Ember thrust reach +3. | **Ember Wake** (16): The thrust leaves a short burning line on the ground. *How:* passive on Ember thrust. | Kindling (18): Ember thrust cooldown -8 %. | Ember Wake II (26): Cinderhelm's closing finisher also leaves the wake. *(needs C60)* | Dragonheart (28): Cinderhelm's flame crescents fly 15 % further. *(needs C60)* |

| Tier (level) | Sword | Changes |
| --- | --- | --- |
| 1 Knight's sword (1) | today's drawing: steel blade with a fuller, brass cross guard, leather grip, brass pommel | starting look |
| 2 Ember-forged sword (8) | the blade 3 px longer; the fuller shows a dull ember line; the cross guard flared at both ends | thrust reach +4 |
| 3 Wave blade (16) | a gently waved edge (2 px undulation); a dragon-head pommel; a crimson grip wrap | guard cost -10 % |
| 4 Starforged edge (24) | the fuller glows white-gold; the cross guard becomes two crescent horns | Starforged edge: the third sweep in a row throws a small flame crescent |

Outfits: Tournament plate (story: own quest); Blackened plate (village: trophy hall tier 1); Ember guard (900 Glint).
Accessories: Dragon crest, head (rare drop: fire country); Heraldic cape, back (arena: castle courtyard, silver); Mail collar, neck (bond 7); Bell charm, trinket (village: bell tower tier 1, perk: burn on you wears off 20 % sooner).

### Clack

Older broad heavy gunner; rocket launcher on the RIGHT shoulder, a separate pressure chamber under the tube, a two-rocket rack on the front LEFT of the belt, a folding loader frame flat on the back. Kit (Codex): Shoulder rocket, Concussive vent, Blast guard, Siegebreaker.

| Branch | Lv 2 to 4 (1 pt) | Technique (2 pts) | Minor (1 pt) | Upgrade (3 pts) | Keystone (4 pts) |
| --- | --- | --- | --- | --- | --- |
| **Loader** (primary) | Practised Hands (2): Rocket reload 6 % faster. | **Hot Loader** (3): The vent's kick speeds the loading. *How:* Concussive vent during a reload. | Quick Fuse (6): Rockets fly 8 % faster. | Hot Loader II (12): A vent that hits two or more foes completes the reload. | Spare Rack (22): Every fourth rocket needs no reload. |
| **Blast** (secondary, special) | Wide Charge (2): Blast radius +6 %. | **Cluster Nose** (9): The blast scatters three small bomblets that pop a moment later. *How:* passive on Shoulder rocket. | Shrapnel (11): Bomblets +1. | Cluster Nose II (20): Bomblets nudge small foes toward the blast's centre. | Siege Master (24): Siegebreaker salvos spread 15 % tighter. *(needs C60)* |
| **Shield** (block) | Thick Plate (4): Blast guard cost -8 %. | **Planted Shield** (16): He plants the shield: he cannot walk, blocked shots stop draining the guard, and the next rocket's blast is larger. *How:* hold Blast guard for 1 s. | Vent Valve (18): Concussive vent cooldown -10 %. | Planted Shield II (26): The planted shield covers his whole front half. | Foundry Wall (28): A planted shield also blocks for an ally champion behind it in sieges. |

| Tier (level) | Rocket launcher | Changes |
| --- | --- | --- |
| 1 Works launcher (1) | today's drawing: gunmetal tube with orange bands, brass muzzle ring, flared exhaust bell | starting look |
| 2 Plated launcher (8) | riveted heat plates over the tube; the orange bands become 2 px diagonal hazard stripes; the bell 2 px wider | reload -8 % |
| 3 Braked launcher (16) | a brass muzzle brake with four vents; a small periscope sight on the left; a second gauge on the pressure chamber | blast radius +6 % |
| 4 Starnose launcher (24) | a dark station-alloy tube with gold bands; the loaded rocket's nose in the bore is pale starlight | Starnose: a rocket that frees a foe cuts the reload by 20 % |

Outfits: Foundry hand (story: own quest); Dock boss (village: workshop tier 1); Hazard orange (arena: gear floor, gold).
Accessories: Welder's cap, head (250 Glint); Canvas cover, back (rare drop: cogsworth); Red neckerchief, neck (bond 5); Gauge fob, trinket (village: workshop tier 2, perk: the bond meter starts each outing 10 higher).

### Nix

Neon Harbour cyborg; the laser arm is his anatomical LEFT arm in every view (steel-blue casing, cyan lens); the RIGHT arm natural with a black wrist wrap; teal jacket with orange lining. Kit (Codex): Laser arm, Afterimage, Arm shield, Limit Release.

| Branch | Lv 2 to 4 (1 pt) | Technique (2 pts) | Minor (1 pt) | Upgrade (3 pts) | Keystone (4 pts) |
| --- | --- | --- | --- | --- | --- |
| **Laser** (primary) | Heat Spread (2): Laser pulses add 8 % less heat. | **Heat Sink** (3): The arm vents part of its heat. *How:* a perfect dodge. | Fine Focus (6): Pulses fly 8 % faster. | Heat Sink II (12): The vent releases a small shock ring. | Overdrive (22): At over 80 % heat, pulses knock back. |
| **Ghost** (secondary) | Quick Image (2): Afterimage cooldown -8 %. | **Flashbreak** (9): The hologram breaks in a flash that blinds foes beside it. *How:* passive when the Afterimage breaks. | Loud Ghost (11): The hologram draws foes from 20 % further. | Flashbreak II (20): The flash also shows elites' weak points for 3 s. | Double Exposure (24): Breaking a hologram cools the arm by 20 %. |
| **Shield** (block, special) | Capacitor (4): Arm shield cost -8 %. | **Redline** (16): Pulses chain to one nearby foe. *How:* passive above 80 % heat. | Grounded (18): Shock on you wears off 20 % sooner. | Redline II (26): Blocking with the arm shield above 80 % heat turns part of the blocked damage into cooling. | Limitless (28): Limit Release's beams pierce one more foe. *(needs C60)* |

| Tier (level) | Laser arm | Changes |
| --- | --- | --- |
| 1 Courier arm (1) | today's drawing: steel-blue casing from the pauldron to a heavy forearm emitter with a cyan lens | starting look |
| 2 Finned arm (8) | three heat fins (2 px) along the forearm; an orange ring round the lens | cooling +10 % |
| 3 Focus arm (16) | the lens pushed 2 px forward in a short barrel; cyan circuit traces along the casing | afterimage cooldown -8 % |
| 4 Pearl arm (24) | pearl-white casing with gold seams; a pale violet-white lens | Pearl core: the heat lockout ends 20 % sooner |

Outfits: Night shift (story: own quest); Runner's kit (village: lookout tier 1); Chrome (arena: neon rooftop, gold).
Accessories: Visor band, head (rare drop: neon); Jacket hood, back (400 Glint); Earpiece cable, neck (bond 7); Glitched keychain, trinket (300 Glint, perk: the map marks company crates within 6 tiles).

### Rook

Orbital salvager in a cream pressure suit; one pulse carbine (right hand on the grip, left on the fore-end); ONE helmet at the RIGHT hip, worn only in Orbital Rig; twin-thruster pack with two nozzles. Kit (Codex): Pulse carbine, Thruster Vault, Energy guard, Orbital Rig.

| Branch | Lv 2 to 4 (1 pt) | Technique (2 pts) | Minor (1 pt) | Upgrade (3 pts) | Keystone (4 pts) |
| --- | --- | --- | --- | --- | --- |
| **Thrusters** (secondary) | Trimmed Jets (2): Vault cooldown -8 %. | **Air Shot** (3): Bolts fired from the air are charged. *How:* carbine bolts fired while airborne in a vault. | Long Hop (6): Vault distance +10 %. | Air Shot II (12): Landing from a vault puffs a dust ring that knocks swarmers back. | Double Jet (22): Two vaults can be chained before the cooldown. *(needs C60)* |
| **Carbine** (primary, block) | Hot Coils (2): Carbine recovers 5 % faster. | **Thruster Flare** (9): The take-off leaves a short flame at its start that burns foes in it. *How:* passive on Thruster Vault. | Shield Cells (11): Energy guard cost -8 %. | Thruster Flare II (20): The vault recharges faster. | Salvager (24): Freed machines drop a little more scrap. |
| **Rig** (special) | Quick Deploy (4): Turrets fire their first pulse sooner. | **Scrap Shell** (16): The guard banks a shell; the next vault lands with a burst round him. *How:* block three hits with Energy guard. | Spotter (18): Designation lasts 0.5 s longer. | Scrap Shell II (26): Orbital Rig's turrets start on the nearest foe he has designated. *(needs C60)* | Overwatch (28): Turrets may stay a little further from you. *(needs C60)* |

| Tier (level) | Pulse carbine | Changes |
| --- | --- | --- |
| 1 Salvage carbine (1) | today's drawing: the pulse carbine with its fore-end | starting look |
| 2 Shrouded carbine (8) | an extended barrel shroud with an orange stripe; a stock pad | bolt speed +8 % |
| 3 Scoped carbine (16) | a top-mounted salvaged scope with an orange lens; a cooling coil on the side | vault cooldown -8 % |
| 4 Lander carbine (24) | a moonsilver emitter crown and a gold crescent on the stock; the bolts turn pale gold | Lander gold: bolts fired from the air pierce one foe |

Outfits: EVA orange (story: own quest); Station crew (village: station tier 4); Salvage rust (rare drop: halcyon).
Accessories: Antenna and stripe, head (arena: zero g dome, silver); Tank paint, back (450 Glint); Dog tags, neck (bond 8); Salvage tag, trinket (rare drop: halcyon, perk: salvage gives 1 more scrap per item).

### Mote

Genderless observatory keeper; long navy coat edged in gold with glass-inlaid hem fragments; two gold crescent hooks at the shoulders; the chest core (gold ring, blue lens); glass shards form in the RIGHT hand. Kit (Codex): Glass volley, Gravity anchor, Glass crescent, Aphelion.

| Branch | Lv 2 to 4 (1 pt) | Technique (2 pts) | Minor (1 pt) | Upgrade (3 pts) | Keystone (4 pts) |
| --- | --- | --- | --- | --- | --- |
| **Glass** (primary) | Fine Glass (2): Shards fly 6 % faster. | **Refraction** (3): The shard splits in two. *How:* passive: a shard that passes through a gravity anchor. | Clear Sight (6): Glass volley recovers 5 % faster. | Refraction II (12): Split shards slow what they hit. | Prism (22): Split shards split once more. |
| **Gravity** (secondary) | Heavy Point (2): Gravity anchor radius +8 %. | **Pane Step** (9): One glass pane stays standing where Mote rolled and stops one projectile. *How:* a perfect dodge. | Tidal Pull (11): Anchor pull +10 %. | Pane Step II (20): A pane that blocks shatters into a small volley. | Event Horizon (24): The anchor holds foes 0.3 s longer. |
| **Orbit** (block, special) | Bright Panes (4): Glass crescent cost -8 %. | **Starfall** (16): A small rain of light falls on the anchor a moment later. *How:* a gravity anchor that draws in three or more foes. | Night Sky (18): Starfall's rain falls 0.1 s sooner. | Starfall II (26): The rain covers a quarter more ground. | Aphelion Bloom (28): Aphelion's orbit gains one more shard. *(needs C60)* |

| Tier (level) | Core and glass | Changes |
| --- | --- | --- |
| 1 Observatory core (1) | today's drawing: gold ring round a blue glass lens with an amber light; clear blue shards | starting look |
| 2 Dropped hooks (8) | the crescent hooks gain hanging glass drops (2 px); the shards gain a faceted light edge | shard speed +8 % |
| 3 Orrery core (16) | a thin gold orrery ring (1 px) tilted round the core; violet-tinted shards | anchor radius +8 % |
| 4 Little moon (24) | the lens becomes a tiny full moon (starlight disc with two craters); the hooks tipped with stars | Little moon: volley shards converge 15 % sooner |

Outfits: Dawn coat (story: own quest); Star chart (village: glassworks tier 2); Eclipse (1,000 Glint).
Accessories: Orbit circlet, head (arena: zero g dome, gold); Star stole, back (bond 9); Collar gem, neck (rare drop: lumen); Pocket orrery, trinket (story: lumen grove, perk: a soft hum when a secret is within 4 tiles).

<!-- end per-character -->

## 6. Art pipeline: building looks without multiplying hand work

**In the castwork rig.**

1. **A look is a parameter, never a drawing.** Each folk module takes `look` and `tier` in its pose (`P0(look=..., tier=...)`), alongside the gear states it already has (`briar`, `storm`, `helm_t`). `build(f, facing, P)` reads them, so the same pose renders every facing and every clip. One look costs one module change and an export, not 1,700 drawings.
2. **Colour is a ramp swap per part.** An outfit maps a part's material to another ramp (`mantle -> russet`) at the `f.add(..., mat)` call. New ramps go into `palette.py` with four tones (deep, shadow, base, light, optional shine), violet-leaning shadows and warm lights; the outline still derives from the deep tone. Starfall's shared ramps (`starlight`, `moonsilver`, `moonwood`) are proposed in `catalogue.json`.
3. **Shape is a part variant in body space.** A hood, a longer cloak, barbs on a spear or a muzzle brake is a new mask placed in body space (`fwd, up, lat`) through `parts.Rig`, shaded from its own silhouette (`rl`, `rs`, `vgrad`) and casting its shadow (`cast=`), so it has the same 3D read as the body in all 8 facings. No flat decals; small marks are parts (a flat tone, `line=None`), so nearer parts still cover them (NOTES.md: details ignore depth).
4. **Equipment checks cover every look.** Each accessory gets a tag (`hat`, `cloak`, `trinket`) and an `EQUIP` rule. `checks.py` runs per look and tier across every clip and facing: every base `EQUIP` item keeps its 4 visible pixels (a cloak may not hide the quiver), the colour budget (64 a frame), palette, hard alpha, lone pixels, the ground rule, and the cell border (tier 4 Bramble is 46 px tip to tip and must stay inside 160 x 144).
5. **Anchors stay put.** A tier keeps grip and release anchors within 1 px. Where it moves one (a longer barrel), the exporter writes `tiers.<n>.anchors` overrides, and the runtime emits from that tier's anchor.
6. **Glows are finite and respect reduced motion**: a tone change on a part, a 2-drawing pulse on hit, a trail of 2 drawings. Nothing loops forever.

**Export: layers, not combinations.** Baking every combination is impossible. The imported cast is about 26 MB for four facings today (`docs/godot.md`); 8 facings, four outfits times four tiers times accessories would multiply that many times over. Instead the exporter writes:

- one **body sheet per outfit** (home plus 3), with the signature weapon left out;
- one **weapon layer per tier**, split per frame into a part behind the body and a part in front (the exporter knows each part's `z`);
- one **layer per accessory**, split the same way;
- **occlusion baked against the body**: each layer pixel a nearer body part covers is cut out per frame and per outfit, and identical frames are stored once (the manifest's `sha256`).

**In the Godot runtime** (for Codex and Claude A; not built here).

- `CastSprite` plays the body sheet for the folk's outfit and draws the weapon and accessory layers as child sprites on the same clip, frame index and facing, behind or in front of the body. The runner and `player.gd` (C60's grant) need no change for looks; tier anchors come from the manifest.
- **Save fields** (proposed for the save owner): `progression.level` and `progression.xp`; `folk.<id>.weapon_tier` and `folk.<id>.fittings` (the fitting in each socket); `folk.<id>.look` = {outfit, head, back, neck, trinket}; `wardrobe` = {folk: [item ids]}; `drop_counters` = {region: count}; `folk.<id>.nodes` (the nodes taken; unspent points are the level minus one, minus the points spent); `seen` for the "new" marks. A save version step migrates the old hats as accessories (game-design 14.1).
- **Unlock events:** the existing quest, restore and flag events plus `arena:*`, `bond:*`, `drop:*` and `buy:*` go to one `Progression` node, which checks `catalogue.json` and each folk's file, writes the wardrobe, and raises `points:<folk>:<n>`, `node:<folk>:<id>`, `tier:<folk>:<n>` and `cosmetic:<folk>:<item>` for the HUD's one-line toast.

## 7. Conflicts and dependencies (raised on #149)

1. **What the runner must support**: per-folk skill points and node prerequisites (level and the previous node), nodes as modifiers over the canonical kit (a percentage or a count on a named field), and technique hooks (after action X within t, while guard is held for t, on guard release after a block, on a perfect dodge, passive on hit or on projectile). All of it reads `game/data/progression/<id>.json`; the kit files are not edited.
2. **Nodes that change a count or rule inside the powered form** wait for C60 and are marked *(needs C60)*: three technique upgrades (Pendle's Dead Eye II, Ashe's Ember Wake II, Rook's Scrap Shell II) and a few keystones and minors (for example Iona's Gale Rider, Brine's Leviathan, Nix's Limitless, Mote's Aphelion Bloom). The JSON flags each with `touches_canonical`.
3. **game-design changes.** "Any folk can equip any weapon" (4.3 and 5) gives way to signature weapons with fittings (Matt, 25 Oct). The perk card (6) gives way to the skill tree. 4.3's specials (Puffcap, Puddle, Tally, Tuff and Bunk among them) predate Codex's fourteen; some of their ideas return as techniques (Bramble's Steady Aim, Velvet's Dim, Cairn's Bedrock, Ashe's Banked Fire, Mirra's Seep, Mote's Starfall). Claude A updates game-design.md to match.
4. **Homes and materials** follow Claude K's proposal on #149, which Matt has not decided. Only the tier material depends on it.

## 8. For Matt

Decided on 25 Oct: signature weapons with fittings; a skill tree on level points with weapon tiers at set levels; cheap forging per folk with late joiners at the highest open tier; perks only on trinkets. Still open, each with a recommendation in bold:

1. **Respec.** **At the hut bed for 50 Glint, the first one free.** Or free at any time outside a fight.
2. **The tree's budget.** **29 points against a 33-point tree, so a finished folk leaves out one keystone.** Or enough points to fill the whole tree by level 30.
3. **Where to change looks.** **At the bed in your hut, with a wardrobe screen that previews every facing.** Or anywhere outside a fight.
