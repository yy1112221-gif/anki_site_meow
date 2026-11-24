# R-1124-④-털고르기: 상점 첫 줄 털 동그라미(기본+6) · 가진 털 바로 입힘(저장) · 안 가진 털 3초 입어 보기 + 「상점에서 보기」 · 구매 데이터 변화 0
import asyncio, json, sys
from playwright.async_api import async_playwright
R=[]
def ok(n,c,i=""): R.append(c); print(("✅" if c else "❌"), n, "" if c else i)
def mk(n=6):
  return {f"d{i}":dict(id=f"d{i}",lang="es",word=f"pal{i}",meaning=f"뜻{i}",example="",level=2,due="2026-01-01",isNew=False,lapses=0,reps=3,created=i,introduced="2025-12-01",mastered=False,relearn=False,log=[],deck="default",step=2,S=3,D=5,last="2025-12-20") for i in range(n)}
async def seed(pg, ui="ko", cos=None):
  meta={"setup":1,"tutAsked":1,"loginAsked":1,"days":{},"settings":{"ui":ui,"lang":"es","homePet":False},"stepv":1,"pet":{"inv":{"sushi":2},"kcal":0,"lv":1,"granted":{},"seenTier":9}}
  if cos is not None: meta["cos"]=cos
  for _ in range(3):
    await pg.evaluate("s=>localStorage.setItem('focus-vocab-v1', s)", json.dumps({"cards":mk(),"meta":meta})); await pg.reload(); await pg.wait_for_timeout(900)
    if await pg.evaluate("u=>window.__t.S().meta.settings.ui===u", ui): break
  await pg.evaluate("()=>{ const t=window.__t; if(!t.pet()) t.openPet(); }"); await pg.wait_for_timeout(800)
  await pg.click("#petCos"); await pg.wait_for_timeout(400)
async def st(pg): return await pg.evaluate("()=>{ const m=window.__t.S().meta, d=JSON.parse(localStorage.getItem('focus-vocab-v1')).meta.cos||{}; return { on:(m.cos||{}).on||null, try:window.__t.pet().tryOn||null, own:JSON.stringify((m.cos||{}).own||{}), sOn:d.on||null, pressed:[...document.querySelectorAll('#cosFur .cos-fd[aria-pressed=true]')].map(b=>b.dataset.fid), pick:(document.querySelector('#cosPick')||{}).textContent||'' }; }")
async def main():
  async with async_playwright() as pw:
    b=await pw.chromium.launch()
    for vw,vh in [(390,844),(360,640)]:
      ctx=await b.new_context(viewport={"width":vw,"height":vh}); pg=await ctx.new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)))
      await pg.goto("http://localhost:8765/index.html")
      own={"cheese":1700000000000}
      await seed(pg, cos={"own":own,"want":{}})
      ids=await pg.evaluate("()=>[...document.querySelectorAll('#cosFur .cos-fd')].map(b=>b.dataset.fid)")
      ok(f"{vw} 털 동그라미 7개(기본+6)", ids==["","mochi_st","mochi_mc","cheese","pudding","soda","sesame"], ids)
      sz=await pg.evaluate("()=>[...document.querySelectorAll('#cosFur .cos-fd')].map(b=>{ const r=b.getBoundingClientRect(); return [r.width,r.height,r.right<=innerWidth]; })")
      ok(f"{vw} 동그라미 24px 이상·화면 안", all(w>=24 and h>=24 and inside for w,h,inside in sz), sz)
      s=await st(pg); ok(f"{vw} 처음엔 기본이 눌린 상태", s["pressed"]==[""], s)
      await pg.screenshot(path=f"/tmp/fur{vw}.png")
      # 가진 털(치즈) → 바로 입힘·저장
      await pg.click('#cosFur [data-fid="cheese"]'); await pg.wait_for_timeout(200); s=await st(pg)
      ok(f"{vw} 가진 털 누르면 입힘·저장", s["on"]=="cheese" and s["sOn"]=="cheese" and s["pressed"]==["cheese"] and not s["try"], s)
      # 안 가진 털(소다) → 입어 보기, 저장 안 함, 3초 뒤 원래대로
      await pg.click('#cosFur [data-fid="soda"]'); await pg.wait_for_timeout(200); s=await st(pg)
      ok(f"{vw} 안 가진 털 → 입어 보기(저장 안 함)", s["try"]=="soda" and s["on"]=="cheese" and s["sOn"]=="cheese" and s["pressed"]==["soda"], s)
      ok(f"{vw} 「상점에서 보기」 버튼", await pg.evaluate("()=>!!document.querySelector('#cosFurGo')") and "입어 보는 중" in s["pick"], s["pick"])
      await pg.wait_for_timeout(3200); s=await st(pg); ok(f"{vw} 3초 뒤 원래 털(치즈)로", not s["try"] and s["pressed"]==["cheese"], s)
      # 상점에서 보기 → 스킨 탭, 그 상품
      await pg.click('#cosFur [data-fid="pudding"]'); await pg.wait_for_timeout(150); await pg.click("#cosFurGo"); await pg.wait_for_timeout(300)
      r=await pg.evaluate("()=>({ tab:document.querySelector('.cos-tabs [aria-pressed=true]').dataset.cat, items:[...document.querySelectorAll('#cosRow .cos-it')].map(b=>b.dataset.id), pick:document.querySelector('#cosPick').textContent, try:window.__t.pet().tryOn })")
      ok(f"{vw} 상점에서 보기 → 스킨 탭·푸딩", r["tab"]=="skin" and "pudding" in r["items"] and "푸딩" in r["pick"] and r["try"]=="pudding", r)
      # 기본으로
      await pg.click('#cosFur [data-fid=""]'); await pg.wait_for_timeout(200); s=await st(pg)
      ok(f"{vw} 기본 누르면 벗음(저장)", s["on"] is None and s["sOn"] is None and not s["try"] and s["pressed"]==[""], s)
      ok(f"{vw} 구매·보유 데이터 변화 0", s["own"]==json.dumps(own,separators=(",",":")) and await pg.evaluate("()=>JSON.stringify(window.__t.S().meta.pet.buy||[])==='[]' && window.__t.S().meta.pet.inv.sushi===2"), s["own"])
      # 닫으면 입어 보기 해제
      await pg.click('#cosFur [data-fid="soda"]'); await pg.wait_for_timeout(100); await pg.click("#cosX"); await pg.wait_for_timeout(200)
      ok(f"{vw} 상점 닫으면 입어 보기 해제", not await pg.evaluate("()=>window.__t.pet().tryOn"))
      sc=await pg.evaluate("()=>{ const p=document.querySelector('#pet'); return [p.scrollHeight,p.clientHeight,document.documentElement.scrollWidth,innerWidth]; }")
      ok(f"{vw} 냥이 화면 스크롤 없음", sc[0]<=sc[1]+1 and sc[2]<=sc[3]+1, sc)
      # 옛 데이터(cos 없음)·일본어
      await seed(pg, ui="ja"); s=await st(pg); ok(f"{vw} 옛 데이터(cos 없음) 기본 선택", s["pressed"]==[""], s)
      await pg.click('#cosFur [data-fid="cheese"]'); await pg.wait_for_timeout(150); s=await st(pg)
      ok(f"{vw} ja 안 가진 털 → 試着中·ショップで見る", s["try"]=="cheese" and s["on"] is None and "試着中" in s["pick"] and "ショップで見る" in s["pick"], s)
      # 후원 골드 가진 사람은 8개
      await seed(pg, cos={"own":{"sup_gold":1},"want":{}}); n=await pg.evaluate("()=>document.querySelectorAll('#cosFur .cos-fd').length"); ok(f"{vw} 후원 골드 보유 → 8개", n==8, n)
      ok(f"{vw} 오류 없음", not errs, errs[:3])
      await ctx.close()
    await b.close()
  print(f"\n{sum(R)}/{len(R)}"); sys.exit(0 if all(R) else 1)
asyncio.run(main())
