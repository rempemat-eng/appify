"""The Godot game's sound palette, synthesised from code like the art (docs/vision/sound.md).

    npm run sound:game            writes game/audio/sfx/*.wav, game/audio/ambience/*.wav, game/audio/cues.json
    npm run check:sound-repro     regenerates in memory and compares every byte with what is committed,
                                  and checks each file's shape (short, ends in silence, level, seam, budget)
    python3 scripts/audio/game_sounds.py --measure   a table of peak, RMS, length and spectral centroid

It reuses the old app's synthesis helpers (scripts/audio/sounds.py) and changes none of that script's
outputs: nothing here writes to assets/sounds or lib/.

The palette rules are the old app's: sine and triangle tones, gentle attacks, low-passed noise, notes from
C major pentatonic, no square waves and no alarms. Every effect is under 2 s and fades to silence; only
the four ambience loops repeat. Loudness lives in the files (effects peak between -18 and -28 dBFS, loops
at -24), so the game plays everything at volume 1.

Deterministic: each sound's random numbers come from a seed made from its own name, so adding or
reordering sounds never changes another file.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sounds import (  # noqa: E402  (the old app's helpers, unchanged)
    NOTE, SR, band, bell, chirp_phrase, cricket, env, finish, gusts, loopable, noise, norm, osc, place,
    silence, sweep, times, wind, write_wav,
)

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, 'game', 'audio')

AMB_SR = 12000        # the loops hold nothing above 5 kHz
LOOP_SECONDS = 18.0
LOOP_OVERLAP = 2.0
BUDGET_BYTES = 4 * 1024 * 1024
TIERS = ('confirm', 'moment', 'flavour', 'step')

# C major pentatonic again, with the octaves below the old table for horns, growls and stone.
N = dict(NOTE)
N.update({'C2': 65.41, 'G2': 98.00, 'A2': 110.00, 'C3': 130.81, 'D3': 146.83, 'E3': 164.81,
          'G3': 196.00, 'A3': 220.00})


def rng_for(name: str) -> np.random.Generator:
    return np.random.default_rng(int.from_bytes(hashlib.sha256(name.encode()).digest()[:8], 'little'))


def lead(x: np.ndarray, seconds: float, sr: int = SR) -> np.ndarray:
    """Silence before a finished sound, so it follows the cue that starts with it (coins, then the build)."""
    return np.concatenate([silence(seconds, sr), x])


def knock(freq: float, seconds: float = 0.09, decay: float = 0.02, wood: float = 0.4) -> np.ndarray:
    """A small wooden knock: a sine with one quick inharmonic partial."""
    x = osc(freq, seconds) * env(seconds, 0.002, decay)
    return x + wood * osc(freq * 2.4, seconds) * env(seconds, 0.001, decay * 0.5)


def burst(rng, seconds: float, lo: float | None, hi: float | None, attack: float, decay: float,
          hold: float = 0.0, colour: str = 'white') -> np.ndarray:
    """Filtered noise under a soft envelope: scuffs, puffs, whooshes."""
    return band(noise(seconds, rng, SR, colour), lo, hi) * env(seconds, attack, decay, hold=hold)


# -------------------------------------------------------------------- player

def make_step(surface: str):
    def step(rng):
        # Each part is levelled on its own, then mixed: a low thump that carries the weight and a mid
        # scuff that a small speaker can still play.
        s = 0.11
        if surface == 'grass':
            low = norm(osc(84 + 14 * rng.random(), s) * env(s, 0.004, 0.024))
            body = norm(burst(rng, s, 220, 700 + 150 * rng.random(), 0.005, 0.028))
            brush = norm(burst(rng, s, 1600, 4600, 0.014, 0.03))
            x = low + 1.1 * body + 0.5 * brush
        elif surface == 'stone':
            low = norm(osc(112 + 18 * rng.random(), s) * env(s, 0.003, 0.018))
            tick = norm(burst(rng, s, 700, 2300, 0.002, 0.012))
            body = norm(burst(rng, s, 250, 900, 0.003, 0.02))
            x = low + 0.9 * tick + 0.7 * body
        else:  # wood: a hollow board
            f = 236 + 30 * rng.random()
            body = norm(burst(rng, s, 300, 1100, 0.003, 0.018))
            x = norm(knock(f, s, 0.028, wood=0.5)) + 0.55 * body + 0.4 * norm(osc(96, s) * env(s, 0.003, 0.02))
        return finish(x, -28)
    return step


def bow_draw(rng):
    # The stave creaking as the string comes back: a slow rising stick-slip, kept low and quiet.
    s = 0.3
    t = times(s)
    creak = osc(sweep(170, 250, s, curve=0.8), s, wave_='triangle') * (0.55 + 0.45 * np.sin(2 * np.pi * 38 * t) ** 2)
    fibre = 0.25 * band(noise(s, rng), 600, 2200)
    return finish(band((creak + fibre) * env(s, 0.06, 0.09, hold=0.1), None, 1800), -28)


def bow_release(rng):
    # The string's soft thrum (G3, with its octave) and the arrow's breath of air.
    s = 0.32
    thrum = osc(sweep(N['G3'] * 1.06, N['G3'], s, curve=0.4), s, wave_='triangle') * env(s, 0.002, 0.05)
    thrum += 0.6 * osc(sweep(N['G4'] * 1.04, N['G4'], s, curve=0.4), s) * env(s, 0.002, 0.035)
    whiff = norm(burst(rng, s, 900, 3200, 0.02, 0.05))
    return finish(band(norm(thrum) + 0.3 * whiff, None, 3500), -22)


def arrow_hit(rng):
    # The arrow counts on a creature: the old app's soft thump, with the shaft's small thock over it.
    s = 0.3
    thump = norm(osc(sweep(150, 55, s, curve=0.5), s) * env(s, 0.002, 0.055))
    thock = norm(knock(420, s, 0.02) + 0.6 * burst(rng, s, 500, 1800, 0.001, 0.012))
    return finish(thump + 0.8 * thock, -20)


def arrow_wall(rng):
    # The arrow stops at a solid: one small tick of wood.
    s = 0.12
    x = knock(N['C5'], s, 0.016) + 0.5 * burst(rng, s, 1000, 3000, 0.001, 0.008)
    return finish(band(x, None, 4000), -26)


def glance(rng):
    # Matt, 11 Nov: an arrow from beyond reach must read as a miss. A small dull clink: a damped bit of
    # metal, nothing like the thump of a hit.
    s = 0.26
    ting = bell(N['E6'], s, 0.045, brightness=0.55)
    tick = burst(rng, 0.03, 1500, 4000, 0.001, 0.006)
    x = ting.copy()
    place(x, tick, 0.0, gain=0.35)
    return finish(band(x, None, 3600), -22)


def roll(rng):
    # Cloth and ground: a short swish that rises and falls, and the shoulder landing.
    s = 0.4
    t = times(s)
    swish = band(noise(s, rng), 500, 1500) * (1 - t / s) + band(noise(s, rng), 1200, 2800) * (t / s)
    x = norm(swish * env(s, 0.09, 0.07, hold=0.1))
    place(x, norm(osc(sweep(120, 70, 0.12), 0.12) * env(0.12, 0.004, 0.035)), 0.24, gain=0.45)
    return finish(x, -27)


def hurt(rng):
    # A low, short "oof": a falling triangle note (A3 to E3, with its octave) over a thump.
    s = 0.34
    voice = osc(sweep(N['A3'], N['E3'], s, curve=0.6), s, wave_='triangle') * env(s, 0.006, 0.08)
    voice += 0.5 * osc(sweep(N['A4'], N['E4'], s, curve=0.6), s) * env(s, 0.006, 0.06)
    x = norm(voice)
    place(x, norm(osc(sweep(140, 60, 0.2, curve=0.5), 0.2) * env(0.2, 0.002, 0.05)), 0.0, gain=0.5)
    return finish(band(x, None, 1800), -19)


def downed(rng):
    # Three slow falling notes over a low C: going down is gentle, not a punishment.
    out = silence(1.5)
    for i, n in enumerate(['G4', 'E4', 'C4']):
        place(out, osc(N[n], 0.9) * env(0.9, 0.03, 0.32), 0.24 * i, gain=1 - 0.1 * i)
    place(out, osc(N['C3'], 1.2) * env(1.2, 0.2, 0.4, hold=0.2), 0.1, gain=0.3)
    return finish(band(out, None, 2400), -20)


def get_up(rng):
    out = silence(0.95)
    for i, n in enumerate(['C4', 'E4', 'G4']):
        tone = osc(N[n], 0.55, wave_='triangle') * env(0.55, 0.008, 0.18)
        place(out, band(tone, None, 2600), 0.12 * i, gain=0.8 + 0.08 * i)
    return finish(out, -21)


# ------------------------------------------------------------------- enemies

def tell_mossling(rng):
    # Leaves shaking faster as it gathers itself (its wind-up is 0.5 s).
    s = 0.45
    t = times(s)
    shake = band(noise(s, rng), 1500, 4500) * (0.5 + 0.5 * np.sin(2 * np.pi * sweep(14, 30, s) * t) ** 2)
    rise = 0.5 * osc(sweep(300, 420, s), s, wave_='triangle')
    x = (shake + band(rise, None, 1500)) * (t / s) ** 1.5 * env(s, 0.05, 0.06, hold=0.3)
    return finish(x, -27)


def tell_rusher(rng):
    # The boarlet: two snorts, the second higher.
    out = silence(0.6)
    for i, (f0, f1) in enumerate([(210, 250), (240, 300)]):
        d = 0.22
        snort = norm(burst(rng, d, 250, 1100, 0.03, 0.06))
        snort = snort + 0.8 * norm(osc(sweep(f0, f1, d), d, wave_='triangle') * env(d, 0.03, 0.06))
        place(out, snort, 0.3 * i, gain=0.85 + 0.15 * i)
    return finish(band(out, None, 1600), -26)


def tell_shooter(rng):
    # The toad filling its throat: a low croak that swells and wobbles.
    s = 0.6
    t = times(s)
    croak = osc(sweep(140, 190, s), s, vibrato=(22, 0.06)) + 0.4 * osc(sweep(280, 380, s), s, vibrato=(22, 0.06))
    x = croak * (0.3 + 0.7 * t / s) * env(s, 0.08, 0.08, hold=0.38)
    return finish(band(x, None, 1300), -26)


def tell_shield(rng):
    # The mossback bracing: stone dragged a hand's width, over a low hum.
    s = 0.6
    t = times(s)
    grain = 0.6 + 0.4 * np.abs(norm(band(noise(s, rng), None, 28)))
    scrape = norm(band(noise(s, rng), 350, 1400)) * grain
    x = (scrape + 0.35 * osc(N['G2'], s, wave_='triangle')) * env(s, 0.1, 0.1, hold=0.3) * (0.4 + 0.6 * t / s)
    return finish(band(x, None, 1800), -26)


def tell_elite(rng):
    # The horned one: a deeper double huff (its wind-up is the shortest, 0.65 s).
    out = silence(0.55)
    for i, (f0, f1) in enumerate([(150, 172), (168, 205)]):
        d = 0.2
        huff = norm(burst(rng, d, 200, 900, 0.025, 0.055))
        huff = huff + 0.9 * norm(osc(sweep(f0, f1, d), d, wave_='triangle') * env(d, 0.025, 0.055))
        place(out, huff, 0.26 * i, gain=0.8 + 0.2 * i)
    return finish(band(out, None, 1400), -25)


def enemy_strike(rng):
    # A lunge through the air: one quick soft whoosh.
    s = 0.2
    return finish(burst(rng, s, 700, 2600, 0.05, 0.04, hold=0.02), -26)


def enemy_spit(rng):
    # The toad's shot leaving: "pft", and a small falling plop.
    out = silence(0.2)
    place(out, burst(rng, 0.06, 1200, 3500, 0.002, 0.012), 0.0)
    place(out, osc(sweep(520, 260, 0.1, curve=0.6), 0.1) * env(0.1, 0.004, 0.03), 0.02, gain=0.8)
    return finish(out, -25)


def enemy_freed(rng):
    # Freed, not killed: the shard lets go with a breath, and two soft notes rise after it.
    out = silence(0.95)
    place(out, burst(rng, 0.3, 800, 3000, 0.08, 0.07), 0.0, gain=0.5)
    place(out, bell(N['E5'], 0.5, 0.16, brightness=0.2), 0.14)
    place(out, bell(N['G5'], 0.6, 0.2, brightness=0.2), 0.3, gain=0.9)
    return finish(band(out, None, 5000), -24)


# ----------------------------------------------------------------- Thornback

def boss_tell_charge(rng):
    # Head down, a forefoot pawing: three scuffs over a low growl that rises (wind-up 0.8 s, 0.6 in phase 2).
    s = 0.58
    t = times(s)
    growl = osc(sweep(N['G2'], N['C3'], s), s, wave_='triangle') + 0.5 * osc(sweep(N['G3'], N['C4'], s), s)
    growl = norm(growl * (0.6 + 0.4 * np.sin(2 * np.pi * 30 * t) ** 2) * (0.3 + 0.7 * t / s) * env(s, 0.08, 0.08, hold=0.36))
    out = 0.8 * growl
    for i in range(3):
        place(out, norm(burst(rng, 0.1, 250, 1300, 0.01, 0.03)), 0.03 + 0.17 * i, gain=0.4)
    return finish(band(out, None, 1700), -22)


def boss_tell_volley(rng):
    # The bramble shell rattling, quicker and quicker (wind-up 0.9 s, 0.7 in phase 2).
    out = silence(0.66)
    at, gap = 0.0, 0.11
    while at < 0.56:
        place(out, knock(700 + 400 * rng.random(), 0.06, 0.012, wood=0.6), at, gain=0.5 + 0.8 * at)
        at += gap
        gap = max(0.035, gap * 0.82)
    return finish(band(out, None, 3200), -24)


def boss_tell_slam(rng):
    # It rears: a swell from C3 to G3 over its low octave that grows until the fall (wind-up 1.0 s, 0.75
    # in phase 2).
    s = 0.72
    t = times(s)
    tone = osc(sweep(N['C3'], N['G3'], s, curve=1.4), s, wave_='triangle') + 0.6 * osc(sweep(N['C2'], N['G2'], s, curve=1.4), s)
    tone += 0.4 * osc(sweep(N['C4'], N['G4'], s, curve=1.4), s)
    rumble = norm(band(noise(s, rng), 200, 900))
    x = (norm(tone) + 0.3 * rumble) * (t / s) ** 1.6 * env(s, 0.1, 0.06, hold=0.52)
    return finish(band(x, None, 1500), -22)


def boss_charge(rng):
    # The rush itself: a heavy first step and wind.
    out = silence(0.5)
    place(out, osc(sweep(110, 50, 0.2, curve=0.5), 0.2) * env(0.2, 0.003, 0.05), 0.0)
    place(out, norm(burst(rng, 0.46, 90, 700, 0.14, 0.1, hold=0.08, colour='brown')), 0.02, gain=0.8)
    return finish(out, -20)


def boss_volley(rng):
    # Thorns leaving in a fan: five small breaths of air, one after another.
    out = silence(0.34)
    for i in range(5):
        lo = 1400 + 500 * rng.random()
        place(out, burst(rng, 0.09, lo, lo + 2200, 0.012, 0.02), 0.045 * i, gain=1 - 0.1 * i)
    return finish(out, -23)


def boss_slam(rng):
    # It comes down: one deep soft thump, the floor's knock and the dust after it.
    out = silence(0.65)
    place(out, norm(osc(sweep(120, 38, 0.5, curve=0.45), 0.5) * env(0.5, 0.003, 0.12)), 0.0)
    place(out, norm(knock(190, 0.2, 0.04)), 0.0, gain=0.6)
    place(out, norm(burst(rng, 0.45, 250, 1500, 0.01, 0.1)), 0.0, gain=0.45)
    return finish(out, -18)


def boss_roar(rng):
    # The second phase (its roar is 1.1 s): a low rough breath falling from C3 to G2 with its octave.
    # Low-passed, so it is a growl in the chest and never a scream.
    s = 1.1
    t = times(s)
    rough = 0.55 + 0.45 * np.sin(2 * np.pi * 26 * t) ** 2
    breath = norm(band(noise(s, rng), 180, 900)) * rough
    tone = osc(sweep(N['C3'] * 1.08, N['G2'], s, curve=0.7), s, wave_='triangle', vibrato=(7, 0.02))
    tone += 0.6 * osc(sweep(N['C4'] * 1.08, N['G3'], s, curve=0.7), s, wave_='triangle', vibrato=(7, 0.02))
    x = (0.7 * breath + norm(tone) * rough) * env(s, 0.12, 0.2, hold=0.5)
    return finish(band(x, None, 1300), -18)


def boss_stagger(rng):
    # Stopped by the wall: a thud, then a dazed wobble that fades.
    out = silence(0.75)
    place(out, norm(osc(sweep(130, 50, 0.25, curve=0.5), 0.25) * env(0.25, 0.002, 0.06)), 0.0)
    place(out, norm(burst(rng, 0.12, 300, 1400, 0.002, 0.03)), 0.0, gain=0.3)
    place(out, osc(sweep(N['E4'], N['C4'], 0.6), 0.6, wave_='triangle', vibrato=(9, 0.04)) * env(0.6, 0.05, 0.16), 0.1, gain=0.5)
    return finish(band(out, None, 1800), -22)


def boss_freed(rng):
    # The bramble shell cracks, falls away in pieces, and it lies down calm: a quiet C major chord.
    out = silence(1.95)
    for at in (0.0, 0.14, 0.3):
        place(out, burst(rng, 0.05, 500, 2500, 0.001, 0.012), at, gain=0.7)
    for at in np.sort(0.36 + 0.3 * rng.random(4)):
        place(out, knock(150 + 120 * rng.random(), 0.1, 0.02), at, gain=0.5)
    for i, n in enumerate(['C5', 'E5', 'G5']):
        place(out, bell(N[n], 1.0, 0.36, brightness=0.2), 0.74 + 0.1 * i, gain=0.9)
    place(out, osc(N['C4'], 1.1) * env(1.1, 0.25, 0.3, hold=0.2), 0.74, gain=0.3)
    return finish(band(out, None, 5000), -19)


# --------------------------------------------------------------------- world

def door(rng):
    # A latch, a short creak and the air of the next place.
    out = silence(0.5)
    place(out, knock(1150, 0.04, 0.008), 0.0, gain=0.6)
    place(out, knock(900, 0.04, 0.008), 0.07, gain=0.5)
    t = times(0.22)
    creak = osc(sweep(240, 300, 0.22), 0.22, wave_='triangle') * (0.6 + 0.4 * np.sin(2 * np.pi * 34 * t) ** 2)
    place(out, band(creak * env(0.22, 0.04, 0.06, hold=0.06), None, 1600), 0.1, gain=0.5)
    place(out, burst(rng, 0.34, 400, 1800, 0.12, 0.08), 0.14, gain=0.45)
    return finish(out, -24)


def door_stone(rng):
    # The hatch and the stair under the stones: stone on stone, and a low thud as it settles.
    out = silence(0.75)
    grain = 0.55 + 0.45 * np.abs(norm(band(noise(0.5, rng), None, 30)))
    scrape = norm(band(noise(0.5, rng), 300, 1300)) * grain * env(0.5, 0.08, 0.1, hold=0.22)
    place(out, scrape, 0.0, gain=0.8)
    place(out, norm(osc(sweep(95, 55, 0.25, curve=0.5), 0.25) * env(0.25, 0.004, 0.06)), 0.46)
    place(out, norm(knock(210, 0.12, 0.03)), 0.46, gain=0.6)
    return finish(band(out, None, 1800), -22)


def plate(rng):
    # The plate goes down under a foot: a stone click, then the settle.
    out = silence(0.38)
    place(out, norm(knock(330, 0.07, 0.014) + 0.5 * burst(rng, 0.07, 800, 2400, 0.001, 0.008)), 0.0)
    place(out, norm(osc(sweep(120, 70, 0.2, curve=0.5), 0.2) * env(0.2, 0.004, 0.05)), 0.1, gain=0.8)
    place(out, norm(knock(250, 0.1, 0.022)), 0.1, gain=0.6)
    return finish(band(out, None, 2600), -22)


def seal_open(rng):
    # The lever's dull clank, then the sealed slab grinding down into the floor and stopping.
    out = silence(1.9)
    place(out, band(bell(N['G4'], 0.3, 0.06, brightness=0.5), None, 2400), 0.0, gain=0.6)
    s = 1.35
    grain = 0.5 + 0.5 * np.abs(norm(band(noise(s, rng), None, 22)))
    slab = norm(band(noise(s, rng, SR, 'brown'), 40, 260)) + 0.22 * norm(band(noise(s, rng), 600, 1800)) * grain
    place(out, slab * grain * env(s, 0.25, 0.12, hold=0.85), 0.22)
    place(out, osc(sweep(90, 45, 0.3, curve=0.5), 0.3) * env(0.3, 0.004, 0.07), 1.5, gain=0.9)
    return finish(band(out, None, 2000), -20)


def glint(rng):
    # Glint gained: two bright small notes. It waits a quarter second, so it follows the cue it comes
    # with (a creature freed, a cache picked up) instead of sitting on top of it.
    out = silence(0.52)
    place(out, bell(N['E6'], 0.3, 0.09, brightness=0.25), 0.0, gain=0.85)
    place(out, bell(N['A6'], 0.4, 0.12, brightness=0.25), 0.085)
    return lead(finish(band(out, None, 7000), -26), 0.24)


def cache(rng):
    # The pouch left where you fell, scooped up: cloth, and the coins shifting in it.
    out = silence(0.4)
    place(out, burst(rng, 0.2, 700, 2500, 0.06, 0.05), 0.0, gain=0.6)
    for i, n in enumerate(['D6', 'G6', 'E6']):
        place(out, band(bell(N[n], 0.1, 0.022, brightness=0.5), None, 5000), 0.1 + 0.055 * i, gain=0.6)
    return finish(out, -23)


def pay(rng):
    # Coins counted out at a build mark: four small ticks going down.
    out = silence(0.45)
    for i, n in enumerate(['A6', 'G6', 'E6', 'D6']):
        place(out, band(bell(N[n], 0.12, 0.03, brightness=0.5), None, 5000), 0.075 * i, gain=1 - 0.1 * i)
    return finish(out, -24)


def built(rng):
    # A building restored: two hammer taps and a warm chord opening. It starts after the coins.
    out = silence(1.55)
    for at in (0.0, 0.24):
        place(out, knock(600, 0.09, 0.02) + 0.5 * burst(rng, 0.09, 900, 2600, 0.001, 0.01), at, gain=0.8)
    for i, n in enumerate(['C5', 'E5', 'G5', 'C6']):
        place(out, bell(N[n], 0.9, 0.3, brightness=0.25), 0.5 + 0.07 * i, gain=0.9)
    place(out, osc(N['C4'], 0.9) * env(0.9, 0.2, 0.25, hold=0.15), 0.5, gain=0.25)
    return lead(finish(band(out, None, 6000), -18), 0.38)


def quest_start(rng):
    # A quest accepted: two rising notes.
    out = silence(0.85)
    place(out, bell(N['G5'], 0.6, 0.22), 0.0)
    place(out, bell(N['C6'], 0.7, 0.26), 0.13)
    return finish(band(out, None, 6000), -21)


def quest_done(rng):
    # A quest done: the old three-note chime, with a held note above it.
    out = silence(1.4)
    for i, n in enumerate(['C6', 'E6', 'G6']):
        place(out, bell(N[n], 0.8, 0.28 - 0.04 * i), 0.065 * i, gain=1 - 0.15 * i)
    place(out, osc(N['C7'], 1.0, vibrato=(5.5, 0.005)) * env(1.0, 0.02, 0.32), 0.26, gain=0.4)
    return finish(band(out, None, 6500), -19)


def tok(freq: float, peak: float):
    def make(rng):
        # The old app's small wooden "tok".
        s = 0.09
        x = osc(sweep(freq * 1.03, freq, s), s) * env(s, 0.002, 0.022)
        x += 0.3 * osc(freq * 1.5, s) * env(s, 0.001, 0.012)
        return finish(band(x, None, 4000), peak)
    return make


def ui_cancel(rng):
    # Back, or "not tonight": two quick low falling notes.
    out = silence(0.24)
    for i, n in enumerate(['E5', 'C5']):
        place(out, osc(N[n], 0.13, wave_='triangle') * env(0.13, 0.005, 0.04), 0.08 * i)
    return finish(band(out, None, 2400), -24)


def pause_pair(first: str, second: str):
    def make(rng):
        out = silence(0.26)
        for i, n in enumerate([first, second]):
            place(out, osc(N[n], 0.16) * env(0.16, 0.006, 0.045), 0.075 * i)
        return finish(band(out, None, 3000), -24)
    return make


def card_start(rng):
    # The opening card: a slow rise over an open fifth, like a morning.
    out = silence(1.95)
    for i, n in enumerate(['C5', 'E5', 'G5', 'A5']):
        place(out, osc(N[n], 1.0) * env(1.0, 0.03, 0.34), 0.2 * i, gain=0.9)
    place(out, (osc(N['C4'], 1.7) + 0.6 * osc(N['G4'], 1.7)) * env(1.7, 0.3, 0.45, hold=0.4), 0.0, gain=0.22)
    return finish(band(out, None, 3200), -20)


def card_end(rng):
    # The closing card: the same notes coming home to C.
    out = silence(1.95)
    for i, n in enumerate(['A5', 'G5', 'E5', 'C5']):
        place(out, osc(N[n], 1.0) * env(1.0, 0.03, 0.34), 0.2 * i, gain=0.9)
    chord = osc(N['C4'], 1.2) + 0.7 * osc(N['E4'], 1.2) + 0.6 * osc(N['G4'], 1.2)
    place(out, chord * env(1.2, 0.3, 0.3, hold=0.2), 0.7, gain=0.2)
    return finish(band(out, None, 3200), -20)


def rest(rng):
    # Resting at the hut: the old lullaby, shorter.
    out = silence(1.7)
    for i, n in enumerate(['G5', 'E5', 'C5']):
        place(out, osc(N[n], 0.95) * env(0.95, 0.03, 0.36), 0.25 * i, gain=1 - 0.1 * i)
    place(out, osc(N['C4'], 1.3) * env(1.3, 0.25, 0.4, hold=0.2), 0.1, gain=0.25)
    return finish(band(out, None, 3000), -22)


# --------------------------------------------------------------- first night

def horn_call(seconds: float, freq: float) -> np.ndarray:
    f = sweep(freq * 0.97, freq, seconds, curve=0.3)
    call = sum((0.55 ** k) * osc(f * k, seconds, vibrato=(4.5, 0.004)) for k in range(1, 6))
    return call * env(seconds, 0.12, 0.16, hold=max(seconds - 0.5, 0.05))


def raid_horn(rng):
    # A horn from the halt road, far off (G3): a short call and a long one, low-passed so it is distance
    # and never an alarm, with one soft echo off the houses.
    out = silence(1.95)
    place(out, horn_call(0.4, N['G3']), 0.0, gain=0.8)
    place(out, horn_call(1.0, N['G3']), 0.5)
    dry = band(out, None, 1100)
    wet = silence(1.95)
    place(wet, band(dry, None, 600), 0.19, gain=0.25)
    return finish(dry + wet, -20)


def raid_bell(rng):
    # "Ring the bell": two strikes of the village bell (C5 over its C4 hum).
    out = silence(1.95)
    for i, at in enumerate((0.0, 0.62)):
        strike = bell(N['C5'], 1.3, 0.42, brightness=0.5) + 0.45 * osc(N['C4'], 1.3) * env(1.3, 0.01, 0.6)
        place(out, strike, at, gain=1 - 0.12 * i)
    return finish(band(out, None, 5500), -18)


def hurdle_hit(rng):
    # A hurdle battered: a blow on wood and the rails rattling.
    out = silence(0.28)
    place(out, norm(knock(230, 0.14, 0.035, wood=0.6)), 0.0)
    place(out, norm(burst(rng, 0.1, 300, 1500, 0.002, 0.02)), 0.0, gain=0.4)
    for at in (0.07, 0.13):
        place(out, norm(knock(430 + 120 * rng.random(), 0.06, 0.012)), at, gain=0.35)
    return finish(band(out, None, 2800), -22)


def hurdle_break(rng):
    # A hurdle broken: one crack, and the rails coming down on the road.
    out = silence(0.78)
    place(out, norm(burst(rng, 0.08, 400, 3000, 0.001, 0.018)), 0.0, gain=0.7)
    place(out, norm(knock(200, 0.16, 0.04, wood=0.6)), 0.0, gain=0.8)
    for i, at in enumerate(np.sort(0.12 + 0.45 * rng.random(5))):
        place(out, norm(knock(220 + 160 * rng.random(), 0.1, 0.022, wood=0.6)), at, gain=0.7 - 0.09 * i)
    return finish(band(out, None, 3200), -19)


def lantern_hit(rng):
    # The lantern struck: glass and iron ringing dully, over the blow. A worry, kept soft.
    out = silence(0.52)
    place(out, band(bell(N['A5'], 0.5, 0.12, brightness=0.5), None, 3600), 0.0)
    place(out, osc(sweep(140, 60, 0.2, curve=0.5), 0.2) * env(0.2, 0.002, 0.05), 0.0, gain=0.6)
    return finish(out, -20)


def raid_wave(rng):
    # A wave on the halt road: two low pulses (the old app's raid cue with one pulse fewer). Brief, and
    # no alarm.
    out = silence(0.52)
    for i in range(2):
        s = 0.2
        tone = osc(N['A3'], s, wave_='triangle') + 0.5 * osc(N['E4'], s, wave_='triangle')
        place(out, tone * env(s, 0.012, 0.065), 0.22 * i, gain=1 - 0.15 * i)
    return finish(band(out, None, 1600), -22)


def night_won(rng):
    # The lantern held: a rising run and a held note over it.
    out = silence(1.9)
    for i, n in enumerate(['C5', 'E5', 'G5', 'C6', 'E6']):
        place(out, bell(N[n], 0.6, 0.2), 0.075 * i, gain=0.8)
    place(out, osc(N['G6'], 1.2, vibrato=(6, 0.005)) * env(1.2, 0.02, 0.42), 0.4, gain=0.6)
    place(out, osc(N['C4'], 1.3) * env(1.3, 0.2, 0.4, hold=0.2), 0.3, gain=0.2)
    return finish(band(out, None, 7000), -18)


def night_lost(rng):
    # The night lost: three slow low notes down. Nothing is taken, so it only sighs.
    out = silence(1.5)
    for i, n in enumerate(['A4', 'E4', 'C4']):
        place(out, osc(N[n], 0.8, wave_='triangle') * env(0.8, 0.02, 0.26), 0.3 * i, gain=1 - 0.08 * i)
    return finish(band(out, None, 1800), -21)


# ------------------------------------------------------------------ ambience

def amb_woodland(rng):
    """The woodland by day: wind in the crowns, leaves stirring three times, birds near and far."""
    sr = AMB_SR
    total = LOOP_SECONDS + LOOP_OVERLAP
    out = 0.5 * wind(rng, total, sr, 520)
    for at in np.sort(rng.random(3)) * (total - 1):
        leaves = band(noise(0.7, rng, sr), 1800, 5000, sr) * env(0.7, 0.2, 0.18, sr, hold=0.1)
        place(out, leaves, at, sr, gain=0.12)
    for i in range(8):
        far = rng.random() < 0.4
        phrase = chirp_phrase(rng, sr, low=2300.0, spread=1000.0)
        if far:
            phrase = band(phrase, None, 3000, sr)
        place(out, phrase, (i + 0.8 * rng.random()) * total / 8, sr, gain=0.09 if far else 0.19)
    return finish(loopable(out, LOOP_SECONDS, sr, LOOP_OVERLAP), -24, sr, edges=False)


def amb_crossroads(rng):
    """Crossroads: a quiet village bed. Low wind between the houses, sparrows kept far, a dove once, a
    sign creaking on its hooks twice, and one soft far bell note."""
    sr = AMB_SR
    total = LOOP_SECONDS + LOOP_OVERLAP
    out = 0.42 * wind(rng, total, sr, 420)
    for i in range(5):
        phrase = band(chirp_phrase(rng, sr, low=2100.0, spread=800.0), None, 2800, sr)
        place(out, phrase, (i + 0.8 * rng.random()) * total / 5, sr, gain=0.09)
    coo = silence(1.1, sr)
    for k, note in enumerate(('G4', 'E4', 'E4')):
        place(coo, osc(N[note], 0.28, sr) * env(0.28, 0.05, 0.1, sr, hold=0.06), 0.33 * k, sr)
    place(out, band(coo, None, 1200, sr), 6.0 + 3 * rng.random(), sr, gain=0.13)
    for at in (2.0 + 2 * rng.random(), 12.0 + 3 * rng.random()):
        t = times(0.5, sr)
        creak = osc(sweep(300, 345, 0.5, sr), 0.5, sr, wave_='triangle') * (0.6 + 0.4 * np.sin(2 * np.pi * 21 * t) ** 2)
        place(out, band(creak * env(0.5, 0.15, 0.12, sr, hold=0.1), None, 900, sr), at, sr, gain=0.05)
    far_bell = band(bell(N['C5'], 1.6, 0.5, sr, brightness=0.2), None, 2400, sr)
    place(out, far_bell, 15.0 + rng.random(), sr, gain=0.07)
    return finish(loopable(out, LOOP_SECONDS, sr, LOOP_OVERLAP), -24, sr, edges=False)


def amb_undercroft(rng):
    """The Undercroft: low cave air that breathes slowly, a hollow tone in the vaults (C3 and its fifth,
    barely there), and water dripping at uneven times, each drop with two soft echoes."""
    sr = AMB_SR
    total = LOOP_SECONDS + LOOP_OVERLAP
    t = times(total, sr)
    breathe = 0.7 + 0.3 * np.sin(2 * np.pi * 0.055 * t + 0.6)
    out = 0.5 * norm(band(noise(total, rng, sr, 'brown'), 70, 320, sr, order=2)) * breathe
    out += 0.12 * norm(band(noise(total, rng, sr, 'pink'), 320, 1100, sr, order=2)) * breathe
    for note, level in (('C3', 0.1), ('G3', 0.05)):
        hollow = norm(band(noise(total, rng, sr), N[note] - 8, N[note] + 8, sr, order=2))
        out += level * hollow * (0.5 + 0.5 * np.sin(2 * np.pi * 0.04 * t + (1.1 if note == 'G3' else 0.0)))
    at = 0.8 + rng.random()
    while at < total - 0.6:
        f0 = 900 + 800 * rng.random()
        drop = osc(sweep(f0, f0 * 1.5, 0.035, sr), 0.035, sr) * env(0.035, 0.002, 0.01, sr)
        level = 0.1 + 0.1 * rng.random()
        place(out, drop, at, sr, gain=level)
        for delay, share in ((0.11, 0.35), (0.23, 0.15)):
            place(out, band(drop, None, 1400, sr), at + delay, sr, gain=level * share)
        at += 1.6 + 2.4 * rng.random()
    return finish(loopable(out, LOOP_SECONDS, sr, LOOP_OVERLAP), -24, sr, edges=False)


def amb_night(rng):
    """The first night: crickets in two voices, low wind, and two slow gusts down the halt road. No owl:
    the night is waiting, not asleep."""
    sr = AMB_SR
    total = LOOP_SECONDS + LOOP_OVERLAP
    out = 0.38 * wind(rng, total, sr, 380)
    out += cricket(rng, total, sr, 4150, 0.78, 0.15)
    out += cricket(rng, total, sr, 3700, 1.05, 0.085)
    gust = gusts(total, sr, (4.0 + 2 * rng.random(), 13.0 + 2 * rng.random()), 1.8)
    out += 0.16 * norm(band(noise(total, rng, sr, 'pink'), 300, 900, sr)) * (0.02 + 0.98 * gust ** 2)
    return finish(loopable(out, LOOP_SECONDS, sr, LOOP_OVERLAP), -24, sr, edges=False)


# ------------------------------------------------------------------ the list
# cue: (maker or makers, tier, what it is and where it plays). A list of makers is a cue with variants,
# played in turn. Tiers (game/core/sound_rules.gd): confirm always answers, moment plays while effects
# are on, flavour at most one per 600 ms and none with Gentle sound, step is the footsteps' own.
STEP_VARIANTS = 4
EFFECTS: dict[str, tuple] = {
    'step_grass': ([make_step('grass')] * STEP_VARIANTS, 'step', 'a footstep on grass or earth'),
    'step_stone': ([make_step('stone')] * STEP_VARIANTS, 'step', 'a footstep on paving or the vault floor'),
    'step_wood': ([make_step('wood')] * STEP_VARIANTS, 'step', 'a footstep on the footbridge'),
    'bow_draw': (bow_draw, 'flavour', 'the bow creaking as it is drawn'),
    'bow_release': (bow_release, 'moment', 'the string and the arrow leaving'),
    'arrow_hit': (arrow_hit, 'moment', 'an arrow that counts on a creature (the creature hurt)'),
    # a moment, not flavour: it follows the bow's creak by half a second, inside the flavour's own gap
    'arrow_wall': (arrow_wall, 'moment', 'an arrow stopping at a solid'),
    'glance': (glance, 'moment', 'an arrow from beyond reach: a small dull clink'),
    'roll': (roll, 'moment', 'the roll'),
    'hurt': (hurt, 'moment', 'the player hurt'),
    'downed': (downed, 'moment', 'the player going down'),
    'get_up': (get_up, 'moment', 'getting up at the zone\'s start'),
    'tell_mossling': (tell_mossling, 'moment', 'a mossling winding up'),
    'tell_rusher': (tell_rusher, 'moment', 'a boarlet winding up'),
    'tell_shooter': (tell_shooter, 'moment', 'a toad winding up'),
    'tell_shield': (tell_shield, 'moment', 'a mossback winding up'),
    'tell_elite': (tell_elite, 'moment', 'the horned elite winding up'),
    'enemy_strike': (enemy_strike, 'moment', 'a creature lunging'),
    'enemy_spit': (enemy_spit, 'moment', 'the toad\'s shot leaving'),
    'enemy_freed': (enemy_freed, 'moment', 'a creature freed'),
    'boss_tell_charge': (boss_tell_charge, 'moment', 'the Thornback pawing before a charge'),
    'boss_tell_volley': (boss_tell_volley, 'moment', 'the Thornback rattling before a volley'),
    'boss_tell_slam': (boss_tell_slam, 'moment', 'the Thornback rearing before a slam'),
    'boss_charge': (boss_charge, 'moment', 'the charge'),
    'boss_volley': (boss_volley, 'moment', 'the thorns leaving'),
    'boss_slam': (boss_slam, 'moment', 'the slam landing'),
    'boss_roar': (boss_roar, 'moment', 'the Thornback\'s second phase'),
    'boss_stagger': (boss_stagger, 'moment', 'the Thornback staggered'),
    'boss_freed': (boss_freed, 'moment', 'the Thornback freed'),
    'door': (door, 'moment', 'walking from one zone into another'),
    'door_stone': (door_stone, 'moment', 'the hatch and the stair of the Undercroft'),
    'plate': (plate, 'moment', 'the Undercroft\'s plate going down'),
    'seal_open': (seal_open, 'moment', 'the lever pulled and the seal sinking'),
    'glint': (glint, 'moment', 'Glint gained'),
    'cache': (cache, 'moment', 'the downed cache picked up'),
    'pay': (pay, 'moment', 'Glint paid at a build mark'),
    'built': (built, 'moment', 'a building restored'),
    'quest_start': (quest_start, 'moment', 'a quest accepted'),
    'quest_done': (quest_done, 'moment', 'a quest done'),
    'talk': (tok(N['G5'], -24), 'confirm', 'a line opening or turning'),
    'ui_confirm': (tok(N['C6'], -22), 'confirm', 'a menu choice'),
    'ui_cancel': (ui_cancel, 'confirm', 'back, or "not tonight"'),
    'pause_open': (pause_pair('G5', 'D5'), 'confirm', 'the pause menu opening'),
    'pause_close': (pause_pair('D5', 'G5'), 'confirm', 'the pause menu closing'),
    'card_start': (card_start, 'moment', 'the opening card'),
    'card_end': (card_end, 'moment', 'the closing card'),
    'rest': (rest, 'moment', 'resting at the hut'),
    'raid_horn': (raid_horn, 'moment', 'the night announced: a horn from the halt road'),
    'raid_bell': (raid_bell, 'moment', 'the bell rung'),
    'raid_wave': (raid_wave, 'moment', 'a wave arriving'),
    'hurdle_hit': (hurdle_hit, 'moment', 'a hurdle battered'),
    'hurdle_break': (hurdle_break, 'moment', 'a hurdle broken'),
    'lantern_hit': (lantern_hit, 'moment', 'the lantern struck'),
    'night_won': (night_won, 'moment', 'the night won'),
    'night_lost': (night_lost, 'moment', 'the night lost'),
}
AMBIENCE: dict[str, tuple] = {
    'woodland': (amb_woodland, 'the woodland by day: wind and birds'),
    'crossroads': (amb_crossroads, 'Crossroads: a quiet village bed'),
    'undercroft': (amb_undercroft, 'the Undercroft: low cave air and drips'),
    'night': (amb_night, 'the first night: crickets and low wind'),
}


# ------------------------------------------------------------------ building

def wav_bytes(x: np.ndarray, sr: int) -> bytes:
    """The same 16-bit mono WAV write_wav makes, as bytes (through a temporary file is not needed)."""
    import io
    import wave
    pcm = np.clip(np.round(x * 32767), -32768, 32767).astype('<i2')
    buf = io.BytesIO()
    with wave.open(buf, 'wb') as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(sr)
        f.writeframes(pcm.tobytes())
    return buf.getvalue()


def peak_db(x: np.ndarray) -> float:
    return float(20 * np.log10(np.max(np.abs(x)) + 1e-12))


def build() -> tuple[dict[str, bytes], dict[str, np.ndarray], dict]:
    """Every file as bytes, every signal (for the checks and the measurements) and the cue table."""
    files: dict[str, bytes] = {}
    signals: dict[str, np.ndarray] = {}
    table = {
        '_about': 'Generated by scripts/audio/game_sounds.py (npm run sound:game). Do not edit by hand. '
                  'game/core/sound.gd reads it: each effect cue with its files (several are variants played in '
                  'turn), its tier (game/core/sound_rules.gd) and its length; each ambience loop with its frames.',
        'effects': {},
        'ambience': {},
    }
    for name, (makers, tier, what) in EFFECTS.items():
        if tier not in TIERS:
            raise SystemExit(f'{name}: unknown tier {tier!r}')
        many = isinstance(makers, list)
        paths = []
        longest = 0.0
        for i, make in enumerate(makers if many else [makers]):
            stem = f'{name}_{i + 1}' if many else name
            x = make(rng_for(stem))
            path = f'sfx/{stem}.wav'
            files[path] = wav_bytes(x, SR)
            signals[path] = x
            paths.append(path)
            longest = max(longest, len(x) / SR)
        table['effects'][name] = {'files': paths, 'tier': tier, 'seconds': round(longest, 3), 'what': what}
    for name, (make, what) in AMBIENCE.items():
        x = make(rng_for('ambience_' + name))
        path = f'ambience/{name}.wav'
        files[path] = wav_bytes(x, AMB_SR)
        signals[path] = x
        table['ambience'][name] = {'file': path, 'rate': AMB_SR, 'frames': len(x),
                                   'seconds': round(len(x) / AMB_SR, 3), 'what': what}
    files['cues.json'] = (json.dumps(table, indent=1) + '\n').encode()
    return files, signals, table


def seam(x: np.ndarray) -> tuple[float, float]:
    """A loop's join: the step from its last sample to its first, and the RMS of the steps inside it.
    A seamless loop's join is no larger than its own ordinary sample-to-sample movement."""
    return float(abs(x[0] - x[-1])), float(np.sqrt(np.mean(np.diff(x) ** 2)))


def centroid(x: np.ndarray, sr: int) -> float:
    spec = np.abs(np.fft.rfft(x * np.hanning(len(x)))) ** 2
    freqs = np.fft.rfftfreq(len(x), 1 / sr)
    return float(np.sum(freqs * spec) / (np.sum(spec) + 1e-20))


def shape_failures(files: dict[str, bytes], signals: dict[str, np.ndarray]) -> list[str]:
    """What check:sound-repro holds every file to, beyond its bytes."""
    bad = []
    for path, x in signals.items():
        level = peak_db(x)
        if path.startswith('sfx/'):
            seconds = len(x) / SR
            if not 0.05 < seconds <= 2.0:
                bad.append(f'{path}: {seconds:.2f} s is not a short effect (0.05 to 2 s)')
            if abs(x[0]) > 0.001 or abs(x[-1]) > 0.0005:
                bad.append(f'{path}: does not start and end in silence ({x[0]:.4f}, {x[-1]:.4f})')
            if not -28.5 <= level <= -17.5:
                bad.append(f'{path}: peaks at {level:.1f} dBFS, outside -18 to -28')
        else:
            if abs(level + 24.0) > 0.2:
                bad.append(f'{path}: peaks at {level:.1f} dBFS, not -24')
            join, step = seam(x)
            if join > step:
                bad.append(f'{path}: the loop joins with a step of {join:.5f}, larger than its ordinary step ({step:.5f} RMS)')
    total = sum(len(b) for p, b in files.items() if p.endswith('.wav'))
    if total > BUDGET_BYTES:
        bad.append(f'the palette is {total} bytes, over its {BUDGET_BYTES} byte budget')
    return bad


def on_disk() -> dict[str, bytes]:
    found = {}
    for folder, _dirs, names in os.walk(OUT):
        for name in names:
            if name.endswith('.wav') or name == 'cues.json':
                full = os.path.join(folder, name)
                with open(full, 'rb') as f:
                    found[os.path.relpath(full, OUT).replace(os.sep, '/')] = f.read()
    return found


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    parser.add_argument('--check', action='store_true', help='compare with the committed files; write nothing')
    parser.add_argument('--measure', action='store_true', help='print peak, RMS, length and centroid per file')
    args = parser.parse_args()
    files, signals, _table = build()
    if args.measure:
        print('| file | seconds | peak dBFS | RMS dBFS | centroid Hz |')
        print('| --- | ---: | ---: | ---: | ---: |')
        for path, x in signals.items():
            sr = SR if path.startswith('sfx/') else AMB_SR
            rms = 20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-12)
            print(f'| {path} | {len(x) / sr:.2f} | {peak_db(x):.1f} | {rms:.1f} | {centroid(x, sr):.0f} |')
        for path, x in signals.items():
            if path.startswith('ambience/'):
                join, step = seam(x)
                print(f'seam {path}: join step {join:.6f}, RMS step inside {step:.6f}')
        print(f'total {sum(len(b) for p, b in files.items() if p.endswith(".wav"))} bytes of WAV')
        return
    failures = shape_failures(files, signals)
    if args.check:
        disk = on_disk()
        for path in sorted(set(files) | set(disk)):
            if path not in disk:
                failures.append(f'{path}: not committed (run npm run sound:game)')
            elif path not in files:
                failures.append(f'{path}: on disk but no cue makes it')
            elif disk[path] != files[path]:
                failures.append(f'{path}: differs from what the generator writes')
        for failure in failures:
            print(f'FAIL: {failure}')
        if failures:
            raise SystemExit(1)
        print(f'PASS: {len(files) - 1} game sounds reproduce the committed bytes and keep their shape '
              f'({sum(len(b) for p, b in files.items() if p.endswith(".wav"))} bytes of {BUDGET_BYTES}).')
        return
    if failures:
        for failure in failures:
            print(f'FAIL: {failure}')
        raise SystemExit(1)
    stale = set(on_disk()) - set(files)
    for path in stale:
        os.remove(os.path.join(OUT, path))
        for extra in ('.import',):
            if os.path.exists(os.path.join(OUT, path + extra)):
                os.remove(os.path.join(OUT, path + extra))
    for path, data in files.items():
        full = os.path.join(OUT, path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, 'wb') as f:
            f.write(data)
    print(f'wrote {len(files) - 1} sounds and cues.json to {os.path.relpath(OUT, ROOT)}')


if __name__ == '__main__':
    main()
