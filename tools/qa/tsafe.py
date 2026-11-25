# 데이터 안전 테스트: ①냥이 u 갱신 ②결제·꾸미기 병합 ④학습일 병합 ⑤탭 충돌 ⑥백업 회전 ⑦가져오기 u
import asyncio, json, sys
from playwright.async_api import async_playwright
B="http://localhost:8765/index.html"; R=[]
def ok(name, cond, info=""): R.append(cond); print(("✅" if cond else "❌"), name, "" if cond else info)
SEED=r"""() => localStorage.setItem("focus-vocab-v1", JSON.stringify({cards:{c1:{id:"c1",lang:"ja",word:"先生",meaning:"선생님",u:1000,due:"2026-11-20"}}, meta:{setup:1,tutAsked:1,loginAsked:1,days:{"2026-11-18":true}, pet:{inv:{churu:3},u:500,kcal:10,lv:1,coins:5}, settings:{ui:"ko",lang:"ja"}}}))"""
async def main():
  async with async_playwright() as pw:
    b=await pw.chromium.launch(); ctx=await b.new_context(locale="ko-KR"); A=await ctx.new_page()
    errs=[]; A.on("pageerror",lambda e: errs.append(str(e)))
    await A.goto(B); await A.evaluate(SEED); await A.reload(); await A.wait_for_timeout(2500)
    # ① 간식이 바뀌면 u가 올라감
    u0=await A.evaluate("window.__t.S().meta.pet.u")
    u1=await A.evaluate("() => { const S=window.__t.S(); S.meta.pet.inv.cake=(S.meta.pet.inv.cake||0)+10; window.__t.save(); return S.meta.pet.u; }")
    ok("① 간식 지급 후 냥이 u 갱신", u1>u0, f"{u0}->{u1}")
    u2=await A.evaluate("() => { window.__t.save(); return window.__t.S().meta.pet.u; }")
    ok("① 바뀐 게 없으면 u 그대로", u2==u1)
    # ① 옛 원격 냥이가 새 지급을 덮지 않음
    inv=await A.evaluate("() => { window.__t.mergeData({cards:{}, meta:{pet:{inv:{churu:3},u:900}}}); return window.__t.S().meta.pet.inv.cake; }")
    ok("① 옛 원격 냥이가 산 간식을 못 덮음", inv==10, inv)
    # ② 결제·꾸미기·후원 병합
    r=await A.evaluate("""() => { const S=window.__t.S(); S.meta.paid={o1:{id:"snk_s"}}; S.meta.cos={own:{hat:1},on:"hat"}; S.meta.sup=1;
      window.__t.mergeData({cards:{}, meta:{paid:{o2:{id:"cap"}}, cos:{own:{cap:1},on:"cap"}, sup:2, nick:{name:"냥냥",key:"k1"}, payPend:{orderId:"x"}}});
      return {paid:Object.keys(S.meta.paid).sort(), own:Object.keys(S.meta.cos.own).sort(), on:S.meta.cos.on, sup:S.meta.sup, nick:S.meta.nick && S.meta.nick.name, pp:S.meta.payPend}; }""")
    ok("② 결제 기록 합침", r["paid"]==["o1","o2"], r); ok("② 꾸미기 합침(착용은 이 기기)", r["own"]==["cap","hat"] and r["on"]=="hat", r)
    ok("② 후원 등급 큰 쪽", r["sup"]==2, r); ok("② 없는 닉네임은 받음", r["nick"]=="냥냥", r); ok("② 결제 대기는 안 받음", r["pp"] is None, r)
    # ④ 같은 날: 공부(true)가 얼림을 이김
    d=await A.evaluate("""() => { const S=window.__t.S(); S.meta.days["2026-11-19"]="freeze"; window.__t.mergeData({cards:{}, meta:{days:{"2026-11-19":true,"2026-11-17":true}}}); return [S.meta.days["2026-11-19"], S.meta.days["2026-11-17"], S.meta.days["2026-11-18"]]; }""")
    ok("④ 학습일 병합", d==[True,True,True], d)
    # 카드 병합: 새 것이 이김, 삭제 기록 존중
    c=await A.evaluate("""() => { const S=window.__t.S(); window.__t.mergeData({cards:{c1:{id:"c1",lang:"ja",word:"先生",meaning:"OLD",u:1}, c2:{id:"c2",lang:"ja",word:"学校",u:5}}, meta:{deleted:{c2:10}}}); return [S.cards.c1.meaning, !!S.cards.c2]; }""")
    ok("카드 병합(새 것 우선·삭제 존중)", c==["선생님",False], c)
    await A.evaluate("window.__t.save()")
    # ⑤ 탭 두 개: 옛 탭 B가 저장해도 A의 새 카드가 남음
    Bp=await ctx.new_page(); Bp.on("pageerror",lambda e: errs.append(str(e))); await Bp.goto(B); await Bp.wait_for_timeout(2500)
    await A.evaluate("""() => { const S=window.__t.S(); S.cards.n1={id:"n1",lang:"ja",word:"新しい",meaning:"새",u:Date.now()}; window.__t.save(); }""")
    await Bp.wait_for_timeout(500)
    await Bp.evaluate("""() => { const S=window.__t.S(); S.cards.n2={id:"n2",lang:"ja",word:"古い",meaning:"옛",u:Date.now()}; window.__t.save(); }""")
    final=await A.evaluate("Object.keys(JSON.parse(localStorage.getItem('focus-vocab-v1')).cards).sort()")
    ok("⑤ 탭 충돌 없음(두 탭 카드 모두 보존)", "n1" in final and "n2" in final, final)
    # ⑥ 백업 회전
    await A.evaluate("""() => localStorage.setItem("focus-vocab-v1-bak", JSON.stringify({d:"2026-01-01", raw:"{}"}))""")
    await A.reload(); await A.wait_for_timeout(1500)
    bk=await A.evaluate("[!!localStorage.getItem('focus-vocab-v1-bak2'), JSON.parse(localStorage.getItem('focus-vocab-v1-bak')).d]")
    ok("⑥ 백업 2일치 이상 보관", bk[0] and bk[1]!="2026-01-01", bk)
    # ⑦ 가져오기는 u 갱신
    iu=await A.evaluate("""() => { document.querySelector('#importBox').value = JSON.stringify([{word:"先生",lang:"ja",meaning:"가져옴",u:1}]); document.querySelector('#btnImport').click(); const c=Object.values(window.__t.S().cards).find(c=>c.word==="先生"); return [c.meaning, c.u > 1e12]; }""")
    ok("⑦ 가져온 카드 u 갱신", iu==["가져옴",True], iu)
    # ⑧ 프로모션(오늘의 간식·수험생·막차) 기록 병합이 학습일·카드를 안 건드림, 날짜는 늦은 쪽
    pr=await A.evaluate("""() => { const S=window.__t.S(), d0=JSON.stringify(S.meta.days), c0=Object.keys(S.cards).length; S.meta.promo={ds:"2026-12-01",late:"2026-12-03"};
      window.__t.mergeData({cards:{}, meta:{promo:{ds:"2026-12-02",late:"2026-11-30",exam:"2026-12-01"}}}); return [S.meta.promo.ds, S.meta.promo.late, S.meta.promo.exam, JSON.stringify(S.meta.days)===d0, Object.keys(S.cards).length===c0]; }""")
    ok("⑧ 프로모션 병합(늦은 날짜)·학습일·카드 그대로", pr==["2026-12-02","2026-12-03","2026-12-01",True,True], pr)
    ok("페이지 오류 없음", not errs, errs[:3])
    await b.close()
  print("결과:", "통과" if all(R) else "실패"); sys.exit(0 if all(R) else 1)
asyncio.run(main())
