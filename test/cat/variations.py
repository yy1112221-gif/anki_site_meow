# 암기냥이 — まったく違う8つの方向性（なめらか版・ふつう顔）
INK="#1d2b27"; FUR="#f8f3ea"; SHADE="#ebe1cf"; PINK="#f2a1b4"; BLUSH="#f4b39a"; GREEN="#006945"; GREEN2="#2f8a5f"
GRAY="#9aa3a0"; ORANGE="#e9a15a"; BROWN="#8a6a4f"; BLACK="#23282a"; FELT="#efe6d6"
def sv(shapes, details, w=6.4):
    """shapes: [(tag, attrs_without_fill, fill)] — 白い縁 → 黒い輪郭 → 色 の順に重ねる"""
    out=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="-6 -6 140 140" width="128" height="128"><g stroke-linejoin="round" stroke-linecap="round">']
    for col,sw in (("#fff",w+12),(INK,w)):
        for tag,a,f in shapes:
            if f=="none": out.append(f'<{tag} {a} fill="none" stroke="{col}" stroke-width="{sw+10}"/>')
            else: out.append(f'<{tag} {a} fill="{col}" stroke="{col}" stroke-width="{sw}"/>')
    for tag,a,f in shapes:
        if f=="none": continue
        out.append(f'<{tag} {a} fill="{f}"/>')
    for tag,a,f in shapes:
        if f=="none": out.append(f'<{tag} {a} fill="none" stroke="{FUR if "data-c" not in a else a.split("data-c=")[1].split(chr(34))[1]}" stroke-width="10"/>')
    out+=details; out.append('</g></svg>'); return "\n".join(out)
P='path'; E='ellipse'; C='circle'; R='rect'
def eyes_dot(L,R_,y,r=3.4): return [f'<circle cx="{L}" cy="{y}" r="{r}" fill="{INK}"/>',f'<circle cx="{R_}" cy="{y}" r="{r}" fill="{INK}"/>']
def omega(cx,y,w=6): return f'<path d="M{cx-w} {y} Q{cx-w/2} {y+5} {cx} {y+1} Q{cx+w/2} {y+5} {cx+w} {y}" fill="none" stroke="{INK}" stroke-width="2.4"/>'
def blush(L,R_,y,c=BLUSH): return [f'<ellipse cx="{L}" cy="{y}" rx="6.5" ry="3.8" fill="{c}" opacity=".7"/>',f'<ellipse cx="{R_}" cy="{y}" rx="6.5" ry="3.8" fill="{c}" opacity=".7"/>']
V={}

# A 食パン猫: 横に長いパンの塊で寝そべる。真顔
V["A_loaf"]=sv([
  (P,'d="M10 96 C8 70 20 54 42 52 C46 40 56 34 64 34 C72 34 82 40 86 52 C108 54 120 70 118 96 C117 108 108 112 96 112 L32 112 C20 112 11 108 10 96 Z"',FUR),
  (P,'d="M44 52 L48 30 L58 40 Z"',FUR),(P,'d="M84 52 L80 30 L70 40 Z"',FUR),
  (P,'d="M116 98 C126 98 128 88 122 84" data-c="'+FUR+'"',"none")],
  [f'<path d="M48 48 L50 36 L55 42 Z" fill="{PINK}"/>',f'<path d="M80 48 L78 36 L73 42 Z" fill="{PINK}"/>',
   f'<path d="M14 100 C30 112 98 112 114 100 L114 106 C100 114 28 114 14 106 Z" fill="{SHADE}"/>',
   f'<path d="M50 62 L58 62 M70 62 L78 62" stroke="{INK}" stroke-width="3"/>',
   f'<path d="M60 72 L68 72" stroke="{INK}" stroke-width="2.4"/>', f'<ellipse cx="64" cy="67" rx="2.2" ry="1.6" fill="{PINK}"/>',
   f'<path d="M24 96 L40 96 M88 96 L104 96" stroke="{INK}" stroke-width="2.2" opacity=".5"/>',
   f'<path d="M40 80 Q64 90 88 80 L88 85 Q64 95 40 85 Z" fill="{GREEN}"/>'])

# B たまご型: 縦長でちょこんと立つ。大きな白目にちっちゃい黒目（ぎょろ）
V["B_egg"]=sv([
  (P,'d="M64 16 C92 16 108 46 108 76 C108 104 90 120 64 120 C38 120 20 104 20 76 C20 46 36 16 64 16 Z"',FUR),
  (P,'d="M34 36 L32 10 L52 22 Z"',FUR),(P,'d="M94 36 L96 10 L76 22 Z"',FUR),
  (E,'cx="50" cy="122" rx="8" ry="4"',FUR),(E,'cx="78" cy="122" rx="8" ry="4"',FUR)],
  [f'<path d="M36 30 L35 16 L46 24 Z" fill="{PINK}"/>',f'<path d="M92 30 L93 16 L82 24 Z" fill="{PINK}"/>',
   f'<circle cx="46" cy="58" r="13" fill="#fff" stroke="{INK}" stroke-width="2.4"/>',f'<circle cx="84" cy="56" r="11" fill="#fff" stroke="{INK}" stroke-width="2.4"/>',
   f'<circle cx="41" cy="62" r="3" fill="{INK}"/>',f'<circle cx="89" cy="52" r="2.6" fill="{INK}"/>',
   f'<ellipse cx="64" cy="78" rx="2.4" ry="1.7" fill="{PINK}"/>',f'<ellipse cx="65" cy="86" rx="3" ry="2.2" fill="{INK}"/>',
   f'<path d="M44 96 Q64 104 84 96" fill="none" stroke="{GREEN}" stroke-width="6"/>'])

# C ぬいぐるみ: フェルト地・ステッチの縁・刺しゅうの目とボタン鼻
V["C_plush"]=sv([
  (P,'d="M20 70 C20 42 40 30 64 30 C88 30 108 42 108 70 C108 100 92 118 64 118 C36 118 20 100 20 70 Z"',FELT),
  (P,'d="M26 46 L28 14 L50 32 Z"',FELT),(P,'d="M102 46 L100 14 L78 32 Z"',FELT)],
  [f'<path d="M24 70 C24 46 42 34 64 34 C86 34 104 46 104 70 C104 96 90 114 64 114 C38 114 24 96 24 70 Z" fill="none" stroke="{BROWN}" stroke-width="1.6" stroke-dasharray="3 4"/>',
   f'<path d="M32 38 L33 22 L44 32 Z" fill="{PINK}"/>',f'<path d="M96 38 L95 22 L84 32 Z" fill="{PINK}"/>',
   f'<path d="M40 62 L52 62 M46 56 L46 68" stroke="{INK}" stroke-width="2.6"/>',f'<path d="M76 62 L88 62 M82 56 L82 68" stroke="{INK}" stroke-width="2.6"/>',
   f'<circle cx="64" cy="76" r="4.5" fill="{BROWN}"/><circle cx="62.5" cy="74.5" r="1.2" fill="#fff"/>',
   f'<path d="M58 86 L64 82 L70 86" fill="none" stroke="{INK}" stroke-width="2.2"/>',
   f'<path d="M56 108 L72 98 M60 112 L74 104" stroke="{GREEN}" stroke-width="3"/>'] + blush(36,92,80,PINK))

# D ぶさかわ: 平たい大きい顔・たれ目・まつげ・大きな黒い鼻
V["D_busa"]=sv([
  (P,'d="M12 72 C12 44 34 30 64 30 C94 30 116 44 116 72 C116 100 96 116 64 116 C32 116 12 100 12 72 Z"',FUR),
  (P,'d="M24 48 L26 14 L50 34 Z"',FUR),(P,'d="M104 48 L102 14 L78 34 Z"',FUR)],
  [f'<path d="M30 40 L31 22 L44 33 Z" fill="{BLACK}"/>',f'<path d="M98 40 L97 22 L84 33 Z" fill="{BLACK}"/>',
   f'<ellipse cx="44" cy="62" rx="11" ry="8" fill="#fff" stroke="{INK}" stroke-width="2.4"/>',f'<ellipse cx="84" cy="62" rx="11" ry="8" fill="#fff" stroke="{INK}" stroke-width="2.4"/>',
   f'<circle cx="46" cy="63" r="3.6" fill="{INK}"/>',f'<circle cx="80" cy="64" r="3.6" fill="{INK}"/>',
   f'<path d="M33 60 Q44 54 55 60" fill="none" stroke="{INK}" stroke-width="2.6"/>',f'<path d="M73 60 Q84 54 95 60" fill="none" stroke="{INK}" stroke-width="2.6"/>',
   *[f'<path d="M{x} 70 L{x+dx} 76" stroke="{INK}" stroke-width="1.6"/>' for x,dx in ((38,-2),(44,0),(50,2),(78,-2),(84,0),(90,2))],
   *[f'<path d="M{x} 54 L{x+dx} 49" stroke="{INK}" stroke-width="1.6"/>' for x,dx in ((37,-2),(51,2),(77,-2),(91,2))],
   f'<ellipse cx="64" cy="86" rx="10" ry="7" fill="{BLACK}"/><ellipse cx="61" cy="84" rx="3" ry="1.6" fill="#fff" opacity=".6"/>',
   f'<path d="M58 98 Q64 102 70 98" fill="none" stroke="{INK}" stroke-width="2.2"/>'])

# E 黒猫シルエット: まっ黒に白い目だけ（・_・）
V["E_black"]=sv([
  (P,'d="M18 84 C16 56 36 38 64 38 C92 38 112 56 110 84 C109 106 92 118 64 118 C36 118 19 106 18 84 Z"',BLACK),
  (P,'d="M26 56 L28 18 L52 40 Z"',BLACK),(P,'d="M102 56 L100 18 L76 40 Z"',BLACK),
  (P,'d="M108 100 C126 96 126 72 116 62" data-c="'+BLACK+'"',"none")],
  [f'<ellipse cx="46" cy="74" rx="8" ry="9" fill="#fff"/>',f'<ellipse cx="82" cy="74" rx="8" ry="9" fill="#fff"/>',
   f'<circle cx="47" cy="76" r="3" fill="{BLACK}"/>',f'<circle cx="83" cy="76" r="3" fill="{BLACK}"/>',
   f'<path d="M60 92 L68 92" stroke="#fff" stroke-width="2.4"/>',
   f'<path d="M36 108 Q64 118 92 108" fill="none" stroke="{GREEN2}" stroke-width="5"/>'])

# F とろける猫: 床に溶けて広がる。目は上のほうにちょこん
V["F_melt"]=sv([
  (P,'d="M4 112 C4 100 14 96 22 96 C24 80 34 60 64 60 C94 60 104 80 106 96 C114 96 124 100 124 112 C124 118 116 120 64 120 C12 120 4 118 4 112 Z"',FUR),
  (P,'d="M40 70 L40 50 L54 62 Z"',FUR),(P,'d="M88 70 L88 50 L74 62 Z"',FUR)],
  [f'<path d="M43 64 L43 55 L50 61 Z" fill="{PINK}"/>',f'<path d="M85 64 L85 55 L78 61 Z" fill="{PINK}"/>',
   *eyes_dot(52,76,80,3), omega(64,88,4), *blush(44,84,88),
   f'<path d="M8 114 C40 120 88 120 120 114" fill="none" stroke="{SHADE}" stroke-width="4"/>',
   f'<circle cx="112" cy="104" r="3" fill="#fff" opacity=".8"/>'])

# G とうふ猫: 四角い箱型。表情は最小限
V["G_tofu"]=sv([
  (R,'x="20" y="40" width="88" height="78" rx="18"',FUR),
  (P,'d="M24 52 L30 22 L50 42 Z"',FUR),(P,'d="M104 52 L98 22 L78 42 Z"',FUR)],
  [f'<path d="M31 44 L34 30 L43 41 Z" fill="{PINK}"/>',f'<path d="M97 44 L94 30 L85 41 Z" fill="{PINK}"/>',
   f'<rect x="20" y="96" width="88" height="22" rx="0" fill="{SHADE}" opacity=".6"/>',
   *eyes_dot(48,80,72,3.2), omega(64,80,4), *blush(40,88,82),
   f'<rect x="20" y="92" width="88" height="7" fill="{GREEN}"/>'])

# H まる顔（ゆるキャラ風）: 顔だけの大きな丸、手足なし、片目つぶりでとぼける
V["H_ball"]=sv([
  (C,'cx="64" cy="72" r="46"',FUR),
  (P,'d="M28 44 L24 16 L50 32 Z"',FUR),(P,'d="M100 44 L104 16 L78 32 Z"',FUR)],
  [f'<path d="M31 38 L29 24 L42 32 Z" fill="{ORANGE}"/>',f'<path d="M97 38 L99 24 L86 32 Z" fill="{GRAY}"/>',
   f'<path d="M30 44 C38 34 52 32 60 36 C52 46 40 50 30 44 Z" fill="{ORANGE}" opacity=".85"/>',
   f'<circle cx="46" cy="70" r="3.6" fill="{INK}"/>',f'<path d="M76 70 L88 70" stroke="{INK}" stroke-width="3"/>',
   f'<path d="M58 84 Q64 90 70 84" fill="none" stroke="{INK}" stroke-width="2.4"/><path d="M66 87 Q68 94 72 90" fill="{PINK}" stroke="{INK}" stroke-width="1.6"/>',
   *blush(38,90,84), f'<ellipse cx="64" cy="79" rx="2.4" ry="1.7" fill="{PINK}"/>'])

import os
for k,v in V.items(): open(f"var/{k}.svg","w").write(v)
print(list(V))
