# 큐레이션 번역 섞임 테스트 (11/25 사용자 발견: ko-beg 「못하다」 #3 예문에 #1677 예문의 번역이 붙음)
# 실제 단어장 전부에서 「같은 단어가 두 번 이상 + 큐레이션 있음」을 찾아,
#  ① 다른 예문의 번역이 붙은 푼 카드 → applyCuration 뒤 자기 번역(또는 빈칸)으로 고쳐지는지
#  ② 새로 만든 카드(materialize) → 자기 예문의 번역만 붙는지
# 를 화면 언어 ko·ja 둘 다에서 본다. 손으로 만든 예시가 아니라 저장소의 presets/*.json 을 그대로 읽는다.
import asyncio, json, glob, os
from playwright.async_api import async_playwright
R = []
def ok(n, c, i=""): R.append(c); print(("✅" if c else "❌"), n, "" if c else i)
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def cases():
    out = []
    for p in sorted(glob.glob(f"{ROOT}/presets/*.json")):
        name = os.path.basename(p)[:-5]
        if name.startswith("script-") or name.endswith("-slang"): continue
        try: items = json.load(open(p, encoding="utf-8")).get("items") or []
        except Exception: continue
        lang = name.split("-")[0]; by = {}
        for i, it in enumerate(items):
            if not isinstance(it, list) or not it: continue
            X = next((v for v in it if isinstance(v, dict)), None)
            if not X: continue
            ex = X.get("e") or (it[3] if lang == "ko" and len(it) > 3 and isinstance(it[3], str) else "")
            if ex: by.setdefault(it[0], []).append((i, ex, X.get("t") or {}, X.get("f") or it[0]))
        for w, L in by.items():
            if len(L) > 1: out.append((name, lang, w, L))
    return out

async def main():
    C = cases()
    print(f"같은 단어 여럿 + 큐레이션: {len(C)}개", ", ".join(f"{n}:{w}" for n, _, w, _ in C[:15]))
    async with async_playwright() as pw:
        b = await pw.chromium.launch(); errs = []
        for ui in ("ja", "ko"):
            rows = [(n, l, w, L) for n, l, w, L in C if l != ui and any(t.get(ui) for _, _, t, _ in L)]
            if not rows: continue
            pg = await b.new_page(); pg.on("pageerror", lambda e: errs.append(str(e)))
            cards, decks, expect = {}, {}, {}
            for n, l, w, L in rows:
                decks[n] = {"id": "d_" + n, "name": "", "on": True, "preset": n, "cursor": 0}
                for a, (ia, exa, ta, fa) in enumerate(L[:1]):   # 앱은 같은 단어를 카드 한 장(단어장에서 먼저 나온 항목)으로만 만든다
                    other = next((t.get(ui) for k, (_, _, t, _) in enumerate(L) if k != a and t.get(ui) and t.get(ui) != ta.get(ui)), None)
                    if not other: continue
                    cid = f"x{len(cards)}"
                    cards[cid] = {"id": cid, "lang": l, "deck": "d_" + n, "word": w, "meaning": "m", "example": exa, "form": fa, "exampleKo": other,
                                  "isNew": False, "reps": 2, "level": 1, "due": "2030-01-01", "u": 1}
                    expect[cid] = (n, w, ia, ta.get(ui) or "")
            seed = {"cards": cards, "meta": {"setup": 1, "tutAsked": 1, "loginAsked": 1, "days": {}, "decks": list(decks.values()),
                                             "settings": {"ui": ui, "lang": rows[0][1], "newLimit": 0}}}
            await pg.goto("http://localhost:8765/index.html")
            await pg.evaluate("s => localStorage.setItem('focus-vocab-v1', s)", json.dumps(seed, ensure_ascii=False))
            await pg.reload(); await pg.wait_for_timeout(1500)
            await pg.evaluate("() => window.__t.applyCuration(true)")
            got = await pg.evaluate("() => Object.fromEntries(Object.values(window.__t.S().cards).map(c => [c.id, c.exampleKo || '']))")
            bad = [(expect[k][0], expect[k][1], f"#{expect[k][2]}", (got.get(k) or "")[:18]) for k in expect
                   if got.get(k, "") not in ("", expect[k][3])]
            ok(f"[화면 {ui}] 같은 단어 {len(rows)}개·카드 {len(expect)}장: 다른 예문 번역이 안 붙음", not bad, bad[:6])
            miss = [k for k in expect if k.startswith("x") and got.get(k, "") != expect[k][3] and expect[k][3]]
            ok(f"[화면 {ui}] 섞였던 카드는 자기 번역으로 고쳐짐", not miss, [(expect[k][1], f"#{expect[k][2]}") for k in miss[:6]])
            # ② 새 카드: 단어장을 처음부터 실제로 카드로 만들기(materialize) → 번역이 그 카드 예문의 것인지
            for n in sorted({r[0] for r in rows}):
                res = await pg.evaluate("""async n => { const t = window.__t, S = t.S(); Object.keys(S.cards).forEach(k => delete S.cards[k]);
                    const r = await fetch('presets/' + n + '.json'); const data = await r.json(); const d = { id: 'm_' + n, preset: n, cursor: 0 };
                    t.materialize(d, data, data.items.length); return Object.values(S.cards).map(c => [c.word, c.example || '', c.exampleKo || '']); }""", n)
                items = json.load(open(f"{ROOT}/presets/{n}.json", encoding="utf-8"))["items"]
                tr_of = {}
                for it in items:
                    X = next((v for v in it if isinstance(v, dict)), None)
                    ex = X and (X.get("e") or (it[3] if n.startswith("ko") and len(it) > 3 and isinstance(it[3], str) else ""))
                    if X and ex and (X.get("t") or {}).get(ui): tr_of[(X["t"][ui])] = ex
                wrong = [(w, e[:16], k[:16]) for w, e, k in res if k in tr_of and tr_of[k] != e]
                ok(f"[화면 {ui}] {n} 새 카드 {len(res)}장: 번역이 자기 예문의 것", not wrong, wrong[:6])
            await pg.close()
        ok("페이지 오류 없음", not errs, errs[:3])
        await b.close()
    if not C: ok("검사 대상 없음(같은 단어 중복이 없으면 통과)", True)
asyncio.run(main())
raise SystemExit(0 if all(R) else 1)
