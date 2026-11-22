# 레벨 디자인 v2 2단계(C) 테스트: 한 판 12문제 · 틀려도 칸 수 그대로 · 다음 판으로 넘김 · 첫 판 끝 = 하루 달성 1번 · 옛 세션
import asyncio, sys, json
from playwright.async_api import async_playwright
R=[]
def ok(n,c,i=""): R.append(c); print(("✅" if c else "❌"), n, "" if c else i)
def mk(n_due, n_new, lang="es"):
  cs={}
  for i in range(n_due): cs[f"d{i}"]=dict(id=f"d{i}",lang=lang,word=f"pal{i}",meaning=f"뜻{i}",example="",level=2,due="2026-01-01",isNew=False,lapses=(4 if i==0 else 0),reps=3,created=i,introduced="2025-12-01",mastered=False,relearn=False,log=[],deck="default",step=2+(i%3),S=5+i%7,D=5,last="2025-12-20")
  for i in range(n_new): cs[f"n{i}"]=dict(id=f"n{i}",lang=lang,word=f"neu{i}",meaning=f"새뜻{i}",example="",level=0,due=None,isNew=True,lapses=0,reps=0,created=1000+i,introduced=None,mastered=False,relearn=False,log=[],deck="default")
  return cs
async def seed(pg, cards, extra=None):
  meta={"setup":1,"tutAsked":1,"loginAsked":1,"days":{},"settings":{"ui":"ko","lang":"es"},"stepv":1}
  if extra: meta.update(extra)
  await pg.evaluate("s=>localStorage.setItem('focus-vocab-v1', s)", json.dumps({"cards":cards,"meta":meta})); await pg.reload(); await pg.wait_for_timeout(1500)
async def main():
  async with async_playwright() as pw:
    b=await pw.chromium.launch(); pg=await b.new_page(viewport={"width":390,"height":844}); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)))
    await pg.goto("http://localhost:8765/index.html")
    await seed(pg, {})
    r=await pg.evaluate("()=>window.__t.buildCourse().queue.length"); ok("복습 0·새 단어 0 → 빈 판", r==0, r)
    await seed(pg, mk(3,0))
    r=await pg.evaluate("()=>{ const s=window.__t.buildCourse(); return [s.queue.length, s.course.n, new Set(s.queue.map(i=>i.id)).size]; }"); ok("복습 3개만 → 3칸(+끈질긴 단어 보여 주기 1칸, R1-10-2)", r==[4,4,3], r)
    await seed(pg, mk(200,30))
    r=await pg.evaluate("""()=>{ const s=window.__t.buildCourse(), q=s.queue; const ks=q.map(i=>i.k).join(''); const per={}; q.forEach(i=>{ if(i.mode!=='study') per[i.id]=(per[i.id]||0)+1; });
      return {n:q.length, cn:s.course.n, ks, newc:Object.keys(per).filter(k=>k[0]==='n').length, dup:Object.entries(per).filter(([k,v])=>k[0]==='d'&&v>1).length, boss:q[10].id}; }""")
    ok("복습 200개(밀림)·새 단어 30 → 12칸: 몸풀기2·본편8·보스1·마무리1", r["n"]==12 and r["cn"]==12 and r["ks"][:2]=="ww" and r["ks"][-2:]=="bf" and r["dup"]==0, r)
    ok("새 단어 3개(×2칸) · 보스 = 끈질긴 단어", r["newc"]==3 and r["boss"]=="d0", r)
    await seed(pg, mk(0,10))
    r=await pg.evaluate("()=>{ const s=window.__t.buildCourse(); return [s.queue.length, s.queue.map(i=>i.mode+i.st).filter(x=>x==='study0').length]; }")
    ok("복습 없음 → 새 단어로 채움(하루 한도 안)", r[0]>=2 and r[0]<=12 and r[0]==2*r[1], r)
    # 틀려도 12 유지
    await seed(pg, mk(40,0))
    r=await pg.evaluate("""()=>{ const t=window.__t; const s=t.buildCourse(); t.setSES(s); t.startSession && 0;
      document.querySelector('#sessionStart').classList.add('hidden'); document.querySelector('#sessionBox').classList.remove('hidden');
      const lens=[]; for(let k=0;k<5;k++){ t.settleItem(false); const S2=t.getSES(); lens.push(S2.done+S2.queue.length); } return lens; }""")
    ok("틀려도 판의 칸 수 12 그대로", all(x==12 for x in r), r)
    r=await pg.evaluate("""()=>{ const t=window.__t, s=t.getSES(); let g=0; while(s.queue.length && g++<40){ t.settleItem(false); } return [s.done, (t.S().meta.carry||{}).ids||[]]; }""")
    ok("남은 복습 칸이 없으면 다음 판 첫 본편으로 넘김", r[0]==12 and len(r[1])>=1, r)
    r=await pg.evaluate("""()=>{ const t=window.__t, c=t.S().meta.carry.ids[0]; const s=t.buildCourse(); const i=s.queue.findIndex(q=>q.id===c); return [i, s.queue[i] && s.queue[i].k]; }""")
    ok("넘긴 문제는 다음 판 본편에", r[0]>=2 and r[1]=="m", r)
    # 첫 판 끝 = 하루 달성 1번
    await seed(pg, mk(30,0))
    r=await pg.evaluate("""async()=>{ const t=window.__t, S=t.S(), d=t.today(); document.querySelector('#petClose') && document.querySelector('#petClose').click();
      t.startSession(); const s=t.getSES(); let g=0, mid=null; while(s.queue.length>1 && g++<40){ t.settleItem(true); if(g===10) mid=S.meta.days[d]||null; }
      t.settleItem(true); await new Promise(r=>setTimeout(r,500)); const one=!!document.querySelector('#oneMore'); return [mid, S.meta.days[d], one, !!S.meta.session]; }""")
    ok("판 중간(10문제)엔 하루 달성 안 됨 → 첫 판 끝에 달성", r[0] is None and r[1]==True, r)
    ok("판 끝 화면 [한 판 더] · 세션 정리", r[2] and r[3]==False, r)
    r=await pg.evaluate("()=>document.documentElement.scrollHeight<=innerHeight+1")
    ok("판 끝 화면 한 화면(390×844)", r, r)
    # G: 360×640에서도 한 화면 · 버튼 한 줄([▶ 한 판 더] + 아이콘 📤·🍖·🏠)
    p2=await b.new_page(viewport={"width":360,"height":640}); p2.on("pageerror",lambda e:errs.append(str(e)))
    await p2.goto("http://localhost:8765/index.html"); await seed(p2, mk(30,0))
    r=await p2.evaluate("""async()=>{ const t=window.__t; document.querySelector('#petClose') && document.querySelector('#petClose').click(); t.startSession(); const s=t.getSES(); let g=0; while(s.queue.length && g++<40) t.settleItem(true);
      await new Promise(r=>setTimeout(r,3500)); const p=document.querySelector('#pet'); if(p && !p.classList.contains('hidden')) document.querySelector('#petClose').click(); await new Promise(r=>setTimeout(r,300));
      const bs=[...document.querySelectorAll('#sessionBox .row.ce-row button')], tops=new Set(bs.map(b=>Math.round(b.getBoundingClientRect().top)));
      return [document.documentElement.scrollHeight<=innerHeight+1, bs.length, tops.size, !!document.querySelector('#oneMore'), bs.filter(b=>b.classList.contains('ce-ic')).every(b=>b.getAttribute('aria-label'))]; }""")
    ok("판 끝 화면 한 화면(360×640) · 버튼 한 줄 · 아이콘에 이름", r[0] and r[1]>=2 and r[2]==1 and r[3] and r[4], r)
    r=await p2.evaluate("""async()=>{ const t=window.__t, S=t.S(); Object.keys(S.cards).forEach(k=>delete S.cards[k]);
      document.querySelector('#backHome').click(); await new Promise(r=>setTimeout(r,300)); t.setSES({queue:[{id:'d1',mode:'recall',st:3,k:'m'}],done:11,failed:{},remaining:{d1:1},finished:[],state:null,course:{n:12,i:11,newK:0,ok:11,g:11}});
      document.querySelector('#sessionStart').classList.add('hidden'); document.querySelector('#sessionBox').classList.remove('hidden'); t.settleItem(true); await new Promise(r=>setTimeout(r,800)); const p=document.querySelector('#pet'); if(p && !p.classList.contains('hidden')) document.querySelector('#petClose').click(); await new Promise(r=>setTimeout(r,300));
      const h=document.querySelector('#backHome'); return [!document.querySelector('#oneMore'), h.classList.contains('primary'), document.documentElement.scrollHeight<=innerHeight+1]; }""")
    ok("다음 판 없으면 「오늘 끝!」 + 🏠가 주 버튼 · 한 화면", r==[True,True,True], r)
    await p2.close()
    # 옛 세션(course 없음) 이어 하기
    await seed(pg, mk(5,0), {"session":{"day":"__TODAY__","lang":"es","queue":[{"id":"d1","mode":"meaning"},{"id":"d2","mode":"recall"}],"done":3,"failed":{},"remaining":{"d1":1,"d2":1},"finished":[]}})
    r=await pg.evaluate("""()=>{ const t=window.__t, S=t.S(); S.meta.session.day=t.today(); document.querySelector('#petClose') && document.querySelector('#petClose').click(); const rb=document.querySelector('#resumeBtn'); 
      t.setSES(null); return 1; }""")
    r=await pg.evaluate("""()=>{ const t=window.__t, S=t.S(); const z=S.meta.session; t.setSES({queue:z.queue,done:z.done,failed:{},remaining:z.remaining,finished:[],state:null}); t.settleItem(true); t.settleItem(true); return [t.getSES().queue.length, !t.getSES().course, S.cards.d1.reps]; }""")
    ok("옛 세션(course 없음) 옛 방식으로 끝까지", r==[0,True,4], r)
    # ── D: 자동 조절 · 복귀 판 · 녹아내림 ──
    await seed(pg, mk(60,30))
    r=await pg.evaluate("""()=>{ const t=window.__t, S=t.S(); const z=t.ddaState(); const a=[z.n];
      const run=(ok,g)=>{ t.setSES({queue:[],done:12,failed:{},remaining:{},finished:[],state:null}); return t.courseEnd({n:12,ok,g}); };
      run(12,12); a.push(t.ddaState().n); run(12,12); a.push(t.ddaState().n); run(12,12); a.push(t.ddaState().n);
      run(5,12); a.push(t.ddaState().n, t.ddaState().lo); run(10,12); a.push(t.ddaState().n, t.ddaState().lo);
      for(let k=0;k<6;k++) run(2,12); a.push(t.ddaState().n); return a; }""")
    ok("85% 조절: >92% +1(최대 4) · <75% −1(최소 1)+쉬운 문제 · 사이면 그대로", r==[3,4,4,4,3,1,3,0,1], r)
    r=await pg.evaluate("""()=>{ const t=window.__t, S=t.S(); S.cards.d0.lapses=0; S.meta.dda={n:1,h:[]}; const a=t.buildCourse().course.newK; S.meta.dda={n:4,h:[]}; const b=t.buildCourse().course.newK; S.meta.dda={n:3,h:[]}; return [a,b]; }""")
    ok("판당 새 단어 수 = dda.n", r==[1,4], r)
    r=await pg.evaluate("""()=>{ const t=window.__t, S=t.S(); S.meta.days={}; S.meta.days[t.addDays(t.today(),-4)]=true; S.meta.days[t.addDays(t.today(),-5)]=true;
      for(let k=1;k<=20;k++){ const c=S.cards['d'+k]; c.S=2; c.last=t.addDays(t.today(),-5); }
      const s=t.buildCourse(); const Rs=s.queue.map(i=>t.Rof(S.cards[i.id])); const low=Rs.filter(r=>r<.4).length; return [t.isReturnDay(), s.course.ret, s.course.newK, s.queue.some(i=>i.mode==='study'), low]; }""")
    ok("복귀 판(3일+): 새 단어 0 · R<0.4는 뒤 판으로", r[:4]==[True,1,0,False] and r[4]==0, r)
    r=await pg.evaluate("""()=>{ const t=window.__t, S=t.S(); S.meta.days={}; S.meta.days[t.addDays(t.today(),-3)]=true; S.meta.days[t.addDays(t.today(),-4)]=true; S.meta.days[t.addDays(t.today(),-5)]=true;
      document.querySelector('#petClose') && document.querySelector('#petClose').click(); return 1; }""")
    r=await pg.evaluate("""async()=>{ const t=window.__t, S=t.S(); const inv0=JSON.stringify((S.meta.pet||{}).inv||{}); t.startSession(); const s=t.getSES(); let g=0; while(s.queue.length && g++<40) t.settleItem(true); await new Promise(r=>setTimeout(r,600));
      const tot=o=>Object.values(o||{}).reduce((a,b)=>a+b,0); return [s.course.ret, document.querySelector('#sessionBox .say .bubble').textContent, tot(S.meta.pet.inv)-tot(JSON.parse(inv0))]; }""")
    ok("복귀 판 끝: 「기다렸다냥」 + 간식 +2 (하루 간식 위에)", r[0]==1 and "기다렸다냥" in r[1] and r[2]>=2, r)
    r=await pg.evaluate("""()=>{ const t=window.__t, S=t.S(); S.meta.days={}; [6,5,4,2].forEach(k=>S.meta.days[t.addDays(t.today(),-k)]=true); return t.meltPoints(); }""")
    ok("녹아내림: 빠진 날 −1 (3일 → 빠짐 → 1일 → 빠짐 = 2, 예전 −1.5면 1)", r==2, r)
    # H: 같은 날 둘째 판부터 간식 1~2개 · 하루 5판 상한 · granted 그대로
    await seed(pg, mk(80,0))
    r=await pg.evaluate("""async()=>{ const t=window.__t, S=t.S(), d=t.today(); document.querySelector('#petClose') && document.querySelector('#petClose').click();
      const tot=()=>Object.values((S.meta.pet||{}).inv||{}).reduce((a,b)=>a+b,0);
      const run=async(okAll)=>{ t.setSES(null); t.startSession(); const s=t.getSES(); let g=0; while(s.queue.length && g++<40) t.settleItem(okAll); await new Promise(r=>setTimeout(r,600)); const p=document.querySelector('#pet'); if(p && !p.classList.contains('hidden')) document.querySelector('#petClose').click(); };
      await run(true); const g1=S.meta.pet.granted[d], a=tot();
      await run(true); const b=tot(), txt=(document.querySelector('#sessionBox .ce-gift')||{}).textContent||'';
      await run(false); const c=tot();
      S.meta.pet.cg.n=5; await run(true); const e=tot();
      return [g1>0, S.meta.pet.granted[d]===g1, b-a, c-b, e-c, txt.includes('+'), S.meta.pet.cg.d===d]; }""")
    ok("둘째 판 끝 간식 +2(90%↑)·+1(낮으면) · 「+N」 표시 · 5판 넘으면 없음 · granted 그대로", r==[True,True,2,1,0,True,True], r)
    ok("페이지 오류 없음", not errs, errs[:3])
    await b.close()
  print("결과:", "통과" if all(R) else "실패"); sys.exit(0 if all(R) else 1)
asyncio.run(main())
