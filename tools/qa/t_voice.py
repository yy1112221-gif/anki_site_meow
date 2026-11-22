# 검수단 R1-4-2(학습 언어 음성 0개면 다른 언어로 읽음)·R1-4-4(정확한 언어 일치가 premium·google보다 약함)·R1-4-5(도달 불가 블록)
import asyncio, json
from playwright.async_api import async_playwright
R=[]
def ok(n,c,i=""): R.append(c); print(("✅" if c else "❌"), n, "" if c else i)
INIT="""(()=>{ window.__spoken=[]; const V=%s;
  try{ class U{ constructor(t){ this.text=t; this.lang=''; this.voice=null; } } window.SpeechSynthesisUtterance=U;
    speechSynthesis.getVoices=()=>V; speechSynthesis.speak=u=>window.__spoken.push({text:u.text,lang:u.lang,v:u.voice&&u.voice.name}); speechSynthesis.cancel=()=>{}; }catch(e){} })()"""
SEED={"cards":{},"meta":{"setup":1,"tutAsked":1,"loginAsked":1,"days":{},"settings":{"ui":"ko","lang":"es"}}}
async def page(b, voices):
  ctx=await b.new_context(); await ctx.add_init_script(INIT%json.dumps(voices)); pg=await ctx.new_page(); errs=[]; pg.on("pageerror",lambda e:errs.append(str(e)))
  await pg.goto("http://localhost:8765/index.html"); await pg.evaluate("s=>localStorage.setItem('focus-vocab-v1',JSON.stringify(s))",SEED)
  await pg.reload(); await pg.wait_for_timeout(1200); await pg.evaluate("()=>window.__t.loadVoices()"); return ctx,pg,errs
async def main():
  async with async_playwright() as pw:
    b=await pw.chromium.launch()
    # A: 스페인어 음성 없음 (한·일·영만)
    ctx,pg,errs=await page(b,[{"name":"Yuna","lang":"ko-KR","voiceURI":"yuna"},{"name":"Kyoko","lang":"ja-JP","voiceURI":"kyoko"},{"name":"Samantha","lang":"en-US","voiceURI":"sam"}])
    r=await pg.evaluate("()=>[window.__t.canSpeakLang(), window.__t.speak('hola, ¿qué tal?',{audio:null}), window.__spoken.length, document.body.innerText.includes('스페인어 음성이 없다냥')]")
    ok("es 음성 없음: canSpeakLang false", r[0] is False, r)
    ok("es 음성 없음: 다른 언어 음성으로 안 읽음", r[2]==0, r)
    ok("es 음성 없음: 안내 토스트(한국어)", r[3], r)
    r=await pg.evaluate("()=>{ const k=window.__t.S().meta.nvt; window.__t.speak('otra vez',{audio:null}); return [k, window.__t.S().meta.nvt===k, window.__spoken.length]; }")
    ok("안내는 하루 한 번(nvt 기록)", bool(r[0]) and r[1] and r[2]==0, r)
    r=await pg.evaluate("()=>{ window.__t.speak('안녕하세요',{lang:'ko',audio:null}); return window.__spoken.map(x=>x.lang+'/'+x.v); }")
    ok("화면 언어(ko) 읽기는 ko 음성으로 그대로", r==["ko-KR/Yuna"], r)
    ok("오류 없음 (A)", not errs, errs[:3]); await ctx.close()
    # B: es-MX premium · es-US google · es-ES 기본 → es-ES
    ctx,pg,errs=await page(b,[{"name":"Paulina (Premium)","lang":"es-MX","voiceURI":"p"},{"name":"Google español de Estados Unidos","lang":"es-US","voiceURI":"g"},{"name":"Mónica","lang":"es-ES","voiceURI":"m"},{"name":"Yuna","lang":"ko-KR","voiceURI":"yuna"}])
    r=await pg.evaluate("()=>{ const v=window.__t.pickVoice(); window.__t.speak('hola',{audio:null}); return [v&&v.lang, window.__spoken.map(x=>x.lang+'/'+x.v)]; }")
    ok("정확한 언어(es-ES)가 premium·google 다른 지역보다 먼저", r[0]=="es-ES" and r[1]==["es-ES/Mónica"], r)
    r=await pg.evaluate("()=>{ window.__t.S().meta.settings.voices={es:'p'}; return window.__t.pickVoice().lang; }")
    ok("사용자가 고른 음성은 그대로", r=="es-MX", r)
    # C: 화면 언어 음성 없음 → 번역 읽기 안 함
    r=await pg.evaluate("()=>{ window.__spoken.length=0; window.__t.speak('こんにちは',{lang:'ja',audio:null}); return window.__spoken.length; }")
    ok("화면 언어(ja) 음성 없으면 다른 음성으로 안 읽음", r==0, r)
    ok("오류 없음 (B·C)", not errs, errs[:3]); await ctx.close()
    # D: 음성 목록을 아직 못 받음(빈 목록) → 예전처럼 읽음
    ctx,pg,errs=await page(b,[])
    r=await pg.evaluate("()=>{ window.__t.speak('hola',{audio:null}); return [window.__t.canSpeakLang(), window.__spoken.map(x=>x.lang)]; }")
    ok("음성 목록 빈 상태: 판단 안 하고 그대로 읽음", r[0] is True and r[1]==["es-ES"], r)
    await ctx.close(); await b.close()
asyncio.run(main()); import sys; sys.exit(0 if all(R) else 1)
