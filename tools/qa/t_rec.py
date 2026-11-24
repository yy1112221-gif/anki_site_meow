# R-1124-④-촬영모드: ?rec=pet → 냥이 화면 바로, 저장·동기화·기록·서버 요청 0, 기존 데이터 그대로
import asyncio, json, re
from playwright.async_api import async_playwright
R=[]
def ok(n,c,i=""): R.append(c); print(("✅" if c else "❌"), n, "" if c else i)
BASE="http://localhost:8765/index.html"
USER={"cards":{"c1":{"id":"c1","word":"猫","meaning":"고양이","lang":"ja","u":1,"due":0}},"meta":{"setup":1,"tutAsked":1,"loginAsked":1,"days":{"2026-11-01":True},"settings":{"ui":"ko","lang":"ja"},"cos":{"own":{"soda":1},"on":"soda"},"pet":{"inv":{"sushi":5},"coins":77,"kcal":40,"lv":2},"sync":{"code":"ABCD-EFGH"}}}
async def allLS(pg): return await pg.evaluate("()=>{const o={};for(let i=0;i<localStorage.length;i++){const k=localStorage.key(i);o[k]=localStorage.getItem(k);}return o;}")
async def main():
  async with async_playwright() as pw:
    b=await pw.chromium.launch()
    for vw,vh in [(390,844),(360,640)]:
      # ① 빈 저장소
      ctx=await b.new_context(viewport={"width":vw,"height":vh}); pg=await ctx.new_page(); errs=[]; net=[]
      pg.on("pageerror",lambda e:errs.append(str(e))); pg.on("request",lambda r:net.append(r.url) if re.search(r"supabase|tosspayments",r.url) else None)
      await pg.goto(BASE+"?rec=pet&skin=cheese&clean=1"); await pg.wait_for_timeout(1500)
      vis=await pg.evaluate("()=>{const p=document.querySelector('#pet');return !!p&&!p.classList.contains('hidden')}")
      ok(f"{vw} 빈 저장소 → 냥이 화면 바로 열림", vis)
      ok(f"{vw} 치즈 털 입음", await pg.evaluate("()=>__t.S().meta.cos.on==='cheese'"))
      hid=await pg.evaluate("()=>['.pet-top','#petSnd','#petCos','#petBrag','.pet-hint'].map(q=>{const e=document.querySelector(q);return !e||getComputedStyle(e).display==='none'})")
      ok(f"{vw} clean: 버튼·게이지·연속일수 숨김", all(hid), hid)
      ok(f"{vw} 온보딩·시트 없음", await pg.evaluate("()=>!document.querySelector('#ob:not(.hidden), .sheet-ov, #riskPop')"))
      ok(f"{vw} 간식 트레이 있음", await pg.evaluate("()=>__t.petCount()>0"))
      ok(f"{vw} 삐짐 없음(sulk 없음)", await pg.evaluate("()=>__t.sulkLv()===0"))
      await pg.screenshot(path=f"/tmp/shots/rec_{vw}.png")
      # 만지기·닫기 뒤에도 저장 0
      await pg.mouse.move(vw/2-20,vh*0.45); await pg.mouse.down(); await pg.mouse.move(vw/2+20,vh*0.47,steps=8); await pg.mouse.up(); await pg.wait_for_timeout(300)
      await pg.mouse.click(vw/2,vh*0.45); await pg.wait_for_timeout(900)
      await pg.evaluate("()=>{__t.save();__t.closePet();}"); await pg.wait_for_timeout(700)
      ls=await allLS(pg); ok(f"{vw} localStorage 변화 0", ls=={}, list(ls.keys()))
      ok(f"{vw} supabase·결제 요청 0", net==[], net[:3])
      ok(f"{vw} 오류 없음", errs==[], errs[:2])
      await ctx.close()
      # ② 기존 사용자 데이터가 있는 브라우저
      ctx=await b.new_context(viewport={"width":vw,"height":vh}); pg=await ctx.new_page(); errs=[]; net=[]
      pg.on("pageerror",lambda e:errs.append(str(e))); pg.on("request",lambda r:net.append(r.url) if re.search(r"supabase|tosspayments",r.url) else None)
      await ctx.route(re.compile(r"supabase\.co"), lambda r: r.abort())
      await pg.goto(BASE+"?nosw=1"); await pg.evaluate("s=>{localStorage.clear();localStorage.setItem('focus-vocab-v1',s);localStorage.setItem('meowca-dev','dev-1');}", json.dumps(USER))
      before=await allLS(pg); net.clear()
      await pg.goto(BASE+"?rec=pet&skin=mochi_st&night=1&ui=ja&sulk=2"); await pg.wait_for_timeout(1500)
      ok(f"{vw} 기존 데이터 안 읽음(카드 0·딸기 털)", await pg.evaluate("()=>Object.keys(__t.S().cards).length===0 && __t.S().meta.cos.on==='mochi_st'"))
      ok(f"{vw} ui=ja", await pg.evaluate("()=>__t.S().meta.settings.ui==='ja' && document.querySelector('#petClose').textContent.indexOf('학')<0"))
      ok(f"{vw} night=1 → 밤 배경", await pg.evaluate("()=>document.querySelector('#pet').classList.contains('night') && getComputedStyle(document.querySelector('#pet')).backgroundImage.includes('rgb(14, 20, 41)')"))
      ok(f"{vw} sulk=2 → 화남 단계", await pg.evaluate("()=>__t.sulkLv()===2"))
      ok(f"{vw} clean 없으면 버튼 보임", await pg.evaluate("()=>getComputedStyle(document.querySelector('#petCos')).display!=='none'"))
      await pg.screenshot(path=f"/tmp/shots/rec_night_{vw}.png")
      await pg.evaluate("()=>{__t.save();__t.closePet();}"); await pg.wait_for_timeout(600)
      ok(f"{vw} 기존 localStorage 그대로", await allLS(pg)==before)
      ok(f"{vw} 서버 요청 0(동기화 코드 있어도)", net==[], net[:3])
      ok(f"{vw} 오류 없음 ②", errs==[], errs[:2])
      # sulk 1·3, 이상한 값
      for q,lv in [("?rec=pet&sulk=1",1),("?rec=pet&sulk=3",3),("?rec=pet&sulk=9",0)]:
        await pg.goto(BASE+q); await pg.wait_for_timeout(1100); ok(f"{vw} {q} → 삐짐 {lv}", await pg.evaluate(f"()=>__t.sulkLv()==={lv}"))
      await pg.goto(BASE+"?rec=pet&skin=%3Cscript%3E&acc=santa_hat"); await pg.wait_for_timeout(1100)
      ok(f"{vw} 이상한 skin 무시·산타 모자", await pg.evaluate("()=>__t.S().meta.cos.on===null && __t.S().meta.cos.hat==='santa_hat' && !document.querySelector('script[data-x]')"))
      ok(f"{vw} 이상한 값 뒤에도 localStorage 그대로", await allLS(pg)==before)
      # ③ rec 없는 평소 열기 회귀: 기존 데이터 읽고 저장함
      await pg.goto(BASE); await pg.wait_for_timeout(1200)
      ok(f"{vw} 평소: 기존 카드 읽음", await pg.evaluate("()=>!!__t.S().cards.c1 && __t.S().meta.pet.coins===77 && __t.REC()===null"))
      await pg.evaluate("()=>__t.save()"); mu=await pg.evaluate("()=>JSON.parse(localStorage.getItem('focus-vocab-v1')).meta.mu||0")
      ok(f"{vw} 평소: 저장 동작", mu>0)
      await pg.goto(BASE+"?rec=home"); await pg.wait_for_timeout(900)
      ok(f"{vw} rec=home 은 평소대로", await pg.evaluate("()=>__t.REC()===null && !!__t.S().cards.c1"))
      ok(f"{vw} 오류 없음 ③", errs==[], errs[:2])
      await ctx.close()
    await b.close()
  print(f"t_rec: {sum(R)}/{len(R)}"); 
  if not all(R): raise SystemExit(1)
asyncio.run(main())
