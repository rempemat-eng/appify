# Port regression cases and authority corrections

These are requirements for the future Godot/GdUnit4 port. They are not a claim that it has been implemented. Numeric values below are in original canonical units and seconds. The recovered compiled engine in #242 is the oracle; exact provenance and executable probes accompany the data.

## Correct earlier descriptions before porting

| Earlier prototype description | Verified recovered behaviour | Consequence of copying the description |
| --- | --- | --- |
| Nix's secondary is a cooling pulse. | Afterimage inserts one stationary hologram at action commitment origin. It lasts3s or one hit. Q does not reset heat; the special caps heat at45. | Changes resource budget and removes the intended decoy action. |
| Mote's powered orbit entities automatically damage nearby enemies. | Powered primary adds two `orbit-shard` projectiles to its three glass shots. The orbit effect is visual; idle powered state has no autonomous orbit attack. | Adds unrequested idle damage and changes the kit. |
| Velvet's guard counter requires the form still to be active when striking. | Successful powered guard primes a2s counter. Primary consumes the counter while its independent timer remains positive, including after form expiry. | Incorrectly removes a valid counter window. |
| Brine's gun-butt and Morel's close burst are invalid fallbacks. | Untethered/out-of-range Brine Q uses the21-damage gun-butt; patchless Morel Q uses the20-damage close burst. | Disables canonical abilities. |
| Powered Pendle Q is another rifle fan. | It is a22-damage rifle-stock strike. Normal Q fires up to three remaining revolver rounds, then reloads. | Changes weapon/ammo behaviour and draws the wrong action. |
| Rook cannot fire during the vault or is immune to all attacks. | Vault retains aim/carbine fire. It avoids ground melee/field attacks above the airborne threshold, while projectile/explosion hits remain valid. | Changes combat availability and defensive rules. |

The validated general lesson is to check the executed stateful branch and its boundary conditions, rather than infer mechanics from a name, catalogue summary or animation study. These corrections are specific to the recovered engine. Future intentional design changes should be explicit data revisions with new expectations, not silent port drift.

## Required cases

- Clock: an event crosses release time exactly once under exact-boundary, slightly early/late,60Hz, mixed-delta and overshoot steps. Render the authored release pose at that event even when serialized frame-duration sums round differently. Changing drawing count does not change cooldown or attack duration.
- Art: every chosen facing uses its own clips/attachments; no whole-body mirror substitutes for W. Missing art is reported. Guard holds its declared brace; defeat holds the terminal drawing; powered equipment persists until the actual return transition.
- Bramble: powered arrow uses captured launch state; pierce budget3 means the first hit plus up to three further hits. Only its last surviving target retains that projectile's root.
- Morel: patchless Q keeps its close burst. Prepared patches chain finitely; field insertion remains bounded. A projectile's launch-state effects do not disappear merely because the form expires in flight.
- Velvet: distinguish normal cut and counter. Powered guard primes the counter, it survives form expiry for its own remaining lifetime, and one primary consumes it. Echoes are finite separate effects.
- Cairn: the boulder stops at first collision. Its powered contact adds the declared slam; physical projectile contacts do not use the screen hand'sY as a ground coordinate. Held rock disappears on release, not on an arbitrary later animation frame.
- Iona: one lunge deals its intended single contact per target; a blocked path does not hit through a wall. Storm impact arcs to one eligible nearby foe.
- Tam: repeated frost, bind/shatter and tank differences match the recovered rules. Glacier movement is a glide and does not remove ordinary sleeves or duplicate limbs.
- Brine: no tether, dead tether, expired tether and out-of-range tether choose the gun-butt. Light/heavy reel directions differ. Activation resets integral reload/ammo. An in-flight harpoon retains its captured powered state.
- Pendle: six-round capacity; normal Q uses min(3,remaining), then reloads. Powered primary uses the rifle; powered Q remains a stock strike with no fan projectiles. Reload stages retain the same weapon.
- Mirra: a seal widens water only when reached before the target. One-oldest replacement thresholds, seal lifetimes and finite network ticks stay canonical. Aim-point placement clamps to reach and arena bounds.
- Ashe: finite form expiry triggers the aimed finisher only while alive and when not interrupted. It uses current aim at expiry. Helmet exists once, carried before and worn during the form.
- Clack: secondary vent remains available during rocket reload. Activation refills/reset reload. Powered primary fires three finite rockets with the original spreads/blasts and remains mobile.
- Nix: Q retains its commitment origin while the player moves; a second decoy replaces the first. It lasts at most3s or one hit. Heat gates primary at92, passively cools at the applicable rate, and Q itself does not clear it.
- Rook: exactly two finite operator-near turrets fire on their own cooldowns and honour designation. Vault height/duration/forward motion are physical; the shadow stays on support and body art does not add a second height arc. Base and powered airborne carbine poses emit once.
- Mote: powered primary has three glass plus two orbit-shard projectiles. Waiting in powered idle creates no autonomous damaging orbit system. Gravity placement, radius and finite duration retain the recovered values.
- World: support height, airborne height and ground-foot depth are independent. Test blocked cells, landings, stairs/decks where actually authored, foreground occlusion, inactive time and reduced motion against the landed foundation.

The pure combat engine has arena bounds and enemy collision, not the future game's complete terrain/occlusion system. Wall/support cases above are integration requirements, not evidence that they were already provided by the canonical oracle.
