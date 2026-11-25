# 설정 화면 묶음(아이콘 카드) + 냥이 감도 연속 슬라이더·흔들림 미리보기
import asyncio, json, re
from playwright.async_api import async_playwright
R=[]
def ok(n,c,i=""): R.append(c); print(("✅" if c else "❌"), n, "" if c else i)
async def seed(pg, ui, **st):
  s={"ui":ui,"lang":"es","homePet":False}; s.update(st)
  await pg.goto("http://localhost:8765/index.html")
  await pg.evaluate("s=>localStorage.setItem('focus-vocab-v1', s)", json.dumps({"cards":{},"meta":{"setup":1,"tutAsked":1,"loginAsked":1,"days":{},"settings":s,"stepv":1}}))
  await pg.goto("http://localhost:8765/index.html"); await pg.wait_for_timeout(1100)
  await pg.evaluate("()=>window.__t.showView('how')"); await pg.wait_for_timeout(400)
async def amp(pg, v):
  await pg.evaluate("v=>{const r=document.querySelector('#petSensSel'); r.value=v; r.dispatchEvent(new Event('input'));}", v)
  await pg.evaluate("()=>document.querySelector('#psStage').scrollIntoView({block:'center'})")
  await pg.wait_for_timeout(2500); return await pg.evaluate("()=>window.__t.PS.max")
async def main():
  async with async_playwright() as pw:
    b=await pw.chromium.launch()
    for vw,vh in [(360,640),(390,844)]:
      ctx=await b.new_context(viewport={"width":vw,"height":vh}); pg=await ctx.new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)))
      await ctx.route(re.compile(r"(tosspayments|supabase\.co)"), lambda r: r.abort())
      for ui in ["ko","ja"]:
        await seed(pg, ui)
        g=await pg.evaluate("()=>[...document.querySelectorAll('#mySet .card.sg')].map(c=>[c.querySelector('.sg-ic').textContent, c.querySelector('h2').textContent, c.querySelector('.sg-sub').textContent])")
        ok(f"{vw} {ui} 설정 묶음 6개, 아이콘·제목·설명 다 있음", len(g)==6 and all(a and b and c for a,b,c in g), g)
        grp=await pg.evaluate("""()=>{ const w=id=>{const e=document.getElementById(id); const c=e&&e.closest('.card.sg'); return c?c.querySelector('h2').dataset.sgt:''}; return ['nickIn','authBox','setNew','setTarget','setMaxRev','setOrder','setWrite','setSpeak','setHf','setAccent','vkOnChk','setVoice','setRate','petSensSel','homePetOn','setSign','setUi','trackOn','setEmail'].map(w).join(','); }""")
        ok(f"{vw} {ui} 관련 설정끼리 같은 묶음", grp=="acct,acct,study,study,study,study,quiz,quiz,quiz,quiz,quiz,voice,voice,pet,pet,pet,app,app,app", grp)
        ov=await pg.evaluate("()=>document.documentElement.scrollWidth-innerWidth"); ok(f"{vw} {ui} 가로 넘침 0", ov<=0, ov)
        ok(f"{vw} {ui} 감도 = 연속 슬라이더", await pg.evaluate("()=>{const r=document.querySelector('#petSensSel'); return r.type==='range' && +r.step<=0.01}"))
        w=await pg.evaluate("()=>document.querySelector('#petSensOut').textContent"); ok(f"{vw} {ui} 감도 이름·% 표시", "100%" in w, w)
        ok(f"{vw} {ui} 복습 원리는 아래로", await pg.evaluate("()=>{const a=document.querySelector('#mySet'), f=document.querySelector('#forecast'); return !!(a.compareDocumentPosition(f) & Node.DOCUMENT_POSITION_FOLLOWING)}"))
      lo=await amp(pg,"0.5"); ll=await pg.evaluate("()=>window.__t.PS.lmax"); hi=await amp(pg,"1.8")
      ok(f"{vw} 감도 높을수록 더 멀리 흔들림", hi>lo*1.8 and lo>1, [lo,hi])
      hl=await pg.evaluate("()=>window.__t.PS.lmax"); ok(f"{vw} 감도 높을수록 목이 더 늘어남(고무)", hl>15 and hl>ll*3, [ll,hl])
      px=await pg.evaluate("()=>{const c=document.querySelector('#psCv'), d=c.getContext('2d').getImageData(0,0,c.width,c.height).data; let n=0; for(let i=3;i<d.length;i+=4) if(d[i]>0) n++; return n}"); ok(f"{vw} 냥이 그림 그려짐(캔버스)", px>3000, px)
      ok(f"{vw} 몸은 고정(원본 img 숨김·캔버스만)", await pg.evaluate("()=>document.querySelector('#psCat').hidden"))
      await pg.evaluate("()=>{const r=document.querySelector('#petSensSel'); r.value='1.23'; r.dispatchEvent(new Event('input')); r.dispatchEvent(new Event('change'));}"); await pg.wait_for_timeout(150)
      v=await pg.evaluate("()=>JSON.parse(localStorage.getItem('focus-vocab-v1')).meta.settings.petSens"); ok(f"{vw} 중간값 1.23 저장", v==1.23, v)
      await seed(pg, "ko", petSens=1.35)
      ok(f"{vw} 옛 단계값 1.35 그대로 읽음", await pg.evaluate("()=>document.querySelector('#petSensSel').value")=="1.35")
      await pg.evaluate("()=>window.__t.showView('today')"); await pg.wait_for_timeout(1200)
      ok(f"{vw} 다른 화면에선 흔들림 멈춤", await pg.evaluate("()=>window.__t.PS.run")==0)
      ok(f"{vw} 오류 없음", not errs, errs[:3])
      await ctx.close()
    await b.close()
  print(f"\n{sum(R)}/{len(R)}")
  if not all(R): raise SystemExit(1)
asyncio.run(main())
