# 암기냥이 — とろける体 ＋ 最初の猫の顔・耳・ひげ・スカーフ・単語カード
import os
exec(open("variations.py").read().split("V={}")[0])
RED="#d9465a"; BLUE="#78bee6"; CREAM="#fff1b0"
BODY=[(P,'d="M4 112 C4 100 14 95 22 95 C22 72 38 52 64 52 C90 52 106 72 106 95 C114 95 124 100 124 112 C124 118 116 121 64 121 C12 121 4 118 4 112 Z"',FUR),
      (P,'d="M28 70 L32 34 Q34 28 39 32 L56 54 Z"',FUR),(P,'d="M100 70 L96 34 Q94 28 89 32 L72 54 Z"',FUR)]
COMMON=[f'<path d="M35 62 L37 41 Q38 38 40 40 L50 53 Z" fill="{PINK}"/>',f'<path d="M93 62 L91 41 Q90 38 88 40 L78 53 Z" fill="{PINK}"/>',
        f'<path d="M8 114 C40 121 88 121 120 114" fill="none" stroke="{SHADE}" stroke-width="4"/>',
        f'<path d="M30 100 Q64 110 98 100 L98 106 Q64 116 30 106 Z" fill="{GREEN}"/>',
        f'<path d="M80 106 L86 118 L76 115 Z" fill="{GREEN2}"/>']
st='stroke="#fff" stroke-width="4" paint-order="stroke"'
def card(mark):
    c=[f'<g transform="rotate(-8 104 92)"><rect x="90" y="74" width="30" height="32" rx="6" fill="{GREEN}" stroke="{INK}" stroke-width="3"/><rect x="94" y="78" width="22" height="24" rx="3" fill="{CREAM}"/>']
    if mark in "?!": c.append(f'<text x="105" y="97" text-anchor="middle" font-family="Arial Rounded MT Bold,Arial,sans-serif" font-weight="900" font-size="20" fill="{GREEN}">{mark}</text>')
    else: c+= [f'<rect x="97" y="{y}" width="{w}" height="3" rx="1.5" fill="{GREEN2}"/>' for y,w in ((83,15),(89,11),(95,15))]
    c.append('</g>'); c.append(f'<ellipse cx="94" cy="100" rx="7" ry="5.5" fill="{FUR}" stroke="{INK}" stroke-width="3"/>')
    return c
def face(kind):
    L,R_,y=50,78,76; f=[]
    if kind in ("ask","think","listen"):
        f+=[f'<ellipse cx="{x}" cy="{y}" rx="4" ry="5" fill="{INK}"/><circle cx="{x+1.5}" cy="{y-1.8}" r="1.5" fill="#fff"/>' for x in (L,R_)]
    elif kind=="happy": f+=[f'<path d="M{x-5} {y+2} Q{x} {y-4.5} {x+5} {y+2}" fill="none" stroke="{INK}" stroke-width="3"/>' for x in (L,R_)]
    elif kind=="surprised": f+=[f'<circle cx="{x}" cy="{y}" r="6.5" fill="#fff" stroke="{INK}" stroke-width="2.4"/><circle cx="{x}" cy="{y}" r="3" fill="{INK}"/>' for x in (L-1,R_+1)]
    elif kind=="sleepy": f+=[f'<path d="M{x-5} {y} Q{x} {y+3} {x+5} {y}" fill="none" stroke="{INK}" stroke-width="3"/>' for x in (L,R_)]
    elif kind=="love": f+=[f'<path d="M{x} {y+4.5} C{x-7} {y} {x-4.5} {y-5.5} {x} {y-2} C{x+4.5} {y-5.5} {x+7} {y} {x} {y+4.5} Z" fill="{RED}"/>' for x in (L,R_)]
    f+=[f'<ellipse cx="{x}" cy="{y+9}" rx="5.5" ry="3.2" fill="{PINK}" opacity=".55"/>' for x in (39,89)]
    f.append(f'<path d="M60.5 {y+5} L67.5 {y+5} L64 {y+8.5} Z" fill="{PINK}" stroke="{PINK}" stroke-width="1.4"/>')
    if kind=="surprised": f.append(f'<ellipse cx="64" cy="{y+14}" rx="3.2" ry="4" fill="{INK}"/>')
    elif kind in ("happy","love"): f.append(f'<path d="M57 {y+11} Q64 {y+21} 71 {y+11} Z" fill="{RED}" stroke="{INK}" stroke-width="2.4"/>')
    else: f.append(f'<path d="M57 {y+11} Q60.5 {y+15} 64 {y+11} Q67.5 {y+15} 71 {y+11}" fill="none" stroke="{INK}" stroke-width="2.4"/>')
    for yy,dy in ((y+6,-3),(y+11,3)):   # ひげ
        f.append(f'<path d="M14 {yy+dy} L28 {yy}" stroke="{INK}" stroke-width="2.2"/><path d="M114 {yy+dy} L100 {yy}" stroke="{INK}" stroke-width="2.2"/>')
    return f
def extras(kind):
    e=[]
    if kind=="sleepy": e.append(f'<text x="98" y="44" font-family="Arial,sans-serif" font-weight="900" font-size="18" fill="{BLUE}" {st}>z</text><text x="110" y="30" font-family="Arial,sans-serif" font-weight="900" font-size="12" fill="{BLUE}" {st}>z</text><circle cx="73" cy="92" r="4.5" fill="#dff1fb" stroke="{BLUE}" stroke-width="1.5"/>')
    if kind=="love": e.append(f'<path d="M108 40 C98 32 102 22 108 27 C114 22 118 32 108 40 Z" fill="{RED}" stroke="#fff" stroke-width="3" paint-order="stroke"/>')
    if kind=="happy":
        for (x,y,r) in ((110,40,6),(18,52,4.5),(114,86,3.5)): e.append(f'<path d="M{x} {y-r} Q{x} {y} {x+r} {y} Q{x} {y} {x} {y+r} Q{x} {y} {x-r} {y} Q{x} {y} {x} {y-r} Z" fill="{CREAM}" stroke="#fff" stroke-width="2.5" paint-order="stroke"/>')
    if kind=="surprised": e.append(f'<path d="M22 56 Q28 66 22 70 Q16 66 22 56 Z" fill="{BLUE}" stroke="#fff" stroke-width="2.5" paint-order="stroke"/>')
    if kind=="listen":
        e.append(f'<path d="M22 80 Q20 38 64 38 Q108 38 106 80" fill="none" stroke="{GREEN}" stroke-width="6.5" stroke-linecap="round"/>')
        e.append(f'<rect x="12" y="70" width="15" height="22" rx="7" fill="{GREEN}" stroke="{INK}" stroke-width="2.4"/><rect x="101" y="70" width="15" height="22" rx="7" fill="{GREEN}" stroke="{INK}" stroke-width="2.4"/>')
        e.append(f'<path d="M112 14 L112 26 M112 14 L120 12" stroke="{INK}" stroke-width="2.4" fill="none"/><circle cx="109" cy="27" r="3.5" fill="{INK}"/>')
    if kind=="think":
        for (x,y,r) in ((98,46,3),(106,34,4.5),(116,20,6.5)): e.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="#fff" stroke="{INK}" stroke-width="2"/>')
    return e
CARD={"ask":"?","surprised":"!","think":"lines"}
os.makedirs("mix",exist_ok=True)
for k in ["ask","happy","surprised","sleepy","love","listen","think"]:
    open(f"mix/cat_{k}.svg","w").write(sv(BODY, COMMON+face(k)+(card(CARD[k]) if k in CARD else [])+extras(k)))
print("ok")
