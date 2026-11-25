# 11-25 사용자: 첫 설정에서 태어난 해 + 생일(월·일, 선택) 함께
import asyncio, json
from playwright.async_api import async_playwright
R=[]
def ok(n,c,i=""): R.append(bool(c)); print(("✅" if c else "❌"), n, "" if c else i)
async def to_setup2(pg):
  await pg.goto("http://localhost:8765/index.html"); await pg.evaluate("()=>localStorage.clear()"); await pg.goto("http://localhost:8765/index.html"); await pg.wait_for_timeout(1500)
  await pg.click('[data-ui="ko"]'); await pg.wait_for_timeout(200); await pg.click('[data-lg="ja"]'); await pg.wait_for_timeout(500)
async def pick(pg, sel, v):
  await pg.evaluate("([s,v])=>{ const w=document.querySelector(s), k=w.querySelector(`[data-v=\"${v}\"]`); w.scrollTop=k.offsetTop-w.clientHeight/2+k.offsetHeight/2; }", [sel, v]); await pg.wait_for_timeout(300)
async def main():
  async with async_playwright() as pw:
    b=await pw.chromium.launch()
    for vw,vh in [(360,640),(390,844)]:
      ctx=await b.new_context(viewport={"width":vw,"height":vh}); pg=await ctx.new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)))
      sent=[]; pg.on("request", lambda r: sent.append(r.post_data or ""))
      await to_setup2(pg)
      ok(f"{vw} 생년월일 바퀴 3개", await pg.evaluate("()=>!!document.querySelector('#suWheel')&&!!document.querySelector('#suWM')&&!!document.querySelector('#suWD')"))
      ok(f"{vw} 한 화면(가로 넘침 없음)", await pg.evaluate("()=>document.documentElement.scrollWidth")<=vw)
      await pick(pg,"#suWM","2"); await pick(pg,"#suWD","31"); await pg.click("#suOk"); await pg.wait_for_timeout(300)
      m=await pg.evaluate("()=>{ const S=window.__t.S(); return [S.meta.by, S.meta.bmd, (S.meta.fr||{}).bday, (S.meta.fr||{}).bshare]; }")
      ok(f"{vw} 2월 31일 → 02-29로 저장·친구 생일 칸에도(공개는 꺼짐)", m[0] and m[1]=="02-29" and m[2]=="02-29" and not m[3], m)
      ok(f"{vw} 생일은 사용 기록으로 안 보냄", not any("02-29" in s for s in sent))
      await to_setup2(pg); await pg.click("#suOk"); await pg.wait_for_timeout(300)
      m=await pg.evaluate("()=>{ const S=window.__t.S(); return [S.meta.by, S.meta.bmd||null]; }")
      ok(f"{vw} 월·일 안 고르면(—) 생일 저장 안 함, 해는 그대로", m[0] and m[1] is None, m)
      ok(f"{vw} 오류 없음", not errs, errs[:3])
      await ctx.close()
    await b.close()
  print("통과" if all(R) else "실패", f"{sum(R)}/{len(R)}"); raise SystemExit(0 if all(R) else 1)
asyncio.run(main())
