# 말하기 채점 스페인어 동음어 (요청 R-1123-루프-말하기동음, 검수단 R1-4-3)
# 인식이 valla·votar·vello로 받아 적어도 핵심 단어(vaya·botar·bello)로 보고 「철자는 ○○」 한 줄 / 쓰기 채점 check는 그대로 오답 / ja·ko 말하기 회귀
import asyncio, sys, json, datetime
from playwright.async_api import async_playwright
R=[]
def ok(n,c,i=""): R.append(bool(c)); print(("✅" if c else "❌"), n, "" if c else i)
def ds(d): return (datetime.datetime.now(datetime.timezone.utc)-datetime.timedelta(days=d, hours=4)).strftime("%Y-%m-%d")
def card(i,lang,w,m,ex,tr): return dict(id=i,lang=lang,word=w,meaning=m,deck="default",example=ex,exampleKo=tr,due=ds(1),level=2,reps=3,lapses=0,created=1,introduced="2025-12-01",S=4,D=5,last=ds(5),step=4,log=[])
def state(lang):
  cs={"v1":card("v1","es","vaya","가다(접속법)","Que te vaya bien.","잘 지내."),"b1":card("b1","es","botar","던지다, 버리다","Hay que botar la basura.","쓰레기를 버려야 한다."),
      "j1":card("j1","ja","猫","고양이","猫が好きです。","고양이를 좋아해요.")}
  return {"cards":cs,"meta":{"setup":1,"tutAsked":1,"loginAsked":1,"days":{},"stepv":1,"settings":{"ui":"ko","lang":lang,"speaking":True}}}
INIT="""(()=>{ try{ Object.defineProperty(navigator,'mediaDevices',{value:{getUserMedia:async()=>({getTracks:()=>[]})},configurable:true}); }catch(e){}
  class FakeSR{ start(){ setTimeout(()=>{ const t=window.__heard||''; this.onresult&&this.onresult({results:[[{transcript:t}]]}); setTimeout(()=>this.onend&&this.onend(),30); },30); } stop(){ this.onend&&this.onend(); } }
  window.webkitSpeechRecognition=FakeSR; window.SpeechRecognition=FakeSR; })()"""
ASK="""([id,heard])=>{ const t=window.__t; window.__heard=heard; document.querySelectorAll('.sheet-bg,#riskPop,.sup-ov,#s7').forEach(e=>e.remove()); const p=document.querySelector('#pet'); if(p&&!p.classList.contains('hidden')) document.querySelector('#petClose').click();
  t.showView('today'); t.setSES({queue:[{id,mode:'speak',st:5,k:'w'}],done:0,failed:{},remaining:{[id]:1},finished:[],state:null,course:{n:12,i:0,newK:0,ok:0,g:0}}); t.$('#sessionStart').classList.add('hidden'); t.$('#sessionBox').classList.remove('hidden'); t.nextItem(); return !!document.querySelector('#micBtn'); }"""
async def main():
  async with async_playwright() as pw:
    b=await pw.chromium.launch(); errs=[]
    ctx=await b.new_context(viewport={"width":390,"height":844},locale="ko-KR"); await ctx.add_init_script(INIT)
    pg=await ctx.new_page(); pg.on("pageerror",lambda e:errs.append(str(e)))
    await pg.goto("http://localhost:8765/index.html")
    await pg.evaluate("s=>localStorage.setItem('focus-vocab-v1', s)", json.dumps(state("es"))); await pg.reload(); await pg.wait_for_timeout(1500)
    # 단위
    r=await pg.evaluate("""()=>{ const t=window.__t; return [t.spkHas('que te valla bien','vaya','es'), t.spkHas('hay que votar la basura','botar','es'), t.spkHas('es muy vello','bello','es'), t.spkHas('que te vaya bien','vaya','es'), t.spkHas('que te vio bien','vaya','es'), t.spkHas('ola','hola','es'), t.spkHas('chico','hico','es'), t.spkHas('ねこがすき','猫','ja'), t.spkHas('','vaya','es')]; }""")
    ok("valla ← vaya 핵심 단어 + 철자 안내", r[0].get("ok") and r[0].get("spell")=="vaya", r[0])
    ok("votar ← botar 핵심 단어", r[1].get("ok") and r[1].get("spell")=="botar", r[1])
    ok("vello ← bello 핵심 단어", r[2].get("ok"), r[2])
    ok("정확한 철자는 안내 없이 정답", r[3].get("ok") and not r[3].get("spell"), r[3])
    ok("다른 단어(vio)는 핵심 단어 아님", not r[4].get("ok"), r[4])
    ok("소리 안 나는 h: ola ← hola", r[5].get("ok"), r[5])
    ok("ch의 h는 지우지 않음(chico ≠ hico)", not r[6].get("ok"), r[6])
    ok("ja는 보조 판정 안 씀", not r[7].get("ok"), r[7])
    ok("들린 것 없음 → 아님", not r[8].get("ok"), r[8])
    r=await pg.evaluate("()=>{ const t=window.__t; return [t.check('valla','vaya'), t.check('votar','botar'), t.check('vaya','vaya')]; }")
    ok("쓰기 채점 check는 그대로(valla·votar 오답)", r[0]=="no" and r[1]=="no" and r[2]=="ok", r)
    # 화면: 말하기 문제
    for cid,heard,want,spell in [("v1","que te valla bien","ok","vaya"),("b1","hay que votar la basura","ok","botar"),("v1","que te vaya bien","ok",None),("v1","buenos dias","no",None)]:
      has=await pg.evaluate(ASK,[cid,heard]); await pg.wait_for_timeout(300)
      if not has: ok("마이크 버튼", False, "no micBtn"); continue
      await pg.click("#micBtn"); await pg.wait_for_timeout(400); await pg.click("#rv"); await pg.wait_for_timeout(300)
      fb=await pg.evaluate("()=>{ const f=document.querySelector('#fb .feedback'); return f?[f.className, f.textContent]:null; }")
      good = fb and (("ok" in fb[0].split()) == (want=="ok")) and ((spell and f"철자는 {spell}" in fb[1]) or (not spell and "철자는" not in fb[1]))
      ok(f"말하기 화면 '{heard}' → {want}" + (f" + 철자는 {spell}" if spell else ""), good, fb)
    await ctx.close()
    # ja 말하기 회귀
    ctx=await b.new_context(viewport={"width":390,"height":844},locale="ko-KR"); await ctx.add_init_script(INIT)
    pg=await ctx.new_page(); pg.on("pageerror",lambda e:errs.append(str(e)))
    await pg.goto("http://localhost:8765/index.html")
    await pg.evaluate("s=>localStorage.setItem('focus-vocab-v1', s)", json.dumps(state("ja"))); await pg.reload(); await pg.wait_for_timeout(1500)
    for heard,want in [("猫が好きです","ok"),("犬が好きです","no")]:
      await pg.evaluate(ASK,["j1",heard]); await pg.wait_for_timeout(300); await pg.click("#micBtn"); await pg.wait_for_timeout(400); await pg.click("#rv"); await pg.wait_for_timeout(300)
      fb=await pg.evaluate("()=>{ const f=document.querySelector('#fb .feedback'); return f?[f.className, f.textContent]:null; }")
      ok(f"ja 말하기 '{heard}' → {want}", fb and (("ok" in fb[0].split()) == (want=="ok")) and "철자는" not in fb[1], fb)
    await ctx.close()
    ok("페이지 오류 없음", not errs, errs[:3])
    await b.close()
  sys.exit(0 if all(R) else 1)
asyncio.run(main())
