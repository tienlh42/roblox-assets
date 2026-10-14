"""Synthesizes the police goose sound effects as 16-bit mono WAV files (standard library only).

Run: python build_sounds.py
Reuses the synth helpers of the treasure chest sounds. Timings match the animations in ../build_police_goose.py;
levels and pitch follow SOUND_GUIDE.md; looped animations get a file that fits one loop (Walk 0.5 s, Run 0.22 s, Fly 0.5 s, Attack 0.7 s, Sleep 3 s, Search 2.4 s).
"""

import math
import random
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE.parent.parent / "TreasureChest" / "Sounds"))
import build_sounds as synth  # noqa: E402

synth.HERE = HERE
RATE, TAU = synth.RATE, synth.TAU
silence, mix, sweep, noise, bell, save = synth.silence, synth.mix, synth.sweep, synth.noise, synth.bell, synth.save

random.seed(11)


def honk(f0, f1, seconds, volume, power=1.0):
    """Buzzy goose-like tone: a pitch glide with a few harmonics and a slight wobble."""
    n = int(RATE * seconds)
    out, phase = [], 0.0
    for i in range(n):
        f = f0 + (f1 - f0) * i / n + 8 * math.sin(TAU * 30 * i / RATE)
        phase += TAU * f / RATE
        wave = math.sin(phase) + 0.6 * math.sin(2 * phase) + 0.4 * math.sin(3 * phase) + 0.2 * math.sin(5 * phase)
        out.append(volume * synth.decay(i, n, power) * wave / 2.2)
    return out


def breath(seconds, volume, power=1.5):
    """Airy noise limited to roughly 250 Hz - 1.5 kHz, so it never rumbles or hisses."""
    n = int(RATE * seconds)
    out, stages, low = [], [0.0, 0.0, 0.0], 0.0
    for i in range(n):
        value = random.uniform(-1, 1)
        for k in range(3):
            stages[k] += 0.15 * (value - stages[k])
            value = stages[k]
        low += 0.035 * (value - low)
        out.append(volume * synth.decay(i, n, power) * (value - low))
    return out


def whistle(seconds, volume):
    """Pea whistle: a high tone with a fast trill that stays loud until the end."""
    n = int(RATE * seconds)
    out, phase = [], 0.0
    for i in range(n):
        f = 1900 + 100 * math.sin(TAU * 38 * i / RATE)
        phase += TAU * f / RATE
        env = min(i / (0.01 * RATE), 1) * (1 - i / n) ** 0.4
        out.append(volume * env * math.sin(phase))
    return out


def step():
    out = silence(0.12)
    mix(out, sweep(220, 90, 0.08, 0.8), 0.0)
    mix(out, noise(0.06, 0.5, 0.3), 0.0)
    return out


def run_step():
    out = silence(0.1)
    mix(out, sweep(260, 110, 0.06, 0.8), 0.0)
    mix(out, noise(0.05, 0.5, 0.35), 0.0)
    return out


def wing_flap():
    out = silence(0.5)
    mix(out, breath(0.22, 1.0, power=1.0), 0.0)
    mix(out, breath(0.12, 0.5), 0.22)
    return out


def idle():
    out = silence(0.5)
    mix(out, honk(330, 280, 0.12, 0.6), 0.0)
    mix(out, honk(310, 260, 0.1, 0.4), 0.17)
    return out


def attack():
    out = silence(0.7)
    mix(out, honk(420, 330, 0.18, 0.7), 0.22)
    mix(out, sweep(900, 300, 0.05, 0.9), 0.42)
    mix(out, noise(0.04, 0.6, 0.6), 0.42)
    return out


def sleep():
    out = silence(3.0)
    mix(out, noise(1.2, 0.35, 0.06, power=0.6), 0.2)
    mix(out, sweep(130, 105, 0.9, 0.5, vibrato=18, power=0.8), 1.5)
    mix(out, noise(0.9, 0.3, 0.05, power=1.5), 1.5)
    return out


def faint():
    out = silence(2.4)
    for i, start in enumerate((0.0, 0.25, 0.5)):
        mix(out, honk(380 - 40 * i, 300 - 40 * i, 0.22, 0.45), start)
    mix(out, sweep(500, 150, 0.4, 0.5, vibrato=40), 0.75)
    mix(out, sweep(170, 100, 0.3, 1.0), 1.15)
    mix(out, noise(0.25, 0.6, 0.08), 1.15)
    for start in (1.7, 2.0):
        mix(out, sweep(180, 90, 0.07, 0.4), start)
    return out


def alert():
    out = silence(0.9)
    mix(out, honk(280, 520, 0.28, 0.7, power=0.6), 0.2)
    mix(out, honk(500, 430, 0.15, 0.5), 0.5)
    return out


def whistle_blast():
    out = silence(1.0)
    mix(out, noise(0.08, 0.3, 0.7), 0.2)
    mix(out, whistle(0.3, 0.8), 0.3)
    mix(out, whistle(0.25, 0.8), 0.62)
    return out


def stunned():
    out = silence(1.0)
    mix(out, sweep(250, 110, 0.15, 1.0), 0.0)
    mix(out, noise(0.08, 0.6, 0.3), 0.0)
    mix(out, honk(450, 220, 0.4, 0.6, power=1.5), 0.1)
    for i, freq in enumerate((1318.5, 1568.0, 1318.5)):
        mix(out, bell(freq, 0.3, 0.25), 0.4 + 0.15 * i)
    return out


def search():
    out = silence(2.4)
    for start in (0.45, 0.65, 1.1, 1.3, 1.7, 1.9):
        mix(out, breath(0.12, 0.6), start)
    return out


def threaten():
    out = silence(2.4)
    mix(out, honk(150, 120, 0.4, 0.6, power=0.7), 0.0)
    for start in (0.5, 0.9):
        mix(out, sweep(700, 250, 0.06, 0.8), start)
        mix(out, noise(0.04, 0.5, 0.6), start)
    for i, freq in enumerate((1568.0, 1318.5, 1568.0, 1318.5)):
        mix(out, bell(freq, 0.25, 0.3), 1.1 + 0.2 * i)
    mix(out, honk(240, 200, 0.3, 0.5), 1.7)
    return out


SOUNDS = {
    "idle": idle, "walk": step, "run": run_step, "fly": wing_flap, "attack": attack, "sleep": sleep,
    "faint": faint, "alert": alert, "whistle": whistle_blast, "stunned": stunned, "search": search,
    "threaten": threaten,
}

if __name__ == "__main__":
    for name, build in SOUNDS.items():
        save(f"goose_{name}.wav", build())
