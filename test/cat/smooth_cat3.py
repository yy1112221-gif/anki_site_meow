# 암기냥이 v2 — もちっとした丸いかたまり・離れた点目・ω口（なめらか版 SVG）
import os
INK="#1d2b27"; FUR="#f8f3ea"; SHADE="#ebe1cf"; PINK="#f2a1b4"; BLUSH="#f4b39a"; PATCH="#d9c2a0"; GREEN="#006945"; GREEN2="#2f8a5f"; RED="#d9465a"; BLUE="#78bee6"; CREAM="#ffe9a8"
# 体: 上が少しつぶれたおまんじゅう型
BODY = "M14 92 C10 60 30 34 64 34 C98 34 118 60 114 92 C112 110 96 118 64 118 C32 118 16 110 14 92 Z"
EAR_L = "M24 52 C22 38 26 26 32 24 C37 23 44 32 48 38 Z"
EAR_R = "M104 52 C106 38 102 26 96 24 C91 23 84 32 80 38 Z"
TAIL = "M110 100 C124 98 126 84 118 80"
PAWS = [(44,116),(84,116)]
def sil(fill, stroke, w):
    p=[]
    p.append(f'<path d="{TAIL}" fill="none" stroke="{stroke}" stroke-width="{10+w}" stroke-linecap="round"/>')
    for d in (EAR_L, EAR_R, BODY): p.append(f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{w}" stroke-linejoin="round"/>')
    for x,y in PAWS: p.append(f'<ellipse cx="{x}" cy="{y}" rx="9" ry="5.5" fill="{fill}" stroke="{stroke}" stroke-width="{w}"/>')
    return p
def fill_layer():
    p=[f'<path d="{TAIL}" fill="none" stroke="{FUR}" stroke-width="10" stroke-linecap="round"/>']
    for d in (EAR_L, EAR_R, BODY): p.append(f'<path d="{d}" fill="{FUR}"/>')
    p.append(f'<path d="M30 42 C29 34 31 29 33 29 C36 29 40 34 42 38 Z" fill="{PINK}"/>')
    p.append(f'<path d="M98 42 C99 34 97 29 95 29 C92 29 88 34 86 38 Z" fill="{PINK}"/>')
    p.append(f'<path d="M78 37 C88 36 98 40 104 48 C96 46 86 44 78 44 Z" fill="{PATCH}" opacity=".9"/>')  # 右耳の付け根にぶち
    p.append(f'<path d="M20 100 C30 112 98 112 108 100 C104 112 90 118 64 118 C38 118 24 112 20 100 Z" fill="{SHADE}"/>')
    p.append(f'<path d="M36 96 Q64 106 92 96 L92 101 Q64 112 36 101 Z" fill="{GREEN}"/>')       # スカーフ
    p.append(f'<path d="M80 100 L86 112 L76 109 Z" fill="{GREEN2}"/>')
    for x,y in PAWS: p.append(f'<ellipse cx="{x}" cy="{y}" rx="9" ry="5.5" fill="{FUR}"/>')
    return p
def derp_eye(cx, y, px, py, lid=0.42, r=(7.4,6.3)):
    rx,ry=r; f=[]
    f.append(f'<ellipse cx="{cx}" cy="{y}" rx="{rx}" ry="{ry}" fill="#fff" stroke="{INK}" stroke-width="2.2"/>')
    f.append(f'<circle cx="{cx+px}" cy="{y+py}" r="2.7" fill="{INK}"/>')
    # 重いまぶた: 上の方を毛色でふさいで、横線を一本
    ly = y-ry+ry*2*lid
    f.append(f'<path d="M{cx-rx-1.2} {ly} L{cx+rx+1.2} {ly} L{cx+rx+1.2} {y-ry-2} L{cx-rx-1.2} {y-ry-2} Z" fill="{FUR}"/>')
    f.append(f'<path d="M{cx-rx-1} {ly} Q{cx} {ly-1.2} {cx+rx+1} {ly}" fill="none" stroke="{INK}" stroke-width="2.4" stroke-linecap="round"/>')
    # 下まつげ（ちょんちょん）
    for dx in (-3.6,0,3.6):
        f.append(f'<path d="M{cx+dx} {y+ry+0.6} L{cx+dx*1.25} {y+ry+3.6}" stroke="{INK}" stroke-width="1.3" stroke-linecap="round"/>')
    return f
def face(kind):
    f=[]; y=70; L,R=40,88
    if kind in ("ask","listen","think"):
        f+=derp_eye(L,y,-1.6,1.0); f+=derp_eye(R,y,1.8,-0.2)        # 左右で視線がずれる
    elif kind=="happy":
        for cx in (L,R): f.append(f'<path d="M{cx-5} {y+1.5} Q{cx} {y-4.5} {cx+5} {y+1.5}" fill="none" stroke="{INK}" stroke-width="2.8" stroke-linecap="round"/>')
    elif kind=="surprised":
        f+=derp_eye(L,y,0.4,0.6,lid=0.08,r=(6.8,6.4)); f+=derp_eye(R,y,-0.6,-0.4,lid=0.0,r=(8,7.6))  # 目の大きさもちぐはぐ
    elif kind=="sleepy":
        for cx in (L,R): f.append(f'<path d="M{cx-5} {y} Q{cx} {y+2.5} {cx+5} {y}" fill="none" stroke="{INK}" stroke-width="2.8" stroke-linecap="round"/>')
    elif kind=="love":
        for cx in (L,R): f.append(f'<path d="M{cx} {y+4} C{cx-6} {y} {cx-4} {y-5} {cx} {y-2} C{cx+4} {y-5} {cx+6} {y} {cx} {y+4} Z" fill="{RED}"/>')
    for cx in (L-5,R+5): f.append(f'<ellipse cx="{cx}" cy="{y+12}" rx="6.5" ry="3.8" fill="{BLUSH}" opacity=".7"/>')
    f.append(f'<ellipse cx="64" cy="{y+8}" rx="2.4" ry="1.7" fill="{PINK}"/>')
    if kind in ("happy","love"):
        f.append(f'<path d="M58 {y+12} Q61 {y+17} 64 {y+13} Q67 {y+17} 70 {y+12}" fill="none" stroke="{INK}" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/><path d="M61 {y+15} Q64 {y+22} 67 {y+15} Z" fill="{RED}"/>')
    elif kind in ("ask","listen","think","surprised"):
        # ぽかんと開いた口（少し横にずれる）
        f.append(f'<ellipse cx="{65 if kind!="surprised" else 64}" cy="{y+16}" rx="{3.2 if kind!="surprised" else 3.6}" ry="{4.2 if kind!="surprised" else 5}" fill="{INK}"/><ellipse cx="{65.6}" cy="{y+18}" rx="1.8" ry="1.4" fill="{PINK}"/>')
    else:
        f.append(f'<path d="M58 {y+12} Q61 {y+17} 64 {y+13} Q67 {y+17} 70 {y+12}" fill="none" stroke="{INK}" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round"/>')
    return f
def extras(kind):
    e=[]; st='stroke="#fff" stroke-width="4" paint-order="stroke"'
    if kind=="ask": e.append(f'<text x="100" y="30" text-anchor="middle" font-family="Arial Rounded MT Bold,Arial,sans-serif" font-weight="900" font-size="26" fill="{GREEN}" {st}>?</text>')
    if kind=="surprised": e.append(f'<text x="102" y="30" text-anchor="middle" font-family="Arial,sans-serif" font-weight="900" font-size="26" fill="{GREEN}" {st}>!</text><path d="M24 46 Q30 56 24 60 Q18 56 24 46 Z" fill="{BLUE}" stroke="#fff" stroke-width="2.5" paint-order="stroke"/>')
    if kind=="sleepy": e.append(f'<text x="100" y="30" font-family="Arial,sans-serif" font-weight="900" font-size="18" fill="{BLUE}" {st}>z</text><text x="112" y="16" font-family="Arial,sans-serif" font-weight="900" font-size="12" fill="{BLUE}" {st}>z</text><ellipse cx="74" cy="86" rx="3" ry="4" fill="{BLUE}" opacity=".7"/>')
    if kind=="love": e.append(f'<path d="M106 30 C96 22 100 12 106 17 C112 12 116 22 106 30 Z" fill="{RED}" stroke="#fff" stroke-width="3" paint-order="stroke"/>')
    if kind=="happy":
        for (x,y,r) in ((108,22,6),(18,34,4.5)): e.append(f'<path d="M{x} {y-r} Q{x} {y} {x+r} {y} Q{x} {y} {x} {y+r} Q{x} {y} {x-r} {y} Q{x} {y} {x} {y-r} Z" fill="{CREAM}" stroke="#fff" stroke-width="2.5" paint-order="stroke"/>')
    if kind=="listen":
        e.append(f'<path d="M22 66 Q20 30 64 30 Q108 30 106 66" fill="none" stroke="{GREEN}" stroke-width="6.5" stroke-linecap="round"/>')
        e.append(f'<rect x="12" y="60" width="15" height="24" rx="7" fill="{GREEN}" stroke="{INK}" stroke-width="2.4"/><rect x="101" y="60" width="15" height="24" rx="7" fill="{GREEN}" stroke="{INK}" stroke-width="2.4"/>')
        e.append(f'<path d="M114 14 L114 26 M114 14 L122 12" stroke="{INK}" stroke-width="2.4" stroke-linecap="round" fill="none"/><circle cx="111" cy="27" r="3.5" fill="{INK}"/>')
    if kind=="think":
        for (x,y,r) in ((100,28,3),(108,18,4.5),(118,7,6)): e.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="#fff" stroke="{INK}" stroke-width="2"/>')
    return e
def make(kind):
    parts=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="-4 -4 136 136" width="128" height="128"><g stroke-linejoin="round" stroke-linecap="round">']
    parts+=sil("#fff","#fff",12)+sil("#1d2b27","#1d2b27",6.4)+fill_layer()+face(kind)+extras(kind)
    parts.append('</g></svg>'); return "\n".join(parts)
os.makedirs("smooth3",exist_ok=True)
for k in ["ask","happy","surprised","sleepy","love","listen","think"]:
    open(f"smooth3/cat_{k}.svg","w").write(make(k))
print("ok")
