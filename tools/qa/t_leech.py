# 검수단 R1-10-2: 끈질긴 단어(lapses≥3)가 칸 1 pick으로 매일 같은 형식·하루 판의 5/12·보스 칸 차지
# → 한 판에 끈질긴 단어 2개까지 · 먼저 보여 주기(study) · 날마다 형식 돌리기(칸은 그대로)
import asyncio, json
from playwright.async_api import async_playwright
R=[]
def ok(n,c,i=""): R.append(c); print(("✅" if c else "❌"), n, "" if c else i)
def mk(n_due, n_leech, lang="es"):
  cs={}
  for i in range(n_due): cs[f"d{i}"]=dict(id=f"d{i}",lang=lang,word=f"pal{i}",meaning=f"뜻{i}",example="",level=2,due="2026-01-01",isNew=False,lapses=(5 if i<n_leech else 0),reps=3,created=i,introduced="2025-12-01",mastered=False,relearn=False,log=[],deck="default",step=(1 if i<n_leech else 2),S=3,D=5,last="2025-12-20")
  return cs
async def seed(pg, cards):
  meta={"setup":1,"tutAsked":1,"loginAsked":1,"days":{},"settings":{"ui":"ko","lang":"es"},"stepv":1}
  await pg.evaluate("s=>localStorage.setItem('focus-vocab-v1', s)", json.dumps({"cards":cards,"meta":meta})); await pg.reload(); await pg.wait_for_timeout(1500)
async def main():
  async with async_playwright() as pw:
    b=await pw.chromium.launch(); pg=await b.new_page(viewport={"width":390,"height":844}); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)))
    await pg.goto("http://localhost:8765/index.html")
    await seed(pg, mk(40,5))
    r=await pg.evaluate("""()=>{ const t=window.__t, S=t.S(), q=t.buildCourse().queue; const L=new Set(q.filter(i=>S.cards[i.id].lapses>=3).map(i=>i.id));
      const st=[...L].map(id=>{ const its=q.filter(i=>i.id===id); return its[0].mode==='study' && its.length>=2; });
      const b=q[q.length-2]; return {n:q.length, leech:L.size, studyFirst:st.every(x=>x), boss:b.k, bossLeech:S.cards[b.id].lapses>=3, ks:q.map(i=>i.k+':'+i.mode).join(' ')}; }""")
    ok("끈질긴 단어 5개 덱: 한 판에 2개 이하", r["leech"]<=2 and r["leech"]>=1, r)
    ok("끈질긴 단어는 먼저 보여 주기(study) → 문제", r["studyFirst"], r)
    ok("판은 12칸 · 보스는 끈질긴 단어", r["n"]==12 and r["boss"]=="b" and r["bossLeech"], r)
    r=await pg.evaluate("""()=>{ const t=window.__t, S=t.S(); const out=[]; for(const id of ['d0','d1','d2','d3','d4']){ const c=S.cards[id]; let same=0, ms=new Set(); for(let k=0;k<30;k++){ const a=t.leechMode(c,1,t.addDays('2026-11-01',k)), b2=t.leechMode(c,1,t.addDays('2026-11-01',k+1)); if(a===b2) same++; ms.add(a); } out.push([same, ms.size]); } return out; }""")
    ok("이틀 연속 같은 형식 아님(30일 × 5단어)", all(x[0]==0 for x in r), r)
    ok("형식이 돌아감(pick·meaning·recall)", all(x[1]>=3 for x in r), r)
    r=await pg.evaluate("""()=>{ const t=window.__t, S=t.S(), q=t.buildCourse().queue; return q.filter(i=>S.cards[i.id].lapses>=3 && i.mode!=='study').every(i=>i.st===1); }""")
    ok("형식이 바뀌어도 칸(st)은 그대로", r, r)
    # 판 끝까지 플레이 — 오류 없음, 칸 오르내리기 정상(asked = 지금 칸)
    r=await pg.evaluate("""async()=>{ const t=window.__t, S=t.S(); const p=document.querySelector('#pet'); if(p && !p.classList.contains('hidden')) document.querySelector('#petClose').click();
      t.startSession(); const s=t.getSES(); let g=0; while(s.queue.length && g++<60) t.settleItem(true); await new Promise(r=>setTimeout(r,300)); return [s.done, ['d0','d1','d2','d3','d4'].map(id=>S.cards[id].step)]; }""")
    ok("판 끝까지 플레이 · 맞힌 끈질긴 단어는 한 칸만 오름", r[0]==12 and all(x in (1,2) for x in r[1]), r)
    # 끈질긴 단어만 있는 작은 덱
    await seed(pg, mk(3,3))
    r=await pg.evaluate("""()=>{ const t=window.__t, S=t.S(), q=t.buildCourse().queue; return [q.length, new Set(q.map(i=>i.id)).size]; }""")
    ok("끈질긴 단어 3개뿐인 덱 → 2개만, 판은 만들어짐", r[1]==2 and r[0]>=2, r)
    ok("페이지 오류 없음", not errs, errs)
    await b.close()
  print(f"t_leech: {sum(R)}/{len(R)}"); raise SystemExit(0 if all(R) else 1)
asyncio.run(main())
