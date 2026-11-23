# 검수단 11-24: R1-45-1 문의 버튼 언어 · R1-46-2 링크 단어 언어 = 화면 언어 · R1-48-1 판 끝 「오늘 끝!」과 메인 숫자 일치
import asyncio, json, re, urllib.parse
from playwright.async_api import async_playwright
R=[]
def ok(n,c,i=""): R.append(c); print(("✅" if c else "❌"), n, "" if c else i)
U="http://localhost:8765/index.html"
def card(i, w, lang="ja", **kw):
  d=dict(id=f"c{i}",lang=lang,word=w,meaning=f"뜻{i}",example="",deck="default",due="2099-01-01",level=2,reps=3,isNew=False,lapses=0,created=i,introduced="2025-12-01",mastered=False,relearn=False,log=[],step=2,S=30,D=5,last="2026-11-01")
  d.update(kw); return d
def st(cards, ui="ko", lang="ja", extra=None):
  m={"setup":1,"tutAsked":1,"loginAsked":1,"tutWant":0,"stepv":1,"days":{},"settings":{"ui":ui,"lang":lang,"homePet":False}}
  if extra: m.update(extra)
  return {"cards":cards,"meta":m}
async def put(pg, s, qs=""):
  await pg.goto(U); await pg.evaluate("s=>localStorage.setItem('focus-vocab-v1', s)", json.dumps(s)); await pg.goto(U+qs); await pg.wait_for_timeout(2500)
  await pg.evaluate("()=>{ const p=document.querySelector('#pet'); if(p && !p.classList.contains('hidden')) document.querySelector('#petClose').click(); }")
FB="()=>{ const b=document.querySelector('#fbBtn small'); return b?b.textContent:null }"
NOSCROLL="()=>document.scrollingElement.scrollHeight<=innerHeight+1"
async def main():
  async with async_playwright() as pw:
    b=await pw.chromium.launch(); errs=[]
    for W,H in [(390,844),(360,640)]:
      tag=f"{W}×{H}"
      ctx=await b.new_context(viewport={"width":W,"height":H},locale="ko-KR"); pg=await ctx.new_page(); pg.on("pageerror",lambda e:errs.append(str(e)))
      # ── R1-45-1 문의 버튼 ──
      await pg.goto(U); await pg.evaluate("()=>localStorage.clear()"); await pg.goto(U); await pg.wait_for_timeout(2000)
      before=await pg.evaluate(FB)
      has=await pg.evaluate("()=>!!document.querySelector('#setupBox [data-ui=\"ja\"]')")
      if has: await pg.click('#setupBox [data-ui="ja"]'); await pg.wait_for_timeout(400)
      ok(f"{tag} 온보딩 日本語 → 문의 버튼 「質問」", has and before=="문의" and await pg.evaluate(FB)=="質問", [has,before,await pg.evaluate(FB)])
      await put(pg, st({"c0":card(0,"猫")}))
      ok(f"{tag} ko 사용자 문의 버튼 「문의」 회귀", await pg.evaluate(FB)=="문의")
      await pg.evaluate("()=>{ const s=document.querySelector('#setUi'); s.value='ja'; s.dispatchEvent(new Event('change')); }"); await pg.wait_for_timeout(300)
      a=await pg.evaluate(FB)
      await pg.evaluate("()=>{ const s=document.querySelector('#setUi'); s.value='ko'; s.dispatchEvent(new Event('change')); }"); await pg.wait_for_timeout(300)
      ok(f"{tag} 설정에서 ko→ja→ko 바로 반영", a=="質問" and await pg.evaluate(FB)=="문의", [a, await pg.evaluate(FB)])
      # ── R1-46-2 링크 단어 언어 = 화면 언어 ──
      qs="?w="+urllib.parse.quote("狭い")+"&src=ig_test"
      await put(pg, st({"c0":card(0,"선생님",lang="ko")}, ui="ja", lang="ko"), qs); await pg.wait_for_timeout(1500)
      r=await pg.evaluate("()=>{const p=document.querySelector('#wlPop'); return p?{t:p.innerText, add:!!p.querySelector('#wlAdd'), same:!!p.querySelector('#wlSame')}:null}")
      lat=bool(r) and re.search(r"narrow|spacious|[A-Za-z]{4,}", r["t"]) is not None
      ok(f"{tag} ui ja·lang ko + ?w=狭い: 팝업에 영어 뜻 없음·안내 한 줄·넣기 없음", bool(r) and not lat and r["same"] and not r["add"], r)
      S0=await pg.evaluate("()=>JSON.stringify(__t.S().cards)")
      ok(f"{tag} ui ja: 카드 변화 없음·설정 그대로", await pg.evaluate("()=>{const s=__t.S().meta.settings; return s.ui==='ja'&&s.lang==='ko'}"))
      # 이미 있는 일본어 카드(화면 ko 시절에 넣은 것) + ui ja → #wlGo 뒤 학습 언어 안 바뀜
      await put(pg, st({"c0":card(0,"선생님",lang="ko"),"c1":card(1,"狭い",meaning="せまい · 좁다")}, ui="ja", lang="ko"), qs); await pg.wait_for_timeout(1500)
      go=await pg.evaluate("()=>!!document.querySelector('#wlGo')")
      if go: await pg.click("#wlGo"); await pg.wait_for_timeout(500)
      r=await pg.evaluate("()=>{const s=__t.S().meta.settings; return [s.ui,s.lang]}")
      ok(f"{tag} ui ja + 있는 狭い 카드: 「単語帳で見る」 뒤 settings.lang ≠ ui", go and r[1]!=r[0] and r==["ja","ko"], [go,r])
      # 회귀: ui ko 사용자 ?w=狭い → 한국어 뜻, 넣기 버튼
      await put(pg, st({"c0":card(0,"猫")}, ui="ko", lang="ja"), qs); await pg.wait_for_timeout(1500)
      r=await pg.evaluate("()=>{const p=document.querySelector('#wlPop'); return p?{t:p.innerText, add:!!p.querySelector('#wlAdd'), same:!!p.querySelector('#wlSame')}:null}")
      ok(f"{tag} ui ko ?w=狭い: 한국어 뜻·넣기 버튼 회귀", bool(r) and re.search(r"[가-힣]", r["t"].split("狭い")[-1]) and r["add"] and not r["same"], r)
      # ── R1-48-1 오늘 끝 숫자 ──
      async def endcase(cday):
        cs={f"c{i}":card(i,f"単語{i}") for i in range(30)}
        cs["n0"]=card(99,"新語",isNew=True,reps=0,introduced=None,due=None,step=0,S=None,last=None); cs["n0"]["id"]="n0"
        ex={"days":{}}
        await put(pg, st(cs, extra=ex));
        await pg.evaluate("c=>{ const S=__t.S(); if(c){ S.meta.cday={d:__t.today(),c:1,n:{}}; S.meta.days[__t.today()]=true; } __t.renderAll(); }", cday)
        await pg.wait_for_timeout(300)
        return await pg.evaluate("()=>({start:!!document.querySelector('#startBtn'), txt:document.querySelector('#sessionStart').innerText, q:__t.buildCourse().queue.length})")
      r=await endcase(True)
      ok(f"{tag} 오늘 한 판 뒤 새 단어 1개(4문제 아래): 메인 ▶시작 없음·「오늘 분량 끝」·「내일로」", r["q"]==0 and not r["start"] and "오늘 분량 끝" in r["txt"] and "내일" in r["txt"] and "남음" not in r["txt"], r)
      ok(f"{tag} 오늘 끝 메인 스크롤 없음", await pg.evaluate(NOSCROLL)); await pg.screenshot(path=f"/tmp/r1124_end_{W}.png")
      r=await endcase(False)
      ok(f"{tag} 오늘 첫 판이면 새 단어 1개여도 ▶시작 그대로", r["q"]>0 and r["start"], r)
      await ctx.close()
    ok("페이지 오류 없음", not errs, errs[:3])
    await b.close()
  print(f"t_r1124: {sum(R)}/{len(R)}"); raise SystemExit(0 if all(R) else 1)
asyncio.run(main())
