# 콘텐츠 C1·C2 테스트: 단어장 큐레이션 객체 {e,f,r,t} 반영 · 안 푼 카드만 교체 · 푼 카드는 빈칸만 · 빈칸 읽기 정답
import asyncio, sys, json
from playwright.async_api import async_playwright
R=[]
def ok(n,c,i=""): R.append(c); print(("✅" if c else "❌"), n, "" if c else i)
async def main():
  async with async_playwright() as pw:
    b=await pw.chromium.launch(); pg=await b.new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)))
    await pg.goto("http://localhost:8765/index.html")
    await pg.evaluate("""()=>localStorage.setItem('focus-vocab-v1', JSON.stringify({cards:{}, meta:{setup:1,tutAsked:1,loginAsked:1,days:{},settings:{ui:'ko',lang:'ja'}}}))""")
    await pg.reload(); await pg.wait_for_timeout(2000)
    # C1: ja 단어장 (ui ko)
    r=await pg.evaluate("""()=>{ const t=window.__t, S=t.S(); const d={id:'dja',preset:'ja-n5',cursor:0};
      const data={items:[["近い","ちかい","near","가깝다",{"e":"駅はここから近いです。","f":"近い","r":"ちかい","t":{"ko":"역은 여기서 가까워요."}}],["働く","はたらく","work","일하다",{"e":"父は銀行で働いています。","f":"働いて","r":"はたらいて","t":{"ko":"아빠는 은행에서 일하고 있어요."}}],["行く","いく","go","가다"]]};
      t.materialize(d, data, 10); const by=w=>Object.values(S.cards).find(c=>c.word===w);
      const a=by('近い'), b=by('働く'), c=by('行く');
      return {a:[a.example,a.form,a.formR,a.exampleKo,!!a.lazy], b:[b.form,b.formR], c:[c.example||'',!!c.lazy,c.curv||'']}; }""")
    ok("C1 ja 예문·빈칸·읽기·번역 반영", r["a"][:4]==["駅はここから近いです。","近い","ちかい","역은 여기서 가까워요."], r["a"])
    ok("C1 예문·뜻 다 있으면 Tatoeba 조회 생략", r["a"][4]==False, r["a"])
    ok("C1 활용형 빈칸(働いて)·읽기", r["b"]==["働いて","はたらいて"], r["b"])
    ok("C1 큐레이션 없는 항목은 예전 그대로(조회 대상)", r["c"]==["",True,""], r["c"])
    # ko 단어장 (ui ja) — 예문 번역 t.ja
    await pg.evaluate("()=>{window.__t.S().meta.settings.ui='ja'}")
    r=await pg.evaluate("""()=>{ const t=window.__t, S=t.S(); const d={id:'dko',preset:'ko-beg',cursor:0};
      t.materialize(d,{items:[["예쁘다","きれいだ、かわいい","","길가에 예쁜 꽃들이 피었어요.",{"f":"예쁜","t":{"ja":"道端にきれいな花が咲いた。"}}]]},5);
      const c=Object.values(S.cards).find(c=>c.word==='예쁘다'); return [c.example,c.form,c.exampleKo]; }""")
    ok("C1 ko 용언 빈칸 모양·일본어 번역", r==["길가에 예쁜 꽃들이 피었어요.","예쁜","道端にきれいな花が咲いた。"], r)
    await pg.evaluate("()=>{window.__t.S().meta.settings.ui='ko'}")
    # C2: 이미 있는 카드
    r=await pg.evaluate("""()=>{ const t=window.__t; const X={"e":"新しい例文です。","f":"例文","t":{"ko":"새 예문이에요."}};
      const fresh={id:'f1',word:'例文',lang:'ja',isNew:true,reps:0,example:'古い例文。',form:'例文',due:'2026-11-23',iv:0,mOk:1};
      const played={id:'p1',word:'例文',lang:'ja',isNew:false,reps:3,example:'내가 쓴 예문 例文',form:'例文',due:'2026-12-01',iv:9,ef:2.4};
      const playedEmpty={id:'p2',word:'例文',lang:'ja',isNew:false,reps:2,example:'',due:'2026-12-02',iv:5};
      const before=JSON.stringify({due:played.due,iv:played.iv,ef:played.ef,reps:played.reps});
      const a=t.curApply(fresh,X,true), b=t.curApply(played,X,false), c=t.curApply(playedEmpty,X,false), again=t.curApply(fresh,X,true);
      return {a, fresh:[fresh.example,fresh.exampleKo], b, played:played.example, keep: before===JSON.stringify({due:played.due,iv:played.iv,ef:played.ef,reps:played.reps}), c, pe:[playedEmpty.example,playedEmpty.exampleKo, playedEmpty.due], again}; }""")
    ok("C2 안 푼 카드는 큐레이션으로 교체", r["a"] and r["fresh"]==["新しい例文です。","새 예문이에요."], r)
    ok("C2 푼 카드의 사용자 예문은 그대로", (not r["b"]) and r["played"]=="내가 쓴 예문 例文" and r["keep"], r)
    ok("C2 푼 카드라도 예문이 비면 채움(학습 기록 그대로)", r["c"] and r["pe"]==["新しい例文です。","새 예문이에요.","2026-12-02"], r)
    ok("C2 같은 데이터로 두 번 돌아도 그대로", r["again"]==False, r)
    # 빈칸 정답: 큐레이션 읽기
    r=await pg.evaluate("""()=>{ const t=window.__t, S=t.S(); const c={word:'働く',reading:'はたらく',form:'働いて',formR:'はたらいて',lang:'ja'};
      const a=t.ansOk(c,'はたらいて','働いて'); const w=t.ansOk(c,'はたらく','働いて'); S.meta.settings.strictKanji=true; const s=t.ansOk(c,'はたらいて','働いて'); S.meta.settings.strictKanji=false; return [a,w,s]; }""")
    ok("빈칸 활용형 히라가나 정답", r[0]!="no" and r[1]=="no", r)
    ok("「한자까지 정확히」면 히라가나는 오답", r[2]=="no", r)
    ok("페이지 오류 없음", not errs, errs[:3])
    await b.close()
  print("결과:", "통과" if all(R) else "실패"); sys.exit(0 if all(R) else 1)
asyncio.run(main())
