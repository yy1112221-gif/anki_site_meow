# R-1124-검수단-던지는중닫기(R1-55-1) + R-1124-루프-냥이화면문구: 날아가는 간식 되돌리기 · 냥이 화면 문구·배치
import asyncio, json
from playwright.async_api import async_playwright
R=[]
def ok(n,c,i=""): R.append(c); print(("✅" if c else "❌"), n, "" if c else i)
def mk(n=6):
  return {f"d{i}":dict(id=f"d{i}",lang="es",word=f"pal{i}",meaning=f"뜻{i}",example="",level=2,due="2026-01-01",isNew=False,lapses=0,reps=3,created=i,introduced="2025-12-01",mastered=False,relearn=False,log=[],deck="default",step=2,S=3,D=5,last="2025-12-20") for i in range(n)}
async def seed(pg, inv, ui="ko", buy=None):
  pet={"inv":inv,"kcal":0,"lv":1,"granted":{},"seenTier":9}
  if buy is not None: pet["buy"]=buy
  meta={"setup":1,"tutAsked":1,"loginAsked":1,"days":{},"settings":{"ui":ui,"lang":"es","homePet":False},"stepv":1,"pet":pet}
  for _ in range(3):   # 앞 단계 화면이 숨을 때 저장해 시드를 덮을 수 있음 → 확인하고 다시
    await pg.evaluate("s=>localStorage.setItem('focus-vocab-v1', s)", json.dumps({"cards":mk(),"meta":meta})); await pg.reload(); await pg.wait_for_timeout(1000)
    if await pg.evaluate("o=>{ const m=window.__t.S().meta; return m.settings.ui===o.ui && JSON.stringify(m.pet.inv)===JSON.stringify(o.inv); }", {"ui":ui,"inv":inv}): break
  await pg.evaluate("()=>{ const t=window.__t; if(!t.pet()) t.openPet(); }"); await pg.wait_for_timeout(700)
# 세게 위로(머리 넘어 빗나감) / 알맞게(명중) 던지기: pts를 직접 넣고 petRelease
FLICK = """(o)=>{ const t=window.__t, st=t.pet(); const el=document.querySelector('.pw-it.sel')||document.body; t.petGrab(o.id, el); const g=st.grab; const now=performance.now(), cx=st.W/2;
  g.pts=[{x:cx,y:st.H-120,t:now-o.dt},{x:cx,y:st.H-120-o.dy,t:now}]; t.petRelease(); return st.proj.map(q=>({hit:q.hit,lot:q.lot??null})); }"""
async def inv(pg, id): return await pg.evaluate("id=>{ const p=window.__t.S().meta.pet; return [p.inv[id]||0, (p.buy||[]).filter(l=>l.id===id).reduce((a,l)=>a+l.n,0), p.kcal]; }", id)
async def stored(pg, id): return await pg.evaluate("id=>{ const d=JSON.parse(localStorage.getItem('focus-vocab-v1')).meta.pet; return [d.inv[id]||0, (d.buy||[]).filter(l=>l.id===id).reduce((a,l)=>a+l.n,0)]; }", id)
async def main():
  async with async_playwright() as pw:
    b=await pw.chromium.launch()
    for vw,vh in [(360,640),(390,844)]:
      ctx=await b.new_context(viewport={"width":vw,"height":vh},has_touch=True); pg=await ctx.new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)))
      await pg.goto("http://localhost:8765/index.html")
      # ① 세게 던져 빗나가는 중 250ms 뒤 닫기 → 그대로 3
      await seed(pg,{"sushi":3})
      pr=await pg.evaluate(FLICK,{"id":"sushi","dt":30,"dy":220}); ok(f"{vw} 세게 던짐: 빗나가는 투사체", len(pr)==1 and not pr[0]["hit"], pr)
      ok(f"{vw} 던지는 순간 3→2", (await inv(pg,"sushi"))[0]==2)
      await pg.wait_for_timeout(250); await pg.click("#petClose"); await pg.wait_for_timeout(300)
      ok(f"{vw} 날아가는 중 닫기 → 🍣3 되돌림(저장도)", (await inv(pg,"sushi"))[0]==3 and (await stored(pg,"sushi"))[0]==3, [await inv(pg,"sushi"), await stored(pg,"sushi")])
      await pg.evaluate("()=>window.__t.openPet()"); await pg.wait_for_timeout(600)
      ok(f"{vw} 다시 열면 🍣3", (await inv(pg,"sushi"))[0]==3)
      # ② 평소 놓침: 끝까지 두면 3→3
      await seed(pg,{"sushi":3}); await pg.evaluate(FLICK,{"id":"sushi","dt":30,"dy":220}); await pg.wait_for_timeout(3200)
      ok(f"{vw} 놓침 끝까지 → 3", (await inv(pg,"sushi"))[0]==3, await inv(pg,"sushi"))
      m=await pg.evaluate("()=>document.querySelector('#petMsg').textContent"); ok(f"{vw} 놓침 말풍선 기본 문구", "빗나갔군" in m, m)
      # ③ 명중: 3→2 + kcal
      await seed(pg,{"sushi":3}); hits=None
      for dy in (60,50,70,45,80):
        pr=await pg.evaluate(FLICK,{"id":"sushi","dt":30,"dy":dy})
        if pr and pr[-1]["hit"]: hits=dy; break
      await pg.wait_for_timeout(1200); r=await inv(pg,"sushi")
      ok(f"{vw} 명중 던지기 → 줄고 kcal↑", hits is not None and r[0]==2 and r[2]>0, [hits, r])
      # ④ 톡 던지기(tap) 3→2, 날아가는 중 닫으면 되돌림
      await seed(pg,{"sushi":3})
      await pg.evaluate("()=>{ const el=document.querySelector('.pw-it.sel'); window.__t.petThrow('sushi', el); }"); await pg.wait_for_timeout(1000)
      r=await inv(pg,"sushi"); ok(f"{vw} 톡 던지기 3→2 + kcal", r[0]==2 and r[2]>0, r)
      await pg.evaluate("()=>{ const el=document.querySelector('.pw-it.sel'); window.__t.petThrow('sushi', el); }"); await pg.wait_for_timeout(120)
      await pg.click("#petClose"); await pg.wait_for_timeout(200)
      ok(f"{vw} 톡 던진 직후 닫기 → 2 그대로", (await inv(pg,"sushi"))[0]==2, await inv(pg,"sushi"))
      # ⑤ 산 간식: 빗나가는 중 닫기 → 묶음 n도 되돌림 / 놓침 끝까지도 묶음 n 되돌림
      far=1e13
      await seed(pg,{"sushi":2},buy=[{"id":"sushi","n":2,"exp":far}])
      pr=await pg.evaluate(FLICK,{"id":"sushi","dt":30,"dy":220}); ok(f"{vw} 산 간식 던지면 lot 기억", pr and pr[0]["lot"]==far, pr)
      ok(f"{vw} 산 간식 던짐 → inv1·묶음1", (await inv(pg,"sushi"))[:2]==[1,1])
      await pg.wait_for_timeout(250); await pg.click("#petClose"); await pg.wait_for_timeout(200)
      ok(f"{vw} 산 간식 닫기 → inv2·묶음2", (await inv(pg,"sushi"))[:2]==[2,2], await inv(pg,"sushi"))
      await pg.evaluate("()=>window.__t.openPet()"); await pg.wait_for_timeout(600)
      await pg.evaluate(FLICK,{"id":"sushi","dt":30,"dy":220}); await pg.wait_for_timeout(3200)
      ok(f"{vw} 산 간식 놓침 끝까지 → inv2·묶음2", (await inv(pg,"sushi"))[:2]==[2,2], await inv(pg,"sushi"))
      # ⑥ 숨김(visibilitychange)으로도 되돌림
      await seed(pg,{"sushi":3}); await pg.evaluate(FLICK,{"id":"sushi","dt":30,"dy":220}); await pg.wait_for_timeout(150)
      await pg.evaluate("()=>{ Object.defineProperty(document,'hidden',{configurable:true,get:()=>true}); document.dispatchEvent(new Event('visibilitychange')); delete document.hidden; }"); await pg.wait_for_timeout(200)
      ok(f"{vw} 화면 숨김 → 되돌림·저장", (await inv(pg,"sushi"))[0]==3 and (await stored(pg,"sushi"))[0]==3, [await inv(pg,"sushi"), await stored(pg,"sushi")])
      ok(f"{vw} 오류 없음", not errs, errs[:3]); await ctx.close()
    # 문구
    pg=await b.new_page(viewport={"width":390,"height":844}); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)))
    await pg.goto("http://localhost:8765/index.html")
    txt=await pg.evaluate("()=>JSON.stringify([window.__t.MELT(), Object.fromEntries(Object.entries(window.__t.PT()).map(([k,v])=>[k, Object.fromEntries(Object.entries(v).filter(([a,b])=>typeof b==='string'||Array.isArray(b)))]))])")
    ok("대사표에 꼬리·しっぽ 0", "꼬리" not in txt and "しっぽ" not in txt)
    ok("귀가 멋대로·耳が勝手に", "귀가 멋대로" in txt and "耳が勝手に" in txt)
    for ui,auto,zero in [("ko","톡 치면 자동으로 던져","쓰다듬어 봐"),("ja","タップで自動で投げる","なでてみて")]:
      await seed(pg,{"sushi":1},ui=ui); h=await pg.text_content("#petHint"); ok(f"{ui} 간식 있을 때 힌트", auto in h, h)
      await pg.evaluate("()=>{ const el=document.querySelector('.pw-it.sel'); window.__t.petThrow('sushi', el); }"); await pg.wait_for_timeout(200)
      h=await pg.text_content("#petHint"); ok(f"{ui} 간식 0개 → 쓰다듬기 힌트", zero in h, h); await pg.wait_for_timeout(800)
      await seed(pg,{},ui=ui); h=await pg.text_content("#petHint"); ok(f"{ui} 처음부터 0개 힌트", zero in h, h)
    # 배치: 말풍선이 📸·게이지와 안 겹침, 안내 줄 낱말 안 끊김, 스크롤 없음
    for ui in ("ko","ja"):
      for vw,vh in [(390,844),(360,640)]:
        await pg.set_viewport_size({"width":vw,"height":vh}); await seed(pg,{"sushi":2},ui=ui)
        await pg.evaluate("()=>{ const m=document.querySelector('#petMsg'); m.textContent=window.__t.PT()[window.__t.S().meta.settings.ui].welcome || 'x'; m.classList.add('show'); }"); await pg.wait_for_timeout(400)
        r=await pg.evaluate("""()=>{ const q=s=>document.querySelector(s).getBoundingClientRect(); const m=q('#petMsg'), b=q('#petBrag'), c=q('#petCos'), lv=q('#petLv');
          const ov=(a,b)=>!(a.right<=b.left||b.right<=a.left||a.bottom<=b.top||b.bottom<=a.top); return {brag:ov(m,b), cos:ov(m,c), lv:ov(m,lv), hint:ov(m,q('#petHint')), scroll:(()=>{ const p=document.querySelector('#pet'); return p.scrollHeight>p.clientHeight+1 || p.getBoundingClientRect().height>innerHeight+1; })(), m:[m.top,m.bottom,m.left,m.right], b:[b.top,b.bottom,b.left]}; }""")
        ok(f"{ui} {vw} 말풍선이 📸·🛒·레벨 게이지·안내 줄 안 가림", not r["brag"] and not r["cos"] and not r["lv"] and not r["hint"], r)
        ok(f"{ui} {vw} 스크롤 없음", not r["scroll"])
        wb=await pg.evaluate("()=>getComputedStyle(document.querySelector('#petHint')).wordBreak"); ok(f"{ui} {vw} 안내 줄 keep-all", wb=="keep-all", wb)
        await pg.screenshot(path=f"/tmp/petfly_{ui}_{vw}.png")
    ok("오류 없음(문구)", not errs, errs[:3])
    await b.close()
  print(f"{sum(R)}/{len(R)}");
  if not all(R): raise SystemExit(1)
asyncio.run(main())
