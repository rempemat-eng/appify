# Brief: NapAttack resident stories (for drafters and graders)

NapAttack is a cosy, mobile-first, top-down pixel-art game (Expo/React Native) whose point is to spend LESS time on the phone: you put the phone down, your character rests, and the rest earns Dream Dust (the one currency) and moves the world on. You play a folk character with a Grassling (a small plant creature) as your familiar; it follows you, naps with you, and says short lowercase lines. The world is a journey from rest (a green home valley) to screens (Neon Harbour, home of Doomscroll Dave, who never sleeps) and back to sleep (a quiet moon, Lumen).

"Every region has someone who has lost their balance in that region's way. You never fix them with chores: you rest near them, their story moves on, and in its last chapter they find their balance again." When a resident's story ends, their APPRENTICE asks to travel with you and becomes a playable folk (14 folk in all; each lights one of fourteen stones round a moon: the fourteenth makes it full). The resident stays home, balanced.

## Matt's rules (hard constraints; a draft that breaks one scores zero on it)

1. Rest is the only engine. Chapters advance ONLY by the player resting at that region's rest spots. Never by a chore, a fetch quest, a fight win, a payment, a daily login or a timer.
2. Count up, never down. Nothing expires, nothing is lost, nothing goes back. A chapter waits however long the player is away. No "come back tomorrow or else", no streaks.
3. No FOMO, no guilt, no shaming, no paywall, no grind. Never say "missed", "late", "failed", "hurry", "only N left", "you should", or imply the player neglected someone. The resident's imbalance is never the player's fault and never gets worse while the player is away.
4. Decorative interactions give nothing and cost nothing. A chapter's lasting world change is presentation (a lamp lit, a bench, a person asleep), never a reward, a price or a new chore.
5. Fights are a separate, kind, Pokémon-style card screen. The ring rival is a friendly sparring partner; the story never needs a fight won. A story may MENTION the ring (an invitation to spar), never require it.
6. No phone-shaming of the player. The game is gently anti-doomscroll through its characters (Dave), not through lectures.
7. Honest: the game cannot see the phone; it counts the time between START and WAKE UP. Never claim the game knows the player slept or stayed off their phone.

## How chapters are triggered (fixed; do not invent other triggers)

- Chapter 1: the first rest at one of the region's rest spots (any length).
- Chapter 2 and 3: each needs one more rest at the region's spots that either ends on a new calendar day or is a long rest (90 minutes or more; a night counts). One chapter per rest at most.
- Each chapter is shown as a short beat in the welcome-back sheet when the player returns ("while you were away ...") and can be re-read in the journal. The player is never required to walk anywhere to receive it.
- Chapter 3 ends with the apprentice asking to come along (a line from the apprentice) and a lasting change in the world.

## Voice

- All in-game lines lowercase, short (max ~90 characters each), plain words, warm, gentle, a little funny. No exclamation-mark spam, no emoji, no lectures, no therapy-speak ("self-care", "mindfulness", "boundaries" are banned words). Show balance through small concrete things: a kettle, a lamp kept low, a clock a minute slow, a forge banked at sunset.
- The companion (the Grassling) speaks in lowercase too; it is curious and kind, never preachy.
- Residents each have a distinct way of talking that fits their trade.
- Dave is the game's comic villain: a never-sleeping scroller, but likeable; his ending has him asleep on a bench, phone face down, for good.

## The eleven stories (region, resident, apprentice, ring rival, key places)

Use only places listed here or in the region briefs (docs/vision/regions/\*.md in /home/claude/appify). Folk descriptions are in /home/claude/appify/docs/vision/cast.md (section 4). Read cast.md and the relevant brief before writing.

| id        | region (opens with)                                               | resident (lost balance)                                                                                                                             | apprentice (folk)                                                                                                                                      | ring rival                                                   | rest spots to use                                                                                                  |
| --------- | ----------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------ |
| valley    | the home valley (start)                                           | the gardener, who never stops tending; the shelter by the green that became a meeting place (an approved story seed)                                | Cairn, a standing stone of the woodland stone circle that wakes (moss, a fern behind one ear)                                                          | Dave is the tutor at the green ring (not this story's rival) | the hut's bed, the spring pool in the woodland, the millpond bench, the bandstand in the park                      |
| brackens  | the Brackens, west moor (start)                                   | the drover, always on the move with his flock and his dog along the Drover's Road; never stops walking                                              | Tally, a lamb of the sheep-folk in a knitted cardigan with a tally stick and a fold bell                                                               | none (no ring)                                               | the shepherd's hut step, the drove well, the bench below the Brackens gap                                          |
| lull      | the Lull plain, Lullford and Gullwick (start)                     | the bargee, whose old barge horse has pulled for years and never rests                                                                              | Puddle, a frog in fisherman's oilskins and red wellies                                                                                                 | none (no ring)                                               | Lullford's quay and mooring, the willows by the oxbow, a boat hauled up at Gullwick                                |
| frostline | the Frostline highlands (W2)                                      | the hut warden of the Snow Saddle bothy ("the bothy is always open. the kettle is always on.") who keeps the bothy for everyone and never sits down | Tam, a marmot-folk in a bobble hat with a dented kettle on her rucksack                                                                                | the hut warden (a snowy clearing by the bothy)               | the bothy's bunk, the Col hut bench, the tarn shore at Snowmelt Lake                                               |
| cogsworth | Cogsworth (W3)                                                    | the tinkerer, who runs every clock to the second                                                                                                    | Pendle, a brass station automaton whose clock-dial head runs a minute behind (the tinkerer sets it slow)                                               | the tinkerer (the plaza)                                     | the allotments' bench warm from the foundry, the narrowboat's cabin, the clock room                                |
| isles     | the Tidebloom Isles (W4)                                          | the naturalist, who counts everything and never just listens                                                                                        | Tuff, a basalt golem of the isles' dormant volcano with sea thrift and a turtle asleep on his back (the boulder by the cove that moves an inch a year) | none (the isles stay the quiet place, no ring)               | a hammock at Lagoon Landing, the rain shelter at the headwaters, the black sand of the cove                        |
| sunstone  | the Sunstone basin: Palm Spring, Dust Gulch, the Lode (W5)        | the oasis trader at Palm Spring; the gulch's creek dried when a dune crept over the pool's outlet (drought, like attention run dry)                 | Mirra, a gecko water-diviner with a forked rod and a wide hat                                                                                          | the cowhand (the dusty corral)                               | the palm shade at Palm Spring, the caravan camp under the stars, the saloon's porch                                |
| fire      | the fire country: Hearthold, the Ember forge, Cinder Springs (W6) | the smith at the Ember forge who works through the night (burnout)                                                                                  | Ashe, a drake-folk knight in dented plate with a bell on her belt, keeper of Hearthold's bedtime bell; her ember scales grey as she rests              | the smith (the basalt ring by the lava)                      | the bathhouse at Cinder Springs, Hearthold's herb garden, Cinderwick's sand                                        |
| neon      | Neon Harbour and the delta (W7)                                   | Doomscroll Dave, who never sleeps                                                                                                                   | Nix, a courier android in a hooded reflective jacket, cracked face-screen showing a sleep glyph; Neon's 3 a.m. courier who brought Dave his parcels    | Dave (the Neon court)                                        | a bench in the Heights gardens, the chapel on Chapel Islet, the gallery behind the falls, a reed hide in the delta |
| halcyon   | Halcyon Station in orbit (W8)                                     | the sleep-bay keeper, who keeps the station's sleep bay perfect for everyone else and never lies down                                               | Bunk, a barrel-shaped white station robot with magnetic boots, a sleeping bag rolled on its back and a slow-blinking visor                             | the station botanist (a padded ring)                         | the sleep bay, the lounge window seat, the galley                                                                  |
| lumen     | Lumen, the quiet moon (W9): the journey's end                     | the stargazer, who counts the stars on a chart with a gap and never closes their eyes                                                               | Mote, a star of Dream Dust in a nightcap that floats; the fourteenth folk, the full moon                                                               | the stargazer (the sparring crater)                          | the hammock under the moon tree in the Dream Grove, the habitat bunk, the dream pools                              |

## Output format (one JSON object per story; an array of 11)

```json
{
  "id": "frostline",
  "title": "the kettle is always on",
  "theme": "one line: the imbalance and the balance found",
  "chapters": [
    {
      "n": 1,
      "title": "short title",
      "spot": "where it happens (one of the rest spots)",
      "beat": "one or two sentences: what happened while you were away (welcome-back text, lowercase)",
      "lines": [
        { "who": "warden", "text": "..." },
        { "who": "companion", "text": "..." }
      ],
      "change": "what stays changed in the world afterwards, presentation only (or null for chapter 1)"
    }
  ],
  "apprentice": {
    "who": "Tam",
    "ask": "her line asking to come along",
    "joins": "one sentence: how she joins"
  },
  "rival": {
    "who": "the hut warden",
    "invite": "one lowercase line inviting a friendly spar (optional to accept)"
  },
  "artNeeds": ["short list of the props/poses a map lane must draw for the world changes"]
}
```

Each chapter: 2 to 4 lines, the beat under 40 words. Keep art needs small: each world change should reuse or slightly alter something the region already has (a lamp on, a door open, a bench, a person in a new pose), at most one new small prop per chapter.
