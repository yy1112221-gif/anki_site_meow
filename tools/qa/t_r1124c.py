# R-1124-검수단-일본어결제화면(R1-56-1·R1-56-2) + R-1124-루프-산간식만료안내(R1-56-4·R1-56-3)
import asyncio, json, re
from playwright.async_api import async_playwright
R=[]
def ok(n,c,i=""): R.append(c); print(("✅" if c else "❌"), n, "" if c else i)
HG=re.compile(r"[가-힣]")
def meta(ui, pet=None):
  m={"setup":1,"tutAsked":1,"loginAsked":1,"days":{},"settings":{"ui":ui,"lang":"es" if ui=="ko" else "ko","homePet":False},"stepv":1}
  if pet is not None: m["pet"]=pet
  return m
async def seed(pg, m, q=""):
  await pg.goto("http://localhost:8765/index.html")
  await pg.evaluate("s=>localStorage.setItem('focus-vocab-v1', s)", json.dumps({"cards":{},"meta":m}))
  await pg.goto("http://localhost:8765/index.html"+q); await pg.wait_for_timeout(1400)
async def main():
  async with async_playwright() as pw:
    b=await pw.chromium.launch()
    for vw,vh in [(360,640),(390,844)]:
      ctx=await b.new_context(viewport={"width":vw,"height":vh}); pg=await ctx.new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)))
      await ctx.route(re.compile(r"(tosspayments|supabase\.co)"), lambda r: r.abort())
      # ① ui ja ?buy=snk_s → 결제 시트 없음, 토스트에 한글·원 없음
      await seed(pg, meta("ja"), "?buy=snk_s"); await pg.wait_for_timeout(600)
      sh=await pg.evaluate("()=>[...document.querySelectorAll('.sup-ov')].map(e=>e.textContent).join('|')")
      ok(f"{vw} ja ?buy=snk_s 결제 시트 안 열림", await pg.evaluate("()=>!document.querySelector('#payGo')") and "원" not in sh, sh[:80])
      await pg.evaluate("()=>window.__t.payOpen('snk_s')"); tt=await pg.evaluate("()=>document.querySelector('#toast').textContent")
      ok(f"{vw} ja payOpen → 準備中 토스트(한글 0)", "準備中" in tt and not HG.search(tt), tt)
      ok(f"{vw} ja payOpen 시트 없음", await pg.evaluate("()=>!document.querySelector('#payGo')"))
      # ② ja 푸터·설정 상점 링크 없음
      f=await pg.evaluate("()=>window.__t.bizFootHTML()"); ok(f"{vw} ja 푸터 shop 링크 없음·한글 0", 'href="shop"' not in f and not HG.search(f), f)
      await pg.evaluate("()=>window.__t.showView('how')"); await pg.wait_for_timeout(300)
      sb=await pg.evaluate("()=>document.querySelector('#supBox').innerHTML"); ok(f"{vw} ja 설정 상점 버튼 없음", 'href="shop"' not in sb)
      # ③ ko 회귀: 푸터·설정 상점 링크, payOpen 시트 열림
      await seed(pg, meta("ko"))
      f=await pg.evaluate("()=>window.__t.bizFootHTML()"); ok(f"{vw} ko 푸터 shop 링크", 'href="shop"' in f and "상점" in f)
      await pg.evaluate("()=>window.__t.showView('how')"); await pg.wait_for_timeout(300)
      ok(f"{vw} ko 설정 상점 버튼", 'href="shop"' in await pg.evaluate("()=>document.querySelector('#supBox').innerHTML"))
      await pg.evaluate("()=>window.__t.showView('today')")
      await pg.evaluate("()=>window.__t.payOpen('snk_s')"); await pg.wait_for_timeout(300)
      t=await pg.evaluate("()=>{ const g=document.querySelector('#payGo'); return g?g.textContent:''; }"); ok(f"{vw} ko 결제 시트 열림(990원)", "990원" in t, t)
      ok(f"{vw} payWhat 아이콘 petIconHTML", await pg.evaluate("()=>document.querySelector('.pay-what .peti, .pay-what svg')!=null") and "🍪" not in await pg.evaluate("()=>document.querySelector('.pay-what').innerHTML"))
      await pg.evaluate("()=>document.querySelectorAll('.sup-ov').forEach(e=>e.remove())")
      # ④ 산 간식 기한 표시·만료 안내 (ko·ja)
      for ui in ("ko","ja"):
        await seed(pg, meta(ui, {"inv":{},"kcal":0,"lv":1,"granted":{},"seenTier":9}))
        await pg.evaluate("()=>window.__t.payGrant('snk_s','T1')")
        d=await pg.evaluate("()=>{ const p=window.__t.S().meta.pet; const id=p.buy[0].id; return [id, window.__t.buyDays(p,id), p.inv[id]]; }")
        ok(f"{vw} {ui} 산 간식 D-3", d[1]=="D-3", d)
        await pg.evaluate("()=>window.__t.openPet()"); await pg.wait_for_timeout(700)
        ok(f"{vw} {ui} 트레이 D 배지", await pg.evaluate("()=>[...document.querySelectorAll('.pw-d')].some(e=>e.textContent==='D-3')"))
        await pg.evaluate("()=>window.__t.closePet()")
        await pg.evaluate("()=>{ let b=document.querySelector('#shopBody'); if(!b){ b=document.createElement('div'); b.id='shopBody'; document.body.appendChild(b);} window.__t.renderShop(); }")
        ok(f"{vw} {ui} 상점 D 표시", await pg.evaluate("()=>[...document.querySelectorAll('#shopBody .shop-d')].some(e=>e.textContent==='D-3')"))
        await pg.evaluate("()=>{ const b=document.querySelector('#shopBody'); if(b && b.parentNode===document.body) b.remove(); }")
        bg0=await pg.evaluate("()=>(window.__t.S().meta.pet.bgone||[]).length")
        await pg.evaluate("()=>{ const p=window.__t.S().meta.pet; p.buy.forEach(l=>l.exp=Date.now()-1000); }")
        await pg.evaluate("()=>window.__t.openPet()"); await pg.wait_for_timeout(500)
        tt=await pg.evaluate("()=>document.querySelector('#toast').textContent")
        want = "산 간식 10개가 기한이 지나 사라졌다냥" if ui=="ko" else "買ったおやつ10個が期限切れで消えたニャ"
        ok(f"{vw} {ui} 만료 안내 한 번", tt==want, tt)
        st=await pg.evaluate("()=>{ const m=window.__t.S().meta; return [m.bxp||null, (m.pet.buy||[]).length, Object.values(m.pet.inv).reduce((a,b)=>a+b,0), (m.pet.bgone||[]).length]; }")
        ok(f"{vw} {ui} 만료: 묶음·inv 비움, bgone 늘어남, bxp 지움", st[0] is None and st[1]==0 and st[2]==0 and st[3]>bg0, st)
        await pg.evaluate("()=>{ window.__t.closePet(); document.querySelector('#toast').textContent=''; }")
        await pg.evaluate("()=>window.__t.openPet()"); await pg.wait_for_timeout(500)
        tt=await pg.evaluate("()=>document.querySelector('#toast').textContent"); ok(f"{vw} {ui} 두 번째 열기엔 안내 없음", "期限" not in tt and "기한" not in tt, tt)
        ok(f"{vw} {ui} 냥이 화면 스크롤 없음", await pg.evaluate("()=>document.documentElement.scrollHeight<=innerHeight+1"))
        if vw==390 and ui=="ja":
          await pg.evaluate("()=>{ window.__t.closePet(); window.__t.payGrant('snk_m','T2'); window.__t.openPet(); }"); await pg.wait_for_timeout(900)
          await pg.screenshot(path="/tmp/r1124c_tray.png")
        await pg.evaluate("()=>window.__t.closePet()")
      # ⑤ 저장된 데이터에 bxp가 동기화 대상 아님(MERGE_LOCAL)
      r=await pg.evaluate("()=>{ const m=window.__t.S().meta; delete m.bxp; window.__t.mergeData({cards:{},meta:{bxp:{n:5,at:1}}},{server:1}); return window.__t.S().meta.bxp||null; }")
      ok(f"{vw} 원격 bxp 안 받음", r is None, r)
      ok(f"{vw} 페이지 오류 없음", not errs, errs[:3])
      await ctx.close()
    await b.close()
  print(f"t_r1124c: {sum(R)}/{len(R)}")
  if not all(R): raise SystemExit(1)
asyncio.run(main())
