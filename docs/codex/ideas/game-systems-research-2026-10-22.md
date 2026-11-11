# The game beyond combat: design recommendations, 22 October 2026

For Claude A, the world and character lanes, and Matt. Preparation for drawing and animation on Saturday 24 October. This is a research and design proposal, not a change to gameplay, accepted vision, worker assignments or existing holds.

Reviewed against `main@18a8bef77d79bb81163ada1df038fbb3ce6477df`, PR #223's `game-design.md@637cfb0677e45321f2bfd21990a88e4155b926fd`, the two existing design-feedback comments, the current cast, animation and sound specifications, the world/save boundaries and the real-time prototype. The recommendations below extend that draft. They do not treat it as implemented.

## 1. The game to build

An action RPG about travelling through a fractured world and rebuilding a town that becomes home to the people met along the way. The fourteen playable folk provide different ways to fight. A familiar makes the chosen fighter feel like one half of a partnership. Expeditions earn equipment, discoveries and the means to restore Crossroads. Homecoming lets the player see what those expeditions achieved, make a useful change and choose the next journey.

The central promise is: **go somewhere worth discovering, fight in your own style, bring something meaningful home, and leave with a new possibility**.

The village should be a place the player wants to inhabit, as well as a collection of useful services. Combat should be enjoyable before the first level-up. A favourite character should remain useful after guns and lasers arrive. Exploration needs discoveries beyond additional fights and money. These are the four standards against which the larger feature list should be tested.

Matt's accepted direction is retained: the old sleep, nap, screen-time, away-time and Dream Dust systems are removed; direct real-time fighting replaces card battles; all fourteen folk remain playable; progression, quests, arenas, decorating, village improvement and occasional village attacks remain; the starfall and Glint remain; the player fights with familiar support; desktop and landscape come first, with phone support. Crossroads is the current restoration setting. Its precise framing, raid insistence and distribution/packaging details still appear as choices in the draft.

Developer comparisons inform individual mechanisms rather than dictate a complete formula. Eastward is useful for space and visual storytelling [S1], Children of Morta for character identity [S2], Moonlighter for the relationship between expeditions and home [S6], Cult of the Lamb for simplifying two interdependent genres [S7], CrossCode for action clarity [S8, S9], and Hades for flexible challenge and characters who remember progress [S5]. The recommendations are design inferences, not findings that those games prove this design will succeed.

## 2. What exists, what is proposed

| Building block | Verified position at the reviewed heads | Recommendation |
| --- | --- | --- |
| World and travel | Main contains connected regions/zones, walking, routes and transport, discovery/save models and a world-canvas rebuild in progress. | Extend the existing geography; author encounters against its actual movement and deck rules. |
| Visual production | Main has house-style rules, region plans/kits, generators, asset checks and animation data/machine scaffolding. | Preserve these tools, revise their action-RPG assumptions before drawing fight sets. |
| Action combat | A standalone real-time prototype demonstrates movement, bow, dodge, telegraphs, leash and a phased boss. | Port and prove production integration. Its old Glares, sleeping defeat and placeholder facings do not carry over. |
| Fourteen playable folk | Defined cast and accepted roster target; ordinary-attack kit proposals are in #223's feedback. | Four contrasting temporary kits first, all fourteen as the production target. |
| Familiar | Existing companion identity/art infrastructure; the new aura/save/burst and bond design is a draft. | A readable, non-blocking support partner; retain passive value and test burst access. |
| New campaign | Starfall, Company, four-act arc, regional recruitment and fourteen stones are designed in #223. | Convert into distinct chapter problems with local and town consequences. |
| Loot/levelling | Shared progression exists in the old game; the new Glint, weapon, affix, perk and gear-level economy is proposed. | Author a small useful reward set, then prove campaign budgets. |
| Home/decor | Hut, decoration, keepsake and garden infrastructure exists. | Reuse identity and placement where suitable; new restoration, crop and service rules need implementation. |
| Village defence | Old raid systems exist; the new prepared real-time sieges/earned raids are proposals. | One later prototype using the same combat engine and a few defence functions. |
| NPC life and story | Residents, routes and prior story material exist. | Retain places and personalities, rewrite progression triggers around player actions. |
| Sound | Existing generated cues and several ambient loops; old rules assume a gentle rest game. | Preserve lifecycle discipline, add an action-focused cue hierarchy and regional identity. |
| Saves/platforms | Persistent world position, layout migration, recovery and native-readiness work exist. | Preserve data; prove the new campaign can pause/resume without duplicate rewards or offline combat. |

Neither the complete RPG loop nor its new balance is established by the standalone prototype, CI results or document graders.

## 3. Make the world a journey, with room to explore

Keep the continent and its transport network. Use an authored main route, optional local loops, and shortcuts back to familiar places. Avoid both an immediate map full of unrelated objectives and a corridor where every region is an isolated combat level.

Each chapter should offer five kinds of space: an inhabited arrival point; an exploratory route with a view of the destination; a field encounter that teaches the chapter's idea; a dungeon or major set piece that combines it; and a changed route home. That is a design grammar, not a demand to add five maps to every region. Several functions can share one place.

Give each route a recognisable landmark and a reason it exists: the millrace serves the town, the foundry follows coal and rail, the delta carries freight, the oasis supports the caravan route. The starfall has disrupted these relationships. Repairing them explains why travel and town services improve together. Cogsworth and Neon should be two stages of the same industrial/trading world, with the Company's equipment and supply routes providing continuity. The islands' basalt and the fire country's forge already offer a material connection. Do not solve the genre mixture by distributing unrelated fantasy decorations everywhere. Team Cherry's account of visible power structures and coherent ecosystems is a useful comparison for making a faction's influence readable before reaching its centre [S10].

Eastward's director discusses fixed-camera visibility, elevation and paths as tools for making top-down spaces legible [S1]. The inference here is to compose for a moving fighter as well as a walking visitor: a detailed building can frame a route, but its roof cannot hide a charge or the player's feet.

### Exploration rewards

Use different rewards for different discoveries:

- A hidden path opens a permanent shortcut or an alternate approach to a camp.
- A lookout reveals the shape of the next destination and records a named place on the map.
- A small optional room contains a meaningful item, seed, crafting pattern or familiar encounter.
- A domestic or historical discovery changes a resident's conversation and adds a keepsake or journal entry.
- An optional hard fight provides a sidegrade or cosmetic distinction, while the main path still supplies a viable build.

Not every bench, ruin, boot or marker-stone slot needs a reward or quest. Some scenery should simply imply history. Give a few secrets consistent clues, so discovering one teaches the player how to look elsewhere. Tunic's developers describe this distinction between learning an isolated location and learning a property of the world [S11]. The map should distinguish an unresolved discovery from decorative ground and a completed objective. Show transport connections when learnt; keep undiscovered local details concealed. Pin one chosen objective and give a useful last-action reminder on resume.

Travel is atmosphere and a return route, not a recurring toll. Show the first journey and a changed journey; make familiar trips promptly skippable. Unlocking a shortcut should save real walking. Cleared main routes should not become unavoidable trash fights after every train ride. Optional repeatable camps can refresh on an explicit expedition reset or bounty state, with their rewards tracked independently from first clears.

### Traversal and environmental puzzles

Begin with walking, dodge, stairs/decks, doors and a small common interaction set: lever, carry/place, push where authored, break a marked obstruction. Use chapter machinery for local puzzles. Avoid fourteen character-key locks and an unrestricted physics system.

Pendle might recognise a governor's function in dialogue, and Tuff might have a different interaction animation at basalt, but the main route must remain completable with any available fighter. Alternate character methods can save a step or reveal a flavour detail without monopolising a necessary reward. If a traversal upgrade becomes essential later, make it a shared tool and retrofit only deliberate locations, not every old prop.

## 4. A story whose chapters do different things

Keep the starfall and the Company, but make the campaign's questions evolve. Act 1 asks how to restore ordinary life. Act 2 asks why the same shard-powered machinery appears in unrelated places. Act 3 asks what the Company knew, who depends on its power, and how to stop extraction without abandoning those people. Act 4 resolves the source of the fracture and the town's role in repairing it.

The Company will be more convincing if its power initially solves a real problem: restarting pumps, running trains or lighting crowded districts. Show ordinary engineers and residents with conflicting interests. The answer need not be an elaborate morality simulation. A repaired local alternative, a rescued worker and evidence of a deliberate cover-up can make the conflict concrete. A final supernatural threat should emerge from visible earlier evidence so it does not absolve the Company's decisions or replace the human story at the last minute.

Differentiate small stable Glint fragments from the dangerous great shards in the fiction. Otherwise spending fallen-moon currency while recovering the moon's essential pieces creates an avoidable question. A brief physical distinction is enough; it need not become a new resource type.

| Chapter | Proposed local problem and playable shape | What changes afterwards |
| --- | --- | --- |
| Valley/woodland | Restore a practical route to the smith; the Undercroft reveals what a shard does to a familiar animal. Teach space, recovery and dodge. | Forge working, one household home, first light at the lantern. |
| Frostline | Reach an isolated bothy by a ridge loop; ice-cave passages alternate exposure with sheltered fighting. Rescue rather than a second camp clearance story. | A safe route over the col, training-yard help, Tam's place in town. |
| Brackens | Read tracks and clear the wolves' routes so a scattered flock can return. The finale is pack positioning, not a slower Frostline boss. | Fold/loom, visible sheep, a changed village green. |
| Cogsworth | Enter a functioning but unsafe foundry; shut down its linked machines in a chosen order. Find the first clear Company evidence. | Workshop, rail repair and Pendle; trial a firearm before the boss that tests it. |
| Lull | Recover a seized barge and reopen the swing bridge. Use linked banks, mooring points and cover, without a separate boat-driving system. | Mill/kitchen and a credible freight route home. |
| Tidebloom | Trace disrupted water through springs and basalt channels; small authored flow changes connect exploration and combat. | Menagerie/greenhouse, Tuff and a changed cove/headwaters. |
| Sunstone | Restore the oasis supply around the drill. Follow the pipework and dispute over water, rather than find another key in a random chest. | Irrigation, traders returning and evidence that the harm was foreseeable. |
| Fire country | Enter a forge under pressure to supply the Company; reach and free the dragon without treating it as an evil creature to kill. | Forge/glasswork craft, Ashe, a visible dragon return later. |
| Neon | Use the courier's ground-level routes and tower service paths to expose the system that links the earlier chapters. | Refugee households, radio lookout, Nix and access to the launch route. |
| Halcyon | Follow the extraction chain to its origin; reroute a few fixed gravity/magnetic mechanisms, with Bunk's disc language foreshadowed. | The launch/lander route and the final evidence, rather than another town-service grind. |
| Lumen | Recombine earlier spatial/combat ideas in a strange but readable place. Mote's role makes the circle's function clear. | A mended moon and an inhabited Crossroads epilogue. |

These are chapter briefs using the existing geography, not eleven newly assigned dungeons. Each needs its own local cast, conflict and silhouette. A shared enemy role or puzzle component does not require a repeated quest sequence.

Keep essential recruitment on the story route if all fourteen are required for the circle. Better still, let the principal story resolve through its required deeds and use the fully lit fourteen-stone circle for a richer community epilogue. The two unchosen starters cannot be called optional side quests and secretly become a last-minute completion gate. This needs an explicit decision in the vision.

### NPCs, relationships and choices

Start with a few residents who recur at several meaningful beats. Give each a want, a practical role, a recognisable animation and a relationship with another resident. The smith might prioritise the mill's repair before upgrading their own chimney; the newcomer from Cogsworth might have to work with a local craftsperson whose workshop was damaged. A resident becomes memorable through a specific problem and response, not a three-part quest quota.

Use brief, optional homecoming scenes when something changes, then context lines and visible behaviour. Prioritise current quest, recent major event and personal relationship over generic chatter. Do not replay the same sympathetic line after every defeat.

Village relationships can develop through completed shared tasks, conversations and displays of found objects. Avoid compulsory daily gifts, friendship decay or a second experience bar for every resident. Romance, extensive schedules and minigame careers are outside the present design.

Keep choices small enough to finish well: who receives a recovered machine, which town fixture to restore first, or how to resolve a resident disagreement. Let the outcome change a prop, service order or later line. Required combat power remains obtainable either way. Two authored outcomes with one later acknowledgement are more convincing than numerous dialogue choices without consequences.

## 5. Combat, enemies and dungeons

Retain the previous fourteen-kit proposal, and revise the draft's universal-weapon rule around it. The everyday action should establish the character. Keep consistent button roles and teach the differences by fighting, rather than add an instructional page for each recruit.

| Folk | The ordinary decision that distinguishes the kit |
| --- | --- |
| Bramble | Commit to a precise bow opening, then reposition or sweep close pressure away. |
| Puffcap | Place a pod ahead of enemy movement and choose when to burst it. |
| Velvet | Create a short flank with needles, movement and a readable decoy. |
| Cairn | Use stone fists and a charged rock to break posture and open space. |
| Pendle | Spend a visible revolver cylinder on deliberate shots and choose a safe reload. |
| Puddle | Place a harpoon line, pull or pin a small foe, then keep a safe working distance. |
| Mirra | Place a water seal and align the next wave through it; remain useful alone. |
| Ashe | Build heat in close combat and choose when to release a flame strike. |
| Nix | Track with a laser while managing exposure and heat. |
| Tally | Herd a pack into a lane before spending a heavy bell/crook attack. |
| Tam | Read a blow, brace/counter and follow with an ice-axe or crossbow opening. |
| Tuff | Place a committed basalt impact; later choose lava control or physical fragmentation. |
| Bunk | Align the outward and returning path of a magnetic disc. |
| Mote | Place visible star marks and choose a focused or distributed detonation. |

Children of Morta's lead designer explicitly connects fighting styles to character personalities [S2]. The relevant inference is identity in repeated decisions, not importing its roster fatigue or progression system.

Keep golem roles separate: Cairn is posture/guard control and Tuff is placed impact/volcanic control. Tam's defining action should be an active brace rather than a second copy of the familiar's death save. Pendle can have a western gun rhythm in Cogsworth's brass idiom. New regions broaden available tactics without turning all characters into rifle carriers.

### Enemy ecology

Use a few common behavioural primitives, but combine them with a regional condition and a social/ecological role. A wolf circles with its pack, a foundry guard holds a machine lane, a Company shooter relocates between cover. They should change what the player reads, not merely wear different textures.

Teach one new threat alone, combine it with one familiar threat, then use the combination in a meaningful location. A first shooter needs space and visible projectiles. A later shield-and-shooter pairing asks for flanking, posture pressure or placed damage. Every kit must have a workable answer; no mandatory element or random resistance roll should nullify a character.

Attack tokens are a starting scheduler, not proof of fairness. Count outstanding dangerous projectiles, persistent lava/pods, summons and forced movement when allocating new pressure. At least one escape lane must remain visible and reachable. Shots cannot originate beyond the relevant camera view merely because an edge indicator exists. Clutter, roof occlusion and the touch HUD consume the same readability budget as enemy count.

For control effects, specify the boss-resistant result: reduced displacement becomes posture pressure; a root becomes a brief slow or vulnerability opportunity. Do not make boss immunity erase half a kit. Cap chain count, persistent patches, marks and summons before producing their final effects.

### Dungeon shape

Use an authored loop: visible goal, simple introduction, fork with an optional reward, combined encounter, shortcut to the checkpoint, final test. Vary this structure after it is established. A short dungeon can deliver one strong idea without a three-floor quota. Team Cherry's map-development account supports blocking out meaningful routes and connections before dressing rooms, rather than assuming procedural assembly will preserve them [S12].

Examples: the Undercroft wraps thorned rooms around a shaft whose lower chamber is visible early; the foundry puts the boss behind the machine being stopped, with two branches that disable different hazards; the water chapter shows a dry channel before a lever fills it, creating a return shortcut. Safe rooms and doors must make sense as architecture, and re-entry must not repeat a claimed unique reward.

Bosses need a clear silhouette, two or three readable attack ideas and a vulnerability that each kit can exploit differently. Add a phase only when it changes a decision. Give the first full boss one environmental reaction and a visible post-fight state. Reward arrives once; practising a phase or rematch does not duplicate campaign rewards.

### Familiar partnership

Keep the familiar outside combat collision, invulnerable and visually separated from ground telegraphs. Its point, save and celebration should be legible even when effects are muted. Passive support must be useful for ordinary play, not an invisible percentage on a menu.

Prototype the draft's skill-only burst charge against a baseline combat charge plus skill bonuses. A weak-point hit or precise dodge can give a larger reward without preventing the player who needs help from using the partner at all. This comparison is not settled by document scores. Meals can offer a modest starting advantage without becoming a mandatory pre-expedition checklist.

## 6. Progression and loot that preserve character identity

Separate campaign advancement, build choices and optional mastery. Shared progression keeps recruits usable. A new recruit arrives with a clear recommended build and an immediate training opportunity; the player can change it later. Do not ask someone to process twenty-nine perk offers before trying Nix.

For initial implementation, give each test kit its defining move immediately, one early meaningful branch and one later evolution. Expand after the choices demonstrably alter play. The long-term shared-level target can remain 30, but fourteen pools of roughly 24 perks need a design, UI and interaction budget before being promised as finished content. Free respec should restore chosen builds, not secretly reroll endless random offers.

Loot should improve or bend a kit, not replace it. A named basalt core could trade Tuff's splitting rock for a small lava impact; Pendle's cylinder component could reward a full reload or a controlled single-shot rhythm; Mirra's focus could extend a seal's directional reach. These are authored effects, not validated balance values.

Use compatible equipment families with retained character loadouts. Shared charms and materials keep most rewards relevant. Show compatibility plainly. Give major milestones a guaranteed useful choice for the active character, plus clearly labelled items for other owned folk. Recruits have a functional baseline kit without depending on a drop.

Start with a handful of readable item qualities and a few effects. Five rarities, twelve affixes, mods, rerolls and separate gear levels can follow only where they create useful decisions. A rarity colour cannot substitute for the question: what does this change about my next fight? If affix replacement is introduced, begin with a visible choice at a fixed known cost rather than repeated rising-cost random rolls.

The proposed sixteen-item satchel is likely restrictive across fourteen character loadouts. Test it with actual drops before drawing final inventory UI. Equipped items should leave the general bag; named rewards should be protected. A full bag must not destroy a quest reward or force immediate salvage. A return chest or clearly held overflow at the checkpoint can solve that without adding a bag-packing minigame.

Automatic comparison should show relevant behaviour, compatibility and one or two numbers. A single up-arrow or DPS value cannot rank a piercing bolt against a stronger single hit. Let the player inspect details, mark a favourite and bulk salvage ordinary items. Avoid a modal for every defeated enemy's drop.

### Economy and campaign balance

Keep Glint, general scrap and the useful regional materials. Do not give each character a private currency. Main-story income should pay for required route repairs and service unlocks and an adequate active kit, while leaving meaningful choices over optional improvements. Travel itself remains free. If a favourite upgrade uses the same scarce material as the required bridge, reserve or separately award the bridge cost; otherwise the next objective becomes a farming correction for an uninformed earlier choice.

Define a chapter ledger before tuning formulas: guaranteed quest/chest income, expected incidental income, mandatory service costs, affordable build upgrades, consumable baseline and discretionary remainder. Test a main-route player, a curious player and a player with repeated defeats. These are scenarios, not assumptions about observed players.

Required progression must not depend on random salvage or returning to an obsolete region for its one material. Later recipes can accept a current substitute or the stall can supply older materials at a predictable price. Forge upgrades for favourites should remain affordable against replacement drops.

Do not restart the old C40 economy assignment. Its sleep-era pacing work remains on hold. A new campaign simulation should follow agreed combat, rewards and excursion interfaces and use a separate explicit assignment.

Keep defeat a slight setback, as Matt requested. The draft's non-compounding cache is a reasonable candidate, but settle where currency banks and show the amount exposed. A cache must be reachable after a boss gate or terrain change. Boss learning should remain free under the proposed checkpoint protection. Gear, recruitment and the restored town remain intact.

## 7. Crossroads as a lived-in home

The town should grow in three connected layers: physical restoration, functional services and relationships. A working forge is a mechanical gain; smoke from its chimney, its owner at work and a neighbour using the square make that gain visible. A new service does not require a separate compulsory maintenance system. Moonlighter's creator describes decisions in each half referring back to the other [S6]. Cult of the Lamb's designer describes removing busywork and simplifying each half of the combined game [S7]. The inference here is to connect useful decisions rather than reproduce either game's management system.

Keep the seven-district plan as spatial identity rather than seven simultaneous menus. The square offers essential services close together; the terrace is personal space; the green provides training and community; the halt road records new arrivals; Millside carries food and water; the harbour road shows later industry. Natural routes should let a player reach the forge and leave again quickly, while optional alleys invite lingering.

For the first complete loop, focus on the forge, stash, basic recovery, one crop/meal connection and training. Other buildings can already be visible as homes or future lots. A cottage, library wing, greenhouse or mill need not introduce an independent subsystem at first appearance.

Make each arrival a small event: luggage at the platform, a temporary workbench, then a completed service and a changed routine. Have newcomers interact with existing villagers. Use a valley material palette with one recognisable imported feature, as the draft already proposes, so the town records the journey without becoming disconnected themed kiosks.

Give the player a limited choice over repair order after essentials are secured. Allow hut rooms, exterior details, garden layout and keepsakes to express taste. Display a found object and its short provenance rather than convert it into a combat buff. Decorations retain no mechanical stats and cannot block a road, door, character route or defence pad. Preview, rotate where authored, undo and store should be straightforward.

Use a few activity anchors for residents rather than an intricate schedule simulation. Let work, gathering on the green and homecoming scenes follow an explicit active-world phase or story beat. Essential services remain available when their owner strolls. Day, night and weather can change the atmosphere without creating appointments, waiting requirements or a missed opportunity while the game is closed.

### Crops and meals

Keep growth tied to completed play rather than elapsed real time. Define a productive outing once: a saved expedition with a meaningful objective/combat receipt, settled once at home. Leaving the gate and returning, loading a save or repeating a callback must not advance crops or repairs. The exact qualifying events belong in one agreed contract.

Begin with a small plot set, one familiar regional seed and two meal choices. A sweetroot meal could support survivability; an ember recipe could support a committed attack style later. Use finite, legible effects rather than making every meal a stackable optimisation layer. Include a free baseline recovery route so food is an advantage, not the price of retrying a boss.

Offer harvest/replant in batches. Remove compulsory repeated watering clicks; if watering stays, make it an occasional optional action with an honest effect. Skipping an optional growth boost does have an opportunity cost, so do not describe it as mechanically consequence-free. There is no wilting, spoilage or offline loss.

Resolve seasons before drawing crop-state variants. Recommended: story seasons change the look and available recipes/seeds, while already planted essential crops keep growing. The greenhouse offers variety rather than rescuing a player from a compulsory winter supply lock. Post-game seasonal turns need a qualifying outing count, not raw doorway crossings.

## 8. Village defence without making home an obligation

Keep the prepared-defence idea: inspect the threat, place a small set of pieces on fixed pads, then fight using the normal character controls. The village provides the terrain and visible stakes. The player should not have to learn a second resource economy, command followers and manually reload towers during the same fight.

The first defence prototype needs three functions: block/delay, focus a lane and control a group. Use one objective and a few waves on a clearly readable approach. New defence art can follow later chapters, but do not start with thirteen tower systems and all fourteen automated champion kits. Stationary champion appearances can begin as a limited scripted support effect, subject to the same threat and visual limits as the player.

Story sieges should happen at a named story beat after ordinary combat and homecoming are learnt. Optional raids should stay pending until the player chooses defence or attacks the camp. The current two-postponement rule remains a recommendation needing resolution; automatic combat on entering town is especially risky for a loop that depends on enjoying homecoming. Always retain stash, recovery, essential services, save and exit before committing.

Keep the visible camp and one-pending-raid limit. Distinguish a raid notification from immediate danger. Clearing a camp and defending must settle the same event so both routes cannot pay twice. Do not stack a queue of raids while the player is exploring.

On defeat, damage overlays and a short repair scene can show a consequence without taking away the supplies needed to recover. If a temporary tier reduction survives review, protect established healing/loadout capacity and never trap the player below a required forge tier. The first loss is a teaching event, not a new bill. Nothing occurs while the game is closed.

Once the basic mode is good, vary objectives: hold the lantern, escort households along a short marked route, stop a machine before it establishes a new lane. These reuse normal combat and town geography. Weather should vary atmosphere first; fog must not make attacks unreadable. A no-raid/calm-town setting can retain story sieges and ordinary progression.

## 9. Arenas, optional mastery and the end of the story

Use three complementary challenge types: readable rival duels, mixed-role encounters, and spatial/precision trials. Introduce a rival's identity in their region before a rematch. A rival uses the same honest tells and recovery rules as other actors, not invisible input-reading.

Score several forms of mastery: clean evasion, breaking guards, controlling a lane or efficient use of a kit. Raw timed killing can heavily favour burst damage. Compare leaderboards only under clearly defined loadout/rules later, if that feature is wanted. Main progression should not require a prescribed hero or an optional high rank.

Replace blanket melee-only trials where a caster or laser character has no meaningful melee kit. A trial can test close-range positioning, or provide a declared temporary training loadout, but should not quietly invalidate a favourite character. Rewards should favour sidegrades, visible trophies and cosmetics, so the strongest equipment is not required to win the challenge that grants it.

After the ending, let Crossroads remain repaired. Explain repeatable threats as remaining extraction sites, unsettled pockets or arena reconstructions; do not repeatedly crack the moon again. Start with the existing rival circuit, remixed bounties and unfinished personal stories. A procedural deep-shard dungeon, infinite rarity chase and seasonal content service are separate production commitments, not necessary to finish this game.

The ending should include the town functioning without intervention: trains running, households meeting, the mill turning, the familiar at home and the moon visibly repaired. Let the player walk through it. That is the payoff to restoration.

## 10. Controls, camera, sound and interruption

Use action-based bindings shared by all kits. Primary and alternate do consistent jobs even when one is a punch and another a beam. Hold-to-repeat, charge, reload and aimed placement cannot all silently share the same touch gesture. Test the four contrasting kits on mouse, controller and touch before the final HUD is drawn. Pause for inventory/build decisions in the single-player game.

Keep Story, Normal and Hard as comprehensible presets, with separate controls for incoming damage, tell duration and aim assistance where useful. Changes preserve campaign progress and ordinary loot. Optional challenge ranks can retain clearly stated conditions without locking essential power behind them. Supergiant's account supports flexibility and permanent progression alongside action challenge [S5].

Keep UI scale independent from world zoom. Treat roughly 320 by 180 world pixels as a framing target, then define the smallest supported combat-safe rectangle after safe areas and touch controls. The draft's own viewport table varies by device. Compose encounters for the agreed safe view, keep active threats inside it, and use extra peripheral scenery on wider views rather than granting unseen enemies permission to attack.

Reserve strong contrast and distinct shapes for enemy tells, player location, dangerous projectiles and interaction cues. Detailed ground can remain quieter beneath a fight. Roofs and foreground foliage need a consistent fade/outline rule. Loot sparkles, familiar effects and friendly lava cannot borrow the same visual language as incoming danger.

Reduced motion should remove cosmetic shake, afterimages, bobbing and decorative loops while preserving essential locomotion, wind-ups, hit timing and projectile travel. Separate the cosmetic removal from a gameplay slow-motion assist. The old animation spec's frozen translation/one-frame rule belongs to the previous presentation and is unsuitable as an action-combat requirement. Microsoft explicitly distinguishes core gameplay movement from ancillary motion [S3].

### Sound as information and place

Retain warm material sounds without limiting every action to a pentatonic notification. Prioritise danger wind-up, committed projectile, hit/guard response, low health/recovery, reload/resource feedback, interaction and ambience in that order as appropriate. The same tell should keep its core sound across variants. Give stone, brass, water, heat and electricity different attack textures.

Use a small regional motif/instrument palette and ambient bed, with controlled transitions into encounters and back to quiet. Crossroads can acquire a new layer or activity sound as a service returns. A forge, mill and station should sound like working places, not a continuous chord of reward cues. Darren Korb's account of music belonging to a place, combat stems and a concluding musical response supports a small state-based audio prototype, without requiring Hades' full soundtrack or middleware [S13].

Sound must have visual equivalents. Mute and reduced stimulation must preserve the information in telegraphs and HUD. The old global cue debounce can swallow closely spaced attack tells, so essential threat cues need their own priority/voice rules. Do not claim latency, simultaneous mixing or phone audio quality from file checks; listen to busy fights on representative hardware.

### Saving and sessions

Pause simulation and clear held inputs on blur/background. Resume without a large elapsed-time step, an accidental attack or a held movement command. Save rewards and meaningful decisions at durable boundaries; the player can stop without being punished for leaving.

Picked-up loot, cleared enemies, opened chests and quest rewards need stable identities and receipts. If a room restarts after closing, previously claimed rewards cannot pay again. Checkpoints, currency banking and excursion settlement are distinct events even if one waystone triggers several together.

Preserve old player progress in a recoverable, versioned migration. Inactive legacy systems can be retained as history. A development slice cap must not cap a real saved level at five. Preserve original balances, identity, collected items and unknown save fields; settle or safely retire old callbacks once. No reset follows from the design pivot.

## 11. What Saturday's drawing and animation need

World lanes can continue stable terrain, buildings, landmarks, materials and regional ambience. Before final camps, siege lanes and combat animation, agree the following small production packet.

| Needed decision/data | Why art needs it | Initial deliverable |
| --- | --- | --- |
| Combat-safe view and scale units | Determines arena size, tell visibility and useful detail. | One woodland view and one town view with HUD/phone occlusion overlays. |
| Actor/cover/deck collision | A dodge or rock must not cross a wall simply because a sprite looks low. | Ground footprint, clearance, low/high cover and deck/occlusion masks. |
| Four kit move contracts | Prevents drawing generic attacks that will be discarded. | Tuff impact, Pendle shot/reload, Nix track/vent, Puffcap cast/place/trigger in temporary frames first. |
| Hit and projectile event anchors | Visual frames and damage must agree. | Foot, hand/muzzle, active interval, recovery/cancel data and effect spawn points. |
| Direction policy | The current E/W-only card-fight set cannot support free aim. | At least cardinal locomotion and aimed-action proof, including north/south; choose authored diagonal support after seeing it. |
| Enemy tells and release states | Every fight depends on understanding before impact. | Three small enemy roles, one elite and one boss pattern with clear anticipation/recovery. |
| Town stage plan | Routes and story blocking must survive restoration. | Broken, first restored service and thriving sample; reusable damage overlays with prop swaps and lights. |
| Familiar support states | Prevents accidentally creating another full fighter roster. | Follow, point, save, celebrate and one tested family effect. |
| Effect/audio priority | Prevents final art from hiding incoming danger. | One busy fight with marks, loot, familiar support and a danger cue together. |

All action manifests need a state, facing, duration, foot pivot, effect anchor, ground footprint and relevant event marker. The combat simulation determines hit timing; the animation expresses it. A wind-up shortened by animation must not covertly change balance. A cosmetic setting must not remove the information used to dodge. The Children of Morta team's postmortem describes rework from fluid production boundaries and confusing systems understood mainly by their creators [S14]. This makes a tested action contract and outside play-test especially useful before the next animation batch.

Keep upper-left lighting and authored west facings under the house standard. Work with compact sheets and load only what the scene needs. Mark decorative loops as local to an active scene. Do not draw fourteen complete production fight sets before the four temporary styles demonstrate the required differences. This does not prevent other lanes from continuing coherent world scenery.

## 12. Prove the game in one complete slice

Suggested delivery order, not new assignments:

1. Settle viewport, input, movement/collision and combat-event contracts. Run the existing woodland prototype as a reference, then prove the production implementation.
2. In a separate combat test scene, compare Tuff, Pendle, Nix and Puffcap against the same camp and boss at matched progression. Let later recruits be tested here without changing story order.
3. Build the valley opening with the existing starters, Mossling, one camp, the Undercroft/Thornback, a meaningful reward and one restored service with a returning household.
4. Connect that service to a changed next fight. Add a small crop/meal example, a keepsake placed at home and a shortcut or clear next journey. Observe the complete expedition/homecoming loop.
5. Add one prepared siege only after that loop works. Then validate a second region, including a new combat idea and a new homecoming, before replicating the structure across the continent.

An initial 60–90 minute complete loop is a play-test target, not a schedule estimate or a requirement to pad play. The draft's 25–35 hour whole-game target, eleven regions at 3–6 hours each, and large quest/perk totals are not mutually demonstrated. Keep all eleven regions as the world target, but measure actual content time before committing to campaign length.

| Question to test | Evidence to collect |
| --- | --- |
| Does the fighting feel different? | Players can explain the four kits' distinct decisions and use them without waiting helplessly on cooldowns. |
| Is incoming danger readable? | Players can identify the cause of a loss and a usable escape; essential tells survive touch HUD, effects and reduced motion. |
| Is every kit viable? | Each handles close pressure, a shooter, a shield and the boss without a forced character swap. |
| Does loot matter? | Players understand a useful reward and can say how it changes their next attempt. |
| Does the village matter? | Players notice the restored service/household and use a new option on the next excursion. |
| Is home enjoyable? | Players voluntarily explore or decorate without being driven back out by chores or raid pressure. |
| Can play stop safely? | Pause/resume and close/reload preserve one reward/quest/crop outcome and clear stale inputs. |
| Does it run in a busy scene? | Measured frame time, memory and input responsiveness with the intended actors/projectiles/effects, plus an actual phone check before phone claims. |

Use small observed sessions with people who did not write the design. Grade disagreement and failure reports as information, not a request to make every number identical. Do not invent target frame-time or completion metrics after seeing the result.

## 13. Decisions to reconcile in the next vision revision

These have consequences beyond local tuning and should be settled before affected production work. Recommendations are supplied so work can advance; none is asserted as a new Matt decision.

| Draft issue | Recommended resolution |
| --- | --- |
| Universal weapons versus character-defining ordinary combat | Compatible kit equipment, shared charms/materials and retained per-character loadouts. |
| Later ranged-led acts versus favourite-character viability | Encounters broaden; early melee and magic remain complete viable styles. |
| All fourteen required at finale versus optional starters | Required recruits on the main path, or optional full-circle epilogue without a surprise finale gate. |
| Forced raid after two postponements | Pending raid until explicit defence/camp attack; preserve normal town access. |
| Winter crop lock versus seasons changing no mechanics | Essential planted crops continue; season changes variety and appearance. |
| Skill-only familiar charge | Compare it with baseline meaningful-combat charge plus skill bonus. |
| Random perk offers and late-recruit backlog | Curated recommended build, meaningful milestones, saved choices and free respec. |
| Five rarities/large affix pool before a fun loop | Small authored reward set first, expand by observed decisions. |
| Old E/W fight animation/reduced-motion rules | Action states and aim facings with cosmetic motion separated from essential combat cues. |
| Save migration capped at level five | Lossless legacy preservation and explicitly mapped/separate campaign progression. |
| Roughly fixed view versus variable viewport table | One executable scale/usable-view contract; author fights for the supported safe view. |
| Many content counts and mutually inconsistent duration targets | Validate a finished chapter and extrapolate transparently. |

## Sources and limits

The following sources support specific comparisons. They are developer statements or official guidance. Their systems are not treated as tested prescriptions for this game. All recommendations and example content above remain proposals; no new gameplay, balance, performance or player-preference result is claimed.

- **S1.** [Pixpil's Tommo Zhou on Eastward's art, visibility, elevation and worldbuilding](https://www.gamedeveloper.com/art/eastward-s-creators-share-insights-on-making-pixel-art-adventures), developer interview, 11 October 2021.
- **S2.** [Dead Mage lead designer Aryan Bina on Children of Morta's character classes](https://news.xbox.com/en-us/2019/09/20/family-personalities-character-classes-children-of-morta/), developer-authored, 20 September 2019.
- **S3.** [Microsoft XAG 117: visual distractions and motion settings](https://learn.microsoft.com/en-us/xbox/accessibility/xbox-accessibility-guidelines/117), official guidance, accessed 22 October 2026.
- **S4.** [Digital Sun/11 bit: Moonlighter 2 announcement](https://11bitstudios.com/moonlighter-2-is-revealed/), publisher/developer material, 5 December 2024. Connects expedition rewards, local businesses and gear; does not establish that a particular item/town economy is balanced.
- **S5.** [Supergiant: Hades FAQ](https://www.supergiantgames.com/blog/hades-faq/), official developer material, accessed 22 October 2026. Supports flexible challenge, permanent progression and returning character interaction; this proposal does not import a roguelike reset structure.
- **S6.** [Moonlighter director Javier Gimenez on linking the shop and dungeon](https://www.pushsquare.com/news/2018/05/interview_talking_shop_with_action_rpg_moonlighters_developer), direct developer interview, 9 May 2018.
- **S7.** [Cult of the Lamb designer Jay Armstrong on combining action and management](https://www.gamedeveloper.com/design/interview-corralling-the-inherent-cuteness-of-cult-of-the-lamb), direct developer interview, 7 September 2022.
- **S8.** [Radical Fish: CrossCode Update 47, combat finishers](https://www.radicalfishgames.com/?p=2061), developer diary, 27 May 2014. A concrete example of recovery giving a repeated attack rhythm and an opponent an opening, rather than a prescribed combo length.
- **S9.** [Radical Fish: CrossCode DevLog 62, readable effects and hold/toggle options](https://www.radicalfishgames.com/?p=2888), developer diary, 2 February 2015.
- **S10.** [Team Cherry on Pharloom's ecosystem and visible power structures](https://www.acmi.net.au/stories-and-ideas/from-ludum-dare-to-pharloom/), direct developer interview, ACMI, 5 September 2025.
- **S11.** [Tunic's developers on discoveries that teach world rules](https://www.gamedeveloper.com/design/designing-content-for-no-one-an-interview-with-the-team-behind-tunic), direct developer interview, 15 March 2022.
- **S12.** [Team Cherry on the development of Hollow Knight's map](https://www.pcgamer.com/how-to-design-a-great-metroidvania-map/), direct developer interview. Supports authored meaningful connections, not wholesale adoption of its Metroidvania gates.
- **S13.** [Darren Korb: The Sound of Hades](https://gameplay.co/hades-game-music-sound-design-darren-korb-supergiant-games/), direct interview and transcript, 24 December 2020.
- **S14.** [Dead Mage team lead Amir H. Fassihi: Children of Morta postmortem](https://www.gamedeveloper.com/design/postmortem-children-of-morta), developer-authored, 2 November 2020.

Validation of this report: current-head/document comparison, source inspection and primary-source research. Not run: an integrated new-RPG play-test, balance validation, final art review, performance measurement or native/device testing. The repository change is Markdown only and remains a draft for review.
