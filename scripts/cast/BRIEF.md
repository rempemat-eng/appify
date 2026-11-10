# Cast brief (Claude A, 25 Oct)

Matt, 25 Oct 09:21, after seeing the first Eastward-style pass of Bramble, Iona, Pendle and Cairn:
"these are good. make all characters like that but make sure the detail is perfect (no logic issues). also pendle could use a little bit of work and cairn has too human like proportions: make him a bit rounder, arms and legs larger like before. then make sure the animations and abilities work well and all characters are animated well."

Earlier decisions: keep Codex's cast (identities and equipment); Eastward-style true pixel art; native 1920x1080 = a 960x540 art grid shown exactly 2x (4x on 4K); relatively sharp, somewhat smooth animation; detailed characters.

## Workspace

/tmp/claude-0/-home-claude/740ae43f-1e6f-546c-a61b-113cd8f682fd/scratchpad/castwork/ is a local git repo (no remote). Commit your own files often with a clear message. Never rewrite history. Read STYLE.md and src/ first.

## Ownership (one writer per file)

- Lead: src/ew.py, src/parts.py, src/palette.py, src/anim*.py, src/checks*.py, CONTRACT.md, STYLE.md, and src/bramble.py, src/iona.py, src/pendle.py, src/cairn.py.
- Each designer: only src/<id>.py for their characters, plus review/<id>\_\*.png. Need a shared-rig feature? Put a local helper in your own module and add a line to NOTES.md asking the lead to adopt it. Never edit shared files.
- Everyone may append to NOTES.md (append only).

## Identity and logic (the source of truth)

Codex's identity table: /tmp/claude-0/-home-claude/740ae43f-1e6f-546c-a61b-113cd8f682fd/scratchpad/c241/prototypes/mygame-animation-studio/ART_DIRECTION.md ("Identity reference" table: silhouette, equipment, continuity rules). Codex's current frames for colours and designs: .../mygame-animation-studio/assets/animated/<id>/ (idle-00.png etc.) and art-source/.
"No logic issues" means at least: every carried item exists exactly once and stays attached to the same place across facings and frames; anatomical sides stay fixed (e.g. Nix's laser arm is anatomical LEFT in every view); hands that hold something show the grip; nothing floats or clips through the body; the far side is occluded correctly; back views show what is on the back (quiver, pack, cape); light from the upper left in every facing (west is relit, not a plain mirror; one-sided gear swaps sides correctly); feet on the ground line at the pivot; consistent size between characters (bench 48 px, oak trunk ~90 px, average adult ~74 px).
