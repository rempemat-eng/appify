# Character progression: weapon lines, skill trees, outfits and accessories (25 and 26 Oct)

Matt, 25 Oct: "can you create new outfits/ accessories for the characters that they unlock some way and if i upgrade/ level up a character their weapons should become cooler as well/ they should learn new abilities". His decisions on the first draft, the same day: a "skill tree that you spend level points on and then a new weapons unlocked at specific levels. money can be spent on cosmetics and other things in the map"; one signature weapon per folk with loot as fittings set into it; each folk pays the forge cheaply, and a late joiner arrives at the highest open tier; only trinkets carry small perks, never damage.

Matt, 26 Oct: "some ideas for weapon upgrades could be a crossbow for bramble and then maybe an automatic one later or one that shoots 3 projectiles or different kinds of projectiles (these could also be separate skill tree upgrades with the bow turning into a crossbow as the level upgrade and different projectiles as part of the skill tree). similarly for the revolver guy (first normal revolver then maybe two revolvers or a cooler more powerful one and then different ammo ...)". So the level tiers are now **real transformations** of each weapon, and the tree holds the variations: **kinds** (bolt heads, rounds, reagents, lights) and **forms** (multi-shot, spreads, twin barrels). How each folk fits the world is in [world-and-cast.md](world-and-cast.md).

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

**Each folk's tree has three branches, always in the same roles**, with five nodes a branch, fifteen in all:

1. **Kinds** (branch 1): what the weapon fires or carries. Bramble's bolt heads (barbed, fire, shard, net), Pendle's rounds (hot, silver, lodestone, sun slugs), Morel's reagents, Velvet's lantern lights, Tam's stances. **One kind is loaded at a time**, chosen at a waystone, the hut or the tree screen, never in a fight, so there is no new button. The base kind is free.
2. **Form** (branch 2): how the weapon fires. Bramble's twin shot, then a three-bolt spread; Pendle's ricochets and a two-gun fan; Tam's twin and triple ridges; Morel's flask pairs and clusters.
3. **Craft** (branch 3): the rest of the kit (guard, secondary, special), holding the techniques of 25 Oct that fit there.

| Slot | Cost | Unlocks at (branch 1 / 2 / 3) | Usually |
| --- | --- | --- | --- |
| 1 | 1 | level 2 / 2 / 4 | the first kind, or a small passive |
| 2 | 2 | 3 / 9 / 16 | a second kind, or a technique |
| 3 | 1 | 6 / 11 / 18 | a small passive |
| 4 | 3 | 12 / 20 / 26 | a third kind, or the technique's upgrade |
| 5 | 4 | 22 / 24 / 28 | the keystone |

- **It cannot be rushed.** Each node needs its level and the node before it in its branch.
- **The build choice.** The whole tree costs 33 points and a folk has 29 at level 30, so a finished folk has everything except one keystone. On the way, the order you take nodes in is the choice (at level 12 you can afford about half the open nodes).
- **Points are per folk, the level is shared.** A late joiner arrives at the shared level with all its points to spend, and a "choose for me" button that follows the first branch (game-design 6: nothing is levelled twice).
- **Respec (proposal).** At your bed in the hut, for 50 Glint (the first one free), every point comes back. Never in a fight, siege or dungeon.
- **No new buttons.** Each technique binds to an existing input (primary, secondary, block, special, dodge), a short timing window after one ("primary within 0.4 s after the sweep"), a held guard, or a passive condition. None uses a hold on primary, because Codex's primary repeats while held.
- **Art cost in the tree.** Kinds and forms are effects: a bolt head's colour, a second projectile, a ridge's extra lane. They need effect sprites, not body clips. A few techniques need one new clip each: Velvet's waltz lunge, Mirra's curtain wave and Ashe's shoulder check. Rook's air shot needs the airborne primary that #257 already lists as missing.
- **Several techniques use the dodge and the perfect dodge** (game-design 4.2; Codex's kits have no dodge of their own). If the dodge changes, those bindings change with it.

## 3. Weapon lines and fittings

Each folk keeps one **signature weapon line**, and **its tiers are level milestones**: a tier opens at level 8, 16 or 24, and Hale forges it cheaply, per folk. Each tier is a real step, not a reskin: Bramble's bow becomes a crossbow at level 8 and a repeating crossbow at 16; Pendle's revolver becomes a heavy Sunhammer, then twin Sunhammers. The full table for all fourteen is in section 5 and in [world-and-cast.md](world-and-cast.md).

- **One form change per folk** needs new clip tables (Bramble's crossbow, Pendle's twin guns, Iona's glaive, Morel's mortar, Velvet's beam lantern, Brine's cannon, Clack's twin tubes). The other tiers are new or swapped rig parts on the existing clips. Each tier's `rig` field says which.
- **The kit keeps its four actions, roles and inputs.** A form change alters the primary's projectile or hit numbers through the modifier layer, never the kit files (raised on #149). The damage per second of each step is held level by gear level, so a new form is a new feel, not a power spike.

| Tier | Name | Opens at | Sockets | Hale forges it for (placeholders) |
| --- | --- | --- | --- | --- |
| 1 | Made | level 1 | 1 | the starting look |
| 2 | Fitted | level 8, once the forge is restored | 2 | 60 Glint, 5 scrap, 2 of the folk's home material |
| 3 | Masterwork | level 16 | 2 | 150 Glint, 10 scrap, 4 home material |
| 4 | Starfall | level 24, at the great forge | 3 | 300 Glint, 20 scrap, 6 home material, 1 starshard |

- **Loot is fittings.** Weapon drops are fittings with game-design's rarity and affixes (5.3 and 5.4): a Fine fitting carries one affix, a Heroic three. Hale sets them into the signature weapon's sockets, and moves them between folk for a small Glint fee. Gear level and its forge upgrade (5.6) apply to the signature weapon. A fitting is a small visible part where it sits (a gem, a band, a scope).
- **What a tier changes.** The weapon's form and drawing (each tier is described for an artist in the folk's JSON and below), one more socket at tiers 2 and 4, and its handling (fire rate, capacity, reach, projectiles per shot). Tier 4, Starfall, keeps tier 3's form and adds one named effect, such as Pendle's last round being a critical hit. Power stays with gear level.
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

Older grassland ranger; left-handed archer: bow in the RIGHT hand, quiver over the LEFT shoulder, billhook at the RIGHT hip, folding buckler on the RIGHT forearm. Kit (Codex): Quickdraw, Billhook, Briar buckler, Briarshot. Loadout kind: bolt or arrow head.

| Level | Weapon | What it is | Rig | Changes (placeholders) |
| --- | --- | --- | --- | --- |
| 1 | **Yew bow** | the tier-1 drawing: a shallow recurve held in the right hand, quiver over the left shoulder | as drawn | starting weapon |
| 8 | **Hedge crossbow** | a short ash-wood crossbow with a steel prod (bow arms) as wide as the shoulders, a walnut stock to the shoulder and a goat's-foot lever on the right side; bolts in the same quiver; slung across the back when the billhook is out | new clips | slower, harder-hitting bolts; damage per second held equal by gear level |
| 16 | **Repeating crossbow** | the crossbow gains a box magazine of 6 bolts on top of the stock and a cocking lever along the right side; the prod +2 px each end over tier 2 | parts | magazine 6, fire interval -30 %, reload seconds 1.2 |
| 24 | **Starfall repeater** | moonwood stock and prod with crescent tips; the string drawn in starlight; the loaded bolt's head glows | parts | Starlit: the loaded kind's effect is 25 % stronger |

| Branch | 1 pt | 2 pts | 1 pt | 3 pts | Keystone, 4 pts |
| --- | --- | --- | --- | --- | --- |
| **Bolts** | Barbed heads (2): Loads barbed bolts: they slow what they hit. | Fire heads (3): Loads fire bolts: they set burn. | Fletcher (6): The loaded kind's effect lasts 20 % longer. | Shard heads (12): Loads shard bolts: they pierce one more foe and show a weak point. | Net heads (22): Loads net bolts: they root a light foe; a tank is slowed instead. |
| **Volley** | Steady hands (2): Shots recover 6 % faster. | Twin shot (9): Every third shot looses two bolts side by side. | Long eye (11): Bolts fly 8 % further. | Three-bolt spread (20): Twin shot becomes three bolts in a narrow fan. | Briar volley (24): Briarshot's powered shots are three-bolt spreads. *(needs C60)* |
| **Woodcraft** | Keen hook (4): Billhook cooldown -8 %. | Briar snare (16): Lowering the buckler just after a block drops a snare that roots the next foe on it. | Bracer hide (18): Buckler guard cost -8 %. | Briar snare II (26): Two snares at once. | Hook and loose (28): A shot right after the billhook sweep fires point-blank with knockback. |

Outfits: Autumn forester (story: own quest); Sheepskin mantle (village: fold and loom tier 1); Ranger's pine (450 Glint).
Accessories: Feathered cap, head (rare drop: valley); Patched travelling cloak, back (arena: training yard, silver); Oak-leaf scarf, neck (bond 3); Acorn whistle, trinket (250 Glint, perk: pickup magnet radius +15 %).

### Iona

Grassland storm-lancer; one long spear in the RIGHT hand, the LEFT grips the same shaft for two-handed actions; long braid down the back, magenta scarf. Kit (Codex): Spearpoint, Wind lunge, Gust guard, Storm Mantle. Loadout kind: storm.

| Level | Weapon | What it is | Rig | Changes (placeholders) |
| --- | --- | --- | --- | --- |
| 1 | **Ash spear** | the tier-1 drawing: steel leaf blade, gold collar, gold-banded brass shaft, butt spike | as drawn | starting weapon |
| 8 | **Winged spear** | two swept wings (+4 px each) below the blade that hook a foe; a magenta pennon at the collar | parts | lunge pull 8 |
| 16 | **Storm glaive** | the leaf blade becomes a long single-edged glaive head (+6 px) with a copper storm vane on its back; the thrust ends in a short cutting turn | new clips | primary arc degrees 40 |
| 24 | **Starfall lance** | a moonsilver glaive head with a storm-blue fuller; a gold crescent collar; a ribbon of light | parts | Stormlit: the first hit after a lunge arcs to one more foe |

| Branch | 1 pt | 2 pts | 1 pt | 3 pts | Keystone, 4 pts |
| --- | --- | --- | --- | --- | --- |
| **Storm** | Static (2): Loads static: hits charge foes; every third hit sparks. | Gale (3): Loads gale: hits push foes a step. | Weather eye (6): The loaded storm's effect lasts 20 % longer. | Rain (12): Loads rain: hits soak foes, so shock hurts them more. | Thunderhead (22): Storm Mantle's arcs reach one tile further. *(needs C60)* |
| **Lance** | Long haft (2): Spearpoint reach +3. | Gale step (9): Primary right after a dodge is a long thrust. | Windborne (11): Wind lunge cooldown -8 %. | Gale step II (20): A Gale step that hits gives back half a dodge. | Gale rider (24): Two Wind lunges can be chained. *(needs C60)* |
| **Gust** | Steady feet (4): Gust guard drain -10 %. | Windbreak (16): A guard raised just as a shot arrives turns it back. | Crosswind (18): Shots slow near your raised guard. | Windbreak II (26): Turned-back shots carry a storm arc. | Eye of the storm (28): While guarding, foes in melee are pushed back once a second. |

Outfits: Moor coat (story: own quest); Yard drill coat (village: training yard tier 2); Tempest (600 Glint).
Accessories: Kestrel hairpin, head (bond 4); Shoulder cloak, back (arena: training yard, gold); Moor tartan scarf, neck (rare drop: brackens); Weathervane charm, trinket (300 Glint, perk: the familiar's weak-point glint lasts 0.5 s longer).

### Pendle

Sunstone robot gunslinger; one revolver on the RIGHT hip, one marksman rifle slung across the back (stock at the right hip, barrel past the LEFT shoulder); cattleman hat; no clock motif. Kit (Codex): Revolver, Fan fire, Steel plate, Longshot. Loadout kind: round.

| Level | Weapon | What it is | Rig | Changes (placeholders) |
| --- | --- | --- | --- | --- |
| 1 | **Trail revolver** | the tier-1 drawing: one gunmetal revolver on the right hip, walnut grip; the marksman rifle slung across the back | as drawn | starting weapon |
| 8 | **Sunhammer** | a heavier long-barrel revolver: barrel +4 px over tier 1, a fluted cylinder, a brass hammer spur and ivory grips | parts | five heavier rounds instead of six |
| 16 | **Twin Sunhammers** | a second Sunhammer in a cross-draw holster on the left hip; both drawn for primary and fan fire | new clips | capacity per gun 5, alternate hands, fire interval -25 % |
| 24 | **Six Suns** | both cylinders turn to sunstone glass lit from inside, one glint per loaded round; gold muzzle crowns; the rifle gains a gold crescent sight | parts | Six Suns: the last round in each gun is a critical hit |

| Branch | 1 pt | 2 pts | 1 pt | 3 pts | Keystone, 4 pts |
| --- | --- | --- | --- | --- | --- |
| **Rounds** | Hot-loaded (2): Loads hot rounds: they set burn. | Silver (3): Loads silver rounds: they pierce one foe. | Hand-loaded (6): Reload 8 % faster. | Lodestone (12): Loads lodestone rounds: they shock and chain to one foe. | Sun slugs (22): Loads sun slugs: a heavy round that staggers but reloads after every two. |
| **Gunslinger** | Smooth action (2): Revolver recovers 5 % faster. | Ricochet (9): Fan fire rounds bounce once off high cover. | Quick hands (11): A perfect dodge loads two rounds. | Ricochet II (20): A bounced round turns toward the nearest foe. | Showdown (24): With twin guns, fan fire empties both in one wide fan. |
| **Marksman** | Plate fold (4): Steel plate raises 15 % faster. | Dead eye (16): Holding still for 0.6 s in Longshot shows the foe's weak point. | Steady stock (18): Longshot shots knock tanks back slightly. | Dead eye II (26): A weak-point hit in Longshot gives back 1 s of the form. *(needs C60)* | Bullseye (28): Longshot weak-point hits stagger elites. |

Outfits: Gulch duster (story: own quest); Oasis whites (village: water tower tier 1); Midnight rider (arena: dusty corral, gold).
Accessories: Flat-brim hat, head (rare drop: sunstone); Serape, back (500 Glint); Star bandana, neck (bond 5); Lucky silver dollar, trinket (village: stall tier 2, perk: the first reload of each fight is 15 % faster).

### Cairn

Moss-covered granite golem from the woodland circle, about 90 px; great round fists, a sprout on the LEFT shoulder, two floating pebbles over the RIGHT shoulder. Kit (Codex): Stone fist, Boulder, Crossed arms, Old Growth. Loadout kind: stone.

| Level | Weapon | What it is | Rig | Changes (placeholders) |
| --- | --- | --- | --- | --- |
| 1 | **Bare stone** | the tier-1 drawing: round granite fists | as drawn | starting weapon |
| 8 | **Banded fists** | two iron bands round each fist, raised 2 px | parts | guard cost -8 % |
| 16 | **Boulder gauntlets** | the fists grow into rough boulder gauntlets, +4 px round, with roots binding them to the forearms and moss on the knuckles | parts | primary reach 4, knockback +20 % |
| 24 | **Moonvein gauntlets** | white-gold moonstone veins in the gauntlets' cracks; a crescent shard in each | parts | Moonvein: Stone fist staggers swarmers |

| Branch | 1 pt | 2 pts | 1 pt | 3 pts | Keystone, 4 pts |
| --- | --- | --- | --- | --- | --- |
| **Stones** | River stone (2): Throws river stones: they bounce once. | Mossball (3): Throws mossballs: they root where they burst. | Strong arm (6): Thrown stones fly 8 % faster. | Flint (12): Throws flint: it sparks and sets burn. | Landslide (22): Any stone that hits a wall breaks into three. |
| **Fists** | Moss fists (2): Stone fist recovers 5 % faster. | Stonebreak (9): Fists and boulders crack a tank's front armour. | Deep roots (11): Old Growth shockwave +10 % radius. *(needs C60)* | Stonebreak II (20): Every hit slows the foe's next wind-up. | Rockslide (24): Every third punch in a row sends a short shockwave. |
| **Bedrock** | Settled (4): Guard recovers 10 % faster. | Bedrock (16): Every few seconds the guard takes a whole hit free. | Pebble ward (18): The two pebbles each catch one shot. | Bedrock II (26): A Bedrock block shoves the attacker back. | Standing stone (28): While guarding he cannot be knocked back. |

Outfits: Spring bloom (village: greenhouse tier 1); Circle runes (story: own quest); Basalt (arena: basalt ring, silver).
Accessories: Daisy crown, head (bond 2); Wren's nest, back (rare drop: valley); Festival ribbon, neck (200 Glint); Smooth river stone, trinket (rare drop: lull, perk: tonics are drunk 15 % faster).

### Morel

Older grassland alchemist; one blue flask in the RIGHT hand, a closed reagent case on the RIGHT hip, the catalyst apparatus at the LEFT hip, one mask on the chest (on the face in the special). Kit (Codex): Reagent flask, Catalyst, Mineral ward, Catalyst mask. Loadout kind: reagent.

| Level | Weapon | What it is | Rig | Changes (placeholders) |
| --- | --- | --- | --- | --- |
| 1 | **Field kit** | the tier-1 drawing: one blue flask in the right hand, the case on the right hip, the catalyst at the left hip | as drawn | starting weapon |
| 8 | **Bandolier** | a leather bandolier of six flasks across the chest (left shoulder to right hip); the catalyst gains a second coil | parts | fire interval -15 % |
| 16 | **Flask mortar** | a short brass mortar on a shoulder strap, the length of a forearm, with a flask seated in its cup; it lobs flasks in a high arc | new clips | range +40 %, lob |
| 24 | **Starglass mortar** | starglass flasks with a floating mote; the mortar's mouth ringed in gold; gold rims on the mask lenses | parts | Starglass: a foe in a patch shows its weak point when Catalyst sparks through it |

| Branch | 1 pt | 2 pts | 1 pt | 3 pts | Keystone, 4 pts |
| --- | --- | --- | --- | --- | --- |
| **Reagents** | Glue (2): Loads glue: patches slow. | Frost salt (3): Loads frost salt: patches chill. | Long brew (6): Patches last 15 % longer. | Quicklime (12): Loads quicklime: patches burn. | Drowsy fume (22): Loads fume: patches make foes attack half as often. |
| **Volley** | Good arm (2): Flask range +8 %. | Pair (9): Every third throw is two flasks. | Spark gap (11): Catalyst cooldown -8 %. | Cluster (20): The pair becomes three flasks in a triangle. | Grand reaction (24): Catalyst mask's chains jump one extra patch. *(needs C60)* |
| **Remedies** | Mineral lining (4): Mineral ward guard cost -8 %. | Mineral skin (16): A flask at your own feet softens the next hit. | Field medic (18): A light hit no longer interrupts a tonic. | Mineral skin II (26): The skin also clears burn, chill and shock. | Antidote (28): Burn, chill and shock on you wear off 25 % sooner. |

Outfits: Herbalist's apron (village: apothecary tier 2); Laboratory coat (story: own quest); Ember smock (rare drop: fire country).
Accessories: Bowler hat, head (300 Glint); Oilcloth cape, back (arena: gear floor, silver); Spectacles on a chain, neck (bond 4); Pocket mortar, trinket (story: apothecary first tonic, perk: tonics heal 5 % more).

### Velvet

Coastal duellist from Driftwood; one sabre in the LEFT hand (closed brass knuckle-bow), its empty scabbard on the RIGHT hip, one black lantern by its bail in the RIGHT hand. Kit (Codex): Sabre, Lantern flare, Sabre parry, Black Lantern. Loadout kind: lantern light.

| Level | Weapon | What it is | Rig | Changes (placeholders) |
| --- | --- | --- | --- | --- |
| 1 | **Naval sabre** | the tier-1 drawing: sabre in the left hand, black lantern by its bail in the right | as drawn | starting weapon |
| 8 | **Cutlass** | a broader, shorter cutlass (+2 px wide at the tip, -2 px long) with a closed brass bowl guard | parts | arc degrees 15, reach -2 |
| 16 | **Moth sabre and dark lens** | a long slender sabre (+4 px over tier 1) with a moth-wing shell guard; the lantern gains a shuttered bull's-eye lens on its front, so the flare becomes a beam | new clips | reach 4, flare shape cone |
| 24 | **Moonlit sabre** | a moonsilver blade with a pale edge light; the lantern cage gold, its light pale blue-white | parts | Moonlit: a perfect parry flashes the lantern and exposes foes near you |

| Branch | 1 pt | 2 pts | 1 pt | 3 pts | Keystone, 4 pts |
| --- | --- | --- | --- | --- | --- |
| **Lights** | White light (2): Loads white: the flare exposes foes longer. | Amber light (3): Loads amber: the flare sets burn. | Trimmed wick (6): Flare cooldown -8 %. | Moth dust (12): Loads moth dust: dazzled foes wander for a moment. | Lighthouse (22): The flare reaches 30 % further. |
| **Blade** | Light wrist (2): Sabre recovers 5 % faster. | Moth's waltz (9): The third cut in a row is a stepping lunge-cut. | Duellist (11): Parry raises 15 % faster. | Moth's waltz II (20): The lunge leaves an echo that cuts again. | Black waltz (24): Black Lantern's echoes cut once as they fade. *(needs C60)* |
| **Shadow** | Light step (4): Walk speed +4 %. | Riposte (16): A parry at the last moment makes the next cut faster. | Dim (18): After a flare, shooters lose track of you for a moment. | Riposte II (26): The riposte cut exposes the foe. | En garde (28): After a parry, the next hit you take is 20 % lighter. |

Outfits: Harbour blue (story: own quest); Keeper's oilskin (village: bell tower tier 2); Masquerade (arena: harbour jetty, gold).
Accessories: Tricorn, head (rare drop: valley); Boat cloak, back (550 Glint); Lace jabot, neck (bond 6); Moth brooch, trinket (arena: harbour jetty, bronze, perk: your defeat cache shows from twice as far).

### Tam

Mature Frostline warrior monk, bald, in saffron and ochre robes (the castwork redesign); cool grey-blue wraps on both forearms, palms and shins; one mala round the neck; no weapon, the wraps are his. Kit (Codex): Frost palms, Ice ridge, Ice guard, Glacier Form. Loadout kind: stance.

| Level | Weapon | What it is | Rig | Changes (placeholders) |
| --- | --- | --- | --- | --- |
| 1 | **Plain wraps** | the tier-1 drawing: grey-blue wraps on forearms, palms and shins | as drawn | starting weapon |
| 8 | **Iron wraps** | dark iron rings sewn into the wraps at wrist and shin; a heavier mala | parts | knockback +15 % |
| 16 | **Frost gauntlets** | ice grows into fitted gauntlets over both hands with three short ice ridges on the knuckles (+2 px proud); shin guards of ice | parts | every palm adds frost in the base form |
| 24 | **Moonbead gauntlets** | the ice clears to starglass lit from inside; the guru bead a small glowing moon | parts | Moonbead: a frost shatter chills foes beside the target |

| Branch | 1 pt | 2 pts | 1 pt | 3 pts | Keystone, 4 pts |
| --- | --- | --- | --- | --- | --- |
| **Stances** | Crane (2): Takes crane stance: palms reach 3 further. | Ox (3): Takes ox stance: palms stagger light foes. | Breath (6): Changing stance at a waystone is free and instant. | Glacier (12): Takes glacier stance: every palm adds frost. | Hundred palms (22): Every fifth palm in a row strikes twice. |
| **Ridge** | Long ridge (2): Ice ridge travels 10 % further. | Twin ridge (9): Ice ridge splits into two lanes. | Glacier step (11): Glacier Form's glide +10 % speed. *(needs C60)* | Three ridges (20): Three lanes in a narrow fan. | Ridge wall (24): Each ridge ends in a low ice wall that stops shots for 2 s. |
| **Stillness** | Calm guard (4): Ice guard drain -10 %. | Cold breath (16): Holding guard 1 s makes the next palm add two frost. | Still water (18): A perfect dodge leaves a frost patch that slows. | Cold breath II (26): The steadied palm also slows. | Unmoved (28): Holding guard 2 s makes the next block cost nothing. |

Outfits: Snow robes (village: training yard tier 1); Pilgrim (story: own quest); Temple gold (700 Glint).
Accessories: Straw rain hat, head (arena: castle courtyard, gold); Straw rain cape, back (rare drop: frostline); Winter mala, neck (bond 3); Kettle charm, trinket (300 Glint, perk: your first tonic of each outing refills at the next camp you free).

### Mirra

Oasis water diviner; hands empty and open in every clip (water is a scene effect); ivory headwrap with a turquoise gem above the RIGHT ear; turquoise wrist bands; shawl end over the LEFT shoulder. Kit (Codex): Water bolt, Spring seal, Water curtain, Oasis Unbound. Loadout kind: water.

| Level | Weapon | What it is | Rig | Changes (placeholders) |
| --- | --- | --- | --- | --- |
| 1 | **Turquoise bands** | the tier-1 drawing: turquoise wrist bands with gold studs; the gem above the right ear | as drawn | starting weapon |
| 8 | **Wave bands** | the bands +1 px wider with a gold wave line; a teardrop pendant under the gem | parts | bolt speed +10 % |
| 16 | **Spring orb** | a fist-sized orb of water that floats at her right hand's height and follows it (a scene effect anchored to hand_R, like her seals); the bolts leave the orb | parts | bolts per shot 2, spread degrees 8 |
| 24 | **Starspring orb** | the orb holds a starlit core; the bands turn to clear water-glass | parts | Starspring: seals last 1 s longer |

| Branch | 1 pt | 2 pts | 1 pt | 3 pts | Keystone, 4 pts |
| --- | --- | --- | --- | --- | --- |
| **Waters** | Spring water (2): Loads spring water: seals heal you a little. | Brine (3): Loads brine: bolts soak foes. | Deep well (6): Seals last 10 % longer. | Hot spring (12): Loads hot spring water: bolts scald (burn). | Oasis (22): You may keep one more seal. |
| **Currents** | Swift water (2): Bolts fly 8 % faster. | Undertow (9): A bolt through a seal pulls light foes toward it. | Wide seal (11): Seal radius +8 %. | Fountain (20): Bolts through a seal split into three. | Riverbed (24): Oasis Unbound's currents slow foes they cross. |
| **Curtain** | Flowing guard (4): Curtain guard cost -8 %. | Curtain wave (16): Hold the curtain 0.8 s and release: a wave pushes foes and shots back. | Spray (18): Blocked shots splash and soak the nearest foe. | Curtain wave II (26): The wave leaves a seal where it breaks. | Still pool (28): Standing in a seal clears burn. |

Outfits: Dusk caravan (story: own quest); Garden linen (village: water tower tier 2); Festival red (rare drop: sunstone).
Accessories: Gold head chain, head (400 Glint); Travelling shawl, back (arena: dusty corral, silver); Shell necklace, neck (rare drop: isles); Dowsing pendant, trinket (bond 5, perk: regional seeds drop 10 % more often).

### Brine

Coastal diver in a sealed copper helmet; one harpoon gun (wooden stock, gunmetal body, brass reel on the right side); an olive air pack with ONE hose to the helmet's right rear. Kit (Codex): Harpoon gun, Reel, Dive brace, Abyssal Drive. Loadout kind: harpoon head.

| Level | Weapon | What it is | Rig | Changes (placeholders) |
| --- | --- | --- | --- | --- |
| 1 | **Dock harpoon** | the tier-1 drawing: wooden stock, gunmetal body, brass reel, harpoon in the muzzle | as drawn | starting weapon |
| 8 | **Sheathed harpoon** | a copper barrel sheath with rivets; the reel +2 px; a barbed head | parts | reel speed +15 % |
| 16 | **Pressure cannon** | a short, fat pressure cannon: a brass air bottle under the barrel with a gauge, a flared muzzle (+3 px) and a winch drum twice the tier-1 reel | new clips | projectile speed +30 %, pierce 1, tether heavy |
| 24 | **Abyssal cannon** | a moonsilver head with a teal glow line; navy lacquer; the drum's spokes glow while reeling | parts | Abyss light: a tethered foe shows its weak point |

| Branch | 1 pt | 2 pts | 1 pt | 3 pts | Keystone, 4 pts |
| --- | --- | --- | --- | --- | --- |
| **Heads** | Barbed head (2): Loads barbed heads: tethered foes slow. | Eel head (3): Loads eel heads: the tether shocks every second. | Long line (6): Tether length +10 %. | Buoy head (12): Loads buoy heads: a light foe is lifted and stunned briefly. | Net head (22): Loads net heads: the harpoon bursts into a net that roots. |
| **Winch** | Oiled reel (2): Reel 10 % faster. | Anchor line (9): Reeling to a heavy target ends in a gun-butt strike. | Quick winch (11): Harpoon reload 8 % faster. | Snap line (20): Reeling a light foe into a wall stuns it. | Leviathan (24): Abyssal Drive's shots pierce one more foe. *(needs C60)* |
| **Brace** | Weighted boots (4): Brace guard cost -8 %. | Pressure brace (16): Hold the brace 1 s: the next harpoon is faster and pierces. | Sea legs (18): Knockback on you -20 %. | Pressure brace II (26): For its first 0.3 s the brace blocks from every side. | Ironclad (28): The brace blocks from both sides. |

Outfits: Reef suit (story: own quest); Naturalist's suit (village: menagerie tier 1); Deep black (arena: basalt ring, gold).
Accessories: Copper crest fin, head (bond 6); Net bag, back (rare drop: isles); Diver's medal, neck (350 Glint); Lucky shell, trinket (250 Glint, perk: loot bursts land 30 % closer to you).

### Ashe

Ember knight in brass-edged steel plate; ONE sword in the RIGHT hand; ONE barred-visor helm with a crimson crest, carried under the LEFT arm and worn only in Cinderhelm; crimson cape and tabard. Kit (Codex): Ember blade, Ember thrust, Armoured guard, Cinderhelm. Loadout kind: flame.

| Level | Weapon | What it is | Rig | Changes (placeholders) |
| --- | --- | --- | --- | --- |
| 1 | **Knight's sword** | the tier-1 drawing: steel blade with a fuller, brass cross guard; the helm under the left arm | as drawn | starting weapon |
| 8 | **Ember longsword** | a longer blade (+5 px) with a flared guard and an ember line in the fuller; still one-handed | parts | reach 4 |
| 16 | **Wyrmfang** | a broad blade cut from the freed dragon's shed fang: ivory-white, gently curved, +3 px wider than tier 2, the dragon's scale on the grip; it smoulders at the edge | parts | burn on hit seconds 1 |
| 24 | **Starforged fang** | the fang's edge glows white-gold; the guard becomes two crescent horns | parts | Starforged: the third sweep in a row throws a small flame crescent |

| Branch | 1 pt | 2 pts | 1 pt | 3 pts | Keystone, 4 pts |
| --- | --- | --- | --- | --- | --- |
| **Flames** | Ember (2): Loads ember: hits build heat; Ember thrust spends it. | Smoke (3): Loads smoke: thrusts leave a cloud shooters cannot see through. | Stoked (6): Flame effects last 20 % longer. | White fire (12): Loads white fire: thrusts pierce one foe. | Ember wake (22): Thrusts leave a burning line. |
| **Blade** | Swordwork (2): Blade recovers 5 % faster. | Crescent (9): The third sweep in a row throws a short flame crescent. | Long thrust (11): Ember thrust reach +3. | Twin crescent (20): The crescent becomes two, crossed. | Dragonheart (24): Cinderhelm's crescents fly 15 % further. *(needs C60)* |
| **Plate** | Heavy pauldron (4): Guard cost -8 %. | Shoulder check (16): Lowering the guard just after a block shoves the foe. | Hearthold drill (18): Guard raises 15 % faster. | Shoulder check II (26): The check breaks a tank's guard. | Bulwark (28): Burn on you wears off 30 % sooner. |

Outfits: Tournament plate (story: own quest); Blackened plate (village: trophy hall tier 1); Ember guard (900 Glint).
Accessories: Dragon crest, head (rare drop: fire country); Heraldic cape, back (arena: castle courtyard, silver); Mail collar, neck (bond 7); Bell charm, trinket (village: bell tower tier 1, perk: burn on you wears off 20 % sooner).

### Clack

Older broad heavy gunner; rocket launcher on the RIGHT shoulder, a separate pressure chamber under the tube, a two-rocket rack on the front LEFT of the belt, a folding loader frame flat on the back. Kit (Codex): Shoulder rocket, Concussive vent, Blast guard, Siegebreaker. Loadout kind: rocket.

| Level | Weapon | What it is | Rig | Changes (placeholders) |
| --- | --- | --- | --- | --- |
| 1 | **Works launcher** | the tier-1 drawing: gunmetal tube with orange bands on the right shoulder | as drawn | starting weapon |
| 8 | **Plated launcher** | riveted heat plates, hazard stripes, a bell +2 px wider | parts | reload -10 % |
| 16 | **Twin-tube launcher** | a second tube strapped beside the first (the pair 1.6 times the tier-1 width), one loaded nose in each; the rack holds four | new clips | two shots between reloads |
| 24 | **Starnose launcher** | station-alloy tubes with gold bands; both loaded noses glow in starlight | parts | Starnose: a rocket that frees a foe cuts the reload by 20 % |

| Branch | 1 pt | 2 pts | 1 pt | 3 pts | Keystone, 4 pts |
| --- | --- | --- | --- | --- | --- |
| **Rockets** | Cluster (2): Loads cluster rockets: three bomblets pop after the blast. | Incendiary (3): Loads incendiary rockets: the blast leaves fire. | Wide charge (6): Blast radius +6 %. | Concussion (12): Loads concussion rockets: a wider push, less damage. | Flare (22): Loads flare rockets: they light the area and show weak points. |
| **Salvo** | Practised hands (2): Reload 6 % faster. | Hot loader (9): A vent during a reload speeds it. | Quick fuse (11): Rockets fly 8 % faster. | Hot loader II (20): A vent that hits two foes finishes the reload. | Siege master (24): Siegebreaker salvos spread 15 % tighter. *(needs C60)* |
| **Shield** | Thick plate (4): Blast guard cost -8 %. | Planted shield (16): Hold the guard 1 s: planted, it stops draining and the next blast is larger. | Vent valve (18): Vent cooldown -10 %. | Planted shield II (26): The planted shield covers his front half. | Foundry wall (28): In sieges a planted shield also covers a champion behind it. |

Outfits: Foundry hand (story: own quest); Dock boss (village: workshop tier 1); Hazard orange (arena: gear floor, gold).
Accessories: Welder's cap, head (250 Glint); Canvas cover, back (rare drop: cogsworth); Red neckerchief, neck (bond 5); Gauge fob, trinket (village: workshop tier 2, perk: the bond meter starts each outing 10 higher).

### Nix

Neon Harbour cyborg; the laser arm is his anatomical LEFT arm in every view (steel-blue casing, cyan lens); the RIGHT arm natural with a black wrist wrap; teal jacket with orange lining. Kit (Codex): Laser arm, Afterimage, Arm shield, Limit Release. Loadout kind: pulse.

| Level | Weapon | What it is | Rig | Changes (placeholders) |
| --- | --- | --- | --- | --- |
| 1 | **Courier arm** | the tier-1 drawing: steel-blue casing on the LEFT arm, cyan lens | as drawn | starting weapon |
| 8 | **Finned arm** | three heat fins along the forearm; an orange lens ring | parts | cooling +15 % |
| 16 | **Split-lens arm** | the emitter widens into a three-lens head (+3 px wide), the lenses in a short row; the casing gains cyan traces | parts | beams 3, spread degrees 10, heat per shot +20 % |
| 24 | **Pearl arm** | pearl-white casing with gold seams that brighten with heat; violet-white lenses | parts | Pearl core: the heat lockout ends 20 % sooner |

| Branch | 1 pt | 2 pts | 1 pt | 3 pts | Keystone, 4 pts |
| --- | --- | --- | --- | --- | --- |
| **Pulses** | Needle (2): Sets needle pulses: thin, fast, pierce one. | Arc (3): Sets arc pulses: shock that chains to one foe. | Heat spread (6): Pulses add 8 % less heat. | Scatter (12): Sets scatter pulses: short range, a wide spray. | Redline (22): Above 80 % heat, every pulse chains. |
| **Ghost** | Quick image (2): Afterimage cooldown -8 %. | Flashbreak (9): The hologram breaks in a blinding flash. | Loud ghost (11): The hologram draws foes 20 % further. | Flashbreak II (20): The flash shows elites' weak points. | Double exposure (24): Breaking a hologram cools the arm by 20 %. |
| **Shield** | Capacitor (4): Arm shield cost -8 %. | Heat sink (16): A perfect dodge vents heat. | Grounded (18): Shock on you wears off 20 % sooner. | Heat sink II (26): The vent releases a small shock ring. | Limitless (28): Limit Release's beams pierce one more. *(needs C60)* |

Outfits: Night shift (story: own quest); Runner's kit (village: lookout tier 1); Chrome (arena: neon rooftop, gold).
Accessories: Visor band, head (rare drop: neon); Jacket hood, back (400 Glint); Earpiece cable, neck (bond 7); Glitched keychain, trinket (300 Glint, perk: the map marks company crates within 6 tiles).

### Rook

Orbital salvager in a cream pressure suit; one pulse carbine (right hand on the grip, left on the fore-end); ONE helmet at the RIGHT hip, worn only in Orbital Rig; twin-thruster pack with two nozzles. Kit (Codex): Pulse carbine, Thruster Vault, Energy guard, Orbital Rig. Loadout kind: cell.

| Level | Weapon | What it is | Rig | Changes (placeholders) |
| --- | --- | --- | --- | --- |
| 1 | **Salvage carbine** | the tier-1 drawing: pulse carbine, right hand on the grip, left on the fore-end | as drawn | starting weapon |
| 8 | **Shrouded carbine** | a barrel shroud (+3 px) with an orange stripe; a stock pad | parts | projectile speed +10 % |
| 16 | **Twin-barrel rifle** | two stacked barrels under one shroud, a top cell housing with a lit charge bar, +4 px longer than tier 1 | parts | burst 2, fire interval +20 % |
| 24 | **Launch-gold rifle** | a moonsilver emitter crown and gold crescent stock; the bolts pale gold | parts | Launch gold: bolts fired in a vault pierce one |

| Branch | 1 pt | 2 pts | 1 pt | 3 pts | Keystone, 4 pts |
| --- | --- | --- | --- | --- | --- |
| **Cells** | Amber cell (2): Loads amber: bolts designate longer. | Flare cell (3): Loads flare: bolts set burn. | Hot coils (6): Carbine recovers 5 % faster. | Mag cell (12): Loads mag: bolts slow machines more. | Overwatch (22): Turrets may stay a little further from you. *(needs C60)* |
| **Jets** | Trimmed jets (2): Vault cooldown -8 %. | Air shot (9): Bolts fired in a vault are charged. | Long hop (11): Vault distance +10 %. | Air shot II (20): Landing puffs a ring that knocks swarmers back. | Double jet (24): Two vaults can be chained. *(needs C60)* |
| **Rig** | Shield cells (4): Energy guard cost -8 %. | Scrap shell (16): Three blocked hits bank a shell; the next vault lands with a burst. | Spotter (18): Designation lasts 0.5 s longer. | Scrap shell II (26): Turrets start on the nearest designated foe. *(needs C60)* | Quick deploy (28): Turrets fire their first pulse sooner. *(needs C60)* |

Outfits: EVA orange (story: own quest); Station crew (village: station tier 4); Salvage rust (rare drop: halcyon).
Accessories: Antenna and stripe, head (arena: zero g dome, silver); Tank paint, back (450 Glint); Dog tags, neck (bond 8); Salvage tag, trinket (rare drop: halcyon, perk: salvage gives 1 more scrap per item).

### Mote

Genderless observatory keeper; long navy coat edged in gold with glass-inlaid hem fragments; two gold crescent hooks at the shoulders; the chest core (gold ring, blue lens); glass shards form in the RIGHT hand. Kit (Codex): Glass volley, Gravity anchor, Glass crescent, Aphelion. Loadout kind: glass.

| Level | Weapon | What it is | Rig | Changes (placeholders) |
| --- | --- | --- | --- | --- |
| 1 | **Observatory core** | the tier-1 drawing: gold ring round a blue lens; clear blue shards formed in the right hand | as drawn | starting weapon |
| 8 | **Dropped hooks** | glass drops hang from the crescent hooks; faceted shards | parts | shard speed +10 % |
| 16 | **Orrery** | a thin gold orrery ring tilted round the body at chest height (2 px outside the coat) carrying two glass beads; each volley also fires one shard from each bead | parts | extra shards 2 |
| 24 | **Little moon** | the core lens becomes a tiny full moon; the hooks tipped with stars; the beads lit | parts | Little moon: shards converge 15 % sooner |

| Branch | 1 pt | 2 pts | 1 pt | 3 pts | Keystone, 4 pts |
| --- | --- | --- | --- | --- | --- |
| **Glass** | Clear glass (2): Loads clear: shards pierce one. | Violet glass (3): Loads violet: shards chill. | Fine glass (6): Shards fly 6 % faster. | Mirror glass (12): Loads mirror: shards bounce once off walls. | Prism (22): Shards that pass an anchor split in two. |
| **Gravity** | Heavy point (2): Anchor radius +8 %. | Starfall (9): An anchor holding three foes calls a small rain of light. | Tidal pull (11): Anchor pull +10 %. | Starfall II (20): The rain covers a quarter more ground. | Aphelion bloom (24): Aphelion's orbit gains one shard. *(needs C60)* |
| **Panes** | Bright panes (4): Glass crescent cost -8 %. | Pane step (16): A perfect dodge leaves a pane that stops one shot. | Clear sight (18): Volley recovers 5 % faster. | Pane step II (26): A pane that blocks shatters into a small volley. | Event horizon (28): Anchors hold foes 0.3 s longer. |

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

1. **What the runner must support**:
   - per-folk skill points and node prerequisites (a level and the previous node);
   - nodes as modifiers over the canonical kit (a percentage or a count on a named field);
   - **weapon forms**: a tier swaps the primary's projectile and hit parameters (count, spread, capacity, alternating hands);
   - **loadout kinds**: one kind loaded at a time, adding an effect to hits;
   - technique hooks (after action X within t, while guard is held for t, on guard release after a block, on a perfect dodge, passive on hit or on projectile).

   All of it reads `game/data/progression/<id>.json`; the kit files are not edited.
2. **Nodes that change a count or rule inside the kit or powered form** wait for C60 and are marked *(needs C60)*; the JSON flags each with `touches_canonical`.
3. **The form changes need new clips in castwork**: seven folk, one clip set each (section 3).
4. **game-design changes.** "Any folk can equip any weapon" (4.3 and 5) gives way to signature weapon lines with fittings (Matt, 25 Oct). The perk card (6) gives way to the skill tree. Claude A updates game-design.md to match.
5. **Homes, Rook and Tam**: see [world-and-cast.md](world-and-cast.md).

## 8. For Matt

Decided: signature weapon lines with fittings; a skill tree on level points with weapon tiers at set levels; cheap forging per folk; perks only on trinkets. The open questions are in [world-and-cast.md](world-and-cast.md)'s summary, plus these two:

1. **Respec.** **At the hut bed for 50 Glint, the first one free.** Or free at any time outside a fight.
2. **Where to change looks and kinds.** **At a waystone or the hut, with a screen that previews every facing.** Or anywhere outside a fight.
