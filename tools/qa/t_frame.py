# 문형 틀(frame) 문제 (요청 R-1123-루프-frame문제): presets/index.json 「more」 등록 → <lang>-frame.json 덱 추가 → 틀 빈칸 문제(고르기·쓰기)
# 견본 데이터는 테스트 안에서만(가로채기). 기존 단어장 출제 변화 0 확인.
import asyncio, json
from playwright.async_api import async_playwright
R=[]
def ok(n,c,i=""): R.append(c); print(("✅" if c else "❌"), n, "" if c else i)
U="http://localhost:8765/index.html"
JA={"v":1,"kind":"frame","items":[
 {"id":"nagara","w":"〜ながら","m":{"ko":"~하면서","ja":"〜しながら（同時に）"},"x":[{"s":"音楽を聞き{ながら}勉強します。","t":{"ko":"음악을 들으면서 공부해요."}},{"s":"歩き{ながら}話しましょう。","t":{"ko":"걸으면서 이야기해요."}},{"s":"泣き{ながら}笑った。","t":{"ko":"울면서 웃었다."}}],"d":["ても","のに","ために"]},
 {"id":"temo","w":"〜ても","m":{"ko":"~해도","ja":"〜しても"},"x":[{"s":"雨が降っ{ても}行きます。","t":{"ko":"비가 와도 갈게요."}},{"s":"何度聞い{ても}わからない。","t":{"ko":"몇 번 들어도 모르겠어."}},{"s":"遠く離れ{ても}忘れない。","t":{"ko":"멀리 떨어져도 잊지 않아."}}]},
 {"id":"youni","w":"〜ように","m":{"ko":"~하도록","ja":"〜するように"},"x":[{"s":"忘れない{ように}書きます。","t":{"ko":"잊지 않도록 써요."}},{"s":"届く{ように}歌うよ。","t":{"ko":"닿도록 노래할게."}},{"s":"夢が叶う{ように}。","t":{"ko":"꿈이 이루어지도록."}}]}]}
KO={"v":1,"kind":"frame","items":[
 {"id":"janha","w":"-잖아","m":{"ja":"〜じゃない（確認）","ko":"~잖아"},"x":[{"s":"내가 말했{잖아}.","t":{"ja":"言ったじゃない。"}},{"s":"너도 알{잖아}.","t":{"ja":"君も知ってるじゃない。"}},{"s":"좋아한다고 했{잖아}.","t":{"ja":"好きって言ったじゃない。"}}],"d":["는데","니까"]},
 {"id":"rge","w":"-ㄹ게","m":{"ja":"〜するね（約束）","ko":"~할게"},"x":[{"s":"내일 전화{할게}.","t":{"ja":"明日電話するね。"}},{"s":"기다{릴게}.","t":{"ja":"待ってるね。"}}]},
 {"id":"cheoreom","w":"-처럼","m":{"ja":"〜のように","ko":"~처럼"},"x":[{"s":"꿈{처럼} 사라졌어.","t":{"ja":"夢のように消えた。"}},{"s":"별{처럼} 빛나.","t":{"ja":"星のように輝く。"}}]}]}
OLD={f"k{i}":dict(id=f"k{i}",lang=l,word=w,meaning=m,deck="default",due="2099-01-01",level=2,reps=2,isNew=False,lapses=0,created=i,log=[],step=2) for i,(l,w,m) in enumerate([("ja","先生","선생님"),("ja","学校","학교"),("ja","猫","고양이"),("ja","犬","개"),("ko","학교","学校"),("ko","고양이","猫"),("ko","선생님","先生"),("ko","개","犬")])}
def base(ui,lang):
  return {"cards":json.loads(json.dumps(OLD)),"meta":{"setup":1,"tutAsked":1,"loginAsked":1,"tutWant":0,"days":{"2026-11-20":True},"settings":{"ui":ui,"lang":lang,"homePet":False}}}
async def setup_routes(ctx):
  async def idx(route):
    r=await route.fetch(); d=await r.json()
    d["more"]={"ja":[{"id":"frame","kind":"frame","label":"J-POPによく出る文型","labelKo":"J-POP에 자주 나오는 문형","n":3}],"ko":[{"id":"frame","kind":"frame","label":"K-POPによく出る文型","labelKo":"K-POP에 자주 나오는 문형","n":3}],"es":[{"id":"../x","kind":"frame","label":"bad"}]}
    await route.fulfill(response=r, body=json.dumps(d, ensure_ascii=False), headers={**r.headers, "content-type":"application/json"})
  await ctx.route("**/presets/index.json", idx)
  await ctx.route("**/presets/ja-frame.json", lambda rt: rt.fulfill(body=json.dumps(JA,ensure_ascii=False), content_type="application/json"))
  await ctx.route("**/presets/ko-frame.json", lambda rt: rt.fulfill(body=json.dumps(KO,ensure_ascii=False), content_type="application/json"))
SES_JS="""(a)=>{ const t=window.__t, S=t.S(); const c=Object.values(S.cards).find(c=>c.frame&&c.frame.id===a.id); t.setSES({queue:[{id:c.id,mode:a.mode,st:a.st}],done:0,failed:{},remaining:{},finished:[],state:null,course:{n:12,newK:0,ok:0,g:0}});
  document.querySelector('#sessionStart').classList.add('hidden'); document.querySelector('#sessionBox').classList.remove('hidden'); t.nextItem(); return c.id; }"""
NOSCROLL="()=>document.scrollingElement.scrollHeight<=innerHeight+1"
async def main():
  async with async_playwright() as pw:
    b=await pw.chromium.launch(); errs=[]
    # 단위: frameSplit
    ctx=await b.new_context(); pg=await ctx.new_page(); await pg.goto(U); await pg.wait_for_timeout(800)
    r=await pg.evaluate("()=>[__t.frameSplit('音楽を聞き{ながら}勉強します。'), __t.frameSplit('括弧なし'), __t.frameSplit('{a}{b}'), __t.frameSplit('x{ }y')]")
    ok("frameSplit: {틀} 자리 나눔·없음/두 개/빈 칸은 null", r[0]=={"before":"音楽を聞き","answer":"ながら","after":"勉強します。"} and r[1] is None and r[2] is None and r[3] is None, r)
    await ctx.close()
    for W,H in [(390,844),(360,640)]:
      for ui,lang,data,ans,wrong in [("ko","ja",JA,"ながら","ても"),("ja","ko",KO,"잖아","는데")]:
        tag=f"{W}×{H} ui={ui}"
        ctx=await b.new_context(viewport={"width":W,"height":H}); await setup_routes(ctx); pg=await ctx.new_page(); pg.on("pageerror",lambda e:errs.append(str(e)))
        await pg.goto(U); await pg.evaluate("s=>localStorage.setItem('focus-vocab-v1', s)", json.dumps(base(ui,lang))); await pg.goto(U); await pg.wait_for_timeout(1200)
        old=await pg.evaluate("()=>{const S=__t.S(); return Object.values(S.cards).map(c=>[c.id,c.word,c.meaning,c.due,c.step].join('|')).sort().join(',')}")
        modes0=await pg.evaluate("()=>{const S=__t.S(); return Object.values(S.cards).map(c=>[0,1,2,3,4,5].map(s=>__t.stepMode(c,s)).join('/')).join(',')}")
        # 단어장 세트 화면에 「more」 줄 + 이상한 id는 안 보임
        await pg.evaluate("()=>{__t.showView('add'); try{__t.setAddPanel&&__t.setAddPanel('preset')}catch(e){} return __t.renderPresets()}"); await pg.wait_for_timeout(600)
        r=await pg.evaluate("()=>({b:[...document.querySelectorAll('[data-mx]')].map(x=>x.dataset.mx), t:(document.querySelector('.pmore')||{}).innerText||''})")
        lab="J-POP에 자주 나오는 문형" if ui=="ko" else "K-POPによく出る文型"
        ok(f"{tag}: 세트 화면에 새 덱 줄({lab})", r["b"]==["frame"] and lab in r["t"], r)
        await pg.evaluate("()=>__t.addPresetMore(__t.S().meta.settings.lang,'frame',document.querySelector('[data-mx]'))"); await pg.wait_for_timeout(500)
        r=await pg.evaluate("()=>{const S=__t.S(); const f=Object.values(S.cards).filter(c=>c.frame); const d=S.meta.decks.find(x=>x.preset===S.meta.settings.lang+'-frame'); return {n:f.length, w:f.map(c=>c.word).sort(), m:f.map(c=>c.meaning), ex:f.every(c=>!c.example&&!c.form), deck:!!d, kind:d&&d.kind, same:f.every(c=>c.deck===d.id), saved:Object.values(JSON.parse(localStorage.getItem('focus-vocab-v1')).cards).filter(c=>c.frame).length}}")
        ok(f"{tag}: 덱 추가 → 틀 카드 3장(c.frame, 예문·form 비움), 저장됨", r["n"]==3 and r["ex"] and r["deck"] and r["kind"]=="frame" and r["same"] and r["saved"]==3, r)
        ok(f"{tag}: 뜻은 화면 언어", all((("~" in m) if ui=="ko" else ("〜" in m)) for m in r["m"]), r["m"])
        again=await pg.evaluate("async()=>{ const r=await __t.addPresetMore(__t.S().meta.settings.lang,'frame'); return [r, Object.values(__t.S().cards).filter(c=>c.frame).length] }")
        ok(f"{tag}: 두 번 추가해도 카드 늘지 않음", again==[False,3], again)
        r=await pg.evaluate("()=>{const S=__t.S(); const c=Object.values(S.cards).find(c=>c.frame); return [0,1,2,3,4,5].map(s=>__t.stepMode(c,s)).concat([__t.leechMode(c,1),__t.leechMode(c,2)]).join('/')}")
        ok(f"{tag}: 틀 카드 칸→형식 study/pick/frame…, 끈질긴 단어 규칙도 frame", r=="study/pick/frame/frame/frame/frame/pick/frame", r)
        old2=await pg.evaluate("()=>{const S=__t.S(); return Object.values(S.cards).filter(c=>!c.frame).map(c=>[c.id,c.word,c.meaning,c.due,c.step].join('|')).sort().join(',')}")
        modes1=await pg.evaluate("()=>{const S=__t.S(); return Object.values(S.cards).filter(c=>!c.frame).map(c=>[0,1,2,3,4,5].map(s=>__t.stepMode(c,s)).join('/')).join(',')}")
        ok(f"{tag}: 기존 카드·기존 카드 출제 형식 그대로", old==old2 and modes0==modes1, (modes0,modes1))
        fid=data["items"][0]["id"]
        # 고르기(1칸)
        await pg.evaluate(SES_JS, {"id":fid,"mode":"pick","st":1}); await pg.wait_for_timeout(400)
        r=await pg.evaluate("()=>({opts:[...document.querySelectorAll('.pk-b')].map(b=>b.textContent), s:(document.querySelector('.sentence')||{}).innerText||'', blank:!!document.querySelector('.sentence .blank'), head:(document.querySelector('.modehead')||{}).innerText||''})")
        hd="문형 빈칸" if ui=="ko" else "文型の穴埋め"
        ok(f"{tag}: 고르기 화면 — 빈칸 문장·보기 4개(정답+오답 틀)·머리 「{hd}」", r["blank"] and len(r["opts"])==4 and ans in r["opts"] and ans not in r["s"] and hd in r["head"], r)
        ok(f"{tag}: 고르기 화면 스크롤 없음", await pg.evaluate(NOSCROLL)); await pg.screenshot(path=f"/tmp/fr_pick_{ui}_{W}.png")
        await pg.evaluate("(a)=>[...document.querySelectorAll('.pk-b')].find(b=>b.textContent===a).click()", ans); await pg.wait_for_timeout(200)
        r=await pg.evaluate("()=>({ok:!!document.querySelector('.feedback.ok'), fill:(document.querySelector('.blank.filled')||{}).textContent})")
        ok(f"{tag}: 맞는 틀 고르면 정답·빈칸 채움", r["ok"] and r["fill"]==ans, r)
        # 쓰기(2칸+): 맞는 틀 / 〜 붙여도 정답 / 다른 틀 오답
        for typed,exp in [(ans,"ok"),(("〜" if lang=="ja" else "-")+ans,"ok"),(wrong,"no")]:
          await pg.evaluate(SES_JS, {"id":fid,"mode":"frame","st":3}); await pg.wait_for_timeout(300)
          r0=await pg.evaluate("()=>({inp:!!document.querySelector('#ans'), s:(document.querySelector('.sentence')||{}).innerText||'', tr:(document.querySelector('.q-sub')||{}).innerText||''})")
          if typed==ans:
            ok(f"{tag}: 쓰기 화면 — 입력칸·빈칸 문장·번역", r0["inp"] and ans not in r0["s"] and len(r0["tr"])>0, r0)
            ok(f"{tag}: 쓰기 화면 스크롤 없음", await pg.evaluate(NOSCROLL)); await pg.screenshot(path=f"/tmp/fr_write_{ui}_{W}.png")
          await pg.evaluate("(v)=>{const i=document.querySelector('#ans'); i.readOnly=false; i.value=v; document.querySelector('#chk').click()}", typed); await pg.wait_for_timeout(250)
          r=await pg.evaluate("()=>document.querySelector('.feedback.ok')?'ok':document.querySelector('.feedback.no')?'no':'?'")
          ok(f"{tag}: 쓰기 '{typed}' → {exp}", r==exp, r)
        # 판에 섞였을 때: 새 틀 카드도 buildCourse 로 나옴(study→pick)
        r=await pg.evaluate("()=>{const t=__t,S=t.S(); S.meta.days[t.addDays(t.today(),-1)]=true; t.setSES(null); const s=t.buildCourse(); const q=s.queue.filter(it=>S.cards[it.id]&&S.cards[it.id].frame); return q.map(it=>it.mode)}")
        ok(f"{tag}: 판 만들기에 틀 카드는 study·pick 형식으로", len(r)>0 and set(r)<= {"study","pick","frame"}, r)
        await ctx.close()
    await b.close()
    ok("페이지 오류 없음", not errs, errs[:3])
  print(f"\n{sum(R)}/{len(R)} 통과"); raise SystemExit(0 if all(R) else 1)
asyncio.run(main())
