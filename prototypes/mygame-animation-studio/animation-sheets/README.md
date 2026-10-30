# MyGame character animation sheets

Fourteen transparent east-view PNG atlases, timing/coordinate JSON and GIF motion reviews. Twelve characters have 152 drawings, Velvet 151 and Pendle 160:2135 total. Each contains112 base/combat/traversal drawings and40 powered-state drawings (Velvet39). Pendle has8 extra reload drawings.

Clips: idle, walk16, primary16, secondary, special activation, guard, hit, defeat, jump, stair_up, stair_down, dodge, powered_idle, powered_walk, powered_primary, powered_guard, powered_exit. Cairn also has16secondary and4hit/defeat. Pendle has an eighteenth reload clip. Velvet exit has7valid authored poses; no duplicate padding.

JSON explicitly identifies every rectangle, duration and foot pivot. Do not assume one row equals one clip. Common cells192×192/pivot96,172; Iona224×192/pivot96,172; Ashe256×192/pivot132,172. Transparent spare atlas cells are not animation poses.

GIFs show source drawings at their authored durations, not recorded gameplay. The native preview records the actual Godot physics/effects. These east-facing base studies do not provide other directions, powered traversal or powered secondaries. See the studio README/validation and visual review for exact scope and remaining cleanup.
