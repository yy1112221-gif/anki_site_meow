# MEOWCA ⑥: 일본어 단어장 보조 데이터 생성 (읽기 함정·숙자훈·가나 단어·한자 트리)
# 실행: python3 tools/build_ja_extra.py /path/to/jamdict.db → presets/ja-extra.json · presets/ja-kanji.json · tools/ja_review.json
import json, re, sqlite3, sys, collections, itertools
import os
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = sys.argv[1] if len(sys.argv) > 1 else 'jamdict.db'   # pip download jamdict-data 후 jamdict.db.xz 압축 풀기
LV = ['n5','n4','n3','n2','n1']
k2h = lambda s: ''.join(chr(ord(ch)-0x60) if 'ァ'<=ch<='ヶ' else ch for ch in s)
isK = lambda ch: bool(re.match(r'[一-龯々〆ヵヶ]', ch))
db = sqlite3.connect(DB)

# ---------- KANJIDIC: 한자별 읽기 ----------
U2I = dict(zip('うくぐすつぬぶむる', 'いきぎしちにびみり'))
KR = collections.defaultdict(set); ON = collections.defaultdict(list); KO = {}
for lit, rt, val in db.execute("select ch.literal,r.r_type,r.value from character ch join rm_group g on g.cid=ch.ID join reading r on r.gid=g.ID where r.r_type in ('ja_on','ja_kun','korean_h')"):
    if rt == 'korean_h': KO.setdefault(lit, []).append(val); continue
    v = k2h(val).replace('-', '')
    if rt == 'ja_kun':
        stem, _, oku = v.partition('.')
        for k in range(len(oku)+1): KR[lit].add(stem + oku[:k])          # 오쿠리가나 일부 생략(当り·落し物)
        if oku and oku[-1] in U2I: KR[lit].add(stem + oku[:-1] + U2I[oku[-1]])   # 연용형(物語·知合い)
    else: KR[lit].add(v); ON[lit].append(v)
U2I = dict(zip('うくぐすつぬぶむる', 'いきぎしちにびみり'))
DAK = dict(zip('かきくけこさしすせそたちつてとはひふへほ', 'がぎぐげござじずぜぞだぢづでどばびぶべぼ'))
HAN = dict(zip('はひふへほ', 'ぱぴぷぺぽ'))
def variants(r):
    out = {r}
    if r and r[0] in DAK: out.add(DAK[r[0]] + r[1:])          # 연탁
    if r and r[0] in HAN: out.add(HAN[r[0]] + r[1:])
    if len(r) >= 2 and r[-1] in 'つくちき': out.add(r[:-1] + 'っ')   # 촉음화
    if r and r[0] == 'ち': out.add('じ' + r[1:])                   # 中(じゅう)
    if r and r[0] == 'つ': out.add('ず' + r[1:])
    out.add(r + 'っ')                                            # 切手(き+っ+て)
    return out
def segmentable(word, read):
    """한자별 읽기(+연탁·촉음)로 읽기를 나눌 수 있는가"""
    w = list(word); r = read
    from functools import lru_cache
    @lru_cache(None)
    def go(i, j, prev):
        if i == len(w): return j == len(r)
        ch = w[i]
        if not isK(ch):
            h = k2h(ch)
            return r.startswith(h, j) and go(i+1, j+len(h), '')
        src = prev if ch == '々' else ch
        for base in KR.get(src, ()):
            for v in variants(base):
                if v and r.startswith(v, j) and go(i+1, j+len(v), src): return True
        return False
    return go(0, 0, '')

def pieces(word, read):
    """읽기를 한자별 조각으로 나눔: [(시작, 끝, 'on'|'kun'|'kana')] — 못 나누면 None"""
    w = list(word); r = read
    from functools import lru_cache
    @lru_cache(None)
    def go(i, j, prev):
        if i == len(w): return () if j == len(r) else None
        ch = w[i]
        if not isK(ch):
            h = k2h(ch)
            if r.startswith(h, j):
                t = go(i+1, j+len(h), '')
                if t is not None: return ((j, j+len(h), 'kana'),) + t
            return None
        src = prev if ch == '々' else ch
        for base in sorted(KR.get(src, ()), key=lambda b: -len(b)):
            for v in variants(base):
                if v and r.startswith(v, j):
                    t = go(i+1, j+len(v), src)
                    if t is not None: return ((j, j+len(v), 'on' if base in ON[src] else 'kun'),) + t
        return None
    return go(0, 0, '')

# ---------- JMdict: 표기별 정보 ----------
def jm(word):
    """word(한자 표기)에 대한 JMdict 정보: 읽기 목록, 숙자훈/당자 읽기, 가나 표기 우선 여부"""
    ids = [x[0] for x in db.execute("select idseq from Kanji where text=?", (word,))]
    reads, juku, uk, ateji = set(), set(), False, False
    for i in ids:
        if db.execute("select 1 from KJI k join Kanji kk on kk.ID=k.kid where kk.idseq=? and kk.text=? and k.text like 'ateji%'", (i, word)).fetchone(): ateji = True
        for kid, t in db.execute("select ID,text from Kana where idseq=?", (i,)):
            reads.add(t)
            if db.execute("select 1 from KNI where kid=? and text like 'gikun%'", (kid,)).fetchone(): juku.add(t)
        sens = [s for (s,) in db.execute("select ID from Sense where idseq=? order by ID", (i,))]
        if sens and db.execute("select 1 from misc where sid=? and text like 'word usually written using kana%'", (sens[0],)).fetchone(): uk = True
    return reads, juku, uk, ateji

# ---------- 읽기 함정 (JLPT 문제1식: 장음·탁음·촉음만 살짝 틀린 그럴듯한 오답) ----------
O_ROW = set('おこごそぞとどのほぼぽもよろょ'); E_ROW = set('えけげせぜてでねへべぺめれ')
UNV = set('かきくけこさしすせそたちつてとはひふへほぱぴぷぺぽ')
UNDAK = {v:k for k,v in DAK.items() if v not in 'ぢづ'}; UNDAK.update({v:k for k,v in HAN.items()})
def core_span(w, r):
    """읽기 중 한자에 해당하는 구간(앞의 お·ご, 뒤의 오쿠리가나 제외)"""
    i = 0
    while i < len(w) and not isK(w[i]) and r.startswith(k2h(w[:i+1])): i += 1
    j = 0
    while j < len(w) - i and not isK(w[-1-j]) and r.endswith(k2h(w[len(w)-1-j:])): j += 1
    return len(k2h(w[:i])), len(r) - len(k2h(w[len(w)-j:])) if j else len(r)
def traps(w, r, real):
    ps = pieces(w, r)
    if ps is None: s0, e0 = core_span(w, r); ps = [(s0, e0, 'on')]
    c = {'long': [], 'dak': [], 'sok': []}
    for k, (a, b, kind) in enumerate(ps):
        if kind == 'kana': continue
        if kind == 'kun':                       # 훈독은 연탁 자리(두 번째 이후 한자 첫소리)만 흔들기
            if k and r[a] in DAK and DAK[r[a]] not in 'ぢづ': c['dak'].append(r[:a] + DAK[r[a]] + r[a+1:])
            if k and r[a] in UNDAK: c['dak'].append(r[:a] + UNDAK[r[a]] + r[a+1:])
            continue
        seg = r[a:b]
        # 장음: 음독 조각 끝의 う·い를 빼거나, 1음절 음독에 붙이기 (とちゅう↔とうちゅう, めいし↔めし)
        if len(seg) >= 2 and seg[-1] == 'う' and (seg[-2] in O_ROW or seg[-2] == 'ゅ'): c['long'].append(r[:b-1] + r[b:])
        elif len(seg) >= 2 and seg[-1] == 'い' and seg[-2] in E_ROW: c['long'].append(r[:b-1] + r[b:])
        elif seg[-1] in O_ROW or seg[-1] == 'ゅ': c['long'].append(r[:b] + 'う' + r[b:])
        elif seg[-1] in E_ROW: c['long'].append(r[:b] + 'い' + r[b:])
        # 탁음: 음독 첫소리
        if a == 0 or r[a-1] != 'っ':
            ch = r[a]
            if ch in DAK and DAK[ch] not in 'ぢづ': c['dak'].append(r[:a] + DAK[ch] + r[a+1:])
            if ch in UNDAK: c['dak'].append(r[:a] + UNDAK[ch] + r[a+1:])
            if ch in 'ぱぴぷぺぽ': c['dak'].append(r[:a] + DAK[UNDAK[ch]] + r[a+1:])
        # 촉음: 음독 끝 っ ↔ つ·く
        if seg[-1] == 'っ': c['sok'] += [r[:b-1] + 'つ' + r[b:], r[:b-1] + r[b:]]
        elif seg[-1] in 'つく' and len(seg) == 2 and b < len(r) and r[b] in UNV: c['sok'].append(r[:b-1] + 'っ' + r[b:])
    bad = set(real) | {r}; out = []
    ok = lambda x: x not in bad and len(x) >= 2 and not re.search('ぢ|づ|っっ|^っ|っ$|うう|いい', x)
    for kind in ('long', 'dak', 'sok'):
        for x in c[kind]:
            if ok(x): out.append(x); bad.add(x); break
    for kind in ('dak', 'long', 'sok'):
        for x in c[kind]:
            if len(out) >= 3: break
            if ok(x): out.append(x); bad.add(x)
    return out[:3]

# ---------- 사용자 한자 리스트 ----------
USER = {}; USER_JUKU = set()
for line in open(f'{REPO}/tools/kanji_core_n5n3.md', encoding='utf-8'):
    cols = [x.strip() for x in line.strip().strip('|').split('|')]
    if len(cols) >= 7 and cols[0].startswith('Lv') and len(cols[2]) == 1:
        lv = cols[0]; kj = cols[2]
        USER[kj] = {'lv': int(lv[2]), 'cat': cols[1] if not cols[1].isdigit() else '', 'ko': cols[3], 'on': cols[4], 'kun': cols[5], 'ex': cols[6]}
        for m in re.finditer(r'★([^\s(（,]+)\(([ぁ-ゖ/]+)', cols[6]):
            USER_JUKU.add(m.group(1))
KANA_ONLY_USER = {'鞄','椅子','瓶','此れ','為','可成り','態々','態態','嘴','噛む','丈'}

# ---------- 상용한자표 付表 (공식 숙자훈·당자) ----------
FUHYO = [l.split() for l in '''あす 明日|あずき 小豆|あま 海女|あま 海士|いおう 硫黄|いくじ 意気地|いなか 田舎|いぶき 息吹|うなばら 海原|うば 乳母|うわき 浮気|うわつ 浮つ|えがお 笑顔|おじ 叔父|おじ 伯父|おとな 大人|おとめ 乙女|おば 叔母|おば 伯母|おまわり お巡り|おみき 御神酒|おもや 母屋|おもや 母家|かあ 母さん|かぐら 神楽|かし 河岸|かじ 鍛冶|かぜ 風邪|かたず 固唾|かな 仮名|かや 蚊帳|かわせ 為替|かわら 河原|かわら 川原|きのう 昨日|きょう 今日|くだもの 果物|くろうと 玄人|けさ 今朝|けしき 景色|ここち 心地|こじ 居士|ことし 今年|さおとめ 早乙女|ざこ 雑魚|さじき 桟敷|さしつかえ 差し支え|さしつかえ 差支え|さつき 五月|さなえ 早苗|さみだれ 五月雨|しぐれ 時雨|しっぽ 尻尾|しない 竹刀|しにせ 老舗|しばふ 芝生|しみず 清水|しゃみせん 三味線|じゃり 砂利|じゅず 数珠|じょうず 上手|しらが 白髪|しろうと 素人|しわす 師走|すきや 数寄屋|すもう 相撲|ぞうり 草履|だし 山車|たち 太刀|たちの 立ち退|たなばた 七夕|たび 足袋|ちご 稚児|ついたち 一日|つきやま 築山|つゆ 梅雨|でこぼこ 凸凹|てつだ 手伝|とあみ 投網|とう 父さん|とえはたえ 十重二十重|どきょう 読経|とけい 時計|ともだち 友達|なこうど 仲人|なごり 名残|なだれ 雪崩|にい 兄さん|ねえ 姉さん|のら 野良|のりと 祝詞|はかせ 博士|はたち 二十歳|はたち 二十|はつか 二十日|はとば 波止場|ひとり 一人|ひより 日和|ふたり 二人|ふつか 二日|ふぶき 吹雪|へた 下手|へや 部屋|まいご 迷子|まじめ 真面目|まっか 真っ赤|まっさお 真っ青|みやげ 土産|むすこ 息子|めがね 眼鏡|もさ 猛者|もみじ 紅葉|もめん 木綿|もより 最寄|やおちょう 八百長|やおや 八百屋|やまと 大和|やよい 弥生|ゆかた 浴衣|ゆくえ 行方|よせ 寄席|わこうど 若人'''.split('|')]
def fuhyo(w, r): return any(k in w and rd in r for rd, k in FUHYO)

NOT_JUKU = {'温い','扇ぐ','錆びる','詰る','湿気る','清む','清ます','空ろ','斑','予て','傾らか','各々','田ぼ','図々しい','坊っちゃん'}   # 드문 훈독일 뿐 숙자훈은 아님
# ---------- 처리 ----------
words = {}; order = []
for lv in LV:
    for it in json.load(open(f'{REPO}/presets/ja-{lv}.json'))['items']:
        w = it[0]
        if w in words: continue
        words[w] = (lv, it); order.append(w)
extra = {}; stats = collections.Counter(); review = []
ONCNT = collections.Counter()                                 # 단어장에서 실제로 많이 쓰인 음독 순으로
for w in order:
    r = (words[w][1][1] or '').split(';')[0].strip()
    ps = pieces(w, r) if r and re.fullmatch(r'[ぁ-ゖー]+', r) else None
    if ps:
        ks = [ch for ch in w if isK(ch) or True]
        for ch, (a, b, kind) in zip(w, ps):
            if kind == 'on': ONCNT[(ch, r[a:b])] += 1
for ch in ON: ON[ch].sort(key=lambda v: -ONCNT[(ch, v)])
for w in order:
    lv, it = words[w]; r0 = it[1] or ''
    if not re.search(r'[一-龯々]', w) or '、' in w: continue
    rs = [x.strip() for x in re.split(r'[;；]', r0) if x.strip()] if re.fullmatch(r'[ぁ-ゖー;； ]+', r0 or '-') else []
    reads, jk, uk, ateji = jm(w)
    e = {}
    main = rs[0] if rs else ''
    if main.endswith('する') and main[:-2] in reads: e['r'] = main[:-2]; main = main[:-2]; stats['fixread'] += 1   # 準備: じゅんびする → じゅんび
    elif main and main not in reads and ('お' + main) in reads and w.startswith('お'): e['r'] = 'お' + main; main = e['r']; stats['fixread'] += 1
    # 숙자훈 ★: 사용자 리스트 or JMdict gikun/당자 or 한자 읽기로 못 나누는 단어(+JMdict 확인)
    seg = segmentable(w, main) if main else True
    juku = w in USER_JUKU or (main and fuhyo(w, main)) or (main and main in jk) or (ateji and main in reads and not seg)
    if not juku and main and not seg and main in reads and w not in NOT_JUKU: juku = True; stats['juku_auto'] += 1
    if not juku and main and not seg: review.append((w, main, lv, 'JMdict에 있음' if main in reads else 'JMdict에 없음(읽기 오류 의심)'))
    if juku: e['juku'] = 1; stats['juku'] += 1
    # 가나 표기 단어
    if uk or w in KANA_ONLY_USER: e['kana'] = 1; stats['kana'] += 1
    # 읽기 함정 (가나 표기 단어는 한자 읽기를 안 물으니 제외)
    if main and not e.get('kana') and e.get('juku'):      # 숙자훈: 글자대로 읽은 오답 (今日→こんにち)
        lit = []
        for pick in (lambda S: S[:1], lambda S: S[1:2] or S[:1]):   # 대표 음독(사전 첫 번째) → 두 번째 음독
            parts = []
            for ch in w:
                if isK(ch) and ON.get(ch): parts.append(pick(ON[ch])[0])
                elif isK(ch): parts = None; break
                else: parts.append(k2h(ch))
            if parts: lit.append(''.join(parts))
        t = [x for x in dict.fromkeys(lit) if x not in reads and x != main and not re.search('っ[がぎぐげござじずぜぞだでどばびぶべぼ]|っ$', x)]
        if t: e['trap'] = t[:2]; stats['trap_juku'] += 1
    elif main and not e.get('kana'):
        t = traps(w, main, reads | set(rs))
        if len(t) >= 2: e['trap'] = t; stats['trap'] += 1
    if e: e['lv'] = lv; extra[w] = e
# 한자 트리
tree = {}
for w in order:
    lv, it = words[w]
    if e := extra.get(w):
        if e.get('kana'): continue
    for ch in dict.fromkeys(c for c in w if re.match(r'[一-龯]', c)):
        ex = extra.get(w, {}); rd = ex.get('r') or (it[1] or '').split(';')[0].strip()
        tree.setdefault(ch, []).append([w, rd, lv] + ([1] if ex.get('juku') else []))
kanji = {}
for ch, ws in tree.items():
    if len(ws) < 2 and ch not in USER: continue
    k = {'w': ws[:12], 'n': len(ws)}
    if ch in USER: u = USER[ch]; k.update({'core': u['lv'], 'ko': u['ko'], 'on': u['on'], 'kun': u['kun'], 'ex': u['ex']})
    elif ch in KO: k['ko'] = '·'.join(dict.fromkeys(KO[ch]))[:12]
    kanji[ch] = k
stats['kanji'] = len(kanji); stats['core'] = sum(1 for k in kanji.values() if 'core' in k); stats['user'] = len(USER)
json.dump({'v': 1, 'src': 'JMdict·KANJIDIC2 (EDRDG, CC BY-SA 4.0) + MEOWCA 운영자 한자 리스트', 'words': extra}, open(f'{REPO}/presets/ja-extra.json', 'w'), ensure_ascii=False, separators=(',', ':'))
json.dump({'v': 1, 'src': 'KANJIDIC2 (EDRDG, CC BY-SA 4.0) + MEOWCA 운영자 한자 리스트', 'kanji': kanji}, open(f'{REPO}/presets/ja-kanji.json', 'w'), ensure_ascii=False, separators=(',', ':'))
json.dump(review, open(f'{REPO}/tools/ja_review.json', 'w'), ensure_ascii=False)
print(dict(stats))
