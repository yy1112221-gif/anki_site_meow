# 레벨 디자인 v2 1단계(B1) 테스트: 단어 계단 이사 · 칸→문제 · 오르내리기 · 가중치 · 동기화 병합 · 옛 세션
import asyncio, sys, json
from playwright.async_api import async_playwright
R=[]
def ok(n,c,i=""): R.append(c); print(("✅" if c else "❌"), n, "" if c else i)
OLD = {}
specs=[("n1",dict(isNew=True,level=0),0),("n2",dict(isNew=True,level=0,lapses=0),0),
 ("m1",dict(isNew=False,level=5,mastered=True),5),("m2",dict(isNew=False,level=3,mastered=True,lapses=4),5),
 ("a0",dict(isNew=False,level=0),2),("a1",dict(isNew=False,level=1),2),("a2",dict(isNew=False,level=2),3),
 ("a3",dict(isNew=False,level=3),4),("a4",dict(isNew=False,level=4),4),("a5",dict(isNew=False,level=5),4),
 ("l1",dict(isNew=False,level=1,lapses=3),2),("l2",dict(isNew=False,level=2,lapses=3),2),("l3",dict(isNew=False,level=3,lapses=5),3),
 ("l4",dict(isNew=False,level=4,lapses=3),3),("l5",dict(isNew=False,level=5,lapses=9),3),("x2",dict(isNew=False,level=2,lapses=2),3),
 ("x3",dict(isNew=False,level=3,lapses=1),4),("x1",dict(isNew=False,level=1,lapses=2),2),("x4",dict(isNew=False,level=4,lapses=0),4),("x0",dict(isNew=False,level=0,lapses=3),2)]
for i,(k,o,_) in enumerate(specs):
  c=dict(id=k,lang="es",word="pal%d"%i,meaning="뜻%d"%i,example="",lapses=0,reps=0 if o.get("isNew") else 3,due=None if o.get("isNew") else "2026-01-01",created=1,introduced=None,mastered=False,relearn=False,log=[],u=111)
  c.update(o); OLD[k]=c
async def main():
  async with async_playwright() as pw:
    b=await pw.chromium.launch(); pg=await b.new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)))
    await pg.goto("http://localhost:8765/index.html")
    st={"cards":OLD,"meta":{"setup":1,"tutAsked":1,"loginAsked":1,"days":{},"settings":{"ui":"ko","lang":"es"},"mu":5}}
    await pg.evaluate("s=>localStorage.setItem('focus-vocab-v1', s)", json.dumps(st))
    await pg.reload(); await pg.wait_for_timeout(1500)
    r=await pg.evaluate("""()=>{ const S=window.__t.S(); return {st:Object.fromEntries(Object.values(S.cards).map(c=>[c.id,c.step])), at:Object.values(S.cards).some(c=>c.stepAt), v:S.meta.stepv, saved:JSON.parse(localStorage.getItem('focus-vocab-v1')).meta.stepv}; }""")
    exp={k:e for k,_,e in specs}
    ok("이사: 옛 카드 20종 → step 기대값", r["st"]==exp, {k:(r["st"].get(k),exp[k]) for k in exp if r["st"].get(k)!=exp[k]})
    ok("이사: stepAt 안 넣음 · stepv=1 저장", (not r["at"]) and r["v"]==1 and r["saved"]==1, r)
    r=await pg.evaluate("""o=>{ const S=window.__t.S(); const bad=[]; Object.keys(o).forEach(k=>{ const c=S.cards[k], a=o[k]; Object.keys(a).forEach(f=>{ if(JSON.stringify(c[f])!==JSON.stringify(a[f])) bad.push(k+'.'+f); }); Object.keys(c).forEach(f=>{ if(!(f in a) && !['step','rank','_linked'].includes(f)) bad.push(k+'+'+f); }); }); return bad; }""", OLD)
    ok("이사: 다른 키 변화 0 (u 포함)", r==[], r[:8])
    # 칸 → 문제
    r=await pg.evaluate("""()=>{ const t=window.__t; const c={id:'z',lang:'es',word:'hablar',meaning:'말하다',example:'',reps:0,level:1,lapses:0}; return [0,1,2,3,4,5].map(s=>t.stepMode(c,s)); }""")
    ok("칸→문제 (빈칸 없는 카드 3칸=recall, 5칸=cloze↔recall 대체)", r[:5]==["study","pick","meaning","recall","recall"] and r[5] in ("recall","order","write","speak"), r)
    r=await pg.evaluate("""()=>{ const t=window.__t; const c={id:'l',lang:'es',word:'hablar',meaning:'말하다',reps:4,level:3,lapses:4,step:4}; return t.stepItems(c).map(i=>[i.mode,i.st]); }""")
    ok("끈질긴 단어: 한 칸 아래 + 지금 칸 2문제", r==[["meaning",3],["recall",4]] or (len(r)==2 and r[0][1]==3 and r[1][1]==4), r)
    # 오르내리기
    r=await pg.evaluate("""()=>{ const t=window.__t; const c={step:2}; t.stepSettle(c,true,2); const a=c.step; t.stepSettle(c,true,3); const b=c.step; t.stepSettle(c,false,3); const d=c.step; const e={step:1}; t.stepSettle(e,false,1); return [a,b,d,e.step,c.stepAt===t.today()]; }""")
    ok("같은 날 두 번 맞혀도 한 칸만 · 틀리면 한 칸 아래(최소 1)", r==[3,3,2,1,True], r)
    # 가중치·졸업
    r=await pg.evaluate("""()=>{ const t=window.__t, d=t.addDays(t.today(),-30); const mk=()=>({id:'w',isNew:false,level:3,S:10,D:5,last:d,reps:3,lapses:0,log:[]});
      const a=mk(), b=mk(), c=mk(); t.schedule(a,true,1); t.schedule(b,true,3); t.schedule(c,true,4);
      const n=t.addDays(t.today(),0); const nw={id:'n',isNew:true,reps:0,lapses:0,log:[],level:0}; t.schedule(nw,true,1);
      const g={id:'g',isNew:false,level:5,S:400,D:2,last:t.addDays(t.today(),-200),reps:9,lapses:0,log:[]}; t.schedule(g,true,2);
      const g2={id:'g2',isNew:false,level:5,S:400,D:2,last:t.addDays(t.today(),-200),reps:9,lapses:0,log:[]}; t.schedule(g2,true,4);
      return {a:a.S,b:b.S,c:c.S,nw:nw.S,g:[!!g.mastered,!!g.due],g2:g2.mastered}; }""")
    ok("가중치: 1~2칸 < 3칸 < 4칸 S 증가", r["a"]<r["b"]<r["c"] and r["a"]>10, r)
    ok("새 단어 첫날 맞음 S=1.6", abs(r["nw"]-1.6)<1e-9, r)
    ok("졸업은 4칸 이상에서만", r["g"]==[False,True] and r["g2"]==True, r)
    # mergeData
    r=await pg.evaluate("""()=>{ const t=window.__t, S=t.S(); S.cards.a2.step=3; S.cards.a2.u=500; S.cards.a2.stepAt='2026-11-20';
      const rem={cards:JSON.parse(JSON.stringify(S.cards)),meta:{}}; rem.cards.a2.step=4; rem.cards.a2.u=100; rem.cards.a2.stepAt='2026-11-21';
      t.mergeData(rem); return [S.cards.a2.step, S.cards.a2.stepAt, S.cards.a2.u]; }""")
    ok("mergeData: A 3칸 · B 4칸 → 4 (늦은 stepAt)", r==[4,"2026-11-21",500], r)
    # 새 단어 첫날 2문제
    r=await pg.evaluate("""()=>{ const t=window.__t, S=t.S(); Object.values(S.cards).forEach(c=>{ if(!c.isNew) c.due=t.addDays(t.today(),5); }); const s=t.buildSession(); const per={}; s.queue.forEach(i=>{ per[i.id]=(per[i.id]||[]).concat([i.mode+':'+i.st]); }); return per; }""")
    ok("새 단어 첫날 = 맞혀보기 + 1칸 뜻 고르기 (2문제)", all(sorted(v)==sorted(["study:0","pick:1"]) for v in r.values()) and len(r)>=1, r)
    # 세션 진행: 새 단어 맞힘 → step 2
    r=await pg.evaluate("""()=>{ const t=window.__t, S=t.S(); const s=t.buildSession(); s.queue=s.queue.filter(i=>i.id==='n1'); s.remaining={n1:s.queue.length}; t.setSES(s);
      try{ t.settleItem(true); t.settleItem(true); }catch(e){ return 'err '+e; } const c=S.cards.n1; return [c.step, c.isNew, c.stepAt===t.today(), S.meta.session ? !!S.meta.session.ask : 'none']; }""")
    ok("새 단어 2문제 다 맞음 → 2칸", r[0]==2 and r[1]==False and r[2], r)
    # 옛 세션 이어 하기 (st 없음, mode cloze 등)
    r=await pg.evaluate("""()=>{ const t=window.__t, S=t.S(); t.setSES({queue:[{id:'a3',mode:'cloze'},{id:'a3',mode:'recall'}],done:0,failed:{},remaining:{a3:2},finished:[],state:null});
      try{ t.settleItem(true); t.settleItem(true); }catch(e){ return 'err '+e; } const c=S.cards.a3; return [c.step, c.reps]; }""")
    ok("옛 세션(st 없음) 이어 하기 정상 → 칸 +1", r==[5,4], r)
    # ── B2: trap·pick·juku ──
    pg2=await b.new_page(viewport={"width":390,"height":844}); e2=[]; pg2.on("pageerror",lambda e:e2.append(str(e)))
    await pg2.goto("http://localhost:8765/index.html")
    words=[("今朝","けさ · 오늘 아침"),("財布","さいふ · 지갑"),("近い","ちかい · 가깝다"),("行く","いく · 가다"),("食べる","たべる · 먹다"),("水","みず · 물"),("雑誌","ざっし · 잡지")]
    cards={f"j{i}":dict(id=f"j{i}",lang="ja",word=w,meaning=m,example="",level=1,due="2026-01-01",isNew=False,lapses=0,reps=2,created=i,introduced="2026-01-01",mastered=False,relearn=False,log=[],deck="default",step=1) for i,(w,m) in enumerate(words)}
    await pg2.evaluate("s=>localStorage.setItem('focus-vocab-v1', s)", json.dumps({"cards":cards,"meta":{"setup":1,"tutAsked":1,"loginAsked":1,"days":{},"settings":{"ui":"ko","lang":"ja"},"stepv":1}}))
    await pg2.reload(); await pg2.wait_for_timeout(1500)
    r=await pg2.evaluate("""async()=>{ const t=window.__t, S=t.S(); await t.jaxLoad(); const tr=t.trapOpts(S.cards.j1), pk=t.pickOpts(S.cards.j2), nj=t.trapOpts(S.cards.j3);
      return {tr: tr && [tr.ans, tr.opts.length, tr.opts.includes('ざいふ')], pk: pk && [pk.ans, pk.opts.length, new Set(pk.opts).size, pk.opts.every(o=>!/^[ぁ-ゖ]+ ·/.test(o))], nj: nj, jk: !!(t.jaxOf(S.cards.j0)||{}).juku}; }""")
    ok("trap 보기 = 정답 읽기 + 함정 (財布 → さいふ/ざいふ…)", r["tr"] and r["tr"][0]=="さいふ" and r["tr"][1]>=2 and r["tr"][2], r)
    ok("pick 보기 4개 · 겹침 없음 · 읽기 앞머리 지움", r["pk"]==["가깝다",4,4,True], r)
    ok("trap 데이터 없는 단어 → trap 안 냄", r["nj"] is None, r)
    r=await pg2.evaluate("""()=>{ const d=window.__t.diffKind; return [d('ざっし','ざし'), d('さいふ','ざいふ'), d('きょう','きょ'), d('とうきょう','ときょう'), d('いく','ゆく')]; }""")
    ok("diffKind: 촉음·탁음·장음·없음", r==["촉음","탁음","장음","장음",""], r)
    # 화면: trap 2×2 → 오답 고르면 빨강+정답 초록+차이 줄, 한 화면
    r=await pg2.evaluate("""()=>{ const t=window.__t, S=t.S(); t.setSES({queue:[{id:'j1',mode:'pick',st:1}],done:0,failed:{},remaining:{j1:1},finished:[],state:null});
      document.querySelector('#sessionStart').classList.add('hidden'); document.querySelector('#sessionBox').classList.remove('hidden'); t.nextItem();
      const bs=[...document.querySelectorAll('#sessionBox .pk-b')]; const wrong=bs.find(b=>b.textContent!=='さいふ'); wrong.click();
      return {n:bs.length, no:wrong.classList.contains('no'), okb:bs.some(b=>b.classList.contains('ok')&&b.textContent==='さいふ'), fb:document.querySelector('#fb').textContent, nx:!document.querySelector('#chk').disabled, sh:document.documentElement.scrollHeight<=innerHeight+1}; }""")
    ok("trap 화면: 2×2 버튼 · 오답 빨강 · 정답 초록 · 다음 버튼", r["n"]>=2 and r["no"] and r["okb"] and r["nx"] and "さいふ" in r["fb"], r)
    ok("trap 화면 스크롤 없음(390×844)", r["sh"], r)
    await pg2.evaluate("()=>document.querySelector('#chk').click()"); await pg2.wait_for_timeout(300)
    r=await pg2.evaluate("()=>{ const t=window.__t, Q=t.getSES().queue; const re=Q.length===1&&Q[0].st===1; t.settleItem(true); const c=t.S().cards.j1; return [re, c.step, c.lapses]; }")
    ok("trap 틀림 → 다시 내기(칸 유지) → 끝나면 칸 1(최소 1)·lapses +1", r==[True,1,1], r)
    # juku: 0칸 ★ 소개, 채점 없음
    r=await pg2.evaluate("""()=>{ const t=window.__t, S=t.S(); const c=S.cards.j0; c.isNew=true; c.step=0; t.setSES({queue:[{id:'j0',mode:'study',st:0},{id:'j0',mode:'pick',st:1}],done:0,failed:{},remaining:{j0:2},finished:[],state:null}); t.nextItem();
      const tag=!!document.querySelector('#sessionBox .juku-tag'); document.querySelector('#chk').click(); return [tag, !!t.getSES().failed.j0, t.getSES().queue.length]; }""")
    ok("★ juku 소개 화면 · 채점 없음", r==[True,False,1], r)
    await pg2.close()
    # 오프라인: ja-extra 받기 실패 → meaning
    pg3=await b.new_page(); e3=[]; pg3.on("pageerror",lambda e:e3.append(str(e)))
    await pg3.route("**/ja-extra.json", lambda rt: rt.abort())
    await pg3.goto("http://localhost:8765/index.html"); await pg3.wait_for_timeout(1500)
    await pg3.evaluate("s=>localStorage.setItem('focus-vocab-v1', s)", json.dumps({"cards":cards,"meta":{"setup":1,"tutAsked":1,"loginAsked":1,"days":{},"settings":{"ui":"ko","lang":"ja"},"stepv":1}}))
    await pg3.reload(); await pg3.wait_for_timeout(1500)
    r=await pg3.evaluate("""async()=>{ const t=window.__t; const j=await t.jaxLoad(); t.setSES({queue:[{id:'j1',mode:'pick',st:1}],done:0,failed:{},remaining:{j1:1},finished:[],state:null});
      document.querySelector('#sessionStart').classList.add('hidden'); document.querySelector('#sessionBox').classList.remove('hidden'); t.nextItem(); await new Promise(r=>setTimeout(r,2800));
      return [j, document.querySelectorAll('#sessionBox .pk-b').length, !!document.querySelector('#sessionBox #ans')]; }""")
    ok("ja-extra 실패(오프라인) → trap 대신 meaning, 오류 없음", r[0] is None and r[1]==0 and r[2] and not e3, [r,e3[:2]])
    await pg3.close()
    ok("B2 페이지 오류 없음", not e2, e2[:3])
    # ── B3: 고친 읽기·가나 ──
    pg4=await b.new_page(); e4=[]; pg4.on("pageerror",lambda e:e4.append(str(e)))
    await pg4.goto("http://localhost:8765/index.html")
    cs={"r1":dict(id="r1",lang="ja",word="世話",reading="せわする",meaning="せわする · 돌봄, 신세",isNew=False,level=2,reps=3,lapses=0,log=[],u=77,due="2026-12-01"),
        "r2":dict(id="r2",lang="ja",word="退院",reading="내가 쓴 읽기",meaning="내가 쓴 읽기 · 퇴원",isNew=True,level=0,reps=0,lapses=0,log=[],u=78),
        "r3":dict(id="r3",lang="ja",word="椅子",reading="いす",meaning="いす · 의자",isNew=False,level=3,reps=3,lapses=0,log=[],u=79,due="2026-12-01"),
        "r4":dict(id="r4",lang="ja",word="学生",reading="がくせい",meaning="がくせい · 학생",isNew=False,level=3,reps=3,lapses=0,log=[],u=80,due="2026-12-01")}
    await pg4.evaluate("s=>localStorage.setItem('focus-vocab-v1', s)", json.dumps({"cards":cs,"meta":{"setup":1,"tutAsked":1,"loginAsked":1,"days":{},"settings":{"ui":"ko","lang":"ja"},"stepv":1}}))
    await pg4.reload(); await pg4.wait_for_timeout(3500)
    r=await pg4.evaluate("""()=>{ const t=window.__t, S=t.S(), a=S.cards.r1, b=S.cards.r2; const sv=JSON.parse(localStorage.getItem('focus-vocab-v1'));
      return {a:[a.reading,a.meaning,a.u,a.due], b:[b.reading,b.meaning], rfix:S.meta.rfix, saved:sv.cards.r1.reading, rd:t.readingOf(a)}; }""")
    ok("C7 고친 읽기: せわする → せわ (뜻 앞 읽기도) · u·due 그대로", r["a"]==["せわ","せわ · 돌봄, 신세",77,"2026-12-01"] and r["saved"]=="せわ" and r["rfix"]==1, r)
    ok("C7 사용자가 바꾼 읽기는 그대로", r["b"]==["내가 쓴 읽기","내가 쓴 읽기 · 퇴원"], r)
    r=await pg4.evaluate("""()=>{ const t=window.__t, S=t.S(); S.meta.settings.strictKanji=true; const a=t.ansOk(S.cards.r3,'いす','椅子'), b=t.ansOk(S.cards.r4,'がくせい','学生'); S.meta.settings.strictKanji=false; return [t.isKanaWord(S.cards.r3), t.isKanaWord(S.cards.r4), a, b]; }""")
    ok("C8 가나 단어: 「한자까지 정확히」여도 가나 답 정답(다른 단어는 오답)", r[0] and (not r[1]) and r[2]!="no" and r[3]=="no", r)
    r=await pg4.evaluate("""()=>{ const t=window.__t; t.setSES({queue:[{id:'r3',mode:'meaning',st:2}],done:0,failed:{},remaining:{r3:1},finished:[],state:null});
      document.querySelector('#sessionStart').classList.add('hidden'); document.querySelector('#sessionBox').classList.remove('hidden'); t.nextItem(); return document.querySelector('#sessionBox .word').textContent; }""")
    ok("C8 가나 단어는 가나를 크게 표시", r=="いす", r)
    # ── E: 한자 형제 한 줄 ──
    r=await pg4.evaluate("""async()=>{ const t=window.__t; await t.kjxLoad(); const a=t.kanjiSib({lang:'ja',word:'学生'}), b=t.kanjiSib({lang:'es',word:'hola'}), c=t.kanjiSib({lang:'ja',word:'ねこ'}); return [a,b,c]; }""")
    ok("C9 한자 형제 한 줄(学生 → 学 형제: …, 자기 단어 빼고 3개)", r[0].count("·")==2 and "学生" not in [x.strip() for x in r[0].split(":")[1].split("<")[0].split("·")] and r[1]=="" and r[2]=="", r)
    r=await pg4.evaluate("""()=>{ const t=window.__t; t.setSES({queue:[{id:'r4',mode:'pick',st:1}],done:0,failed:{},remaining:{r4:1},finished:[],state:null}); t.nextItem(); const bs=[...document.querySelectorAll('#sessionBox .pk-b')]; if(!bs.length) return 'nogrid'; const w=bs.find(b=>!b.classList.contains('x')&&b.textContent!=='がくせい'); w.click(); return !!document.querySelector('#fb .kj-sib'); }""")
    ok("C9 틀린 문제 피드백에 형제 줄", r==True, r)
    r=await pg4.evaluate("()=>document.body.innerHTML.includes('EDRDG') || (window.__t.S().meta.settings.ui==='ko')")
    # ── F: 사전형 유도 ──
    r=await pg4.evaluate("""()=>{ const t=window.__t; const k={lang:'ko',word:'예쁘다',form:'예쁜'}, j={lang:'ja',word:'働く',reading:'はたらく',form:'働いて'};
      return [t.dictFormHit(k,'예쁘다','예쁜'), t.dictFormHit(k,'예쁜','예쁜'), t.dictFormHit(k,'예쁘다','예쁘다'), t.dictFormHit(j,'はたらく','働いて'), t.dictFormHit(j,'働く','働いて'), t.dictFormHit(k,'귀엽다','예쁜')]; }""")
    ok("C4 사전형 답 → 유도(활용형 정답일 때만)", r==[True,False,False,True,True,False], r)
    r=await pg4.evaluate("""async()=>{ const t=window.__t, S=t.S(); S.meta.settings.lang='ko'; S.meta.settings.ui='ja'; S.cards.k1={id:'k1',lang:'ko',word:'예쁘다',meaning:'きれいだ',example:'길가에 예쁜 꽃들이 피었어요.',exampleKo:'道端にきれいな花が咲いた。',form:'예쁜',isNew:false,level:3,reps:3,lapses:0,log:[],step:3,due:'2026-01-01'};
      t.setSES({queue:[{id:'k1',mode:'cloze',st:3}],done:0,failed:{},remaining:{k1:1},finished:[],state:null}); t.nextItem(); await new Promise(r=>setTimeout(r,300));
      const i=document.querySelector('#ans'); if(!i) return 'noinput'; i.value='예쁘다'; document.querySelector('#chk').click(); await new Promise(r=>setTimeout(r,200));
      const a=[t.getSES().state.answered, (document.querySelector('#fb')||{}).textContent||'']; i.value='예쁘다'; document.querySelector('#chk').click(); await new Promise(r=>setTimeout(r,200)); a.push(t.getSES().state.answered); S.meta.settings.lang='ja'; S.meta.settings.ui='ko'; return a; }""")
    ok("C4 빈칸 화면: 첫 사전형 답은 유도(채점 안 함), 두 번째는 채점", r!="noinput" and r[0]==False and "文の形" in r[1] and r[2]==True, r)
    ok("B3 페이지 오류 없음", not e4, e4[:3])
    await pg4.close()
    await pg.wait_for_timeout(300)
    ok("페이지 오류 없음", not errs, errs[:3])
    await b.close()
  print("결과:", "통과" if all(R) else "실패"); sys.exit(0 if all(R) else 1)
asyncio.run(main())
