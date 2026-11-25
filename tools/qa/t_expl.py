# 📖 해설 테스트 (11/25 사용자 요청: 못하다며·頼みました 가 왜 그 모양인지 납득하게)
# 실제 단어장(ko-beg·ja-n5)을 통째로 카드로 만들어
#  ① 해설이 붙은 카드는 자기 예문의 해설(단어장 같은 항목의 x)인지
#  ② 해설 언어 = 화면 언어(ko-beg → ja, ja-n5 → ko), 반대 UI 에서는 안 붙음
#  ③ 이미 푼 카드에도 applyCuration 뒤 붙고, 예문이 다르면 안 보임
#  ④ 화면 HTML: 접힌 <details> 「📖 解説/해설」
import asyncio, json, os, re
from playwright.async_api import async_playwright
R = []
def ok(n, c, i=""): R.append(c); print(("✅" if c else "❌"), n, "" if c else i)
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CASES = [("ko-beg", "ko", "ja", re.compile(r"[぀-ヿ]")), ("ja-n5", "ja", "ko", re.compile(r"[가-힯]"))]

def xmap(n):
    items = json.load(open(f"{ROOT}/presets/{n}.json", encoding="utf-8"))["items"]; m = {}
    for it in items:
        X = next((v for v in it if isinstance(v, dict)), None)
        if X and X.get("x"):
            ex = X.get("e") or (it[3] if n.startswith("ko") and len(it) > 3 and isinstance(it[3], str) else "")
            m.setdefault(it[0], []).append((ex, X["x"]))
    return m

async def main():
    async with async_playwright() as pw:
        b = await pw.chromium.launch(); errs = []
        for n, lang, ui, rx in CASES:
            M = xmap(n); total = sum(len(v) for v in M.values())
            ok(f"{n}: 해설 {total}개, 모두 {ui} 한 언어·120자 이하", total > 0 and all(set(x) == {ui} and rx.search(x[ui]) and len(x[ui]) <= 120 for L in M.values() for _, x in L))
            for u in (ui, lang if lang != ui else "ko"):
                pg = await b.new_page(); pg.on("pageerror", lambda e: errs.append(str(e)))
                seed = {"cards": {}, "meta": {"setup": 1, "tutAsked": 1, "loginAsked": 1, "days": {}, "decks": [], "settings": {"ui": u, "lang": lang, "newLimit": 0}}}
                await pg.goto("http://localhost:8765/index.html")
                await pg.evaluate("s => localStorage.setItem('focus-vocab-v1', s)", json.dumps(seed, ensure_ascii=False))
                await pg.reload(); await pg.wait_for_timeout(1200)
                res = await pg.evaluate("""async n => { const t = window.__t, S = t.S(); const r = await fetch('presets/' + n + '.json'); const data = await r.json();
                    const d = { id: 'm_' + n, preset: n, cursor: 0 }; t.materialize(d, data, data.items.length);
                    return Object.values(S.cards).map(c => [c.word, c.example || '', c.expl || '', t.explHTML(c)]); }""", n)
                withx = [r for r in res if r[2]]
                if u == ui:
                    wrong = [(w, e[:14]) for w, e, x, h in withx if not any(ex == e and xx[ui] == x for ex, xx in M.get(w, []))]
                    ok(f"[화면 {u}] {n} 새 카드 {len(res)}장 중 해설 {len(withx)}장: 모두 자기 예문의 해설", len(withx) >= total * 0.8 and not wrong, (len(withx), wrong[:5]))
                    h = next((h for w, e, x, h in withx), "")
                    ok(f"[화면 {u}] 화면: 접힌 <details> 「📖 {'解説' if u == 'ja' else '해설'}」", h.startswith('<details class="fb-expl">') and ("解説" if u == "ja" else "해설") in h and " open" not in h, h[:80])
                    # ③ 푼 카드 + 예문 다른 카드
                    w0, L0 = next(iter(M.items()))
                    r3 = await pg.evaluate("""async ([n, w, ex]) => { const t = window.__t, S = t.S(); Object.keys(S.cards).forEach(k => delete S.cards[k]);
                        S.meta.decks = [{ id: 'd1', name: '', on: true, preset: n, cursor: 0 }];
                        S.cards.a = { id: 'a', lang: S.meta.settings.lang, deck: 'd1', word: w, meaning: 'm', example: ex, form: '', isNew: false, reps: 3, level: 2, due: '2030-01-01', u: 1 };
                        S.cards.b = { id: 'b', lang: S.meta.settings.lang, deck: 'd1', word: w, meaning: 'm', example: '内容がちがう例文 다른 예문', isNew: false, reps: 3, level: 2, due: '2030-01-01', u: 1 };
                        await t.applyCuration(true); const a = S.cards.a, b2 = S.cards.b; return [a.expl || '', t.explHTML(a) ? 1 : 0, t.explHTML(b2) ? 1 : 0]; }""", [n, w0, L0[0][0]])
                    ok(f"[화면 {u}] 이미 푼 카드에도 해설이 붙고, 다른 예문 카드엔 안 보임", r3[0] == L0[0][1][ui] and r3[1] == 1 and r3[2] == 0, r3)
                else:
                    ok(f"[화면 {u}] {n}: 다른 화면 언어에선 해설 안 붙음(언어 원칙)", not withx, withx[:3])
                await pg.close()
        ok("페이지 오류 없음", not errs, errs[:3])
        await b.close()
asyncio.run(main())
raise SystemExit(0 if all(R) else 1)
