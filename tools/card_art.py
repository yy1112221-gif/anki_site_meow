#!/usr/bin/env python3
"""MEOWCA 선물 카드 그림 생성기 (② 디자인 2026-11-25).
python3 tools/card_art.py            -> cat/card/ 에 모든 장식(svg·webp)과 펜낙서 냥이 png를 만든다.
같은 시드라 매번 같은 그림. 필요: numpy, Pillow(webp), 같은 폴더의 meowca_doodle.py·meowca_doodle_base.json.
디자인 시안: https://claude.ai/artifact/2YritWLAbnc6ZKH2GPRrNZ · 설계: 프로젝트 문서 claude/MEOWCA_선물카드_구현설계.md
"""
import json, math, random, os, sys, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "..", "cat", "card")
os.makedirs(OUT, exist_ok=True)

INK = "#3a2a2a"

def jit(pts, a, r):
    return [(x + r.uniform(-a, a), y + r.uniform(-a, a)) for x, y in pts]

def smooth(pts, closed=True):
    # Catmull-Rom -> cubic bezier
    n = len(pts); d = f"M{pts[0][0]:.1f},{pts[0][1]:.1f}"
    rng = range(n) if closed else range(n - 1)
    for i in rng:
        p0 = pts[(i - 1) % n] if closed or i > 0 else pts[0]
        p1 = pts[i]; p2 = pts[(i + 1) % n]
        p3 = pts[(i + 2) % n] if closed or i + 2 < n else pts[-1]
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        d += f" C{c1[0]:.1f},{c1[1]:.1f} {c2[0]:.1f},{c2[1]:.1f} {p2[0]:.1f},{p2[1]:.1f}"
    return d + (" Z" if closed else "")

def rect_pts(x, y, w, h, step=24, rr=0):
    pts = []
    for t in range(0, int(w), step): pts.append((x + t, y))
    for t in range(0, int(h), step): pts.append((x + w, y + t))
    for t in range(0, int(w), step): pts.append((x + w - t, y + h))
    for t in range(0, int(h), step): pts.append((x, y + h - t))
    return pts

def wobble_rect(x, y, w, h, r, a=1.6, step=22):
    return smooth(jit(rect_pts(x, y, w, h, step), a, r))

def heart(cx, cy, s, r, fill, stroke=INK, sw=2.2, rot=0):
    pts = []
    for k in range(28):
        t = k / 28 * 2 * math.pi
        x = 16 * math.sin(t) ** 3
        y = -(13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t) - math.cos(4 * t))
        pts.append((cx + x * s / 16, cy + y * s / 16))
    pts = jit(pts, s * 0.03, r)
    return f'<path d="{smooth(pts)}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" stroke-linejoin="round" transform="rotate({rot} {cx} {cy})"/>'

def star(cx, cy, s, r, fill, stroke=INK, sw=2.2, rot=0):
    pts = []
    for k in range(10):
        ang = -math.pi / 2 + k * math.pi / 5
        rad = s if k % 2 == 0 else s * 0.48
        pts.append((cx + rad * math.cos(ang), cy + rad * math.sin(ang)))
    pts = jit(pts, s * 0.06, r)
    d = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts) + " Z"
    return f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" stroke-linejoin="round" transform="rotate({rot} {cx} {cy})"/>'

def sparkle(cx, cy, s, r, col=INK, sw=2.4):
    o = ""
    for ang in (0, 90):
        a = math.radians(ang + r.uniform(-8, 8))
        o += f'<path d="M{cx - s * math.cos(a):.1f},{cy - s * math.sin(a):.1f} Q{cx + r.uniform(-2,2):.1f},{cy + r.uniform(-2,2):.1f} {cx + s * math.cos(a):.1f},{cy + s * math.sin(a):.1f}" stroke="{col}" stroke-width="{sw}" stroke-linecap="round" fill="none"/>'
    return o

def dot(cx, cy, s, col): return f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{s}" fill="{col}"/>'

def scallop(x, y, w, h, bump, r):
    # wavy (scalloped) frame outline going clockwise
    pts = []
    def edge(x0, y0, x1, y1, nx, ny):
        L = math.hypot(x1 - x0, y1 - y0); n = max(2, round(L / bump))
        for i in range(n):
            for k in range(6):
                t = (i + k / 6) / n
                amp = math.sin(k / 6 * math.pi) * bump * 0.32
                pts.append((x0 + (x1 - x0) * t + nx * amp, y0 + (y1 - y0) * t + ny * amp))
    edge(x, y, x + w, y, 0, -1); edge(x + w, y, x + w, y + h, 1, 0)
    edge(x + w, y + h, x, y + h, 0, 1); edge(x, y + h, x, y, -1, 0)
    return smooth(jit(pts, 0.9, r))

def svg(name, w, h, body):
    open(f"{OUT}/{name}", "w").write(
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">{body}</svg>')

def scatter(r, n, w, h, avoid, kinds, margin=30):
    out = []; tries = 0; placed = []
    while len(out) < n and tries < 4000:
        tries += 1
        x, y = r.uniform(margin, w - margin), r.uniform(margin, h - margin)
        if any(ax <= x <= ax + aw and ay <= y <= ay + ah for ax, ay, aw, ah in avoid): continue
        if any(math.hypot(x - px, y - py) < 70 for px, py in placed): continue
        placed.append((x, y)); out.append(r.choice(kinds)(x, y))
    return "".join(out)

W, H = 1080, 1350

# ---------- 1. PINK letter paper ----------
r = random.Random(11)
b = ""
b += f'<path d="{scallop(56, 56, W - 112, H - 112, 46, r)}" fill="#fffafb" stroke="#e98bb0" stroke-width="5"/>'
b += f'<path d="{wobble_rect(92, 92, W - 184, H - 184, r, 1.2)}" fill="none" stroke="#f2a9c4" stroke-width="3" stroke-dasharray="2 14" stroke-linecap="round"/>'
# tiny hearts in outer margin (between edge and scallop)
pinks = ["#ff9fc0", "#ffc2d6", "#f47aa5"]
kinds = [lambda x, y: heart(x, y, r.uniform(9, 14), r, r.choice(pinks), INK, 1.8, r.uniform(-25, 25)),
         lambda x, y: dot(x, y, r.uniform(3, 5), "#f7b7cc"),
         lambda x, y: sparkle(x, y, r.uniform(7, 10), r, "#e07aa0", 2)]
b += scatter(r, 120, W, H, [(110, 110, W - 220, H - 220)], kinds, 14)
# ruled lines for message
for i in range(5):
    y = 840 + i * 72
    pts = [(170 + t * 37, y + r.uniform(-1.2, 1.2)) for t in range(21)]
    b += f'<path d="{smooth(pts, False)}" stroke="#f4b9cd" stroke-width="2.4" fill="none" stroke-linecap="round"/>'
# big hand heart deco near title
b += heart(220, 300, 34, r, "#ff8fb6", INK, 3, -14) + heart(870, 250, 24, r, "#ffd0e0", INK, 2.6, 18)
b += sparkle(905, 335, 16, r) + sparkle(170, 420, 12, r)
svg("pink.svg", W, H, b)

# ---------- 2. MINT photo-strip frame ----------
r = random.Random(5)
b = ""
win = (120, 150, W - 240, 1020)
b += f'<path d="{wobble_rect(*win, r, 1.8)}" fill="#ffffff" stroke="{INK}" stroke-width="4.5"/>'
b += f'<path d="{wobble_rect(win[0]+16, win[1]+16, win[2]-32, win[3]-32, r, 1.4)}" fill="none" stroke="#9ad8bb" stroke-width="2.5" stroke-dasharray="10 9" stroke-linecap="round"/>'
# grid dots inside (graph paper)
for gx in range(180, W - 170, 40):
    for gy in range(210, 1130, 40):
        b += dot(gx, gy, 1.6, "#d3efe2")
cols = ["#ffe27a", "#ffb4c9", "#a9e3ff", "#ffffff"]
kinds = [lambda x, y: star(x, y, r.uniform(12, 18), r, r.choice(cols), INK, 2.4, r.uniform(-30, 30)),
         lambda x, y: heart(x, y, r.uniform(11, 15), r, "#ffb4c9", INK, 2.2, r.uniform(-20, 20)),
         lambda x, y: sparkle(x, y, r.uniform(8, 12), r, INK, 2.6),
         lambda x, y: dot(x, y, 5, "#ffffff")]
b += scatter(r, 46, W, H, [(win[0] - 10, win[1] - 10, win[2] + 20, win[3] + 20), (0, 1180, 1080, 170)], kinds, 30)
svg("mint.svg", W, H, b)

# ---------- 3. CREAM Korean hand-letter ----------
r = random.Random(8)
b = ""
# soft emboss: faint raised petals in corner
for k in range(7):
    ang = k / 7 * 2 * math.pi
    cx, cy = 900 + 60 * math.cos(ang), 190 + 60 * math.sin(ang)
    b += f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="46" ry="26" transform="rotate({math.degrees(ang):.0f} {cx:.1f} {cy:.1f})" fill="none" stroke="#ffffff" stroke-width="5"/>'
    b += f'<ellipse cx="{cx+2:.1f}" cy="{cy+2:.1f}" rx="46" ry="26" transform="rotate({math.degrees(ang):.0f} {cx+2:.1f} {cy+2:.1f})" fill="none" stroke="#e9e1d2" stroke-width="2"/>'
# thin pen tulip, lower left
pen = "#4a3b36"
stem = smooth([(170, 1230), (176, 1150), (168, 1070), (182, 990), (178, 930)], False)
b += f'<path d="{stem}" stroke="{pen}" stroke-width="2.2" fill="none" stroke-linecap="round"/>'
b += f'<path d="M176,1120 C130,1090 112,1050 120,1010 C150,1030 170,1070 176,1120" stroke="{pen}" stroke-width="2" fill="none"/>'
b += f'<path d="M150,935 C140,880 160,850 178,840 C196,850 216,880 206,935 C190,948 166,948 150,935 Z" stroke="{pen}" stroke-width="2.2" fill="#f7c9cf"/>'
b += f'<path d="M178,842 C172,870 172,905 178,944" stroke="{pen}" stroke-width="1.6" fill="none"/>'
b += sparkle(232, 880, 9, r, pen, 1.8) + sparkle(120, 870, 6, r, pen, 1.6)
# airmail stripe edge top & bottom
for i in range(0, W, 54):
    b += f'<path d="M{i},0 l26,0 l-18,22 l-26,0 Z" fill="#f2a6b4" opacity=".75"/>'
    b += f'<path d="M{i+27},0 l26,0 l-18,22 l-26,0 Z" fill="#9cc8e8" opacity=".75"/>'
    b += f'<path d="M{i},{H} l26,0 l-18,-22 l-26,0 Z" fill="#9cc8e8" opacity=".75"/>'
    b += f'<path d="M{i+27},{H} l26,0 l-18,-22 l-26,0 Z" fill="#f2a6b4" opacity=".75"/>'
# light ruled lines
for i in range(5):
    y = 860 + i * 70
    b += f'<path d="M300,{y} L{W-130},{y}" stroke="#e6dccb" stroke-width="2" stroke-dasharray="1 9" stroke-linecap="round"/>'
svg("cream.svg", W, H, b)

# ---------- 4. NIGHT starry ----------
r = random.Random(21)
b = ""
gold = ["#f7d774", "#ffe9a8", "#f4c35a"]
kinds = [lambda x, y: star(x, y, r.uniform(8, 16), r, r.choice(gold), "#1a1d38", 2, r.uniform(-30, 30)),
         lambda x, y: dot(x, y, r.uniform(2, 3.6), "#fff3c4"),
         lambda x, y: sparkle(x, y, r.uniform(6, 10), r, "#ffe9a8", 2.2)]
b += scatter(r, 70, W, H, [(150, 560, 780, 620)], kinds, 30)
# crescent moon
b += f'<path d="M880,150 C800,170 770,280 830,340 C880,390 960,370 990,320 C930,340 870,300 865,240 C860,200 870,170 880,150 Z" fill="#fbe39a" stroke="#1a1d38" stroke-width="3"/>'
# hand line card
b += f'<path d="{wobble_rect(130, 560, 820, 640, r, 2)}" fill="#fffaf0" stroke="#f7d774" stroke-width="4"/>'
b += f'<path d="{wobble_rect(150, 580, 780, 600, r, 1.4)}" fill="none" stroke="#e7c766" stroke-width="2" stroke-dasharray="3 12" stroke-linecap="round"/>'
svg("night.svg", W, H, b)

# ---------- 5. GIFT BOX (closed) + lid ----------
def box(name, pal, lid_off=0, lid_rot=0, seed=3):
    r = random.Random(seed)
    body, dk, rib = pal
    BW, BH = 320, 300
    b = ""
    # shadow
    b += f'<ellipse cx="160" cy="290" rx="128" ry="10" fill="#000" opacity=".08"/>'
    # body
    b += f'<path d="{wobble_rect(40, 130, 240, 152, r, 1.6, 20)}" fill="{body}" stroke="{INK}" stroke-width="4" stroke-linejoin="round"/>'
    # pattern: tiny hearts & dots on body
    for (hx, hy) in [(72, 170), (110, 230), (230, 175), (250, 245), (80, 262), (200, 262)]:
        b += heart(hx, hy, 8, r, "#ffffff", dk, 1.6, r.uniform(-25, 25))
    for (hx, hy) in [(95, 195), (225, 215), (130, 160), (190, 150), (60, 220), (262, 205)]:
        b += dot(hx, hy, 3, "#ffffff")
    # ribbon vertical with wavy edge
    lv = smooth(jit([(146, 132), (148, 170), (145, 210), (148, 250), (146, 282), (174, 282), (176, 250), (173, 210), (176, 170), (174, 132)], 1, r))
    b += f'<path d="{lv}" fill="{rib}" stroke="{INK}" stroke-width="3"/>'
    b += f'<path d="M160,140 L160,276" stroke="{dk}" stroke-width="1.6" stroke-dasharray="4 7" stroke-linecap="round" opacity=".7"/>'
    # lid group
    lid = ""
    lid += f'<path d="{wobble_rect(28, 96, 264, 46, r, 1.5, 20)}" fill="{body}" stroke="{INK}" stroke-width="4" stroke-linejoin="round"/>'
    lid += f'<path d="M34,134 Q160,142 286,134" stroke="{dk}" stroke-width="2" fill="none" opacity=".5"/>'
    lid += f'<path d="{smooth(jit([(145,98),(147,120),(145,140),(175,140),(173,120),(175,98)],0.8,r))}" fill="{rib}" stroke="{INK}" stroke-width="3"/>'
    # bow: two loops + tails
    lid += f'<path d="M160,96 C120,50 70,62 86,92 C96,112 140,104 160,96 Z" fill="{rib}" stroke="{INK}" stroke-width="3.4" stroke-linejoin="round"/>'
    lid += f'<path d="M160,96 C200,50 250,62 234,92 C224,112 180,104 160,96 Z" fill="{rib}" stroke="{INK}" stroke-width="3.4" stroke-linejoin="round"/>'
    lid += f'<path d="M110,80 Q125,86 140,92 M210,80 Q195,86 180,92" stroke="{dk}" stroke-width="2" fill="none" stroke-linecap="round" opacity=".6"/>'
    lid += f'<ellipse cx="160" cy="96" rx="13" ry="11" fill="{rib}" stroke="{INK}" stroke-width="3.2"/>'
    if lid_off or lid_rot:
        lid = f'<g transform="translate(0 {-lid_off}) rotate({lid_rot} 160 120)">{lid}</g>'
    b += lid
    b += sparkle(22, 60, 10, r) + sparkle(300, 40, 12, r) + sparkle(296, 190, 8, r)
    svg(name, BW, BH, b)

box("box.svg", ("#ffb8cf", "#d94a7e", "#fff5e6"))
box("box_open.svg", ("#ffb8cf", "#d94a7e", "#fff5e6"), lid_off=70, lid_rot=-16)

# small gift icon for notification
r = random.Random(9)
b = f'<path d="{wobble_rect(10, 26, 44, 30, r, 1, 10)}" fill="#ffb8cf" stroke="{INK}" stroke-width="3"/>'
b += f'<path d="{wobble_rect(6, 16, 52, 12, r, .8, 10)}" fill="#ffb8cf" stroke="{INK}" stroke-width="3"/>'
b += f'<path d="M29,16 L29,56 M35,16 L35,56" stroke="{INK}" stroke-width="2.4"/><path d="M29,17 L35,17 L35,56 L29,56 Z" fill="#fff5e6"/>'
b += f'<path d="M32,16 C22,2 10,6 16,14 C20,18 28,17 32,16 Z M32,16 C42,2 54,6 48,14 C44,18 36,17 32,16 Z" fill="#fff5e6" stroke="{INK}" stroke-width="2.6"/>'
svg("gift_icon.svg", 64, 60, b)

# paper bg for phone
r = random.Random(4)
kinds = [lambda x, y: heart(x, y, r.uniform(6, 9), r, "#ffd3e1", "#e9a3bd", 1.4, r.uniform(-25, 25)),
         lambda x, y: dot(x, y, 2.6, "#f6c6d6"),
         lambda x, y: sparkle(x, y, 6, r, "#e9a3bd", 1.6)]
svg("phone_bg.svg", 390, 844, scatter(r, 34, 390, 844, [], kinds, 16))


# ================= 모던 포장지 =================
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageChops

rng = np.random.default_rng(7); R = random.Random(7)
base = json.load(open(os.path.join(HERE, "meowca_doodle_base.json")))

# ---------- washi fibers overlay (transparent) ----------
W, H = 1080, 1350
im = Image.new("RGBA", (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(im)
for _ in range(900):
    x, y = R.uniform(0, W), R.uniform(0, H); L = R.uniform(8, 46); a = R.uniform(0, math.pi)
    pts = [(x + math.cos(a) * L * t + R.uniform(-1.5, 1.5), y + math.sin(a) * L * t + R.uniform(-1.5, 1.5)) for t in np.linspace(0, 1, 5)]
    col = (150, 130, 110, R.randint(18, 45)) if R.random() < .6 else (255, 255, 255, R.randint(60, 120))
    d.line(pts, fill=col, width=1)
n = rng.normal(0, 1, (H // 2, W // 2)); n = Image.fromarray(((n * 14) + 128).clip(0, 255).astype("uint8")).resize((W, H)).filter(ImageFilter.GaussianBlur(1.2))
a = np.array(n).astype(float) - 128
blot = np.zeros((H, W, 4), "uint8"); blot[..., :3] = np.where((a < 0)[..., None], [140, 120, 100], [255, 255, 255]); blot[..., 3] = (np.abs(a) * 1.2).clip(0, 22)
im = Image.alpha_composite(Image.fromarray(blot), im)
im.resize((W // 2, H // 2), Image.LANCZOS).save(f"{OUT}/washi.webp", quality=60)  # 앱에서 1080×1350으로 늘려 씀

# ---------- watercolor sprig ----------
S = 2
def wc_blob(size, cx, cy, rx, ry, rot, color, alpha=0.55, seed=0):
    rr = random.Random(seed)
    lay = Image.new("L", size, 0); dd = ImageDraw.Draw(lay)
    pts = []
    for k in range(40):
        t = k / 40 * 2 * math.pi; rad = 1 + rr.uniform(-.12, .12)
        x, y = rx * math.cos(t) * rad, ry * math.sin(t) * rad
        c, s = math.cos(rot), math.sin(rot)
        pts.append((cx + x * c - y * s, cy + x * s + y * c))
    dd.polygon(pts, fill=255)
    soft = lay.filter(ImageFilter.GaussianBlur(3 * S))
    edge = ImageChops.subtract(lay.filter(ImageFilter.GaussianBlur(1.2 * S)), lay.filter(ImageFilter.GaussianBlur(7 * S)))
    m = np.array(soft).astype(float) / 255 * alpha + np.array(edge).astype(float) / 255 * 0.55
    noise = rng.normal(1, .12, m.shape); m = (m * noise).clip(0, .95)
    out = np.zeros((size[1], size[0], 4), "uint8"); out[..., :3] = color; out[..., 3] = (m * 255).astype("uint8")
    return Image.fromarray(out)

def sprig(name, w, h, flowers, stems, leaves, seed):
    size = (w * S, h * S); canvas = Image.new("RGBA", size, (0, 0, 0, 0))
    k = seed
    for (pts, col) in stems:
        lay = Image.new("RGBA", size, (0, 0, 0, 0)); dd = ImageDraw.Draw(lay)
        dd.line([(x * S, y * S) for x, y in pts], fill=col + (170,), width=int(2.2 * S), joint="curve")
        canvas = Image.alpha_composite(canvas, lay.filter(ImageFilter.GaussianBlur(.6 * S)))
    for (cx, cy, l, wd, rot, col) in leaves:
        k += 1; canvas = Image.alpha_composite(canvas, wc_blob(size, (cx + math.cos(rot) * l / 2) * S, (cy + math.sin(rot) * l / 2) * S, l / 2 * S, wd * S, rot, col, .5, k))
    for (cx, cy, r, col, np_) in flowers:
        for p in range(np_):
            k += 1; ang = p / np_ * 2 * math.pi + seed
            canvas = Image.alpha_composite(canvas, wc_blob(size, (cx + math.cos(ang) * r * .55) * S, (cy + math.sin(ang) * r * .55) * S, r * .55 * S, r * .38 * S, ang, col, .45, k))
        k += 1; canvas = Image.alpha_composite(canvas, wc_blob(size, cx * S, cy * S, r * .18 * S, r * .18 * S, 0, (235, 180, 70), .8, k))
    canvas.resize((w, h), Image.LANCZOS).save(f"{OUT}/{name}", quality=88)

pink, blue, lilac, leaf, leaf2 = (232, 128, 150), (120, 160, 210), (175, 140, 205), (120, 165, 120), (150, 185, 120)
sprig("sprig_a.webp", 420, 520,
      flowers=[(250, 110, 46, pink, 5), (150, 190, 36, (240, 160, 175), 5), (300, 230, 30, blue, 5), (205, 300, 26, lilac, 5), (110, 95, 22, blue, 5)],
      stems=[([(60, 500), (120, 400), (170, 300), (210, 200), (250, 120)], (110, 140, 100)), ([(120, 400), (160, 330), (205, 300)], (110, 140, 100)), ([(170, 300), (240, 260), (300, 230)], (110, 140, 100)), ([(150, 340), (140, 260), (150, 190)], (110, 140, 100))],
      leaves=[(120, 400, 70, 16, -2.4, leaf), (160, 340, 64, 15, -.4, leaf2), (200, 230, 56, 14, -2.6, leaf), (90, 450, 60, 14, -.9, leaf2), (230, 170, 48, 12, -.2, leaf)], seed=1)
sprig("sprig_b.webp", 300, 260,
      flowers=[(90, 90, 30, (240, 160, 175), 5), (170, 70, 22, blue, 5), (210, 140, 18, pink, 5)],
      stems=[([(20, 240), (70, 170), (90, 90)], (110, 140, 100)), ([(70, 170), (140, 120), (210, 140)], (110, 140, 100)), ([(110, 140), (150, 100), (170, 70)], (110, 140, 100))],
      leaves=[(60, 190, 50, 12, -2.2, leaf), (120, 135, 44, 11, -.6, leaf2), (40, 215, 44, 11, -.5, leaf)], seed=4)

# ---------- wax seal with embossed cat (original silhouette) ----------
SZ = 360
def seal(name, base_col):
    big = SZ * 2
    m = Image.new("L", (big, big), 0); d = ImageDraw.Draw(m)
    pts = []
    for k in range(60):
        t = k / 60 * 2 * math.pi; r = big * .46 * (1 + R.uniform(-.035, .035))
        pts.append((big / 2 + r * math.cos(t), big / 2 + r * math.sin(t)))
    d.polygon(pts, fill=255); m = m.filter(ImageFilter.GaussianBlur(3))
    # height map: dome + inner ring + cat relief
    h = Image.new("L", (big, big), 0); hd = ImageDraw.Draw(h)
    hd.polygon(pts, fill=120)
    hd.ellipse([big * .14, big * .14, big * .86, big * .86], fill=70)
    sc = big * .62 / base["W"]; ox = big / 2 - base["W"] * sc / 2; oy = big / 2 - base["H"] * sc / 2 + big * .02
    cat = [(ox + x * sc, oy + y * sc) for x, y in base["outline"]]
    hd.polygon(cat, fill=150)
    for (ex, ey) in base["eyes"]:
        hd.ellipse([ox + ex * sc - 7, oy + ey * sc - 7, ox + ex * sc + 7, oy + ey * sc + 7], fill=95)
    mx, my, mw, mh = base["mouth"]
    cx0, cy0 = ox + mx * sc, oy + my * sc; ww, hh = mw * sc / 2, mh * sc
    hd.arc([cx0 - ww, cy0 - hh / 2, cx0, cy0 + hh / 2], 0, 180, fill=95, width=6)
    hd.arc([cx0, cy0 - hh / 2, cx0 + ww, cy0 + hh / 2], 0, 180, fill=95, width=6)
    hf = np.array(h.filter(ImageFilter.GaussianBlur(5))).astype(float)
    gy, gx = np.gradient(hf)
    shade = (-gx * .7 - gy * .7) * 4.5
    col = np.array(base_col, float)[None, None, :] * (1 + shade[..., None] / 255 * 2.2)
    col = col + (rng.normal(0, 4, col.shape))
    out = np.zeros((big, big, 4), "uint8"); out[..., :3] = col.clip(0, 255); out[..., 3] = np.array(m)
    Image.fromarray(out).resize((SZ, SZ), Image.LANCZOS).save(f"{OUT}/{name}", quality=88)
seal("seal_rose.webp", (196, 92, 112))
seal("seal_gold.webp", (190, 150, 80))

# ---------- envelope (back, flap closed / open) ----------
def env(name, open_):
    w, h = 760, 500
    b = f'<rect x="4" y="4" width="{w-8}" height="{h-8}" rx="10" fill="#fbf7f0" stroke="#e5dccd" stroke-width="2"/>'
    b += f'<path d="M6,{h-6} L{w/2},{h*0.52} L{w-6},{h-6}" fill="#f6f0e6" stroke="#e2d8c8" stroke-width="2"/>'
    b += f'<path d="M6,8 L{w/2},{h*0.55} L6,{h-8} Z" fill="#f8f2e9" stroke="#e7ddce" stroke-width="1.5"/>'
    b += f'<path d="M{w-6},8 L{w/2},{h*0.55} L{w-6},{h-8} Z" fill="#f8f2e9" stroke="#e7ddce" stroke-width="1.5"/>'
    if not open_:
        b += f'<path d="M6,8 L{w/2},{h*0.58} L{w-6},8 Z" fill="#fdf9f3" stroke="#e2d8c8" stroke-width="2"/>'
        # liner pattern peek: tiny dots on flap
        for i in range(14):
            for j in range(6):
                x = 60 + i * 48 + (j % 2) * 24; y = 22 + j * 34
                if y < (h * 0.58 - 10) * (1 - abs(x - w / 2) / (w / 2)) + 8:
                    b += f'<circle cx="{x}" cy="{y}" r="2.2" fill="#f2c9d2"/>'
    else:
        b += f'<path d="M6,8 L{w/2},{-h*0.42} L{w-6},8 Z" fill="#f4d9df" stroke="#e2c6cc" stroke-width="2"/>'
    open(f"{OUT}/{name}", "w").write(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 {-h*0.45 if open_ else 0} {w} {h*(1.45 if open_ else 1)}" width="{w}" height="{h*(1.45 if open_ else 1):.0f}">{b}</svg>')
env("env_closed.svg", False); env("env_open.svg", True)

# ---------- blind-emboss sakura petals (tone on tone) ----------
def petal(cx, cy, s, rot):
    p = f"M0,{-s} C{s*.7},{-s*.7} {s*.75},{s*.3} 0,{s} C{-s*.75},{s*.3} {-s*.7},{-s*.7} {-s*.12},{-s*1.02} L0,{-s*.8} Z"
    t = f'transform="translate({cx:.1f} {cy:.1f}) rotate({rot:.0f})"'
    return (f'<path d="{p}" {t} fill="none" stroke="#ffffff" stroke-width="3.2" stroke-opacity=".95" />'
            f'<path d="{p}" transform="translate({cx+1.8:.1f} {cy+2.2:.1f}) rotate({rot:.0f})" fill="none" stroke="#d9b9c0" stroke-width="1.6" stroke-opacity=".7"/>')
def blossom(cx, cy, s, rot):
    o = ""
    for k in range(5):
        a = math.radians(rot + k * 72)
        o += petal(cx + math.cos(a - math.pi/2) * s * .95, cy + math.sin(a - math.pi/2) * s * .95, s, rot + k * 72)
    return o
b = ""
spots = []
for _ in range(400):
    x = R.uniform(-40, W + 40); y = R.uniform(-40, 700)
    # cascade densest top-right
    if R.random() > (x / W) * (1 - y / 700) * 1.4: continue
    if any(math.hypot(x - a, y - c) < 70 for a, c in spots): continue
    spots.append((x, y))
    if R.random() < .45: b += blossom(x, y, R.uniform(16, 26), R.uniform(0, 72))
    else: b += petal(x, y, R.uniform(10, 16), R.uniform(0, 360))
open(f"{OUT}/emboss.svg", "w").write(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}">{b}</svg>')

# ---------- thin pen heart for korean card ----------
open(f"{OUT}/pen_heart.svg", "w").write('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 120 110" width="120" height="110"><path d="M60,96 C30,74 8,56 12,32 C16,10 46,8 58,30 C62,12 92,4 106,24 C120,48 92,72 60,96 M58,30 C57,40 62,52 60,60" fill="none" stroke="#2b2b2b" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/></svg>')


# ---------- 펜낙서 냥이 (키트 원본, 투명, 여백 잘라냄) ----------
from PIL import Image as _I
for style, expr, pose, name in [("B","happy","sit","cat_b_happy"),("B","love","sit","cat_b_love"),("B","happy","jump:.6","cat_b_jump"),
                                ("A","happy","sit","cat_a_happy"),("A","love","sit","cat_a_love"),("A","sleepy","melt:.4","cat_a_melt"),
                                ("B","shock","stretch:.4","cat_b_shock"),("A","shock","sit","cat_a_shock")]:
    p = os.path.join(OUT, name + ".png")
    subprocess.run([sys.executable, os.path.join(HERE, "meowca_doodle.py"), "still", "--style", style, "--expr", expr, "--pose", pose, "--size", "0", "--out", p], check=True, stdout=subprocess.DEVNULL)
    im = _I.open(p).convert("RGBA"); im = im.crop(im.getbbox()); im.thumbnail((640, 640)); im.save(p, optimize=True)
# 종이 결 타일
_rng = np.random.default_rng(3)
_n = _rng.normal(0, 1, (512, 512)); _img = _I.fromarray(((_n * 20) + 128).clip(0, 255).astype("uint8")).filter(ImageFilter.GaussianBlur(.6))
_a = np.array(_img).astype(float); _s = _rng.normal(0, 1, (512, 512))
_s = np.array(_I.fromarray(((_s * 40) + 128).clip(0, 255).astype("uint8")).resize((512, 64)).resize((512, 512))).astype(float)
_v = (_a - 128) * 0.7 + (_s - 128) * 0.3
_rgba = np.zeros((512, 512, 4), "uint8"); _rgba[..., 0:3] = np.where((_v < 0)[..., None], 60, 255); _rgba[..., 3] = (np.abs(_v) * 0.9).clip(0, 40)
_I.fromarray(_rgba).resize((256, 256), _I.LANCZOS).save(os.path.join(OUT, "grain.webp"), quality=60)  # 512px로 깔아 씀
for f in sorted(os.listdir(OUT)): print(f"{os.path.getsize(os.path.join(OUT, f)):>8}  {f}")
