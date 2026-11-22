# 검수단 R1-7-3(ñ를 n으로 바꿔 año/ano 같은 말 취급)·R1-7-5(분해형 악센트 입력 NFC 없음)
import asyncio
from playwright.async_api import async_playwright
R=[]
def ok(n,c,i=""): R.append(c); print(("✅" if c else "❌"), n, "" if c else i)
DEC="café"   # café 분해형
async def main():
  async with async_playwright() as pw:
    b=await pw.chromium.launch(); pg=await b.new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)))
    await pg.goto("http://localhost:8765/index.html"); await pg.wait_for_timeout(1200)
    async def ck(a,t,strict=False): return await pg.evaluate("([a,t,s])=>{window.__t.S().meta.settings.strictAccent=s; return window.__t.check(a,t)}",[a,t,strict])
    for st in (False,True):
      r=await ck("ano","año",st); ok("check('ano','año') → no (strict=%s)"%st, r=="no", r)
      r=await ck("Nino","niño",st); ok("check('Nino','niño') → no (strict=%s)"%st, r=="no", r)
      r=await ck(DEC,"café",st); ok("분해형 café → ok (strict=%s)"%st, r=="ok", r)
      r=await ck("año","año",st); ok("año → ok (strict=%s)"%st, r=="ok", r)
      r=await ck("año","año",st); ok("분해형 año → ok (strict=%s)"%st, r=="ok", r)
    r=await ck("cafe","café"); ok("악센트 관대 판정 그대로: cafe←café → accent", r=="accent", r)
    r=await ck("cafe","café",True); ok("strictAccent: cafe←café → no", r=="no", r)
    r=await ck("canon","cañón"); ok("cañón←canon → no (ñ 다름)", r=="no", r)
    r=await ck("cañon","cañón"); ok("cañón←cañon → accent (ó만 다름)", r=="accent", r)
    r=await pg.evaluate("()=>[window.__t.stripAcc('Año niño Ñandú canción'), window.__t.stripAcc('が한글'), window.__t.stripAcc('café').length]")
    ok("stripAcc: ñ·Ñ 남기고 다른 악센트만 지움", r[0]=="Año niño Ñandu cancion", r)
    ok("stripAcc: 가나·한글 그대로, 길이 그대로", r[1]=="が한글" and r[2]==4, r)
    r=await pg.evaluate("()=>{window.__t.S().meta.settings.lang='es'; const c={word:'año',example:'Este año viajo.'}; c.form=window.__t.findForm(c.example,c.word); const p=window.__t.clozeParts(c); return p&&p.answer}")
    ok("빈칸: año 예문 그대로 찾음", r=="año", r)
    ok("오류 없음", not errs, errs[:3])
    await b.close()
asyncio.run(main()); import sys; sys.exit(0 if all(R) else 1)
