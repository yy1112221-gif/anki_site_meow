# 레벨 진단(백로그 R): 결과 유지 · 늘 주 버튼 하나 · 함정 문구 · ?diag=1 · 한 화면 · 데이터 불변
import asyncio, sys, json
from playwright.async_api import async_playwright
R=[]
def ok(n,c,i=""): R.append(c); print(("✅" if c else "❌"), n, "" if c else i)
U="http://localhost:8765/index.html"
def base(cards=None, diag=None, decks=None, ui="ko"):
  m={"setup":1,"tutAsked":1,"loginAsked":1,"tutWant":0,"days":{},"settings":{"ui":ui,"lang":"ja"}}
  if diag: m["diag"]=diag
  if decks: m["decks"]=decks
  return {"cards":cards or {},"meta":m}
CARDS={f"k{i}":dict(id=f"k{i}",lang="ja",word=w,meaning=f"뜻{i}",deck="default",due="2099-01-01",iv=3,ef=2.5,reps=2,u=0) for i,w in enumerate(["先生","学校","猫"])}
async def load(pg, st, q=""):
  await pg.goto(U); await pg.evaluate("s=>localStorage.setItem('focus-vocab-v1', s)", json.dumps(st)); await pg.goto(U+q); await pg.wait_for_timeout(1500)
  await pg.evaluate("()=>document.querySelectorAll('.sheet-bg,#pet,#riskPop,.sup-ov,#s7,#tutAsk').forEach(e=>e.remove())")
async def presets(pg):
  await pg.evaluate("()=>{ __t.showView('add'); __t.setAddPanel('preset'); }"); await pg.wait_for_function("()=>document.querySelector('#presetBox #diagBtn')", timeout=8000); await pg.wait_for_timeout(300)
async def run_diag(pg, pick):   # pick: 'all' | 'none' | 'real'(진짜 단어만)
  await pg.evaluate("()=>__t.startDiag('ja', document.querySelector('#presetBox #diagBox'), 'test')"); await pg.wait_for_timeout(300)
  for _ in range(12):
    if not await pg.query_selector("#diagNext"): break
    if pick!="none":
      await pg.evaluate("""p=>{ document.querySelectorAll('#diagBox [data-di]').forEach(b=>{ const w=b.textContent; b.click(); }); }""", pick)
    await pg.click("#diagNext"); await pg.wait_for_timeout(120)
async def main():
  async with async_playwright() as pw:
    b=await pw.chromium.launch(); errs=[]
    ctx=await b.new_context(viewport={"width":390,"height":844},locale="ko-KR"); pg=await ctx.new_page(); pg.on("pageerror",lambda e:errs.append(str(e)))
    # ① 옛 형식 저장 → 레벨 세트 화면에 카드
    await load(pg, base(CARDS, {"ja":{"date":"2026-11-20","est":"JLPT N4","rec":"n3","adj":[100,80,40,10,0]}}))
    await presets(pg)
    r=await pg.evaluate("()=>{const c=document.querySelector('#presetBox .dcard'); return c?{t:c.innerText, k:(c.querySelector('#diagGo')||{}).dataset}:null}")
    ok("옛 형식 {date,est,rec,adj} 저장도 결과 카드로 그림", bool(r) and "N4" in r["t"] and "11/20" in r["t"], r)
    ok("옛 형식: 추천 세트 없음 → 주 버튼 a(추가하고 바로 첫 판)", bool(r) and r["k"] and r["k"].get("k")=="a", r)
    # ② 진단 끝 → 새로고침 → 카드 유지, 새 키
    await load(pg, base(CARDS)); await presets(pg); await run_diag(pg, "all")
    d=await pg.evaluate("()=>__t.S().meta.diag.ja")
    ok("진단 결과에 새 키(recLabel·known·fakeHit·fakeN·at) + 옛 키 그대로", all(k in d for k in ["date","est","rec","adj","known","fakeHit","fakeN","at"]), d)
    t=await pg.inner_text("#presetBox #diagBox")
    ok("다 누르면 함정에 걸린 문구 「없는 말에 속았다냥」", "속았다냥" in t, t)
    await pg.reload(); await pg.wait_for_timeout(1500); await pg.evaluate("()=>document.querySelectorAll('.sheet-bg,#pet,#riskPop,.sup-ov,#s7').forEach(e=>e.remove())"); await presets(pg)
    ok("새로고침 뒤에도 레벨 세트 화면에 결과 카드", bool(await pg.query_selector("#presetBox .dcard #diagGo")))
    # ③ 함정 피함 문구(진짜 단어만 누름)
    await load(pg, base(CARDS)); await presets(pg)
    await pg.evaluate("()=>__t.startDiag('ja', document.querySelector('#presetBox #diagBox'), 'test')"); await pg.wait_for_timeout(300)
    for _ in range(12):
      if not await pg.query_selector("#diagNext"): break
      await pg.evaluate("""async()=>{ const idx=await __t.presetIndex(), F=new Set(idx.diag.ja.fake.map(w=>Array.isArray(w)?w[0]:w));
        document.querySelectorAll('#diagBox [data-di]').forEach(b=>{ const w=b.childNodes[0].textContent; if(!F.has(w)) b.click(); }); }""")
      await pg.click("#diagNext"); await pg.wait_for_timeout(120)
    t=await pg.inner_text("#presetBox #diagBox")
    ok("함정 단어 다 피하면 「함정 단어 n개 중 n개 피함 🐾」", "피함" in t, t)
    # ④ 경우 a·b·c·d 주 버튼 + a·b 누르면 학습 판 시작
    cases=[("a",{"ja":{"date":"2026-11-20","est":"JLPT N4","rec":"n3","adj":[100,80,40,10,0]}},None),
           ("b",{"ja":{"date":"2026-11-20","est":"JLPT N4","rec":"n3","adj":[100,80,40,10,0]}},"have"),
           ("c",{"ja":{"date":"2026-11-20","est":"JLPT N1","rec":None,"adj":[100,100,95,90,80]}},None),
           ("d",{"ja":{"date":"2026-11-20","est":"입문","rec":"n5","adj":[10,0,0,0,0]}},None)]
    for k,dg,have in cases:
      st=base(CARDS, dg)
      if have:
        st["meta"]["decks"]=[{"id":"default","name":"","on":True},{"id":"dn3","name":"N3","on":False,"preset":"ja-n3","cursor":0}]
        st["cards"]=dict(CARDS, **{f"n{i}":dict(id=f"n{i}",lang="ja",word=w,meaning=f"m{i}",deck="dn3",due="",iv=0,ef=2.5,reps=0,u=0) for i,w in enumerate(["政治","経済","環境","技術","社会","文化"])})
      await load(pg, st); await presets(pg)
      r=await pg.evaluate("()=>{const g=document.querySelector('#presetBox .dcard #diagGo'); return g?g.dataset.k:null}")
      ok(f"경우 {k}: 주 버튼 있음(kind={k})", r==k, r)
      if k in ("a","b"):
        await pg.click("#presetBox .dcard #diagGo"); await pg.wait_for_timeout(3500)
        s=await pg.evaluate("()=>({ses:!!__t.SES&&!!(__t.SES()||{}).queue, box:!document.querySelector('#sessionBox').classList.contains('hidden'), dk:__t.S().meta.decks.map(d=>[d.preset,d.on])})")
        ok(f"경우 {k}: 누르면 학습 판 시작", s["box"], s)
        if k=="b": ok("경우 b: 그 단어장 켬", ["ja-n3",True] in s["dk"], s)
      if k=="c": ok("경우 c: 유행어 세트 추천 줄", bool(await pg.query_selector("#presetBox .dcard #diagSl")))
    # ⑤ ?diag=1 → 온보딩에서 바로 진단
    await load(pg, base(), "?diag=1"); await pg.wait_for_timeout(1500)
    ok("?diag=1 로 오면 진단 시작", bool(await pg.query_selector("#diagBox .dpg")))
    ok("?diag=1 은 주소창에서 지움", "diag" not in pg.url, pg.url)
    # 온보딩: 이미 진단한 언어면 카드
    await load(pg, base(None, {"ja":{"date":"2026-11-20","est":"JLPT N4","rec":"n3","adj":[100,80,40,10,0]}})); await pg.wait_for_timeout(800)
    ok("온보딩: 이미 진단했으면 결과 카드", bool(await pg.query_selector("#sessionStart .dcard #diagGo")))
    await ctx.close()
    # ⑥ 390·360 진단 페이지·결과 카드가 화면 높이 안에
    for W,H in [(390,844),(360,640)]:
      ctx=await b.new_context(viewport={"width":W,"height":H},locale="ko-KR",has_touch=True,is_mobile=True); pg=await ctx.new_page(); pg.on("pageerror",lambda e:errs.append(str(e)))
      await load(pg, base(CARDS)); await presets(pg)
      await pg.evaluate("()=>__t.startDiag('ja', document.querySelector('#presetBox #diagBox'), 'test')"); await pg.wait_for_timeout(500)
      h=await pg.evaluate("()=>Math.round(document.querySelector('#diagBox .dpg').getBoundingClientRect().height)")
      ok(f"{W}×{H} 진단 페이지가 한 화면 안({h}px)", h<=H-100, h)
      await pg.screenshot(path=f"/tmp/diag_pg_{W}.png")
      await run_diag(pg, "real"); await pg.wait_for_timeout(600)
      h=await pg.evaluate("()=>Math.round(document.querySelector('#diagBox .dcard').getBoundingClientRect().height)")
      ok(f"{W}×{H} 결과 카드가 한 화면 안({h}px)", h<=H-120, h)
      await pg.evaluate("()=>document.querySelector('#diagBox .dcard').scrollIntoView({block:'center'})"); await pg.wait_for_timeout(500)
      await pg.screenshot(path=f"/tmp/diag_res_{W}.png")
      await ctx.close()
    # ⑦ 카드·덱 데이터 불변(진단만 하고 버튼 안 누름)
    ctx=await b.new_context(viewport={"width":390,"height":844}); pg=await ctx.new_page()
    await load(pg, base(CARDS)); before=await pg.evaluate("()=>JSON.stringify([__t.S().cards, __t.S().meta.decks])")
    await presets(pg); await run_diag(pg, "real")
    after=await pg.evaluate("()=>JSON.stringify([__t.S().cards, __t.S().meta.decks])")
    ok("진단만 하면 카드·덱 데이터 그대로", before==after)
    ok("페이지 오류 없음", not errs, errs[:3])
    await b.close()
  print(f"t_diag: {sum(R)}/{len(R)}"); sys.exit(0 if all(R) else 1)
asyncio.run(main())
