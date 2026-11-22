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
    ok("칸→문제 (빈칸 없는 카드 3칸=recall, 5칸=cloze↔recall 대체)", r[:5]==["study","meaning","meaning","recall","recall"] and r[5] in ("recall","order","write","speak"), r)
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
    ok("새 단어 첫날 = 맞혀보기 + 1칸 (2문제)", all(sorted(v)==sorted(["study:0","meaning:1"]) for v in r.values()) and len(r)>=1, r)
    # 세션 진행: 새 단어 맞힘 → step 2
    r=await pg.evaluate("""()=>{ const t=window.__t, S=t.S(); const s=t.buildSession(); s.queue=s.queue.filter(i=>i.id==='n1'); s.remaining={n1:s.queue.length}; t.setSES(s);
      try{ t.settleItem(true); t.settleItem(true); }catch(e){ return 'err '+e; } const c=S.cards.n1; return [c.step, c.isNew, c.stepAt===t.today(), S.meta.session ? !!S.meta.session.ask : 'none']; }""")
    ok("새 단어 2문제 다 맞음 → 2칸", r[0]==2 and r[1]==False and r[2], r)
    # 옛 세션 이어 하기 (st 없음, mode cloze 등)
    r=await pg.evaluate("""()=>{ const t=window.__t, S=t.S(); t.setSES({queue:[{id:'a3',mode:'cloze'},{id:'a3',mode:'recall'}],done:0,failed:{},remaining:{a3:2},finished:[],state:null});
      try{ t.settleItem(true); t.settleItem(true); }catch(e){ return 'err '+e; } const c=S.cards.a3; return [c.step, c.reps]; }""")
    ok("옛 세션(st 없음) 이어 하기 정상 → 칸 +1", r==[5,4], r)
    await pg.wait_for_timeout(300)
    ok("페이지 오류 없음", not errs, errs[:3])
    await b.close()
  print("결과:", "통과" if all(R) else "실패"); sys.exit(0 if all(R) else 1)
asyncio.run(main())
