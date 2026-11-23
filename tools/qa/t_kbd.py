# 화면 자판 + 물리 키보드·스크린리더 (요청 R-1123-검수단-자판키보드, 검수단 R1-40-1)
# ① 화면 자판(기본 ON)인데 물리 키보드로 'ser'+Enter → 정답 ② 자판 키 Tab 포커스 + Enter/Space(click만 옴) → 입력
# ③ 마우스·터치 자판 입력은 한 번만(중복 없음) ④ 물리 키보드 뒤 다음 문제는 바로 키보드 입력칸 ⑤ 「한자까지 정확히」(vkFor) 회귀
import asyncio, json, datetime
from playwright.async_api import async_playwright
R=[]
def ok(n,c,i=""): R.append(bool(c)); print(("✅" if c else "❌"), n, "" if c else i)
def ds(d): return (datetime.datetime.now(datetime.timezone.utc)-datetime.timedelta(days=d, hours=4)).strftime("%Y-%m-%d")
def card(i,lang,word,meaning,**k):
  c=dict(id=i,lang=lang,word=word,meaning=meaning,deck="default",example="",due=ds(1),level=2,reps=3,lapses=0,created=1,introduced="2025-12-01",S=4,D=5,last=ds(5),step=4,log=[]); c.update(k); return c
def state(ui="ja", lang="es", strict=False):
  cards={"e1":card("e1","es","ser","である、～だ"),"e2":card("e2","es","mesa","テーブル"),
         "k1":card("k1","ja","遅い","おそい · 느리다, 늦다",reading="おそい")}
  st={"ui":ui,"lang":lang}
  if strict: st["strictKanji"]=True
  return {"cards":cards,"meta":{"setup":1,"tutAsked":1,"loginAsked":1,"days":{},"stepv":1,"settings":st}}
ASK="""([id,mode])=>{ const t=window.__t; document.querySelectorAll('.sheet-bg,#riskPop,.sup-ov,#s7').forEach(e=>e.remove()); const p=document.querySelector('#pet'); if(p&&!p.classList.contains('hidden')) document.querySelector('#petClose').click();
  if(document.activeElement) document.activeElement.blur();
  t.showView('today'); t.setSES({queue:[{id,mode,st:4,k:'w'}],done:0,failed:{},remaining:{[id]:1},finished:[],state:null,course:{n:12,i:0,newK:0,ok:0,g:0}}); t.$('#sessionStart').classList.add('hidden'); t.$('#sessionBox').classList.remove('hidden'); t.nextItem(); return 1; }"""
FB="()=>{ const f=document.querySelector('#fb'); return f? f.innerText : ''; }"
async def main():
  async with async_playwright() as pw:
    b=await pw.chromium.launch(); errs=[]
    async def page(st,mobile=False):
      o=dict(viewport={"width":390,"height":844},locale="ja-JP",has_touch=True,is_mobile=True) if mobile else dict(viewport={"width":1280,"height":800},locale="ja-JP")
      ctx=await b.new_context(**o); pg=await ctx.new_page(); pg.on("pageerror",lambda e:errs.append(str(e)))
      await pg.goto("http://localhost:8765/index.html")
      await pg.evaluate("s=>localStorage.setItem('focus-vocab-v1', s)", json.dumps(st)); await pg.reload(); await pg.wait_for_timeout(1500)
      return ctx,pg
    okfb="()=>document.querySelectorAll('#fb .feedback.ok').length>0"
    # ① PC 물리 키보드
    ctx,pg=await page(state())
    await pg.evaluate(ASK,["e1","recall"]); await pg.wait_for_timeout(500)
    ok("PC: 화면 자판 기본 ON(readOnly)", await pg.evaluate("()=>document.querySelector('#ans').readOnly && !!document.querySelector('.vk-host .vk')"))
    await pg.keyboard.type("ser"); await pg.wait_for_timeout(150)
    v=await pg.input_value("#ans"); ok("PC: 물리 키보드 'ser' 입력됨", v=="ser", v)
    ok("PC: 입력칸이 키보드 입력으로 바뀜(readOnly 해제·포커스)", await pg.evaluate("()=>{ const i=document.querySelector('#ans'); return !i.readOnly && document.activeElement===i; }"))
    await pg.keyboard.press("Enter"); await pg.wait_for_timeout(500)
    ok("PC: 'ser'+Enter 정답", await pg.evaluate(okfb), await pg.evaluate(FB))
    # Backspace 도 동작
    await pg.evaluate(ASK,["e2","recall"]); await pg.wait_for_timeout(500)
    r=await pg.evaluate("()=>{ const i=document.querySelector('#ans'); return [i.readOnly, document.activeElement===i]; }")
    ok("PC: 다음 문제는 바로 키보드 입력칸(포커스)", r==[False,True], r)
    await pg.keyboard.type("mesx"); await pg.keyboard.press("Backspace"); await pg.keyboard.type("a"); await pg.keyboard.press("Enter"); await pg.wait_for_timeout(500)
    ok("PC: 'mesx'⌫'a'+Enter → mesa 정답", await pg.evaluate(okfb), await pg.evaluate(FB))
    await ctx.close()
    # ② 자판 키 포커스 + Enter/Space (키보드·스크린리더 활성화)
    ctx,pg=await page(state())
    await pg.evaluate(ASK,["e1","recall"]); await pg.wait_for_timeout(500)
    for ch,key in [("s","Enter"),("e"," "),("r","Enter")]:
      await pg.focus(f".vk-host [data-v='{ch}']"); await pg.keyboard.press("Space" if key==" " else key); await pg.wait_for_timeout(60)
    v=await pg.input_value("#ans"); ok("자판 키 포커스 + Enter/Space 로 'ser'", v=="ser", v)
    ok("자판 키 활성화 뒤에도 화면 자판 그대로", await pg.evaluate("()=>document.querySelector('#ans').readOnly && !!document.querySelector('.vk-host .vk')"))
    # 스크린리더 활성화 = pointer 없이 click 만
    await pg.evaluate("()=>{ const b=document.querySelector(\".vk-host [data-v='@bs']\"); b.click(); }"); await pg.wait_for_timeout(60)
    await pg.evaluate("()=>{ const b=document.querySelector(\".vk-host [data-v='r']\"); b.click(); }"); await pg.wait_for_timeout(60)
    v=await pg.input_value("#ans"); ok("스크린리더 click(⌫, r) 입력", v=="ser", v)
    await pg.focus(".vk-host [data-v='@ok']"); await pg.keyboard.press("Enter"); await pg.wait_for_timeout(500)
    ok("↵ 키 포커스 + Enter → 정답", await pg.evaluate(okfb), await pg.evaluate(FB))
    await ctx.close()
    # ③ 마우스·터치 자판 입력 한 번만
    ctx,pg=await page(state(),mobile=True)
    await pg.evaluate(ASK,["e1","recall"]); await pg.wait_for_timeout(500)
    for ch in "ser": await pg.click(f".vk-host [data-v='{ch}']")
    v=await pg.input_value("#ans"); ok("마우스 자판 'ser' 한 번씩", v=="ser", v)
    await pg.click(".vk-host [data-v='@bs']"); v=await pg.input_value("#ans"); ok("마우스 ⌫ 한 번만", v=="se", v)
    await pg.tap(".vk-host [data-v='r']"); await pg.wait_for_timeout(60); v=await pg.input_value("#ans"); ok("터치 탭 'r' 한 번만", v=="ser", v)
    await pg.tap(".vk-host [data-v='@ok']"); await pg.wait_for_timeout(500)
    ok("터치 ↵ → 정답(한 번만 채점)", await pg.evaluate(okfb), await pg.evaluate(FB))
    await ctx.close()
    # ④ 물리 키보드로 바꾼 뒤 터치로 입력칸 누르면 화면 자판 돌아옴
    ctx,pg=await page(state(),mobile=True)
    await pg.evaluate(ASK,["e1","recall"]); await pg.wait_for_timeout(500)
    await pg.keyboard.type("s"); await pg.wait_for_timeout(100)
    await pg.tap("#ans"); await pg.wait_for_timeout(150)
    r=await pg.evaluate("()=>{ const i=document.querySelector('#ans'); return [i.readOnly, !!document.querySelector('.vk-host .vk'), i.value]; }")
    ok("물리 키보드 뒤 입력칸 터치 → 화면 자판 다시(값 유지)", r==[True,True,"s"], r)
    await ctx.close()
    # ⑤ 「한자까지 정확히」 회귀
    ctx,pg=await page(state(ui="ko",lang="ja",strict=True))
    await pg.evaluate(ASK,["k1","recall"]); await pg.wait_for_timeout(500)
    r=await pg.evaluate("()=>{ const i=document.querySelector('#ans'); return [i.readOnly, !!document.querySelector('.vk-host')]; }")
    ok("strictKanji: 화면 자판 없음(폰 키보드)", r==[False,False], r)
    await pg.fill("#ans","遅い"); await pg.keyboard.press("Enter"); await pg.wait_for_timeout(500)
    ok("strictKanji: 遅い 정답", await pg.evaluate(okfb), await pg.evaluate(FB))
    await ctx.close()
    ok("페이지 오류 없음", not errs, errs[:3])
    await b.close()
  print(f"t_kbd: {sum(R)}/{len(R)}"); return all(R)
import sys; sys.exit(0 if asyncio.run(main()) else 1)
