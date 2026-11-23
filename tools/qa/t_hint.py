# 문제·힌트 줄 정리 (요청 R-1123-검수단-뜻괄호원어 R1-22-1 · R-1123-루프-힌트줄정리 R1-22-2·R1-6-2·R1-5-1·R1-6-3)
# ① es 뜻 칸 괄호 속 원어('(sin embargo) 그러나')가 빈칸·뜻 보고 쓰기·먼저 맞혀보기·뜻 고르기 화면에 안 보임 (정답 공개 뒤 해설엔 그대로)
# ② 뜻 = 정답인 약어 카드(tv·dvd·cd)·정답이 든 뜻 조각(cv·pin)은 화면에 정답 없음 → 듣고 쓰기(음성 없으면 뜻 고르기)
# ③ 힌트 「첫 글자 ○」(받침 무관) ④ study 화면은 뜻을 힌트 줄에서 되풀이하지 않음·빈 번역 줄 없음 ⑤ 390×844·360×640 스크롤 없음·오류 없음
import asyncio, json, datetime, re
from playwright.async_api import async_playwright
R=[]
def ok(n,c,i=""): R.append(bool(c)); print(("✅" if c else "❌"), n, "" if c else i)
def ds(d): return (datetime.datetime.now(datetime.timezone.utc)-datetime.timedelta(days=d, hours=4)).strftime("%Y-%m-%d")
def card(i,lang,word,meaning,ex="",exk="",reading=""):
  d=dict(id=i,lang=lang,word=word,meaning=meaning,deck="default",example=ex,exampleKo=exk,due=ds(1),level=2,reps=3,lapses=0,created=1,introduced="2025-12-01",S=4,D=5,last=ds(5),step=4,log=[])
  if reading: d["reading"]=reading
  return d
CARDS=[card("emb","es","embargo","(sin embargo) 그러나","Sin embargo, no quiero ir.","그러나 가고 싶지 않다."),
  card("duc","es","duchar","(ducharse) 샤워하다"), card("men","es","menudo","(a menudo) 자주","Voy al cine a menudo.","나는 자주 영화관에 간다."),
  card("tv","es","tv","TV"), card("dvd","es","dvd","DVD"), card("cv","es","cv","이력서 (CV)"), card("pin","es","pin","핀, PIN 번호"),
  card("len","es","lento","느린","El tren es lento.","기차가 느리다."), card("mesa","es","mesa","탁자"), card("silla","es","silla","의자"), card("casa","es","casa","집"), card("perro","es","perro","개"),
  card("ban","ja","晩","ばん · 저녁",reading="ばん"), card("hiro","ja","広い","ひろい · 넓다",reading="ひろい")]
def state(ui="ko", lang="es", cards=None):
  cs={c["id"]:c for c in (cards or CARDS) if c["lang"]==lang}
  return {"cards":cs,"meta":{"setup":1,"tutAsked":1,"loginAsked":1,"days":{},"stepv":1,"settings":{"ui":ui,"lang":lang,"vk":False}}}
INIT="""(()=>{ window.__spoken=[]; const V=%s; if(V===null) return;
  try{ class U{ constructor(t){ this.text=t; this.lang=''; this.voice=null; } } window.SpeechSynthesisUtterance=U;
    speechSynthesis.getVoices=()=>V; speechSynthesis.speak=u=>window.__spoken.push({text:u.text,lang:u.lang}); speechSynthesis.cancel=()=>{}; }catch(e){} })()"""
ESV=[{"name":"es","lang":"es-ES","localService":True,"default":False,"voiceURI":"es"},{"name":"ko","lang":"ko-KR","localService":True,"default":True,"voiceURI":"ko"},{"name":"ja","lang":"ja-JP","localService":True,"default":False,"voiceURI":"ja"}]
ASK="""([id,mode,st])=>{ const t=window.__t; document.querySelectorAll('.sheet-bg,#riskPop,.sup-ov,#s7').forEach(e=>e.remove()); const p=document.querySelector('#pet'); if(p&&!p.classList.contains('hidden')) document.querySelector('#petClose').click();
  t.showView('today'); t.setSES({queue:[{id,mode,st:st||4,k:'w'}],done:0,failed:{},remaining:{[id]:1},finished:[],state:null,course:{n:12,i:0,newK:0,ok:0,g:0}}); t.$('#sessionStart').classList.add('hidden'); t.$('#sessionBox').classList.remove('hidden'); t.nextItem(); return 1; }"""
STAGE="()=>{ const s=document.querySelector('#sessionBox .stage'), g=document.querySelector('#pkG'); return (s?s.innerText:'')+' | '+(g?g.innerText:''); }"
SCROLL="()=>{ const e=document.scrollingElement; const st=document.querySelector('#sessionBox .stage'); return [e.scrollHeight-e.clientHeight, st?st.scrollHeight-st.clientHeight:0]; }"
async def main():
  async with async_playwright() as pw:
    b=await pw.chromium.launch(); errs=[]
    async def page(W,H,st,voices=ESV,loc="ko-KR"):
      ctx=await b.new_context(viewport={"width":W,"height":H},locale=loc,has_touch=True,is_mobile=True)
      await ctx.add_init_script(INIT%json.dumps(voices))
      pg=await ctx.new_page(); pg.on("pageerror",lambda e:errs.append(str(e)))
      await pg.goto("http://localhost:8765/index.html")
      await pg.evaluate("s=>localStorage.setItem('focus-vocab-v1', s)", json.dumps(st)); await pg.reload(); await pg.wait_for_timeout(1500)
      return ctx,pg
    ctx,pg=await page(390,844,state())
    # ① qMean 단위
    Q=[("embargo","es","(sin embargo) 그러나","그러나"),("duchar","es","(ducharse) 샤워하다","샤워하다"),("menudo","es","(a menudo) 자주","자주"),
       ("gracia","es","은혜, 우아함 (gracias 고마워요)","은혜, 우아함"),("tv","es","TV",""),("dvd","es","DVD",""),("cv","es","이력서 (CV)","이력서"),("pin","es","핀, PIN 번호","핀"),
       ("organización no gubernamental","es","非政府組織 (NGO)","非政府組織"),("sres","es","各位 (Señores の略)","各位"),("lento","es","느린","느린"),("ser","es","~이다, ~이 되다","~이다, ~이 되다"),
       ("tv","es","テレビ","テレビ"),("引き出す","ja","ひきだす（引き出す） · 끌어내다","ひきだす（引き出す） · 끌어내다"),("끄집어내다","ko","引っ張り出す (hikidasu)","引っ張り出す (hikidasu)"),("mes","es","달 (월)","달 (월)")]
    for w,lg,m,want in Q:
      got=await pg.evaluate("([w,l,m])=>window.__t.qMean(m,{word:w,lang:l})",[w,lg,m]); ok(f"qMean {w}: {m!r} → {want!r}", got==want, got)
    # ② 화면: 괄호 원어 숨김
    for cid,word in [("emb","embargo"),("duc","duchar"),("men","menudo")]:
      for mode in ["study","cloze","recall"]:
        await pg.evaluate(ASK,[cid,mode,3]); await pg.wait_for_timeout(350)
        tx=await pg.evaluate(STAGE)
        ok(f"{word} {mode}: 화면에 정답 원어 없음", word[:5].lower() not in tx.lower().replace("____",""), tx)
    # 정답 공개 뒤 해설엔 원래 뜻 그대로
    await pg.evaluate(ASK,["emb","recall",3]); await pg.wait_for_timeout(300)
    await pg.fill("#ans","embargo"); await pg.click("#chk"); await pg.wait_for_timeout(400)
    fb=await pg.inner_text("#fb"); ok("정답 공개 뒤 해설엔 '(sin embargo) 그러나' 그대로", "sin embargo" in fb, fb)
    # 뜻 고르기 보기에도 원어 없음
    await pg.evaluate(ASK,["emb","pick",1]); await pg.wait_for_timeout(400)
    g=await pg.evaluate("()=>{ const g=document.querySelector('#pkG'); return g?g.innerText:null; }")
    ok("embargo 뜻 고르기 보기에 'sin embargo' 없음·'그러나' 있음", g and "embargo" not in g and "그러나" in g, g)
    # ③ 약어 카드: 화면에 정답 없음 → 듣고 쓰기
    for cid in ["tv","dvd"]:
      for mode in ["study","recall"]:
        await pg.evaluate("()=>{window.__spoken.length=0}")
        await pg.evaluate(ASK,[cid,mode,3]); await pg.wait_for_timeout(400)
        tx=await pg.evaluate(STAGE); sp=await pg.evaluate("()=>window.__spoken.map(s=>s.text)")
        ok(f"{cid} {mode}: 화면에 정답 문자열 없음·듣기 버튼·소리로 냄", not re.search(r"\b"+cid+r"\b",tx,re.I) and await pg.locator("#sessionBox [data-say]").count()>0 and cid in sp, [tx,sp])
    await pg.evaluate(ASK,["tv","recall",3]); await pg.wait_for_timeout(300)
    await pg.fill("#ans","tv"); await pg.click("#chk"); await pg.wait_for_timeout(400)
    ok("tv 듣고 쓰기: 'tv' 정답", await pg.locator("#fb .feedback.ok").count()>0, await pg.inner_text("#fb"))
    for cid,bad in [("cv","cv"),("pin","pin")]:
      await pg.evaluate(ASK,[cid,"recall",3]); await pg.wait_for_timeout(350)
      tx=await pg.evaluate(STAGE); ok(f"{cid} recall: 뜻 조각에 정답 없음", not re.search(r"\b"+bad+r"\b",tx,re.I) and ("이력서" in tx or "핀" in tx), tx)
    # ④ 힌트 문구: 「첫 글자 ○」·study는 뜻 되풀이 없음
    await pg.evaluate(ASK,["len","cloze",3]); await pg.wait_for_timeout(350)
    h=await pg.inner_text("#sessionBox .q-hint"); ok("일반 카드 빈칸 힌트: '힌트: 느린 · 첫 글자 l'", h.strip()=="힌트: 느린 · 첫 글자 l", h)
    await pg.evaluate(ASK,["mesa","study",0]); await pg.wait_for_timeout(350)
    h=await pg.inner_text("#sessionBox .q-hint"); w=await pg.inner_text("#sessionBox .stage .word")
    ok("study(예문 없음): 위에 뜻, 힌트 줄은 첫 글자만", w.strip()=="탁자" and h.strip()=="힌트: 첫 글자 m", [w,h])
    n=await pg.evaluate("()=>[...document.querySelectorAll('#sessionBox .q-sub')].filter(e=>!e.textContent.trim()).length"); ok("빈 번역 줄 없음", n==0, n)
    await ctx.close()
    # 일본어 카드 晩·広い 힌트(받침 무관 꼴)
    ctx,pg=await page(390,844,state("ko","ja"))
    for cid,ch in [("ban","晩"),("hiro","広")]:
      await pg.evaluate(ASK,[cid,"study",0]); await pg.wait_for_timeout(350)
      h=await pg.inner_text("#sessionBox .q-hint"); ok(f"{ch} study 힌트 '첫 글자 {ch}'·'로 시작' 없음", f"첫 글자 {ch}" in h and "로 시작" not in h and "저녁" not in h and "넓다" not in h, h)
    await ctx.close()
    # ko 카드(화면 ja) 끄집어내다 예문 없음 study: 뜻 중복 없음·빈 줄 없음
    ko=[card("kk","ko","끄집어내다","引っ張り出す"),card("k2","ko","사과","りんご"),card("k3","ko","학교","学校"),card("k4","ko","의자","椅子")]
    ctx,pg=await page(390,844,state("ja","ko",ko),loc="ja-JP")
    await pg.evaluate(ASK,["kk","study",0]); await pg.wait_for_timeout(350)
    tx=await pg.evaluate(STAGE); h=await pg.inner_text("#sessionBox .q-hint")
    ok("끄집어내다 study(ui ja): 뜻 한 번만·힌트 「끄」で始まる", tx.count("引っ張り出す")==1 and h.strip()=="ヒント：「끄」で始まる", [tx,h])
    n=await pg.evaluate("()=>[...document.querySelectorAll('#sessionBox .stage p')].filter(e=>!e.textContent.trim()&&e.getBoundingClientRect().height>0).length"); ok("끄집어내다 study: 빈 줄 없음", n==0, n)
    await ctx.close()
    # ⑤ 음성 없음(es 음성 0개) → 약어 카드는 뜻 고르기
    ctx,pg=await page(390,844,state(),voices=[ESV[1],ESV[2]])
    await pg.evaluate(ASK,["tv","recall",3]); await pg.wait_for_timeout(400)
    r=await pg.evaluate("()=>[!!document.querySelector('#pkG'), !!document.querySelector('#ans')]"); ok("es 음성 없음: tv는 뜻 고르기로", r[0] and not r[1], r)
    await ctx.close()
    # ⑥ 390×844·360×640 스크롤 없음
    for W,H in [(390,844),(360,640)]:
      ctx,pg=await page(W,H,state())
      for cid,mode in [("emb","cloze"),("tv","recall"),("mesa","study"),("men","study")]:
        await pg.evaluate(ASK,[cid,mode,3]); await pg.wait_for_timeout(400)
        s=await pg.evaluate(SCROLL); ok(f"{W}×{H} {cid} {mode}: 스크롤 없음", s[0]<=1 and s[1]<=4, s)
        if W==360 and cid=="tv": await pg.screenshot(path="/tmp/t_hint_tv360.png")
        if W==360 and cid=="emb": await pg.screenshot(path="/tmp/t_hint_emb360.png")
      await ctx.close()
    ok("페이지 오류 없음", not errs, errs[:3])
    await b.close()
  print(f"t_hint: {sum(R)}/{len(R)}");
  if not all(R): raise SystemExit(1)
asyncio.run(main())
