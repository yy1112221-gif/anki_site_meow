# 암기냥이 v2 ドット版 — もちっとした丸いかたまり・ぼーっとした目
from PIL import Image
import os
N=32
INK=(29,43,39,255); FUR=(248,243,234,255); SHADE=(235,225,207,255); PINK=(242,161,180,255); BLUSH=(244,179,154,255)
PATCH=(217,194,160,255); GREEN=(0,105,69,255); GREEN2=(47,138,95,255); RED=(217,70,90,255); BLUE=(120,190,230,255); CREAM=(255,233,168,255); WHITE=(255,255,255,255); NONE=(0,0,0,0)
def blank(): return [[NONE]*N for _ in range(N)]
def put(g,x,y,c):
    if 0<=x<N and 0<=y<N: g[y][x]=c
def rect(g,x0,y0,x1,y1,c):
    for y in range(y0,y1+1):
        for x in range(x0,x1+1): put(g,x,y,c)
def ellipse(g,cx,cy,rx,ry,c):
    for y in range(N):
        for x in range(N):
            if ((x+.5-cx)/rx)**2+((y+.5-cy)/ry)**2<=1: g[y][x]=c
def base(g):
    for (x,y) in [(27,25),(28,24),(28,23),(28,22),(27,21)]: ellipse(g,x+.5,y+.5,1.2,1.2,FUR)   # しっぽ
    ellipse(g,16,20,12.6,10.4,FUR); rect(g,5,20,26,26,FUR); ellipse(g,16,26.5,11,3.2,FUR)       # まんじゅう型
    for x,y in [(6,8),(7,8),(6,9),(7,9),(8,9),(6,10),(7,10),(8,10),(9,10),(7,11),(8,11),(9,11),(10,11)]: put(g,x,y,FUR)
    for x,y in [(25,8),(24,8),(25,9),(24,9),(23,9),(25,10),(24,10),(23,10),(22,10),(24,11),(23,11),(22,11),(21,11)]: put(g,x,y,FUR)
    put(g,7,9,PINK); put(g,7,10,PINK); put(g,8,10,PINK); put(g,24,9,PINK); put(g,24,10,PINK); put(g,23,10,PINK)
    for x,y in [(20,11),(21,12),(22,12),(23,12),(22,13),(23,13)]: put(g,x,y,PATCH)
    ellipse(g,16,27.6,9.5,1.8,SHADE)
    for x in range(9,23): put(g,x,25,GREEN)
    for x in range(10,22): put(g,x,26,GREEN)
    put(g,19,27,GREEN); put(g,20,27,GREEN2)
    ellipse(g,11.5,29.2,2,1.1,FUR); ellipse(g,20.5,29.2,2,1.1,FUR)
def derp_eye(g,x,y,pdx,lid=True,big=False):
    w=4 if not big else 5; h=3 if not big else 4
    rect(g,x,y,x+w-1,y+h-1,WHITE)
    put(g,x+1+pdx,y+h-1 if not big else y+1,INK); put(g,x+1+pdx,y+h-2 if not big else y+2,INK)
    if lid: rect(g,x,y,x+w-1,y,INK)
    for xx in range(x-1,x+w+1): put(g,xx,y-1 if not lid else y-1,NONE if g[y-1][xx]==INK else g[y-1][xx])
    put(g,x,y+h,INK); put(g,x+2,y+h,INK)   # 下まつげ
def face(g,kind):
    y=15
    if kind in ("ask","listen","think"):
        derp_eye(g,8,y,0); derp_eye(g,20,y,2)
        rect(g,15,y+5,16,y+6,INK)            # ぽかん口
    elif kind=="surprised":
        derp_eye(g,7,y-1,1,lid=False,big=True); derp_eye(g,20,y-1,1,lid=False,big=True)
        rect(g,15,y+5,16,y+7,INK)
    elif kind=="happy":
        for ox in (8,20):
            put(g,ox,y+1,INK); put(g,ox+1,y,INK); put(g,ox+2,y,INK); put(g,ox+3,y+1,INK)
        put(g,14,y+5,INK); put(g,15,y+6,INK); put(g,16,y+6,INK); put(g,17,y+5,INK); put(g,15,y+7,RED); put(g,16,y+7,RED)
    elif kind=="sleepy":
        rect(g,8,y+1,11,y+1,INK); rect(g,20,y+1,23,y+1,INK)
        put(g,14,y+5,INK); put(g,15,y+6,INK); put(g,16,y+6,INK); put(g,17,y+5,INK); put(g,18,y+7,BLUE)
    elif kind=="love":
        for ox in (8,20):
            for x,yy in [(0,0),(2,0),(0,1),(1,1),(2,1),(1,2)]: put(g,ox+x,y+yy,RED)
        put(g,14,y+5,INK); put(g,15,y+6,INK); put(g,16,y+6,INK); put(g,17,y+5,INK)
    put(g,15,y+4,PINK); put(g,16,y+4,PINK)
    for x in (6,7): put(g,x,y+4,BLUSH)
    for x in (24,25): put(g,x,y+4,BLUSH)
def outline(g):
    out=[r[:] for r in g]
    for y in range(N):
        for x in range(N):
            if g[y][x]==NONE and any(0<=x+dx<N and 0<=y+dy<N and g[y+dy][x+dx] not in (NONE,INK) for dx,dy in ((1,0),(-1,0),(0,1),(0,-1))): out[y][x]=INK
    return out
def sticker(g):
    out=[r[:] for r in g]
    for y in range(N):
        for x in range(N):
            if g[y][x]==NONE and any(0<=x+dx<N and 0<=y+dy<N and g[y+dy][x+dx]!=NONE for dx,dy in ((1,0),(-1,0),(0,1),(0,-1))): out[y][x]=WHITE
    return out
def extras(g,kind):
    if kind=="ask":
        for x,y in [(26,1),(27,1),(28,1),(28,2),(27,3),(27,5)]: put(g,x,y,GREEN)
    if kind=="surprised":
        for y in (1,2,3): put(g,27,y,GREEN)
        put(g,27,5,GREEN)
        for x,y in [(4,12),(4,13),(3,14),(4,14),(5,14)]: put(g,x,y,BLUE)
    if kind=="sleepy":
        for x,y in [(25,3),(26,3),(27,3),(26,4),(25,5),(26,5),(27,5),(28,0),(29,0),(29,1),(28,2),(29,2)]: put(g,x,y,BLUE)
    if kind=="love":
        for x,y in [(25,2),(27,2),(24,3),(25,3),(26,3),(27,3),(28,3),(25,4),(26,4),(27,4),(26,5)]: put(g,x,y,RED)
    if kind=="happy":
        for x,y in [(27,3),(26,4),(27,4),(28,4),(27,5),(3,8),(2,9),(3,9),(4,9),(3,10)]: put(g,x,y,CREAM)
    if kind=="listen":
        for x in range(8,24): put(g,x,7 if 10<=x<=21 else 8,GREEN)
        rect(g,3,14,5,20,GREEN); rect(g,26,14,28,20,GREEN); put(g,4,15,GREEN2); put(g,27,15,GREEN2)
        for x,y in [(28,3),(29,2),(29,4)]: put(g,x,y,INK)
    if kind=="think":
        for x,y in [(26,6),(28,4),(29,4),(28,3),(30,1),(31,1),(30,2)]: put(g,x,y,INK)
def make(kind):
    g=blank(); base(g); face(g,kind); g=outline(g); extras(g,kind); return sticker(g)
os.makedirs("dot2",exist_ok=True)
for k in ["ask","happy","surprised","sleepy","love","listen","think"]:
    g=make(k); im=Image.new("RGBA",(N,N)); im.putdata([c for r in g for c in r]); im.resize((128,128),Image.NEAREST).save(f"dot2/cat_{k}.png")
print("ok")
