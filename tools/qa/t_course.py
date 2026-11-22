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
    r=await pg.evaluate("()=>{ const s=window.__t.buildCourse(); return [s.queue.length, s.course.n, new Set(s.queue.map(i=>i.id)).size]; }"); ok("복습 3개만 → 3칸", r==[3,3,3], r)
    await seed(pg, mk(200,30))
    r=await pg.evaluate("""()=>{ const s=window.__t.buildCourse(), q=s.queue; const ks=q.map(i=>i.k).join(''); const per={}; q.forEach(i=>per[i.id]=(per[i.id]||0)+1);
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
    # 옛 세션(course 없음) 이어 하기
    await seed(pg, mk(5,0), {"session":{"day":"__TODAY__","lang":"es","queue":[{"id":"d1","mode":"meaning"},{"id":"d2","mode":"recall"}],"done":3,"failed":{},"remaining":{"d1":1,"d2":1},"finished":[]}})
    r=await pg.evaluate("""()=>{ const t=window.__t, S=t.S(); S.meta.session.day=t.today(); document.querySelector('#petClose') && document.querySelector('#petClose').click(); const rb=document.querySelector('#resumeBtn'); 
      t.setSES(null); return 1; }""")
    r=await pg.evaluate("""()=>{ const t=window.__t, S=t.S(); const z=S.meta.session; t.setSES({queue:z.queue,done:z.done,failed:{},remaining:z.remaining,finished:[],state:null}); t.settleItem(true); t.settleItem(true); return [t.getSES().queue.length, !t.getSES().course, S.cards.d1.reps]; }""")
    ok("옛 세션(course 없음) 옛 방식으로 끝까지", r==[0,True,4], r)
    ok("페이지 오류 없음", not errs, errs[:3])
    await b.close()
  print("결과:", "통과" if all(R) else "실패"); sys.exit(0 if all(R) else 1)
asyncio.run(main())
