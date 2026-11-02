"""Office-funk chase track for the 칼퇴 박대리 reel -> out/music.wav
112 bpm slap bass, clav stabs, horn hits and a tight kit; a record scratch + sad trombone when the boss catches you."""
import json, os, wave
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
data = json.load(open(os.path.join(HERE, 'out', 'events.json'))); DUR, EV = data['duration'], data['events']
SR = 44100; N = int(SR * (DUR + .6))
at = lambda n, d=DUR: next((e[1] for e in EV if e[0] == n), d)
mtof = lambda n: 440.0 * 2 ** ((n - 69) / 12)
T_CAUGHT, T_END = at('caught'), at('endcard')
rng = np.random.default_rng(4); noise = rng.uniform(-1, 1, SR)
bus = {k: np.zeros(N) for k in ('drums', 'bass', 'keys', 'horn', 'sfx')}
def add(b, t, s, g=1.0):
    i = int(t * SR)
    if i >= N or i + len(s) <= 0: return
    a, e = max(0, i), min(N, i + len(s)); bus[b][a:e] += s[a - i:e - i] * g
def env(n, a=.003, d=.1, sus=0.):
    t = np.arange(n) / SR; e = np.minimum(1, t / a) * (sus + (1 - sus) * np.exp(-t / d)); r = min(n, int(.02 * SR)); e[-r:] *= np.linspace(1, 0, r); return e
def osc(kind, f, n, f2=None):
    t = np.arange(n) / SR; fr = np.full(n, f) if f2 is None else f * (f2 / f) ** (t / (n / SR)); ph = 2 * np.pi * np.cumsum(fr) / SR
    return {'sine': np.sin(ph), 'saw': (ph / np.pi) % 2 - 1, 'sq': np.sign(np.sin(ph)), 'tri': 2 / np.pi * np.arcsin(np.sin(ph))}[kind]
def lp(x, fc):
    a = np.exp(-2 * np.pi * fc / SR); y = np.zeros_like(x); acc = 0.
    for i in range(len(x)): acc = (1 - a) * x[i] + a * acc; y[i] = acc
    return y
HP = noise - lp(noise, 6000); MID = lp(noise, 3000) - lp(noise, 700)
def kick(t): n = int(.25 * SR); add('drums', t, osc('sine', 140, n, 45) * env(n, .001, .08), 1.0)
def snare(t, g=1): n = int(.18 * SR); add('drums', t, osc('tri', 220, n, 170) * env(n, .001, .04) * .5 + MID[:n] * env(n, .001, .06) * 1.6, .5 * g)
def hat(t, g=1, op=False): n = int((.15 if op else .04) * SR); add('drums', t, HP[:n] * env(n, .001, .05 if op else .012), .16 * g)
def slap(t, note, d=.18):
    n = int(d * SR); s = lp(osc('saw', mtof(note), n), 1600) * env(n, .002, .06, .35) * 1.5 + osc('sine', mtof(note), n) * env(n, .002, .12, .3)
    add('bass', t, s, .5)
def clav(t, notes, d=.1):
    n = int(d * SR)
    for k in notes: add('keys', t, lp(osc('sq', mtof(k), n), 2500) * env(n, .001, .04), .05)
def horn(t, notes, d=.22):
    n = int(d * SR)
    for k in notes:
        s = lp(osc('saw', mtof(k) * 1.003, n) + osc('saw', mtof(k) * .997, n), 2200) * env(n, .015, d * .5, .4)
        add('horn', t, s, .06)
BPM = 112; B = 60 / BPM; S16 = B / 4
BASS = [[40, None, 52, None, None, 40, None, 43, 40, None, 52, 50, None, 47, None, 45], [41, None, 53, None, None, 41, None, 45, 41, None, 53, 51, None, 48, None, 46]]
CH = [[64, 67, 71, 74], [65, 69, 72, 76]]
def groove(t0, t1, bar=0):
    t = t0
    while t < t1 - .02:
        pat = BASS[bar % 2]; ch = CH[bar % 2]
        for s in range(16):
            ts = t + s * S16 + (S16 * .1 if s % 2 else 0)
            if ts >= t1: break
            if s in (0, 10): kick(ts)
            if s == 7 and bar % 2: kick(ts)
            if s in (4, 12): snare(ts)
            if s in (3, 9) : snare(ts, .25)
            hat(ts, .8 if s % 2 == 0 else .45, op=(s == 14))
            if pat[s]: slap(ts, pat[s])
            if s in (2, 6, 11, 14): clav(ts, ch[1:])
        if bar % 4 == 3: [horn(t + B * k, [76, 79, 83]) for k in (2, 2.5, 3)]
        bar += 1; t += 4 * B
groove(0, T_CAUGHT)
groove(T_END, DUR + .5)
# caught: record scratch, then sad trombone
n = int(.35 * SR); add('sfx', T_CAUGHT, lp(osc('saw', 600, n, 120), 3000) * env(n, .005, .2, .3) * .8 + HP[:n] * env(n, .005, .15), .6)
for dt, nt, d in [(.45, 58, .42), (.93, 57, .42), (1.41, 56, .42), (1.89, 55, 1.2)]:
    n = int(d * SR); tt = np.arange(n) / SR; f = mtof(nt) * (1 + .012 * np.sin(2 * np.pi * 6 * tt) * (d > 1))
    add('horn', T_CAUGHT + dt, lp((2 * np.pi * np.cumsum(f) / SR / np.pi) % 2 - 1, 900) * env(n, .03, d * .9, .6), .5)
# sound effects
def blip(t, f, d, g, kind='sine', f2=None): n = int(d * SR); add('sfx', t, osc(kind, f, n, f2) * env(n, .002, d / 3), g)
for name, t in EV:
    if name == 'tap': blip(t, 900, .05, .08, 'tri')
    if name == 'gate': [blip(t + i * .05, f, .18, .12) for i, f in enumerate([1047, 1319, 1568])]
    if name == 'boost': blip(t, 300, .5, .14, 'saw', 1400); horn(t, [72, 76, 79, 84], .4)
    if name == 'smash': n = int(.15 * SR); add('sfx', t, MID[:n] * env(n, .001, .04) * 1.6 + osc('sine', 160, n, 60) * env(n, .001, .06), .5)
    if name == 'crash': n = int(.3 * SR); add('sfx', t, MID[:n] * env(n, .002, .08) + osc('sine', 120, n, 50) * env(n, .002, .1), .7); blip(t + .1, 500, .3, .08, 'tri', 250)
mix = bus['drums'] + bus['bass'] + bus['keys'] + bus['horn'] + bus['sfx'] * 1.1
mix = mix / (np.percentile(np.abs(mix), 99.5) + 1e-9) * .8; mix = np.tanh(mix * 1.3) / np.tanh(1.3) * .92
f = int(.5 * SR); mix[-f:] *= np.linspace(1, 0, f)
d = int(.012 * SR); L = mix + np.concatenate([np.zeros(d), bus['horn'][:-d]]) * .1; R = mix + np.concatenate([np.zeros(d), bus['keys'][:-d]]) * .1
st = np.clip(np.stack([L, R], 1), -1, 1)
with wave.open(os.path.join(HERE, 'out', 'music.wav'), 'wb') as w:
    w.setnchannels(2); w.setsampwidth(2); w.setframerate(SR); w.writeframes((st * 32767).astype(np.int16).tobytes())
print('music.wav', round(N / SR, 2))
