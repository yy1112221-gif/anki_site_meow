#!/usr/bin/env python3
"""자동 배포 관문: PR 하나가 「단어장·그림만 바뀐 안전한 PR」인지 기계적으로 판정한다.
사용: python3 tools/qa/pr_gate.py <PR번호>   (저장소 루트에서, gh 로그인 필요)
결과(첫 줄):
  OK: …      (exit 0) 합쳐도 됨 — 그림만 바뀌었거나, 단어장 변경이 이 버전(head sha) 그대로 검수 통과됨
  REVIEW: …  (exit 3) 단어장·유행어 내용이 바뀜 → 검토자가 /tmp/pr_<N>_review.json 을 보고 판정해야 함
  SKIP: …    (exit 2) 합치면 안 됨
검수 기록은 PR 댓글 속 표식 <!--qa-ok:SHA--> / <!--qa-hold:SHA--> 로 남긴다(새 커밋이 오면 다시 검수)."""
import json, re, subprocess, sys, xml.dom.minidom as X
R = "yy1112221-gif/anki_site_meow"
ALLOW = re.compile(r"^(presets/[\w.-]+\.json|slang/[\w.-]+\.json|cat/[\w./-]+\.svg|icon[\w.-]*\.(png|svg))$")
def sh(*a): return subprocess.run(a, capture_output=True, text=True, check=True).stdout
def skip(msg): print("SKIP: " + msg); sys.exit(2)
n = sys.argv[1]
pr = json.loads(sh("gh", "api", f"repos/{R}/pulls/{n}"))
if pr["base"]["ref"] != "main": skip("main 대상 PR이 아님")
files = json.loads(sh("gh", "api", "--paginate", f"repos/{R}/pulls/{n}/files?per_page=100"))
if not files: skip("바뀐 파일 없음")
sh("git", "fetch", "-q", "origin", f"pull/{n}/head:gate{n}", "main")
def show(ref, path):
    r = subprocess.run(["git", "show", f"{ref}:{path}"], capture_output=True)
    return r.stdout.decode("utf-8") if r.returncode == 0 else None
probs = []
for f in files:
    p, st = f["filename"], f["status"]
    if not ALLOW.match(p): probs.append(f"{p}: 자동 배포 허용 밖 파일"); continue
    if st in ("removed", "renamed"): probs.append(f"{p}: 삭제·이름 변경은 자동 배포 안 함"); continue
    new = show(f"gate{n}", p); old = show("origin/main", p)
    if new is None: probs.append(f"{p}: 내용을 읽을 수 없음"); continue
    if p.endswith(".svg"):
        try: X.parseString(new.encode("utf-8"))
        except Exception as e: probs.append(f"{p}: SVG 깨짐 ({e})"); continue
        if re.search(r"<script|javascript:|\bon[a-z]+\s*=|<foreignObject|href\s*=\s*[\"']https?:", new, re.I):
            probs.append(f"{p}: SVG 안에 스크립트·외부 링크가 있음(보안)")
        continue
    if p.endswith(".json"):
        try: d = json.loads(new)
        except Exception as e: probs.append(f"{p}: JSON 깨짐 ({e})"); continue
        if p.startswith("presets/") and p != "presets/index.json" and old is not None:
            o = json.loads(old)
            oi, ni = o.get("items", []), d.get("items", [])
            if len(ni) < len(oi): probs.append(f"{p}: 항목 수 줄어듦 {len(oi)}→{len(ni)}"); continue
            for i, (a, b) in enumerate(zip(oi, ni)):
                if not isinstance(b, list) or len(b) < 2: probs.append(f"{p}#{i}: 항목 형식 깨짐"); break
                if a[0] != b[0]: probs.append(f"{p}#{i}: 단어(첫 칸)가 바뀜 {a[0]}→{b[0]}"); break
                for k in range(1, min(len(a), len(b))):
                    if isinstance(a[k], str) and a[k].strip() and isinstance(b[k], str) and not b[k].strip():
                        probs.append(f"{p}#{i}: {k}번 칸이 비워짐"); break
            changed = sum(1 for a, b in zip(oi, ni) if a != b) + max(0, len(ni) - len(oi))
            if changed > 300: probs.append(f"{p}: 한 번에 {changed}개 변경 — 너무 많아 ① 검토 필요")
if probs: skip("; ".join(probs[:5]))
# 내용 검수: 단어장·유행어가 바뀌었으면 이 버전이 검수됐는지 본다
content = [f for f in files if f["filename"].startswith(("presets/", "slang/"))]
if content:
    sha = pr["head"]["sha"]
    notes = "\n".join(c.get("body") or "" for c in json.loads(sh("gh", "api", "--paginate", f"repos/{R}/issues/{n}/comments?per_page=100")))
    if f"<!--qa-hold:{sha}-->" in notes: skip("검수 보류된 버전 — 새 커밋이 올라오면 다시 검수")
    if f"<!--qa-ok:{sha}-->" not in notes:
        out = []
        for f in content:
            p = f["filename"]; new = json.loads(show(f"gate{n}", p)); old_t = show("origin/main", p); old = json.loads(old_t) if old_t else {}
            if p.startswith("presets/"):
                oi, ni = old.get("items", []), new.get("items", [])
                for i in range(len(ni)):
                    a = oi[i] if i < len(oi) else None
                    if a != ni[i]: out.append({"file": p, "i": i, "old": a, "new": ni[i]})
            else:
                ot = {json.dumps(t, ensure_ascii=False, sort_keys=True) for t in old.get("terms", [])} if isinstance(old, dict) else set()
                for t in (new.get("terms", []) if isinstance(new, dict) else []):
                    k = json.dumps(t, ensure_ascii=False, sort_keys=True)
                    if k not in ot: out.append({"file": p, "new": t})
        json.dump({"pr": int(n), "sha": sha, "title": pr["title"], "changes": out[:300]}, open(f"/tmp/pr_{n}_review.json", "w"), ensure_ascii=False, indent=1)
        print(f"REVIEW: 내용 변경 {len(out)}건 검수 필요 — /tmp/pr_{n}_review.json (sha {sha[:7]})"); sys.exit(3)
print(f"OK: 파일 {len(files)}개 통과")
