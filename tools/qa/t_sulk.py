# 백로그 S: 며칠 안 오면 냥이가 삐짐(마지막 접속 S.meta.seen 기준) — 단계·화 풀기·ω 입·한 화면·데이터 불변
import asyncio, json
from playwright.async_api import async_playwright
R=[]
def ok(n,c,i=""): R.append(c); print(("✅" if c else "❌"), n, "" if c else i)
def mk(n=14):
  return {f"d{i}":dict(id=f"d{i}",lang="es",word=f"pal{i}",meaning=f"뜻{i}",example="",level=2,due="2026-01-01",isNew=False,lapses=0,reps=3,created=i,introduced="2025-12-01",mastered=False,relearn=False,log=[],deck="default",step=2,S=3,D=5,last="2025-12-20") for i in range(n)}
async def seed(pg, extra=None, days=None, cards=None):
  meta={"setup":1,"tutAsked":1,"loginAsked":1,"days":days or {},"settings":{"ui":"ko","lang":"es","homePet":False},"stepv":1,"pet":{"inv":{"kari":5},"kcal":0,"lv":1,"granted":{},"seenTier":9}}
  if extra: meta.update(extra)
  await pg.evaluate("s=>localStorage.setItem('focus-vocab-v1', s)", json.dumps({"cards":cards if cards is not None else mk(),"meta":meta})); await pg.reload(); await pg.wait_for_timeout(1200)
async def ago(pg,n): return await pg.evaluate("n=>{ const d=new Date(); d.setDate(d.getDate()-n); return d.toLocaleDateString('sv-SE'); }", n)
async def sul(pg): return await pg.evaluate("()=>{ const s=window.__t.S().meta; return {sulk:s.sulk, seen:s.seen, today:window.__t.today()}; }")
async def main():
  async with async_playwright() as pw:
    b=await pw.chromium.launch(); pg=await b.new_page(viewport={"width":390,"height":844}); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)))
    await pg.goto("http://localhost:8765/index.html")
    for n,lv,need in [(1,0,0),(2,1,3),(4,2,6),(8,3,10)]:
      await seed(pg,{"seen":await ago(pg,n)}); r=await sul(pg)
      ok(f"seen {n}일 전 → lv{lv}", r["sulk"]["lv"]==lv and r["sulk"]["gap"]==n and r["sulk"]["need"]==need and r["seen"]==r["today"], r)
    await seed(pg,None,{await ago(pg,5):True, await ago(pg,9):True}); r=await sul(pg)
    ok("seen 없는 옛 데이터 → 마지막 공부일(5일 전) 기준 lv2", r["sulk"]["lv"]==2 and r["sulk"]["gap"]==5, r)
    await seed(pg,None,{},{}); r=await sul(pg); ok("데이터 없음 → lv0", r["sulk"]["lv"]==0 and r["sulk"]["done"]==1, r)
    # 다시 열어도 그날은 다시 안 정함
    await seed(pg,{"seen":await ago(pg,4)}); await pg.reload(); await pg.wait_for_timeout(1000); r=await sul(pg)
    ok("같은 날 다시 열어도 lv 그대로(seen이 오늘로 바뀌어도)", r["sulk"]["lv"]==2, r)
    # 홈 말풍선
    hb=await pg.evaluate("()=>[...document.querySelectorAll('#sessionStart .bubble')].map(b=>b.textContent).join('|')")
    ok("홈 말풍선 화남 문구", "화났다냥" in hb, hb)
    # 냥이 화면 열기 → 말풍선 → 쓰다듬기 need 번
    await pg.evaluate("()=>window.__t.openPet()"); await pg.wait_for_timeout(900)
    m=await pg.evaluate("()=>document.querySelector('#petMsg').textContent"); ok("냥이 화면 lv2 말풍선", "4일 동안 기다렸는데" in m, m)
    shown=await pg.evaluate("()=>window.__t.S().meta.sulk.sh"); ok("sulk_show 한 번 표시(sh=1)", shown==1)
    ev=await pg.evaluate("()=>{ const t=window.__t; for(let i=0;i<5;i++) t.sulkTouch(); return [t.sulkOn(), t.S().meta.sulk.c]; }"); ok("5번 쓰다듬기 → 아직 화남", ev==[True,5], ev)
    await pg.wait_for_timeout(300)
    m=await pg.evaluate("()=>document.querySelector('#petMsg').textContent")
    # 화난 동안 얼굴: ω 입 그리기 함수가 불림
    ev=await pg.evaluate("()=>{ const t=window.__t; t.sulkTouch(); return [t.sulkOn(), t.S().meta.sulk.done]; }"); ok("6번째 → 풀림 done=1", ev==[False,1], ev)
    await pg.wait_for_timeout(400); m=await pg.evaluate("()=>document.querySelector('#petMsg').textContent"); ok("풀림 문구", "매일 와라냥" in m, m)
    await pg.reload(); await pg.wait_for_timeout(1000); r=await sul(pg); ok("다시 열어도 그날은 안 화냄", r["sulk"]["done"]==1 and not await pg.evaluate("()=>window.__t.sulkOn()"), r)
    # 간식: lv2 첫 간식 튕김(돌려줌) → 둘째 간식에 풀림
    await seed(pg,{"seen":await ago(pg,4)})
    ev=await pg.evaluate("()=>{ const t=window.__t; return [t.sulkSnack({id:'kari'}), t.sulkOn(), t.sulkSnack({id:'kari'}), t.sulkOn()]; }"); ok("lv2: 첫 간식 튕김, 둘째 간식에 풀림", ev==[True,True,False,False], ev)
    await seed(pg,{"seen":await ago(pg,2)})
    ev=await pg.evaluate("()=>{ const t=window.__t; return [t.sulkSnack({id:'kari'}), t.sulkOn()]; }"); ok("lv1: 첫 간식에 바로 풀림", ev==[False,False], ev)
    # 실제 던지기 경로: 간식 개수 그대로(돌려줌)
    await seed(pg,{"seen":await ago(pg,9)})
    await pg.evaluate("()=>window.__t.openPet()"); await pg.wait_for_timeout(2600)
    m=await pg.evaluate("()=>document.querySelector('#petMsg').textContent"); ok("lv3 말풍선 「9일이나…!」", "9일이나" in m, m)
    flt=await pg.evaluate("()=>document.querySelector('#petGL').style.filter"); ok("lv3 붉은 색조", "sepia" in flt, flt)
    # 실제로 간식 톡 던지기(lv3): 첫 간식은 튕겨 내고 개수는 돌려줌
    await seed(pg,{"seen":await ago(pg,9)}); await pg.evaluate("()=>window.__t.openPet()"); await pg.wait_for_timeout(1200)
    bx=await pg.evaluate("()=>{ const r=document.querySelector('.pw-it.sel').getBoundingClientRect(); return [r.x+r.width/2, r.y+r.height/2]; }")
    await pg.mouse.click(bx[0],bx[1]); await pg.wait_for_timeout(1500)
    ev=await pg.evaluate("()=>{ const t=window.__t, S=t.S(); return [S.meta.pet.inv.kari, S.meta.pet.kcal, t.sulkOn(), S.meta.sulk.sn]; }")
    ok("lv3 첫 간식 튕김: 간식 그대로 5개·kcal 0·아직 화남", ev==[5,0,True,1], ev)
    await pg.mouse.click(bx[0],bx[1]); await pg.wait_for_timeout(1500)
    ev=await pg.evaluate("()=>{ const t=window.__t, S=t.S(); return [S.meta.pet.inv.kari, S.meta.pet.kcal>0, t.sulkOn()]; }")
    ok("둘째 간식은 받아먹고 풀림", ev==[4,True,False], ev)
    # 입은 어떤 단계든 ω: drawCatFace0 안에서 omegaMouth를 조건 없이 부름(앞에 return 없음)
    import re
    src=open("index.html",encoding="utf-8").read(); body=src[src.index("function drawCatFace0("):]; body=body[:body.index("\nfunction ")]
    pre=body[:body.index("omegaMouth(g, my")]
    ok("화난 얼굴도 ω 입(omegaMouth 무조건 호출)", "omegaMouth(g, my, mw, sq, open, tongue, tongueOut);" in body and "return" not in pre and "sulkLv()" in pre)
    # 한 판 끝내면 풀림
    ev=await pg.evaluate("""async()=>{ const t=window.__t; document.querySelector('#petClose').click(); await new Promise(r=>setTimeout(r,300)); t.setSES(null); t.startSession(); const s=t.getSES(); let g=0; while(s.queue.length && g++<80) t.settleItem(true); await new Promise(r=>setTimeout(r,500)); return [!!(s.course), t.sulkOn(), t.S().meta.sulk.done]; }""")
    ok("한 판 끝내면 풀림", ev[1]==False and ev[2]==1, ev)
    # 화면: 390·360 냥이 화면 스크롤 없음
    for w,h in [(390,844),(360,640)]:
      await pg.set_viewport_size({"width":w,"height":h}); await seed(pg,{"seen":await ago(pg,0)})
      base=await pg.evaluate("()=>document.documentElement.scrollHeight-innerHeight")   # 같은 데이터·화남 없음 기준(뒤 홈 높이)
      await seed(pg,{"seen":await ago(pg,9)})
      await pg.evaluate("()=>window.__t.openPet()"); await pg.wait_for_timeout(1500)
      sc=await pg.evaluate("()=>{ const p=document.querySelector('#pet'), r=p.getBoundingClientRect(); return [document.documentElement.scrollHeight-innerHeight, p.scrollHeight-p.clientHeight, Math.round(r.bottom-innerHeight)]; }")
      ok(f"{w}×{h} 화난 냥이 화면 스크롤 없음(뒤 홈도 화남 없을 때와 같음)", sc[0]<=max(base,0) and sc[1]<=1 and sc[2]<=1, [base]+sc)
      await pg.screenshot(path=f"/tmp/sulk_{w}.png")
    # 데이터 불변: 카드·pet 기존 키
    await pg.set_viewport_size({"width":390,"height":844})
    cs=mk(); await seed(pg,{"seen":await ago(pg,4)},None,cs)
    r=await pg.evaluate("()=>{ const S=window.__t.S(); return [Object.keys(S.cards).length, S.meta.pet.inv.kari, S.meta.pet.kcal]; }"); ok("카드·pet 데이터 불변", r==[14,5,0], r)
    ok("페이지 오류 없음", not errs, errs)
    await b.close()
  print(f"t_sulk: {sum(R)}/{len(R)}"); raise SystemExit(0 if all(R) else 1)
asyncio.run(main())
