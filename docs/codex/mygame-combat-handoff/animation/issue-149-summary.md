Forward animation requirements for Claude A's `game/` integration:

- Keep the existing per-facing manifest shape: variable-length frames, positive weighted durations, `view`, `frame_size` and `foot_pivot`. Neither the old 96 px figures nor any 96-frame quota is required. Re-author all image anchors on the new 74 px art.
- Actions need explicit `release_frame`/`release_time` and measured per-facing `release_anchor`; guard needs `hold_frame`; jump/vault needs named load/rise/apex/fall/land indices. Canonical simulation seconds remain authoritative.
- Supply the 12 base clips and 12 powered clips for each S/N/E/W facing. Required variants: Brine's untethered gun butt, Rook's airborne carbine, Pendle reload, Velvet counter and Ashe expiry contact/recovery. No extra idle-aim clip is currently required.
- Add moving-emitter tracks for Brine's tether, held-boulder tracks for Cairn and actual nozzle anchors/directions for Rook. Image offsets, planar projectile seeds and physical height are different coordinates.
- Event semantics: release, finish, cancel, footfall, landed and void fall. Release payload separates the semantic action from its selected clip/view, with action-instance ID, canonical time, contact index, ground origin, visual origin, height and aim. Commit the actual contact drawing before one release event; variable render steps cannot duplicate damage.

Please confirm the manifest/resource layout, canonical-to-world units, cardinal/continuous aim, event API, support-height API and owned `game/` files once the foundation lands. Ashe's finisher occurs at exact natural expiry with current aim; an overlapping action needs presentation priority, not a new preparation delay or animation lock.

Published #241 remains an E-only study with 17 common clips. This is the forward handoff, not a claim that the new runtime or Godot 4.7.2 port already exists. The data/checks contain no generated PNGs.
