# 한 화면 원칙 테스트(백로그 K): 홈 화면이 390×844·360×640에서 스크롤 없이 들어가고, 홈 카드가 아래 고정 메뉴에 가리지 않는지
import asyncio, sys, json, datetime
from playwright.async_api import async_playwright
R=[]
def ok(n,c,i=""): R.append(c); print(("✅" if c else "❌"), n, "" if c else i)
def ds(d): return (datetime.datetime.now(datetime.timezone.utc)-datetime.timedelta(days=d, hours=4)).strftime("%Y-%m-%d")
WS=["先生","学校","働く","食べる","飲む","行く","来る","見る","聞く","話す","読む","書く","買う","売る","会う","待つ","持つ","立つ","座る","歩く","走る","泳ぐ","休む","遊ぶ","住む","死ぬ","呼ぶ","飛ぶ","選ぶ","運ぶ"]
def state(kind, ui="ko"):
  due = ds(2) if kind=="due" else ds(-1)
  cards={} if kind=="empty" else {f"a{i}":dict(id=f"a{i}",lang="ja",word=w,meaning=f"뜻{i}",deck="default",ex="",due=due,iv=3,ef=2.5,reps=(0 if kind=="new" else 2),u=0) for i,w in enumerate(WS)}
  days={ds(i):{"n":10,"ok":8} for i in range(1,9)}
  return {"cards":cards,"meta":{"days":days,"setup":1,"tutAsked":1,"loginAsked":1,"tutWant":0,"settings":{"ui":ui,"lang":"ja"}}}
CASES=[("복습 있음","due","ko"),("오늘 할 것 없음","none","ko"),("카드 없음","empty","ko"),("일본어 화면","due","ja")]
async def main():
  async with async_playwright() as pw:
    b=await pw.chromium.launch(); errs=[]
    for W,H in [(390,844),(360,640)]:
      ctx=await b.new_context(viewport={"width":W,"height":H},locale="ko-KR",has_touch=True,is_mobile=True)
      pg=await ctx.new_page(); pg.on("pageerror",lambda e:errs.append(str(e)))
      await pg.goto("http://localhost:8765/index.html")
      for name,kind,ui in CASES:
        await pg.evaluate("s=>localStorage.setItem('focus-vocab-v1', s)", json.dumps(state(kind,ui))); await pg.reload(); await pg.wait_for_timeout(1800)
        await pg.evaluate("() => { document.querySelectorAll('.sheet-bg,#pet,#riskPop,.sup-ov,#s7').forEach(e=>e.remove()); window.__t.showView('today'); }")
        await pg.wait_for_timeout(500)
        r=await pg.evaluate("""()=>{ const nav=document.querySelector('nav.subnav'), card=document.querySelector('#sessionStart');
          const nt=nav&&getComputedStyle(nav).display!=='none'?nav.getBoundingClientRect().top:innerHeight;
          return {sh:document.scrollingElement.scrollHeight, ih:innerHeight, cb:Math.round(card.getBoundingClientRect().bottom), nt:Math.round(nt)}; }""")
        ok(f"홈 {W}×{H} {name}: 스크롤 없음", r["sh"]<=r["ih"]+2, r)
        ok(f"홈 {W}×{H} {name}: 카드가 아래 메뉴에 안 가림", r["cb"]<=r["nt"]+2, r)
        r=await pg.evaluate("""()=>{ const g=document.querySelector('#sessionStart .hv2-fgo'), f=g&&g.closest('.hv2-feed'), b=document.querySelector('#sessionStart .hv2-say .bubble');
          const o={}; if(g&&f){ const a=g.getBoundingClientRect(), c=f.getBoundingClientRect(); o.fit=a.left>=c.left-1&&a.right<=c.right+1&&g.scrollWidth<=g.clientWidth+1; }
          if(b&&!b.classList.contains('slam')) o.clip=getComputedStyle(b).overflowX; return o; }""")
        if "fit" in r: ok(f"홈 {W}×{H} {name}: 간식 카드 이름이 카드 안에", r["fit"], r)
        if "clip" in r: ok(f"홈 {W}×{H} {name}: 말풍선 셋째 줄 안 비침(clip)", r["clip"]=="clip", r)
      # 냥이 화면(백로그 L): 겹침 없음 · 스크롤 없음
      st=state("due"); st["meta"]["pet"]={"inv":{"kari":3,"nibo":2,"sasa":1,"can":1}}
      await pg.evaluate("s=>localStorage.setItem('focus-vocab-v1', s)", json.dumps(st)); await pg.reload(); await pg.wait_for_timeout(1800)
      await pg.evaluate("window.__t.showView('today')"); await pg.evaluate("window.__t.openPet()"); await pg.wait_for_timeout(900)
      r=await pg.evaluate("""()=>{ const R=s=>{const e=document.querySelector(s); return e&&e.offsetHeight?e.getBoundingClientRect():null};
        const hit=(a,b)=>a&&b&&a.left<b.right-1&&b.left<a.right-1&&a.top<b.bottom-1&&b.top<a.bottom-1;
        const h=R('#pet .pet-hint'); const bad=['#petClose','#petSnd','#petCos','#petBrag'].filter(s=>hit(h,R(s)));
        const p=document.querySelector('#pet'); return {bad, inner:p.scrollHeight-p.clientHeight, hb:h&&Math.round(h.bottom), ih:innerHeight}; }""")
      ok(f"냥이 화면 {W}×{H}: 안내 줄이 버튼과 안 겹침", not r["bad"], r)
      ok(f"냥이 화면 {W}×{H}: 스크롤 없음", r["inner"]<=2, r)
      # 판 끝 화면(백로그 N): 작은 화면에서도 냥이 한마디가 보이고, 문제 화면에선 그대로 빠짐 · 스크롤 없음
      cs={f"d{i}":dict(id=f"d{i}",lang="es",word=f"pal{i}",meaning=f"뜻{i}",example="",level=2,due="2026-01-01",isNew=False,lapses=0,reps=3,created=i,introduced="2025-12-01",mastered=False,relearn=False,log=[],deck="default",step=2+(i%3),S=5+i%7,D=5,last="2025-12-20") for i in range(80)}
      await pg.evaluate("s=>localStorage.setItem('focus-vocab-v1', s)", json.dumps({"cards":cs,"meta":{"setup":1,"tutAsked":1,"loginAsked":1,"days":{},"settings":{"ui":"ko","lang":"es"},"stepv":1}})); await pg.reload(); await pg.wait_for_timeout(1500)
      r=await pg.evaluate("""async()=>{ const t=window.__t, out=[]; const close=()=>{const p=document.querySelector('#pet'); if(p&&!p.classList.contains('hidden')) document.querySelector('#petClose').click();};
        for(let k=0;k<2;k++){ close(); t.setSES(null); t.startSession(); const s=t.getSES(); const sq=document.querySelector('#sessionBox > .say'); const qs=sq?sq.offsetHeight:0;
          let g=0; while(s.queue.length && g++<40) t.settleItem(true); await new Promise(r=>setTimeout(r,8500)); close(); await new Promise(r=>setTimeout(r,800));
          const b=document.querySelector('#sessionBox > .say .bubble'); out.push({q:qs, ce:b?b.offsetHeight:0, over:document.scrollingElement.scrollHeight-innerHeight}); }
        return out; }""")
      short=H<=760
      ok(f"판 끝 {W}×{H}: 첫 판·둘째 판 끝에 냥이 한마디 보임", all(x["ce"]>0 for x in r), r)
      ok(f"판 끝 {W}×{H}: 스크롤 없음", all(x["over"]<=2 for x in r), r)
      if short: ok(f"문제 화면 {W}×{H}: 냥이 말풍선은 그대로 빠짐", all(x["q"]==0 for x in r), r)
      await ctx.close()
    ok("페이지 오류 없음", not errs, errs[:3])
    await b.close()
  print("결과:", "통과" if all(R) else "실패"); sys.exit(0 if all(R) else 1)
asyncio.run(main())
