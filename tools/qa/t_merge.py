# 검수단 11-24: R1-49-3 냥이 병합(산 간식·코인 사라짐) · R1-49-1 카드 병합(시계 어긋난 기기의 옛 복습 기록이 덮음·필드 빠진 카드)
import asyncio, json
from playwright.async_api import async_playwright
R=[]
def ok(n,c,i=""): R.append(c); print(("✅" if c else "❌"), n, "" if c else i)
U="http://localhost:8765/index.html"
FAR=4102444800000  # 2100년
def card(i, **kw):
  d=dict(id=f"c{i}",lang="ja",word=f"語{i}",meaning=f"뜻{i}",example="",deck="default",due="2026-12-01",level=2,reps=3,isNew=False,lapses=0,created=i,introduced="2026-10-01",mastered=False,relearn=False,log=[],step=2,S=30,D=5,last="2026-11-01",u=100)
  d.update(kw); return d
BASE={"setup":1,"tutAsked":1,"loginAsked":1,"stepv":1,"days":{},"settings":{"ui":"ko","lang":"ja","homePet":False}}
async def put(pg, cards, meta=None):
  m=dict(BASE); m.update(meta or {})
  await pg.goto(U); await pg.evaluate("s=>localStorage.setItem('focus-vocab-v1', s)", json.dumps({"cards":cards,"meta":m})); await pg.goto(U); await pg.wait_for_timeout(1500)
async def merge(pg, remote, opt=None):
  return await pg.evaluate("([r,o])=>{ __t.mergeData(r,o||undefined); const S=__t.S(); return JSON.parse(JSON.stringify({cards:S.cards, meta:S.meta})); }", [remote, opt])
async def main():
  async with async_playwright() as pw:
    b=await pw.chromium.launch(); errs=[]
    ctx=await b.new_context(viewport={"width":390,"height":844}); await ctx.route("**/*supabase.co/**", lambda r: r.abort()); pg=await ctx.new_page(); pg.on("pageerror",lambda e:errs.append(str(e)))
    # 1) 냥이: 기준 없음 — 두 기기에서 따로 산 간식이 둘 다 남음
    lp={"u":100,"inv":{"a":1},"buy":[{"id":"a","n":1,"exp":FAR}],"coins":5,"kcal":10,"lv":1}
    rp={"u":10**13,"inv":{"x":3},"buy":[{"id":"x","n":3,"exp":FAR+1}],"coins":7,"kcal":20,"lv":1}
    await put(pg, {"c0":card(0)}, {"pet":lp})
    r=await merge(pg, {"cards":{"c0":card(0)},"meta":{"pet":rp}})
    p=r["meta"]["pet"]
    ok("냥이 기준 없음: 원격 u가 커도 로컬 산 간식 a 남음 + 원격 x 남음", p["inv"].get("a")==1 and p["inv"].get("x")==3, p)
    ok("냥이 buy 항목 합집합(a·x)", sorted(l["id"] for l in p.get("buy",[]))==["a","x"], p.get("buy"))
    ok("냥이 나머지 값은 새 쪽(kcal 20·coins 7)·u = 큰 값", p["kcal"]==20 and p["coins"]==7 and p["u"]==10**13, p)
    # 반대 방향(로컬이 새 쪽)
    await put(pg, {"c0":card(0)}, {"pet":dict(rp,u=300)})
    p=(await merge(pg, {"cards":{"c0":card(0)},"meta":{"pet":dict(lp,u=50)}}))["meta"]["pet"]
    ok("냥이 기준 없음(로컬이 새 쪽): 원격 산 간식 a 더해짐", p["inv"].get("a")==1 and p["inv"].get("x")==3, p)
    # 2) 다 먹은(사라진) 산 간식은 되살아나지 않음
    lp2={"u":300,"inv":{},"buy":[],"bgone":[f"x|{FAR+1}"],"coins":0}
    await put(pg, {"c0":card(0)}, {"pet":lp2})
    p=(await merge(pg, {"cards":{"c0":card(0)},"meta":{"pet":dict(rp,u=200)}}))["meta"]["pet"]
    ok("이 기기에서 다 먹은 산 간식 x는 다른 기기 옛 기록으로 안 되살아남", not p["inv"].get("x") and not [l for l in p.get("buy",[]) if l["id"]=="x"], p)
    # buyExpire가 다 쓴 항목을 bgone에 남김
    await put(pg, {"c0":card(0)}, {"pet":{"u":10,"inv":{"x":1},"buy":[{"id":"x","n":0,"exp":FAR}],"coins":0}})
    g=await pg.evaluate("()=>{ __t.S(); return (__t.S().meta.pet.bgone||[]) }")
    if not g:
      g=await pg.evaluate("()=>{ const p=__t.S().meta.pet; __t.mergeData({cards:{},meta:{}}); return p.bgone||[] }")
    ok("다 쓴 산 간식 기록은 bgone에 남음", f"x|{FAR}" in (await pg.evaluate("()=>{ const S=__t.S(); return JSON.stringify(S.meta.pet) }")) or f"x|{FAR}" in g, g)
    # 3) 기준(petBase)이 있으면 두 기기의 코인·간식 변화를 둘 다 더함
    base={"u":100,"coins":10,"inv":{"a":1},"at":1,"c":"ABCD-EFGH"}
    await put(pg, {"c0":card(0)}, {"sync":{"code":"ABCD-EFGH"},"petBase":base,"pet":{"u":150,"coins":15,"inv":{"a":2},"buy":[]}})
    p=(await merge(pg, {"cards":{"c0":card(0)},"meta":{"pet":{"u":200,"coins":7,"inv":{"a":1,"x":1},"buy":[]}}}))["meta"]["pet"]
    ok("기준 있음: 코인 = 10 +5(이 기기 번 것) −3(다른 기기 쓴 것) = 12", p["coins"]==12, p)
    ok("기준 있음: 간식 a 2(이 기기 산 것)·x 1(다른 기기 산 것)", p["inv"]=={"a":2,"x":1}, p["inv"])
    # 다른 동기화 코드의 기준은 안 씀
    await put(pg, {"c0":card(0)}, {"sync":{"code":"ZZZZ-YYYY"},"petBase":base,"pet":{"u":150,"coins":15,"inv":{"a":2},"buy":[]}})
    p=(await merge(pg, {"cards":{"c0":card(0)},"meta":{"pet":{"u":10**13,"coins":7,"inv":{"a":1,"x":1},"buy":[]}}}))["meta"]["pet"]
    ok("동기화 코드가 다르면 기준 무시(새 쪽 그대로 coins 7)", p["coins"]==7 and p["inv"]=={"a":1,"x":1}, p)
    # 4) 카드: 시계가 앞선 기기의 옛 복습 기록이 나중 복습을 덮지 않음
    loc=card(0, reps=10, lapses=2, last="2026-11-20", due="2026-12-20", S=40, log=[{"d":"2026-11-20","ok":True}], u=100)
    rem=card(0, reps=5, lapses=1, last="2026-11-10", due="2026-11-15", S=10, meaning="고친 뜻", u=100+86400000)
    await put(pg, {"c0":loc})
    c=(await merge(pg, {"cards":{"c0":rem},"meta":{}}))["cards"]["c0"]
    ok("카드: 원격 u+1일이어도 로컬 복습 기록(reps 10·due 12-20·lapses 2) 유지", c["reps"]==10 and c["due"]=="2026-12-20" and c["lapses"]==2 and c["last"]=="2026-11-20", c)
    ok("카드: 내용(뜻)은 수정 시각 새 쪽 「고친 뜻」", c["meaning"]=="고친 뜻", c["meaning"])
    # 반대: 원격 복습이 더 나중이면 원격 복습 기록
    rem2=card(0, reps=12, last="2026-11-22", due="2027-01-01", u=50)
    await put(pg, {"c0":loc})
    c=(await merge(pg, {"cards":{"c0":rem2},"meta":{}}))["cards"]["c0"]
    ok("카드: 원격 복습이 더 나중(11-22)이면 원격 reps 12·due 01-01", c["reps"]==12 and c["due"]=="2027-01-01", c)
    # 같은 날이면 reps 많은 쪽
    await put(pg, {"c0":card(0, reps=7, last="2026-11-20", due="2026-12-05", u=500)})
    c=(await merge(pg, {"cards":{"c0":card(0, reps=9, last="2026-11-20", due="2026-12-09", u=100)},"meta":{}}))["cards"]["c0"]
    ok("카드: 같은 날이면 복습 많은 쪽(reps 9)", c["reps"]==9 and c["due"]=="2026-12-09", c)
    # 5) 필드 빠진 원격 카드가 이겨도 due·reps 비지 않음
    thin={"id":"c0","lang":"ja","word":"語0","meaning":"새 뜻","deck":"default","u":999999,"created":0}
    await put(pg, {"c0":loc})
    c=(await merge(pg, {"cards":{"c0":thin},"meta":{}}))["cards"]["c0"]
    ok("필드 빠진 원격 카드: due·reps·last 유지(null 아님)", c.get("due")=="2026-12-20" and c.get("reps")==10 and c.get("last")=="2026-11-20", c)
    thin2=dict(thin, last="2026-11-23")   # 복습 날짜만 있고 due·reps 없음
    await put(pg, {"c0":loc})
    c=(await merge(pg, {"cards":{"c0":thin2},"meta":{}}))["cards"]["c0"]
    ok("복습 쪽이 필드가 빠져도 due·reps는 다른 쪽에서 채움", c.get("due") is not None and c.get("reps") is not None, c)
    # 6) 회귀: 삭제·빈 원격·days·paid·cos·sup·새 카드
    await put(pg, {"c0":card(0), "c1":card(1)}, {"days":{"2026-11-20":"x"},"paid":{"p1":1},"cos":{"own":{"hat":1}},"sup":1})
    r=await merge(pg, {"cards":{"c0":card(0), "c2":card(2)},"meta":{"deleted":{"c1":10**13},"days":{"2026-11-20":True,"2026-11-21":True},"paid":{"p2":1},"cos":{"own":{"scarf":1}},"sup":3}})
    m=r["meta"]
    ok("회귀: 원격에서 지운 카드 c1 삭제·원격 새 카드 c2 들어옴", "c1" not in r["cards"] and "c2" in r["cards"] and "c0" in r["cards"], list(r["cards"]))
    ok("회귀: days true 우선·paid·cos·sup 합침", m["days"].get("2026-11-20") is True and m["days"].get("2026-11-21") is True and set(m["paid"])=={"p1","p2"} and set(m["cos"]["own"])=={"hat","scarf"} and m["sup"]==3, m)
    await put(pg, {"c0":loc}, {"pet":lp})
    r=await merge(pg, {"cards":{},"meta":{}})
    ok("회귀: 빈 원격 → 카드·냥이 그대로", r["cards"]["c0"]["reps"]==10 and r["meta"]["pet"]["inv"]=={"a":1}, r["meta"].get("pet"))
    # 같은 카드 같은 값이면 그대로(옛 판정과 같음)
    await put(pg, {"c0":loc})
    c=(await merge(pg, {"cards":{"c0":loc},"meta":{}}))["cards"]["c0"]
    ok("회귀: 같은 카드는 변화 없음", c==loc, c)
    # 7) syncNow 흐름(가짜 서버): petBase는 서버로 안 보내고, 다음 동기화 때 두 기기 변화를 더함
    await put(pg, {"c0":card(0)}, {"sync":{"code":"ABCD-EFGH"},"pet":{"u":100,"coins":10,"inv":{"a":1},"buy":[]}})
    res=await pg.evaluate("""async()=>{
      const SV={data:{v:1,cards:{c0:%s},meta:{pet:{u:100,coins:10,inv:{a:1},buy:[]}}}}; const puts=[];
      window.fetch=async(url,o)=>{ const b=JSON.parse(o.body); if(url.includes('sync_get')) return new Response(JSON.stringify(SV)); if(url.includes('sync_put')){ puts.push(b.p_data); SV.data=JSON.parse(JSON.stringify(b.p_data)); return new Response(''); } return new Response('{}'); };
      const run=async()=>{ const n0=puts.length; for(let i=0;i<40 && puts.length===n0;i++){ await __t.syncNow(); if(puts.length===n0) await new Promise(r=>setTimeout(r,250)); } };
      await run(); const S=__t.S();
      const hasBase=!!S.meta.petBase, sentBase=puts.some(p=>p.meta&&p.meta.petBase);
      // 이 기기: 코인 +4 / 다른 기기: 간식 x 2개 사고 코인 -3
      S.meta.pet.coins+=4; S.meta.pet.u=Date.now();
      SV.data.meta.pet=Object.assign({},SV.data.meta.pet,{coins:SV.data.meta.pet.coins-3,inv:Object.assign({},SV.data.meta.pet.inv,{x:2}),u:Date.now()+5000});
      await run();
      return {hasBase, sentBase, pet:S.meta.pet, srv:SV.data.meta.pet, n:puts.length};
    }""" % json.dumps(card(0)))
    ok("동기화 뒤 petBase 저장·서버로는 안 보냄", res["hasBase"] and not res["sentBase"], res)
    ok("두 번째 동기화: 코인 10+4−3=11·간식 a1·x2 (서버도 같음)", res["pet"]["coins"]==11 and res["pet"]["inv"]=={"a":1,"x":2} and res["srv"]["coins"]==11, res)
    ok("페이지 오류 없음", not errs, errs[:3])
    await b.close()
  print(f"{sum(R)}/{len(R)}")
  if not all(R): raise SystemExit(1)
asyncio.run(main())
