# Character animation and combat research

Research checked 24 October 2026. This document distinguishes published guidance from MyGame design proposals. It is a production reference, not a claim that every recommendation is implemented or artistically validated.

## The main correction: timing before frame count

Thomas Vasseur, the Motion Twin artist responsible for Dead Cells' art and animation, describes first making the fewest necessary key poses convincing and correctly timed. Additional poses support those keys; the attack's decisive transition stays sharp. He also describes a deliberately retake-friendly production pipeline. The useful principle is that a fast, clear strike with a readable preparation and recovery can communicate more force than a uniformly smooth sequence. More frames help when they explain motion or material, rather than merely filling elapsed time.[1]

Disney and DreamWorks animator Dave Burgess gives a compatible account: equal timing can remove rhythm, while selective holds make major poses readable. Longer holds can communicate greater mass, with fast transitions preserving energy. His article is about cinematic animation, so game attacks also need to meet input-response and gameplay constraints.[2]

For MyGame, each attack should therefore have four inspectable phases: preparation, release or contact, follow-through, and recovery. The event that causes damage must agree with the visible contact. A greater number of authored poses is useful for weight transfer, directional changes, a readable throwing arc and settling. Repeating one pose ten times is a hold, not ten new drawings. Procedurally moving a flattened drawing is also not ten independently authored drawings. Record those quantities separately.

## Cairn: stone construction should determine his motion

The current roster identifies Cairn as a stone golem using fists and boulders. Preserve that identity. The requested redesign can make him less human by changing the structure rather than adding extra surface noise.

**MyGame design proposal:** give him a low, broad centre of mass; a small head embedded into a rock mass; irregular shoulders and forearms; a few large readable joints separated by dark gaps; squat stone feet; no human ears, lips, exposed muscles or clothing anatomy. Stone planes, selected chips and moss seams should describe structure. Keep detail concentrated at the face, joint gaps and forearms, with calmer broad planes elsewhere. This is an art-direction proposal, not a scientifically defined golem anatomy.

Do not animate the body as one rubbery cutout. Let the feet establish support, then the lower mass move, then the heavy shoulder and arm follow. Plate gaps may compress, but the stone volumes should remain rigid. A planted foot should not slide on the ground during a weight-bearing phase. A short settling action after a step or strike makes the change of support understandable. Sparse dust or a displaced pebble can reinforce contact; the camera need not move.

Drew Adams' discussion of overlap makes an important material distinction: the amount and timing of drag depend on what a part is made from and how it is attached. Apply that distinction selectively. Nix's hair, cloth and machine joints can each respond differently. Cairn's moss or small loose stones can overlap while his main slabs stay comparatively rigid.[3]

Chris Hurtt's anticipation article explains both mechanical preparation and the warning function of anticipation in games. It also warns against reactions beginning before contact. Cairn's wind-up should expose where force will go: a shoulder loads, a fist pulls back, the base braces, then the action releases. Damage reactions should start on contact rather than before it.[4]

## Attacks: one coherent visual language

Riot's VFX education argues for a balance between satisfaction and legibility, and for both kit-wide cohesion and recognisable individual sources. This applies even though League's painterly rendering differs from MyGame's pixel rendering.[5]

Riot's clarity guidance adds three practical requirements: effects should match their hit areas; their visual emphasis should reflect gameplay importance; and projectiles should communicate direction even in a still image. Silhouette should also communicate character, facing and power source.[6]

**MyGame application:** keep the same logical pixel grid, contour treatment and palette discipline across character, projectile and impact. Nix's energy can use a narrow bright core, restrained coloured edge, directional tail and a very short local impact. Cairn's effect should read as stone: angular fragments, a weighted ballistic arc, a separate ground shadow and earth-coloured debris. Reusing a generic neon orb for both would weaken their identities.

A boulder has two positions to communicate: its projection onto the ground and its height above that ground. Keep the collision path and shadow interpretable; do not silently treat a visually airborne projectile as an unlimited wall-crossing object. Choose a clear rule for the prototype, expose it in the controls or notes, and test it.

For impacts, stage the sequence: the attack reaches the actual contact, a tight high-contrast accent identifies the moment, the target reacts in the incoming direction, then larger but lower-contrast debris settles. The impact's brightest area should be brief and local. Smoke should not conceal the character's face or subsequent attacks. Screen-filling flashes and perpetual bloom would obscure the detailed drawing the user asked to see.

## World interaction: causal response rather than decoration

**MyGame design proposal:** use a small set of explicitly tagged practice surfaces and objects. A struck wooden practice object can emit short grain-aligned splinters, a stone blocker can shed angular chips, a shallow water patch can make a compact ripple, and soft ground can produce a restrained dust puff. Only declared destructible props should break. Marks should have a lifetime or bounded count; reset must restore the practice room consistently.

Resolve projectile travel against the first valid collision before spawning its impact. An effect must not appear on an object behind a wall. A fast projectile should be checked along the distance it travelled during the physics step, not only at the next endpoint. A broad strike needs a region or shape test rather than an infinitely thin visual-only line.

Godot's RayCast2D reports the first intersected object and exposes contact position and normal. ShapeCast2D sweeps a region and can report multiple objects; its documentation specifically identifies broad beams as one use. Immediate shape updates can also avoid relying on overlap information that has not updated yet.[7–8] These are appropriate engine tools, but art-facing collision shape, material tags and damage rules still need deliberate authoring.

## Engine workflow and tools

Use authored sprite frames for discrete poses. Godot supports both AnimatedSprite2D/SpriteFrames and AnimationPlayer-driven sprite sheets.[9] SpriteFrames supports different relative durations per frame, so the runtime can hold a load-bearing pose longer without changing the drawings or interpolating a blurred character.[10]

For complex attacks, AnimationPlayer method tracks can invoke the release or contact event at a precise point. The same timeline can coordinate sound and effects. Its call-method events do not fire in editor preview, so previewing the strip alone does not test gameplay contact.[11]

AnimationTree can provide state transitions and layered control, but it uses animations authored in AnimationPlayer. It is not a tool that invents better drawings. Use it when the growing state graph justifies it, not as a substitute for readable preparation, impact and recovery.[12]

CPUParticles2D exposes one-shot emission, fixed particle rate, lifetime, spread, sprite animation and fixed seeds. Those controls suit bounded local dust and debris experiments; a seeded capture can be repeatable. A specific Godot class does not establish an appropriate particle budget on the user's hardware.[13]

Two viable production paths remain:

- **Layered hand-drawn pixel animation:** most direct control over clusters, silhouettes and expressive exaggeration. Use an editable Pixelorama or Aseprite master, stable pivots and directional anchors. Finish key poses first and add breakdowns where the action needs explanation.
- **Low-resolution 3D rendering with pixel cleanup:** Motion Twin's developer account shows why this can make repeated timing changes and large rosters more manageable. It also documents pixel flicker and detail compromises. It is a potential later toolchain experiment, not evidence that MyGame should immediately replace its current hand-drawn art.[1]

Eastward's developer describes bespoke Aseprite assets divided along their natural structure, with individual preparation for lighting. The useful lesson is layered authoring and controlled presentation. Eastward does not provide a universal frame count, source sprite size, or engine setting that makes another game's characters equally expressive.[14]

## Review before adding more effects

Review each action at gameplay size, enlarged nearest-neighbour size, normal speed and slow playback. A normal-speed loop reveals rhythm; a contact sheet reveals unwanted changes in volume, equipment, face and contour. Neither a passed assertion suite nor a generated frame count certifies visual quality.

A practical review order is silhouette and facing; support and foot planting; anticipation and contact; recovery and material response; effect-to-hitbox agreement; palette and layering; then optional ambience. Preview an effect-free attack as well. If the body action cannot be read without particles, improve its poses first.

Keep the fixed camera. The Game Accessibility Guidelines identify camera shake, tilting, motion blur and unexpected view changes as potential barriers. Local body movement, direction-specific reactions, sound and brief contact accents can communicate force without moving the entire frame.[15] Any proposed hit-stop duration should be labelled an experiment, applied sparingly, and independently toggleable; no universal number of milliseconds follows from the sources reviewed here.

## Sources

1. Thomas Vasseur, Motion Twin (2018), [Art Design Deep Dive: Using a 3D pipeline for 2D animation in Dead Cells](https://www.gamedeveloper.com/production/art-design-deep-dive-using-a-3d-pipeline-for-2d-animation-in-i-dead-cells-i-). First-person developer account; directly read.
2. Dave Burgess (2017), [Timing: The 12 Basic Principles of Animation](https://www.animationmentor.com/blog/timing-the-12-basic-principles-of-animation/). Working animator's explanation; directly read.
3. Drew Adams (2017), [Follow-through and Overlapping Action](https://www.animationmentor.com/blog/follow-through-and-overlapping-action-the-12-basic-principles-of-animation/). Working animator's explanation; directly read.
4. Chris Hurtt (2017), [Anticipation](https://www.animationmentor.com/blog/anticipation-the-12-basic-principles-of-animation/). Working animator's explanation, including games; directly read.
5. Riot Games, [Art Education: Visual Effects](https://www.riotgames.com/en/artedu/visual-effects). Official studio education text; directly read. The linked video was not independently watched.
6. Riot Games (2021), [Clarity in League](https://www.leagueoflegends.com/en-us/news/dev/clarity-in-league/). Official studio design guidance; directly read.
7. Godot 4.5, [RayCast2D](https://docs.godotengine.org/en/4.5/classes/class_raycast2d.html). Official version-matched documentation.
8. Godot 4.5, [ShapeCast2D](https://docs.godotengine.org/en/4.5/classes/class_shapecast2d.html). Official version-matched documentation.
9. Godot 4.5, [2D sprite animation](https://docs.godotengine.org/en/4.5/tutorials/2d/2d_sprite_animation.html). Official version-matched documentation.
10. Godot 4.5, [SpriteFrames](https://docs.godotengine.org/en/4.5/classes/class_spriteframes.html). Official version-matched documentation.
11. Godot 4.5, [Animation track types](https://docs.godotengine.org/en/4.5/tutorials/animation/animation_track_types.html). Official version-matched documentation.
12. Godot 4.5, [Using AnimationTree](https://docs.godotengine.org/en/4.5/tutorials/animation/animation_tree.html). Official version-matched documentation.
13. Godot 4.5, [CPUParticles2D](https://docs.godotengine.org/en/4.5/classes/class_cpuparticles2d.html). Official version-matched documentation.
14. Tommo Zhou / Pixpil interview (2021), [Eastward's creators share insights on making pixel art adventures](https://www.gamedeveloper.com/art/eastward-s-creators-share-insights-on-making-pixel-art-adventures). Developer responses are primary testimony; directly read.
15. [Game Accessibility Guidelines: camera movement](https://gameaccessibilityguidelines.com/avoid-or-provide-option-to-disable-any-difference-between-controller-movement-and-camera-movement/). Direct developer guidance; directly read.

The original League VFX style-guide URL now redirects to its homepage, so it was not used as evidence. GDC's Berbece presentation page redirected to maintenance during this check. Sakurai's official hit-stop video page was reachable but did not expose its contents; its detailed techniques are therefore not asserted here. These are useful follow-up viewing candidates, not sources silently treated as watched.
