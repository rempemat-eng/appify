"""NapAttack sound palette, synthesised from code like the pixel art.

Run with `npm run sound`. Writes assets/sounds/*.wav and lib/sound-assets.ts.

Style (see docs/vision/sound.md):
- soft and warm: sine and triangle tones, gentle attacks, low-passed noise;
- notes come from the C major pentatonic scale, so any two cues sound kind together;
- every effect is short and finite; only the ambience loops repeat (the garden's day and
  night, and one for each kind of place out in the world);
- loudness is baked into each file (iOS Safari ignores programmatic volume),
  so players always run at volume 1.

Deterministic: a fixed seed per sound, so regenerating gives identical files.
"""

from __future__ import annotations

import json
import os
import wave

import numpy as np
from scipy import signal

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = os.path.join(ROOT, 'assets', 'sounds')
TS = os.path.join(ROOT, 'lib', 'sound-assets.ts')

SR = 22050  # effects
AMB_SR = 16000  # ambience loops: smaller files, nothing above 6 kHz
LOOP_SECONDS = 20.0

# C major pentatonic, by note name
NOTE = {
    'C4': 261.63, 'D4': 293.66, 'E4': 329.63, 'G4': 392.00, 'A4': 440.00,
    'C5': 523.25, 'D5': 587.33, 'E5': 659.25, 'G5': 783.99, 'A5': 880.00,
    'C6': 1046.50, 'D6': 1174.66, 'E6': 1318.51, 'G6': 1567.98, 'A6': 1760.00,
    'C7': 2093.00,
}


# ---------------------------------------------------------------- primitives

def silence(seconds: float, sr: int = SR) -> np.ndarray:
    return np.zeros(int(round(seconds * sr)))


def times(seconds: float, sr: int = SR) -> np.ndarray:
    return np.arange(int(round(seconds * sr))) / sr


def sweep(f0: float, f1: float, seconds: float, sr: int = SR, curve: float = 1.0) -> np.ndarray:
    """Instantaneous frequency gliding from f0 to f1 (curve > 1 eases in)."""
    t = times(seconds, sr)
    x = (t / seconds) ** curve if seconds > 0 else t
    return f0 + (f1 - f0) * x


def osc(freq, seconds: float, sr: int = SR, wave_: str = 'sine', vibrato=(0.0, 0.0)) -> np.ndarray:
    """Phase-accumulating oscillator; `freq` may be a number or an array."""
    n = int(round(seconds * sr))
    f = np.full(n, float(freq)) if np.isscalar(freq) else np.asarray(freq, dtype=float)[:n]
    if vibrato[0] > 0:
        rate, depth = vibrato
        f = f * (1 + depth * np.sin(2 * np.pi * rate * np.arange(n) / sr))
    phase = 2 * np.pi * np.cumsum(f) / sr
    if wave_ == 'triangle':
        return (2 / np.pi) * np.arcsin(np.sin(phase))
    return np.sin(phase)


def env(seconds: float, attack: float, decay: float, sr: int = SR, hold: float = 0.0) -> np.ndarray:
    """Soft attack, optional hold, then an exponential decay (time constant `decay`)."""
    t = times(seconds, sr)
    a = np.clip(t / max(attack, 1e-4), 0, 1)
    a = np.sin(a * np.pi / 2) ** 2  # smooth start, no click
    tail = np.where(t > attack + hold, np.exp(-(t - attack - hold) / max(decay, 1e-4)), 1.0)
    return a * tail


def noise(seconds: float, rng: np.random.Generator, sr: int = SR, colour: str = 'white') -> np.ndarray:
    n = int(round(seconds * sr))
    white = rng.standard_normal(n)
    if colour == 'white':
        return white / 3
    if colour == 'brown':
        b = np.cumsum(white)
        b = signal.sosfilt(signal.butter(1, 20, 'highpass', fs=sr, output='sos'), b)
        return b / (np.max(np.abs(b)) + 1e-9)
    # pink: -3 dB/octave via a standard three-pole approximation
    b = [0.049922035, -0.095993537, 0.050612699, -0.004408786]
    a = [1, -2.494956002, 2.017265875, -0.522189400]
    p = signal.lfilter(b, a, white)
    return p / (np.max(np.abs(p)) + 1e-9)


def band(x: np.ndarray, lo: float | None, hi: float | None, sr: int = SR, order: int = 4) -> np.ndarray:
    if lo and hi:
        sos = signal.butter(order, [lo, hi], 'bandpass', fs=sr, output='sos')
    elif lo:
        sos = signal.butter(order, lo, 'highpass', fs=sr, output='sos')
    else:
        sos = signal.butter(order, hi, 'lowpass', fs=sr, output='sos')
    return signal.sosfilt(sos, x)


def place(dst: np.ndarray, src: np.ndarray, at: float, sr: int = SR, gain: float = 1.0) -> None:
    i = int(round(at * sr))
    j = min(len(dst), i + len(src))
    if i < len(dst):
        dst[i:j] += gain * src[: j - i]


def bell(freq: float, seconds: float, decay: float, sr: int = SR, brightness: float = 0.35) -> np.ndarray:
    """A soft glockenspiel-like tone: fundamental plus quickly fading inharmonic partials."""
    tone = osc(freq, seconds, sr) * env(seconds, 0.004, decay, sr)
    tone += brightness * osc(freq * 2.76, seconds, sr) * env(seconds, 0.002, decay * 0.35, sr)
    tone += 0.12 * brightness * osc(freq * 5.4, seconds, sr) * env(seconds, 0.001, decay * 0.15, sr)
    return tone


def finish(x: np.ndarray, peak_db: float, sr: int = SR, edges: bool = True) -> np.ndarray:
    """Remove DC, fade in briefly and release smoothly, normalise to a peak level (dBFS).

    The release covers the last quarter of the sound (at most 0.15 s), so a
    ringing tail always reaches silence instead of being cut off with a click.
    Loops pass edges=False: their ends already join seamlessly.
    """
    x = x - np.mean(x)
    if edges:
        attack = int(0.004 * sr)
        release = int(min(0.15, 0.25 * len(x) / sr) * sr)
        x[:attack] *= np.sin(np.linspace(0, np.pi / 2, attack)) ** 2
        x[-release:] *= np.cos(np.linspace(0, np.pi / 2, release)) ** 2
    peak = np.max(np.abs(x)) + 1e-9
    return x / peak * (10 ** (peak_db / 20))


def loopable(x: np.ndarray, seconds: float, sr: int, overlap: float = 2.0) -> np.ndarray:
    """Equal-power crossfade of the extra tail into the head, so the loop has no seam."""
    n = int(seconds * sr)
    k = int(overlap * sr)
    assert len(x) >= n + k
    body = x[:n].copy()
    tail = x[n:n + k]
    t = np.linspace(0, 1, k)
    body[:k] = body[:k] * np.sin(t * np.pi / 2) + tail * np.cos(t * np.pi / 2)
    return body


# ------------------------------------------------------------------- effects

def tap(rng):
    # A small wooden "tok": the default press for buttons and choices.
    s = 0.09
    f = sweep(NOTE['C6'] * 1.03, NOTE['C6'], s)
    x = osc(f, s) * env(s, 0.002, 0.022)
    x += 0.3 * osc(NOTE['G6'], s) * env(s, 0.001, 0.012)
    return finish(band(x, None, 4000), -17)


def chime(rng):
    out = silence(1.05)
    for i, n in enumerate(['C6', 'E6', 'G6']):
        place(out, bell(NOTE[n], 0.8, 0.28 - 0.04 * i), 0.065 * i, gain=1 - 0.15 * i)
    return finish(band(out, None, 6000), -15)


def oops(rng):
    out = silence(0.42)
    for i, n in enumerate(['A4', 'E4']):
        s = 0.2
        place(out, osc(NOTE[n], s, wave_='triangle') * env(s, 0.006, 0.07), 0.12 * i)
    return finish(band(out, None, 2200), -19)


def hit(rng):
    s = 0.3
    thump = osc(sweep(150, 55, s, curve=0.5), s) * env(s, 0.002, 0.055)
    click = band(noise(s, rng), None, 1800) * env(s, 0.001, 0.012)
    return finish(thump + 0.6 * click, -13)


def raid(rng):
    out = silence(0.75)
    for i in range(3):
        s = 0.18
        tone = osc(NOTE['A4'] / 2, s, wave_='triangle') + 0.5 * osc(NOTE['E4'], s, wave_='triangle')
        place(out, tone * env(s, 0.01, 0.06), 0.2 * i, gain=1 - 0.12 * i)
    return finish(band(out, None, 1800), -15)


def nap(rng):
    # A tiny lullaby: three falling notes over a soft low C.
    out = silence(2.0)
    for i, n in enumerate(['G5', 'E5', 'C5']):
        s = 1.1
        place(out, osc(NOTE[n], s) * env(s, 0.03, 0.42), 0.27 * i, gain=1 - 0.1 * i)
    pad = osc(NOTE['C4'], 1.5) * env(1.5, 0.25, 0.5, hold=0.2)
    place(out, pad, 0.1, gain=0.25)
    return finish(band(out, None, 3000), -17)


def wake(rng):
    out = silence(1.05)
    for i, n in enumerate(['C5', 'E5', 'G5', 'C6']):
        s = 0.6
        tone = osc(NOTE[n], s, wave_='triangle') * env(s, 0.006, 0.2)
        place(out, band(tone, None, 3500), 0.1 * i, gain=0.8 + 0.07 * i)
    return finish(out, -16)


def friend(rng):
    out = silence(1.5)
    place(out, bell(NOTE['G5'], 0.6, 0.22), 0.0)
    place(out, bell(NOTE['C6'], 0.6, 0.22), 0.12)
    last = osc(NOTE['E6'], 1.2, vibrato=(5.5, 0.006)) * env(1.2, 0.01, 0.3)
    place(out, last, 0.24)
    return finish(band(out, None, 6000), -15)


def levelup(rng):
    out = silence(1.4)
    for i, n in enumerate(['C5', 'E5', 'G5', 'C6', 'E6']):
        place(out, bell(NOTE[n], 0.5, 0.16), 0.06 * i, gain=0.75)
    held = osc(NOTE['G6'], 1.0, vibrato=(6, 0.005)) * env(1.0, 0.02, 0.4)
    place(out, held, 0.32, gain=0.7)
    return finish(band(out, None, 7000), -14)


def reward(rng):
    # Grass sparkle: a quick climb up the pentatonic scale.
    out = silence(0.8)
    for i, n in enumerate(['C6', 'D6', 'E6', 'G6', 'A6', 'C7']):
        place(out, bell(NOTE[n], 0.35, 0.1, brightness=0.25), 0.042 * i, gain=0.6 + 0.06 * i)
    return finish(band(out, None, 7500), -16)


def footstep(rng, sr=SR):
    s = 0.09
    body = band(noise(s, rng, sr, 'brown'), None, 700 + 150 * rng.random(), sr) * env(s, 0.004, 0.03, sr)
    thump = osc(85 + 15 * rng.random(), s, sr) * env(s, 0.003, 0.025, sr)
    grass = band(noise(s, rng, sr), 2500, 6000, sr) * env(s, 0.002, 0.02, sr)
    return body + 0.5 * thump + 0.08 * grass


def steps(rng):
    out = silence(1.15)
    for i, gain in enumerate([1.0, 0.85, 0.72, 0.58]):
        place(out, footstep(rng), 0.04 + 0.26 * i + 0.015 * rng.standard_normal(), gain=gain)
    return finish(out, -19)


def splash(rng):
    out = silence(0.7)
    plop = osc(sweep(260, 900, 0.05, curve=0.6), 0.05) * env(0.05, 0.002, 0.018)
    place(out, plop, 0.0)
    wash = band(noise(0.5, rng), 450, 2600) * env(0.5, 0.01, 0.12)
    place(out, wash, 0.02, gain=0.9)
    for at in sorted(0.15 + 0.3 * rng.random(3)):
        f0 = 1300 + 600 * rng.random()
        drop = osc(sweep(f0, f0 * 1.6, 0.03), 0.03) * env(0.03, 0.002, 0.008)
        place(out, drop, at, gain=0.45)
    return finish(band(out, None, 5000), -17)


def page(rng):
    # A paper swish: noise whose band rises as the page lifts, a soft crinkle
    # grain, then a small flap as it lands.
    s = 0.5
    t = times(s)
    rising = band(noise(s, rng), 1200, 3200) * (1 - t / s) + band(noise(s, rng), 3000, 7000) * (t / s)
    crinkle = band(noise(s, rng), None, 60)
    crinkle = 0.7 + 0.3 * crinkle / (np.max(np.abs(crinkle)) + 1e-9)
    swish = rising * crinkle * env(s, 0.12, 0.08, hold=0.06)
    flap = band(noise(0.06, rng), None, 1100) * env(0.06, 0.002, 0.014)
    out = swish.copy()
    place(out, flap, 0.3, gain=0.7)
    return finish(out, -21)


def water(rng):
    s = 1.0
    out = band(noise(s, rng), 2000, 5200) * env(s, 0.12, 0.3, hold=0.45) * 0.25
    for at in np.sort(rng.random(36) * 0.85):
        f0 = 1800 + 1700 * rng.random()
        d = 0.018
        drop = osc(sweep(f0, f0 * 1.35, d), d) * env(d, 0.001, 0.005)
        place(out, drop, at, gain=0.35 + 0.3 * rng.random())
    out *= env(s, 0.08, 0.28, hold=0.5)
    return finish(band(out, None, 6500), -21)


def rustle(rng):
    s = 0.65
    grain = 0.55 + 0.45 * np.abs(band(noise(s, rng), None, 30))
    grain /= np.max(grain)
    out = band(noise(s, rng), 1800, 6800) * grain * env(s, 0.08, 0.14, hold=0.12)
    return finish(out, -23)


def lantern(rng):
    s = 1.7
    ting = osc(NOTE['A6'], s) * env(s, 0.002, 0.36) + 0.4 * osc(NOTE['A6'] * 1.5, s) * env(s, 0.002, 0.2)
    glow = osc(NOTE['A4'] / 2, s) * env(s, 0.15, 0.3, hold=0.1)
    return finish(band(ting + 0.3 * glow, None, 6000), -19)


def boop(rng):
    out = silence(0.32)
    first = osc(sweep(360, 520, 0.11, curve=0.7), 0.11, wave_='triangle') * env(0.11, 0.008, 0.04)
    second = osc(sweep(440, 620, 0.08, curve=0.7), 0.08, wave_='triangle') * env(0.08, 0.006, 0.03)
    place(out, first, 0.0)
    place(out, second, 0.15, gain=0.6)
    return finish(band(out, None, 2500), -17)


def munch(rng):
    out = silence(0.5)
    for i in range(3):
        s = 0.06
        crunch = band(noise(s, rng), 900, 3800) * env(s, 0.002, 0.016)
        thump = osc(140, s) * env(s, 0.002, 0.02)
        place(out, crunch + 0.4 * thump, 0.11 * i + 0.01 * rng.random(), gain=1 - 0.15 * i)
    return finish(out, -19)


# ------------------------------------------------------------------ ambience

def chirp_phrase(rng, sr, low=2400.0, spread=1100.0):
    """One small bird phrase: two to five quick up- or down-swept notes, starting
    between `low` and `low + spread` Hz (lower birds suit a loop stored at 8 kHz)."""
    notes = int(rng.integers(2, 6))
    base = low + spread * rng.random()
    out = silence(1.2, sr)
    at = 0.0
    for _ in range(notes):
        d = 0.05 + 0.07 * rng.random()
        span = (300 + 600 * rng.random()) * (1 if rng.random() < 0.6 else -1)
        f = sweep(base, base + span, d, sr, curve=0.7)
        tone = osc(f, d, sr, vibrato=(28, 0.01)) * env(d, 0.006, d * 0.45, sr)
        place(out, tone, at, sr)
        at += d + 0.03 + 0.08 * rng.random()
    return out


def wind(rng, seconds, sr, cutoff):
    w = band(noise(seconds, rng, sr, 'brown'), None, cutoff, sr, order=2)
    t = times(seconds, sr)
    swell = 0.6 + 0.25 * np.sin(2 * np.pi * 0.07 * t + 1.3) + 0.15 * np.sin(2 * np.pi * 0.13 * t)
    return w / (np.max(np.abs(w)) + 1e-9) * swell


def ambience_day(rng):
    sr = AMB_SR
    total = LOOP_SECONDS + 2.0
    out = 0.5 * wind(rng, total, sr, 520)
    for at in np.sort(rng.random(3)) * (total - 1):
        leaves = band(noise(0.7, rng, sr), 1800, 5500, sr) * env(0.7, 0.2, 0.18, sr, hold=0.1)
        place(out, leaves, at, sr, gain=0.12)
    for i in range(9):
        at = (i + rng.random() * 0.8) * total / 9
        far = rng.random() < 0.35
        phrase = chirp_phrase(rng, sr)
        if far:
            phrase = band(phrase, None, 3000, sr)
        place(out, phrase, at, sr, gain=0.09 if far else 0.2)
    return finish(loopable(out, LOOP_SECONDS, sr), -24, sr, edges=False)


def cricket(rng, total, sr, carrier, every, level):
    out = silence(total, sr)
    at = rng.random() * every
    while at < total:
        pulses = int(rng.integers(3, 5))
        for p in range(pulses):
            d = 0.012
            place(out, osc(carrier, d, sr) * env(d, 0.002, 0.004, sr), at + p * 0.022, sr, gain=level)
        at += every * (0.85 + 0.3 * rng.random())
    return out


def ambience_night(rng):
    sr = AMB_SR
    total = LOOP_SECONDS + 2.0
    out = 0.35 * wind(rng, total, sr, 380)
    out += cricket(rng, total, sr, 4150, 0.78, 0.16)
    out += cricket(rng, total, sr, 3700, 1.05, 0.09)
    hoo = silence(1.0, sr)
    for i, (f0, f1) in enumerate([(372, 352), (360, 330)]):
        d = 0.32
        place(hoo, osc(sweep(f0, f1, d, sr), d, sr) * env(d, 0.06, 0.1, sr, hold=0.08), 0.42 * i, sr)
    place(out, band(hoo, None, 900, sr), 9.0 + 2 * rng.random(), sr, gain=0.22)
    return finish(loopable(out, LOOP_SECONDS, sr), -25, sr, edges=False)


# The new places' loops (coherence plan B3): one for each region, as the plan asks.
# They hold nothing above 4 kHz, so they are stored at 8 kHz and run 15 s, which keeps
# all three to 0.7 MB (check:sound's size budget).
PLACE_SR = 8000
PLACE_SECONDS = 15.0


def norm(x: np.ndarray) -> np.ndarray:
    return x / (np.max(np.abs(x)) + 1e-9)


def gusts(total, sr, centres, width):
    """A gust envelope: soft bumps (Gaussian, `width` seconds) at the given times."""
    t = times(total, sr)
    out = np.zeros_like(t)
    for at in centres:
        out += np.exp(-(((t - at) / width) ** 2))
    return np.clip(out, 0, 1)


def caw(rng, sr, f0):
    """A raven's far 'kraa': a short falling call of a few soft harmonics with a quick
    flutter, low-passed hard so it stays distant rather than harsh."""
    d = 0.3
    f = sweep(f0 * 1.06, f0 * 0.84, d, sr, curve=0.8)
    flutter = (40 + 10 * rng.random(), 0.035)
    call = sum((0.62 ** k) * osc(f * k, d, sr, vibrato=flutter) for k in range(1, 5))
    return band(call * env(d, 0.025, 0.08, sr, hold=0.1), None, 1400, sr)


def ambience_frost(rng):
    """The Frostline: cold wind over the high ground, gusting twice with a dry hiss of
    blown snow and a faint whistle (G5) over the ridges; one raven calls far off."""
    sr = PLACE_SR
    total = PLACE_SECONDS + 2.0
    out = 0.55 * wind(rng, total, sr, 480)
    gust = gusts(total, sr, (3.0 + 2 * rng.random(), 10.0 + 2 * rng.random()), 1.6)
    out += 0.2 * norm(band(noise(total, rng, sr, 'pink'), 900, 3000, sr)) * (0.02 + 0.98 * gust ** 2)
    whistle = norm(band(noise(total, rng, sr), NOTE['G5'] - 18, NOTE['G5'] + 18, sr, order=2))
    out += 0.06 * whistle * (0.08 + 0.92 * gust)
    call = silence(1.4, sr)
    place(call, caw(rng, sr, 520), 0.0, sr)
    place(call, caw(rng, sr, 490), 0.55, sr)
    place(out, call, 6.5 + 2 * rng.random(), sr, gain=0.16)
    return finish(loopable(out, PLACE_SECONDS, sr), -25, sr, edges=False)


def ambience_sunstone(rng):
    """Sunstone Reach, from Dust Gulch to the caldera: a warm, dry wind with sand hissing
    along the ground in three gusts and the odd rattle of dry grass, over the lava's low
    rumble, which swells slowly (with a warmer band so a phone speaker carries it), and
    three slow bubbles popping far off (C3 sliding to G2)."""
    sr = PLACE_SR
    total = PLACE_SECONDS + 2.0
    t = times(total, sr)
    out = 0.45 * wind(rng, total, sr, 420)
    gust = gusts(total, sr, np.sort(rng.random(3)) * (total - 4) + 2, 2.0)
    out += 0.17 * norm(band(noise(total, rng, sr), 1500, 3400, sr)) * (0.02 + 0.98 * gust ** 2)
    for at in np.sort(rng.random(5)) * (total - 1):
        rattle = band(noise(0.25, rng, sr), 2000, 3700, sr) * env(0.25, 0.01, 0.05, sr)
        place(out, rattle, at, sr, gain=0.06)
    swell = 0.75 + 0.25 * np.sin(2 * np.pi * 0.06 * t)
    out += 0.38 * norm(band(noise(total, rng, sr, 'brown'), 40, 170, sr)) * swell
    out += 0.11 * norm(band(noise(total, rng, sr, 'brown'), 170, 380, sr)) * swell
    for i in range(3):
        d = 0.36
        pop = osc(sweep(130.81, 98.0, d, sr), d, sr) * env(d, 0.012, 0.08, sr)
        place(out, pop, (i + 0.15 + 0.6 * rng.random()) * total / 3, sr, gain=0.16)
    return finish(loopable(out, PLACE_SECONDS, sr), -25, sr, edges=False)


def ambience_isles(rng):
    """The Tidebloom Isles: the falls' steady rush under the canopy, waves arriving every
    five or six seconds (a slow swell that breaks, then draws back as a brighter hiss over
    the sand), birds near and far, a two-note whistle (G5, E5) answered across the water,
    and a dove's low coo (G4, E4)."""
    sr = PLACE_SR
    total = PLACE_SECONDS + 2.0
    t = times(total, sr)
    out = 0.07 * norm(band(noise(total, rng, sr, 'pink'), 200, 1500, sr)) * (0.9 + 0.1 * np.sin(2 * np.pi * 0.11 * t))
    at = 0.2
    while at < total:
        dur = 4.6 + 1.8 * rng.random()
        crash = norm(band(noise(dur, rng, sr, 'pink'), 180, 2400, sr))
        crash *= env(dur, 0.9 + 0.5 * rng.random(), 1.0, sr, hold=0.2) ** 1.5
        wash = norm(band(noise(dur, rng, sr), 1500, 3400, sr)) * env(dur, 1.9, 0.8, sr, hold=0.4) ** 2
        place(out, crash + 0.2 * wash, at, sr, gain=0.42 + 0.12 * rng.random())
        at += dur * (0.72 + 0.18 * rng.random())
    for i in range(8):
        far = rng.random() < 0.45
        phrase = chirp_phrase(rng, sr, low=1700, spread=900)
        if far:
            phrase = band(phrase, None, 2400, sr)
        place(out, phrase, (i + 0.8 * rng.random()) * total / 8, sr, gain=0.08 if far else 0.17)
    whistle = silence(0.9, sr)
    for k, (note, d) in enumerate([('G5', 0.22), ('E5', 0.34)]):
        place(whistle, osc(NOTE[note], d, sr, vibrato=(6, 0.012)) * env(d, 0.03, 0.12, sr, hold=0.05),
              0.3 * k, sr)
    place(out, whistle, 2.5 + rng.random(), sr, gain=0.14)
    place(out, band(whistle, None, 2000, sr), 4.6 + rng.random(), sr, gain=0.07)
    coo = silence(1.1, sr)
    for k, note in enumerate(('G4', 'E4', 'E4')):
        d = 0.28
        place(coo, osc(NOTE[note], d, sr) * env(d, 0.05, 0.1, sr, hold=0.06), 0.33 * k, sr)
    place(out, band(coo, None, 1200, sr), 9.5 + rng.random(), sr, gain=0.16)
    return finish(loopable(out, PLACE_SECONDS, sr), -24, sr, edges=False)


EFFECTS = {
    'tap': tap, 'chime': chime, 'oops': oops, 'hit': hit, 'raid': raid,
    'nap': nap, 'wake': wake, 'friend': friend, 'levelup': levelup, 'reward': reward,
    'steps': steps, 'splash': splash, 'page': page, 'water': water, 'rustle': rustle,
    'lantern': lantern, 'boop': boop, 'munch': munch,
}
# Each loop with its sample rate. New loops go at the end: the seed follows the order.
AMBIENCE = {
    'day': (ambience_day, AMB_SR), 'night': (ambience_night, AMB_SR),
    'frost': (ambience_frost, PLACE_SR), 'sunstone': (ambience_sunstone, PLACE_SR),
    'isles': (ambience_isles, PLACE_SR),
}
# Matt, 18 Oct: "reduce the sound effects a bit". Every effect sits 5 dB under its
# mastered peak (players stay at volume 1; the level lives in the files).
EFFECT_TRIM_DB = -5.0


def write_wav(path: str, x: np.ndarray, sr: int) -> None:
    pcm = np.clip(np.round(x * 32767), -32768, 32767).astype('<i2')
    with wave.open(path, 'wb') as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(sr)
        f.writeframes(pcm.tobytes())


def main() -> None:
    os.makedirs(OUT, exist_ok=True)
    durations: dict[str, float] = {}
    entries: list[tuple[str, str, str]] = []
    for seed, (name, make) in enumerate(EFFECTS.items()):
        x = make(np.random.default_rng(1000 + seed)) * (10 ** (EFFECT_TRIM_DB / 20))
        write_wav(os.path.join(OUT, f'{name}.wav'), x, SR)
        durations[name] = round(len(x) / SR, 3)
        entries.append((name, f'{name}.wav', 'effect'))
    for seed, (name, (make, sr)) in enumerate(AMBIENCE.items()):
        x = make(np.random.default_rng(2000 + seed))
        write_wav(os.path.join(OUT, f'ambience-{name}.wav'), x, sr)
        durations[f'ambience-{name}'] = round(len(x) / sr, 3)
        entries.append((f'ambience-{name}', f'ambience-{name}.wav', 'ambience'))

    lines = [
        '// Generated by scripts/audio/sounds.py (npm run sound). Do not edit by hand.',
    ]
    for name, file, _ in entries:
        ident = name.replace('-', '_')
        lines.append(f"import {ident} from '@/assets/sounds/{file}';")
    effect_names = [n for n, _, k in entries if k == 'effect']
    lines.append('')
    lines.append('export const soundEffects = {')
    for n in effect_names:
        lines.append(f'  {n},')
    lines.append('} as const;')
    lines.append('export type SoundId = keyof typeof soundEffects;')
    lines.append('')
    lines.append('export const ambienceLoops = {')
    for name in AMBIENCE:
        lines.append(f'  {name}: ambience_{name},')
    lines.append('} as const;')
    lines.append('export type AmbienceId = keyof typeof ambienceLoops;')
    lines.append('')
    lines.append('/** Seconds, measured from the generated files. */')
    lines.append(f'export const soundDurations: Record<string, number> = {json.dumps(durations)};')
    with open(TS, 'w') as f:
        f.write('\n'.join(lines) + '\n')
    print(f'wrote {len(entries)} sounds to {os.path.relpath(OUT, ROOT)}')


if __name__ == '__main__':
    main()
