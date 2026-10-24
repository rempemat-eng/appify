# Character identity and art-direction reference

Current animation status: fourteen east-facing base/traversal sets plus powered idle, walk, primary, guard and return studies. The final manifests contain 152 drawings for twelve characters,151 for Velvet and160 for Pendle including reload. README.md and VALIDATION.md define current dimensions and actual tested scope. Directional completion, powered traversal and layered masters remain unfinished.

The reference is Eastward's in-game readability: distinct silhouettes, expressive proportions, deliberate colour clusters and poses that remain legible against a busy environment. Dense surface texture alone does not achieve that result. The studies remain a starting point for drawing and animation cleanup, rather than a claim of matching Eastward's finished craft.

## Identity reference

The identities below come from the existing local combat catalogue and its accompanying design notes, inspected on 24 October 2026:

- Catalogue: `/workspace/scratch/cd8973ad8dd5/appify/lib/roster-catalogue.ts`
- Rules and identity notes: `/workspace/scratch/cd8973ad8dd5/appify/docs/codex/roster-actions.md`
- Original art and equipment construction: `/workspace/scratch/cd8973ad8dd5/appify/scripts/art/combat_characters/`
- Repository: [rempemat-eng/appify](https://github.com/rempemat-eng/appify)

The inspected checkout identifies itself as commit `79bc4dcbc80d5aea6f59762cad5074b0b92eb431` on `codex/facial-readability`. These references identify that local source snapshot, not a claim about the latest repository `main`.

| Character | Identity and silhouette to preserve | Equipment and action continuity |
| --- | --- | --- |
| Bramble | Older human ranger with grey hair and beard. Short green mantle over cream clothing and brown trousers. Practical, broad stance. | Bow, carried arrows, attached quiver and billhook. Stow the bow visibly when using the billhook or folding buckler. Briarshot changes the existing bow rather than adding another weapon. |
| Morel | Older, clean-shaven human alchemist with receding grey hair. Rolled cream sleeves and an ochre split apron. A working chemist, not a mushroom creature. | Reagent flasks, catalyst apparatus and one fitted mask. Flasks leave the hand from an identifiable grip. The mask moves from its carried position to the face during the special. |
| Velvet | Adult coastal duellist with silver hair, a narrow naval coat and long divided tails. Cream cuffs and restrained brass fastenings distinguish the dark silhouette. | One sabre, its scabbard and one black lantern. Keep the lantern in its own hand and the sabre in the other. A flare changes the lantern's action, not its identity or location. |
| Cairn | The sole playable golem. Irregular, load-bearing granite slabs, dark joint gaps, short stone feet and turf on the upper masses. The revised head is a small recessed wedge with amber eye slits. No human clothing, belt or facial anatomy. | Stone fists and a thrown boulder. Show the shoulder and lower mass loading before the strike. Old Growth braces the same limbs rather than replacing the body. Its visual activation, held equipment studies and return are supplied; production balance and full powered movement combinations remain separate. |
| Iona | Adult human storm-lancer with a dark tied braid and a berry-red split traveller's coat. The spear gives her a tall, directional silhouette. | One continuous spear shaft, two credible hand grips and a carried harness. Lunge and guard poses retain the same weapon length and the same spearhead. |
| Tam | Mature ice monk with a silver hair knot, layered grey wraps, a weighted sash and prayer beads. Controlled posture and visible open palms. | Hand wraps and connected bead cord. Ice grows around the existing forearms and legs in Glacier Form. Palm strikes remain anatomically readable rather than turning into generic fist attacks. |
| Brine | Human coastal diver in a sealed copper helmet and reinforced cream-and-olive canvas suit. A compact, weight-bearing air pack. | One breathing connection from pack to regulator and helmet, one harpoon gun and its integral reel. The secondary reels the same tether fired by the gun. No disconnected decorative hoses. |
| Pendle | The sole playable robot. Western hat, duster, articulated metal body and a deliberate gunslinger stance. No clock or time motif. | One revolver with a six-round reload and one slung marksman rifle. Longshot visibly holsters the revolver before drawing the rifle. The rifle stays in both hands where the action requires it. |
| Mirra | Adult oasis diviner with an ivory headwrap and tunic, turquoise shawl and an open, readable face. Broad cloth planes distinguish the flowing silhouette. | Water is shaped by gestures. Spring seals and their connecting currents are separate scene effects. Keep jewellery, wrap tails and cloth attached to the same locations across views. |
| Ashe | Adult ember knight with red hair, steel armour, brass edges and a crimson cape and tabard. The normal face remains visible. | One sword and one carried helmet. Cinderhelm moves that helmet onto the head. The helmet must not remain at the belt while another appears on the head. Keep the same armour underneath the lit seams. |
| Clack | Older, broad human heavy gunner with a bald scalp and grey moustache. Teal work clothing and a supporting shoulder harness. Not a volcanic golem. | Shoulder rocket launcher with two attached grips, spare-rocket rack and separate pressure chamber. Rocket exhaust clears the rear. The special unfolds the carried loader and brace without creating a stationary turret. |
| Nix | Mature human cyborg with short asymmetric swept dark hair, a grey temple, teal technical clothing and dark trousers. Keep the organic face readable. | The laser arm is anatomical **left** and the natural arm is **right**. Preserve this in every view. Afterimage leaves one stationary decoy at activation. Limit Release opens the same arm casing. |
| Rook | Mature human orbital salvager with dark hair, light stubble and a worn cream-and-orange pressure suit. The attached pack gives a compact rear silhouette. | One pulse carbine, one helmet and a twin-thruster backpack. Thruster Vault originates at the attached nozzles. Orbital Rig deploys exactly two separate turret entities. No returning disc, tether or launcher substitution. |
| Mote | Bald, genderless humanoid observatory keeper with restrained facial definition and navy-and-gold fragmented clothing. A distinct, quiet silhouette rather than a robot or small mascot. | Glass pieces, the core and flowing garment fragments keep a coherent construction. Aphelion exposes the same core. Orbiting shards remain separate effects rather than extra body parts. |

## Drawing specification for these assets

The current runtime uses **192 × 192 pixel** cells, with ground pivot **(96, 172)**. Ashe uses **256 × 192** and pivot **(132, 172)** to retain wide poses without shrinking the body. A standing character uses approximately **96 drawn pixels vertically**, leaving space for a weapon, hair, cloth and action poses. This is a MyGame asset specification, not a measured statement about Eastward's source sprites.

Cairn uses the common **192×192** canvas and pivot **(96,172)**. His standing body is roughly 112 logical pixels high, with overhead room for his hands. A common source scale preserves crouches and raises within each animation master.

At the intended Full HD presentation, the character artwork has a net enlargement of 2×. A roughly 96-pixel figure therefore occupies about 192 screen pixels vertically. Inspect both that actual play size and a nearest-filtered enlargement. A large portrait is insufficient evidence that a sprite reads in the arena.

Keep the ground pivot independent of the cropped image bounds. Use the same scale through a character's views and actions. A crouch should become shorter, not be stretched back to the standing height. A long weapon may use more of the cell, but it must not move the actor's world origin. Distinguish people through build, posture, hair, head shape and clothing instead of forcing all fourteen into an identical body.

Use a small purposeful set of light, middle and shadow clusters for each material. Put contrast around the face, hands and defining equipment. Keep secondary seams subordinate. Avoid isolated highlight speckles, soft edge haze and clothing texture that changes arbitrarily between frames. Reserve the brightest accent for an emitter, lamp, water edge or other feature the player needs to find quickly.

## Animation handoff

1. **Approve the standing model first.** Review front, side and back views together, at gameplay size, against both light and dark terrain. Check maturity, proportions, palette and equipment connections. Correct inconsistent parts before multiplying them into animation frames.
2. **Draw locomotion.** Build distinct contact, passing and weight-transfer drawings for each required direction. Add breakdowns where they explain motion; choose timing rather than treating a frame count as the quality target. Keep feet planted during contact, separate the knees and let cloth lag the body slightly. Avoid using whole-body translation as a substitute for joint motion. Nix's simple prototype cycle is a reference for integration, not the final locomotion standard for the roster.
3. **Finish one primary attack per character.** Draw readable anticipation, release and recovery poses. Weapon hands, muzzle or strike anchor must agree with the visible pose. The gameplay simulation still decides damage and release timing. Firing an effect must never depend on whether a visual frame happened to complete.
4. **Add the defining secondary.** Give each character a gesture that communicates its particular function. Preserve Nix's stationary Afterimage and Rook's attached-thruster vault. Brine's reel, Morel's catalyst and Velvet's lantern flare should be recognisable before adding particles.
5. **Draw guards and interruptions.** Make the frontal brace readable, retain the carried weapons and show guard break, hit reaction and recovery. Keep impacts local to the character or target. Do not restore room-camera shake, drift, zoom pulses or full-screen flashes.
6. **Complete special transitions and persistent equipment.** Draw the physical transition into the temporary form, then its idle, walk, attack and guard states. A changed helmet, arm casing, rifle or loader must persist for the form's full duration. Draw the return to normal coherently. Keep summoned entities outside body sheets.
7. **Review the loop and rendered scene.** Inspect the last-to-first walk seam, a slow frame sequence and real-time play. Check body-size wobble, foot sliding, missing equipment, arm-side changes, weapon clipping and foreground occlusion. Repeat at Full HD before approving exports.

Keep an editable layered art master, animation tags and a common palette in Pixelorama or an equivalent pixel editor. Export the runtime sheets and frame metadata from that master. Store foot, hand, head and muzzle anchors with the animation contract. Godot's `SpriteFrames` or `AnimationPlayer` resources should consume those exports without changing the collision body or saved player state.

## Remaining cleanup

These studies still require close pose-by-pose art review, anatomical and equipment consistency checks, final pixel cleanup and substantially more original animation. Three views do not establish a complete turnaround, smooth locomotion or every combat state. The Nix scene demonstrates the rendering, input and animation integration separately. Production acceptance needs both that technical integration and a coherent finished art set.

See `ENGINE_RESEARCH.md` for the Eastward and engine sources, and `VALIDATION.md` for the tests actually run on the delivered build.
