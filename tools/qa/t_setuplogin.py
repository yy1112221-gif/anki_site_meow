# 11-25 사용자: 첫 설정에서 로그인 묻기(건너뛰기 + 경고 문구) · 로그인 버튼마다 구글·카카오·LINE 마크
import asyncio, json, re
from playwright.async_api import async_playwright
R=[]
def ok(n,c,i=""): R.append(bool(c)); print(("✅" if c else "❌"), n, "" if c else i)
async def to_login(pg, by_kid=False):
  await pg.goto("http://localhost:8765/index.html"); await pg.evaluate("()=>localStorage.clear()"); await pg.goto("http://localhost:8765/index.html"); await pg.wait_for_timeout(1500)
  await pg.click('[data-ui="ko"]'); await pg.wait_for_timeout(200); await pg.click('[data-lg="ja"]'); await pg.wait_for_timeout(500)
  if by_kid: await pg.evaluate("()=>{ const w=document.querySelector('#suWheel'), k=w.querySelector('[data-y=\"2016\"]'); w.scrollTop=k.offsetTop-w.clientHeight/2+k.offsetHeight/2; }"); await pg.wait_for_timeout(300)
  await pg.click("#suOk"); await pg.wait_for_timeout(800)
async def main():
  async with async_playwright() as pw:
    b=await pw.chromium.launch()
    for vw,vh in [(360,640),(390,844)]:
      ctx=await b.new_context(viewport={"width":vw,"height":vh}); pg=await ctx.new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)))
      await ctx.route(re.compile(r"/auth/v1/settings"), lambda r: r.fulfill(status=200, content_type="application/json", body=json.dumps({"external":{"google":True,"kakao":True,"apple":False}})))
      await ctx.route(re.compile(r"supabase\.co/(rest|functions)"), lambda r: r.abort())
      await to_login(pg)
      t=await pg.evaluate("()=>document.querySelector('#setupBox').textContent")
      ok(f"{vw} 첫 설정에 로그인 단계", "로그인" in t and "건너뛰기" in t, t[:80])
      ok(f"{vw} 경고 문구(작은 글씨)", "저장되지 않을 수 있어요" in t and await pg.evaluate("()=>parseFloat(getComputedStyle(document.querySelector('.su-warn')).fontSize)<13"))
      ok(f"{vw} 버튼마다 마크(SVG)", await pg.evaluate("()=>[...document.querySelectorAll('#suProv .prov')].length>=2 && [...document.querySelectorAll('#suProv .prov')].every(b=>b.querySelector('.prov-ic svg'))"))
      ok(f"{vw} 한 화면", await pg.evaluate("()=>document.documentElement.scrollWidth")<=vw)
      await pg.click("#suLoginSkip"); await pg.wait_for_timeout(300)
      ok(f"{vw} 건너뛰기 → 튜토리얼 질문", await pg.evaluate("()=>!!document.querySelector('[data-tut]')"))
      await to_login(pg, by_kid=True)
      ok(f"{vw} 만 14세 미만은 로그인 단계 없이 튜토리얼로", await pg.evaluate("()=>!!document.querySelector('[data-tut]') && !document.querySelector('#suProv')"))
      ok(f"{vw} 오류 없음", not errs, errs[:3])
      await ctx.close()
    await b.close()
  print("통과" if all(R) else "실패", f"{sum(R)}/{len(R)}"); raise SystemExit(0 if all(R) else 1)
asyncio.run(main())
