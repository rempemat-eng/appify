# The essence of NapAttack, and who you play as

> **Superseded 21 Oct by [game-design.md](game-design.md)** in section 1 (the essence and the five rest pillars), the rest rituals and the turn-based mechanics (now its section 4.3); the roster, section 2's structure and the art notes still stand.

Matt, 20 Oct (London): "think deeply what sort of world we are creating and how the could fit in. perhaps there could be different characters that fit the different towns ... make the make sense and give them functionality. think of the cost and benefit of each new character to the game. develop the essence of the game"; "think about what sorts of characters would fit into the world already built". Earlier the same evening: choose one of a few characters at the start, unlock more later, abilities in fights, ways to upgrade them, more detail than his reference sheet.

**Status.** The structure (section 2) is decided: Matt chose it on 20 Oct, 23:20. The roster, mechanics and numbers are a proposal, built the way Matt asked for content questions: three independent drafts (regional folk; the residents you help become playable; a lean cast of town archetypes), scored by three independent graders (player experience, production and cost, world and story). Totals out of 180: the residents draft 136, the lean draft 135, the regional draft 112. This page is the residents draft as the base with the graders' best grafts from the other two. Nothing here changes a game rule until it is built and Matt has seen it; fights follow `fights.md` (in progress).

## 1. The essence

NapAttack is a cosy adventure you play by putting your phone down. Everything good in it comes back from time away: Dream Dust, a home that grows, new friends, new roads. Opening it is a short visit: see what your rest changed, walk somewhere, spar once, place one thing, and put the phone down again.

The world tells the same story at the scale of a continent: a journey from rest to screens and back to sleep. Near home everything is green and slow; along the line places run on schedules, drought, burnout and glare, up to Neon Harbour, where Doomscroll Dave never sleeps; beyond it, a quiet moon. Every region has someone who has lost their balance in that region's way. You never fix them with chores: you rest near them, their story moves on, and in its last chapter they find their balance again.

The cast says the same thing in fight terms: **every folk turns stillness into strength in their own trade's way.** A guard that holds, a breath before the arrow, a lamp kept low, a clock a minute slow on purpose, a fire banked before it burns out.

Five pillars, for every new idea to be checked against:

1. **Rest is the only engine.** Walking, chatting and sparring are how you find and enjoy things, never how you farm them.
2. **Short visits, lasting change.** Nothing to do every day; nothing expires; everything counts up.
3. **Every place has a balance to restore,** and rest restores it.
4. **Kind fights.** Sparring between friends and rivals; no one is beaten into joining you.
5. **A home that grows with you** (`home-base.md`, #146).

## 2. Who you are, and who is with you (decided)

Two choices, never the same one: **who you are** (a folk character) and **who is with you** (your Grassling, or any befriended visitor).

- **The folk** walks the world, naps and fights. It brings the **class**: four signature cards and one passive.
- **The Grassling is your familiar.** It follows a step behind (Eastward's John and Sam), naps curled against you, and in a fight rides on your shoulder, so one fighter stands on the field. It keeps care, mood and hats, the **type** (REST, ROAM or FOCUS: today's matchup, unchanged) and the **rested special**, charged by real time away (built on today's zen, capped). Three specials, one per family, instead of one per folk.
- **One shared level** sets HP and hand size for everyone, as today. Switching folk keeps level, Dream Dust, hats, cards and collection, and never happens during a mission, nap or battle (the companion rules in AGENTS.md, extended to folk).
- **Existing saves** keep their Grassling as the familiar and pick a folk once; nothing is lost.
- Code: rendering and combat identity move from the companion alone (`guardianPlayer`) to the pair; the type stays on the familiar's species. Codex owns the save change.

## 3. How you get them

- **At the start** you hatch a Grassling and choose one of three valley folk. The choice sticks: the other two are not handed over by a story; they join later through the stone circle (below), so the first pick matters.
- **Every other folk is an apprentice.** When a region's resident story ends (chapter 3: rests there on three different days and one long rest, `gameplay-regions.md` G6), the resident stays home, balanced, and their apprentice asks to travel with you. The smith keeps her forge; Dave stays asleep on his bench.
- **Nothing expires, costs Dream Dust or needs a fight win.**
- **Upgrades respect the shared level.** At shared levels 4, 8 and 12 every folk, owned or not, gains a choice between two variants of one signature card, swappable outside fights. A late folk arrives at full strength; nothing is ground twice. Looks come from region outfits (G8) on the head slot.
- **A rest ritual per folk:** a line of their own on the nap screen ("dim the lights", "make tea and sit"). Words only; no stats (AGENTS.md).

## 4. The cast

Heights follow the size guide (an adult is 25 px). Every folk is drawn at more detail than Matt's reference sheet at the same height (its humans are about 27 px with about three flat tones per material): four to five tones per material, clean clusters, material-specific shading.

| Folk                                                                                                                                                     | Who, and why there                                                                                                                                         | Class and mechanic (proposal)                                                                                                                           | Unlock                                 | Ritual                          | Wave                  |
| -------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------- | ------------------------------- | --------------------- |
| **Bramble**, fox-folk forester with a short bow and a sky-blue cape, 24 px                                                                               | Works the woodland's forester's yard; knows every path in the valley                                                                                       | Striker. **Steady:** end a turn with energy left to gain Aim (up to 3); the next loosed arrow spends it for more damage                                 | starter                                | "a short stroll"                | launch                |
| **Puffcap**, mushroom sprite under a violet nap-cap, 17 px                                                                                               | Tends the sleepy glades round the woodland's spring pool                                                                                                   | Soother. **Drowsy:** spores stack on the foe; at three it dozes through one action (once a fight); small heals over time                                | starter                                | "find a soft spot"              | launch                |
| **Velvet**, moth-folk keeper of the Driftwood lighthouse, dusk wings as a cloak, shuttered lamp, 23 px                                                   | The lighthouse "keeps the night dark for the sleepers": a moth who tends a light so it stays low                                                           | Shade. **Dim:** each turn she holds back an attack she gains Dusk, spent to soften the foe's next card by a third                                       | starter                                | "dim the lights"                | launch                |
| **Cairn**, a standing stone of the woodland circle that woke, moss and a fern behind one ear, 29 px                                                      | The stone circle is the valley's magic place (Matt: "something magic related")                                                                             | Guardian. **Bedrock:** his guard survives one extra hit; a special stance turns held guard into a shoulder charge                                       | the gardener's story, chapter 3 (home) | "sit still till the moss grows" | with the valley       |
| **Pendle**, brass station automaton, its head a station clock dial running a minute behind, a pendulum swinging in a glass belly, conductor's cap, 26 px | Built to call Cogsworth's trains to the second; the tinkerer set it a minute slow and it came to like the gap (it replaces the canal's old automaton prop) | Caster. **A Minute Slow:** set one card on the clock; it lands next turn at half again its strength                                                     | the tinkerer's story                   | "phone face down"               | with Cogsworth        |
| **Puddle**, frog in fisherman's oilskins and red wellies, 18 px                                                                                          | Apprentice of the bargee on the Lull, whose old horse learns to rest                                                                                       | Trickster. **Tide:** ebb and flow alternate each turn between a soak (the foe's next card costs one more) and a splash                                  | the bargee's story                     | "listen to running water"       | with the Lull         |
| **Mirra**, gecko water-diviner with a forked rod and a wide hat, 22 px                                                                                   | Apprentice of the oasis trader who digs out the buried outlet so the creek runs again                                                                      | Support. **Seep:** her flask fills a drop on each still turn and is poured as heals or a cleanse; it never guards (that is Cairn's)                     | the trader's story                     | "a glass of water, slowly"      | with Sunstone         |
| **Ashe**, drake-folk knight in dented plate, a bell on her belt, ember scales that grey as she rests, 26 px                                              | Keeper of Hearthold's bedtime bell; apprentice of the smith who learns to bank the forge                                                                   | Bruiser. **Banked fire:** heat builds each turn and hits harder; when the bell tolls at three heat she must rest one turn (and heals), or she burns out | the smith's story                      | "a warm bath"                   | with the fire country |
| **Nix**, courier android in a hooded reflective jacket and a boxy delivery pack, a cracked face-screen showing a sleep glyph, 25 px                      | Neon Harbour's 3 a.m. courier who brought Dave his parcels; the night he sleeps, her route ends at his bench (she is the atlas's existing courier)         | Ward. **Do Not Disturb:** a still turn mutes the foe's next trick (a card's extra effect); two in a row reflect it                                      | Dave's story                           | "phone in another room"         | with Neon Harbour     |
| **Mote**, a star of Dream Dust in a nightcap, floats, 15 px                                                                                              | Lumen's Dream Grove, the journey's end                                                                                                                     | Wildcard, never the strongest. **Dream:** once a fight, borrow your familiar's special early at half charge                                             | the end of the journey (Lumen)         | "lights out"                    | last                  |

**Fourteen folk, and what the number means (Matt, 23:26: "i think 14 is a good number of total characters. maybe tie that number into the game").** Two independent drafts (the sky, the world) and two independent graders chose this together; both drafts arrived at the same symbol on their own.

- **The symbol.** Fourteen nights take the moon from new to full. Each folk you meet lights one of fourteen stones in the woodland circle and one night of Lumen's moon; the fourteenth makes it full. It counts friends, never days: it never wanes, never times out, follows no real calendar and pays nothing.
- **Where it shows (cheap, no chores):** the select screen is the circle of fourteen stones round a moon, unmet folk dark with a hint ("someone waits at the bothy"); the journal's cast page; on Lumen, fourteen crystal spires round the Dream Grove, lit one by one. No half-moon gate, no moon in every region's sky.
- **One folk for each place on the journey,** simple nature folk first, then the woken and the made:

| Night  | Folk                                         | Home                |
| ------ | -------------------------------------------- | ------------------- |
| 1 to 3 | Bramble, Puffcap, Velvet (starters)          | the valley          |
| 4      | Tally                                        | the Brackens        |
| 5      | Tam                                          | the Frostline       |
| 6      | Puddle                                       | the Lull            |
| 7      | Cairn, the half moon: the first folk to wake | the woodland circle |
| 8      | Pendle, the steampunk automaton              | Cogsworth           |
| 9      | Mirra                                        | Sunstone            |
| 10     | Ashe                                         | the fire country    |
| 11     | Tuff, the second golem                       | the Tidebloom Isles |
| 12     | Nix, the cyberpunk android                   | Neon Harbour        |
| 13     | Bunk, the station robot                      | Halcyon Station     |
| 14     | Mote, the full moon                          | Lumen               |

The number is a label, never a gate: each folk joins when their region's story ends, in whatever order the player rests there. With every region built, a daily rester meets about six in the first month and all fourteen in about two months; in practice each ships with its region's rebuild.

The four added folk:

- **Tally**, lamb of the sheep-folk in a knitted fleece cardigan with a tally stick and a fold bell, 20 px; the drover's apprentice on the Brackens (bringing the flock in at dusk). Herder. **Counting Sheep:** each still turn a sheep hops into the fold (up to 3); next turn each adds a card to her hand (never energy).
- **Tam**, marmot-folk in a bobble hat with a dented kettle on her rucksack, 19 px; the Snow Saddle hut warden's apprentice ("the bothy is always open"). Keeper. **Bothy:** still turns bank Warmth (up to 3); once a fight, a blow that would knock her out finds her curled up at 1 HP, healed by her Warmth. No one else survives a knockout.
- **Tuff**, basalt golem of the isles' dormant volcano, drawn low and wide (about 22 px tall, 30 wide): glossy hexagonal columns, a fringe of sea thrift, a turtle asleep on his back, no moss (that is Cairn's). The naturalist has watched a boulder by the cove move an inch a year. Grower. **Overgrow:** each still turn grows a layer (thrift, frond, flower), each a small lasting boost; a heavy hit knocks the top one off.
- **Bunk**, a barrel-shaped white station robot with magnetic boots, a sleeping bag rolled on its back and a slow-blinking visor, 22 px; built for Halcyon's sleep bay, unlocked by the sleep-bay keeper's story. Cycler. **Sleep Cycle:** a two-stage dial: deep gives a small heal, dream echoes the next card at half; a still turn holds the stage.

Golems are woken by places (Cairn, Tuff); machines are built by people (Pendle, Nix, Bunk). Not folk: the allotments' clockwork gardener (a resident; TICKWREN and Pendle already carry clockwork), a second screen-faced android in Neon (its story folds into Nix's chapter). Cost: about 1,920 frames for all fourteen plus the familiar's perches; if art time runs short, the order above is also the order to stop in, and seven (the starters, Cairn, Pendle, Nix, Mote) still keep the golem and both machine styles.

Three effects that weaken the foe's next card stay apart: Velvet softens damage, Puddle raises cost, Nix mutes tricks, each with its own icon. What a still turn can bank is capped and simulated before numbers are set.

**Not folk, and why.** A folk must bring a fight mechanic no one else has, a town whose trade explains it, and a story that ends in that balance; without the mechanic it is an outfit, without the town a visitor, and a strong look with a ring to stand in is a rival (about a quarter of a folk's cost).

- Dave stays the tutor and is not playable (his last chapter has him asleep for good); his apprentice is Nix, and the moth visitor GLIMMOTH keeps the city.
- The Frostline keeps the hut warden as its ring rival and CAIRNLET as its visitor (so Cairn lives in the woodland, not there).
- The Tidebloom Isles stay the quiet place with no ring; the Brackens' drover is a story.
- Matt's reference sheet, redirected: the kobold is the Cogsworth tinkerer (resident), the dragon-folk knight Ashe, the elf archer joins Bramble's bow, the minotaur becomes Dust Gulch's cowhand rival, the tiefling the Ember forge smith (resident and rival), the wizard the Hearthold library's keeper plus a wizard-hat outfit, the druid the isles' naturalist, the bard plays the park bandstand as a resident, and the plague doctor is cut (sickness does not belong in a game about rest).
- Field skills (abilities that open places) are cut: each needs 6 to 10 spots built in the world and would make switching folk a chore. No folk gates any place.

## 5. Cost and benefit

| Item                              | Cost                                                                                                                                                                                                        |
| --------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| One folk                          | about 134 frames (110 body: four directions with west drawn, idle, walk, nap, react, hit, faint, victory, attack, cast; 24 effects), a portrait, a select card, four cards, a passive, card variants, lines |
| The familiar on the shoulder      | about 40 frames for the three Grasslings, more as visitors are drawn for it                                                                                                                                 |
| Launch (Bramble, Puffcap, Velvet) | about 440 frames; all three exist as exploration art Matt liked; no region story needed                                                                                                                     |
| Everything else                   | one folk with each region's rebuild, Mote last: about 1,480 frames more (about 1,920 in all)                                                                                                                |

What a folk earns: a new way to fight, a reason to finish a region's story (the apprentice), a face for a town, and a reason to choose where to rest. What it does not do: open places, pay more, or need daily play.

## 6. Guard rails

- No time-of-day bonus in fights; the real night is for sleeping.
- Every mechanic that banks something (Aim, Dusk, heat, the delayed card) is simulated against the raid AI before its numbers are set (Codex, after C33).
- Guard stays a simple rule (one extra hit), not a growing number.
- Action denial (Drowsy) is once a fight and never in a friend's raid against an absent player.
- Only residents who become apprentices' masters get redrawn early; the rest follow the asset ledger's redraw order.

## 7. Order of work

1. Production art of the three starters and the familiar on the shoulder (in progress; Cairn, Puddle and Mote are drawn alongside since Matt liked them).
2. The fight system (`fights.md`) maps the classes above onto the card engine.
3. Codex: the save change (folk plus familiar), then the simulation of the mechanics.
4. Each later folk ships with its region's rebuild and its resident's story.
