# 검수단 R1-10-1: 계속 틀리는 단어가 「한 판 더」마다 같은 3~4문제 판으로 끝없이 반복되던 것
# → 같은 단어는 하루 2판까지 · carry는 단어마다 하루 1번 · 오늘 이미 한 판 했으면 4문제 아래 판은 안 만듦
import asyncio, json
from playwright.async_api import async_playwright
R=[]
def ok(n,c,i=""): R.append(c); print(("✅" if c else "❌"), n, "" if c else i)
def mk(n_due, lang="es"):
  cs={}
  for i in range(n_due): cs[f"d{i}"]=dict(id=f"d{i}",lang=lang,word=f"pal{i}",meaning=f"뜻{i}",example="",level=2,due="2026-01-01",isNew=False,lapses=(4 if i<2 else 0),reps=3,created=i,introduced="2025-12-01",mastered=False,relearn=False,log=[],deck="default",step=2,S=3,D=5,last="2025-12-20")
  return cs
async def seed(pg, cards, extra=None):
  meta={"setup":1,"tutAsked":1,"loginAsked":1,"days":{},"settings":{"ui":"ko","lang":"es"},"stepv":1}
  if extra: meta.update(extra)
  await pg.evaluate("s=>localStorage.setItem('focus-vocab-v1', s)", json.dumps({"cards":cards,"meta":meta})); await pg.reload(); await pg.wait_for_timeout(1500)
PLAY = """async(failIds)=>{ const t=window.__t; const p=document.querySelector('#pet'); if(p && !p.classList.contains('hidden')) document.querySelector('#petClose').click();
  const seen={}, sizes=[]; for(let r=0;r<5;r++){ t.setSES(null); t.startSession(); const s=t.getSES(); if(!s){ sizes.push(0); continue; }
    sizes.push(s.queue.length); new Set(s.queue.map(i=>i.id)).forEach(id=>seen[id]=(seen[id]||0)+1);
    let g=0; while(s.queue.length && g++<60){ const it=s.queue[0]; t.settleItem(!failIds.includes(it.id)); }
    await new Promise(r=>setTimeout(r,200)); }
  const S=t.S(); return {seen, sizes, cday:S.meta.cday, carry:S.meta.carry, sess:!!S.meta.session}; }"""
async def main():
  async with async_playwright() as pw:
    b=await pw.chromium.launch(); pg=await b.new_page(viewport={"width":390,"height":844}); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)))
    await pg.goto("http://localhost:8765/index.html")
    # 작은 덱: 복습 6개 중 2개를 매번 틀림 → 한 판 더 5번
    await seed(pg, mk(6))
    r=await pg.evaluate(PLAY, ["d0","d1"])
    mx=max(r["seen"].values()) if r["seen"] else 0
    ok("한 판 더 5번: 같은 단어가 하루 2판 넘게 안 나옴", mx<=2, r)
    ok("끈질긴 단어(d0·d1)도 2판 이하", r["seen"].get("d0",0)<=2 and r["seen"].get("d1",0)<=2, r)
    ok("4문제 아래 판 없음(둘째 판부터)", all(x==0 or x>=4 for x in r["sizes"][1:]), r["sizes"])
    ok("판이 끝없이 이어지지 않음(빈 판 = 오늘 끝)", 0 in r["sizes"], r["sizes"])
    ok("carry 쓴 단어는 u에 · 다시 안 넘김", not set(r["carry"].get("ids",[])) & set(r["carry"].get("u",[])), r["carry"])
    # 판 끝 화면: 다음 판 없으면 「오늘 끝!」
    r2=await pg.evaluate("""async()=>{ const t=window.__t; return [!!document.querySelector('#oneMore'), t.buildCourse().queue.length]; }""")
    ok("다음 판 없으면 「한 판 더」 버튼 없음", r2==[False,0], r2)
    # 첫 판은 3문제여도 그대로(기존 동작)
    await seed(pg, mk(3))
    r=await pg.evaluate("()=>window.__t.buildCourse().queue.length"); ok("오늘 첫 판은 4문제 아래(복습 3개)여도 만듦", r>=3, r)
    # 큰 덱: 끈질긴 단어 계속 틀려도 같은 날 3번째 판엔 없음, 판은 12칸
    await seed(pg, mk(80))
    r=await pg.evaluate(PLAY, ["d0","d1"])
    ok("큰 덱: 끈질긴 단어 하루 2판 이하·판 12칸", r["seen"].get("d0",0)<=2 and r["seen"].get("d1",0)<=2 and all(x==12 for x in r["sizes"]), r["sizes"])
    # 옛 데이터: carry에 u 없음·cday 없음 → 오류 없이
    await seed(pg, mk(10), {"carry":{"d":"__T__","ids":["d0","d1"]}})
    r=await pg.evaluate("""()=>{ const t=window.__t, S=t.S(); S.meta.carry.d=t.today(); const s=t.buildCourse(); return [s.queue.length, s.queue.findIndex(q=>q.id==='d0')>=0]; }""")
    ok("옛 carry(u 없음)·cday 없음 → 정상 판", r[0]>=4 and r[1], r)
    # 어제 cday는 오늘 새로 시작
    await seed(pg, mk(10), {"cday":{"d":"2020-01-01","c":9,"n":{"d0":5,"d1":5}}})
    r=await pg.evaluate("()=>{ const s=window.__t.buildCourse(); return s.queue.some(q=>q.id==='d0'); }")
    ok("지난 날 cday는 무시", r, r)
    ok("페이지 오류 없음", not errs, errs)
    await b.close()
  print(f"t_carry: {sum(R)}/{len(R)}"); raise SystemExit(0 if all(R) else 1)
asyncio.run(main())
