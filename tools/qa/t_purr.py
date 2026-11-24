# R-1124-④-그르릉: 1초 넘게 계속 쓰다듬으면 그르릉(소리·진동·말풍선 10초에 한 번), 멈추면 꺼짐, 🔇면 소리·진동 0
import asyncio, json, math, sys, time
from playwright.async_api import async_playwright
R=[]
def ok(n,c,i=""): R.append(c); print(("✅" if c else "❌"), n, "" if c else i)
def mk(n=6):
  return {f"d{i}":dict(id=f"d{i}",lang="es",word=f"pal{i}",meaning=f"뜻{i}",example="",level=2,due="2026-01-01",isNew=False,lapses=0,reps=3,created=i,introduced="2025-12-01",mastered=False,relearn=False,log=[],deck="default",step=2,S=3,D=5,last="2025-12-20") for i in range(n)}
INIT="window.__vib=[]; try{ Object.defineProperty(navigator,'vibrate',{value:(p)=>{ window.__vib.push(p); return true; }, configurable:true}); }catch(e){}"
async def seed(pg, ui="ko", snd=None, sulk=None):
  st={"ui":ui,"lang":"es","homePet":False}
  if snd is not None: st["petSound"]=snd
  meta={"setup":1,"tutAsked":1,"loginAsked":1,"days":{},"settings":st,"stepv":1,"pet":{"inv":{"sushi":2},"kcal":0,"lv":1,"granted":{},"seenTier":9}}
  for _ in range(3):
    await pg.evaluate("s=>localStorage.setItem('focus-vocab-v1', s)", json.dumps({"cards":mk(),"meta":meta})); await pg.reload(); await pg.wait_for_timeout(900)
    if await pg.evaluate("u=>window.__t.S().meta.settings.ui===u", ui): break
  if sulk: await pg.evaluate("lv=>{ const t=window.__t, m=t.S().meta; m.sulk={lv, gap:4, at:t.today(), need:6, done:0, c:0}; }", sulk)
  await pg.evaluate("()=>{ const t=window.__t; if(!t.pet()) t.openPet(); }"); await pg.wait_for_timeout(900)
  await pg.evaluate("()=>{ window.__vib=[]; const m=document.querySelector('#petMsg'); m.textContent=''; m.classList.remove('show'); }")
async def face(pg): return await pg.evaluate("()=>{ const st=window.__t.pet(), r=document.querySelector('#petCv').getBoundingClientRect(), c=st.toScr(64,84); return [r.left+c.x, r.top+c.y]; }")
async def rub(pg, ms, up=True):
  x,y=await face(pg); await pg.mouse.move(x,y); await pg.mouse.down(); t0=time.monotonic(); i=0
  while (time.monotonic()-t0)*1000<ms:
    a=i*0.7; await pg.mouse.move(x+16*math.cos(a), y+10*math.sin(a)); await pg.wait_for_timeout(30); i+=1
  if up: await pg.mouse.up()
async def ps(pg): return await pg.evaluate("()=>window.__t.purrState()")
async def msg(pg): return await pg.evaluate("()=>document.querySelector('#petMsg').textContent")
async def main():
  async with async_playwright() as pw:
    b=await pw.chromium.launch(args=["--autoplay-policy=no-user-gesture-required"])
    for vw,vh in [(390,844),(360,640)]:
      ctx=await b.new_context(viewport={"width":vw,"height":vh}); await ctx.add_init_script(INIT); pg=await ctx.new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)))
      await pg.goto("http://localhost:8765/index.html")
      await seed(pg)
      await rub(pg, 600, up=False); s=await ps(pg); ok(f"{vw} 0.6초 쓰다듬기 → 아직 그르릉 없음", not s["on"] and not s["purr0"], s)
      await pg.mouse.up(); await pg.wait_for_timeout(200)
      await rub(pg, 1500, up=False); s=await ps(pg)
      ok(f"{vw} 1.5초 쓰다듬기 → 그르릉 소리 켜짐", s["on"] and s["purr0"]>0 and s["n"]==1, s)
      ok(f"{vw} 말풍선 「그르릉…」", (await msg(pg))=="그르릉…", await msg(pg))
      v=await pg.evaluate("()=>window.__vib"); ok(f"{vw} 진동 패턴 한 번", any(isinstance(p,list) and len(p)>=3 for p in v), v)
      await pg.wait_for_timeout(500); s=await ps(pg); ok(f"{vw} 손 안 떼고 멈추면(0.5초 정지) 꺼짐", not s["on"] and not s["purr0"], s)
      await pg.mouse.up(); await pg.wait_for_timeout(100)
      # 다시 쓰다듬기(10초 안) → 소리는 다시, 말풍선은 없음
      await pg.evaluate("()=>{ const m=document.querySelector('#petMsg'); m.textContent=''; }")
      await rub(pg, 1400, up=False); s=await ps(pg); ok(f"{vw} 다시 1.4초 → 그르릉 두 번째", s["on"] and s["n"]==2, s)
      ok(f"{vw} 10초 안 두 번째는 말풍선 없음", (await msg(pg))!="그르릉…", await msg(pg))
      await pg.mouse.up(); await pg.wait_for_timeout(80); s=await ps(pg); ok(f"{vw} 손 떼면 바로 꺼짐", not s["on"] and not s["purr0"], s)
      # 그르릉 중 닫기
      await rub(pg, 1300, up=False); on=(await ps(pg))["on"]; await pg.mouse.up(); await pg.evaluate("()=>window.__t.closePet()"); await pg.wait_for_timeout(100)
      ok(f"{vw} 그르릉 중 닫기 → 소리 꺼짐", on and not (await ps(pg))["on"])
      # 톡 치기는 그르릉 없음
      await pg.evaluate("()=>window.__t.openPet()"); await pg.wait_for_timeout(800); x,y=await face(pg)
      for _ in range(4): await pg.mouse.click(x,y); await pg.wait_for_timeout(150)
      ok(f"{vw} 톡 치기만으론 그르릉 없음", (await ps(pg))["n"]==0)
      sc=await pg.evaluate("()=>{ const p=document.querySelector('#pet'); return [p.scrollHeight, p.clientHeight, p.scrollWidth, p.clientWidth]; }"); ok(f"{vw} 냥이 화면 스크롤 없음", sc[0]<=sc[1]+1 and sc[2]<=sc[3]+1, sc)
      # 🔇: 소리·진동 0
      await seed(pg, snd=False); await rub(pg, 1500, up=False); s=await ps(pg)
      ok(f"{vw} 🔇 소리 없음", not s["on"], s); ok(f"{vw} 🔇 진동 없음", (await pg.evaluate("()=>window.__vib.length"))==0, await pg.evaluate("()=>window.__vib"))
      await pg.mouse.up()
      # 일본어 화면
      await seed(pg, ui="ja"); await rub(pg, 1500, up=False); ok(f"{vw} 일본어 「ゴロゴロ…」", (await msg(pg))=="ゴロゴロ…", await msg(pg)); await pg.mouse.up()
      # 화난 냥이는 그르릉 없음
      await seed(pg, sulk=2); await rub(pg, 1500, up=False); ok(f"{vw} 화난 동안 그르릉 없음", not (await ps(pg))["purr0"]); await pg.mouse.up()
      ok(f"{vw} 오류 없음", not errs, errs[:3])
      await ctx.close()
    await b.close()
  print(f"\n{sum(R)}/{len(R)}"); sys.exit(0 if all(R) else 1)
asyncio.run(main())
