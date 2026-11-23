# 한 글자 정답 힌트 (요청 R-1123-검수단-한글자힌트, 검수단 R1-39-1)
# 정답이 한 글자(晩·手·별·꽃)면 「첫 글자 ○」 = 정답 전체 → study·cloze·끈질긴 단어 힌트 줄에 정답 글자 없음
# 일본어 한자는 읽기가 2글자 이상이면 「읽기 ば…」, 아니면 「한 글자 단어」 · 두 글자 이상은 「첫 글자 ○」 그대로
import asyncio, json, datetime
from playwright.async_api import async_playwright
R=[]
def ok(n,c,i=""): R.append(bool(c)); print(("✅" if c else "❌"), n, "" if c else i)
def ds(d): return (datetime.datetime.now(datetime.timezone.utc)-datetime.timedelta(days=d, hours=4)).strftime("%Y-%m-%d")
def card(i,lang,word,meaning,ex="",exk="",reading="",**k):
  d=dict(id=i,lang=lang,word=word,meaning=meaning,deck="default",example=ex,exampleKo=exk,due=ds(1),level=2,reps=3,lapses=0,created=1,introduced="2025-12-01",S=4,D=5,last=ds(5),step=4,log=[])
  if reading: d["reading"]=reading
  d.update(k); return d
JA=[card("ban","ja","晩","ばん · 저녁","晩に友だちと会う。","저녁에 친구와 만난다.",reading="ばん"),
    card("te","ja","手","て · 손","手を洗ってください。","손을 씻어 주세요.",reading="て"),
    card("hiro","ja","広い","ひろい · 넓다","この部屋は広い。","이 방은 넓다.",reading="ひろい"),
    card("yoru","ja","夜","よる · 밤",reading="よる"),
    card("me","ja","目","め · 눈",reading="め",lapses=4)]
KO=[card("byeol","ko","별","星","하늘에 별이 많다.","空に星が多い。"), card("kkot","ko","꽃","花"),
    card("hak","ko","학교","学校","학교에 간다.","学校に行く。"), card("bam","ko","밤","夜",lapses=4)]
def state(ui,lang,cards): return {"cards":{c["id"]:c for c in cards},"meta":{"setup":1,"tutAsked":1,"loginAsked":1,"days":{},"stepv":1,"settings":{"ui":ui,"lang":lang,"vk":False}}}
ASK="""([id,mode,st])=>{ const t=window.__t; document.querySelectorAll('.sheet-bg,#riskPop,.sup-ov,#s7').forEach(e=>e.remove()); const p=document.querySelector('#pet'); if(p&&!p.classList.contains('hidden')) document.querySelector('#petClose').click();
  t.showView('today'); t.setSES({queue:[{id,mode,st:st||4,k:'w'}],done:0,failed:{},remaining:{[id]:1},finished:[],state:null,course:{n:12,i:0,newK:0,ok:0,g:0}}); t.$('#sessionStart').classList.add('hidden'); t.$('#sessionBox').classList.remove('hidden'); t.nextItem(); return 1; }"""
HINT="()=>{ const h=document.querySelector('#sessionBox .q-hint'); return h?h.innerText.trim():''; }"
async def main():
  async with async_playwright() as pw:
    b=await pw.chromium.launch(); errs=[]
    async def page(W,H,st,loc):
      ctx=await b.new_context(viewport={"width":W,"height":H},locale=loc,has_touch=True,is_mobile=True)
      pg=await ctx.new_page(); pg.on("pageerror",lambda e:errs.append(str(e)))
      await pg.goto("http://localhost:8765/index.html")
      await pg.evaluate("s=>localStorage.setItem('focus-vocab-v1', s)", json.dumps(st)); await pg.reload(); await pg.wait_for_timeout(1500)
      return ctx,pg
    async def hint(pg,cid,mode,st=4):
      await pg.evaluate(ASK,[cid,mode,st]); await pg.wait_for_timeout(350); return await pg.evaluate(HINT)
    # 일본어 단어장, 화면 ko
    ctx,pg=await page(390,844,state("ko","ja",JA),"ko-KR")
    h=await hint(pg,"ban","study"); ok("晩 study(예문): 정답 글자 없음·읽기는 첫 음절만", "晩" not in h and "ばん" not in h and ("한 글자 단어" in h or "읽기 ば…" in h), h)
    h=await hint(pg,"yoru","study"); ok("夜 study(예문 없음, 위에 뜻만): '힌트: 읽기 よ…'", h=="힌트: 읽기 よ…", h)
    h=await hint(pg,"ban","cloze"); ok("晩 cloze: 정답 글자 없음·읽기 전체 없음(R1-42-2) → '읽기 ば…'", "晩" not in h and h=="힌트: 저녁 · 읽기 ば…", h)
    h=await hint(pg,"te","cloze"); ok("手 cloze: 정답 글자 없음·「한 글자 단어」", "手" not in h and "한 글자 단어" in h, h)
    await pg.evaluate("()=>{ const c=window.__t.S().cards.te; c.example=''; c.exampleKo=''; }")
    h=await hint(pg,"te","study"); ok("手(읽기 1글자, 예문 없음) study: 「한 글자 단어」·て 안 보임", "手" not in h and "て" not in h and h=="힌트: 한 글자 단어", h)
    h=await hint(pg,"hiro","cloze"); ok("広い(두 글자) cloze: 읽기 빼고 '첫 글자 広'", h=="힌트: 넓다 · 첫 글자 広", h)
    h=await hint(pg,"me","recall"); ok("目 끈질긴 단어 쓰기 힌트: 정답 글자 없음", "目" not in h and "め" not in h, h)
    # 정답 처리는 그대로
    await pg.evaluate(ASK,["ban","study",4]); await pg.wait_for_timeout(300)
    await pg.fill("#ans","晩"); await pg.click("#chk"); await pg.wait_for_timeout(400)
    ok("晩 study '晩' 정답 그대로", await pg.locator("#fb .feedback.ok").count()>0)
    await ctx.close()
    # 화면 ja
    ctx,pg=await page(390,844,state("ja","ja",JA),"ja-JP")
    h=await hint(pg,"yoru","study"); ok("夜 study(ui ja): 'ヒント：読み「よ」…'", h=="ヒント：読み「よ」…", h)
    await ctx.close()
    # 한국어 단어장, 화면 ja
    ctx,pg=await page(390,844,state("ja","ko",KO),"ja-JP")
    h=await hint(pg,"byeol","study"); ok("별 study: 정답 글자 없음·「1文字の単語」", "별" not in h and "1文字の単語" in h, h)
    h=await hint(pg,"byeol","cloze"); ok("별 cloze: 정답 글자 없음·뜻 星", "별" not in h and "星" in h and "1文字の単語" in h, h)
    h=await hint(pg,"kkot","study"); ok("꽃 study(예문 없음): 정답 글자 없음", "꽃" not in h and "1文字の単語" in h, h)
    h=await hint(pg,"hak","study"); ok("학교 study: 「첫 글자 학」 그대로", "「학」で始まる" in h, h)
    h=await hint(pg,"bam","recall"); ok("밤 끈질긴 단어 쓰기 힌트: 정답 글자 없음", "밤" not in h, h)
    await pg.evaluate(ASK,["byeol","cloze",4]); await pg.wait_for_timeout(300)
    await pg.fill("#ans","별"); await pg.click("#chk"); await pg.wait_for_timeout(400)
    ok("별 cloze '별' 정답 그대로", await pg.locator("#fb .feedback.ok").count()>0)
    # 360×640 한 화면
    await ctx.close(); ctx,pg=await page(360,640,state("ja","ko",KO),"ja-JP")
    await hint(pg,"byeol","cloze")
    sc=await pg.evaluate("()=>document.scrollingElement.scrollHeight-document.scrollingElement.clientHeight")
    ok("360×640 별 cloze 스크롤 없음", sc<=1, sc); await pg.screenshot(path="/tmp/t_onechar360.png")
    await ctx.close()
    ok("페이지 오류 없음", not errs, errs[:3])
    await b.close()
  print(f"t_onechar: {sum(R)}/{len(R)}"); return all(R)
import sys; sys.exit(0 if asyncio.run(main()) else 1)
