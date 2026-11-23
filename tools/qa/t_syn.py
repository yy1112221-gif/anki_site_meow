# 뜻 칸이 완전히 같은 다른 단어 = 정답 (요청 R-1123-루프-동의어정답, 검수단 R1-20-6)
# 팔십↔여든·정치인↔정치가: 3번째에도 정답 + q 기록 near:1 / 첫 뜻만 같은 쌍(아흔↔구십)은 nearSyn 안내 그대로 / 전혀 다른 단어 오답
import asyncio, sys, json, datetime
from playwright.async_api import async_playwright
R=[]
def ok(n,c,i=""): R.append(bool(c)); print(("✅" if c else "❌"), n, "" if c else i)
def ds(d): return (datetime.datetime.now(datetime.timezone.utc)-datetime.timedelta(days=d, hours=4)).strftime("%Y-%m-%d")
def card(i,w,m): return dict(id=i,lang="ko",word=w,meaning=m,deck="default",example="",exampleKo="",due=ds(1),level=2,reps=3,lapses=0,created=1,introduced="2025-12-01",S=4,D=5,last=ds(5),step=4,log=[])
def state(extra):
  cs={"p8":card("p8","팔십","八十（はちじゅう）"),"pi":card("pi","정치인","政治家（せいじか）"),"ah":card("ah","아흔","九十（きゅうじゅう）"),"ha":card("ha","하여튼","何はともあれ（なにはともあれ）、とにかく")}
  if extra: cs["yd"]=card("yd","여든","八十（はちじゅう）")
  return {"cards":cs,"meta":{"setup":1,"tutAsked":1,"loginAsked":1,"days":{},"stepv":1,"settings":{"ui":"ja","lang":"ko","vk":False}}}
ASK="""([id,typed,mode])=>{ const t=window.__t; document.querySelectorAll('.sheet-bg,#riskPop,.sup-ov,#s7').forEach(e=>e.remove()); const p=document.querySelector('#pet'); if(p&&!p.classList.contains('hidden')) document.querySelector('#petClose').click();
  t.showView('today'); const prev=t.getSES(); t.setSES({queue:[{id,mode,st:4,k:'w'},{id:'ha',mode:'recall',st:4,k:'w'}],done:0,failed:{},remaining:{[id]:1,ha:1},finished:[],state:null,course:{n:12,i:0,newK:0,ok:0,g:0}});
  const s=t.getSES(); if(prev&&prev.keepNear) s.state=null; t.$('#sessionStart').classList.add('hidden'); t.$('#sessionBox').classList.remove('hidden'); t.nextItem();
  if(window.__near!=null) t.getSES().state.near=window.__near;
  const i=document.querySelector('#ans'); if(!i) return null; i.readOnly=false; i.value=typed; document.querySelector('#chk').click();
  const f=document.querySelector('#fb .feedback'); return f?[f.className, f.textContent]:null; }"""
async def main():
  async with async_playwright() as pw:
    b=await pw.chromium.launch(); errs=[]
    for extra in (True, False):
      tag="내 카드" if extra else "단어장만"
      ctx=await b.new_context(viewport={"width":390,"height":844},locale="ja-JP"); pg=await ctx.new_page(); pg.on("pageerror",lambda e:errs.append(str(e)))
      await pg.goto("http://localhost:8765/index.html")
      await pg.evaluate("s=>localStorage.setItem('focus-vocab-v1', s)", json.dumps(state(extra))); await pg.reload(); await pg.wait_for_timeout(1500)
      await pg.evaluate("async()=>{ for(const id of ['ko-beg','ko-mid','ko-adv']) await window.__t.presetData(id); }")
      await pg.evaluate("()=>{ window.__tr=[]; const o=window.__t.track; }")
      u=await pg.evaluate("()=>{ const t=window.__t, S=t.S(); const c=id=>S.cards[id]; return [t.sameMeanSyn(c('p8'),'여든'), t.sameMeanSyn(c('pi'),'정치가'), t.sameMeanSyn(c('ha'),'하여간'), t.sameMeanSyn(c('ah'),'구십'), t.sameMeanSyn(c('p8'),'구십'), t.sameMeanSyn(c('p8'),'팔십'), t.sameMeanSyn(c('p8'),'')]; }")
      ok(f"[{tag}] 단위: 여든·정치가·하여간 = 같은 뜻", u[0] and u[1] and u[2], u)
      ok(f"[{tag}] 단위: 첫 뜻만 같은 구십(아흔)·다른 뜻 구십(팔십)·자기 단어·빈 입력은 아님", not any(u[3:]), u)
      for n in (0,2,5):
        await pg.evaluate(f"()=>{{ window.__near={n}; }}")
        fb=await pg.evaluate(ASK,["p8","여든","recall"])
        ok(f"[{tag}] 팔십 ← 여든 정답 (안내 {n}번 뒤)", fb and "ok" in fb[0].split(), fb)
      q0=await pg.evaluate("()=>{ const s=window.__t.getSES(); return s.queue[0] && s.queue[0].near; }")
      ok(f"[{tag}] 문제에 near:1 표시", q0==1, q0)
      await pg.evaluate("()=>{ window.__near=0; }")
      fb=await pg.evaluate(ASK,["pi","정치가","recall"]); ok(f"[{tag}] 정치인 ← 정치가 정답", fb and "ok" in fb[0].split(), fb)
      fb=await pg.evaluate(ASK,["ah","구십","recall"]); ok(f"[{tag}] 아흔 ← 구십: 안내만(meh, 채점 안 함)", fb and "meh" in fb[0].split(), fb)
      await pg.evaluate("()=>{ window.__near=2; }")
      fb=await pg.evaluate(ASK,["ah","구십","recall"]); ok(f"[{tag}] 아흔 ← 구십: 안내 2번 뒤엔 오답 그대로", fb and "no" in fb[0].split(), fb)
      await pg.evaluate("()=>{ window.__near=0; }")
      fb=await pg.evaluate(ASK,["p8","고양이","recall"]); ok(f"[{tag}] 전혀 다른 단어 오답", fb and "no" in fb[0].split(), fb)
      fb=await pg.evaluate(ASK,["p8","팔십","recall"]); ok(f"[{tag}] 원래 정답 그대로", fb and "ok" in fb[0].split(), fb)
      await ctx.close()
    ok("페이지 오류 없음", not errs, errs[:3])
    await b.close()
  sys.exit(0 if all(R) else 1)
asyncio.run(main())
