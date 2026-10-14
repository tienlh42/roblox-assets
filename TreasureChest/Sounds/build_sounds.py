"""Synthesizes the treasure chest sound effects as 16-bit mono WAV files (standard library only).

Run: python build_sounds.py
Timings match the animations in ../build_treasure_chest.py (lid pops at 0.42 s of Open, slams shut at 0.25 s of Vanish).
Levels and pitch follow SOUND_GUIDE.md: peak 0.5, a 20 ms fade-out, nothing below ~100 Hz, bells kept under ~3 kHz.
"""

import math
import random
import struct
import wave
from pathlib import Path

HERE = Path(__file__).parent
RATE = 44100
TAU = 2 * math.pi
PEAK = 0.5
FADE_OUT = 0.02

random.seed(7)


def silence(seconds):
    return [0.0] * int(RATE * seconds)


def mix(buffer, samples, start):
    offset = int(RATE * start)
    for i, v in enumerate(samples):
        if offset + i < len(buffer):
            buffer[offset + i] += v


def decay(i, n, power=3.0):
    return (1 - i / n) ** power


def sweep(f0, f1, seconds, volume, vibrato=0.0, power=2.0):
    """Sine whose pitch glides from f0 to f1. vibrato is the pitch wobble depth in Hz."""
    n = int(RATE * seconds)
    out, phase = [], 0.0
    for i in range(n):
        f = f0 + (f1 - f0) * i / n + vibrato * math.sin(TAU * 12 * i / RATE)
        phase += TAU * f / RATE
        out.append(volume * decay(i, n, power) * math.sin(phase))
    return out


def noise(seconds, volume, cutoff=0.2, power=2.0):
    """White noise through a one-pole low-pass; a lower cutoff (0..1) sounds duller."""
    n = int(RATE * seconds)
    out, state = [], 0.0
    for i in range(n):
        state += cutoff * (random.uniform(-1, 1) - state)
        out.append(volume * decay(i, n, power) * state)
    return out


def bell(freq, seconds, volume):
    n = int(RATE * seconds)
    return [volume * decay(i, n, 4) * (math.sin(TAU * freq * i / RATE) + 0.4 * math.sin(TAU * freq * 2 * i / RATE)
                                       + 0.15 * math.sin(TAU * freq * 3.01 * i / RATE)) / 1.55 for i in range(n)]


def save(name, samples):
    peak = max(abs(v) for v in samples) or 1
    gain = PEAK / peak
    fade = int(RATE * FADE_OUT)
    for i in range(1, min(fade, len(samples)) + 1):
        samples[-i] *= i / fade
    with wave.open(str(HERE / name), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(RATE)
        f.writeframes(b"".join(struct.pack("<h", int(v * gain * 32767)) for v in samples))
    print(f"Wrote {name} ({len(samples) / RATE:.2f} s)")


def spawn():
    out = silence(1.0)
    mix(out, noise(0.4, 0.5, 0.15), 0.0)
    mix(out, sweep(220, 640, 0.25, 0.8), 0.05)
    mix(out, sweep(300, 120, 0.18, 0.7), 0.62)
    mix(out, noise(0.2, 0.4, 0.1), 0.62)
    return out


def idle():
    out = silence(0.55)
    for i, start in enumerate((0.1, 0.2, 0.3, 0.4)):
        mix(out, sweep(520 if i % 2 else 430, 380, 0.05, 0.6), start)
        mix(out, noise(0.03, 0.4, 0.6), start)
    return out


def open_chest():
    out = silence(1.0)
    mix(out, sweep(180, 420, 0.28, 0.35, vibrato=25, power=0.5), 0.15)
    mix(out, sweep(700, 200, 0.09, 0.9), 0.42)
    mix(out, noise(0.12, 0.45, 0.5), 0.42)
    mix(out, sweep(320, 320, 0.4, 0.5, vibrato=70, power=2), 0.52)
    return out


# Pentatonic notes (C5 D5 E5 G5 A5 C6); a higher rarity plays more of them and rings longer.
NOTES = [523.25, 587.33, 659.25, 783.99, 880.0, 1046.5]
CHIME_NOTES = {"Common": 1, "Rare": 2, "Epic": 3, "Legendary": 4, "Mythic": 6}


def chime(count):
    out = silence(0.4 + 0.1 * count + 0.8)
    for i in range(count):
        mix(out, bell(NOTES[i], 0.9, 0.7), 0.1 * i)
    if count >= 4:
        mix(out, bell(NOTES[-1] * 2, 1.1, 0.35), 0.1 * count)
    return out


def vanish():
    out = silence(1.3)
    mix(out, sweep(200, 100, 0.15, 0.9), 0.25)
    mix(out, noise(0.12, 0.5, 0.2), 0.25)
    mix(out, sweep(220, 110, 0.1, 0.5), 0.4)
    for i, freq in enumerate((1318.5, 1046.5, 784.0)):
        mix(out, bell(freq, 0.5, 0.45), 0.55 + 0.1 * i)
    mix(out, sweep(500, 140, 0.25, 0.7), 0.95)
    mix(out, noise(0.3, 0.3, 0.12), 0.95)
    return out


if __name__ == "__main__":
    save("chest_spawn.wav", spawn())
    save("chest_idle.wav", idle())
    save("chest_open.wav", open_chest())
    save("chest_vanish.wav", vanish())
    for rarity, count in CHIME_NOTES.items():
        save(f"chest_chime_{rarity.lower()}.wav", chime(count))
