# 검수단 R1-7-1: meaningMatch 기능 어절('하다'·'이다'·'한'·'이')이 대체 정답이 되던 것 + 정상 정답 회귀
import asyncio, json
from playwright.async_api import async_playwright
R=[]
def ok(n,c,i=""): R.append(c); print(("✅" if c else "❌"), n, "" if c else i)
NO=[("수영하다","피곤하게 하다"),("하다","피곤하게 하다"),("한","피곤한, 지친"),("이","이상하다"),("하다","공부하다"),("이다","학생이다"),("되다","부자가 되다"),("수영하다","하다"),("먹다","마시다"),("い","やさしい"),("する","勉強する")]
YES=[("피곤하게 하다","피곤하게 하다"),("지친","피곤한, 지친"),("피곤하다","피곤한, 지친"),("공부하다","공부하다"),("공부","공부하다"),("하다","하다"),("이","이, 치아"),("눈","눈"),("고양이","고양이 (동물)"),("부자가 되다","부자가 되다"),("공부를 하다","공부를 하다"),("피곤","피곤하다"),("勉強","勉強する"),("やさしい","やさしい、親切な"),("먹다","먹다 / 식사하다"),("식사","먹다 / 식사하다"),("피곤하게","피곤하게 하다")]
async def main():
  async with async_playwright() as pw:
    b=await pw.chromium.launch(); pg=await b.new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)))
    await pg.goto("http://localhost:8765/index.html"); await pg.wait_for_timeout(1200)
    r=await pg.evaluate("p=>p.map(([a,m])=>window.__t.meaningMatch(a,m))", NO)
    ok("기능 어절·조각만으로는 정답 아님 (%d쌍)"%len(NO), not any(r), [NO[i] for i,x in enumerate(r) if x])
    r=await pg.evaluate("p=>p.map(([a,m])=>window.__t.meaningMatch(a,m))", YES)
    ok("정상 정답 그대로 (%d쌍)"%len(YES), all(r), [YES[i] for i,x in enumerate(r) if not x])
    # 실제 한국어 단어장: '하다'·'한'·'이' 입력이 정답이 되는 카드 수 (뜻이 정확히 그 말인 카드만 허용)
    r=await pg.evaluate("""async()=>{ const out={}; for(const f of ['ja-beg','ja-mid','ja-adv','es-beg','es-mid','en-beg']){ try{ const j=await (await fetch('presets/'+f+'.json')).json(); const L=Array.isArray(j)?j:(j.words||j.cards||[]); L.forEach(e=>{ const m=Array.isArray(e)?e[1]:(e.meaning||e.m||''); const mk=typeof m==='object'&&m?(m.ko||''):m; ['하다','한','이','되다'].forEach(a=>{ if(mk&&window.__t.meaningMatch(a,String(mk))&&!String(mk).split(/[,，、;；\\/・·]/).map(s=>s.trim()).includes(a)) out[a]=(out[a]||0)+1; }); }); }catch(e){} } return out; }""")
    ok("단어장: 기능 조각 입력이 정답인 카드 0장", sum(r.values())==0, r)
    ok("오류 없음", not errs, errs[:3])
    await b.close()
asyncio.run(main()); import sys; sys.exit(0 if all(R) else 1)
