# 입력칸·화면 자판 (요청 R-1123-검수단-한자자판 R1-21-1 · R-1123-루프-입력칸정리 R1-14-1·R1-21-3·R1-14-3)
# ① 「한자까지 정확히」(strictKanji) ON → 일본어 답 입력칸은 화면 자판 대신 폰 키보드(readOnly 아님) → 遅い 정답 / OFF → 화면 자판·おそい 정답
# ② 입력칸 안내문(placeholder)이 🎤·⌨️ 아이콘에 가리지 않음(390·360 × ui ko·ja) ③ 화면 자판으로 そっちょく 입력 ④ 문제 머리 줄 「1 / 12」 한 줄
import asyncio, sys, json, datetime
from playwright.async_api import async_playwright
R=[]
def ok(n,c,i=""): R.append(bool(c)); print(("✅" if c else "❌"), n, "" if c else i)
def ds(d): return (datetime.datetime.now(datetime.timezone.utc)-datetime.timedelta(days=d, hours=4)).strftime("%Y-%m-%d")
def state(ui="ko", lang="ja", strict=False, vk=None):
  cards={"k1":dict(id="k1",lang="ja",word="遅い",reading="おそい",meaning="おそい · 느리다, 늦다",deck="default",example="",due=ds(1),level=2,reps=3,lapses=0,created=1,introduced="2025-12-01",S=4,D=5,last=ds(5),step=4,log=[]),
         "k2":dict(id="k2",lang="ja",word="率直",reading="そっちょく",meaning="そっちょく · 솔직",deck="default",example="",due=ds(1),level=2,reps=3,lapses=0,created=2,introduced="2025-12-01",S=4,D=5,last=ds(5),step=4,log=[]),
         "e1":dict(id="e1",lang="es",word="lento",meaning="느린",deck="default",example="El tren es lento.",exampleKo="기차가 느리다.",due=ds(1),level=2,reps=3,lapses=0,created=3,introduced="2025-12-01",S=4,D=5,last=ds(5),step=3,log=[])}
  st={"ui":ui,"lang":lang}
  if strict: st["strictKanji"]=True
  if vk is not None: st["vk"]=vk
  return {"cards":cards,"meta":{"setup":1,"tutAsked":1,"loginAsked":1,"days":{},"stepv":1,"settings":st}}
ASK="""([id,mode])=>{ const t=window.__t; document.querySelectorAll('.sheet-bg,#riskPop,.sup-ov,#s7').forEach(e=>e.remove()); const p=document.querySelector('#pet'); if(p&&!p.classList.contains('hidden')) document.querySelector('#petClose').click();
  t.showView('today'); t.setSES({queue:[{id,mode,st:4,k:'w'}],done:0,failed:{},remaining:{[id]:1},finished:[],state:null,course:{n:12,i:0,newK:0,ok:0,g:0}}); t.$('#sessionStart').classList.add('hidden'); t.$('#sessionBox').classList.remove('hidden'); t.nextItem(); return 1; }"""
CLIP="""()=>{ const i=document.querySelector('#ans'); if(!i) return null; const s=getComputedStyle(i), ic=document.querySelector('.ans-ics');
  const cv=document.createElement('canvas').getContext('2d'); const ps=getComputedStyle(i,'::placeholder'); cv.font=ps.font||s.font; const tw=cv.measureText(i.placeholder).width;
  const r=i.getBoundingClientRect(), pl=parseFloat(s.paddingLeft), pr=parseFloat(s.paddingRight), room=r.width-pl-pr;
  const ir=ic?ic.getBoundingClientRect():null; const contentR=r.right-pr;
  return {ph:i.placeholder, tw:Math.round(tw), room:Math.round(room), over:!!ir && contentR>ir.left+1, icw: ir?Math.round(ir.width):0, pr}; }"""
async def main():
  async with async_playwright() as pw:
    b=await pw.chromium.launch(); errs=[]
    async def page(W,H,st,loc="ko-KR"):
      ctx=await b.new_context(viewport={"width":W,"height":H},locale=loc,has_touch=True,is_mobile=True)
      pg=await ctx.new_page(); pg.on("pageerror",lambda e:errs.append(str(e)))
      await pg.goto("http://localhost:8765/index.html")
      await pg.evaluate("s=>localStorage.setItem('focus-vocab-v1', s)", json.dumps(st)); await pg.reload(); await pg.wait_for_timeout(1500)
      return ctx,pg
    # ① strictKanji ON: 폰 키보드 → 遅い 정답
    ctx,pg=await page(390,844,state(strict=True))
    await pg.evaluate(ASK,["k1","recall"]); await pg.wait_for_timeout(500)
    r=await pg.evaluate("()=>{ const i=document.querySelector('#ans'); return [i.readOnly, i.getAttribute('inputmode'), !!document.querySelector('.vk-host'), document.activeElement===i]; }")
    ok("strictKanji ON: 화면 자판 없음·입력칸 쓰기 가능(폰 키보드)", r[0] is False and r[1]!="none" and not r[2], r)
    await pg.fill("#ans","遅い"); await pg.click("#chk"); await pg.wait_for_timeout(400)
    ok("strictKanji ON: '遅い' 정답", await pg.locator("#fb .feedback.ok").count()>0, await pg.inner_text("#fb"))
    await pg.evaluate(ASK,["k1","recall"]); await pg.wait_for_timeout(400)
    await pg.fill("#ans","おそい"); await pg.click("#chk"); await pg.wait_for_timeout(400)
    ok("strictKanji ON: 'おそい'는 오답(한자 단어)", await pg.locator("#fb .feedback.ok").count()==0)
    # 설정에서 켤 때 안내 토스트
    r=await pg.evaluate("()=>{ const t=window.__t; t.S().meta.settings.strictKanji=false; return 1; }")
    await ctx.close()
    # ② strictKanji OFF: 화면 자판 그대로·おそい 정답 (회귀)
    ctx,pg=await page(390,844,state())
    await pg.evaluate(ASK,["k1","recall"]); await pg.wait_for_timeout(500)
    r=await pg.evaluate("()=>{ const i=document.querySelector('#ans'); return [i.readOnly, !!document.querySelector('.vk-host .vk')]; }")
    ok("strictKanji OFF: 화면 자판 그대로(readOnly)", r[0] is True and r[1], r)
    # 자판으로 おそい: お(a×5) そ(s×5) い(a×2)
    seq=["@ja"]*5+["@br"]+["@js"]*5+["@br"]+["@ja"]*2
    for v in seq: await pg.click(f".vk-host [data-v='{v}']")
    v=await pg.input_value("#ans"); ok("화면 자판으로 おそい 입력", v=="おそい", v)
    await pg.click(".vk-host [data-v='@ok']"); await pg.wait_for_timeout(400)
    ok("strictKanji OFF: 'おそい' 정답", await pg.locator("#fb .feedback.ok").count()>0, await pg.inner_text("#fb"))
    # ③ そっちょく: そ(s×5) っ(t×6) ち(t×2) ょ(y×3 よ → 小) く(k×3)
    await pg.evaluate(ASK,["k2","recall"]); await pg.wait_for_timeout(500)
    seq=["@js"]*5+["@jt"]*6+["@br"]+["@jt"]*2+["@jy"]*3+["@mod"]+["@jk"]*3
    for v in seq: await pg.click(f".vk-host [data-v='{v}']")
    v=await pg.input_value("#ans"); ok("화면 자판으로 そっちょく 입력", v=="そっちょく", v)
    lab=await pg.inner_text(".vk-host [data-v='@mod']"); ok("「小」 키에 작은 글자 표시(っゃ)", "っ" in lab and "ゃ" in lab, lab)
    await ctx.close()
    # 설정 켤 때 토스트
    ctx,pg=await page(390,844,state())
    r=await pg.evaluate("""async()=>{ const t=window.__t; t.showView('how'); await new Promise(r=>setTimeout(r,300)); const k=document.querySelector('#kanjiChk'); if(!k) return 'nochk'; k.checked=true; k.onchange&&k.onchange(); await new Promise(r=>setTimeout(r,100)); return [t.S().meta.settings.strictKanji, document.querySelector('#toast').textContent]; }""")
    ok("「한자까지 정확히」 켤 때 폰 키보드 안내", isinstance(r,list) and r[0] is True and "키보드" in r[1], r)
    await ctx.close()
    # ④ 안내문 가림·머리 줄 한 줄: 390·360 × ui ko·ja (ja 화면은 ko 학습, ko 화면은 ja·es 학습)
    for W,H in [(390,844),(360,640)]:
      for ui,lang,cid,mode in [("ko","ja","k1","recall"),("ko","es","e1","cloze"),("ja","es","e1","cloze"),("ja","es","e1","study"),("ko","es","e1","study")]:
        ctx,pg=await page(W,H,state(ui=ui,lang=lang),"ja-JP" if ui=="ja" else "ko-KR")
        await pg.evaluate(ASK,[cid,mode]); await pg.wait_for_timeout(600)
        c=await pg.evaluate(CLIP)
        ok(f"{W}×{H} ui={ui} {mode}: 안내문이 아이콘에 안 가림", c and not c["over"] and c["tw"]<=c["room"]+1, c)
        hl=await pg.evaluate("()=>{ const s=[...document.querySelectorAll('.modehead > span span')].find(e=>/\\d+ \\/ \\d+/.test(e.textContent)); if(!s) return null; return [s.textContent, s.getClientRects().length]; }")
        ok(f"{W}×{H} ui={ui} {mode}: 「n / 12」 안 끊김", hl and hl[1]==1, hl)
        sc=await pg.evaluate("()=>[document.documentElement.scrollHeight, innerHeight]")
        ok(f"{W}×{H} ui={ui} {mode}: 스크롤 없음", sc[0]<=sc[1]+1, sc)
        if W==360 and ui=="ja" and mode=="study": await pg.screenshot(path="/tmp/t_input_360_ja.png")
        await ctx.close()
    ok("페이지 오류 없음", not errs, errs[:3])
    await b.close()
  sys.exit(0 if all(R) else 1)
asyncio.run(main())
