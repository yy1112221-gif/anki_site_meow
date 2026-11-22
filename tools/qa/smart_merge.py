#!/usr/bin/env python3
"""PR을 지금 main 위에 합친다. 단어장(presets/*.json의 items)은 파일 통째가 아니라 「항목 단위 3자 병합」.
사용: python3 tools/qa/smart_merge.py N   (pr_gate.py N 이 만든 gateN 브랜치가 있어야 함, main 체크아웃 상태)
  - 기준(base) = PR이 갈라진 지점, PR = gateN, 지금 = origin/main
  - 항목 i 를 PR이 바꿨고 지금 main 의 i 가 기준과 같으면 → PR 값으로
  - 둘 다 같은 값으로 바꿨으면 → 그대로 / 서로 다르게 바꿨으면 → 충돌(자동으로 고르지 않음)
  - 그 밖의 파일: main 쪽이 안 바꿨으면 PR 것으로, 둘 다 바꿨으면 줄 단위 3자 병합(같은 줄을 둘 다 고쳤을 때만 충돌)
결과: MERGED (exit 0, 로컬 main에 병합 커밋 — 부모 2개라 GitHub가 PR을 merged로 표시) / CONFLICT: … (exit 4, 아무것도 안 바꿈)"""
import json, os, subprocess, sys
n = sys.argv[1]; head = f"gate{n}"
def g(*a, check=True): return subprocess.run(["git", *a], capture_output=True, text=True, check=check).stdout
def show(ref, p):
    r = subprocess.run(["git", "show", f"{ref}:{p}"], capture_output=True)
    return r.stdout.decode("utf-8") if r.returncode == 0 else None
def out(msg, code): print(msg); sys.exit(code)
base = g("merge-base", "origin/main", head, check=False).strip()
if not base:
    g("fetch", "-q", "--depth=300", "origin", "main", f"pull/{n}/head:{head}", check=False)
    base = g("merge-base", "origin/main", head, check=False).strip()
if not base: out("CONFLICT: 갈라진 지점을 못 찾음(이력 부족)", 4)
if g("rev-parse", "HEAD").strip() != g("rev-parse", "origin/main").strip(): out("CONFLICT: 로컬 main이 origin/main과 다름 — reset 후 다시", 4)
changed = [l for l in g("diff", "--name-status", base, head).splitlines() if l.strip()]
conf, writes, dels = [], {}, []
for line in changed:
    st, *ps = line.split("\t"); p = ps[-1]
    b, t, o = show(base, p), show(head, p), show("origin/main", p)
    if st.startswith("D"):
        if o == b: dels.append(p)
        elif o is not None: conf.append(f"{p}: PR은 지우고 main은 고침")
        continue
    if o == b or o == t: writes[p] = t; continue          # main이 안 건드렸거나 이미 같음
    if p.startswith("presets/") and p.endswith(".json") and b and o:
        try: B, T, O = json.loads(b), json.loads(t), json.loads(o)
        except Exception as e: conf.append(f"{p}: JSON 읽기 실패 {e}"); continue
        if isinstance(B, dict) and isinstance(T, dict) and isinstance(O, dict) and all(isinstance(x.get("items"), list) for x in (B, T, O)):
            R = dict(O); bi, ti, oi = B["items"], T["items"], O["items"]; ri = list(oi); bad = []
            for i in range(max(len(bi), len(ti))):
                bv = bi[i] if i < len(bi) else None; tv = ti[i] if i < len(ti) else None
                if tv == bv: continue
                ov = oi[i] if i < len(oi) else None
                if ov == bv:
                    if i < len(ri): ri[i] = tv
                    elif i == len(ri): ri.append(tv)
                    else: bad.append(f"#{i}(추가 위치 어긋남)")
                elif ov != tv: bad.append(f"#{i}")
            for k in set(B) | set(T):
                if k == "items" or T.get(k) == B.get(k): continue
                if O.get(k) == B.get(k): R[k] = T.get(k)
                elif O.get(k) != T.get(k): bad.append(f"키 {k}")
            if bad: conf.append(f"{p}: 같은 항목을 양쪽이 다르게 고침 {', '.join(bad[:8])}"); continue
            R["items"] = ri
            compact = "\n" not in o.strip()[:200]
            txt = json.dumps(R, ensure_ascii=False, separators=(",", ":")) if compact else json.dumps(R, ensure_ascii=False, indent=1)
            writes[p] = txt + ("\n" if o.endswith("\n") else ""); continue
    if b is not None and o is not None and t is not None:   # 그 밖의 텍스트 파일: 줄 단위 3자 병합(겹치는 줄을 양쪽이 고쳤을 때만 충돌)
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            fo, fb, ft = (os.path.join(d, x) for x in ("o", "b", "t"))
            for f_, s_ in ((fo, o), (fb, b), (ft, t)): open(f_, "w", encoding="utf-8").write(s_)
            r = subprocess.run(["git", "merge-file", "-p", fo, fb, ft], capture_output=True)
            if r.returncode == 0: writes[p] = r.stdout.decode("utf-8"); continue
            conf.append(f"{p}: 같은 줄을 양쪽이 고침({r.returncode}곳)"); continue
    conf.append(f"{p}: PR과 main이 같은 파일을 둘 다 고침")
if conf: out("CONFLICT: " + "; ".join(conf[:6]), 4)
for p, txt in writes.items():
    os.makedirs(os.path.dirname(p) or ".", exist_ok=True); open(p, "w", encoding="utf-8").write(txt)
for p in dels: g("rm", "-q", p)
if writes: g("add", "--", *writes.keys())   # 이 PR이 바꾼 파일만 담는다(작업 폴더의 다른 파일은 절대 안 담음)
tree = g("write-tree").strip()
r = subprocess.run(["gh", "api", f"repos/yy1112221-gif/anki_site_meow/pulls/{n}", "--jq", ".title"], capture_output=True, text=True)
title = r.stdout.strip() if r.returncode == 0 else ""
c = g("commit-tree", tree, "-p", "HEAD", "-p", head, "-m", f"Merge PR #{n}: {title}\n\n항목 단위 병합(tools/qa/smart_merge.py)").strip()
g("reset", "-q", "--hard", c)
out(f"MERGED: 파일 {len(writes)}개" + (f" · 삭제 {len(dels)}개" if dels else ""), 0)
