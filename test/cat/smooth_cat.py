# 암기냥이 — なめらか版 (SVG 128x128)。白いステッカー縁は輪郭を太い白線でなぞって作る
import re, os
INK="#1d2b27"; FUR="#f7f2e8"; SHADE="#e6dcc9"; PINK="#f08fa8"; GREEN="#006945"; GREEN2="#2f8a5f"; CREAM="#fff1b0"; RED="#d9465a"; BLUE="#78bee6"
SW=3.2
def base(card_mark=None, tail=True):
    s=[]
    if tail: s.append(f'<path d="M86 112 C104 112 110 98 104 86 C100 78 108 70 112 74" fill="none" stroke="{FUR}" stroke-width="11" stroke-linecap="round" data-tail="1"/>')
    s.append(f'<ellipse cx="64" cy="101" rx="27" ry="21" fill="{FUR}"/>')
    s.append(f'<path d="M26 56 L33 16 Q35 9 41 13 L58 32 Z" fill="{FUR}" stroke-linejoin="round"/>')
    s.append(f'<path d="M102 56 L95 16 Q93 9 87 13 L70 32 Z" fill="{FUR}" stroke-linejoin="round"/>')
    s.append(f'<ellipse cx="64" cy="60" rx="42" ry="31" fill="{FUR}"/>')
    s.append(f'<ellipse cx="50" cy="118" rx="9" ry="5" fill="{FUR}"/>')
    s.append(f'<ellipse cx="78" cy="118" rx="9" ry="5" fill="{FUR}"/>')
    if card_mark:
        s.append(f'<g transform="rotate(-8 100 88)"><rect x="82" y="70" width="36" height="38" rx="7" fill="{GREEN}"/></g>')
    return s
DETAIL_INNER = [
    f'<path d="M34 46 L38 23 Q39 19 42 21 L52 33 Z" fill="{PINK}" stroke="none"/>',
    f'<path d="M94 46 L90 23 Q89 19 86 21 L76 33 Z" fill="{PINK}" stroke="none"/>',
    f'<ellipse cx="64" cy="112" rx="20" ry="8" fill="{SHADE}" stroke="none"/>',
    f'<path d="M42 86 Q64 96 86 86 L86 92 Q64 102 42 92 Z" fill="{GREEN}" stroke="none"/>',
    f'<path d="M74 92 L80 106 L70 104 Z" fill="{GREEN2}" stroke="none"/>',
]
def face(kind):
    f=[]; y=58
    if kind in ("ask","listen","think"):
        for cx in (47,81): f.append(f'<ellipse cx="{cx}" cy="{y}" rx="4.5" ry="5.5" fill="{INK}"/><circle cx="{cx+1.6}" cy="{y-2}" r="1.6" fill="#fff"/>')
    elif kind=="happy":
        for cx in (47,81): f.append(f'<path d="M{cx-6} {y+2} Q{cx} {y-6} {cx+6} {y+2}" fill="none" stroke="{INK}" stroke-width="3.2" stroke-linecap="round"/>')
    elif kind=="surprised":
        for cx in (46,82): f.append(f'<circle cx="{cx}" cy="{y}" r="8" fill="#fff" stroke="{INK}" stroke-width="2.6"/><circle cx="{cx}" cy="{y}" r="3.6" fill="{INK}"/>')
    elif kind=="sleepy":
        for cx in (47,81): f.append(f'<path d="M{cx-6} {y+1} Q{cx} {y+4} {cx+6} {y+1}" fill="none" stroke="{INK}" stroke-width="3" stroke-linecap="round"/>')
    elif kind=="love":
        for cx in (47,81): f.append(f'<path d="M{cx} {y+6} C{cx-9} {y} {cx-6} {y-7} {cx} {y-3} C{cx+6} {y-7} {cx+9} {y} {cx} {y+6} Z" fill="{PINK}"/>')
    if kind!="sleepy":
        f.append(f'<ellipse cx="36" cy="{y+9}" rx="5" ry="3" fill="{PINK}" opacity=".55"/><ellipse cx="92" cy="{y+9}" rx="5" ry="3" fill="{PINK}" opacity=".55"/>')
    f.append(f'<path d="M60 {y+6} L68 {y+6} L64 {y+10} Z" fill="{PINK}" stroke="{PINK}" stroke-width="1.5" stroke-linejoin="round"/>')
    if kind in ("happy","love"):
        f.append(f'<path d="M56 {y+13} Q64 {y+24} 72 {y+13} Z" fill="{RED}" stroke="{INK}" stroke-width="2.4" stroke-linejoin="round"/>')
    elif kind=="surprised":
        f.append(f'<ellipse cx="64" cy="{y+16}" rx="4" ry="5" fill="{INK}"/>')
    else:
        f.append(f'<path d="M56 {y+12} Q60 {y+16} 64 {y+12} Q68 {y+16} 72 {y+12}" fill="none" stroke="{INK}" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/>')
    for yy,dy in ((y+8,-3),(y+14,3)):
        f.append(f'<path d="M8 {yy+dy} L24 {yy}" stroke="{INK}" stroke-width="2.2" stroke-linecap="round"/><path d="M120 {yy+dy} L104 {yy}" stroke="{INK}" stroke-width="2.2" stroke-linecap="round"/>')
    return f
def card_face(mark):
    c=[f'<g transform="rotate(-8 100 88)"><rect x="86" y="74" width="28" height="30" rx="4" fill="{CREAM}"/>']
    if mark=="?": c.append(f'<text x="100" y="98" text-anchor="middle" font-family="Arial Rounded MT Bold,Arial,sans-serif" font-weight="900" font-size="22" fill="{GREEN}">?</text>')
    if mark=="!": c.append(f'<text x="100" y="98" text-anchor="middle" font-family="Arial,sans-serif" font-weight="900" font-size="22" fill="{GREEN}">!</text>')
    if mark=="lines":
        for yy,w in ((82,18),(89,14),(96,18)): c.append(f'<rect x="91" y="{yy}" width="{w}" height="3" rx="1.5" fill="{GREEN2}"/>')
    c.append('</g>')
    c.append(f'<ellipse cx="86" cy="100" rx="7" ry="6" fill="{FUR}" stroke="{INK}" stroke-width="{SW}"/>')
    return c
def extras(kind):
    e=[]
    if kind=="sleepy": e.append(f'<text x="100" y="26" font-family="Arial,sans-serif" font-weight="900" font-size="18" fill="{BLUE}" stroke="#fff" stroke-width="4" paint-order="stroke">z</text><text x="112" y="14" font-family="Arial,sans-serif" font-weight="900" font-size="12" fill="{BLUE}" stroke="#fff" stroke-width="3" paint-order="stroke">z</text>')
    if kind=="love": e.append(f'<path d="M110 26 C100 18 104 8 110 13 C116 8 120 18 110 26 Z" fill="{PINK}" stroke="#fff" stroke-width="3" paint-order="stroke"/>')
    if kind=="happy":
        for (x,y,r) in ((112,18,6),(16,26,4.5)): e.append(f'<path d="M{x} {y-r} Q{x} {y} {x+r} {y} Q{x} {y} {x} {y+r} Q{x} {y} {x-r} {y} Q{x} {y} {x} {y-r} Z" fill="{CREAM}" stroke="#fff" stroke-width="2.5" paint-order="stroke"/>')
    if kind=="surprised": e.append(f'<path d="M104 30 Q110 40 104 44 Q98 40 104 30 Z" fill="{BLUE}" stroke="#fff" stroke-width="2.5" paint-order="stroke"/>')
    if kind=="listen":
        e.append(f'<path d="M24 50 Q24 14 64 14 Q104 14 104 50" fill="none" stroke="{GREEN}" stroke-width="7" stroke-linecap="round"/>')
        e.append(f'<rect x="14" y="44" width="16" height="26" rx="7" fill="{GREEN}" stroke="{INK}" stroke-width="2.4"/><rect x="98" y="44" width="16" height="26" rx="7" fill="{GREEN}" stroke="{INK}" stroke-width="2.4"/>')
        e.append(f'<path d="M114 10 L114 22 M114 10 L122 8" stroke="{INK}" stroke-width="2.4" stroke-linecap="round" fill="none"/><circle cx="111" cy="23" r="3.5" fill="{INK}"/>')
    if kind=="think":
        for (x,y,r) in ((104,30,3),(112,20,4.5),(122,9,6)): e.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="#fff" stroke="{INK}" stroke-width="2"/>')
    return e
def make(kind):
    mark={"ask":"?","surprised":"!","think":"lines"}.get(kind)
    shapes=base(mark)
    def restyle(el, fill, stroke, w):
        el=re.sub(r' fill="[^"]*"', '', el); el=re.sub(r' stroke="[^"]*"','',el); el=re.sub(r' stroke-width="[^"]*"','',el)
        tail='data-tail' in el
        if tail: return el.replace('<path ', f'<path fill="none" stroke="{stroke}" stroke-width="{11+w}" ')
        return el.replace('<ellipse ', f'<ellipse fill="{fill}" stroke="{stroke}" stroke-width="{w}" ').replace('<path ', f'<path fill="{fill}" stroke="{stroke}" stroke-width="{w}" ').replace('<rect ', f'<rect fill="{fill}" stroke="{stroke}" stroke-width="{w}" ')
    sticker=[restyle(e,"#fff","#fff",12) for e in shapes]
    outline=[restyle(e,INK,INK,SW*2) for e in shapes]
    fill=[re.sub(r'<path (?=d="M86 112)', '<path ', e) for e in shapes]
    fill=[e.replace(f'stroke-width="11"', 'stroke-width="11"') for e in fill]
    parts=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="-4 -4 136 136" width="128" height="128">','<g stroke-linejoin="round" stroke-linecap="round">']
    parts+=sticker+outline+fill+DETAIL_INNER+(card_face(mark) if mark else [])+face(kind)+extras(kind)
    parts.append('</g></svg>')
    return "\n".join(parts)
os.makedirs("smooth",exist_ok=True)
for k in ["ask","happy","surprised","sleepy","love","listen","think"]:
    open(f"smooth/cat_{k}.svg","w").write(make(k))
print("ok")
