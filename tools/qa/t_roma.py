# 화면 로마자 자판 변환(rjStep): nn 뒤 자음에서 ん이 두 번 들어가던 버그(검수단 #29~#32) + 회귀
import asyncio, sys
from playwright.async_api import async_playwright
CASES=[("kannji","かんじ"),("kanji","かんじ"),("kanna","かんな"),("konnnichiha","こんにちは"),("konnichiha","こんにちは"),
       ("sennpai","せんぱい"),("hon'ya","ほんや"),("honnya","ほんや"),("kitte","きって"),("shinbun","しんぶん"),("nninngen","んにんげん"),("tennki","てんき")]
async def main():
  async with async_playwright() as pw:
    b=await pw.chromium.launch(); pg=await b.new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)))
    await pg.goto("http://localhost:8765/index.html"); await pg.wait_for_timeout(1200)
    res=await pg.evaluate("""(cs)=>cs.map(([inp])=>{ const st={c:"",p:""}; for(const ch of inp){ st.p+=ch; window.__t.rjStep(st); } let r=st.c+(st.p==="n"||st.p==="nn"?"ん":st.p); return r; })""", CASES)
    ok=True
    for (inp,want),got in zip(CASES,res):
      g = got==want; ok&=g; print(("✅" if g else "❌"), inp, "→", got, "" if g else f"(기대 {want})")
    if errs: ok=False; print("❌ 페이지 오류", errs[:2])
    await b.close()
  print("결과:", "통과" if ok else "실패"); sys.exit(0 if ok else 1)
asyncio.run(main())
