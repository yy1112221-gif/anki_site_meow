#!/usr/bin/env python3
"""유행어(슬랭) 자동 수집기 — Claude 없이 GitHub Actions에서 매일 돌아감.
1) 여러 방법을 시험(보고서 report.json). 2026-11-18 시험에서 '줴줴이야'를 잡아낸 방법(google/bing/naver 뉴스)만 사전에 반영.
2) 뜻: 기사 속 설명 문장(뜻·의미·means·significa·とは…)을 그대로 수집.
3) 예문: 기사 속 실제 문장 중, 슬랭 말고는 쉬운 일반 어휘·문법으로 된 문장을 골라 수집. 문장을 지어내지 않는다."""
import json, re, time, urllib.request, urllib.parse, html, datetime, collections, os
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
OUT = os.path.join(os.path.dirname(__file__), "..", "slang"); TARGET = os.environ.get("SLANG_PROBE", "줴줴이야")
LANGS = ["ko", "ja", "en", "es"]
def get(url, timeout=20):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept-Language": "ko,ja,en,es;q=0.8"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        raw = r.read(); ct = r.headers.get_content_charset() or "utf-8"
        return raw.decode(ct, "replace")
def strip(s): return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", s))).strip()
QUOTE = re.compile(r"[‘'\"“「『]([^‘’'\"“”「」『』]{2,24})[’'\"”」』]")
OK = {"ko": re.compile(r"^[가-힣ㄱ-ㅎㅏ-ㅣ0-9A-Za-z ~!?.…]{2,14}$"), "ja": re.compile(r"^[぀-ヿ一-鿿ー0-9A-Za-z〜！？…]{2,14}$"),
      "en": re.compile(r"^[a-z][a-z' -]{1,22}$"), "es": re.compile(r"^[a-záéíóúñü][a-záéíóúñü' -]{1,22}$")}
CUE = {"ko": re.compile(r"유행어|신조어|밈|뜻|유래|챌린지|MZ"), "ja": re.compile(r"流行語|ネットスラング|若者言葉|ミーム|意味|バズ"),
       "en": re.compile(r"slang|gen z|meme|means|meaning|word of the year|lingo", re.I), "es": re.compile(r"jerga|argot|significa|significado|palabra del año|generación z|meme", re.I)}
DEF = {"ko": re.compile(r"뜻|의미|비롯|유래|가리키|표현이다|말이다|쓰인다|사용된다"), "ja": re.compile(r"意味|とは|由来|指す|使われ|表現"),
       "en": re.compile(r"\bmeans?\b|\bmeaning\b|refers? to|used to (describe|say)|is slang for|describes", re.I), "es": re.compile(r"significa|se refiere|se usa para|quiere decir|término", re.I)}
META = {"ko": re.compile(r"(이)?라는|(이)?라고|표현|유행어|신조어|단어"), "ja": re.compile(r"という|と(言|い)う|言葉|流行語"), "en": re.compile(r"\bterm\b|\bword\b|\bslang\b|\bphrase\b|called", re.I), "es": re.compile(r"término|palabra|expresión|jerga", re.I)}
BAD = re.compile(r"유행어|신조어|流行語|新語|뜻|意味|^[0-9 .]+$|^(code|query|relkey|setlog)$|기자|대통령|지원금|\d{4}|word of the year|gen z|slang", re.I)
STOP = set("오늘의 진짜 괜찮아 개콘 개그콘서트 네 아니 그냥 정말 밈 MZ 챌린지 단독 속보 종합 영상 포토 인터뷰 공식 사진 若者言葉 速報 動画 the and you this that what".split())
NEWSQ = {"ko": ["유행어", "신조어", "유행어 뜻", "요즘 유행어"], "ja": ["流行語", "ネットスラング", "若者言葉 意味"],
         "en": ["slang meaning", "gen z slang", "new slang word"], "es": ["jerga juvenil significado", "palabra de moda significa", "jerga generación z"]}
HL = {"ko": ("ko", "KR"), "ja": ("ja", "JP"), "en": ("en", "US"), "es": ("es", "ES")}
def rss_items(xml):
    for it in re.findall(r"<item>(.*?)</item>", xml, re.S):
        t = re.search(r"<title>(.*?)</title>", it, re.S); d = re.search(r"<description>(.*?)</description>", it, re.S); l = re.search(r"<link>(.*?)</link>", it, re.S)
        yield strip(t.group(1) if t else "") + " " + strip(d.group(1) if d else ""), strip(l.group(1)) if l else ""
def m_google_news(lang):
    h, g = HL[lang]; out = []
    for q in NEWSQ[lang]: out += list(rss_items(get(f"https://news.google.com/rss/search?q={urllib.parse.quote(q)}+when:30d&hl={h}&gl={g}&ceid={g}:{h}"))); time.sleep(1)
    return out
def m_bing_news(lang):
    h, g = HL[lang]; out = []
    for q in NEWSQ[lang]:
        for txt, link in rss_items(get(f"https://www.bing.com/news/search?q={urllib.parse.quote(q)}&format=rss&setmkt={h}-{g}")):
            u = urllib.parse.parse_qs(urllib.parse.urlparse(link).query).get("url", [link])[0]; out.append((txt, u))
        time.sleep(1)
    return out
def m_naver_news(lang):
    if lang != "ko": return []
    out = []
    for q in NEWSQ["ko"][:3]:
        h = get(f"https://search.naver.com/search.naver?where=news&sort=1&query={urllib.parse.quote(q)}")
        out += [(strip(x), "") for x in re.findall(r'<span[^>]*>([^<]{6,160})</span>', h) if CUE["ko"].search(x)]
        out += [("", u) for u in re.findall(r'href="(https?://[^"]+)"[^>]*class="[^"]*news_tit', h)][:8]; time.sleep(1)
    return out
def m_google_trends(lang): g = HL[lang][1]; return list(rss_items(get(f"https://trends.google.com/trending/rss?geo={g}")))
def m_namu(lang): return [(strip(get("https://namu.wiki/w/%EC%9C%A0%ED%96%89%EC%96%B4"))[:100000], "")] if lang == "ko" else []
METHODS = {"google_news": m_google_news, "bing_news": m_bing_news, "naver_news": m_naver_news, "google_trends": m_google_trends, "namu": m_namu}
USE = {"google_news", "bing_news", "naver_news"}

def clean_term(t):
    t = re.sub(r"^[.…~!?\s]+|[.…~!?\s]+$", "", t.strip())
    if "…" in t or ".." in t: t = re.split(r"\.\.+|…", t)[-1].strip(" ~!?")
    return t
def extract(docs, lang):
    c = collections.Counter(); where = collections.defaultdict(set)
    for i, (d, _) in enumerate(docs):
        if not CUE[lang].search(d): continue
        for m in QUOTE.finditer(d):
            t = clean_term(m.group(1)); tl = t.lower() if lang in ("en", "es") else t
            if tl in STOP or BAD.search(tl) or not OK[lang].match(tl) or len(t.split()) > (3 if lang in ("en", "es") else 2): continue
            c[tl] += 1; where[tl].add(i)
    return [(t, len(where[t])) for t, _ in c.most_common(80)]

SENT = {"ko": re.compile(r"(?<=[.!?。])\s+|(?<=다\.)\s*|(?<=요\.)\s*"), "ja": re.compile(r"(?<=[。！？])"), "en": re.compile(r"(?<=[.!?])\s+(?=[A-Z\"“])"), "es": re.compile(r"(?<=[.!?])\s+(?=[A-ZÁÉÍÓÚ¿¡\"“])")}
def article_sentences(url, lang):
    try: h = get(url, 15)
    except Exception: return []
    ps = [strip(p) for p in re.findall(r"<p[^>]*>(.*?)</p>", h, re.S)]
    if len(" ".join(ps)) < 200: ps = [strip(x) for x in re.findall(r">([^<>]{40,600})<", h)]
    out = []
    for p in ps:
        for s in SENT[lang].split(p):
            s = s.strip()
            if 8 <= len(s) <= 260: out.append(s)
    return out
def ex_score(s, term, lang):
    """예문 고르기: 슬랭 말고는 쉬운 일반 문장일수록 높게"""
    n = len(s); sc = 0.0
    if lang in ("ko", "ja"): sc -= abs(n - 32) / 10
    else: w = len(s.split()); sc -= abs(w - 13) / 3
    sc -= len(re.findall(r"\d", s)) * .6 + len(re.findall(r"[()\[\]@#/|]", s)) * 1.5 + max(0, len(QUOTE.findall(s)) - 1) * 1.2
    if lang in ("en", "es"): sc -= max(0, len(re.findall(r"\b[A-Z][a-z]+", s[1:])) - 1) * .8   # 고유명사 많으면 감점
    if re.search(r"기자|사진=|제공|무단|Copyright|©|記者|写真|ニュース|reporter|via |Getty", s, re.I): sc -= 6
    if META[lang].search(s): sc -= 2.5     # '…라는 표현' 같은 설명문보다 실제로 쓰인 문장 우대
    if DEF[lang].search(s): sc -= 2
    if not re.search(r"[.!?。！？다요]\s*$", s): sc -= 1.5
    return sc
def gather(term, lang, links, docs):
    sents = []
    for d, _ in docs:
        if term in (d.lower() if lang in ("en", "es") else d): sents += [x.strip() for x in SENT[lang].split(d) if x.strip()]
    for u in links[:6]: sents += article_sentences(u, lang); time.sleep(.5)
    key = (lambda s: term in s.lower()) if lang in ("en", "es") else (lambda s: term in s)
    hit = list(dict.fromkeys(s for s in sents if key(s)))
    defs = sorted([s for s in hit if DEF[lang].search(s) and len(s) < 220], key=len)[:2]
    exs = sorted([s for s in hit if s not in defs], key=lambda s: -ex_score(s, term, lang))[:3]
    return defs, [s for s in exs if ex_score(s, term, lang) > -9]

def main():
    report = {"time": datetime.datetime.utcnow().isoformat() + "Z", "probe": TARGET, "methods": {}}
    os.makedirs(OUT, exist_ok=True)
    for lang in LANGS:
        pool = collections.Counter(); srcs = collections.defaultdict(set); alldocs = []
        for name, fn in METHODS.items():
            try:
                docs = fn(lang); terms = extract(docs, lang)
                r = {"ok": True, "docs": len(docs), "terms": [t for t, _ in terms[:30]], "probe_in_raw": any(TARGET in d for d, _ in docs), "probe_in_terms": any(TARGET in t for t, _ in terms)}
                if name in USE:
                    alldocs += docs
                    for t, n in terms: pool[t] += n; srcs[t].add(name)
            except Exception as e: r = {"ok": False, "err": str(e)[:200]}
            report["methods"][f"{lang}:{name}"] = r; print(lang, name, json.dumps(r, ensure_ascii=False)[:300], flush=True)
        ranked = sorted([{"t": t, "n": n, "src": sorted(srcs[t]), "s": n + 2 * len(srcs[t])} for t, n in pool.items()], key=lambda x: -x["s"])[:40]
        old = {}
        try: old = {x["t"]: x for x in json.load(open(os.path.join(OUT, f"{lang}.json"), encoding="utf-8")).get("terms", [])}
        except Exception: pass
        for x in ranked[:25]:   # 상위 단어만 뜻·예문 수집 (예전에 모은 건 유지·보강)
            o = old.get(x["t"], {}); x["first"] = o.get("first", report["time"][:10]); x["def"] = o.get("def", []); x["ex"] = o.get("ex", [])
            links = [u for d, u in alldocs if u and x["t"] in (d.lower() if lang in ("en", "es") else d)]
            try:
                defs, exs = gather(x["t"], lang, links, alldocs)
                x["def"] = list(dict.fromkeys(x["def"] + defs))[:3]; x["ex"] = list(dict.fromkeys(exs + x["ex"]))[:4]
            except Exception as e: print("gather", x["t"], e)
        seen = {x["t"] for x in ranked}; keep = [v for k, v in old.items() if k not in seen and (v.get("ex") or v.get("def"))][:60]
        json.dump({"updated": report["time"], "lang": lang, "terms": ranked + keep}, open(os.path.join(OUT, f"{lang}.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    json.dump(report, open(os.path.join(OUT, "report.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
if __name__ == "__main__": main()
