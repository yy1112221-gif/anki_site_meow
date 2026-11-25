# 사업안 §7 ①친구 ②축하 카드 ③대화로 학습 (v196~)
import asyncio, json, re
from playwright.async_api import async_playwright
R=[]
def ok(n,c,i=""): R.append(c); print(("✅" if c else "❌"), n, "" if c else i)
B="http://localhost:8765/index.html"
def meta(ui="ko", lang="ja", by=1998, fr=None):
  m={"setup":1,"tutAsked":1,"loginAsked":1,"days":{},"settings":{"ui":ui,"lang":lang,"homePet":False},"stepv":1,"by":by,"nick":{"name":"테스트냥","key":"k"*36,"srv":1}}
  if fr is not None: m["fr"]=fr
  return m
async def seed(pg, m, q="", cards=None):
  await pg.goto(B); await pg.evaluate("s=>localStorage.setItem('focus-vocab-v1', s)", json.dumps({"cards":cards or {},"meta":m}))
  await pg.goto(B+q); await pg.wait_for_timeout(1600)
FRIEND={"id":"f"*64,"nick":"ミカ","fur":"cheese","stats":{"st":5,"wk":12,"lang":"ko"},"bday":"","since":"2026-11-25"}
async def main():
  async with async_playwright() as pw:
    b=await pw.chromium.launch()
    for vw,vh in [(360,640),(390,844)]:
      ctx=await b.new_context(viewport={"width":vw,"height":vh}, locale="ko-KR"); pg=await ctx.new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)))
      sent=[]; calls=[]
      async def rpc(route):
        req=route.request; url=req.url; body=req.post_data or ""; sent.append(url+" "+body)
        m=re.search(r"/rpc/(fr_\w+)", url)
        if not m: return await route.abort()
        fn=m.group(1); calls.append((fn, json.loads(body or "{}")))
        today=await pg.evaluate("()=>window.__t.today().slice(5)") if False else None
        res={"fr_sync":{"list":[dict(FRIEND, bday=BD[0])]}, "fr_invite_make":"a"*32, "fr_invite_peek":{"nick":"ミカ","fur":"cheese","st":"ok"}, "fr_invite_accept":"ok", "fr_remove":"ok"}.get(fn)
        await route.fulfill(status=200, content_type="application/json", body=json.dumps(res))
      BD=[""]
      await ctx.route(re.compile(r"supabase\.co"), rpc)
      await ctx.route(re.compile(r"(mymemory|tatoeba|wiktionary|tosspayments)"), lambda r: (sent.append(r.request.url), r.abort())[1])
      # ── ① 만 14세 미만: 설정 줄·대화 메뉴 숨김, 초대 링크 무시
      await seed(pg, meta(by=2015), "?f="+"a"*32+"&src=friend"); await pg.wait_for_timeout(1500)
      ok(f"{vw} 14세 미만 FR_OK false", await pg.evaluate("()=>!window.__t.FR_OK()"))
      await pg.evaluate("()=>window.__t.showView('how')"); await pg.wait_for_timeout(300)
      ok(f"{vw} 14세 미만 설정 친구 줄 숨김", await pg.evaluate("()=>document.querySelector('#frRow').classList.contains('hidden')"))
      ok(f"{vw} 14세 미만 초대 수락 창 없음·RPC 0", await pg.evaluate("()=>!document.querySelector('.fr-req')") and not any(c[0]=="fr_invite_accept" for c in calls))
      await pg.evaluate("()=>window.__t.showView('add')"); await pg.wait_for_timeout(200)
      ok(f"{vw} 14세 미만 대화 메뉴 숨김", await pg.evaluate("()=>document.querySelector('#amChat').classList.contains('hidden')"))
      # ── ① 초대 수락 흐름
      calls.clear(); await seed(pg, meta(), "?f="+"a"*32+"&src=friend"); await pg.wait_for_timeout(1500)
      ok(f"{vw} 초대 수락 창(닉네임)", "ミカ" in await pg.evaluate("()=>(document.querySelector('.fr-req')||{}).textContent||''"))
      await pg.click("#frAcc"); await pg.wait_for_timeout(800)
      acc=[c for c in calls if c[0]=="fr_invite_accept"]
      ok(f"{vw} 수락 RPC(key·token)", acc and acc[0][1].get("p_token")=="a"*32 and len(acc[0][1].get("p_key",""))>=20, acc)
      ok(f"{vw} 수락 뒤 친구 목록", "ミカ" in await pg.evaluate("()=>(document.querySelector('#frList')||{}).textContent||''"))
      ok(f"{vw} 주소에서 f 지움", "f=" not in await pg.evaluate("()=>location.search"))
      sy=[c for c in calls if c[0]=="fr_sync"][-1][1]
      ok(f"{vw} 기본: 학습 현황·생일 비공개로 전송", sy["p_share_stats"] is False and sy["p_share_bday"] is False and sy["p_stats"] is None and sy["p_bday"]=="", sy)
      # 공개 켜기 → 즉시 동기화
      await pg.evaluate("()=>{ document.querySelector('.fr-set').open=true; }")
      await pg.check("#frShare"); await pg.wait_for_timeout(500)
      sy=[c for c in calls if c[0]=="fr_sync"][-1][1]; ok(f"{vw} 학습 현황 공개 켜면 stats 전송", sy["p_share_stats"] is True and isinstance(sy["p_stats"], dict), sy)
      await pg.uncheck("#frShare"); await pg.wait_for_timeout(500)
      sy=[c for c in calls if c[0]=="fr_sync"][-1][1]; ok(f"{vw} 끄면 즉시 stats null", sy["p_share_stats"] is False and sy["p_stats"] is None)
      sw=await pg.evaluate("()=>document.documentElement.scrollWidth"); ok(f"{vw} 친구 창 가로 넘침 없음", sw<=vw, sw)
      # 끊기 → 목록에서 빠짐
      await pg.evaluate("()=>{ window.confirm=()=>true; }")
      await pg.click("[data-more]"); await pg.click("#frUn"); await pg.wait_for_timeout(500)
      ok(f"{vw} 친구 끊기 RPC", any(c[0]=="fr_remove" and c[1]["p_block"] is False for c in calls))
      await pg.evaluate("()=>{ const p=document.querySelector('.sheet-bg'); p && p.remove(); }")
      # ── ② 생일 D-2 → 홈 말풍선
      md=await pg.evaluate("()=>window.__t.addDays(window.__t.today(),2).slice(5)"); BD[0]=md
      await seed(pg, meta(fr={"list":[dict(FRIEND,bday=md)],"ann":{},"at":0}), cards={"c1":{"id":"c1","lang":"ja","word":"先生","meaning":"선생님","isNew":True,"level":0,"due":None,"lapses":0,"reps":0,"log":[],"created":1,"u":1,"deck":"default"}})
      await pg.wait_for_timeout(800)
      ln=await pg.evaluate("()=>window.__t.frHomeLine()"); ok(f"{vw} 생일 D-2 홈 말풍선", "D-2" in ln and "ミカ" in ln, ln)
      ok(f"{vw} 홈 말풍선에 fr-ev", await pg.evaluate("()=>!!document.querySelector('.hv2-say.fr-ev')"))
      far=await pg.evaluate("()=>window.__t.addDays(window.__t.today(),9).slice(5)")
      await pg.evaluate(f"()=>{{ window.__t.frState().list[0].bday='{far}'; }}"); ok(f"{vw} D-9는 알림 없음", await pg.evaluate("()=>window.__t.frEvents().length")==0)
      # ── ② 카드 링크 → 상자 → 열기 → 이 문장으로 외우기
      card={"v":1,"n":"ミカ","c":"happy","w":"mint","m":"お誕生日おめでとう！","p":"생일 축하해!","ml":"ja","pl":"ko","to":"테스트냥","k":"bday"}
      enc=await pg.evaluate("o=>window.__t.b64uEnc(o)", card)
      ok(f"{vw} 카드 인코딩 왕복", await pg.evaluate("s=>window.__t.b64uDec(s).m", enc)==card["m"])
      await seed(pg, meta(), "?g="+enc+"&src=gift"); await pg.wait_for_timeout(1200)
      ok(f"{vw} 받은 카드 상자 보임", await pg.evaluate("()=>!!document.querySelector('#cdBox')"))
      await pg.click("#cdBox"); await pg.wait_for_timeout(1200)
      sn=await pg.evaluate("()=>[...document.querySelectorAll('.cd-sn')].map(e=>[e.getAttribute('lang'), !!e.querySelector('[data-learn]')])")
      ok(f"{vw} 열면 문장 2개·학습 언어(ja)에만 외우기 버튼", sn==[["ja",True],["ko",False]], sn)
      await pg.click("[data-learn]"); await pg.wait_for_timeout(300)
      await pg.wait_for_selector(".cd-toks .cd-tk", timeout=5000); await pg.click(".cd-toks .cd-tk >> text=誕生日")
      await pg.click(".cd-pick .btn.primary", timeout=5000); await pg.wait_for_timeout(1500)
      c=await pg.evaluate("()=>Object.values(window.__t.S().cards).find(c=>c.from)")
      dbg=await pg.evaluate("()=>[document.querySelector('#toast').textContent, (document.querySelector('.cd-pick')||{}).innerHTML||'none', !!document.querySelector('.sheet-bg')]")
      ok(f"{vw} 문장 카드 생성(보낸 사람·priv·예문·번역)", bool(c) and c["from"]=="ミカ" and c.get("priv")==1 and c["example"]=="お誕生日おめでとう！" and c["exampleKo"]=="생일 축하해!" and c["lang"]=="ja", [c, dbg])
      ok(f"{vw} 문장 카드 빈칸 가능", await pg.evaluate("id=>!!window.__t.clozeParts(window.__t.S().cards[id])", c["id"]) if c else False)
      # 처음 온 사람도 상자가 첫 설정 위에
      await pg.goto(B); await pg.evaluate("()=>localStorage.clear()"); await pg.goto(B+"?g="+enc+"&src=gift"); await pg.wait_for_timeout(2200)
      ok(f"{vw} 처음 온 사람: 상자 보임", await pg.evaluate("()=>{ const e=document.querySelector('#cdBox'); if(!e) return false; const r=e.getBoundingClientRect(); return document.elementFromPoint(r.x+r.width/2, r.y+r.height/2)?.closest('#cdBox')!=null; }"))
      # 카드 만들기 창: 캔버스·보내기
      await seed(pg, meta())
      await pg.evaluate("()=>window.__t.cardMake({nick:'ミカ'},'bday')"); await pg.wait_for_timeout(500)
      ok(f"{vw} 카드 만들기 창(상대 언어 칸)", await pg.evaluate("()=>!!document.querySelector('#cdPv') && !!document.querySelector('#cdP')"))
      await pg.fill("#cdP", "誕生日おめでとう"); await pg.wait_for_timeout(200)
      ok(f"{vw} 상대 언어 힌트 표시", len(await pg.evaluate("()=>document.querySelector('#cdHint').textContent"))>3)
      sw=await pg.evaluate("()=>document.documentElement.scrollWidth"); ok(f"{vw} 카드 창 가로 넘침 없음", sw<=vw, sw)
      await pg.evaluate("()=>{ const p=document.querySelector('.sheet-bg'); p && p.remove(); }")
      # ── ③ 대화 파싱
      kk="2025년 1월 5일 오후 3:21, 미카 : 明日は天気がいいから散歩しよう\n2025년 1월 5일 오후 3:22, 나 : 좋아!\n2025년 1월 5일 오후 3:23, 미카 : 사진\n2025년 1월 5일 오후 3:24, 미카 : 駅の近くの喫茶店で待ってるね\n続きの行です"
      line="[LINE] ミカとのトーク履歴\n2025/01/05(日)\n15:21\tミカ\t週末は映画館に行きたい\n15:22\tジュヌ\tいいね"
      p1=await pg.evaluate("s=>window.__t.parseChat(s)", kk); p2=await pg.evaluate("s=>window.__t.parseChat(s)", line)
      ok(f"{vw} 카톡 파싱(이름·미디어 빼기·여러 줄)", [x["who"] for x in p1]==["미카","나","미카"] and "続き" in p1[2]["t"], p1)
      ok(f"{vw} LINE 파싱", [x["who"] for x in p2]==["ミカ","ジュヌ"] and p2[0]["t"]=="週末は映画館に行きたい", p2)
      kw=await pg.evaluate("()=>window.__t.chatWords('친구한테 선물을 줬어요','ko')"); ok(f"{vw} 한국어 조사 떼기", "친구" in kw and "선물" in kw, kw)
      # 대화 화면 → 후보 → 카드, 대화 원문이 밖으로 안 나감
      sent.clear(); await pg.evaluate("()=>window.__t.showView('add')"); await pg.click("#amChat"); await pg.wait_for_timeout(300)
      ok(f"{vw} 대화 패널·개인정보 안내", "저장하지 않아요" in await pg.evaluate("()=>document.querySelector('#chatBox').textContent"))
      await pg.fill("#chatIn", kk); await pg.wait_for_timeout(500)
      await pg.select_option("#chatWho", "미카"); await pg.click("#chatGo"); await pg.wait_for_timeout(1500)
      ws=await pg.evaluate("()=>[...document.querySelectorAll('#chatOut [data-w]')].map(e=>e.dataset.w)")
      ok(f"{vw} 미카 메시지 단어 후보(나 메시지 제외)", "天気" in ws and "散歩" in ws and "좋아" not in ws, ws)
      await pg.click('#chatOut [data-w="散歩"]'); await pg.click("#chatAdd"); await pg.wait_for_timeout(1500)
      cc=await pg.evaluate("()=>Object.values(window.__t.S().cards).find(c=>c.word==='散歩')")
      ok(f"{vw} 대화 단어 카드(priv·대화 예문)", cc and cc.get("priv")==1 and "散歩" in cc["example"], cc)
      await pg.evaluate("id=>window.__t.fillTr && 0", None)
      leak=[s for s in sent if ("%E5%A4%A9%E6%B0%97%E3%81%8C" in s or "天気が" in s or "%E5%96%AB%E8%8C%B6" in s or "喫茶店" in s)]
      ok(f"{vw} 대화 문장이 네트워크로 안 나감", not leak, leak[:2])
      ok(f"{vw} 오류 없음", not errs, errs[:3])
      await ctx.close()
    await b.close()
  print("통과" if all(R) else "실패", f"{sum(R)}/{len(R)}"); raise SystemExit(0 if all(R) else 1)
asyncio.run(main())
