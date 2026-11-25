# 시간 기반 프로모션(11-25): 막차 2배·새벽 안내·오늘의 간식(한국 얼리 집사/일본 事前登録)·수험생 세트+머리띠·기간 자동 켜고 끄기 · 학습일·연속 기록 보존
import asyncio, json, re, sys
from datetime import datetime, timezone, timedelta
from playwright.async_api import async_playwright
B="http://localhost:8765/index.html"; R=[]; KST=timezone(timedelta(hours=9))
def ok(n,c,i=""): R.append(bool(c)); print(("✅" if c else "❌"), n, "" if c else i)
async def page(b, when, ui="ko", lang="ja", days=None, extra=None):
  ctx=await b.new_context(locale="ko-KR", viewport={"width":390,"height":844}); await ctx.route(re.compile(r"(tosspayments|supabase\.co)"), lambda r: r.abort())
  await ctx.clock.set_fixed_time(datetime(*when, tzinfo=KST)); pg=await ctx.new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)))
  meta={"setup":1,"tutAsked":1,"loginAsked":1,"stepv":1,"days":days or {},"settings":{"ui":ui,"lang":lang,"homePet":False},"pet":{"inv":{"kari":2},"coins":7,"kcal":5,"lv":1,"u":1}}
  if extra: meta.update(extra)
  await pg.goto(B); await pg.evaluate("s=>localStorage.setItem('focus-vocab-v1', s)", json.dumps({"cards":{"c1":{"id":"c1","lang":lang,"word":"先生","meaning":"선생님","u":1,"due":"2026-11-20"}},"meta":meta}))
  await pg.goto(B); await pg.wait_for_timeout(1500); return ctx, pg, errs
J=lambda pg, s: pg.evaluate(s)
async def main():
  async with async_playwright() as pw:
    b=await pw.chromium.launch()
    # 1) 기간 전(11-25): 아무것도 안 켜짐
    ctx,pg,E=await page(b,(2026,11,25,14,0))
    ok("11-25 한국: 얼리·수험생 꺼짐", await J(pg,"()=>[window.__t.prOn('early'),window.__t.prOn('exam')]")==[False,False])
    ok("11-25 홈 말풍선 프로모션 없음", await J(pg,"()=>window.__t.prHomeLine()") is None)
    ok("11-25 설정 이벤트 줄 비어 있음", await J(pg,"()=>{window.__t.showView('how'); return document.querySelector('#promoSet').innerHTML}")=="")
    ok("오류 없음(11-25)", not E, E[:3]); await ctx.close()
    # 2) 한국 11-26 14시: 오늘의 간식 1개 고르기 + 산타 모자, 하루 한 번
    days={"2026-11-24":True,"2026-11-25":"freeze"}
    ctx,pg,E=await page(b,(2026,11,26,14,0),days=days)
    l=await J(pg,"()=>window.__t.prHomeLine()"); ok("11-26 한국: 홈 말풍선 = 얼리 집사 간식", l and l["a"]=="snack", l)
    ok("홈 화면에 눌리는 말풍선", await J(pg,"()=>{window.__t.showView('today'); window.__t.renderAll(); return !!document.querySelector('.hv2-say.pr-ev[data-pr=snack]')}"))
    await J(pg,"()=>document.querySelector('.hv2-say.pr-ev').click()"); await pg.wait_for_timeout(300)
    n=await J(pg,"()=>document.querySelectorAll('#prPop [data-sn]').length"); ok("간식 고르기 창(골드·충전 간식 제외)", n==len([1 for _ in range(10)]), n)
    await J(pg,"()=>document.querySelector('#prPop [data-sn=lob]').click()"); await pg.wait_for_timeout(400)
    st=await J(pg,"()=>{const S=window.__t.S(); return {lob:S.meta.pet.inv.lob||0, kari:S.meta.pet.inv.kari, ds:S.meta.promo.ds, early:S.meta.promo.early, santa:!!(S.meta.cos&&S.meta.cos.own.santa_hat), hat:S.meta.cos.hat, coins:S.meta.pet.coins, days:S.meta.days}}")
    ok("고른 간식 1개 지급·기존 간식·코인 그대로", st["lob"]==1 and st["kari"]==2 and st["coins"]==7, st)
    ok("받은 날 기록 + 첫 수령 = 얼리 시작 + 산타 모자", st["ds"]==st["early"] and st["santa"] and st["hat"]=="santa_hat", st)
    ok("학습일 기록 안 건드림", st["days"]==days, st["days"])
    ok("오늘 두 번은 못 받음", await J(pg,"()=>window.__t.prSnackDue()")==False)
    await J(pg,"()=>window.__t.prSnackPick()"); await pg.wait_for_timeout(200); ok("두 번째는 창 안 열림", await J(pg,"()=>!document.querySelector('#prPop [data-sn]')"))
    # 수험생: 체크해야 버튼, 세트 + 머리띠
    await J(pg,"()=>window.__t.prExam()"); await pg.wait_for_timeout(200)
    ok("수험생 창: 체크 전 받기 버튼 꺼짐", await J(pg,"()=>document.querySelector('#prExamGo').disabled"))
    ok("수험생 창에 결제·가격 문구 없음", await J(pg,"()=>!/[₩¥원円]|결제|구매|購入/.test(document.querySelector('#prPop').textContent)"))
    await J(pg,"()=>{const c=document.querySelector('#prExamChk'); c.checked=true; c.dispatchEvent(new Event('change')); document.querySelector('#prExamGo').click();}"); await pg.wait_for_timeout(1500)
    ex=await J(pg,"()=>{const S=window.__t.S(); const d=window.__t.decks().find(d=>d.preset==='ja-travel'); return {exam:S.meta.promo.exam, hachi:!!S.meta.cos.own.hachi, hat:S.meta.cos.hat, deck:d&&d.name, n:Object.values(S.cards).filter(c=>c.deck===(d&&d.id)).length, c1:S.cards.c1.meaning}}")
    ok("수험생: 일본 여행 단어 세트 + 합격 머리띠", ex["exam"] and ex["hachi"] and ex["hat"]=="hachi" and ex["deck"]=="일본 여행 생존 단어" and ex["n"]>=20, ex)
    ok("기존 카드 그대로", ex["c1"]=="선생님", ex)
    await J(pg,"async()=>{ try{ await window.__t.renderPresets(); }catch(_){} }"); await pg.wait_for_timeout(600)
    ok("여행 세트는 일반 단어장 목록엔 안 보임", await J(pg,"()=>!document.querySelector('[data-mx=travel]')"))
    ok("설정 이벤트 줄: 받은 건 ✓", await J(pg,"()=>{window.__t.showView('how'); const t=document.querySelector('#promoSet').textContent; return /오늘의 간식 ✓/.test(t) && /수험생 응원 ✓/.test(t)}"))
    ok("오류 없음(한국)", not E, E[:3]); await ctx.close()
    # 3) 막차 타임 23:30: 오늘 목표 전이면 2배, 같은 사람 14시와 비교
    async def grant(h):
      c,p,e=await page(b,(2026,12,2,h,30),days={"2026-12-01":True}); r=await J(p,"()=>{const g=window.__t.petGrant(10,0); return {n:g.n, late:!!g.late, line:(window.__t.prHomeLine()||{}).a||'', st:window.__t.S().meta.promo.late||''}}"); await c.close(); return r, e
    a,e1=await grant(14); z,e2=await grant(23)
    ok("막차(23시): 보상 간식 2배", z["n"]==a["n"]*2 and z["late"] and not a["late"], [a,z])
    ok("막차 받은 날 기록(다음 날 재방문 측정용)", z["st"]=="2026-12-02" and a["st"]=="", [a,z])
    c,p,e3=await page(b,(2026,12,2,23,10),days={"2026-12-01":True}); ok("23시 + 오늘 목표 전 = 막차 말풍선", (await J(p,"()=>window.__t.prHomeLine()"))["a"]=="go"); await c.close()
    c,p,e4=await page(b,(2026,12,2,23,10),days={"2026-12-01":True,"2026-12-02":True}); l=await J(p,"()=>window.__t.prHomeLine()"); ok("오늘 목표 끝낸 사람은 막차 말풍선 없음", not l or "막차" not in l["t"], l); await c.close()
    # 4) 새벽(01:30): 앱 하루는 아직 전날 → 연속 기록 안내, 학습일은 저장 방식 그대로
    c,p,e5=await page(b,(2026,12,3,1,30),days={"2026-12-01":True})
    r=await J(p,"()=>({td:window.__t.today(), sk:window.__t.streak(), l:window.__t.prHomeLine()})"); ok("01:30은 앱 하루로 전날(12-02) · 연속 1 · 🌙 안내", r["td"]=="2026-12-02" and r["sk"]==1 and r["l"] and "🌙" in r["l"]["t"], r); await c.close()
    # 5) 일본: 12-05 事前登録 → 구매 의향 → 오늘의 간식 / 엔화 결제 버튼 → 사전등록 창
    c,p,E=await page(b,(2026,12,5,12,0),ui="ja",lang="ko")
    ok("일본 12-05: 수험생(2/20~)은 꺼짐·얼리는 켜짐", await J(p,"()=>[window.__t.prOn('early'),window.__t.prOn('exam')]")==[True,False])
    ok("등록 전엔 간식 없음 · 말풍선 = 事前登録", await J(p,"()=>!window.__t.prSnackDue() && window.__t.prHomeLine().a==='prereg'"))
    await J(p,"()=>window.__t.payOpen('snk_s')"); await p.wait_for_timeout(300); ok("엔화 결제 누르면 事前登録 창", await J(p,"()=>!!document.querySelector('#prRegGo')"))
    ok("의향 고르기 전엔 등록 버튼 꺼짐", await J(p,"()=>document.querySelector('#prRegGo').disabled"))
    await J(p,"()=>{document.querySelector('[data-in=maybe]').click(); document.querySelector('#prRegGo').click();}"); await p.wait_for_timeout(1300)
    j=await J(p,"()=>{const S=window.__t.S(); return {jreg:S.meta.promo.jreg, intent:S.meta.promo.intent, santa:!!S.meta.cos.own.santa_hat, due:window.__t.prSnackDue(), pop:!!document.querySelector('#prPop [data-sn]')}}")
    ok("事前登録 + 의향 저장 + サンタ帽子 + 바로 오늘의 간식 창", j["jreg"]=="2026-12-05" and j["intent"]=="maybe" and j["santa"] and j["due"] and j["pop"], j)
    ok("오류 없음(일본)", not E, E[:3]); await c.close()
    c,p,E=await page(b,(2027,2,21,12,0),ui="ja",lang="ko"); ok("일본 2/21: 受験生応援 켜짐", await J(p,"()=>window.__t.prOn('exam')")); await c.close()
    c,p,E=await page(b,(2026,12,5,12,0),ui="ja",lang="ko",extra={"by":2015}); await J(p,"()=>window.__t.prPrereg('t')"); await p.wait_for_timeout(200)
    ok("만 14세 미만: 구매 의향 질문 없음·바로 등록 가능", await J(p,"()=>!document.querySelector('[data-in]') && !document.querySelector('#prRegGo').disabled")); await c.close()
    c,p,E=await page(b,(2027,1,1,12,0),ui="ko"); ok("한국 1/1: 얼리·수험생 자동 꺼짐", await J(p,"()=>[window.__t.prOn('early'),window.__t.prOn('exam')]")==[False,False]); await c.close()
    # 6) 동기화 병합: 늦은 날짜가 이김(다른 기기에서 받은 오늘의 간식 또 안 받음) · 학습일 그대로
    c,p,E=await page(b,(2026,12,10,12,0),days={"2026-12-09":True},extra={"promo":{"ds":"2026-12-08","early":"2026-11-30"}})
    m=await J(p,"()=>{window.__t.mergeData({cards:{}, meta:{promo:{ds:'2026-12-10', exam:'2026-12-01'}, days:{'2026-12-07':true}}}); const S=window.__t.S(); return {p:S.meta.promo, due:window.__t.prSnackDue(), days:S.meta.days}}")
    ok("병합: ds 늦은 쪽·없던 값 받음·내 값 유지", m["p"]["ds"]=="2026-12-10" and m["p"]["exam"]=="2026-12-01" and m["p"]["early"]=="2026-11-30" and not m["due"], m)
    ok("병합: 학습일 두 기기 합침(프로모션 영향 없음)", m["days"]=={"2026-12-07":True,"2026-12-09":True}, m["days"])
    await c.close(); await b.close()
  print(f"\n{sum(R)}/{len(R)}"); sys.exit(0 if all(R) else 1)
asyncio.run(main())
