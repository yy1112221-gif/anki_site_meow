# 암기냥이 — とろける猫（F_melt）の表情7種
import os
exec(open("variations.py").read().split("V={}")[0])   # 色と sv() を流用
RED="#d9465a"; BLUE="#78bee6"; CREAM="#ffe9a8"
BODY=[(P,'d="M4 112 C4 100 14 96 22 96 C24 80 34 60 64 60 C94 60 104 80 106 96 C114 96 124 100 124 112 C124 118 116 120 64 120 C12 120 4 118 4 112 Z"',FUR),
      (P,'d="M40 70 L40 50 L54 62 Z"',FUR),(P,'d="M88 70 L88 50 L74 62 Z"',FUR)]
COMMON=[f'<path d="M43 64 L43 55 L50 61 Z" fill="{PINK}"/>',f'<path d="M85 64 L85 55 L78 61 Z" fill="{PINK}"/>',
        f'<path d="M8 114 C40 120 88 120 120 114" fill="none" stroke="{SHADE}" stroke-width="4"/>',
        f'<circle cx="112" cy="104" r="3" fill="#fff" opacity=".8"/>',
        f'<path d="M30 106 Q64 112 98 106" fill="none" stroke="{GREEN}" stroke-width="4" opacity=".9"/>']
st='stroke="#fff" stroke-width="4" paint-order="stroke"'
def face(kind):
    L,R_,y=52,76,80; f=[]
    if kind in ("ask","think","listen"): f+=eyes_dot(L,R_,y,3)
    elif kind=="happy": f+=[f'<path d="M{x-4} {y+1.5} Q{x} {y-3.5} {x+4} {y+1.5}" fill="none" stroke="{INK}" stroke-width="2.6"/>' for x in (L,R_)]
    elif kind=="surprised": f+=[f'<circle cx="{x}" cy="{y}" r="5" fill="#fff" stroke="{INK}" stroke-width="2.2"/><circle cx="{x}" cy="{y}" r="2" fill="{INK}"/>' for x in (L,R_)]
    elif kind=="sleepy": f+=[f'<path d="M{x-4} {y} Q{x} {y+2.4} {x+4} {y}" fill="none" stroke="{INK}" stroke-width="2.6"/>' for x in (L,R_)]
    elif kind=="love": f+=[f'<path d="M{x} {y+3.5} C{x-5.5} {y} {x-3.5} {y-4.5} {x} {y-1.8} C{x+3.5} {y-4.5} {x+5.5} {y} {x} {y+3.5} Z" fill="{RED}"/>' for x in (L,R_)]
    f+=blush(44,84,88)
    f.append(f'<ellipse cx="64" cy="{y+4.5}" rx="2" ry="1.4" fill="{PINK}"/>')
    if kind=="surprised": f.append(f'<ellipse cx="64" cy="{y+11}" rx="2.6" ry="3.2" fill="{INK}"/>')
    elif kind in ("happy","love"): f.append(omega(64,y+8,4)); f.append(f'<path d="M61.6 {y+11} Q64 {y+16} 66.4 {y+11} Z" fill="{RED}"/>')
    else: f.append(omega(64,y+8,4))
    return f
def extras(kind):
    e=[]
    if kind=="ask": e.append(f'<text x="98" y="48" text-anchor="middle" font-family="Arial Rounded MT Bold,Arial,sans-serif" font-weight="900" font-size="26" fill="{GREEN}" {st}>?</text>')
    if kind=="surprised":
        e.append(f'<text x="98" y="48" text-anchor="middle" font-family="Arial,sans-serif" font-weight="900" font-size="26" fill="{GREEN}" {st}>!</text>')
        e.append(f'<path d="M32 64 Q38 74 32 78 Q26 74 32 64 Z" fill="{BLUE}" stroke="#fff" stroke-width="2.5" paint-order="stroke"/>')
        e+=[f'<path d="M{x} {y} L{x+dx} {y-6}" stroke="{INK}" stroke-width="2" opacity=".7"/>' for x,y,dx in ((50,56,-3),(64,52,0),(78,56,3))]
    if kind=="sleepy":
        e.append(f'<text x="94" y="52" font-family="Arial,sans-serif" font-weight="900" font-size="18" fill="{BLUE}" {st}>z</text><text x="106" y="38" font-family="Arial,sans-serif" font-weight="900" font-size="12" fill="{BLUE}" {st}>z</text>')
        e.append(f'<circle cx="74" cy="94" r="4.5" fill="#dff1fb" stroke="{BLUE}" stroke-width="1.5"/>')
    if kind=="love": e.append(f'<path d="M100 50 C90 42 94 32 100 37 C106 32 110 42 100 50 Z" fill="{RED}" stroke="#fff" stroke-width="3" paint-order="stroke"/>')
    if kind=="happy":
        for (x,y,r) in ((104,44,6),(22,62,4.5),(112,86,3.5)): e.append(f'<path d="M{x} {y-r} Q{x} {y} {x+r} {y} Q{x} {y} {x} {y+r} Q{x} {y} {x-r} {y} Q{x} {y} {x} {y-r} Z" fill="{CREAM}" stroke="#fff" stroke-width="2.5" paint-order="stroke"/>')
    if kind=="listen":
        e.append(f'<path d="M30 84 Q28 50 64 50 Q100 50 98 84" fill="none" stroke="{GREEN}" stroke-width="6" stroke-linecap="round"/>')
        e.append(f'<rect x="20" y="76" width="14" height="20" rx="6" fill="{GREEN}" stroke="{INK}" stroke-width="2.4"/><rect x="94" y="76" width="14" height="20" rx="6" fill="{GREEN}" stroke="{INK}" stroke-width="2.4"/>')
        e.append(f'<path d="M108 34 L108 46 M108 34 L116 32" stroke="{INK}" stroke-width="2.4" fill="none"/><circle cx="105" cy="47" r="3.5" fill="{INK}"/>')
    if kind=="think":
        for (x,y,r) in ((92,56,3),(100,44,4.5),(110,30,6.5)): e.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="#fff" stroke="{INK}" stroke-width="2"/>')
    return e
os.makedirs("melt",exist_ok=True)
for k in ["ask","happy","surprised","sleepy","love","listen","think"]:
    open(f"melt/cat_{k}.svg","w").write(sv(BODY, COMMON+face(k)+extras(k)))
print("ok")
