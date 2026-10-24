# Animation in world context

This is a character integration contract for the isolated studio. It does not replace the map team's terrain, collision API, placements or production game rules. Test status is recorded in VALIDATION.md; a row here alone does not establish that a world feature is playable.

## Separate the foot position from height

The actor's XY position is its ground footprint. Ground elevation and airborne height are separate quantities. The sprite and its hand/weapon origin move above that footprint; its shadow remains on the supporting surface. A jump must have anticipation, takeoff, an airborne phase, contact and recovery. Stairs use a continuous elevation profile for the supported foot path while the drawings show alternating raised feet. The visible staircase is not a succession of teleports.

The studio keeps the camera fixed. It owns the jump arc; the source jump drawings do not add a second whole-character arc. Collision, support checks and one-shot landing events use simulation state rather than the number of rendered frames.

## Places and required states

| Place or condition | Animation and interaction requirement | Scope |
|---|---|---|
| Flat stone, soil, grass | Grounded walk, planted support, stop and idle; restrained material-specific foot response | Studio ground/surface studies |
| Shallow water | Supported wade with local ripples and wet contacts; distinguish from unsupported deep water | Shallow surface response; swimming not supplied |
| Sand, mud, snow, ice | Foot support and contact material should come from the map, not the body art; sinking or slipping requires an agreed gameplay rule | Integration requirement, no invented friction or status effect |
| Stairs, ascent and descent | Separate raised-foot cycles, continuous elevation, stop safely on a tread, retain the correct shadow height | Studio stair course |
| Ramp and uneven ground | Continuous supported height, stable body registration; decide steepness/blocking through the map contract | Same height contract; production slopes need integration tests |
| Low ledge | Block grounded walking when the rise exceeds a step; permit a jump only if its arc clears the top and the destination supports landing | Studio ledge course |
| Pit or unbridged gap | Walking may lose support; airborne recovery must never stand over the void; bounded reset and cleared controls | Studio pit course |
| Bridge over a gap | Bridge top supports the footprint at its own elevation; the pit below must not override valid top support | Studio course; production bridges need layer IDs |
| Moving platform or lift | Carry the supported actor, preserve platform-relative foot position; decide inherited velocity on departure | Production integration pending, no claim from static bridge tests |
| Low ceiling or doorway | Height clearance affects jumps; the feet and weapon remain outside solid walls | Production clearance tests pending |
| Narrow passages and foreground props | Use footprint collision and stable depth sorting; foreground art may occlude the body, but not make interaction targets unreachable | Production occlusion/interaction tests pending |
| Ladders, ropes, handholds, climbing | Separate attached-contact states and authored hand/foot cycles; no reuse of stair walk as climbing | Not supplied; needs map and gameplay agreement |
| Deep water | Entry, swimming, surface state and exit need their own body/gear treatment; sealed Brine suit alone does not authorise underwater gameplay | Not supplied |
| Falling from height | Separate downward state, support acquisition and one landing event; do not play a grounded attack while unsupported | Studio fall/support handling; damage rules unchanged |
| Combat beside a height transition | Visible muzzle/contact and target height must agree; no ground hit on another elevation through a cliff | Studio blocks combat in traversal course; production height combat pending |
| Powered equipment | Keep transformed equipment during idle, walk study, primary and guard, then show an explicit exit | Dedicated powered review; powered jump/stair/dodge drawings not supplied |
| Hit, defeat, interruption and focus loss | Clear buffered action safely, stop old effects, never resurrect the last defeat pose, freeze on lost focus and resume without held input | Studio regressions |
| Off-screen, pause, menus and reset | No continuing hidden motion or stale damage; finite effects, no inherited input or terrain height after reset | Studio regressions |

## Direction and equipment

These masters show east-facing three-quarter acting. The studio does not mirror a cyborg arm or attached equipment and count that as another direction. Up/down movement in the course tests support and elevation, not completed north/south art. Proper production stairs and diagonal travel still need matching directional sets and anchors. A character turning in a narrow space needs a real change of facing rather than rotating a flat image.

Powered mode is an explicit visual review hold, not an invented balance implementation. It has no invented duration, damage multiplier or cooldown. Exit it before using the base traversal course. The form's missing traversal states are exposed rather than silently reverting a helmet, rifle or arm casing while the power is active.

## Research behind this pass

Jason Martinsen's [jump-and-land tutorial](https://www.animationmentor.com/blog/tutorial-animate-a-jump-and-land/) emphasises readable key poses, offset limbs, arc tracking, foot plants and overlapping clothing. Those principles guide the new jump drawings and the review of support contacts. Its cinematic camera advice does not override this project's fixed-camera requirement.

Ray Chase's [body-mechanics discussion](https://www.animationmentor.com/blog/3-reasons-why-every-animator-should-master-the-bouncing-ball-with-ray-chase/) describes using hip motion, supported feet and weight absorption to block stairs and falls. More drawings are useful only when that support and timing remain coherent.

The version-matched [Godot 4.5 CharacterBody2D reference](https://docs.godotengine.org/en/4.5/classes/class_characterbody2d.html) distinguishes top-down floating motion from floor/slope motion and documents support snapping and platform departure. The studio's additional height layer is a project design choice, not a built-in promise that a top-down character automatically handles stairs or moving platforms.

Research checked 24 October 2026. These sources support animation and implementation principles; they do not certify the generated drawings or main-game integration.
