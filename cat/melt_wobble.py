# 암기냥이 F_melt — 出렁出렁(ぷるぷる)を強調した版。SVG内アニメ（imgでも動く）
import re
src=open("melt_cat.py").read().split('os.makedirs("melt"')[0]
exec(src)
BASE ="M4 112 C4 100 14 96 22 96 C24 80 34 60 64 60 C94 60 104 80 106 96 C114 96 124 100 124 112 C124 118 116 120 64 120 C12 120 4 118 4 112 Z"
# 左に寄る / 右に寄る（頭はそのまま、溶けた裾だけが波打つ）
LEFT ="M-4 111 C-5 98 10 93 21 95 C24 80 34 60 64 60 C94 60 104 80 107 97 C114 98 120 102 120 112 C120 118 112 120 60 120 C6 120 -4 117 -4 111 Z"
RIGHT="M8 112 C8 102 16 98 21 97 C24 80 34 60 64 60 C94 60 104 80 107 95 C118 93 133 98 132 111 C132 117 122 120 68 120 C16 120 8 118 8 112 Z"
BODY[0]=(P,f'd="{BASE}"',FUR)
# 耳: 先に描いて体の後ろへ → 肉に埋もれる。低く小さく
BODY[:]=[(P,'d="M44 72 L43 57 L56 66 Z"',FUR),(P,'d="M84 72 L85 57 L72 66 Z"',FUR),BODY[0]]
# 目印（目印の線・ほっぺ・耳の中・マフラー）を作り直し。マフラーは無し
COMMON=[f'<path d="M45.5 66 L45 60.5 L50 64 Z" fill="{PINK}"/>',f'<path d="M82.5 66 L83 60.5 L78 64 Z" fill="{PINK}"/>',
        f'<path d="M8 114 C40 120 88 120 120 114" fill="none" stroke="{SHADE}" stroke-width="4"/>',
        f'<circle cx="112" cy="104" r="3" fill="#fff" opacity=".8"/>']
def blush(L,R_,y,c=None):   # 漫画っぽい斜線ほっぺ ///
    return [f'<path d="M{x-5} {y+2.5} l2.6 -5 M{x-1} {y+2.5} l2.6 -5 M{x+3} {y+2.5} l2.6 -5" stroke="#e8798f" stroke-width="1.8" fill="none"/>' for x in (L,R_)]
def omega(cx,y,w=6):        # 3を寝かせた猫口 ω、両端は上にくるん
    w=w+1.5
    return f'<path d="M{cx-w-2.5} {y-2.5} Q{cx-w-1.5} {y+1} {cx-w/2} {y+3.2} Q{cx-.6} {y+4.4} {cx} {y} Q{cx+.6} {y+4.4} {cx+w/2} {y+3.2} Q{cx+w+1.5} {y+1} {cx+w+2.5} {y-2.5}" fill="none" stroke="{INK}" stroke-width="2.4"/>'
def whiskers():
    w=[]
    for sx,x0 in ((-1,38),(1,90)):
        for dy,ang in ((-3,-4),(1.5,0),(6,4)):
            w.append(f'<path d="M{x0} {84+dy} q{sx*9} {ang*.4} {sx*17} {ang}" fill="none" stroke="{INK}" stroke-width="1.7" opacity=".8"/>')
    return w
# 短すぎて役に立たない手（高速パタパタ）
def hands():
    h=[]
    for x,sgn,ph in ((25,-1,"0s"),(103,1,"-.07s")):
        h.append(f'<g transform="translate({x} 93)"><g><animateTransform attributeName="transform" type="rotate" dur=".16s" begin="{ph}" repeatCount="indefinite" values="{sgn*-35};{sgn*40};{sgn*-35}"/>'
                 f'<ellipse cx="{sgn*5}" cy="0" rx="5" ry="3.3" fill="{FUR}" stroke="#fff" stroke-width="6"/>'
                 f'<ellipse cx="{sgn*5}" cy="0" rx="5" ry="3.3" fill="{FUR}" stroke="{INK}" stroke-width="2.6"/>'
                 '</g></g>')
    return h
DUR="1.8s"
ANIM_D=f'<animate attributeName="d" dur="{DUR}" repeatCount="indefinite" calcMode="spline" keyTimes="0;.25;.5;.75;1" keySplines=".45 0 .55 1;.45 0 .55 1;.45 0 .55 1;.45 0 .55 1" values="{BASE};{LEFT};{BASE};{RIGHT};{BASE}"/>'
JELLY=(f'<animateTransform attributeName="transform" type="scale" dur="{DUR}" repeatCount="indefinite" calcMode="spline" '
       'keyTimes="0;.12;.25;.37;.5;.62;.75;.87;1" keySplines="'+";".join([".45 0 .55 1"]*8)+'" '
       'values="1 1;1.13 .85;.95 1.07;1.03 .97;1 1;1.13 .85;.95 1.07;1.03 .97;1 1"/>')
# 裾のしずく（ぷるん、と遅れて揺れる）
def drips():
    return [f'<g><ellipse cx="14" cy="117" rx="7" ry="4.5" fill="{FUR}" stroke="{INK}" stroke-width="3"><animate attributeName="rx" dur="{DUR}" repeatCount="indefinite" values="7;9;6;7.5;7"/><animate attributeName="cx" dur="{DUR}" repeatCount="indefinite" values="14;9;14;17;14"/></ellipse></g>',
            f'<g><ellipse cx="114" cy="118" rx="5.5" ry="3.6" fill="{FUR}" stroke="{INK}" stroke-width="3"><animate attributeName="rx" dur="{DUR}" repeatCount="indefinite" values="5.5;4.5;6.5;8;5.5"/><animate attributeName="cx" dur="{DUR}" repeatCount="indefinite" values="114;111;114;120;114"/></ellipse></g>']
def build(k):
    s=sv(BODY, COMMON+whiskers()+face(k)+hands()+extras(k))
    # 胴体パス（白縁・黒線・塗りの3枚）に裾アニメ
    s=re.sub(r'(<path d="'+re.escape(BASE)+r'"[^>]*?)/>', lambda m: m.group(1)+'>'+ANIM_D+'</path>', s)
    # 全体を下端中央(64,120)基準でぷるぷる
    head,body=s.split('<g stroke-linejoin',1)
    body='<g stroke-linejoin'+body
    inner,tail=body.rsplit('</svg>',1)
    drip=''.join(drips())
    head=head.replace('viewBox="-6 -6 140 140"','viewBox="-16 18 160 118"').replace('width="128" height="128"','width="174" height="128"')
    return (head+f'<g transform="translate(64 121)"><g>{JELLY}<g transform="translate(-64 -121)">'+drip+inner+'</g></g></g></svg>')
for k in ["ask","happy","surprised","sleepy","love","listen","think"]:
    open(f"melt/cat_{k}.svg","w").write(build(k))
print(open("melt/cat_ask.svg").read().count("<animate"))
