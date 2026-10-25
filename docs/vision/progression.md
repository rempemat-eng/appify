# Character progression: techniques, weapon tiers, outfits and accessories (25 Oct)

Matt, 25 Oct: "can you create new outfits/ accessories for the characters that they unlock some way and if i upgrade/ level up a character their weapons should become cooler as well/ they should learn new abilities".

**Status.** A proposal by Claude A for all fourteen folk. The data is in `game/data/progression/` (`catalogue.json` plus one file per folk); this page explains it, and its per-character section mirrors the JSON. **Every number is a placeholder** until play-tests and Claude L's balance harness set it. Nothing here changes game code, art or the save.

**What it builds on.**

- **Codex's kits** (`game/data/abilities/<id>.json`, C60, PR #261): each folk's primary, secondary, block and special with its powered form. They are canonical: this page adds to them and changes none of their numbers. The three places where a proposed upgrade would touch a canonical rule are marked *(needs C60)* and raised on #149.
- **game-design.md** (PR #223): one shared level from 1 to 30, a perk card of three at every level, gear level and the forge, Glint, scrap and one material per region, sieges, arenas, the familiar's bond levels, and defeat that keeps everything.
- **The castwork cast** (the fourteen at 74 px, `CONTRACT.md`) and cast contract v2 on `claude-a/cast-v2` (8 facings).
- **The vertical slice** (`vertical-slice.md`): Hale's forge is the first restored service.

## 1. Rules

1. **Growth you can see.** Every step shows on the folk: a new move, a weapon that looks finer, a new look. Nothing is a hidden number.
2. **No grind wall, no gambling.** Techniques come with the shared level; tiers are a forge step with fixed prices; cosmetics come from play you would do anyway, and the rare drops have a bad-luck counter and published rates.
3. **Small, readable mechanics.** No tier multiplies damage (gear level does that, game-design appendix B: "no other multipliers"). A technique is one line. A trinket perk is one line, never combat damage.
4. **Nothing on a clock.** No screen time, rest, naps, dailies, timers or expiring stock.
5. **No hand-drawn combinations.** Outfits and tiers are parameters of the castwork rig, rendered into every facing and clip by the exporter (section 6).

## 2. Levels and abilities

The shared level runs from 1 to 30 (about three per region). On top of game-design's perk card, each folk learns **three techniques**, and each technique gets **one upgrade**:

| Level | What every folk gains |
| --- | --- |
| 1 | The base kit (Codex): primary, secondary, block, special and its powered form |
| 3 | Technique 1 (about the Frostline) |
| 9 | Technique 2 (about Cogsworth) |
| 12 | Technique 1's upgrade |
| 16 | Technique 3 (about the Sunstone basin) |
| 20 | Technique 2's upgrade |
| 26 | Technique 3's upgrade |

- **No new buttons.** Each technique binds to an existing input (primary, secondary, block, special, dodge), a short timing window after one ("primary within 0.4 s after the sweep"), a held guard, or a passive condition. None uses a hold on primary, because Codex's primary repeats while held.
- **The base and powered forms stay Codex's.** A technique adds behaviour round them (a follow-up, a passive, a held-guard variant) and never edits their timing or damage.
- **A late joiner** arrives at the shared level with every technique and upgrade it has reached (game-design 6: nothing is levelled twice).
- **Perks stay as game-design designed them.** Techniques are the fixed, identity-led layer Matt asked for ("they should learn new abilities"); perks remain the per-level choice.
- **Art cost.** Of the 42 techniques, 38 reuse existing drawings with a small effect sprite. Four need one new clip each: Bramble's `secondary_loose`, Velvet's `primary_waltz`, Mirra's `guard_wave` and Ashe's `guard_check`. Rook's Air Shot needs the airborne primary that #257 already lists as missing.
- **Several techniques use the dodge and the perfect dodge** (game-design 4.2; Codex's kits have no dodge of their own). If the dodge changes, those bindings change with it.

## 3. Weapon tiers

Each folk's **signature weapon** is the item its kit is built on: Bramble's bow, Iona's spear, Pendle's revolver, Cairn's fists, Morel's flask and catalyst, Velvet's sabre, Tam's wraps, Mirra's wrist bands and gem, Brine's harpoon gun, Ashe's sword, Clack's launcher, Nix's laser arm, Rook's carbine and Mote's core and glass. It has four tiers:

| Tier | Name | Opens at | Paid at Hale's forge (placeholders) |
| --- | --- | --- | --- |
| 1 | Made | level 1 | the starting look |
| 2 | Fitted | level 8, forge tier 1 | 150 Glint, 10 scrap, 4 of the folk's home material |
| 3 | Masterwork | level 16, forge tier 2 | 600 Glint, 30 scrap, 10 home material |
| 4 | Starfall | level 24, forge tier 3 (the great forge) | 1,800 Glint, 60 scrap, 16 home material, 1 starshard |

- **What a tier changes.** The drawing (silhouette, material, glow, size; each tier is described for an artist in the folk's JSON and below) and **one small handling change** (tiers 2 and 3: a few per cent of reload, reach, cooldown, speed or guard cost; tier 4: one named effect, such as Pendle's last round being a critical hit). Power stays with gear level, which the forge also raises (game-design 5.6), so a tier is never a second damage curve.
- **Readable at 74 px.** At 1x, each tier differs from the one before by at least 3 px of silhouette or one new 2 x 2 px colour cluster. Several tier 4 glows carry state the player needs: Pendle's six chamber glints go dark as he fires, Clack's rocket nose shows the reload, and Nix's seams brighten with heat.
- **Starshards** are fist-sized splinters of the moon: guaranteed on the first defeat of each boss from act 3 on and in the deep shards after the story, and sold by Moss at a fixed price after the story. Never random-priced.
- **Hale** shows the next tier on the folk before you pay ("Show me"). Upgrading never fails.
- **A late joiner** arrives at the highest tier the forge has already opened, except Starfall, which is always a forge step.

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

| Level | Learns | How | Upgrade (level) |
| --- | --- | --- | --- |
| 3 | **Steady Aim**: Standing still and not firing builds Aim pips; the next arrow spends them for extra power. | passive: stand still without firing | Pips build faster, and a full three-pip arrow pierces one foe. (12) |
| 9 | **Hook and Loose**: A point-blank arrow follows the sweep and knocks the nearest foe back. | primary within 0.4 s after the billhook sweep | The sweep also staggers light foes, so the arrow lands. (20) |
| 16 | **Briar Snare**: A briar snare drops at your feet and roots the next ground foe that steps on it. | lower the buckler within 0.5 s after it blocks a hit | Two snares at once; a foe rooted by Briarshot springs the nearest snare too. (26) |

| Tier | Bow | Changes |
| --- | --- | --- |
| 1 Yew bow | today's drawing: a plain shallow recurve, 42 px tip to tip, leather grip wrap | starting look |
| 2 Carved recurve | the limb tips curl back 3 px each into a clear recurve; the grip is wrapped in green cord 6 px long | arrow speed +8 % |
| 3 Horn-tipped bow | pale horn caps (3 px) on both tips; a 2 x 3 px shard set into the riser in a gold bezel | primary cooldown -6 % |
| 4 Starfall bow | limbs of dark moonwood that flare into crescent tips (+2 px each end); gold riser; the string is drawn in starlight | Starlit: a three-pip arrow also shows the foe's weak point for 2 s |

Outfits: Autumn forester (story: own quest); Sheepskin mantle (village: fold and loom tier 1); Ranger's pine (450 Glint).
Accessories: Feathered cap, head (rare drop: valley); Patched travelling cloak, back (arena: training yard, silver); Oak-leaf scarf, neck (bond 3); Acorn whistle, trinket (250 Glint, perk: pickup magnet radius +15 %).

### Iona

Grassland storm-lancer; one 92 px spear in the RIGHT hand, the LEFT grips the same shaft for two-handed actions; long braid down the back, magenta scarf. Kit (Codex): Spearpoint, Wind lunge, Gust guard, Storm Mantle.

| Level | Learns | How | Upgrade (level) |
| --- | --- | --- | --- |
| 3 | **Gale Step**: The roll flows into a long thrust that reaches further than Spearpoint. | primary within 0.3 s after a dodge | A Gale Step that hits gives back half a dodge charge. (12) |
| 9 | **Static Charge**: The next Wind lunge into a charged foe discharges one small arc to a second foe. Smaller than Storm Mantle's arcs, and only from a lunge. | passive: every third spear hit on the same foe charges it | The discharge interrupts a shooter's wind-up, once per foe. (20) |
| 16 | **Windbreak**: The projectile is turned back along its path instead of draining guard. | raise Gust guard within 0.2 s of a projectile reaching you | Deflected projectiles carry a storm arc. (26) |

| Tier | Spear | Changes |
| --- | --- | --- |
| 1 Ash spear | today's drawing: steel leaf blade, gold collar, gold-banded brass shaft, steel butt spike; 92 px | starting look |
| 2 Windcut spear | two swept barbs (4 px each) below the leaf blade; a magenta pennon (2 x 6 px) tied at the collar that trails like her scarf | primary reach +4 |
| 3 Stormwrought spear | the blade reforged in blued steel with a bright edge; three copper coil rings below the collar; the butt spike becomes a weighted ring pommel | secondary cooldown -8 % |
| 4 Starfall lance | a pale moonsilver blade with a 1 px storm-blue fuller; a gold crescent collar; the pennon becomes a ribbon of light 8 px long | Stormlit: the first hit after a Wind lunge arcs to one more foe for 30 % |

Outfits: Moor coat (story: own quest); Yard drill coat (village: training yard tier 2); Tempest (600 Glint).
Accessories: Kestrel hairpin, head (bond 4); Shoulder cloak, back (arena: training yard, gold); Moor tartan scarf, neck (rare drop: brackens); Weathervane charm, trinket (300 Glint, perk: the familiar's weak-point glint lasts 0.5 s longer).

### Pendle

Sunstone robot gunslinger; one revolver on the RIGHT hip, one marksman rifle slung across the back (stock at the right hip, barrel past the LEFT shoulder); cattleman hat; no clock motif. Kit (Codex): Revolver, Fan fire, Steel plate, Longshot.

| Level | Learns | How | Upgrade (level) |
| --- | --- | --- | --- |
| 3 | **Quick Hands**: Two rounds slip into the cylinder during the roll. | a perfect dodge | After a full reload from empty, the first shot is a critical hit. (12) |
| 9 | **Ricochet**: Fan fire rounds that hit high cover bounce once. | passive on Fan fire | A bounced round turns toward the nearest foe within 30 degrees. (20) |
| 16 | **Dead Eye**: The foe under the aim shows its weak point (the familiar's glint) for the next shot. | during Longshot, hold still for 0.6 s | A Longshot weak-point hit gives back 1 s of Longshot. (26) *(needs C60)* |

| Tier | Revolver | Changes |
| --- | --- | --- |
| 1 Trail revolver | today's drawing: gunmetal frame, walnut grip, visible cylinder and trigger guard | starting look |
| 2 Engraved revolver | brass inlay lines on the cylinder; cream grip panels; the barrel 2 px longer | reload -8 % |
| 3 Brass-frame revolver | a brass frame with two 1 px ports on the barrel; a red lanyard from the grip to the belt; the rifle's scope gains a brass sunshade to match | fan spread -10 % |
| 4 Six Suns | the cylinder is sunstone glass lit from inside, with six 1 px chamber glints; a gold muzzle crown; a gold crescent front sight on the rifle | Six Suns: the last round in the cylinder is a critical hit |

Outfits: Gulch duster (story: own quest); Oasis whites (village: water tower tier 1); Midnight rider (arena: dusty corral, gold).
Accessories: Flat-brim hat, head (rare drop: sunstone); Serape, back (500 Glint); Star bandana, neck (bond 5); Lucky silver dollar, trinket (village: stall tier 2, perk: the first reload of each fight is 15 % faster).

### Cairn

Moss-covered granite golem from the woodland circle, about 90 px; great round fists, a sprout on the LEFT shoulder, two floating pebbles over the RIGHT shoulder. Kit (Codex): Stone fist, Boulder, Crossed arms, Old Growth.

| Level | Learns | How | Upgrade (level) |
| --- | --- | --- | --- |
| 3 | **Bedrock**: Once every few seconds the guard takes a whole hit with no guard cost. | passive on Crossed arms | A Bedrock block shoves the attacker back. (12) |
| 9 | **Stonebreak**: A boulder that hits a tank cracks its front armour for a few seconds. | passive on Boulder | A boulder that hits any foe slows its next wind-up. (20) |
| 16 | **Pebble Ward**: Each pebble catches one projectile and re-forms after a while. | passive: the two pebbles over his right shoulder | A pebble that catches a shot flicks it back. (26) |

| Tier | Fists | Changes |
| --- | --- | --- |
| 1 Bare stone | today's drawing: round granite fists with dark joint gaps | starting look |
| 2 Banded fists | two iron knuckle bands round each fist, raised 2 px from the stone | boulder speed +8 % |
| 3 Rooted fists | roots wrap the bands and end in small moss cushions on the knuckles; a fern curl on the right wrist | guard cost -10 % |
| 4 Moonvein fists | seams of white-gold moonstone run through the fist cracks; a crescent shard set in each band | Moonvein: Stone fist staggers swarmers |

Outfits: Spring bloom (village: greenhouse tier 1); Circle runes (story: own quest); Basalt (arena: basalt ring, silver).
Accessories: Daisy crown, head (bond 2); Wren's nest, back (rare drop: valley); Festival ribbon, neck (200 Glint); Smooth river stone, trinket (rare drop: lull, perk: tonics are drunk 15 % faster).

### Morel

Older grassland alchemist; one blue flask in the RIGHT hand, a closed reagent case on the RIGHT hip, the catalyst apparatus at the LEFT hip, one mask on the chest (on the face in the special). Kit (Codex): Reagent flask, Catalyst, Mineral ward, Catalyst mask.

| Level | Learns | How | Upgrade (level) |
| --- | --- | --- | --- |
| 3 | **Tacky Reagent**: Foes standing in a patch move slower. | passive on reagent patches | Slowed foes take more from a Catalyst spark. (12) |
| 9 | **Mineral Skin**: Instead of a patch, a mineral skin softens the next hit you take. | throw a flask at your own feet (aim within 1.5 tiles) | The skin also clears burn, chill and shock. (20) |
| 16 | **Drowsy Fume**: A fume rises from the chain and makes foes in it attack half as often for a short time. | Catalyst through three or more patches at once | The fume spreads to patches next to it. (26) |

| Tier | Flask and catalyst | Changes |
| --- | --- | --- |
| 1 Field kit | today's drawing: blue glass flask held by the neck; brass chamber, glass bulb and copper coil | starting look |
| 2 Caged flasks | a copper wire cage (1 px grid) over the flask glass; a second coil on the catalyst | throw range +10 % |
| 3 Sealed flasks | a brass cap with a red wax seal on each flask; brass corners on the reagent case; the catalyst bulb 2 px larger with a small gauge | patch lifetime +15 % |
| 4 Starglass kit | pale violet-white glass with a 2 px mote of light floating inside each flask; the catalyst bulb holds a captive spark; gold rims on the mask lenses | Starglass: a Catalyst chain jumps one extra patch |

Outfits: Herbalist's apron (village: apothecary tier 2); Laboratory coat (story: own quest); Ember smock (rare drop: fire country).
Accessories: Bowler hat, head (300 Glint); Oilcloth cape, back (arena: gear floor, silver); Spectacles on a chain, neck (bond 4); Pocket mortar, trinket (story: apothecary first tonic, perk: tonics heal 5 % more).

### Velvet

Coastal duellist from Driftwood; one sabre in the LEFT hand (closed brass knuckle-bow), its empty scabbard on the RIGHT hip, one black lantern by its bail in the RIGHT hand. Kit (Codex): Sabre, Lantern flare, Sabre parry, Black Lantern.

| Level | Learns | How | Upgrade (level) |
| --- | --- | --- | --- |
| 3 | **Riposte**: The next sabre cut comes faster. In the base form only; Black Lantern's long counter-thrust is unchanged. | a parry in the first 0.2 s of a melee hit | The riposte cut exposes the foe, as Lantern flare does. (12) |
| 9 | **Dim**: The lantern shutters after the flare; for a moment shooters lose track of her and hold fire. | passive after Lantern flare | A perfect dodge while dimmed takes time off the flare's cooldown. (20) |
| 16 | **Moth's Waltz**: The third cut becomes a stepping lunge-cut through the foe. | the third sabre cut in a row | The lunge leaves a pale echo that cuts once more half a second later. (26) |

| Tier | Sabre | Changes |
| --- | --- | --- |
| 1 Naval sabre | today's drawing: curved steel blade, brass knuckle-bow guard | starting look |
| 2 Blackened sabre | a blackened fuller with a bright edge; a second bar on the knuckle-bow | arc degrees +5 |
| 3 Basket-hilt sabre | a full brass shell guard (5 x 5 px) round the fist; a violet sword knot (5 px) from the pommel | flare cooldown -8 % |
| 4 Moonlit sabre | a moonsilver blade whose edge carries a pale light; the black lantern's cage turns gold and its flame pale blue-white | Moonlit: a perfect parry flashes the lantern and exposes foes within 2 tiles |

Outfits: Harbour blue (story: own quest); Keeper's oilskin (village: bell tower tier 2); Masquerade (arena: harbour jetty, gold).
Accessories: Tricorn, head (rare drop: valley); Boat cloak, back (550 Glint); Lace jabot, neck (bond 6); Moth brooch, trinket (arena: harbour jetty, bronze, perk: your defeat cache shows from twice as far).

### Tam

Mature Frostline ice monk in ochre and saffron robes; cool grey-blue wraps on both forearms, palms and shins; one mala round the neck; no weapon, the wraps are his. Kit (Codex): Frost palms, Ice ridge, Ice guard, Glacier Form.

| Level | Learns | How | Upgrade (level) |
| --- | --- | --- | --- |
| 3 | **Cold Breath**: The held breath steadies him: the next palm applies two frost instead of one. | hold Ice guard for 1 s | The steadied palm also slows the foe. (12) |
| 9 | **Ridge Wall**: The ridge ends in a low ice wall that stops projectiles for a moment. | passive on Ice ridge | A wall that is hit shatters and chills foes beside it. (20) |
| 16 | **Still Water Step**: A frost patch is left where he rolled; foes on it slow. | a perfect dodge | Palms on a foe standing on the patch add one more frost. (26) |

| Tier | Wraps | Changes |
| --- | --- | --- |
| 1 Plain wraps | today's drawing: grey-blue cloth wraps on forearms, palms and shins | starting look |
| 2 Frost-stitched wraps | white zigzag stitching (1 px) along the wraps and a second wind at the wrists; three ice-blue beads added to the mala | ridge speed +10 % |
| 3 Hoarfrost guards | pale ice plates (3 px) on the backs of both hands and the shins, tied over the wraps | guard drain -10 % |
| 4 Moonbead wraps | the ice plates turn to clear starglass lit from inside; the guru bead becomes a small glowing moon (2 x 2 px) | Moonbead: a frost shatter also chills foes beside the target |

Outfits: Snow robes (village: training yard tier 1); Pilgrim (story: own quest); Temple gold (700 Glint).
Accessories: Straw rain hat, head (arena: castle courtyard, gold); Straw rain cape, back (rare drop: frostline); Winter mala, neck (bond 3); Kettle charm, trinket (300 Glint, perk: chill on you wears off 20 % sooner).

### Mirra

Oasis water diviner; hands empty and open in every clip (water is a scene effect); ivory headwrap with a turquoise gem above the RIGHT ear; turquoise wrist bands; shawl end over the LEFT shoulder. Kit (Codex): Water bolt, Spring seal, Water curtain, Oasis Unbound.

| Level | Learns | How | Upgrade (level) |
| --- | --- | --- | --- |
| 3 | **Seep**: The spring heals her a little each second, for a few seconds per seal. | passive: stand in one of your own spring seals | Dodges recharge faster while she stands in a seal. (12) |
| 9 | **Undertow**: The widened bolt pulls light foes one step toward the seal. | passive: a water bolt fired through a seal | Pulled foes are soaked: their next hit taken is stronger. (20) |
| 16 | **Curtain Wave**: The curtain rolls forward as a wave that pushes foes and projectiles back. | hold Water curtain for 0.8 s, then let go | A spring seal is left where the wave breaks. (26) |

| Tier | Wrist bands and gem | Changes |
| --- | --- | --- |
| 1 Turquoise bands | today's drawing: turquoise wrist bands with gold studs; the gem in a gold setting above the right ear | starting look |
| 2 Wave bands | the bands 1 px wider with a carved gold wave line; a teardrop pendant (2 x 3 px) under the gem | bolt speed +8 % |
| 3 Paired bands | a second band high on each forearm, joined to the wrist band by two fine gold chains; the gem 3 x 4 px | seal radius +10 % |
| 4 Starspring bands | the turquoise turns to clear water-glass lit from inside; the gem becomes starlit oasis glass | Starspring: your seals last 1 s longer |

Outfits: Dusk caravan (story: own quest); Garden linen (village: water tower tier 2); Festival red (rare drop: sunstone).
Accessories: Gold head chain, head (400 Glint); Travelling shawl, back (arena: dusty corral, silver); Shell necklace, neck (rare drop: isles); Dowsing pendant, trinket (bond 5, perk: regional seeds drop 10 % more often).

### Brine

Coastal diver in a sealed copper helmet; one harpoon gun (wooden stock, gunmetal body, brass reel on the right side); an olive air pack with ONE hose to the helmet's right rear. Kit (Codex): Harpoon gun, Reel, Dive brace, Abyssal Drive.

| Level | Learns | How | Upgrade (level) |
| --- | --- | --- | --- |
| 3 | **Anchor Line**: He arrives with a gun-butt strike. | Reel toward an anchored heavy target | The arrival strike staggers the target. (12) |
| 9 | **Barbed Line**: A tethered foe takes a little damage each second. | passive while a foe is tethered | Reeling a light foe into a wall stuns it. (20) |
| 16 | **Pressure Brace**: Pressure builds in the pack: the next harpoon flies faster and passes through one foe. | hold Dive brace for 1 s | For its first 0.3 s the brace blocks from every side. (26) |

| Tier | Harpoon gun | Changes |
| --- | --- | --- |
| 1 Dock harpoon | today's drawing: wooden stock, gunmetal body, brass reel under the barrel, harpoon in the muzzle | starting look |
| 2 Sheathed harpoon | a copper sheath with three rivets over the barrel; the reel drum 2 px wider; a barbed harpoon head | reel speed +10 % |
| 3 Pressure harpoon | a brass pressure bottle with a round gauge under the barrel; a fin vane on the harpoon | range +8 % |
| 4 Abyssal harpoon | a moonsilver harpoon head with a bioluminescent teal line; a navy lacquered stock; the reel's spokes glow while reeling | Abyss light: a tethered foe shows its weak point while the line holds |

Outfits: Reef suit (story: own quest); Naturalist's suit (village: menagerie tier 1); Deep black (arena: basalt ring, gold).
Accessories: Copper crest fin, head (bond 6); Net bag, back (rare drop: isles); Diver's medal, neck (350 Glint); Lucky shell, trinket (250 Glint, perk: loot bursts land 30 % closer to you).

### Ashe

Ember knight in brass-edged steel plate; ONE sword in the RIGHT hand; ONE barred-visor helm with a crimson crest, carried under the LEFT arm and worn only in Cinderhelm; crimson cape and tabard. Kit (Codex): Ember blade, Ember thrust, Armoured guard, Cinderhelm.

| Level | Learns | How | Upgrade (level) |
| --- | --- | --- | --- |
| 3 | **Banked Fire**: Heat builds in the blade; Ember thrust spends it for extra power. | passive: each Ember blade hit | At full heat the guard costs less. (12) |
| 9 | **Shoulder Check**: She drives the pauldron forward in a short shove. | lower Armoured guard within 0.5 s after it blocks a hit | The check breaks a tank's shield guard. (20) |
| 16 | **Ember Wake**: The thrust leaves a short burning line on the ground. | passive on Ember thrust | Cinderhelm's closing finisher also leaves the wake. (26) *(needs C60)* |

| Tier | Sword | Changes |
| --- | --- | --- |
| 1 Knight's sword | today's drawing: steel blade with a fuller, brass cross guard, leather grip, brass pommel | starting look |
| 2 Ember-forged sword | the blade 3 px longer; the fuller shows a dull ember line; the cross guard flared at both ends | thrust reach +4 |
| 3 Wave blade | a gently waved edge (2 px undulation); a dragon-head pommel; a crimson grip wrap | guard cost -10 % |
| 4 Starforged edge | the fuller glows white-gold; the cross guard becomes two crescent horns | Starforged edge: the third sweep in a row throws a small flame crescent |

Outfits: Tournament plate (story: own quest); Blackened plate (village: trophy hall tier 1); Ember guard (900 Glint).
Accessories: Dragon crest, head (rare drop: fire country); Heraldic cape, back (arena: castle courtyard, silver); Mail collar, neck (bond 7); Bell charm, trinket (village: bell tower tier 1, perk: burn on you wears off 20 % sooner).

### Clack

Older broad heavy gunner; rocket launcher on the RIGHT shoulder, a separate pressure chamber under the tube, a two-rocket rack on the front LEFT of the belt, a folding loader frame flat on the back. Kit (Codex): Shoulder rocket, Concussive vent, Blast guard, Siegebreaker.

| Level | Learns | How | Upgrade (level) |
| --- | --- | --- | --- |
| 3 | **Hot Loader**: The vent's kick speeds the loading. | Concussive vent during a reload | A vent that hits two or more foes completes the reload. (12) |
| 9 | **Cluster Nose**: The blast scatters three small bomblets that pop a moment later. | passive on Shoulder rocket | Bomblets nudge small foes toward the blast's centre. (20) |
| 16 | **Planted Shield**: He plants the shield: he cannot walk, blocked shots stop draining the guard, and the next rocket's blast is larger. | hold Blast guard for 1 s | The planted shield covers his whole front half. (26) |

| Tier | Rocket launcher | Changes |
| --- | --- | --- |
| 1 Works launcher | today's drawing: gunmetal tube with orange bands, brass muzzle ring, flared exhaust bell | starting look |
| 2 Plated launcher | riveted heat plates over the tube; the orange bands become 2 px diagonal hazard stripes; the bell 2 px wider | reload -8 % |
| 3 Braked launcher | a brass muzzle brake with four vents; a small periscope sight on the left; a second gauge on the pressure chamber | blast radius +6 % |
| 4 Starnose launcher | a dark station-alloy tube with gold bands; the loaded rocket's nose in the bore is pale starlight | Starnose: a rocket that frees a foe cuts the reload by 20 % |

Outfits: Foundry hand (story: own quest); Dock boss (village: workshop tier 1); Hazard orange (arena: gear floor, gold).
Accessories: Welder's cap, head (250 Glint); Canvas cover, back (rare drop: cogsworth); Red neckerchief, neck (bond 5); Gauge fob, trinket (village: workshop tier 2, perk: the bond meter starts each outing 10 higher).

### Nix

Neon Harbour cyborg; the laser arm is his anatomical LEFT arm in every view (steel-blue casing, cyan lens); the RIGHT arm natural with a black wrist wrap; teal jacket with orange lining. Kit (Codex): Laser arm, Afterimage, Arm shield, Limit Release.

| Level | Learns | How | Upgrade (level) |
| --- | --- | --- | --- |
| 3 | **Heat Sink**: The arm vents part of its heat. | a perfect dodge | The vent releases a small shock ring. (12) |
| 9 | **Flashbreak**: The hologram breaks in a flash that blinds foes beside it. | passive when the Afterimage breaks | The flash also shows elites' weak points for 3 s. (20) |
| 16 | **Redline**: Pulses chain to one nearby foe. | passive above 80 % heat | Blocking with the arm shield above 80 % heat turns part of the blocked damage into cooling. (26) |

| Tier | Laser arm | Changes |
| --- | --- | --- |
| 1 Courier arm | today's drawing: steel-blue casing from the pauldron to a heavy forearm emitter with a cyan lens | starting look |
| 2 Finned arm | three heat fins (2 px) along the forearm; an orange ring round the lens | cooling +10 % |
| 3 Focus arm | the lens pushed 2 px forward in a short barrel; cyan circuit traces along the casing | afterimage cooldown -8 % |
| 4 Pearl arm | pearl-white casing with gold seams; a pale violet-white lens | Pearl core: the heat lockout ends 20 % sooner |

Outfits: Night shift (story: own quest); Runner's kit (village: lookout tier 1); Chrome (arena: neon rooftop, gold).
Accessories: Visor band, head (rare drop: neon); Jacket hood, back (400 Glint); Earpiece cable, neck (bond 7); Glitched keychain, trinket (300 Glint, perk: shock on you wears off 20 % sooner).

### Rook

Orbital salvager in a cream pressure suit; one pulse carbine (right hand on the grip, left on the fore-end); ONE helmet at the RIGHT hip, worn only in Orbital Rig; twin-thruster pack with two nozzles. Kit (Codex): Pulse carbine, Thruster Vault, Energy guard, Orbital Rig.

| Level | Learns | How | Upgrade (level) |
| --- | --- | --- | --- |
| 3 | **Air Shot**: Bolts fired from the air are charged. | carbine bolts fired while airborne in a vault | Landing from a vault puffs a dust ring that knocks swarmers back. (12) |
| 9 | **Thruster Flare**: The take-off leaves a short flame at its start that burns foes in it. | passive on Thruster Vault | The vault recharges faster. (20) |
| 16 | **Scrap Shell**: The guard banks a shell; the next vault lands with a burst round him. | block three hits with Energy guard | Orbital Rig's turrets start on the nearest foe he has designated. (26) *(needs C60)* |

| Tier | Pulse carbine | Changes |
| --- | --- | --- |
| 1 Salvage carbine | today's drawing: the pulse carbine with its fore-end | starting look |
| 2 Shrouded carbine | an extended barrel shroud with an orange stripe; a stock pad | bolt speed +8 % |
| 3 Scoped carbine | a top-mounted salvaged scope with an orange lens; a cooling coil on the side | vault cooldown -8 % |
| 4 Lander carbine | a moonsilver emitter crown and a gold crescent on the stock; the bolts turn pale gold | Lander gold: bolts fired from the air pierce one foe |

Outfits: EVA orange (story: own quest); Station crew (village: station tier 4); Salvage rust (rare drop: halcyon).
Accessories: Antenna and stripe, head (arena: zero g dome, silver); Tank paint, back (450 Glint); Dog tags, neck (bond 8); Salvage tag, trinket (rare drop: halcyon, perk: salvage gives 1 more scrap per item).

### Mote

Genderless observatory keeper; long navy coat edged in gold with glass-inlaid hem fragments; two gold crescent hooks at the shoulders; the chest core (gold ring, blue lens); glass shards form in the RIGHT hand. Kit (Codex): Glass volley, Gravity anchor, Glass crescent, Aphelion.

| Level | Learns | How | Upgrade (level) |
| --- | --- | --- | --- |
| 3 | **Refraction**: The shard splits in two. | passive: a shard that passes through a gravity anchor | Split shards slow what they hit. (12) |
| 9 | **Pane Step**: One glass pane stays standing where Mote rolled and stops one projectile. | a perfect dodge | A pane that blocks shatters into a small volley. (20) |
| 16 | **Starfall**: A small rain of light falls on the anchor a moment later. | a gravity anchor that draws in three or more foes | The rain covers a quarter more ground. (26) |

| Tier | Core and glass | Changes |
| --- | --- | --- |
| 1 Observatory core | today's drawing: gold ring round a blue glass lens with an amber light; clear blue shards | starting look |
| 2 Dropped hooks | the crescent hooks gain hanging glass drops (2 px); the shards gain a faceted light edge | shard speed +8 % |
| 3 Orrery core | a thin gold orrery ring (1 px) tilted round the core; violet-tinted shards | anchor radius +8 % |
| 4 Little moon | the lens becomes a tiny full moon (starlight disc with two craters); the hooks tipped with stars | Little moon: volley shards converge 15 % sooner |

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
- **Save fields** (proposed for the save owner): `progression.level` and `progression.xp`; `folk.<id>.weapon_tier`; `folk.<id>.look` = {outfit, head, back, neck, trinket}; `wardrobe` = {folk: [item ids]}; `drop_counters` = {region: count}; `seen` for the "new" marks. Techniques derive from the level and are never stored. A save version step migrates the old hats as accessories (game-design 14.1).
- **Unlock events:** the existing quest, restore and flag events plus `arena:*`, `bond:*`, `drop:*` and `buy:*` go to one `Progression` node, which checks `catalogue.json` and each folk's file, writes the wardrobe, and raises `cosmetic:<folk>:<item>`, `tier:<folk>:<n>` and `technique:<folk>:<id>` for the HUD's one-line toast.

## 7. Conflicts and dependencies (raised on #149)

1. **"Any folk can equip any weapon"** (game-design 4.3 and 5) does not fit Codex's kits, which are built on each folk's own weapon, or the castwork rig, which draws that weapon in every clip. This page assumes the signature weapon stays (For Matt, 1).
2. **game-design 4.3's specials** (Puffcap, Puddle, Tally, Tuff and Bunk among them) predate Codex's fourteen. This page follows Codex's cast and kits. Some of 4.3's ideas return as techniques: Bramble's Steady Aim, Velvet's Dim, Cairn's Bedrock, Ashe's Banked Fire, Mirra's Seep and Mote's Starfall.
3. **Three upgrades touch a canonical rule** and wait for C60: Pendle's Dead Eye II gives back Longshot time, Ashe's Ember Wake II adds an effect to Cinderhelm's finisher, and Rook's Scrap Shell II sets the turrets' first target.
4. **The runner needs a technique layer**: data-driven hooks (after action X within t, while guard is held for t, on a perfect dodge, passive on hit or on projectile) that read `abilities.techniques` without editing the kit files.
5. **Homes and materials** follow Claude K's proposal on #149, which Matt has not decided. Only the tier material depends on it.

## 8. For Matt

Each has a recommendation in bold.

1. **Signature weapons or any weapon?** **Each folk keeps its signature weapon, which grows through the four tiers; loot becomes fittings (affixes) set into it at the forge and workshop.** Or keep game-design's free weapon swapping, which needs a second set of kits and a melee and aim set per weapon class for every folk.
2. **Techniques: fixed or chosen?** **Fixed, at levels 3, 9 and 16 with upgrades at 12, 20 and 26, so every folk feels its growth the same way; perks stay the per-level choice.** Or put them into the perk pools.
3. **Does every folk pay for its own tiers?** **Yes, but cheaply, and a late joiner arrives at the forge's highest open tier.** Or one forge pattern raises every folk's weapon at once.
4. **Trinket perks.** **One small perk on each folk's trinket only, never damage; everything else is cosmetic.** Or no perks on any cosmetic.
5. **Where to change looks.** **At the bed in your hut, with a wardrobe screen that previews every facing.** Or anywhere outside a fight.
