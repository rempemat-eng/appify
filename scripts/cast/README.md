# The cast rig

This is the source that draws and animates every character in the game: the 14 folk, the villagers, the creatures and the Thornback. Until 10 Nov 2026 it lived only in a session's working folder ("castwork"). It is source and must stay in the repo.

## What is here

- `src/<id>.py` draws one character (S, N, E and W views) and `src/anim_<id>.py` animates it. `src/folk.py`, `src/critter.py`, `src/parts.py` and `src/anim.py` are the shared rig.
- `src/export.py` renders a character's clips. `src/checks.py` holds the cast checks (anchors, no face on N facings, arm symmetry, scale).
- `BRIEF.md`, `CONTRACT.md` and `STYLE.md` are the brief, the manifest contract and the style rules. `NOTES.md`, `AUDIT.md` and `AUDIT-2.md` are the designers' notes and audits.

## Rebuild a character

```sh
cd scripts/cast/src && python3 export.py bramble          # writes scripts/cast/out/bramble/ (not committed)
python3 game/tools/import_cast.py scripts/cast/out bramble # packs it into game/assets/characters/bramble/
```

Checked on 10 Nov 2026 with Pillow 12.3.0: Ada and Bramble come out pixel for pixel the same as the committed sheets (152 of 152 changed files). The PNG file bytes differ because of the encoder version, and the manifest gains two newer fields (`face`, `anchor_gap`). So do not commit a rebuild unless a character really changed.

## Known loose ends

- The preview tools (`look.py`, `preview.py`, `gifprev.py`) and `anim.STUDIO` still point at the old session folder. Pass an output path or change the constant before using them.
- The other 19 characters have not been rebuilt from this copy yet.
