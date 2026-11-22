# 검수단 R1-8-1·R1-8-2(빈칸: 정답 두 번·한글 복합어 절단) + R1-7-2(findForm 어간 대체: ir→Irene 등)
import asyncio, json
from playwright.async_api import async_playwright
R=[]
def ok(n,c,i=""): R.append(c); print(("✅" if c else "❌"), n, "" if c else i)
JS_CARD = "([w,e,lang])=>{ const t=window.__t; t.S().meta.settings.lang=lang; const c={word:w,example:e}; c.form=t.findForm(e,w); const p=t.clozeParts(c); return p?p.answer+'|'+p.after.slice(0,6):null; }"
async def main():
  async with async_playwright() as pw:
    b=await pw.chromium.launch(); pg=await b.new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)))
    await pg.goto("http://localhost:8765/index.html"); await pg.wait_for_timeout(1200)
    async def cp(w,e,lang="ko"): return await pg.evaluate(JS_CARD,[w,e,lang])
    # ① 정답이 두 번 이상 → 빈칸 없음 (보고서 예문 그대로)
    for w,e in [("일","일에 일을 더하면 이가 된다."),("아기","아기가 울자 아기 엄마가 아기에게 젖병을 물렸다."),("연구","연구원들은 며칠째 밤새도록 실험 연구에 몰두하고 있다.")]:
      ok("두 번 나오면 빈칸 안 냄: "+w, await cp(w,e) is None, await cp(w,e))
    # ② 복합어 앞부분 절단 없음
    for w,e in [("금","금광에서 채굴한 금은 금괴 또는 금화를 만드는 데 쓰인다."),("책","책꽂이에는 많은 종류의 책들이 빼곡하게 꽂혀 있었다."),("수","그 사전에 수록된 어휘의 수는 40만이다."),("책","책꽂이가 넘어졌다.")]:
      r=await cp(w,e); ok("복합어 앞부분을 빈칸으로 안 씀: %s → %s"%(w,r), r is None, r)
    # 이미 저장된 옛 form('금')도 같은 규칙
    r=await pg.evaluate("()=>window.__t.clozeParts({word:'책',form:'책',example:'책꽂이가 넘어졌다.'})"); ok("옛 form 저장 카드도 절단 없음", r is None, r)
    r=await pg.evaluate("()=>!!window.__t.clozeParts({word:'책',form:'책',example:'책꽂이가 넘어졌다.'}, true)"); ok("옛 예문 정리(fixCutExamples)용 느슨한 판정은 옛 그대로", r)
    # 정상 빈칸 회귀 (조사·하다·이다 붙은 명사, 활용형 form)
    for w,e,a in [("고양이","고양이가 밥을 먹는다.","고양이"),("공부","어제 도서관에서 공부했다.","공부"),("아기","아기에게 우유를 줬다.","아기"),("학생","저는 학생입니다.","학생"),("책","책들이 많다.","책"),("사과","사과나 배를 사 와.","사과"),("친구","친구한테서 편지가 왔다.",None)]:
      r=await cp(w,e); good = (r or "").split("|")[0]==a if a else True
      ok("정상 빈칸: %s → %s"%(w,r), good, r)
    r=await pg.evaluate("()=>{const p=window.__t.clozeParts({word:'예쁘다',form:'예쁜',example:'예쁜 꽃이 피었다.'}); return p&&p.answer}"); ok("활용형 form(예쁜) 그대로", r=="예쁜", r)
    r=await pg.evaluate("()=>{const p=window.__t.clozeParts({word:'먹다',form:'먹',example:'밥을 먹었다.'}); return p&&p.answer}"); ok("어간 form(먹+었다)은 오른쪽 경계 안 봄", r=="먹", r)
    # ③ ko 단어장 전체: 정답 노출·복합어 절단 0장
    r=await pg.evaluate("""async()=>{ const t=window.__t; t.S().meta.settings.lang='ko'; const out={n:0,cl:0,leak:[],cut:[],old:0};
      for(const f of ['ko-beg','ko-mid','ko-adv']){ const j=await (await fetch('presets/'+f+'.json')).json(); (j.items||[]).forEach((e,k)=>{ const w=e[0], ex=e[3]; if(!ex) return; out.n++;
        const c={word:w,example:ex}; c.form=t.findForm(ex,w); if(t.clozeParts(c,true)) out.old++; const p=t.clozeParts(c); if(!p) return; out.cl++;
        if((p.before+' '+p.after).includes(p.answer)) out.leak.push(f+':'+k+' '+w);
        if(/^[가-힣]/.test(p.after) && p.answer===w && !t.hgTailOk(p.after)) out.cut.push(f+':'+k+' '+w); }); }
      return out; }""")
    print("   ko 예문 %d장: 빈칸 가능 옛 %d → 새 %d"%(r["n"],r["old"],r["cl"]))
    ok("ko 전체: 빈칸 뒤 예문에 정답이 남는 카드 0장", not r["leak"], r["leak"][:8])
    ok("ko 전체: 복합어 절단 0장", not r["cut"], r["cut"][:8])
    # ④ es findForm 어간 대체 (R1-7-2)
    for w,e in [("ir","Irene va a la escuela."),("ver","La verdad es simple."),("mes","Pon la mesa, por favor."),("tener","Juego al tenis los lunes.")]:
      f=await pg.evaluate("([w,e])=>{window.__t.S().meta.settings.lang='es'; return window.__t.findForm(e,w)}",[w,e]); ok("엉뚱한 단어 빈칸 안 함: %s ✕ %s"%(w,f or "∅"), f=="", f)
    for w,e,a in [("tener","Yo tengo un perro.","tengo"),("hablar","Ayer hablamos mucho.","hablamos"),("comer","Ellos comieron tarde.","comieron"),("vivir","Vivimos en Madrid.","Vivimos"),("levantarse","Me levanto a las siete.","levanto"),("casa","La casa es grande.","casa"),("ciudad","Hay muchas ciudades.","ciudades"),("ir","Voy a ir mañana.","ir")]:
      f=await pg.evaluate("([w,e])=>{window.__t.S().meta.settings.lang='es'; return window.__t.findForm(e,w)}",[w,e]); ok("정상 활용형: %s → %s"%(w,f), f==a, f)
    ok("오류 없음", not errs, errs[:3])
    await b.close()
asyncio.run(main()); import sys; sys.exit(0 if all(R) else 1)
