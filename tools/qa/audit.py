# 한 화면 원칙 점검: 각 화면·시트를 열어 스크롤이 생기는 곳 측정
import json, asyncio, sys
from playwright.async_api import async_playwright
BASE="http://localhost:8765/index.html"
SIZES=[(360,640),(390,844)]
SEED=r"""() => { const td = new Date(); const ds = d => { const t=new Date(td.getTime()-d*864e5-4*3600e3); return t.toISOString().slice(0,10); };
 const cards={}; const ws=["先生","学校","働く","食べる","飲む","行く","来る","見る","聞く","話す","読む","書く","買う","売る","会う","待つ","持つ","立つ","座る","歩く","走る","泳ぐ","休む","遊ぶ","住む","死ぬ","呼ぶ","飛ぶ","選ぶ","運ぶ"];
 ws.forEach((w,i)=>{cards["a"+i]={id:"a"+i,lang:"ja",word:w,meaning:"뜻"+i,deck:"default",ex:"",due:ds(-1),iv:3,ef:2.5,reps:2,u:Date.now()}});
 const days={}; for(let i=1;i<9;i++) days[ds(i)]={n:10,ok:8};
 localStorage.setItem("focus-vocab-v1", JSON.stringify({cards, meta:{days, setup:1, tutAsked:1, loginAsked:1, tutWant:0, settings:{ui:"ko",lang:"ja"}}})); }"""
MEASURE=r"""(label) => { const out=[]; const H=innerHeight, W=innerWidth;
 const de=document.scrollingElement; if(de.scrollHeight>H+2) out.push({el:"페이지 전체", over:de.scrollHeight-H});
 for(const e of document.querySelectorAll("body *")){ const cs=getComputedStyle(e); if(cs.display==="none"||cs.visibility==="hidden") continue;
   if(/(auto|scroll)/.test(cs.overflowY) && e.scrollHeight>e.clientHeight+2 && e.clientHeight>40){
     const r=e.getBoundingClientRect(); if(r.width<5||r.height<5) continue;
     out.push({el:e.tagName.toLowerCase()+(e.id?"#"+e.id:"")+(e.className&&typeof e.className==="string"?"."+e.className.trim().split(/\s+/).slice(0,2).join("."):""), over:e.scrollHeight-e.clientHeight}); } }
 return out; }"""
async def run():
  res={}
  async with async_playwright() as pw:
    b=await pw.chromium.launch()
    for W,H in SIZES:
      ctx=await b.new_context(viewport={"width":W,"height":H},locale="ko-KR",has_touch=True,is_mobile=True,device_scale_factor=2)
      pg=await ctx.new_page(); await pg.goto(BASE); await pg.evaluate(SEED); await pg.reload(); await pg.wait_for_timeout(2500)
      async def shot(name):
        await pg.wait_for_timeout(700); r=await pg.evaluate(MEASURE,name); res.setdefault(name,{})[f"{W}x{H}"]=r
        await pg.screenshot(path=f"/tmp/pt/shots/{name}_{W}.png")
      async def esc():
        await pg.evaluate("() => { document.querySelectorAll('.sheet-bg,#pet,#riskPop,.sup-ov,#s7').forEach(e=>e.remove()); }")
      for v in ["today","list","add","how"]:
        await pg.evaluate(f"window.__t.showView('{v}')"); await shot("view-"+v)
      await pg.evaluate("window.__t.showView('how')")
      await pg.evaluate("() => { const h=document.querySelector('#hshop'); if(h){h.open=true;} }"); await shot("how-shop")
      await pg.evaluate("() => document.querySelectorAll('#view-how details').forEach(d=>d.open=true)"); await shot("how-all-open")
      await pg.evaluate("window.__t.showView('today')")
      try:
        await pg.evaluate("window.__t.openPet()"); await shot("pet")
      except Exception as e: print("pet",e)
      await esc()
      try:
        await pg.evaluate("window.__t.startSession()"); await pg.wait_for_timeout(1500); await shot("session")
      except Exception as e: print("session",e)
      await ctx.close()
    await b.close()
  json.dump(res,open("/tmp/pt/audit.json","w"),ensure_ascii=False,indent=1)
  for n,d in res.items():
    for s,r in d.items(): print(("✅" if not r else "❌"), n, s, "" if not r else "; ".join(f"{x['el']} +{x['over']}px" for x in r[:4]))
asyncio.run(run())
