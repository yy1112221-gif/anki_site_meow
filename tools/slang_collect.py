#!/usr/bin/env python3
"""유행어 자동 수집기 (Claude 없이 GitHub Actions에서 매일 돌아감)
여러 수집 방법을 모두 시도하고, 방법별 결과를 report.json에 남긴 뒤
뉴스·검색에서 '따옴표로 인용된 신조어'를 모아 slang/ko.json, slang/ja.json 으로 저장한다."""
import json, re, time, urllib.request, urllib.parse, html, datetime, collections, os, sys
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
OUT = os.path.join(os.path.dirname(__file__), "..", "slang")
TARGET = os.environ.get("SLANG_PROBE", "줴줴이야")

def get(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "ko,ja;q=0.8,en;q=0.5"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", "replace")

def strip(s): return html.unescape(re.sub(r"<[^>]+>", " ", s))
QUOTE = re.compile(r"[‘'\"“「『]([^‘’'\"“”「」『』]{2,14})[’'\"”」』]")
KO = re.compile(r"^[가-힣ㄱ-ㅎㅏ-ㅣ0-9A-Za-z ~!?.…]{2,14}$"); JA = re.compile(r"^[぀-ヿ一-鿿ー0-9A-Za-z〜！？…]{2,14}$")
CUE = {"ko": re.compile(r"유행어|신조어|밈|뜻|유래|챌린지|MZ"), "ja": re.compile(r"流行語|ネットスラング|若者言葉|ミーム|意味|バズ")}
BAD = re.compile(r"유행어|신조어|流行語|新語|뜻|意味|^[0-9 .]+$|^(code|query|relkey|setlog)$|기자|대통령|지원금|\d{4}")
STOP = set("유행어 신조어 밈 뜻 MZ 챌린지 단독 속보 종합 영상 포토 인터뷰 공식 사진 流行語 若者言葉 意味 速報 動画".split())

def rss_items(xml):
    for it in re.findall(r"<item>(.*?)</item>", xml, re.S):
        t = re.search(r"<title>(.*?)</title>", it, re.S); d = re.search(r"<description>(.*?)</description>", it, re.S)
        yield strip(t.group(1) if t else "") + " " + strip(d.group(1) if d else "")

def m_google_news(lang):
    qs = {"ko": ["유행어", "신조어", "밈 뜻", "유행어 뜻", "요즘 유행어"], "ja": ["流行語", "ネットスラング", "若者言葉 意味", "ミーム 意味"]}[lang]
    hl = {"ko": "hl=ko&gl=KR&ceid=KR:ko", "ja": "hl=ja&gl=JP&ceid=JP:ja"}[lang]
    docs = []
    for q in qs: docs += list(rss_items(get(f"https://news.google.com/rss/search?q={urllib.parse.quote(q)}+when:30d&{hl}"))); time.sleep(1)
    return docs
def m_bing_news(lang):
    qs = {"ko": ["유행어", "신조어", "유행어 뜻"], "ja": ["流行語", "ネットスラング"]}[lang]; mk = {"ko": "ko-KR", "ja": "ja-JP"}[lang]
    docs = []
    for q in qs: docs += list(rss_items(get(f"https://www.bing.com/news/search?q={urllib.parse.quote(q)}&format=rss&setmkt={mk}"))); time.sleep(1)
    return docs
def m_google_trends(lang):
    geo = {"ko": "KR", "ja": "JP"}[lang]; return list(rss_items(get(f"https://trends.google.com/trending/rss?geo={geo}")))
def m_naver_news(lang):
    if lang != "ko": return []
    docs = []
    for q in ["유행어", "신조어", "유행어 뜻"]:
        h = get(f"https://search.naver.com/search.naver?where=news&sort=1&query={urllib.parse.quote(q)}")
        docs += [strip(x) for x in re.findall(r'<a[^>]+class="[^"]*news_tit[^"]*"[^>]*>(.*?)</a>|<div[^>]+class="[^"]*dsc_wrap[^"]*"[^>]*>(.*?)</div>', h, re.S) for x in (x if isinstance(x, tuple) else (x,)) if x]
        docs += [strip(x) for x in re.findall(r'<span[^>]*>([^<]{6,120})</span>', h) if CUE["ko"].search(x)]
        time.sleep(1)
    return docs
def m_daum_news(lang):
    if lang != "ko": return []
    docs = []
    for q in ["유행어", "신조어"]:
        h = get(f"https://search.daum.net/search?w=news&sort=recency&q={urllib.parse.quote(q)}"); docs += [strip(x) for x in re.findall(r">([^<>]{8,160})<", h) if CUE["ko"].search(x)]; time.sleep(1)
    return docs
def m_namu(lang):
    if lang != "ko": return []
    h = get("https://namu.wiki/w/%EC%9C%A0%ED%96%89%EC%96%B4"); return [strip(h)[:200000]]

METHODS = {"google_news": m_google_news, "bing_news": m_bing_news, "google_trends": m_google_trends, "naver_news": m_naver_news, "daum_news": m_daum_news, "namu": m_namu}
# 2026-11-18 시험 결과: 줴줴이야를 잡아낸 방법 = google_news · bing_news · naver_news → 이 셋만 실제 사전에 반영 (나머지는 보고서용으로만 계속 시험)
USE = {"google_news", "bing_news", "naver_news"}

def extract(docs, lang):
    c = collections.Counter(); where = collections.defaultdict(set); ok = KO if lang == "ko" else JA
    for i, d in enumerate(docs):
        if not CUE[lang].search(d): continue
        for m in QUOTE.finditer(d):
            t = re.sub(r"^[.…~!?\s]+|[.…~!?\s]+$", "", m.group(1).strip())
            if "…" in t or ".." in t: t = re.split(r"\.\.+|…", t)[-1].strip(" ~!?")
            if t in STOP or BAD.search(t) or not ok.match(t) or len(t.split()) > 2: continue
            c[t] += 1; where[t].add(i)
    return [(t, len(where[t])) for t, _ in c.most_common(80)]

def main():
    report = {"time": datetime.datetime.utcnow().isoformat() + "Z", "probe": TARGET, "methods": {}}
    for lang in ["ko", "ja"]:
        pool = collections.Counter(); srcs = collections.defaultdict(set)
        for name, fn in METHODS.items():
            r = {"ok": False}
            try:
                docs = fn(lang); terms = extract(docs, lang)
                r = {"ok": True, "docs": len(docs), "terms": [t for t, _ in terms[:40]], "probe_in_raw": any(TARGET in d for d in docs), "probe_in_terms": any(TARGET in t for t, _ in terms)}
                if name in USE:
                    for t, n in terms: pool[t] += n; srcs[t].add(name)
            except Exception as e: r = {"ok": False, "err": str(e)[:200]}
            report["methods"][f"{lang}:{name}"] = r; print(lang, name, json.dumps(r, ensure_ascii=False)[:400], flush=True)
        ranked = sorted([{"t": t, "n": n, "src": sorted(srcs[t]), "s": n + 2 * len(srcs[t])} for t, n in pool.items()], key=lambda x: -x["s"])[:60]
        os.makedirs(OUT, exist_ok=True)
        old = []
        try: old = json.load(open(os.path.join(OUT, f"{lang}.json"), encoding="utf-8")).get("terms", [])
        except Exception: pass
        seen = {x["t"] for x in ranked}; keep = [x for x in old if x["t"] not in seen][:40]   # 예전 수집분도 조금 남겨 둠
        json.dump({"updated": report["time"], "terms": ranked + keep}, open(os.path.join(OUT, f"{lang}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(report, open(os.path.join(OUT, "report.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
if __name__ == "__main__": main()
