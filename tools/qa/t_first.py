# 11-25 사용자: 처음 온 사람 첫 판 6문제(그 뒤 12), 레벨 진단 4페이지
import asyncio, json
from playwright.async_api import async_playwright
R=[]
def ok(n,c,i=""): R.append(bool(c)); print(("✅" if c else "❌"), n, "" if c else i)
def cards(n):
  return {f"c{i}":{"id":f"c{i}","lang":"es","word":w,"meaning":m,"example":"","isNew":True,"level":0,"due":None,"lapses":0,"reps":0,"log":[],"created":i,"u":1,"deck":"default"} for i,(w,m) in enumerate([("casa","집"),("perro","개"),("gato","고양이"),("agua","물"),("libro","책"),("mesa","탁자"),("sol","해"),("luna","달"),("flor","꽃"),("mar","바다")][:n])}
async def main():
  async with async_playwright() as pw:
    b=await pw.chromium.launch(); pg=await b.new_page(viewport={"width":360,"height":640}); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)))
    async def seed(meta):
      await pg.goto("http://localhost:8765/index.html"); await pg.evaluate("s=>localStorage.setItem('focus-vocab-v1', s)", json.dumps({"cards":cards(10),"meta":meta})); await pg.goto("http://localhost:8765/index.html"); await pg.wait_for_timeout(1500)
    base={"setup":1,"tutAsked":1,"loginAsked":1,"days":{},"settings":{"ui":"ko","lang":"es","newLimit":10},"stepv":1}
    await seed(dict(base, first1=1))
    q=await pg.evaluate("()=>window.__t.buildCourse().queue.length"); ok("첫 판 6문제", q==6, q)
    r=await pg.evaluate("()=>{ window.__t.startSession(); return [window.__t.S().meta.first1, window.__t.getSES().queue.length]; }"); ok("첫 판 시작하면 first1=2", r==[2,6], r)
    await seed(base)
    q=await pg.evaluate("()=>window.__t.buildCourse().queue.length"); ok("first1 없으면 그대로 12", q==12, q)
    await seed(dict(base, first1=1))
    q=await pg.evaluate("()=>{ const t=window.__t; t.S().meta.days[t.addDays(t.today(),-1)]=true; return t.buildCourse().queue.length; }"); ok("이미 공부한 날 있으면 12", q==12, q)
    ok("진단 4페이지", "PAGES = 4" in await pg.evaluate("()=>document.documentElement.innerHTML"))
    ok("오류 없음", not errs, errs)
    await b.close()
  print("통과" if all(R) else "실패", f"{sum(R)}/{len(R)}"); raise SystemExit(0 if all(R) else 1)
asyncio.run(main())
