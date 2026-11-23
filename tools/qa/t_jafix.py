# 검수단 R1-41-1·R1-42-1·R1-42-2 (요청 R-1123-검수단-외래어오인정·히라가나경계·빈칸읽기힌트)
# ① ko 카드 뜻 맞히기: 외래어 뼈대 비교는 가타카나 답 + 뜻 칸에 같은 뼈대 가타카나가 있을 때만 (곰←かめ·감←ガム 오답)
# ② 히라가나 단어 빈칸: 다른 낱말 속 조각(いずれ·かくれんぼ·ことば·ときどき·ないしょ)은 빈칸 없음
# ③ 일본어 빈칸 힌트 줄에 읽기 전체가 안 보임(悪口 → わるくち 없음)
import asyncio, json, datetime
from playwright.async_api import async_playwright
R=[]
def ok(n,c,i=""): R.append(bool(c)); print(("✅" if c else "❌"), n, "" if c else i)
def ds(d): return (datetime.datetime.now(datetime.timezone.utc)-datetime.timedelta(days=d, hours=4)).strftime("%Y-%m-%d")
def card(i,lang,word,meaning,ex="",exk="",reading="",**k):
  d=dict(id=i,lang=lang,word=word,meaning=meaning,deck="default",example=ex,exampleKo=exk,due=ds(1),level=2,reps=3,lapses=0,created=1,introduced="2025-12-01",S=4,D=5,last=ds(5),step=4,log=[])
  if reading: d["reading"]=reading
  d.update(k); return d
JA=[card("waru","ja","悪口","わるくち · 욕, 험담","トムの悪口はやめて！","톰 험담은 그만해!",reading="わるくち"),
    card("shozoku","ja","所属","しょぞく · 소속","チームに所属してる？","팀에 소속돼 있어?",reading="しょぞく"),
    card("kaisei","ja","快晴","かいせい · 쾌청","今日は快晴だ。","오늘은 쾌청하다.",reading="かいせい"),
    card("zure","ja","ずれ","차이, 어긋남","いずれは死ぬんだよ。","언젠가는 죽는 거야."),
    card("koto","ja","こと","것, 일","ことばを覚える。","말을 외운다.")]
KO=[card("gom","ko","곰","熊（くま）"), card("gam","ko","감","柿（かき）"), card("keopi","ko","커피","コーヒー、コーヒー豆（コーヒーまめ）"),
    card("byeol","ko","별","星","하늘에 별이 많다.","空に星が多い。")]
ES=[card("casa","es","casa","집","Mi casa es grande.","우리 집은 크다.")]
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
    # ── ① 외래어 오인정 ──
    ctx,pg=await page(390,844,state("ja","ko",KO),"ja-JP")
    L=lambda a,w,m: pg.evaluate("([a,w,m])=>window.__t.loanMatch(a,w,m)",[a,w,m])
    for a,w,m in [("かめ","곰","熊（くま）"),("カメ","곰","熊（くま）"),("かみ","감","柿（かき）"),("ガム","감","柿（かき）"),("しか","수고","苦労（くろう）"),("のり","나리","ユリ"),("こーひー","커피","コーヒー")]:
      ok(f"loanMatch {a}←{w} 오답", (await L(a,w,m)) is False)
    for a,w,m in [("コーヒー","커피","コーヒー、コーヒー豆"),("コーヒ","커피","コーヒー"),("バス","버스","バス"),("シック","시크","シック（chic）、粋"),("시크","シック","시크, 세련됨")]:
      ok(f"loanMatch {a}←{w} 정답(외래어 회귀)", (await L(a,w,m)) is True)
    n=await pg.evaluate("""async()=>{ let n=0,bad=0; for(const lv of ['beg','mid','adv']){ const d=await (await fetch('presets/ko-'+lv+'.json')).json();
      for(const x of d.items){ const runs=String(x[1]).match(/[ァ-ヺー]+/g)||[]; if(runs.some(r=>window.__t.loanMatch(r,x[0],x[1]))) n++;
        for(const h of ['かめ','かみ','しか','のり','ガム']) if(!runs.length && window.__t.loanMatch(h,x[0],x[1])) bad++; } } return [n,bad]; }""")
    ok("ko 단어장: 뜻에 가타카나 없는 카드에 엉뚱한 가나 정답 0", n[1]==0, n); ok("ko 단어장: 외래어 카드는 여전히 가타카나 답 정답(100장 이상)", n[0]>=100, n)
    # 화면: 곰 뜻 맞히기에 かめ → 정답 아님
    await pg.evaluate(ASK,["gom","meaning",4]); await pg.wait_for_timeout(350)
    if await pg.locator("#ans").count():
      await pg.fill("#ans","かめ"); await pg.click("#chk"); await pg.wait_for_timeout(400)
      ok("곰 뜻 맞히기 화면 'かめ' → 정답 아님", await pg.locator("#fb .feedback.ok").count()==0)
      await pg.evaluate(ASK,["keopi","meaning",4]); await pg.wait_for_timeout(350); await pg.fill("#ans","コーヒ"); await pg.click("#chk"); await pg.wait_for_timeout(400)
      ok("커피 뜻 맞히기 화면 'コーヒ' → 정답", await pg.locator("#fb .feedback.ok").count()>0)
    else: ok("뜻 맞히기 입력칸 있음", False)
    await ctx.close()
    # ── ② 히라가나 경계 ──
    ctx,pg=await page(390,844,state("ko","ja",JA),"ko-KR")
    F=lambda e,w: pg.evaluate("([e,w])=>window.__t.findForm(e,w)",[e,w])
    for e,w in [("いずれは死ぬんだよ。","ずれ"),("かくれんぼしよう。","かく"),("ことばを覚える。","こと"),("ときどき行く。","とき"),("ないしょだよ。","ない"),("おさんぽに行こう。","さん"),("先んずれば人を制す。","ずれ")]:
      ok(f"findForm {w} ← 「{e}」 빈칸 없음", (await F(e,w))=="", await F(e,w))
    for e,w in [("時間のずれがある。","ずれ"),("子供のとき、よく遊んだ。","とき"),("行ったことがある。","こと"),("駅はどっちですか。","どっち"),("お金がない。","ない"),("ないです。","ない"),("見るときに","とき"),("ずれ。","ずれ")]:
      ok(f"findForm {w} ← 「{e}」 정상 빈칸", (await F(e,w))==w, await F(e,w))
    for e,w in [("ホームシックだ。","シック"),("先生に会う。","生"),("책꽂이에 놓다.","책")]:
      ok(f"다른 글자 경계 회귀 {w} ← 「{e}」 빈칸 없음", (await F(e,w))=="")
    cp=await pg.evaluate("()=>window.__t.clozeParts({word:'ずれ',example:'いずれは死ぬんだよ。',lang:'ja'})")
    ok("clozeParts ずれ(いずれ 예문) = null", cp is None, cp)
    cp=await pg.evaluate("()=>window.__t.clozeParts({word:'こと',form:'こと',example:'ことばを覚える。',lang:'ja'})")
    ok("clozeParts こと(옛 form 저장, ことば) = null", cp is None, cp)
    # ── ③ 빈칸 읽기 힌트 ──
    for cid,rd,f0 in [("waru","わるくち","悪"),("shozoku","しょぞく","所"),("kaisei","かいせい","快")]:
      h=await hint(pg,cid,"cloze")
      ok(f"{cid} cloze 힌트: 읽기 {rd} 없음·첫 글자 {f0}", rd not in h and f"첫 글자 {f0}" in h and "·" in h, h)
    h=await hint(pg,"waru","study"); ok("悪口 study 힌트(읽기 없는 뜻 위) 회귀", "わるくち" not in h and "悪" in h, h)
    await pg.evaluate("()=>{ const s=window.__t.S(); s.cards.waru.example=''; }")
    await pg.evaluate(ASK,["kaisei","cloze",4]); await pg.wait_for_timeout(300); await pg.fill("#ans","快晴"); await pg.click("#chk"); await pg.wait_for_timeout(400)
    ok("快晴 cloze '快晴' 정답 그대로", await pg.locator("#fb .feedback.ok").count()>0)
    for W,H in [(390,844),(360,640)]:
      await pg.set_viewport_size({"width":W,"height":H}); await pg.evaluate(ASK,["shozoku","cloze",4]); await pg.wait_for_timeout(400)
      sc=await pg.evaluate("()=>document.documentElement.scrollHeight-innerHeight")
      ok(f"{W}×{H} 빈칸 화면 스크롤 없음", sc<=1, sc)
      if W==360: await pg.screenshot(path="/tmp/jafix_360.png")
    await ctx.close()
    ctx,pg=await page(390,844,state("ja","es",ES),"ja-JP")
    h=await hint(pg,"casa","cloze"); ok("es casa cloze 힌트 회귀", "집" in h and "「c」" in h, h)
    await ctx.close()
    ctx,pg=await page(390,844,state("ja","ko",KO),"ja-JP")
    h=await hint(pg,"byeol","cloze"); ok("ko 별 cloze 힌트 회귀(한 글자)", "별" not in h and "星" in h, h)
    await ctx.close()
    ok("페이지 오류 없음", not errs, errs)
    await b.close()
  print(f"t_jafix: {sum(R)}/{len(R)}"); 
  if not all(R): raise SystemExit(1)
asyncio.run(main())
