# 암기냥이 (暗記にゃんこ) — 32x32 ドット。輪郭→白いステッカー縁の順に自動で付ける
from PIL import Image
N = 32
INK=(29,43,39,255); FUR=(247,242,232,255); SHADE=(226,216,199,255); PINK=(240,143,168,255)
GREEN=(0,105,69,255); GREEN2=(47,138,95,255); CREAM=(255,241,176,255); WHITE=(255,255,255,255); NONE=(0,0,0,0)
RED=(217,70,90,255); BLUE=(120,190,230,255)

def blank(): return [[NONE]*N for _ in range(N)]
def put(g,x,y,c):
    if 0<=x<N and 0<=y<N: g[y][x]=c
def ellipse(g,cx,cy,rx,ry,c):
    for y in range(N):
        for x in range(N):
            if ((x+.5-cx)/rx)**2+((y+.5-cy)/ry)**2<=1: g[y][x]=c
def tri(g,pts,c):
    (x1,y1),(x2,y2),(x3,y3)=pts
    def s(ax,ay,bx,by,px,py): return (px-bx)*(ay-by)-(ax-bx)*(py-by)
    for y in range(N):
        for x in range(N):
            px,py=x+.5,y+.5
            d1=s(px,py,x1,y1,x2,y2); d2=s(px,py,x2,y2,x3,y3); d3=s(px,py,x3,y3,x1,y1)
            if not ((d1<0 or d2<0 or d3<0) and (d1>0 or d2>0 or d3>0)): g[y][x]=c
def rect(g,x0,y0,x1,y1,c):
    for y in range(y0,y1+1):
        for x in range(x0,x1+1): put(g,x,y,c)

def base(g, tail=True):
    # しっぽ（右下からくるっと）
    if tail:
        for (x,y) in [(24,26),(25,25),(26,24),(26,23),(27,22),(27,21),(26,20),(25,20)]:
            ellipse(g,x+.5,y+.5,1.3,1.3,FUR)
    ellipse(g,16,25,6.2,5.2,FUR)             # からだ
    ellipse(g,16,27.5,5.2,2.6,SHADE)          # からだの影
    tri(g,[(6.5,12),(9.5,3.5),(13.5,9)],FUR)  # 左耳
    tri(g,[(18.5,9),(22.5,3.5),(25.5,12)],FUR) # 右耳
    tri(g,[(8.6,10),(9.8,6),(11.8,8.8)],PINK)
    tri(g,[(20.2,8.8),(22.2,6),(23.4,10)],PINK)
    ellipse(g,16,15,10.2,7.6,FUR)            # 頭
    ellipse(g,16,20.5,7,2,SHADE)             # あごの影
    rect(g,11,21,20,21,GREEN); rect(g,12,22,19,22,GREEN)  # 深緑のスカーフ
    put(g,18,23,GREEN); put(g,19,23,GREEN2)
    ellipse(g,12.5,29.3,1.8,1.1,FUR); ellipse(g,19.5,29.3,1.8,1.1,FUR)  # 足

def face(g, kind):
    cy=15
    if kind in ("ask","listen","think"):
        rect(g,11,cy-1,12,cy,INK); rect(g,19,cy-1,20,cy,INK); put(g,11,cy-1,WHITE); put(g,19,cy-1,WHITE)
    elif kind=="happy":
        for x,y in [(10,cy),(11,cy-1),(12,cy-1),(13,cy)]: put(g,x,y,INK)
        for x,y in [(18,cy),(19,cy-1),(20,cy-1),(21,cy)]: put(g,x,y,INK)
    elif kind=="surprised":
        rect(g,10,cy-2,13,cy+1,WHITE); rect(g,18,cy-2,21,cy+1,WHITE)
        rect(g,11,cy-1,12,cy,INK); rect(g,19,cy-1,20,cy,INK)
        for x in range(10,14): put(g,x,cy-2,INK); put(g,x,cy+1,INK)
        for x in range(18,22): put(g,x,cy-2,INK); put(g,x,cy+1,INK)
        for y in range(cy-1,cy+1): put(g,9,y,INK); put(g,14,y,INK); put(g,17,y,INK); put(g,22,y,INK)
    elif kind=="sleepy":
        rect(g,10,cy,13,cy,INK); rect(g,18,cy,21,cy,INK)
    elif kind=="love":
        for ox in (10,18):
            for x,y in [(0,0),(2,0),(0,1),(1,1),(2,1),(1,2)]: put(g,ox+x,cy-1+y,PINK)
            put(g,ox+1,cy-1,PINK)
    # ほっぺ
    if kind!="sleepy":
        put(g,9,cy+2,PINK); put(g,22,cy+2,PINK)
    # 鼻と口
    put(g,15,cy+2,PINK); put(g,16,cy+2,PINK)
    if kind in ("happy","love"):
        rect(g,14,cy+3,17,cy+4,INK); rect(g,15,cy+4,16,cy+4,RED)
    elif kind=="surprised":
        rect(g,15,cy+4,16,cy+5,INK)
    else:
        put(g,14,cy+3,INK); put(g,15,cy+4,INK); put(g,16,cy+4,INK); put(g,17,cy+3,INK)
    # ひげ
    for y in (cy+1,cy+3):
        put(g,4,y,INK); put(g,5,y,INK); put(g,26,y,INK); put(g,27,y,INK)

def card(g, mark):
    # 前足で持つ単語カード（深緑のふち・クリーム色の紙）
    rect(g,20,17,28,25,GREEN); rect(g,21,18,27,24,CREAM)
    if mark=="?":
        for x,y in [(23,19),(24,19),(25,19),(25,20),(24,21),(24,23)]: put(g,x,y,GREEN)
    elif mark=="!":
        for y in (19,20,21): put(g,24,y,GREEN)
        put(g,24,23,GREEN)
    elif mark=="lines":
        rect(g,22,19,26,19,GREEN2); rect(g,22,21,25,21,GREEN2); rect(g,22,23,26,23,GREEN2)
    ellipse(g,21,23.5,1.6,1.4,FUR)  # 前足

def extras(g, kind):
    if kind=="sleepy":
        for x,y in [(25,3),(26,3),(27,3),(26,4),(25,5),(26,5),(27,5)]: put(g,x,y,BLUE)
        for x,y in [(28,0),(29,0),(29,1),(28,2),(29,2)]: put(g,x,y,BLUE)
    if kind=="love":
        for x,y in [(25,2),(27,2),(24,3),(25,3),(26,3),(27,3),(28,3),(25,4),(26,4),(27,4),(26,5)]: put(g,x,y,PINK)
    if kind=="happy":
        for x,y in [(27,4),(26,5),(27,5),(28,5),(27,6),(4,6),(3,7),(4,7),(5,7),(4,8)]: put(g,x,y,CREAM)
    if kind=="surprised":
        for x,y in [(25,6),(25,7),(24,8),(25,8),(26,8),(25,9)]: put(g,x,y,BLUE)
    if kind=="listen":
        # ヘッドホン（深緑）
        for x in range(8,24): put(g,x,6 if 11<=x<=20 else 7,GREEN)
        for x,y in [(7,8),(7,9),(24,8),(24,9)]: put(g,x,y,GREEN)
        rect(g,5,11,7,16,GREEN); rect(g,24,11,26,16,GREEN)
        put(g,6,12,GREEN2); put(g,25,12,GREEN2)
        for x,y in [(28,8),(29,7),(29,9)]: put(g,x,y,INK)
    if kind=="think":
        for x,y in [(26,5),(28,3),(29,3),(28,2),(30,1)]: put(g,x,y,INK)

def outline(g):
    out=[row[:] for row in g]
    for y in range(N):
        for x in range(N):
            if g[y][x]==NONE:
                for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)):
                    xx,yy=x+dx,y+dy
                    if 0<=xx<N and 0<=yy<N and g[yy][xx] not in (NONE,) and g[yy][xx]!=INK:
                        out[y][x]=INK; break
    return out
def sticker(g):
    out=[row[:] for row in g]
    for y in range(N):
        for x in range(N):
            if g[y][x]==NONE and any(0<=x+dx<N and 0<=y+dy<N and g[y+dy][x+dx]!=NONE for dx,dy in ((1,0),(-1,0),(0,1),(0,-1))):
                out[y][x]=WHITE
    return out

def make(kind):
    g=blank(); base(g)
    if kind=="ask": card(g,"?")
    if kind=="surprised": card(g,"!")
    if kind=="think": card(g,"lines")
    face(g,kind)
    g=outline(g); extras(g,kind); g=sticker(g)
    return g

def save(g,name,sc=4):
    im=Image.new("RGBA",(N,N)); im.putdata([c for row in g for c in row])
    im.resize((N*sc,N*sc),Image.NEAREST).save(name)

KINDS=["ask","happy","surprised","sleepy","love","listen","think"]
import os; os.makedirs("out",exist_ok=True)
for k in KINDS: save(make(k),f"out/cat_{k}.png")
# 一覧（セージ・白・ダーク の3つの背景で 64px の実寸と 128px）
sheet=Image.new("RGBA",(len(KINDS)*140+20, 3*150+20),(255,255,255,255))
bgs=[(105,167,149,255),(255,255,255,255),(19,48,42,255)]
for r,bg in enumerate(bgs):
    for i,k in enumerate(KINDS):
        tile=Image.new("RGBA",(130,140),bg)
        im=Image.open(f"out/cat_{k}.png")
        tile.alpha_composite(im,(1,6))
        sheet.paste(tile,(10+i*140,10+r*150))
sheet.save("out/sheet.png")
print("ok")
