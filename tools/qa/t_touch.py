# 누르는 대상 크기 측정만 (WCAG 2.2 SC 2.5.8, 24×24 CSS px) — 실패 처리 안 함, 경고 목록만 출력. 고치기는 11-29 이후 과제.
# 24px 미만이어도 중심의 24px 원이 다른 대상(·그 원)과 안 겹치면 예외(간격 예외)로 본다. 문장 속 낱말(.tok)은 인라인 예외라 뺌.
import asyncio, sys, json, datetime
from playwright.async_api import async_playwright
R=[]
def ok(n,c,i=""): R.append(c); print(("✅" if c else "❌"), n, "" if c else i)
def ds(d): return (datetime.datetime.now(datetime.timezone.utc)-datetime.timedelta(days=d, hours=4)).strftime("%Y-%m-%d")
WS=["先生","学校","働く","食べる","飲む","行く","来る","見る","聞く","話す","読む","書く","買う","売る","会う","待つ","持つ","立つ","座る","歩く"]
def state():
  cards={f"a{i}":dict(id=f"a{i}",lang="ja",word=w,meaning=f"뜻{i}",deck="default",example="",due=ds(2),level=2,reps=2,lapses=0,created=i,introduced="2025-12-01",S=4,D=5,last=ds(6),step=1+(i%3),log=[]) for i,w in enumerate(WS)}
  return {"cards":cards,"meta":{"days":{ds(i):{"n":10,"ok":8} for i in range(1,5)},"setup":1,"tutAsked":1,"loginAsked":1,"tutWant":0,"stepv":1,"settings":{"ui":"ko","lang":"ja"},"pet":{"inv":{"kari":3,"nibo":2}}}}
MEASURE="""(root)=>{ const sel='button,a[href],[role=button],input:not([type=hidden]),select,summary,label[for],[data-say],[onclick]';
  const vis=e=>{ const r=e.getBoundingClientRect(); if(r.width<1||r.height<1) return null; const s=getComputedStyle(e); if(s.visibility==='hidden'||s.display==='none'||+s.opacity===0||s.pointerEvents==='none') return null;
    if(r.bottom<0||r.top>innerHeight||r.right<0||r.left>innerWidth) return null; const cx=Math.min(Math.max(r.left+r.width/2,0),innerWidth-1), cy=Math.min(Math.max(r.top+r.height/2,0),innerHeight-1);
    const top=document.elementFromPoint(cx,cy); if(top&&!(e.contains(top)||top.contains(e))) return null; return r; };
  const L=[...document.querySelectorAll(sel)].filter(e=>!e.closest('.tok')&&!e.classList.contains('tok')&&!(e.closest(sel)!==e&&e.parentElement.closest(sel))).map(e=>({e,r:vis(e)})).filter(x=>x.r);
  const name=e=>(e.id?'#'+e.id:'')+(e.className&&typeof e.className==='string'?'.'+e.className.trim().split(/\\s+/).slice(0,2).join('.'):'')+' '+((e.getAttribute('aria-label')||e.textContent||e.value||'').trim().replace(/\\s+/g,' ').slice(0,16));
  const out=[]; L.forEach((x,i)=>{ const r=x.r; if(r.width>=24&&r.height>=24) return; const cx=r.left+r.width/2, cy=r.top+r.height/2;
    const near=L.some((y,j)=>{ if(j===i) return false; const q=y.r; const dx=Math.max(q.left-cx,0,cx-q.right), dy=Math.max(q.top-cy,0,cy-q.bottom); const small=q.width<24||q.height<24;
      if(small){ const qx=q.left+q.width/2, qy=q.top+q.height/2; return Math.hypot(qx-cx,qy-cy)<24; } return Math.hypot(dx,dy)<12; });
    out.push({n:name(x.e).trim(), w:Math.round(r.width), h:Math.round(r.height), sp:!near}); });
  return {n:L.length, small:out}; }"""
async def main():
  async with async_playwright() as pw:
    b=await pw.chromium.launch(); errs=[]; rows=[]
    for W,H in [(390,844),(360,640)]:
      ctx=await b.new_context(viewport={"width":W,"height":H},locale="ko-KR",has_touch=True,is_mobile=True)
      pg=await ctx.new_page(); pg.on("pageerror",lambda e:errs.append(str(e)))
      await pg.goto("http://localhost:8765/index.html")
      await pg.evaluate("s=>localStorage.setItem('focus-vocab-v1', s)", json.dumps(state())); await pg.reload(); await pg.wait_for_timeout(1800)
      async def m(where):
        r=await pg.evaluate(MEASURE); bad=[x for x in r["small"] if not x["sp"]]
        rows.append((f"{W}×{H}",where,r["n"],bad,[x for x in r["small"] if x["sp"]]))
      await pg.evaluate("window.__t.showView('today'); window.__t.openPet()"); await pg.wait_for_timeout(900); await m("냥이 화면")
      if await pg.locator("#petCos").is_visible():
        await pg.click("#petCos"); await pg.wait_for_timeout(700); await m("꾸미기 상점")
      await pg.evaluate("()=>{ document.querySelectorAll('.sheet-bg,#pet,#riskPop,.sup-ov,#s7').forEach(e=>e.remove()); window.__t.showView('today'); }"); await pg.wait_for_timeout(400); await m("홈")
      await pg.goto("http://localhost:8765/index.html"); await pg.wait_for_timeout(1500)
      await pg.evaluate("()=>{ const p=document.querySelector('#petClose'); if(p&&p.offsetParent) p.click(); }"); await pg.wait_for_timeout(300)
      if await pg.locator("#startBtn").is_visible():
        await pg.click("#startBtn"); await pg.wait_for_timeout(900); await m("문제 화면(첫 문제)")
        await pg.evaluate("()=>{ const t=window.__t, s=t.getSES(); let g=0; while(s&&s.queue.length&&g++<40) t.settleItem(true); }"); await pg.wait_for_timeout(8500)
        await pg.evaluate("()=>{ const p=document.querySelector('#pet'); if(p&&!p.classList.contains('hidden')) document.querySelector('#petClose').click(); }"); await pg.wait_for_timeout(600); await m("판 끝")
      await ctx.close()
    print("── 24×24px 미만이고 간격 예외도 안 되는 대상 (경고) ──")
    tot=0
    for vp,where,n,bad,sp in rows:
      tot+=len(bad); print(f"⚠ {vp} {where}: 대상 {n}개 중 {len(bad)}개" + (" — " + " · ".join(f"{x['n']} {x['w']}×{x['h']}" for x in bad[:14]) if bad else "") + (f" (간격 예외 {len(sp)}개: " + " · ".join(f"{x['n']} {x['w']}×{x['h']}" for x in sp[:8]) + ")" if sp else ""))
    print(f"   합계 경고 {tot}개 (실패 처리 안 함)")
    ok("측정 완료·페이지 오류 없음", not errs and len(rows)>=6, (errs[:3], len(rows)))
    await b.close()
  sys.exit(0 if all(R) else 1)
asyncio.run(main())
