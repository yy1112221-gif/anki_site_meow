#!/usr/bin/env python3
"""자동 배포 관문: PR 하나가 「단어장·그림만 바뀐 안전한 PR」인지 기계적으로 판정한다.
사용: python3 tools/qa/pr_gate.py <PR번호>   (저장소 루트에서, gh 로그인 필요)
결과: 첫 줄 OK (exit 0) 또는 SKIP: 이유 (exit 2). 판단을 사람·모델이 하지 않게 하는 게 목적."""
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
print(f"OK: 파일 {len(files)}개 통과")
