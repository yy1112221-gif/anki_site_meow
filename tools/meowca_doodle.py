#!/usr/bin/env python3
"""묘카냥이 조잡한 펜 낙서(손그림) 제작 키트.

원본 냥이(3D 정면 실루엣·얼굴 배치)를 그대로 쓰고, 선만 손으로 대충 그은 느낌으로 다시 그린다.
표정·자세·구도·펜선 떨림(라인 보일)·그림체 섞기 지직 효과를 조합해 PNG/GIF/MP4로 뽑는다.
필요한 것: Python 3, numpy, Pillow (MP4는 ffmpeg).  사용법은 README.md.
"""
import json, math, os, random, subprocess, sys, tempfile, argparse
import numpy as np
from PIL import Image, ImageDraw, ImageChops, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
BASE = json.load(open(next(f for f in (os.path.join(HERE, 'cat_base.json'), os.path.join(HERE, 'meowca_doodle_base.json')) if os.path.exists(f))))   # 키트 폴더 / 저장소 tools/ 둘 다
DW, DH = BASE['W'], BASE['H']            # 디자인 좌표계(정면 냥이 1924×1166)
CX, BY = DW / 2, DH                       # 자세 변형 기준점 = 바닥 가운데

INK = (28, 24, 22, 255); PINK = (246, 150, 178, 255); PINK_A = (230, 110, 140, 255)
FUR = (255, 253, 246, 255); TEAR = (120, 180, 240, 255); PAPER = (236, 230, 220)

# ── 그림체 ─────────────────────────────────────────────
STYLES = {
    'A': dict(name='볼펜 낙서',   w=7,  amp=10, lump=16, off=(0, 0),    ear='line',  double=False),
    'B': dict(name='매직+어긋난 색', w=17, amp=14, lump=26, off=(-26, 16), ear='fill',  double=False),
    'C': dict(name='두 번 긋기',  w=8,  amp=11, lump=18, off=(0, 0),    ear='hatch', double=True),
}

# ── 표정 = 눈 + 입 + 덧붙임 ───────────────────────────────
EXPR = {
    'base':     dict(eyes='dot',    mouth='omega'),
    'meh':      dict(eyes='tiny',   mouth='omega'),                       # 멍
    'mad':      dict(eyes='ring',   mouth='omega', extra=['brows', 'vein']),   # 빡침
    'cry':      dict(eyes='cry',    mouth='omega', extra=['tears', 'wobble']),  # 울음
    'happy':    dict(eyes='happy',  mouth='omega'),                       # 웃음 ∩∩
    'shock':    dict(eyes='ring',   mouth='open',  extra=['exclaim', 'sweat']),  # 충격
    'sleepy':   dict(eyes='line',   mouth='omega', extra=['zzz']),          # 졸림
    'smug':     dict(eyes='half',   mouth='omega', extra=['sparkle']),      # 의기양양
    'love':     dict(eyes='heart',  mouth='omega'),                       # 반함
    'dead':     dict(eyes='x',      mouth='flat',  extra=['soul']),         # 영혼 이탈
    'confused': dict(eyes='spiral', mouth='wavy',  extra=['question']),     # 혼란
    'hungry':   dict(eyes='big',    mouth='tongue', extra=['drool']),       # 배고픔
    'blank':    dict(eyes='dot',    mouth='flat'),                        # 정색
}

# ── 기본 도형 ─────────────────────────────────────────────
def resample(P, step, closed=False):
    P = np.asarray(P, float)
    if closed: P = np.vstack([P, P[:1]])
    d = np.r_[0, np.cumsum(np.hypot(*np.diff(P, axis=0).T))]
    n = max(2, int(d[-1] / step)); t = np.linspace(0, d[-1], n, endpoint=not closed)
    return np.c_[np.interp(t, d, P[:, 0]), np.interp(t, d, P[:, 1])]

def smooth(P, k=7, closed=True):
    if len(P) < k: return P
    pad = k // 2
    Q = np.vstack([P[-pad:], P, P[:pad]]) if closed else np.vstack([np.repeat(P[:1], pad, 0), P, np.repeat(P[-1:], pad, 0)])
    ker = np.ones(k) / k
    return np.c_[np.convolve(Q[:, 0], ker, 'valid'), np.convolve(Q[:, 1], ker, 'valid')]

def arc(c, rx, ry, a0, a1, n=30):   # y가 아래로 + → 0→π는 아래쪽 반원
    return [(c[0] + rx * math.cos(a), c[1] + ry * math.sin(a)) for a in np.linspace(a0, a1, n)]

# ── 자세: 디자인 좌표 → 변형 좌표 (여러 개를 + 로 이어 씀) ──────────
def parse_pose(spec):
    ops = []
    for part in (spec or 'sit').split('+'):
        k, _, v = part.strip().partition(':'); ops.append((k, float(v) if v else 1.0))
    return ops

def pose_fn(spec):
    ops = parse_pose(spec)
    def f(x, y):
        for k, v in ops:
            if k == 'squash':  x, y = CX + (x - CX) * (1 + .35 * v), BY - (BY - y) * (1 - .3 * v)       # 납작
            elif k == 'stretch': x, y = CX + (x - CX) * (1 - .22 * v), BY - (BY - y) * (1 + .35 * v)     # 길쭉
            elif k == 'melt':    # 녹아내림: 아래가 퍼지고 위가 내려앉음
                t = (y / BY) ** 2; x, y = CX + (x - CX) * (1 + .7 * v * t), BY - (BY - y) * (1 - .45 * v)
            elif k == 'tilt':    # 기울기(도), 바닥 가운데 기준
                a = math.radians(v); dx, dy = x - CX, y - BY; x, y = CX + dx * math.cos(a) - dy * math.sin(a), BY + dx * math.sin(a) + dy * math.cos(a)
            elif k == 'lean':    # 윗몸만 옆으로 쏠림(도)
                x = x + (BY - y) * math.tan(math.radians(v)) * ((BY - y) / BY)
            elif k == 'jump':    y = y - 260 * v                                                       # 붕 뜸
            elif k == 'flip':    x = 2 * CX - x                                                        # 좌우 반전
            elif k == 'puff':    # 빵빵(가운데가 부풂)
                r = math.hypot(x - CX, y - BY * .62) / 900; s = 1 + .25 * v * max(0, 1 - r); x, y = CX + (x - CX) * s, BY * .62 + (y - BY * .62) * s
        return x, y
    return f

# ── 펜 ──────────────────────────────────────────────────
class Pen:
    def __init__(s, scale, seed, design_seed, pose='sit', warp=0.0, boil_shift=(0, 0, 0), margin=420):
        s.S = scale; s.m = margin
        s.img = Image.new('RGBA', (int((DW + 2 * margin) * scale), int((DH + 2 * margin) * scale)), (0, 0, 0, 0))
        s.d = ImageDraw.Draw(s.img); s.r = random.Random(seed); s.q = random.Random(design_seed)
        rr = random.Random(design_seed * 13)
        s.warp = (rr.uniform(25, 45) * warp, rr.uniform(20, 40) * warp, rr.uniform(260, 380), rr.uniform(0, 6.28), rr.uniform(0, 6.28))
        s.pose = pose_fn(pose); s.bs = boil_shift
    def T(s, p):
        x, y = s.pose(*p)
        A, B, L, p1, p2 = s.warp
        x, y = x + A * math.sin(y / L + p1) + B * math.sin(x / L * .7 + p2) * .4, y + B * math.sin(x / L + p2) + A * math.sin(y / L * .8 + p1) * .3
        bx, by, ba = s.bs   # 프레임마다 살짝 흔들림(라인 보일)
        x, y = x + bx + ba * math.sin(y / 300), y + by + ba * math.sin(x / 340)
        return ((x + s.m) * s.S, (y + s.m) * s.S)
    def wob(s, P, amp, freq=1.0, closed=False):
        P = np.asarray(P, float); n = len(P)
        if n < 3 or amp <= 0: return P
        tang = np.gradient(P, axis=0); nrm = np.c_[-tang[:, 1], tang[:, 0]]; nrm /= np.maximum(1e-6, np.hypot(*nrm.T))[:, None]
        L = float(np.sum(np.hypot(*np.diff(P, axis=0).T))); t = np.linspace(0, 1, n); off = np.zeros(n); base = max(.35, L / 420) * freq
        for k in range(3):
            f = base * (k + 1) * s.r.uniform(.7, 1.4); off += amp * min(1, L / 120) / (k + 1) ** 1.3 * np.sin(2 * math.pi * f * t + s.r.uniform(0, 6.28))
        off += np.cumsum([s.r.gauss(0, amp * .08) for _ in range(n)]) * .3
        if closed: off -= np.linspace(0, 1, n) * (off[-1] - off[0])
        return P + nrm * off[:, None]
    def stroke(s, P, w=6, col=INK, amp=4, closed=False, over=0, taper=True):
        P = resample(P, 3) if len(P) > 1 else np.asarray(P, float)
        P = s.wob(P, amp, 1, closed)
        if over and len(P) > 4:   # 선 끝이 삐져나감
            e = P[-1] - P[-4]; e /= max(1e-6, np.hypot(*e)); P = np.vstack([P, [P[-1] + e * over * k / 4 for k in range(1, 5)]])
        n = len(P); wv = s.r.uniform(.7, 1.2)
        for i, p in enumerate(P):
            u = i / max(1, n - 1); tw = (min(1, u * 6, (1 - u) * 6) ** .6) if taper else 1
            ww = w * (.75 + .5 * math.sin(u * math.pi * s.r.uniform(1, 3) + wv) ** 2) * max(.35, tw) * s.S / 2
            x, y = s.T(p); s.d.ellipse([x - ww, y - ww, x + ww, y + ww], fill=col)
    def fill(s, P, col, dx=0, dy=0, amp=3):
        P = s.wob(resample(P, 4, True), amp, 1, True); s.d.polygon([s.T((x + dx, y + dy)) for x, y in P], fill=col)
    def dot(s, c, r, col=INK, amp=.18):
        k = 24; P = [(c[0] + r * (1 + s.r.uniform(-amp, amp)) * math.cos(2 * math.pi * i / k), c[1] + r * (1 + s.r.uniform(-amp, amp)) * math.sin(2 * math.pi * i / k)) for i in range(k)]
        s.d.polygon([s.T(p) for p in smooth(np.array(P), 3)], fill=col)

def body_outline(lump, seed):
    r = random.Random(seed); P = np.array(BASE['outline'], float)
    cx, cy = P.mean(0); ang = np.arctan2(P[:, 1] - cy, P[:, 0] - cx)
    rad = sum(lump / (k + 1) * np.sin((k + 2) * ang + r.uniform(0, 6.28)) for k in range(3))
    v = P - [cx, cy]; v /= np.hypot(*v.T)[:, None]; return P + v * rad[:, None]

# ── 얼굴 ─────────────────────────────────────────────────
def draw_eyes(p, kind, w, amp, colored):
    q = p.q; (lx, ly), (rx, ry) = BASE['eyes']; R = BASE['eye_r']
    L = (lx + q.uniform(-15, 10), ly + q.uniform(-12, 12)); Rr = (rx + q.uniform(-10, 20), ry + q.uniform(-14, 14))
    sL, sR = q.uniform(.95, 1.25), q.uniform(.7, 1.0)
    jit = lambda c: (c[0] + p.r.uniform(-3, 3), c[1] + p.r.uniform(-3, 3))
    for c, sc, sg in ((L, sL, 1), (Rr, sR, -1)):
        c = jit(c)
        if kind == 'dot':    p.dot(c, R * sc)
        elif kind == 'tiny': p.dot((c[0] - sg * 30, c[1] + sg * 7), 15 * sc)
        elif kind == 'big':
            p.dot(c, R * 1.5 * sc); p.dot((c[0] - 18, c[1] - 20), R * .45, (255, 255, 255, 255)); p.dot((c[0] + 14, c[1] + 16), R * .2, (255, 255, 255, 255))
        elif kind == 'ring':
            p.stroke(arc(c, 62, 58, 0, 2 * math.pi, 40), w * .8, INK, amp * .6, closed=True, taper=False); p.dot((c[0] + sg * 14, c[1] + 8), 15)
        elif kind == 'happy': p.stroke(arc((c[0], c[1] + 22), 52, 48, math.pi * 1.05, math.pi * 1.95, 20), w * 1.1, INK, amp * .5)
        elif kind == 'line':  p.stroke([(c[0] - 55, c[1] + 4), (c[0] + 55, c[1] + 2)], w * 1.1, INK, amp * .5, over=8)
        elif kind == 'half':
            p.stroke([(c[0] - 62, c[1] - 4), (c[0] + 62, c[1] - 10)], w * 1.2, INK, amp * .4, over=10)
            p.d.pieslice([*p.T((c[0] - 40 + sg * -8, c[1] - 40)), *p.T((c[0] + 40 + sg * -8, c[1] + 40))], 0, 180, fill=INK)
        elif kind == 'x':
            p.stroke([(c[0] - 45, c[1] - 42), (c[0] + 45, c[1] + 42)], w * 1.1, INK, amp * .4); p.stroke([(c[0] + 45, c[1] - 42), (c[0] - 45, c[1] + 42)], w * 1.1, INK, amp * .4)
        elif kind == 'heart':
            hp = [(c[0] + 58 * 16 * math.sin(t) ** 3 / 16, c[1] - 58 * (13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t)) / 16) for t in np.linspace(0, 2 * math.pi, 40)]
            p.fill(hp, (238, 70, 110, 255), -8 if colored else 0, 6 if colored else 0, 3); p.stroke(hp, w * .7, INK, amp * .4, closed=True)
        elif kind == 'spiral':
            sp = [(c[0] + 6 * t * math.cos(t * 1.0), c[1] + 6 * t * math.sin(t * 1.0)) for t in np.linspace(0, 11, 60)]
            p.stroke(sp, w * .7, INK, amp * .3)
        elif kind == 'cry':
            p.stroke([(c[0] - 55, c[1] - 10), (c[0] + 55, c[1] - 14)], w * 1.2, INK, amp * .5, over=10)
            p.stroke([(c[0] - 22, c[1] - 8), (c[0] - 25, c[1] + 55)], w, INK, amp * .3); p.stroke([(c[0] + 22, c[1] - 10), (c[0] + 24, c[1] + 55)], w, INK, amp * .3)
    return L, Rr

def draw_mouth(p, kind, w, amp):
    q = p.q; mx, my, mw, mh = BASE['mouth']; mx += q.uniform(-12, 12); mw *= q.uniform(.9, 1.1); mh *= q.uniform(.85, 1.2)
    U = lambda cx: arc((cx, my), mw / 4, mh, math.pi, 0, 20)[::-1]
    if kind in ('omega', 'tongue'):
        if kind == 'tongue':
            tg = arc((mx + 20, my + mh * .6), 46, 70, 0, math.pi, 20) + [(mx - 26, my + mh * .5), (mx + 66, my + mh * .5)]
            p.fill(tg, (240, 110, 130, 255), -6, 6, 3); p.stroke(arc((mx + 20, my + mh * .6), 46, 70, 0, math.pi, 20), w * .8, INK, amp * .4)
        p.stroke(U(mx - mw / 4), w * 1.05, INK, amp * .7, over=6); p.stroke(U(mx + mw / 4), w * 1.05, INK, amp * .7, over=6)
    elif kind == 'open':
        o = arc((mx, my + 40), 70, 85, 0, 2 * math.pi, 36); p.fill(o, (70, 30, 35, 255), 0, 0, 4); p.stroke(o, w, INK, amp * .5, closed=True)
    elif kind == 'flat':  p.stroke([(mx - 90, my + 30), (mx + 90, my + 26)], w * 1.1, INK, amp * .6, over=10)
    elif kind == 'wavy':  p.stroke([(mx - 110 + k * 22, my + 30 + (14 if k % 2 else -14)) for k in range(11)], w * .9, INK, amp * .3)
    elif kind == 'smile': p.stroke(arc((mx, my), 110, 70, .15, math.pi - .15, 24), w * 1.1, INK, amp * .5, over=6)
    elif kind == 'frown': p.stroke(arc((mx, my + 90), 100, 60, math.pi + .2, 2 * math.pi - .2, 24), w * 1.1, INK, amp * .5, over=6)

def draw_extras(p, extras, w, amp, eyes):
    (L, R) = eyes
    for e in extras:
        if e == 'brows':
            for c, sg in ((L, 1), (R, -1)): p.stroke([(c[0] - sg * 80, c[1] - 110), (c[0] + sg * 55, c[1] - 62)], w * 1.6, INK, amp * .5, over=18)
        elif e == 'vein':   p.stroke([(1210, 420), (1240, 455), (1280, 430)], w * .8, INK, amp * .4); p.stroke([(1235, 405), (1250, 470)], w * .8, INK, amp * .4)
        elif e == 'tears':
            for c in (L, R):
                for k in (-1, 1): p.stroke([(c[0] + k * 24, c[1] + 60), (c[0] + k * 30, c[1] + 190)], w * .8, TEAR, amp * .8)
        elif e == 'wobble': p.stroke(arc((960, 700), 40, 25, 0.2, math.pi - .2, 14), w * .8, INK, amp * .4)
        elif e == 'sweat':
            sw = arc((1330, 380), 26, 36, 0, math.pi, 12) + [(1330, 300)]; p.fill(sw, TEAR, 0, 0, 2); p.stroke(sw, w * .5, INK, amp * .3, closed=True)
        elif e == 'exclaim': p.stroke([(1560, 80), (1530, 260)], w * 1.6, INK, amp * .4); p.dot((1522, 330), 18)
        elif e == 'question':
            p.stroke(arc((1560, 150), 60, 60, math.pi * 1.1, math.pi * 2.4, 20) + [(1555, 260)], w * 1.2, INK, amp * .4); p.dot((1552, 320), 16)
        elif e == 'zzz':
            for k, (x, y, s) in enumerate([(1450, 280, 60), (1560, 180, 80), (1690, 60, 100)]):
                p.stroke([(x, y), (x + s, y), (x, y + s), (x + s, y + s)], w * .9, INK, amp * .3)
        elif e == 'sparkle':
            for (x, y, s) in [(1580, 250, 50), (1690, 360, 32)]:
                p.stroke([(x - s, y), (x + s, y)], w * .7, INK, amp * .2); p.stroke([(x, y - s), (x, y + s)], w * .7, INK, amp * .2)
        elif e == 'soul':
            sl = arc((960, 300), 90, 110, 0, 2 * math.pi, 30)[:24] + [(1100, 120), (1060, 190)]
            p.fill(sl, (230, 240, 255, 200), 0, 0, 6); p.stroke(sl, w * .6, INK, amp * .6)
            p.dot((925, 300), 9); p.dot((995, 300), 9)
        elif e == 'drool': p.stroke([(1040, 720), (1046, 840)], w * .8, TEAR, amp * .4); p.dot((1047, 860), 14, TEAR)

# ── 냥이 한 장 ─────────────────────────────────────────────
def draw_cat(style='B', expr='base', pose='sit', seed=1, frame=0, boil=1.6, scale=.5, fur=None, warp=1.0):
    st = STYLES[style]; ex = EXPR[expr] if isinstance(expr, str) else expr
    br = random.Random(seed * 7919 + frame)
    bshift = (br.uniform(-1, 1) * 3 * boil, br.uniform(-1, 1) * 3 * boil, br.uniform(0, 4) * boil) if frame else (0, 0, 0)
    p = Pen(scale, seed * 1000 + frame, seed * 29, pose, warp * (.7 if style == 'A' else 1), bshift)
    w = st['w']; amp = st['amp'] * (1 if frame == 0 and boil == 0 else .55 * max(.2, boil))
    body = body_outline(st['lump'], seed)
    furc = fur or FUR
    if style == 'B':
        p.fill(body, furc, *st['off'], amp)
        for tri in BASE['ears']: p.fill(tri, PINK, -20, 14, 8)
    else:
        p.fill(body, furc, 0, 0, amp * .4)
        if st['ear'] == 'hatch':
            for tri in BASE['ears']:
                a, b, c = tri
                for k in range(6):
                    u = k / 6; p.stroke([(b[0] + (a[0] - b[0]) * u, b[1] + (a[1] - b[1]) * u), (b[0] + (c[0] - b[0]) * u, b[1] + (c[1] - b[1]) * u)], 3, PINK, 2, taper=False)
    p.stroke(body, w, INK, amp, closed=True, over=26)
    if st['double']: p.stroke(body_outline(st['lump'], seed + 7), w * .6, INK, amp * 1.3, closed=True, over=40)
    if style != 'B':
        for tri in BASE['ears']: p.stroke(tri, w * .6, INK, amp * .5, over=10)
    colored = style != 'A'
    eyes = draw_eyes(p, ex['eyes'], w, amp, colored)
    p.dot(tuple(BASE['nose']), 18, PINK if colored else INK, amp=.35)
    draw_mouth(p, ex['mouth'], w, amp)
    if ex.get('blush', True):
        y0, y1 = BASE['blush_y']
        for xs in BASE['blush_x']:
            for sg, xx in ((1, xs), (-1, DW - xs)): p.stroke([(xx + 12 * sg, y0), (xx - 14 * sg, y1)], w * .85, PINK if colored else PINK_A, amp * .5)
    for (x0, y0, x1, y1) in BASE['whiskers']:
        p.stroke([(x0, y0), (x1, y1)], w * .55, INK, amp * .9, over=14); p.stroke([(DW - x0, y0), (DW - x1, y1)], w * .55, INK, amp * .9, over=14)
    (rx, ry) = BASE['paw_r']
    for c in BASE['paws']: p.stroke(arc(tuple(c), rx, ry, math.pi * 1.05, math.pi * 1.95, 24), w * .9, INK, amp * .6, over=8)
    draw_extras(p, ex.get('extra', []), w, amp, eyes)
    if 'jump' in (pose or ''):   # 뜬 만큼 바닥 그림자
        g = p.T((CX, BY)); gx = g[0]; gy = (BY + p.m) * p.S
        p.d.ellipse([gx - 300 * p.S, gy - 20 * p.S, gx + 300 * p.S, gy + 20 * p.S], fill=(0, 0, 0, 40))
    return p.img

# ── 구도·출력 ───────────────────────────────────────────────
def compose(W, H, items, bg=PAPER):
    """items: [(draw_cat 이미지, 가운데x(0~1), 바닥y(0~1), 폭비율)] — 폭비율은 '기본 자세 냥이 폭' 기준이라
    납작·길쭉·점프 같은 자세도 같은 크기로 보임(바닥 가운데가 그 자리에 옴)."""
    can = Image.new('RGBA', (W, H), (*bg, 255) if bg else (0, 0, 0, 0))
    for im, fx, fy, fw in items:
        S = im.width / (DW + 840)                 # draw_cat 의 scale (margin 420*2 포함 폭)
        k = W * fw / (DW * S); nw, nh = int(im.width * k), int(im.height * k)
        im2 = im.resize((nw, nh), Image.LANCZOS)
        gx, gy = (CX + 420) * S * k, (BY + 420) * S * k   # 바닥 가운데
        can.alpha_composite(im2, (int(W * fx - gx), int(H * fy - gy)))
    return can

def glitch(im, strength, rng, bg=PAPER):
    im = im.convert('RGB'); w, h = im.size
    for _ in range(int(6 * strength)):
        y = rng.randint(0, h - 20); hh = rng.randint(4, int(h * .05) + 5); dx = rng.randint(-int(w * .07), int(w * .07))
        band = im.crop((0, y, w, y + hh)); im.paste(bg, (0, y, w, y + hh)); im.paste(band, (dx, y))
    r, g, b = im.split(); r = ImageChops.offset(r, rng.randint(3, 10), 0); b = ImageChops.offset(b, -rng.randint(3, 10), 0); im = Image.merge('RGB', (r, g, b))
    d = ImageDraw.Draw(im)
    for _ in range(int(w * h / 400 * strength)):
        d.point((rng.randint(0, w - 1), rng.randint(0, h - 1)), fill=rng.choice([(40, 35, 30), (255, 255, 255), (200, 190, 180)]))
    return im

def save_anim(frames, out, fps):
    os.makedirs(os.path.dirname(os.path.abspath(out)) or '.', exist_ok=True)
    if out.endswith('.gif'):
        fr = [f.convert('RGB') for f in frames]; fr[0].save(out, save_all=True, append_images=fr[1:], duration=int(1000 / fps), loop=0)
    elif out.endswith('.mp4'):
        with tempfile.TemporaryDirectory() as td:
            for i, f in enumerate(frames): f.convert('RGB').save(f'{td}/{i:04d}.png')
            subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-framerate', str(fps), '-i', f'{td}/%04d.png', '-vf', 'scale=trunc(iw/2)*2:trunc(ih/2)*2,format=yuv420p',
                            '-c:v', 'libx264', '-preset', 'veryfast', '-r', '30', out], check=True)
    else:   # 폴더 → 투명 PNG 연속
        os.makedirs(out, exist_ok=True)
        for i, f in enumerate(frames): f.save(f'{out}/{i:03d}.png')

def parse_size(s):
    w, h = s.lower().split('x'); return int(w), int(h)

def shot_frames(spec, n, boil, W, H, bg, fx=.5, fy=.82, fw=.8, frame0=0):
    """spec: dict(style, expr, pose, seed, fur) → n 프레임(라인 보일)"""
    out = []
    for k in range(n):
        im = draw_cat(spec.get('style', 'B'), spec.get('expr', 'base'), spec.get('pose', 'sit'), spec.get('seed', 1), frame0 + k + 1, boil)
        out.append(compose(W, H, [(im, spec.get('x', fx), spec.get('y', fy), spec.get('w', fw))], bg) if W else im)
    return out

def parse_shots(s):
    """"B:mad:squash:.5:2, C:cry:melt:.6:1.5"  →  스타일:표정:자세:시간(초)  (자세 값 포함 가능)"""
    shots = []
    for part in s.split(','):
        f = [x.strip() for x in part.strip().split(':')]
        st, ex = f[0], f[1]; dur = float(f[-1]) if len(f) >= 4 else 1.5
        pose = ':'.join(f[2:-1]) if len(f) >= 4 else (f[2] if len(f) == 3 else 'sit')
        shots.append(dict(style=st, expr=ex, pose=pose or 'sit', dur=dur))
    return shots

def main():
    ap = argparse.ArgumentParser(description='묘카냥이 펜 낙서 제작 키트')
    sub = ap.add_subparsers(dest='cmd', required=True)
    def common(a):
        a.add_argument('--style', default='B', choices=list(STYLES)); a.add_argument('--expr', default='base', choices=list(EXPR))
        a.add_argument('--pose', default='sit'); a.add_argument('--seed', type=int, default=2)
        a.add_argument('--size', default='1080x1080', help='캔버스 크기, 0이면 냥이만 투명 배경'); a.add_argument('--bg', default='paper', help='paper | none | #rrggbb')
        a.add_argument('--x', type=float, default=.5); a.add_argument('--y', type=float, default=.82); a.add_argument('--w', type=float, default=.8, help='냥이 폭(캔버스 대비)')
        a.add_argument('--out', required=True)
    a = sub.add_parser('still', help='한 장'); common(a)
    a = sub.add_parser('boil', help='펜선 떨림 반복 애니'); common(a)
    a.add_argument('--frames', type=int, default=8); a.add_argument('--fps', type=float, default=4); a.add_argument('--boil', type=float, default=1.6)
    a = sub.add_parser('seq', help='여러 컷을 이어 붙이고 바뀔 때 지직')
    a.add_argument('--shots', required=True); a.add_argument('--fps', type=float, default=4); a.add_argument('--boil', type=float, default=1.6)
    a.add_argument('--glitch', type=float, default=1.0, help='0이면 지직 없음'); a.add_argument('--seed', type=int, default=2)
    a.add_argument('--size', default='1080x1920'); a.add_argument('--bg', default='paper'); a.add_argument('--w', type=float, default=.85); a.add_argument('--y', type=float, default=.62)
    a.add_argument('--out', required=True)
    a = sub.add_parser('sheet', help='표정·자세 카탈로그 한 장'); a.add_argument('--style', default='B'); a.add_argument('--out', required=True)
    A = ap.parse_args()
    bg = None if getattr(A, 'bg', 'paper') == 'none' else (PAPER if getattr(A, 'bg', 'paper') == 'paper' else tuple(int(A.bg[i:i + 2], 16) for i in (1, 3, 5)))
    if A.cmd == 'still':
        im = draw_cat(A.style, A.expr, A.pose, A.seed, 0, 0)
        if A.size != '0': W, H = parse_size(A.size); im = compose(W, H, [(im, A.x, A.y, A.w)], bg)
        im.save(A.out); print(A.out)
    elif A.cmd == 'boil':
        W, H = (0, 0) if A.size == '0' else parse_size(A.size)
        fr = shot_frames(dict(style=A.style, expr=A.expr, pose=A.pose, seed=A.seed, x=A.x, y=A.y, w=A.w), A.frames, A.boil, W, H, bg)
        save_anim(fr, A.out, A.fps); print(A.out)
    elif A.cmd == 'seq':
        W, H = parse_size(A.size); rng = random.Random(A.seed); shots = parse_shots(A.shots); frames = []; k = 0
        for i, sh in enumerate(shots):
            n = max(1, round(sh['dur'] * A.fps)); sh.update(seed=A.seed, y=A.y, w=A.w)
            fr = shot_frames(sh, n, A.boil, W, H, bg, frame0=k); k += n
            if i > 0 and A.glitch > 0:   # 앞 컷과 섞이며 지직
                prev = frames[-1].convert('RGB'); fr[0] = glitch(Image.blend(prev, fr[0].convert('RGB'), .5), A.glitch, rng, bg or PAPER)
                if len(fr) > 1: fr[1] = glitch(fr[1], A.glitch * .5, rng, bg or PAPER)
            frames += fr
        save_anim(frames, A.out, A.fps); print(A.out, len(frames), 'frames')
    elif A.cmd == 'sheet':
        exprs = list(EXPR); poses = ['sit', 'squash:1', 'stretch:1', 'melt:1', 'tilt:-14', 'lean:18', 'jump:1+stretch:.4', 'puff:1', 'flip+tilt:10']
        cw, chh = 540, 400; cols = 5
        cells = [(e, 'sit') for e in exprs] + [('base', p) for p in poses[1:]]
        rows = (len(cells) + cols - 1) // cols; sheet = Image.new('RGB', (cw * cols, chh * rows), PAPER); d = ImageDraw.Draw(sheet)
        try: F = ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc', 26)
        except Exception: F = ImageFont.load_default()
        for i, (e, ps) in enumerate(cells):
            im = compose(cw, chh - 40, [(draw_cat(A.style, e, ps, 2, 0, 0), .5, .9, .62)], PAPER)
            x, y = (i % cols) * cw, (i // cols) * chh; sheet.paste(im.convert('RGB'), (x, y)); d.text((x + 16, y + chh - 38), f'{e}  /  {ps}', fill=(90, 80, 75), font=F)
        sheet.save(A.out); print(A.out)

if __name__ == '__main__':
    main()
