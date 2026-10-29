# Prospective v56: city coherence and physical placement

Matt's annotated maps reject arbitrary empty paved areas, abrupt city boundaries, scattered building placement and houses apparently in water. His instruction permits changing terrain to fit settlements, adapting his futuristic and medieval references to MyGame, and preparing props separately. This revision implements that instruction; it does not approve the map, city-size exception, concepts, editor or an art merge.

## Source and physical findings

The original input is PR303 `4984438d09b5fe1333d3e6ea6e6ee82be2bdc908`. The new Codex branch explicitly incorporates reviewed355 `7afe9efdb3340bd5bb350176c182db4aa0421ebe`, retaining343 `aa1161cdb03a3dc98d7d38bb41205edbe757b52b` and331 `96215d5b1d6f395e4aa4fbdac207ff6a4ef384d3` through their real ancestry. Their proposal adoption remains default OFF. The old branches and historical v55 PNG/JSON files remain unchanged.

Literal decoding of the committed Crossroads terrain confirms water beneath inherited buildings b001 (5 cells), b003 (16) and b007 (6). The old factory deliberately preserved river/creek cells under fixed zone buildings, while the town checker skipped those buildings before its water check. This is a confirmed27-cell macro/zone inconsistency, distinct from the unresolved historical coarse-route Cinderwick diagnostic. The current Neon81-record plan has no literal water/barrier footprint overlap; its problem is coherent urban form.

## What changes

The producer has an explicit `MYGAME_MAP_REVISION=v56` path. Its default remains v55. Version56 writes `blockout-v56.json`, `stats-v56.json`, `gates-v56.json`, `town-checks-v56.json`, `towns-v56/*.json` and versioned map PNGs. It never replaces the historical town directory or v55 PNGs. Every new rendered heading names v56.

Crossroads keeps its existing seven gameplay-zone footprints and all40 building IDs/forms. The macro Sleepwater is continuously diverted round the zone's eastern edge and rejoins the mill reach, moving actual terrain, river geometry and masks together. The square, well, named trades, crater and garden identity stay in place. The remaining33 buildings are arranged on joined market, mill, halt and garden streets, with working edges rather than isolated radial infill.

Neon Harbour keeps the existing81 source records:72 counted units and nine separate landmarks. This remains an **unapproved city-size proposal**, against Matt's general medium14–22 and large30–45 ranges. Its old waterfront, lanes/east shore, docks, Company district and Heights/Skyport are laid as connected street-facing blocks. Inner courts, cross streets, a service spine, cargo and repair yards, sea-front gardens and lower headland terraces explain the open spaces. Row allocation spreads fronts over the planned streets, including the lower promontory, rather than exhausting the inventory on the first few rows. Existing river/sea and story sites remain placement constraints. The Company shard yard's existing fence is retained. Canalside, Glintside and Halcyon Row form the inhabited approach; Launch Cape's retained first-town proposal336 is not silently adopted.

The map remains a game: a readable arrival, visible landmarks, loops, short links, useful working spaces and quiet pockets. Structures use existing MyGame forms and dimensions; edges/soft grid follow Eastward and the house palette. These are planning footprints, not completed buildings, residents, animals, shops, routines or production prop placement. Highgarth's closed future pass and story landmarks remain intact. The rest of the world still needs its own physical review and first-town adoption.

## Reference adaptation

Matt's supplied futuristic references inform connected districts, a hierarchy of streets and purposeful port infrastructure. His medieval references inform a compact market core, plots behind street fronts, a working river edge and a gradual garden/farm fringe. Their exact road geometry, assets, labels and scale are not copied.

Other primary references supplied by the lead are [Tsumago's official town map](https://tsumago.jp/wordpress/wp-content/uploads/2024/10/tsumago-guide-map-1.pdf), [Saltaire's street plan](https://saltairevillage.info/acrobat/Saltaire_Streetplan_Nemine_Juvante_Publications.pdf), [AlUla's old town and oasis](https://www.experiencealula.com/en/forever-revitalising/oasis/old-town-and-the-oasis), [Randazzo](https://www.visitsicily.info/en/luogo/randazzo/) and the [official Sea of Stars press kit](https://sabotagestudio.com/presskits/sea-of-stars/). Layout inferences are adapted to MyGame; these are not full maps of every game setting or changes to the art direction. Eastward remains the sole edge/soft-grid reference.

## Controls and limits

Bounded controls verify the real inherited water cells, exact retained source inventory/count conventions, a continuous diverted channel and unchanged outside ground, refusal of missing joins/water footprints, actual street-edge clearance, target-region restoration, final inherited-footprint checks and preservation of historical town files. The final full-town report retains every existing checker failure, literal bounds/water/barrier/overlap failure and count shortfall, including towns outside this revision. A v56 command exits1 for incomplete/failing physical checks even if diagnostic proposal pictures were produced. Pictures never waive findings.

The legacy adoption test's final whole-`geo55.py` byte equality predates Matt's terrain-revision instruction. Under narrow lead extension6496583617 it is replaced with equality of the actual default-v55 producer pipeline AST against the original331 blob, specialising only the explicit v56 branch. The exact legacy factory AST, default-OFF selection, unknown-key, packet/refusal,21-record export and seed controls are retained. This is source/wiring preservation, not historical full-world reproduction.

The all-dry source city-layout control executed all81 unique records with no mutual or route-footprint overlap and spread Heights buildings from y4736 to5568. It is a synthetic capacity control, **not real terrain placement**. Initial controls caught a partial-width street-edge bug and a lanes/docks conflict; both were corrected before the passing control. The first test invocation also failed to find its test module because of an incorrect relative setup path; it executed zero product tests and is not credited as a pass.

No new raw continent, renderer, engine or full verify/art suite has run at this source checkpoint. Actual terrain placement, current proposal images, full town checks, macro gates, Y12 packet and Matt's explicit PR approval remain required. Historical v55 raw equality is unavailable because the old process hash seed was not recorded; the reviewed CRC32 producer contract provides a new prospective run only.
