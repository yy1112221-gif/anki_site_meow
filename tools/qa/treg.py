# 회귀 테스트: 옛 버전(/old/)으로 학습 데이터를 만들고 → 새 버전(/)으로 열어 그대로인지 확인
import json, sys, asyncio
from playwright.async_api import async_playwright
BASE = "http://localhost:8765"
SEED = r"""() => {
  const X = window.__t, S = X.S(), addDays = X.addDays, save = X.save, LS_KEY = "focus-vocab-v1";
  const now = Date.now(), td = X.today();
  const mk = (i, lang, w, m) => ({ id: "treg" + i, lang, word: w, meaning: m, deck: "default", ex: "", due: addDays(td, i % 3), iv: 3 + i, ef: 2.5, reps: 2 + i, u: now });
  [["ja","先生","선생님"],["ja","働く","일하다"],["es","hola","안녕"],["en","apple","사과"],["ko","사과","りんご"]].forEach((x, i) => { S.cards["treg" + i] = mk(i, ...x); });
  S.meta.days = S.meta.days || {}; for(let i = 1; i <= 5; i++) S.meta.days[addDays(td, -i)] = i === 3 ? "freeze" : true;
  Object.assign(S.meta.settings, { ui: "ko", lang: "ja", rate: 0.9, newLimit: 9, strictAccent: true });
  const p = S.meta.pet || (S.meta.pet = {}); p.kcal = 1234; p.lv = 3; p.coins = 77; p.inv = Object.assign(p.inv || {}, { churu: 5 });
  save(); return JSON.parse(localStorage.getItem(LS_KEY));
}"""
def pick(d):
    m = d.get("meta", {}); p = m.get("pet", {}) or {}
    cards = {k: {f: v.get(f) for f in ("word","meaning","lang","due","iv","reps","ef")} for k, v in d.get("cards", {}).items() if k.startswith("treg")}
    return {"cards": cards, "days": m.get("days"), "settings": {k: m.get("settings", {}).get(k) for k in ("ui","lang","rate","newLimit","strictAccent")},
            "pet": {k: p.get(k) for k in ("kcal","lv","coins")}, "churu": (p.get("inv") or {}).get("churu")}
async def main():
    async with async_playwright() as pw:
        b = await pw.chromium.launch(); ctx = await b.new_context(locale="ko-KR"); pg = await ctx.new_page()
        errs = []; pg.on("pageerror", lambda e: errs.append(str(e)))
        await pg.goto(BASE + "/old/index.html", wait_until="load"); await pg.wait_for_timeout(2500)
        before = pick(await pg.evaluate(SEED)); oldv = await pg.evaluate("document.documentElement.innerHTML.match(/APP_VER = \"(v\\d+)/)?.[1] || '?'")
        await pg.goto(BASE + "/index.html", wait_until="load"); await pg.wait_for_timeout(4000)
        newv = await pg.evaluate("document.documentElement.innerHTML.match(/APP_VER = \"(v\\d+)/)?.[1] || '?'")
        after = pick(await pg.evaluate("() => (window.__t.save(), JSON.parse(localStorage.getItem('focus-vocab-v1')))"))
        print(f"old {oldv} → new {newv}")
        ok = True
        for k in before:
            same = before[k] == after[k]; ok &= same
            print(("✅" if same else "❌"), k, "" if same else f"\n  전: {json.dumps(before[k], ensure_ascii=False)[:400]}\n  후: {json.dumps(after[k], ensure_ascii=False)[:400]}")
        if errs: print("⚠️ 페이지 오류:", *errs[:5], sep="\n  ")
        await b.close(); print("결과:", "통과" if ok and not errs else "실패"); sys.exit(0 if ok and not errs else 1)
asyncio.run(main())
