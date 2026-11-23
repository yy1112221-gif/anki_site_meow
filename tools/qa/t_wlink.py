# 인스타 단어 바로가기(백로그 Q): ?w=<단어>&src=ig_… — 처음 온 사람 바로 첫 판 · 쓰는 사람 카드+넣기 · 이미 있음 → 이동 · 없는 단어 → 첫 화면
import asyncio, json, urllib.parse
from playwright.async_api import async_playwright
R=[]
def ok(n,c,i=""): R.append(c); print(("✅" if c else "❌"), n, "" if c else i)
U="http://localhost:8765/index.html"
def q(w,src="ig_test"): return "?w="+urllib.parse.quote(w)+"&src="+src
CARDS={f"k{i}":dict(id=f"k{i}",lang="ja",word=w,meaning=f"뜻{i}",deck="default",due="2099-01-01",level=2,reps=2,isNew=False,lapses=0,created=i,log=[]) for i,w in enumerate(["先生","学校","猫"])}
def base(cards):
  return {"cards":cards,"meta":{"setup":1,"tutAsked":1,"loginAsked":1,"tutWant":0,"days":{"2026-11-20":True},"settings":{"ui":"ko","lang":"ja","homePet":False}}}
async def fresh(pg, w):
  await pg.goto(U); await pg.evaluate("()=>localStorage.clear()"); await pg.goto(U+q(w)); await pg.wait_for_timeout(3500)
async def user(pg, st, w):
  await pg.goto(U); await pg.evaluate("s=>localStorage.setItem('focus-vocab-v1', s)", json.dumps(st)); await pg.goto(U+q(w)); await pg.wait_for_timeout(3000)
FIRST="()=>{ const s=__t.getSES(); const it=s&&s.queue[0]; const c=it&&__t.S().cards[it.id]; return c?{w:c.word, ui:__t.S().meta.settings.ui, lang:__t.S().meta.settings.lang, n:Object.keys(__t.S().cards).length, setup:!!document.querySelector('#setupBox'), url:location.search, attr:(__t.S().meta.attr||{}), ses:!!document.querySelector('#sessionBox:not(.hidden)')}:{none:1, setup:!!document.querySelector('#setupBox'), n:Object.keys(__t.S().cards).length, url:location.search} }"
NOSCROLL="()=>document.scrollingElement.scrollHeight<=innerHeight+1"
async def main():
  async with async_playwright() as pw:
    b=await pw.chromium.launch(); errs=[]
    for W,H in [(390,844),(360,640)]:
      ctx=await b.new_context(viewport={"width":W,"height":H},locale="ko-KR"); pg=await ctx.new_page(); pg.on("pageerror",lambda e:errs.append(str(e)))
      tag=f"{W}×{H}"
      # ① 한국어 단어(눈치, 레벨 세트) — 처음 온 사람: 설정 없이 화면 일본어 + 첫 판 첫 문제가 눈치
      await fresh(pg,"눈치"); r=await pg.evaluate(FIRST)
      ok(f"{tag} 눈치: 설정 창 없이 첫 판, 첫 문제 눈치, 화면 ja·학습 ko", r.get("w")=="눈치" and r["ui"]=="ja" and r["lang"]=="ko" and not r["setup"], r)
      ok(f"{tag} 눈치: 주소창에서 w·src 지움, 유입 기록 src·w", "w=" not in r.get("url","x") and r.get("attr",{}).get("src")=="ig_test" and r.get("attr",{}).get("w")=="눈치", r)
      ok(f"{tag} 눈치: 첫 판 화면 스크롤 없음", await pg.evaluate(NOSCROLL)); await pg.screenshot(path=f"/tmp/wl_fresh_{W}.png")
      # ② 일본어 유행어(ドパガキ) — 화면 ko·학습 ja
      await fresh(pg,"ドパガキ"); r=await pg.evaluate(FIRST)
      ok(f"{tag} ドパガキ: 첫 판 첫 문제, 화면 ko·학습 ja", r.get("w")=="ドパガキ" and r["ui"]=="ko" and r["lang"]=="ja" and not r["setup"], r)
      # ③ 데이터에 없는 단어 — 평소 첫 화면(설정 창)
      for w in ["猫舌","없는단어냥"]:
        await fresh(pg,w); await pg.wait_for_timeout(500); r=await pg.evaluate(FIRST)
        ok(f"{tag} {w}(데이터에 없음): 그냥 첫 화면(설정 창), 카드 0, 주소창 정리", r.get("none") and r["setup"] and r["n"]==0 and "w=" not in r["url"], r)
      # ④ 이미 쓰는 사람 + 새 단어 → 카드 한 장 + 넣기
      await user(pg, base(CARDS), "ドパガキ")
      r=await pg.evaluate("()=>{const p=document.querySelector('#wlPop'); return p?{t:p.innerText, add:!!p.querySelector('#wlAdd')}:null}")
      ok(f"{tag} 쓰는 사람: 카드(단어·뜻) + 「단어장에 넣기」", bool(r) and "ドパガキ" in r["t"] and "도파민" in r["t"] and r["add"], r)
      r=await pg.evaluate("()=>{const r=document.querySelector('.wl-card').getBoundingClientRect(), b=[...document.querySelectorAll('.wl-btns .btn')].map(x=>x.getBoundingClientRect().height); return {t:r.top,b:r.bottom,h:innerHeight,bh:b}}")
      ok(f"{tag} 카드 창이 화면 안에 다 들어옴·버튼 한 줄", r["t"]>=0 and r["b"]<=r["h"] and max(r["bh"])<60, r); await pg.screenshot(path=f"/tmp/wl_pop_{W}.png")
      await pg.click("#wlAdd"); await pg.wait_for_timeout(300)
      r=await pg.evaluate("()=>{const S=__t.S(); const cs=Object.values(S.cards); const n=cs.find(c=>c.word==='ドパガキ'); const d=n&&S.meta.decks.find(x=>x.id===n.deck); return {n:cs.length, d:d&&d.wlink, old:['k0','k1','k2'].map(k=>S.cards[k].word+S.cards[k].meaning+S.cards[k].due).join(), first:(__t.newCandidates()[0]||{}).word, pop:!!document.querySelector('#wlPop'), saved:JSON.parse(localStorage.getItem('focus-vocab-v1')).cards[n.id]?1:0}}")
      ok(f"{tag} 넣기: 새 카드 1장(링크 단어 덱), 저장됨, 새 단어 맨 앞", r["n"]==4 and r["d"]=="ja" and r["saved"]==1 and r["first"]=="ドパガキ", r)
      ok(f"{tag} 기존 카드 그대로", r["old"]=="先生뜻02099-01-01,学校뜻12099-01-01,猫뜻22099-01-01", r)
      # ⑤ 이미 있는 단어 → 「단어장에서 보기」 → 그 카드
      cs=dict(CARDS); cs["kk"]=dict(id="kk",lang="ko",word="눈치",meaning="내 뜻",deck="default",due="2099-01-01",level=1,reps=1,isNew=False,lapses=0,created=9,log=[])
      await user(pg, base(cs), "눈치")
      r=await pg.evaluate("()=>{const p=document.querySelector('#wlPop'); return p?{go:!!p.querySelector('#wlGo'), add:!!p.querySelector('#wlAdd'), t:p.innerText}:null}")
      ok(f"{tag} 이미 있는 단어: 「단어장에서 보기」(넣기 없음, 내 뜻 그대로)", bool(r) and r["go"] and not r["add"] and "내 뜻" in r["t"], r)
      await pg.click("#wlGo"); await pg.wait_for_timeout(700)
      r=await pg.evaluate("()=>({lang:__t.S().meta.settings.lang, view:document.body.dataset.view, n:Object.keys(__t.S().cards).length, m:__t.S().cards.kk.meaning, edit:document.body.innerText.includes('내 뜻')})")
      # 검수단 R1-46-2(11-24): 링크 단어 언어 = 화면 언어(ko)면 학습 언어를 ko로 바꾸지 않음(ui ko·lang ko 모순 설정 방지)
      ok(f"{tag} 보기: 화면 ko라 학습 언어 ja 그대로, 단어장 화면, 카드 수·뜻 그대로", r["lang"]=="ja" and r["view"]=="list" and r["n"]==4 and r["m"]=="내 뜻", r)
      # ⑥ ?w 없는 평소 진입은 그대로
      await pg.goto(U); await pg.wait_for_timeout(1200)
      ok(f"{tag} ?w 없으면 카드 창 없음", not await pg.query_selector("#wlPop"))
      await ctx.close()
    # ⑦ 스페인어(tener) 처음 온 사람: 화면은 브라우저 언어 그대로
    ctx=await b.new_context(viewport={"width":390,"height":844},locale="ko-KR"); pg=await ctx.new_page(); pg.on("pageerror",lambda e:errs.append(str(e)))
    await fresh(pg,"tener"); r=await pg.evaluate(FIRST)
    ok("tener: 화면 ko·학습 es, 첫 문제 tener, 같은 단어 카드 1장", r.get("w")=="tener" and r["ui"]=="ko" and r["lang"]=="es" and not r["setup"], r)
    n=await pg.evaluate("()=>Object.values(__t.S().cards).filter(c=>c.word==='tener').length"); ok("tener 중복 카드 없음", n==1, n)
    l=await pg.evaluate("()=>__t.wlLangOf('ドパガキ')+__t.wlLangOf('눈치')+__t.wlLangOf('año')"); ok("언어 판별 ja·ko·es", l=="jakoes", l)
    await b.close()
    ok("페이지 오류 없음", not errs, errs[:3])
  print(f"t_wlink: {sum(R)}/{len(R)}"); 
  if not all(R): raise SystemExit(1)
asyncio.run(main())
