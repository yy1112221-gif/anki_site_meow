# R-1124-④-밤테마: 냥이 화면 ☀️/🌙 버튼 · settings.petNight 유지 · 옛 데이터는 낮 · ?rec=pet&night=1 과 같은 그림
import asyncio, json, sys
from playwright.async_api import async_playwright
R=[]
def ok(n,c,i=""): R.append(c); print(("✅" if c else "❌"), n, "" if c else i)
def mk(n=6):
  return {f"d{i}":dict(id=f"d{i}",lang="es",word=f"pal{i}",meaning=f"뜻{i}",example="",level=2,due="2026-01-01",isNew=False,lapses=0,reps=3,created=i,introduced="2025-12-01",mastered=False,relearn=False,log=[],deck="default",step=2,S=3,D=5,last="2025-12-20") for i in range(n)}
async def seed(pg, ui="ko", night=None):
  st={"ui":ui,"lang":"es","homePet":False}
  if night is not None: st["petNight"]=night
  meta={"setup":1,"tutAsked":1,"loginAsked":1,"days":{},"settings":st,"stepv":1,"pet":{"inv":{"sushi":2},"kcal":0,"lv":1,"granted":{},"seenTier":9}}
  for _ in range(3):
    await pg.evaluate("s=>localStorage.setItem('focus-vocab-v1', s)", json.dumps({"cards":mk(),"meta":meta})); await pg.reload(); await pg.wait_for_timeout(900)
    if await pg.evaluate("u=>window.__t.S().meta.settings.ui===u", ui): break
  await pg.evaluate("()=>{ const t=window.__t; if(!t.pet()) t.openPet(); }"); await pg.wait_for_timeout(900)
GEO="""()=>{ const r=s=>{ const e=document.querySelector(s); if(!e || getComputedStyle(e).display==='none') return null; const b=e.getBoundingClientRect(); return [b.left,b.top,b.right,b.bottom]; };
  return { nt:r('#petNight'), snd:r('#petSnd'), close:r('#petClose'), lv:r('.pet-lv'), msg:r('#petMsg'), night:document.querySelector('#pet').classList.contains('night'), txt:(document.querySelector('#petNight')||{}).textContent,
    sc:[document.querySelector('#pet').scrollHeight, document.querySelector('#pet').clientHeight], bg:getComputedStyle(document.querySelector('#pet')).backgroundImage.slice(0,40) }; }"""
def inter(a,b): return a and b and not (a[2]<=b[0] or b[2]<=a[0] or a[3]<=b[1] or b[3]<=a[1])
async def main():
  async with async_playwright() as pw:
    b=await pw.chromium.launch()
    for vw,vh in [(390,844),(360,640)]:
      ctx=await b.new_context(viewport={"width":vw,"height":vh}); pg=await ctx.new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)))
      await pg.goto("http://localhost:8765/index.html")
      await seed(pg); g=await pg.evaluate(GEO)
      ok(f"{vw} 옛 데이터(키 없음) → 낮 ☀️", g["nt"] and not g["night"] and g["txt"]=="☀️", g)
      ok(f"{vw} 버튼 24px 이상", g["nt"] and g["nt"][2]-g["nt"][0]>=24 and g["nt"][3]-g["nt"][1]>=24, g["nt"])
      ok(f"{vw} 🔉·학습하기·게이지와 안 겹침", not inter(g["nt"],g["snd"]) and not inter(g["nt"],g["close"]) and not inter(g["nt"],g["lv"]), g)
      await pg.click("#petNight"); await pg.wait_for_timeout(300); g=await pg.evaluate(GEO)
      ok(f"{vw} 누르면 밤 🌙", g["night"] and g["txt"]=="🌙" and await pg.evaluate("()=>window.__t.S().meta.settings.petNight===true"), g)
      ok(f"{vw} 밤 배경 그림(radial)", "radial-gradient" in g["bg"], g["bg"])
      await pg.screenshot(path=f"/tmp/night{vw}.png")
      ok(f"{vw} 저장됨", await pg.evaluate("()=>JSON.parse(localStorage.getItem('focus-vocab-v1')).meta.settings.petNight===true"))
      await pg.evaluate("()=>window.__t.closePet()"); await pg.reload(); await pg.wait_for_timeout(900); await pg.evaluate("()=>{ const t=window.__t; if(!t.pet()) t.openPet(); }"); await pg.wait_for_timeout(700)
      g=await pg.evaluate(GEO); ok(f"{vw} 다시 열어도 밤 유지", g["night"] and g["txt"]=="🌙", g)
      ok(f"{vw} 밤 화면 스크롤 없음", g["sc"][0]<=g["sc"][1]+1, g["sc"])
      # 밤 대비: 안내 줄 글자 밝게
      col=await pg.evaluate("()=>getComputedStyle(document.querySelector('#petHint')).color"); ok(f"{vw} 밤 안내 줄 밝은 글자", col.replace(" ","") in ("rgb(230,224,240)",), col)
      await pg.click("#petNight"); await pg.wait_for_timeout(200); g=await pg.evaluate(GEO)
      ok(f"{vw} 다시 누르면 낮(false 저장)", not g["night"] and await pg.evaluate("()=>window.__t.S().meta.settings.petNight===false"), g)
      # 다른 설정·데이터 그대로
      ok(f"{vw} 다른 설정 그대로", await pg.evaluate("()=>{ const s=window.__t.S(); return s.meta.settings.lang==='es' && Object.keys(s.cards).length===6 && s.meta.pet.inv.sushi===2; }"))
      # 일본어 화면
      await seed(pg, ui="ja", night=True); g=await pg.evaluate(GEO); ok(f"{vw} ja 밤 저장값으로 열림", g["night"] and g["txt"]=="🌙", g)
      # rec 촬영 모드: clean이면 버튼 숨김, night=1 그대로
      await pg.goto("http://localhost:8765/index.html?rec=pet&night=1&clean=1"); await pg.wait_for_timeout(1500); g=await pg.evaluate(GEO)
      ok(f"{vw} ?rec=pet&night=1&clean=1 → 밤·버튼 숨김", g["night"] and g["nt"] is None, g)
      await pg.goto("http://localhost:8765/index.html?rec=pet"); await pg.wait_for_timeout(1500); g=await pg.evaluate(GEO)
      ok(f"{vw} ?rec=pet(night 없음) → 낮", not g["night"], g)
      ok(f"{vw} 오류 없음", not errs, errs[:3])
      await ctx.close()
    await b.close()
  print(f"\n{sum(R)}/{len(R)}"); sys.exit(0 if all(R) else 1)
asyncio.run(main())
