# R-1125-②-선물카드: 포장지 7종 캔버스 · 받는 화면 상자/봉투 · 옛 링크 w 값 · 글꼴 못 받을 때
import asyncio, json, sys, re, base64
from playwright.async_api import async_playwright
R=[]
def ok(n,c,i=""): R.append(c); print(("✅" if c else "❌"), n, "" if c else i)
B="http://localhost:8765/index.html"
WR=["pink","mint","cream","night","washi","sakura","hangul"]
def meta(ui="ko"): return {"setup":1,"tutAsked":1,"loginAsked":1,"days":{},"settings":{"ui":ui,"lang":"ja" if ui=="ko" else "ko","homePet":False}}
def enc(o): return base64.urlsafe_b64encode(json.dumps(o,ensure_ascii=False).encode()).decode().rstrip("=")
M80={"ko":"생일 진심으로 축하해! 올해도 맛있는 거 많이 먹고 행복하게 지내자. 늘 고마워 우리 또 만나서 놀자 꼭이야 약속해 정말 정말로","ja":"いつもありがとう！これからもよろしくね。また一緒にごはん行こうね、約束だよ。ずっとずっと友だちでいてね、本当に本当にありがとう"}
async def seed(pg, ui="ko", q=""):
  await pg.goto(B); await pg.evaluate("s=>localStorage.setItem('focus-vocab-v1', s)", json.dumps({"cards":{},"meta":meta(ui)}))
  await pg.goto(B+q); await pg.wait_for_timeout(1400)
async def main():
  async with async_playwright() as pw:
    b=await pw.chromium.launch()
    ctx=await b.new_context(viewport={"width":390,"height":844}); pg=await ctx.new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)))
    await ctx.route(re.compile(r"supabase\.co|tosspayments"), lambda r: r.abort())
    await seed(pg)
    ok("포장지 7종", await pg.evaluate("()=>window.__t.CARD_WRAP && Object.keys(window.__t.CARD_WRAP).join()")=="pink,mint,cream,night,washi,sakura,hangul")
    # 캔버스: 7 × ml ko/ja × to 유무 × bday/free, 80자 + 두 번째 언어
    bad=[]
    for w in WR:
      for ml in ["ko","ja"]:
        for to in ["","하나"]:
          for k in ["bday","free"]:
            o={"n":"미나","c":"surprised" if k=="free" else "love","w":w,"m":M80[ml][:80],"p":M80["ja" if ml=="ko" else "ko"][:80],"ml":ml,"pl":"ja" if ml=="ko" else "ko","to":to,"k":k}
            r=await pg.evaluate("""async o=>{const cv=await window.__t.cardCanvas(o); const g=cv.getContext('2d'); const d=g.getImageData(0,0,cv.width,cv.height).data; let n=0; for(let i=0;i<d.length;i+=4*97) if(d[i]+d[i+1]+d[i+2]<300) n++; return [cv.width,cv.height,n]}""", o)
            if r[0]!=1080 or r[1]!=1350 or r[2]<20: bad.append((w,ml,to,k,r))
    ok("7 포장지 × ko·ja × to × bday/free 카드 생성(글자 그려짐)", not bad, str(bad[:3]))
    # 냥이 그림: 무리별 B/A
    ok("템플릿 냥이 pink=B·cream=A·surprised→shock", await pg.evaluate("()=>{const c=window.__t.cardCat; return c('pink','love')=='cat/card/cat_b_love.png' && c('cream','happy')=='cat/card/cat_a_happy.png' && c('mint','surprised')=='cat/card/cat_b_shock.png'}"))
    # 그림 파일 26개 모두 열림
    miss=await pg.evaluate("""async()=>{const f=['pink.svg','mint.svg','cream.svg','night.svg','emboss.svg','box.svg','box_open.svg','env_closed.svg','env_open.svg','gift_icon.svg','phone_bg.svg','pen_heart.svg','grain.webp','washi.webp','sprig_a.webp','sprig_b.webp','seal_rose.webp','seal_gold.webp','cat_b_happy.png','cat_b_love.png','cat_b_shock.png','cat_b_jump.png','cat_a_happy.png','cat_a_love.png','cat_a_shock.png','cat_a_melt.png']; const out=[]; for(const x of f){ const r=await fetch('cat/card/'+x); if(!r.ok) out.push(x);} return out}""")
    ok("cat/card 그림 26개", not miss, str(miss))
    # 만들기 시트: 포장지 버튼 7개(귀여움 4·모던 3), 44px 이상, 바꾸면 템플릿 그림도 바뀜
    await pg.evaluate("()=>window.__t.cardMake(null,'bday')"); await pg.wait_for_timeout(700)
    ws=await pg.evaluate("()=>[...document.querySelectorAll('.cd-w')].map(b=>{const r=b.getBoundingClientRect(); return [b.dataset.w, r.width>=44&&r.height>=44, b.classList.contains('mod')]})")
    ok("포장지 버튼 7개·44px·모던 3", len(ws)==7 and all(x[1] for x in ws) and [x[0] for x in ws if x[2]]==["washi","sakura","hangul"], str(ws))
    await pg.click(".cd-w[data-w=cream]"); await pg.wait_for_timeout(300)
    ok("cream 고르면 템플릿 버튼이 A 냥이", await pg.evaluate("()=>[...document.querySelectorAll('.cd-t img')].every(i=>i.src.includes('cat_a_'))"))
    ok("만들기 시트 가로 넘침 없음", await pg.evaluate("()=>document.documentElement.scrollWidth<=innerWidth"))
    await pg.evaluate("()=>document.querySelector('.sheet .x').click()")
    # 옛 링크·이상한 w 값
    for w,exp in [("pink","pink"),("mint","mint"),("night","night"),("washi","washi"),("hangul","hangul"),("gold","pink"),("<x>","pink")]:
      await seed(pg,"ko","?g="+enc({"n":"ミナ","c":"love","w":w,"m":"ありがとう","ml":"ja","k":"free"}))
      got=await pg.evaluate("()=>{const l=window.__t.giftState().recv; const z=l.find(z=>z.o&&z.o.m=='ありがとう'); return z?z.o.w:null}")
      ok(f"링크 w={w} → {exp}", got==exp, str(got))
    # 받는 화면
    for vw,vh in [(390,844),(360,640)]:
      await pg.set_viewport_size({"width":vw,"height":vh})
      for w in ["pink","sakura"]:
        for ui in ["ko","ja"]:
          await seed(pg,ui,"?g="+enc({"n":"ミナ","c":"love","w":w,"m":"お誕生日おめでとう！","ml":"ja","p":"생일 축하해","pl":"ko","k":"bday","to":"하나"}))
          await pg.wait_for_timeout(500)
          tag=f"{vw} {w} {ui}"
          st=await pg.evaluate("()=>{const s=document.querySelector('.sheet.cdx'); const b=document.querySelector('#cdBox'); if(!s||!b) return null; const r=b.getBoundingClientRect(); return {mod:s.classList.contains('modern'), env:!!b.querySelector('.cdx-env'), box:!!b.querySelector('.cdx-bx'), scroll:s.scrollHeight>s.clientHeight+1, doc:document.documentElement.scrollHeight>innerHeight+1, vis:r.bottom<=innerHeight&&r.top>=0, hit:b.contains(document.elementFromPoint(r.left+r.width/2,r.top+r.height/2))}}")
          ok(f"{tag} 받는 화면 {'봉투' if w=='sakura' else '상자'}", bool(st) and st["mod"]==(w=="sakura") and (st["env"] if w=="sakura" else st["box"]), str(st))
          ok(f"{tag} 스크롤 없음·상자 보이고 누를 수 있음", bool(st) and not st["scroll"] and not st["doc"] and st["vis"] and st["hit"], str(st))
          if vw==390 and ui=="ko": await pg.screenshot(path=f"/tmp/t_card_{w}_closed.png")
          await pg.click("#cdBox", force=True); await pg.wait_for_timeout(1700)
          ok(f"{tag} 누르면 카드 열림", await pg.evaluate("()=>!!document.querySelector('#cdIn .cd-img') && !document.querySelector('#cdBox')"))
          if vw==360 and ui=="ja": await pg.screenshot(path=f"/tmp/t_card_{w}_open.png")
    # reduced-motion
    ctx2=await b.new_context(viewport={"width":390,"height":844}, reduced_motion="reduce"); p2=await ctx2.new_page(); p2.on("pageerror",lambda e:errs.append(str(e)))
    await ctx2.route(re.compile(r"supabase\.co|tosspayments"), lambda r: r.abort())
    await seed(p2,"ko","?g="+enc({"n":"ミナ","c":"love","w":"mint","m":"ありがとう","ml":"ja","k":"free"})); await p2.wait_for_timeout(500)
    ok("reduced-motion 상자 흔들림 없음", await p2.evaluate("()=>{const e=document.querySelector('.cdx-bx'), c=document.querySelector('.cdx-cat'); return !!e && getComputedStyle(e).animationName=='none' && getComputedStyle(c).animationName=='none'}"))
    # 글꼴 못 받을 때(네트워크 막음)
    ctx3=await b.new_context(viewport={"width":390,"height":844}); p3=await ctx3.new_page(); p3.on("pageerror",lambda e:errs.append(str(e)))
    await ctx3.route(re.compile(r"fonts\.(googleapis|gstatic)\.com|supabase\.co"), lambda r: r.abort())
    await seed(p3)
    r=await p3.evaluate("async()=>{const t0=performance.now(); const cv=await window.__t.cardCanvas({n:'미나',c:'love',w:'hangul',m:'고마워',ml:'ko',k:'bday',to:'하나'}); return [cv.width, performance.now()-t0]}")
    ok("글꼴 막혀도 카드 생성(3초 안)", r[0]==1080 and r[1]<3500, str(r))
    ok("페이지 오류 없음", not errs, str(errs[:3]))
    await b.close()
  print(f"{sum(R)}/{len(R)}"); sys.exit(0 if all(R) else 1)
asyncio.run(main())
