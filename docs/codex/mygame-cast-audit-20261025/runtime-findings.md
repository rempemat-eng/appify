# Runtime review for Claude A and C60

Pinned main: `2f88ca5381388affc1e5f457678cf09a9e481749`.

| Source | Git blob |
| --- | --- |
| `game/actors/player.gd` | `0dd01672a14fda097b3db2e0da8643c5eca6307b` |
| `game/actors/cast_sprite.gd` | `6837d96ed76da2142f36bb611471bc95346d9937` |
| `game/test/test_cast.gd` | `e41101c4538a9a0331e669d0ce4434be520ec55d` |

## Character switching cancels defeat but preserves zero HP

`Player.set_character` (lines 76–84) loads a body and unconditionally assigns idle. Reproduction path in the source: set HP to 1, take one damage, then select another character before defeat completes. HP remains zero but state becomes idle. The downed signal is emitted only in the defeat branch, so that route is lost. Movement and `start_shot` test state rather than HP; future damage returns early at HP zero. Switching during a roll similarly retains `_roll_t` and `_iframe_t` under idle artwork. A programmatic `start_swing` followed by selection retains `_swing_t` and the melee hitbox. The current keyboard binds no melee, so that last case is an API regression rather than a claim about the current keyboard path.

Smallest proposed owner fix, before `sprite.load_character`:

```gdscript
if hp <= 0 or state not in [&"idle", &"walk"] or is_rolling() or is_swinging():
    return false
```

This preserves the current character/HP/facing on rejection and prevents action cancellation without inventing a new cleanup policy. If immediate combat switching is wanted, it needs a declared cancellation and temporary-entity ownership policy. No such rule is introduced here.

Proposed GdUnit regressions for the existing player fixture:

```gdscript
func test_character_switch_cannot_cancel_defeat() -> void:
    var p := _player()
    p.hp = 1
    var got_downed := [false]
    p.downed.connect(func() -> void: got_downed[0] = true)
    assert_bool(p.take_damage(1)).is_true()
    assert_bool(p.set_character("iona")).is_false()
    assert_str(p.character).is_equal("bramble")
    assert_int(p.hp).is_equal(0)
    assert_str(p.state).is_equal("defeat")
    assert_bool(p.start_shot()).is_false()
    await get_tree().create_timer(
        p.sprite.duration("defeat") + Player.DEFEAT_HOLD + 0.1
    ).timeout
    assert_bool(got_downed[0]).is_true()

func test_character_switch_rejects_active_roll() -> void:
    var p := _player()
    assert_bool(p.start_roll(Vector2.RIGHT)).is_true()
    assert_bool(p.set_character("iona")).is_false()
    assert_str(p.character).is_equal("bramble")
    assert_str(p.state).is_equal("dodge")
    assert_bool(p.is_rolling()).is_true()

func test_character_switch_rejects_active_swing() -> void:
    var p := _player()
    p.aim = Vector2.RIGHT
    assert_bool(p.start_swing()).is_true()
    assert_bool(p.set_character("iona")).is_false()
    assert_str(p.character).is_equal("bramble")
    assert_bool(p.is_swinging()).is_true()
```

These are proposed regressions, not an executed GdUnit result. The separate source-method probe executes the exact extracted switching method against fake sprite/state boundaries and confirms zero HP becoming idle, retained roll/invulnerability timers and retained swing time. The existing at-rest selection test does not exercise these paths.

## Crossings and visible contact under large steps

`CastSprite.advance` reduces a loop clock with `fmod`, synchronises the final frame, then enumerates indices only until the new final index. An exact full loop returns no crossings; two full loops also return none. A loop beginning and ending at different indices still loses complete extra revolutions. This matters for future authored footfall/event tracks; current Player walk does not consume those returned entries.

A non-loop action crossing its nonzero release frame does return that frame once even on a large step. However, `_sync` has already set the sprite to the final index. `_advance_action` then calls `_release` for each entered index without displaying its associated pose. The explicit anchor lookup can still spawn at the intended release anchor; it does not prove that the real sprite showed the contact drawing. C60 should dispatch an action/contact event after setting its actual pose, or process canonical substeps/contact boundaries explicitly. Preserve once-only nonzero release crossing while fixing it.

Recommended cases: step exactly to release; overshoot release by several frames; cross the whole action in one step; cancel just before release; restart with a new instance ID; advance one/two complete locomotion cycles; turn while keeping stride phase. At the release callback, assert both the event's contact index and the actual sprite frame, not just the event parameter.

Frame-zero release is a forward-contract gap: `_advance_action` observes only transitions returned by `advance`, so an action whose contact is frame zero is never released on entry. The audited current assets have no frame-zero action release. Define entry dispatch once with an action token before accepting such a manifest; it is not a current-cast failure.

## Arrow projection: preserve the existing split

No present arrow-tip projection defect was confirmed. With the current identity node transforms, ground `(player.x + anchor.x, player.y)` plus height `-anchor.y` renders at `player + anchor`. Adding `anchor.y` to the planar ground would count vertical displacement twice. Body/source anchors, canonical planar seed, support elevation and airborne height must remain distinct in C60. Transformed sprites, stacked decks and wall/height policy require explicit foundation support, not an ad hoc anchor multiplication.

Released arrows surviving a debug selection are observable ownership behaviour, but no agreed cancellation policy makes that alone a defect. Scene teardown must still prevent entities acting in an unloaded scene.

## Executed source-method evidence

`source-method-probe.log` records seven probes under Godot 4.7.2: zero-HP switching, active roll and swing switching, one/full-multiple loop crossings, coarse action contact and frame-zero entry. The extractor checks the exact source Git blobs before embedding the original methods. Fake sprite/state objects isolate the methods; no replacement game project is created and no project file is changed. This is source-method evidence, not full Player, GdUnit or gameplay validation.

To repeat against a checkout of the pinned main:

```sh
python3 build_source_method_probe.py --player /path/to/main/game/actors/player.gd \
  --cast /path/to/main/game/actors/cast_sprite.gd --out /tmp/cast-source-probe.gd
$GODOT --headless --path /path/to/main/game --script /tmp/cast-source-probe.gd
```

No production file was changed by this review. Claude A owns the narrow Player/CastSprite fixes; C60 owns its assigned combat/data/tests. Do not transplant the proposed tests or fix into another owner's branch without agreement.
