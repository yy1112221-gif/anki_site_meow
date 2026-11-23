# 검수단 11-24: R1-50-1 복습 상한(하루) · R1-50-2 판 끝 제목 · R1-49-5 로그인 버튼 카카오 · R1-51-2 한국어 세트 단어장 이름
import asyncio, json, re
from playwright.async_api import async_playwright
R=[]
def ok(n,c,i=""): R.append(c); print(("✅" if c else "❌"), n, "" if c else i)
U="http://localhost:8765/index.html"
HG=re.compile(r"[가-힣]")
def card(i, w, lang="ja", **kw):
  d=dict(id=f"c{i}",lang=lang,word=w,meaning=f"뜻{i}",example="",deck="default",due="2099-01-01",level=2,reps=3,isNew=False,lapses=0,created=i,introduced="2025-12-01",mastered=False,relearn=False,log=[],step=2,S=30,D=5,last="2026-10-01")
  d.update(kw); return d
def st(cards, ui="ko", lang="ja", extra=None):
  m={"setup":1,"tutAsked":1,"loginAsked":1,"tutWant":0,"stepv":1,"days":{},"settings":{"ui":ui,"lang":lang,"homePet":False}}
  if extra: m.update(extra)
  return {"cards":cards,"meta":m}
async def put(pg, s):
  await pg.goto(U); await pg.evaluate("s=>localStorage.setItem('focus-vocab-v1', s)", json.dumps(s)); await pg.goto(U); await pg.wait_for_timeout(2200)
  await pg.evaluate("()=>{ const p=document.querySelector('#pet'); if(p && !p.classList.contains('hidden')) document.querySelector('#petClose').click(); }")
def dues(n): return {f"c{i}":card(i,f"単語{i}",due=f"2026-11-{(i%20)+1:02d}") for i in range(n)}
FIN="""()=>{ const S=__t.SES0=__t.buildCourse(); S.finished=[]; __t.setSES(S); __t.finishSession(); const b=document.querySelector('#sessionBox'); return {t:b.innerText, more:!!b.querySelector('#oneMore')}; }"""
async def main():
  async with async_playwright() as pw:
    b=await pw.chromium.launch(); errs=[]
    for W,H in [(390,844),(360,640)]:
      tag=f"{W}×{H}"
      ctx=await b.new_context(viewport={"width":W,"height":H},locale="ko-KR"); pg=await ctx.new_page(); pg.on("pageerror",lambda e:errs.append(str(e)))
      # ── R1-50-1 ──
      await put(pg, st(dues(120)))
      r=await pg.evaluate("()=>{ const d=__t.dueCards().map(c=>c.id), q=__t.buildCourse().queue.map(i=>i.id); return {n:d.length, out:q.filter(id=>!d.includes(id)).length, q:q.length}; }")
      ok(f"{tag} due120: 상한 80, 판 문제는 상한 안 카드만", r["n"]==80 and r["out"]==0 and r["q"]>0, r)
      r=await pg.evaluate("""()=>{ const S=__t.S(), d=__t.today(); __t.dueCards().slice(0,10).forEach(c=>{ c.last=d; c.due=__t.addDays(d,3); }); __t.renderAll(); return {n:__t.dueCards().length, rv:__t.revToday()}; }""")
      ok(f"{tag} 복습 10장 한 뒤 남은 상한 70(남음이 줄어듦)", r["n"]==70 and r["rv"]==10, r)
      r=await pg.evaluate("""()=>{ const d=__t.today(); __t.dueCards().forEach(c=>{ c.last=d; c.due=__t.addDays(d,3); }); __t.S().meta.cday={d,c:7,n:{}}; __t.renderAll(); return {n:__t.dueCards().length, q:__t.buildCourse().queue.length, start:!!document.querySelector('#startBtn'), txt:document.querySelector('#sessionStart').innerText}; }""")
      ok(f"{tag} 상한까지 다 하면 남은 40장은 안 나옴·▶시작 없음·📦 내일 안내", r["n"]==0 and r["q"]==0 and not r["start"] and "40" in r["txt"], r)
      await put(pg, st(dues(50)))
      ok(f"{tag} due 80 이하 회귀(50장 전부)", await pg.evaluate("()=>__t.dueCards().length")==50)
      # ── R1-50-2 ──
      await put(pg, st(dues(60)))
      r=await pg.evaluate(FIN)
      ok(f"{tag} due60 판1 끝: 「한 판 끝!」 + ▶ 한 판 더", "한 판 끝!" in r["t"] and "오늘 분량 끝" not in r["t"] and r["more"], r["t"][:80])
      ok(f"{tag} 판 끝 스크롤 없음", await pg.evaluate("()=>document.scrollingElement.scrollHeight<=innerHeight+1"))
      if W==360: await pg.screenshot(path="/tmp/r1124b_fin_360.png")
      cs={"c0":card(0,"猫"),"n0":card(1,"新語",isNew=True,reps=0,introduced=None,due=None,step=0,S=None,last=None)}; cs["n0"]["id"]="n0"
      await put(pg, st(cs, extra={"cday":None}))
      r=await pg.evaluate("()=>{ __t.S().meta.cday={d:__t.today(),c:1,n:{}}; return 1 }")
      r=await pg.evaluate(FIN)
      ok(f"{tag} 마지막 판 끝: 「오늘 분량 끝」·▶ 없음", "오늘 분량 끝" in r["t"] and not r["more"], r["t"][:80])
      await put(pg, st(dues(60), ui="ja"))
      r=await pg.evaluate(FIN)
      ok(f"{tag} ui ja 판1 끝: 「1回クリア」", "1回クリア" in r["t"] and r["more"], r["t"][:80])
      # ── R1-49-5 ──
      r=await pg.evaluate("()=>__t.provButtons(['google','kakao','apple','line'])")
      ok(f"{tag} ui ja 로그인 버튼 한글 0·「カカオで続ける」", not HG.search(r) and "カカオで続ける" in r, r)
      await put(pg, st({"c0":card(0,"猫")}))
      r=await pg.evaluate("()=>__t.provButtons(['google','kakao','line'])")
      ok(f"{tag} ui ko 「카카오로 계속하기」 회귀", "카카오로 계속하기" in r and "LINE으로" in r, r)
      # ── R1-51-2 ──
      lv={"id":"beg","label":"初級","labelKo":"초급"}
      await put(pg, st({"c0":card(0,"선생님",lang="ko")}, ui="ja", lang="ko", extra={"decks":[{"id":"default","name":"","on":True},{"id":"dk","name":"한국어 初級","on":True,"preset":"ko-beg"},{"id":"dm","name":"한국어 메모","on":True}]}))
      r=await pg.evaluate("lv=>({nm:__t.presetDeckName('ko',lv), shown:__t.decks().map(d=>__t.deckName(d)), saved:__t.S().meta.decks[1].name})", lv)
      ok(f"{tag} ui ja: 새 ko 세트 이름 「韓国語 初級」", r["nm"]=="韓国語 初級", r)
      ok(f"{tag} ui ja: 옛 「한국어 初級」 단어장은 「韓国語 初級」로 보임·저장 이름 그대로", r["shown"][1]=="韓国語 初級" and r["saved"]=="한국어 初級", r)
      ok(f"{tag} 사용자 단어장 이름(프리셋 아님)은 그대로", r["shown"][2]=="한국어 메모", r)
      await pg.evaluate("()=>{ __t.showView('list'); __t.renderAll(); }"); await pg.wait_for_timeout(300)
      r=await pg.evaluate("()=>{ const m=document.querySelector('#deckMgr'); return m?[...m.querySelectorAll('[data-ren]')].map(e=>e.value):null }")
      ok(f"{tag} #deckMgr 세트 이름 한글 없음", r is not None and r[1]=="韓国語 初級", r)
      await put(pg, st({"c0":card(0,"선생님",lang="ko")}, ui="ko", lang="ko"))
      r=await pg.evaluate("lv=>__t.presetDeckName('ko',lv)", lv)
      ok(f"{tag} ui ko 「한국어 초급」 회귀", r=="한국어 초급", r)
      await ctx.close()
    ok("페이지 오류 없음", not errs, errs[:3])
    await b.close()
  print(f"t_r1124b: {sum(R)}/{len(R)}"); raise SystemExit(0 if all(R) else 1)
asyncio.run(main())
