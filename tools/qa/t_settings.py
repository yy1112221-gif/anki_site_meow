# R-1124-루프-설정정리 (R1-53-1·R1-53-3·R1-53-4·R1-53-6·R1-53-7·R1-53-2): 설정·사용법 화면 문구·배치
import asyncio, json, re
from playwright.async_api import async_playwright
R=[]
def ok(n,c,i=""): R.append(c); print(("✅" if c else "❌"), n, "" if c else i)
def meta(ui, lang, **st):
  s={"ui":ui,"lang":lang,"homePet":False}; s.update(st)
  return {"setup":1,"tutAsked":1,"loginAsked":1,"days":{},"settings":s,"stepv":1}
async def seed(pg, m):
  await pg.goto("http://localhost:8765/index.html")
  await pg.evaluate("s=>localStorage.setItem('focus-vocab-v1', s)", json.dumps({"cards":{},"meta":m}))
  await pg.goto("http://localhost:8765/index.html"); await pg.wait_for_timeout(1200)
  await pg.evaluate("()=>{ const c=document.querySelector('#petClose'); if(c && c.offsetParent) c.click(); }")
async def how(pg):
  await pg.evaluate("()=>window.__t.showView('how')"); await pg.wait_for_timeout(350)
async def main():
  async with async_playwright() as pw:
    b=await pw.chromium.launch()
    for vw,vh in [(360,640),(390,844)]:
      ctx=await b.new_context(viewport={"width":vw,"height":vh}); pg=await ctx.new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)))
      await ctx.route(re.compile(r"(tosspayments|supabase\.co)"), lambda r: r.abort())
      for ui in ["ko","ja"]:
        await seed(pg, meta(ui, "es")); await how(pg)
        ov=await pg.evaluate("()=>document.documentElement.scrollWidth - innerWidth")
        ok(f"{vw} {ui} 설정 화면 가로 넘침 0", ov<=0, ov)
        bad=await pg.evaluate("""()=>{ const out=[]; document.querySelectorAll('#mySet input[type=checkbox], #mySet select').forEach(i=>{ if(!i.offsetParent) return; const c=i.closest('.card').getBoundingClientRect(), r=i.getBoundingClientRect();
          if(r.left<c.left-0.5||r.right>c.right+0.5||r.width<18) out.push(i.id+':'+Math.round(r.left)+'-'+Math.round(r.right)+'/'+Math.round(c.right)+' w'+Math.round(r.width)); }); return out; }""")
        ok(f"{vw} {ui} #mySet 체크박스·선택 전부 카드 안(안 찌그러짐)", not bad, bad)
        lbl=await pg.evaluate("()=>{ const o=[]; document.querySelectorAll('#mySet .ms-tg>span').forEach(s=>{ if(s.offsetParent && s.scrollWidth>s.clientWidth+1) o.push(s.id); }); return o; }")
        ok(f"{vw} {ui} #mySet 라벨 안 잘림", not lbl, lbl)
        ok(f"{vw} {ui} lang es #setAccent 보임", await pg.evaluate("()=>!!document.querySelector('#setAccent').offsetParent"))
        wh=await pg.evaluate("()=>document.querySelector('[data-i18n=writeHelp]').textContent")
        ok(f"{vw} {ui} 문장 쓰기 도움말", ("5" in wh) and len(wh)>10, wh)
        n1=await pg.evaluate("()=>document.querySelector('[data-i18n-html=note1]').textContent")
        ok(f"{vw} {ui} 사용법 note1 = 12문제 판·칸 0~5", "12" in n1 and ("0~5" in n1 or "0〜5" in n1), n1[:60])
        n4=await pg.evaluate("()=>document.querySelector('[data-i18n-html=note4]').textContent")
        ok(f"{vw} {ui} 사용법 note4 = 판에 2개까지", "2" in n4 and ("빈칸과 쓰기 문제가 둘 다" not in n4), n4[:60])
        for lg in (["ja","ko"] if ui=="ko" else ["ko","ja"]):
          if lg==ui: continue
          await seed(pg, meta(ui, lg)); await how(pg)
          ok(f"{vw} {ui} lang {lg} #setAccent 없음", await pg.evaluate("()=>!document.querySelector('#setAccent').offsetParent"))
          ov=await pg.evaluate("()=>document.documentElement.scrollWidth - innerWidth"); ok(f"{vw} {ui} lang {lg} 가로 넘침 0", ov<=0, ov)
          w=await pg.evaluate("()=>[...document.querySelectorAll('#mySet .ms-tg')].filter(l=>l.offsetParent).map(l=>{const i=l.querySelector('input,select'),c=l.closest('.card').getBoundingClientRect(),r=i.getBoundingClientRect();return (r.right<=c.right+0.5&&r.width>=18)?'':l.querySelector('span').textContent.slice(0,10)}).filter(Boolean)")
          ok(f"{vw} {ui} lang {lg} 체크박스 카드 안", not w, w)
      # 문구
      await seed(pg, meta("ko","es"))
      ok(f"{vw} ko 모드 이름 meaning = 뜻 쓰기", 'modes:{ meaning:"뜻 쓰기",' in open("index.html",encoding="utf-8").read())
      await seed(pg, meta("ja","es")); await how(pg)
      ja=await pg.evaluate("()=>document.querySelector('[data-i18n=setAccent]').textContent")
      ok(f"{vw} ja 악센트 문구 「アクセント記号（é など）」", "アクセント記号（é など）" in ja, ja)
      # setNew 0 → 7로 되돌림
      await pg.fill("#setNew","0"); await pg.dispatch_event("#setNew","change"); await pg.wait_for_timeout(200)
      v=await pg.evaluate("()=>[document.querySelector('#setNew').value, window.__t.S().meta.settings.newLimit]")
      ok(f"{vw} #setNew 0 → 입력칸·저장 7", v==["7",7], v)
      await pg.fill("#setNew","12"); await pg.dispatch_event("#setNew","change"); await pg.wait_for_timeout(200)
      v=await pg.evaluate("()=>[document.querySelector('#setNew').value, window.__t.S().meta.settings.newLimit]")
      ok(f"{vw} #setNew 12 그대로", v==["12",12], v)
      # 설정값 저장·읽기 회귀(옛 데이터 그대로)
      await seed(pg, meta("ko","es", writing=False, speaking=False, strictAccent=True, newLimit=15, maxReviews=120)); await how(pg)
      v=await pg.evaluate("()=>[document.querySelector('#setWrite').checked, document.querySelector('#setSpeak').checked, document.querySelector('#setAccent').checked, document.querySelector('#setNew').value, document.querySelector('#setMaxRev').value]")
      ok(f"{vw} 옛 설정 읽기 그대로", v==[False,False,True,"15","120"], v)
      st=await pg.evaluate("()=>JSON.parse(localStorage.getItem('focus-vocab-v1')).meta.settings")
      ok(f"{vw} 저장된 설정 키 보존", st.get("writing") is False and st.get("strictAccent") is True and st.get("newLimit")==15 and st.get("lang")=="es", st)
      await pg.click("#setWrite"); await pg.wait_for_timeout(150)
      ok(f"{vw} #setWrite 바꾸면 저장", await pg.evaluate("()=>JSON.parse(localStorage.getItem('focus-vocab-v1')).meta.settings.writing")==True)
      ok(f"{vw} 오류 없음", not errs, errs[:3])
      await ctx.close()
    await b.close()
  print(f"\n{sum(R)}/{len(R)}");
  if not all(R): raise SystemExit(1)
asyncio.run(main())
