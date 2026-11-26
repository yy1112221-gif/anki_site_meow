# 냥이 화면 유도(11-26): 안내 글줄은 화면에서 숨김(읽어 주기용만) · 말풍선은 버튼 아래·냥이 위(냥이 안 덮음, 두 줄) ·
# 가만히 있으면 간식 있을 때 「もぐもぐ…/움냠냠…」, 볼을 안 당겨 봤으면 냥이가 스스로 볼을 쭉 당겼다 놓음 · 손대면 시계 처음부터
import asyncio, sys
from playwright.async_api import async_playwright
B="http://localhost:8765/index.html"; R=[]
def ok(n,c,i=""): R.append(bool(c)); print(("✅" if c else "❌"), n, "" if c else i)
async def main():
  async with async_playwright() as pw:
    b=await pw.chromium.launch()
    for (W,H) in [(390,844),(360,640)]:
      for ui,word in [("ko","움냠냠"),("ja","もぐもぐ")]:
        pg=await b.new_page(viewport={"width":W,"height":H}); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)))
        await pg.goto(B+f"?rec=pet&ui={ui}"); await pg.wait_for_timeout(1500)
        vis=await pg.evaluate("()=>{const r=document.querySelector('#petHint').getBoundingClientRect(); return r.width<=2&&r.height<=2}")
        ok(f"{W} {ui} 안내 글줄 화면에 안 보임(글은 남음)", vis and await pg.text_content("#petHint"))
        seen=None; pulled=False
        for i in range(32):
          await pg.wait_for_timeout(500)
          st=await pg.evaluate("()=>{const s=window.__t.pet(), m=document.querySelector('#petMsg'); return {t:m.classList.contains('show')?m.textContent:'', ap:!!s.ap, mb:m.getBoundingClientRect().bottom, mt:m.getBoundingClientRect().top, cat:s.toScr(64,50).y+s.cv.getBoundingClientRect().top, brag:document.querySelector('#petBrag').getBoundingClientRect().bottom, h:m.getBoundingClientRect().height}}")
          if st["t"] and seen is None and word in st["t"]: seen=st
          if st["ap"]: pulled=True
          if seen and pulled: break
        ok(f"{W} {ui} 가만히 있으면 배고픈 한마디", seen is not None)
        if seen: ok(f"{W} {ui} 말풍선이 버튼 아래·냥이 위(덮지 않음)", seen["mt"]>=seen["brag"]+4 and seen["mb"]<=seen["cat"]+6, seen)
        ok(f"{W} {ui} 볼을 안 당겼으면 냥이가 스스로 볼 당기기", pulled)
        # 손대면 시계 처음부터
        await pg.evaluate("()=>{const s=window.__t.pet(); const r=s.cv.getBoundingClientRect(); s.cv.dispatchEvent(new PointerEvent('pointerdown',{clientX:r.left+r.width/2,clientY:r.top+r.height*.6,pointerId:9,bubbles:true}));s.cv.dispatchEvent(new PointerEvent('pointerup',{clientX:r.left+r.width/2,clientY:r.top+r.height*.6,pointerId:9,bubbles:true}));}")
        idle=await pg.evaluate("()=>performance.now()-window.__t.pet().act"); ok(f"{W} {ui} 손대면 기다림 시계 처음부터", idle<600, idle)
        ok(f"{W} {ui} 오류 없음", not errs, errs[:2]); await pg.close()
    await b.close()
  print(f"t_nudge: {sum(R)}/{len(R)}"); sys.exit(0 if all(R) else 1)
asyncio.run(main())
