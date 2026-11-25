# 11-25 친구 탭: 하단 메뉴 「친구」(단어장 왼쪽) · 친구/선물함 탭 · 받은·보낸 카드 · 친구 냥이 보기 · 14세 미만 숨김
import asyncio, json, re
from playwright.async_api import async_playwright
R=[]
def ok(n,c,i=""): R.append(bool(c)); print(("✅" if c else "❌"), n, "" if c else i)
B="http://localhost:8765/index.html"
CARD={"c1":{"id":"c1","lang":"ja","word":"先生","meaning":"선생님","isNew":True,"level":0,"due":None,"lapses":0,"reps":0,"log":[],"created":1,"u":1,"deck":"default"}}
FR={"list":[{"id":"f"*64,"nick":"ミカ","fur":"cheese","stats":{"st":5,"wk":12,"lang":"ko"},"bday":"","since":"2026-11-25"}],"ann":{},"at":9e12}
def meta(by=1998, fr=None):
  m={"setup":1,"tutAsked":1,"loginAsked":1,"days":{},"settings":{"ui":"ko","lang":"ja","homePet":False},"stepv":1,"by":by,"nick":{"name":"테스트냥","key":"k"*36,"srv":1}}
  if fr: m["fr"]=fr
  return m
async def seed(pg, m, q=""):
  await pg.goto(B); await pg.evaluate("s=>localStorage.setItem('focus-vocab-v1', s)", json.dumps({"cards":CARD,"meta":m}))
  await pg.goto(B+q); await pg.wait_for_timeout(1800)
async def main():
  async with async_playwright() as pw:
    b=await pw.chromium.launch()
    for vw,vh in [(360,640),(390,844)]:
      ctx=await b.new_context(viewport={"width":vw,"height":vh}, locale="ko-KR"); pg=await ctx.new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)))
      await ctx.route(re.compile(r"supabase\.co"), lambda r: r.fulfill(status=200, content_type="application/json", body=json.dumps({"list":FR["list"]})))
      await ctx.route(re.compile(r"(mymemory|tatoeba|wiktionary|tosspayments)"), lambda r: r.abort())
      await seed(pg, meta(by=2015))
      ok(f"{vw} 14세 미만 친구 메뉴 숨김", await pg.evaluate("()=>document.querySelector('#snFr').classList.contains('hidden')"))
      await pg.evaluate("()=>window.__t.showView('fr')"); ok(f"{vw} 14세 미만 친구 화면 못 엶", await pg.evaluate("()=>document.body.dataset.view")!="fr")
      card={"v":1,"n":"ミカ","c":"happy","w":"mint","m":"お誕生日おめでとう！","p":"생일 축하해!","ml":"ja","pl":"ko","to":"테스트냥","k":"bday"}
      enc=await pg.evaluate("o=>window.__t.b64uEnc(o)", card)
      await seed(pg, meta(fr=FR), "?g="+enc+"&src=gift"); await pg.wait_for_timeout(600)
      ok(f"{vw} 친구 메뉴 보임·단어장 왼쪽", await pg.evaluate("()=>{ const b=document.querySelector('#snFr'); return !b.classList.contains('hidden') && b.nextElementSibling.dataset.view==='list'; }"))
      g=await pg.evaluate("()=>window.__t.giftState()"); ok(f"{vw} 받은 카드 선물함에 저장(새 표시)", len(g["recv"])==1 and g["recv"][0].get("nw")==1 and g["recv"][0]["o"]["n"]=="ミカ", g)
      ok(f"{vw} 새 선물 점", await pg.evaluate("()=>document.querySelector('#snFr').classList.contains('dot')"))
      await pg.evaluate("()=>{ const p=document.querySelector('.sheet-bg'); p && p.remove(); }")
      await pg.click("#snFr"); await pg.wait_for_timeout(500)
      ok(f"{vw} 친구 탭: 친구 목록", "ミカ" in await pg.evaluate("()=>document.querySelector('#frView').textContent"))
      await pg.click("#frView [data-cat]"); await pg.wait_for_timeout(400)
      ok(f"{vw} 친구 냥이 보기(치즈 털 그림)", "cheese.webp" in await pg.evaluate("()=>(document.querySelector('#frCatImg img')||{}).src||''"))
      await pg.click("#frCatImg"); ok(f"{vw} 냥이 쓰다듬기 반응", await pg.evaluate("()=>document.querySelector('#frCatImg').classList.contains('boing')"))
      await pg.evaluate("()=>{ const p=document.querySelector('.sheet-bg'); p && p.remove(); }")
      await pg.click('[data-frt="gift"]'); await pg.wait_for_timeout(300)
      ok(f"{vw} 선물함 탭: 받은 카드 1줄", await pg.evaluate("()=>document.querySelectorAll('.gf-row').length")==1)
      sw=await pg.evaluate("()=>document.documentElement.scrollWidth"); ok(f"{vw} 선물함 가로 넘침 없음", sw<=vw, sw)
      await pg.click(".gf-row"); await pg.wait_for_timeout(500)
      ok(f"{vw} 새 카드는 상자부터", await pg.evaluate("()=>!!document.querySelector('#cdBox')"))
      ok(f"{vw} 열어 보면 새 표시 지움", await pg.evaluate("()=>!window.__t.giftState().recv[0].nw"))
      await pg.evaluate("()=>{ const p=document.querySelector('.sheet-bg'); p && p.remove(); }")
      await pg.evaluate("()=>{ window.prompt=()=>null; }")
      await pg.evaluate("()=>window.__t.cardMake({nick:'ミカ'},'free')"); await pg.wait_for_timeout(300)
      await pg.fill("#cdM", "고마워!"); await pg.click("#cdSend"); await pg.wait_for_timeout(1200)
      g=await pg.evaluate("()=>window.__t.giftState()"); ok(f"{vw} 보낸 카드 저장", len(g["sent"])==1 and g["sent"][0]["o"]["m"]=="고마워!" and "?g=" in g["sent"][0]["k"], g["sent"][:1])
      await pg.evaluate("()=>{ const p=document.querySelector('.sheet-bg'); p && p.remove(); window.__t.FRV.g='sent'; window.__t.showView('fr'); }"); await pg.wait_for_timeout(300)
      await pg.click(".gf-row"); await pg.wait_for_timeout(1500)
      ok(f"{vw} 보낸 카드 바로 열림 + 다시 보내기", await pg.evaluate("()=>!!document.querySelector('.cd-img') && [...document.querySelectorAll('#cdIn .btn')].some(b=>b.textContent.includes('다시'))"))
      ok(f"{vw} 오류 없음", not errs, errs[:3])
      await ctx.close()
    await b.close()
  print("통과" if all(R) else "실패", f"{sum(R)}/{len(R)}"); raise SystemExit(0 if all(R) else 1)
asyncio.run(main())
