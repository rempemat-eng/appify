# Ability and traversal audit

Audit begun 24 October 2026 against the delivered 912-drawing roster studio. This records the starting defects and acceptance requirements for the next pass. It does **not** assert that a later implementation has passed them; see the final validation record for actual results.

## Authority and scope

The fourteen-character identity contract in `ART_DIRECTION.md`, the per-character imported manifests and the existing study source are the available MyGame references. The catalogue snapshot that document names (`79bc4dcbc80d5aea6f59762cad5074b0b92eb431`, `lib/roster-catalogue.ts`, `docs/codex/roster-actions.md`) could not be independently recovered from the named GitHub repository on this date: the commit and file requests returned 404. Current `rempemat-eng/appify` is NapAttack and has a different cast and rules. Its fox-folk Bramble or turn-based mechanics must not silently replace this studio's older human ranger or real-time action studies.

The read-only GitHub coordination issue [appify#149](https://github.com/rempemat-eng/appify/issues/149) preserves isolated ownership, a single integration owner and no competing world traversal edits. This pass belongs in the isolated animation studio. No main-game save, map, balance or navigation contract is approved by this document. A currently present `codex/character-world-contract-20261024` worktree belongs to separate work and was not edited here.

The exact cross-chat title “MyGame – CI & Map Engineering” was not found in the repository's issue results. Do not claim a message was delivered to that chat, or that Claude accepted these assets. An integration handoff should contain the tested studio files, exact manifests, anchors and explicit remaining gaps.

## Frame-count decision

Ninety-six total drawings is not a universal smoothness target. Allocate added drawings to visible missing movement and to large transitions in existing attacks. Keep attack release time and total recovery deliberate; doubling drawings must not automatically double input latency. Duplicate poses, longer holds, palette shifts and translated copies do not count as new body drawings.

The agreed allocation is four new eight-drawing clips (`jump`, `stair_up`, `stair_down`, `dodge`), with eight extra walk and eight extra primary breakdowns for ordinary sets: 112 base drawings. Cairn already has longer walk and attacks, so his allocation follows its own manifest. Five further eight-drawing powered clips (`powered_idle`, `powered_walk`, `powered_primary`, `powered_guard`, `powered_exit`) make 152 selected drawings per character if every supplied frame passes import and review. Pendle has an additional eight-drawing reload target, for 160. These counts are a target, not a substitute for the final manifest or evidence of complete directions. The powered review state is an explicit visual hold, with production timing and balance left to the main-game owner. Powered traversal is gated until matching equipment-continuity drawings exist.

## Ability coverage contract

Every row needs distinct preparation, visible release/contact, follow-through and a supported return. Character sheets contain the body and attached equipment; projectiles, currents, glass shards and turrets remain scene entities. This table describes established visual identities, not new damage, duration, cooldown or terrain powers.

| Character | Primary / secondary already represented | Special continuity needed through use and return |
| --- | --- | --- |
| Bramble | Bow arrow / billhook; bow stows for billhook and buckler | Briarshot alters the existing bow. Growth must not create a second bow or vanish as soon as the activation clip ends. |
| Morel | Flask throw / catalyst apparatus | The carried mask moves onto the same face; flask apparatus stays attached and the mask stays worn while that state is active. |
| Velvet | Sabre / black lantern flare | Keep exactly one sabre and one lantern in their own hands. Retain the activated lantern state without replacing the duellist with a generic glow. |
| Cairn | Fist slam / separate thrown boulder | Old Growth braces the same stone limbs. Preserve rigid slabs, recessed amber eyes and load-bearing feet; do not introduce a second body. |
| Iona | Spear strike / lunge | Preserve one shaft, one head and credible grips through harness/spear activation and all movement. No independently verified new special name or numerical effect is available. |
| Tam | Open-palm strike / frost ridge | Glacier Form grows ice around the same forearms and legs, then clears coherently. Open palms and bead cord remain recognisable. |
| Brine | Harpoon / reel the same tether | Keep one gun, one reel, one helmet/air connection; any deployed rig stays connected. Do not infer swimming or underwater access from the costume. |
| Pendle | Revolver / fan fire | Longshot holsters the revolver, draws the carried rifle and uses that rifle in both hands for powered aiming, movement and firing. A base revolver shot underneath a rifle silhouette is a logical error. Six-round reload needs visible staging if claimed as animated. |
| Mirra | Shaped water / spring seal | Seals and connecting currents are separate effects rooted to actual scene positions. The body gestures shape and maintain them; no invented flooding. |
| Ashe | Sword cut / thrust | Cinderhelm transfers the same carried helmet onto the head. No duplicate at the belt; worn helmet persists through movement, guard and attacks, then returns visibly. |
| Clack | Shoulder rocket / pressure vent | The loader and brace unfold from carried gear and remain attached. Keep both launcher grips and clear rear exhaust. He does not become a stationary turret. |
| Nix | Anatomical left-arm laser / stationary Afterimage | Limit Release opens that same left casing. The organic arm stays right. Open casing persists through powered actions; the decoy stays at activation origin and never becomes an attacker. |
| Rook | Pulse carbine / attached-thruster vault | Orbital Rig deploys exactly two separate turrets. The same helmet moves from hip to head. Turrets and helmet should last for the review state, rather than being deleted on activation recovery. |
| Mote | Glass shards / gravity gesture | Aphelion exposes the existing core. Core continuity survives locomotion and attacks; orbiting shards are separate objects, not extra limbs. |

The previous release had eight base clips for all fourteen characters. Its own source explicitly returned every special to base gear and deleted Rook's turrets on recovery. Consequently, it was a base-animation set with special activations, **not** complete all-ability animation. A sustained-state review may use an explicit enter/hold/exit control without inventing production balance numbers. If the necessary powered body drawings are absent, report that gap plainly.

## Concrete starting defects

1. `RosterStudyActor` always emitted `Vector2.RIGHT` and disabled sprite mirroring. This is truthful for an east-view study, but movement up/down/west cannot be described as complete directional animation. Do not invent facing coverage by mirroring asymmetric equipment.
2. `animation_yard.gd::_on_release` handled every special through a generic activation accent. Only Rook's two temporary props and Mirra's existing-seal link had additional staging. They did not establish fourteen sustained special movesets.
3. Nix's decoy origin was the release position. The older Nix scene captured `action_origin` when the action began. Capturing once at activation prevents a pre-release displacement from moving the decoy.
4. Brine's secondary substituted a new gun-butt melee hit when no tether existed. This contradicts the defining reel action. A no-tether action should give an empty-reel response or reject with a clear state, without phantom contact.
5. A new harpoon could travel while the old contact tether remained. Tether ownership, launch replacement, target validity and reset need explicit handling. Reel feedback should refer to the same endpoint.
6. Iona's lunge applied the entire melee hit at the original position and only then began a dash. Collision/contact should occur along the actual movement and stop at a wall, with at most one hit per target per lunge.
7. Pendle silently refilled ammunition after one second while the body could be idle. Successful ammo assertions alone do not demonstrate a reload animation. Firing while unavailable also needs visible dry-fire/reload behaviour rather than implying a launched shot.
8. `speed_scale` slowed pose/action/dash clocks, but ordinary velocity was unchanged before `move_and_slide()`. Half-speed playback therefore slid across ground at full travel speed, and a dash could cover roughly twice the distance. Animation cadence and movement must share a declared time basis.
9. Footstep particles were emitted every 0.34 seconds regardless of authored contact. Cairn's 1.04-second walk generated about three contacts per cycle. Contact metadata or distance-linked gait is preferable, with no footsteps while airborne or blocked.
10. The ground shadow retained a constant position/shape while vertical lift changed. Jump support height, airborne lift, visual pivot and shadow need separate state. Otherwise a lifted drawing can imply an incorrect platform or landing surface.
11. Physics remained a flat footprint even during the old vault. That is a valid conservative prototype rule, but it does not prove jumping over obstacles. Never clear all collision masks simply to make a leap look possible.

These are findings in the starting build. Any final “fixed” claim needs a regression that fails the original behaviour and a rendered check on the rebuilt export.

## Traversal state and location coverage

Keep world foot position, supporting surface/elevation and airborne lift separate. Project the drawing and shadow from that state, rather than moving the navigation origin whenever the sprite rises. Stairs are support transitions, not repeated small free jumps. A jump needs compression, take-off, rising tuck, apex, descent, contact and settling; landing compression must agree with contact. A staircase needs raised leading foot, transfer onto the tread and a controlled trailing foot. Downstairs needs deliberate lowering and weight absorption, not a reversed upstairs movie.

The following is a world-integration checklist. It is not a claim that this studio contains these places or that a costume grants access.

| Location / condition | Body and equipment requirement | Logic to verify before production |
| --- | --- | --- |
| Level earth, paths, paved rooms | Grounded walk and start/stop; attached gear follows the body | Foot contact, wall slide, blocked movement without walking in place; no effect outside the active scene. |
| Stone/wood/metal stairs and ramps | Distinct ascent/descent support; no involuntary bob | Both directions, stop on a tread, reverse midflight of stairs, enter from a landing, side-edge rejection, camera fixed. |
| Upper terraces, bridges, lower paths | Same gait at correct support elevation | Top deck and path below cannot share collision/occlusion merely because their screen pixels overlap. No lateral entry through a cliff face. |
| Doorways, arches, tunnels, narrow interiors | Weapon/gear silhouette and facing remain credible | Footprint and clearance use real bounds; a jump cannot pass through a lintel or wall; doorway transition cancels stale actions. |
| Low obstacles and short approved gaps | Authored jump with separate ground shadow | Only declared traversable obstacles/gaps; sweep body and landing support; no landing inside solids, double jump or edge teleport. |
| Cliff edges, long gaps, unsupported ledges | Readable stop/airborne/landing state | Reject unsafe target support or use the main game's established fall rule. Do not invent fall damage, rescue or climbing mechanics. |
| Shallow water, mud, sand, snow | Grounded gait with material-specific bounded contact | Surface depth/passability is tagged; cosmetic ripples/prints do not create new slows, damage or resource rules. |
| Deep water, lava, void, ice slopes | Character-specific art only after an access rule exists | Do not assume swimming, sinking, heat immunity or traction from identity. Use existing region traversal policy. |
| Ladders, ropes, lifts and moving decks | Separate attachment/boarding states if authorised | These require dedicated art and support tracking. Generic jump/stair clips do not establish climb or vehicle coverage. |
| Behind foliage, tall props, rails, bridge fronts | Body occlusion follows supporting plane; defining face/weapon remains readable when needed | Sort by ground/support depth, not head or airborne sprite bounds. Foreground must not imply passing through a solid. |
| Attack/guard/ability on elevated ground | Hand/muzzle/projectile share support elevation | Elevated origin cannot hit a lower/upper target through a deck unless the existing rules allow it. Effects and tether endpoints match support layers. |
| Jump interrupted by hit, pause, focus loss, reset or character switch | Stable airborne pose or deliberate transition | No delayed action release, duplicated landing, stale dash, retained held prop, orphaned turret or resumed held input. |

No new map placement is proposed here. Production locations must come from current generated-map and navigation contracts owned by the world lane.

## Acceptance evidence to collect

- Import every selected drawing with stable pivot, common per-character scale, strict alpha and zero clipping; inspect body-volume and equipment continuity at 2× gameplay size.
- Check the last-to-first walk and stair seams, each attack without effects, and normal/slow playback. Pixel uniqueness is an integrity check, not an artistic judgement.
- Verify one release per action across coarse/fine steps; interruption before release causes no late shot. Match muzzle/contact to the authored release drawing.
- Run each base and supplied powered clip for every character on the final export, including exit and reset. Separately test reload, tether, decoy and two-turret ownership.
- Walk up/down the actual studio staircase, stop/reverse on it, jump at both ends and try the blocked side. Check stair and jump support separately from the visible frame.
- Test low obstacle versus high wall, unsupported landing, repeated jump, landing recovery, attacks while airborne, guard transitions and speed changes.
- Verify real browser blur/refocus and pause/reset during airborne, tethered and powered states. Record software/browser/device limitations accurately.
- Sample the camera transform throughout. No camera shake, tilt, follow or zoom pulse is needed to sell weight.

## Research checked for this pass

The existing `COMBAT_RESEARCH.md` retains the fifteen-source animation/VFX review. Additional version-matched primary engine references were read directly on 24 October 2026:

1. [Godot 4.5 CharacterBody2D](https://docs.godotengine.org/en/4.5/classes/class_characterbody2d.html): floating motion is intended for top-down collisions; `velocity` uses pixels per second and `move_and_slide()` already applies the physics delta. **Application:** keep planar collision distinct from an explicit elevation/jump system. A side-view floor-snap setting alone is not a top-down stair solution.
2. [Godot 4.5 SpriteFrames](https://docs.godotengine.org/en/4.5/classes/class_spriteframes.html): each frame has a relative duration. **Application:** added breakdowns can preserve decisive timing, rather than flattening everything to equal holds.
3. [Godot 4.5 CanvasItem](https://docs.godotengine.org/en/4.5/classes/class_canvasitem.html): drawing transforms, Z and Y sorting are distinct controls. **Application:** sort supporting world planes coherently instead of treating sprite lift as ground movement.
4. [Godot 4.5 ShapeCast2D](https://docs.godotengine.org/en/4.5/classes/class_shapecast2d.html): a shape sweep covers a region and can be updated immediately. **Application:** consider a swept footprint/clearance test for movement and a broad contact sweep for lunges, rather than checking only the final pixel.
5. [Godot 4.5 2D sprite animation](https://docs.godotengine.org/en/4.5/tutorials/2d/2d_sprite_animation.html): animation sheets and individual drawings are supported; property and animation updates may need explicit synchronisation. **Application:** update facing/equipment/clip together to avoid a one-frame incorrect state.

These applications are engineering recommendations, not statements that Godot implements MyGame's missing traversal rules automatically.
