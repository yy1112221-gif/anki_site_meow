#!/usr/bin/env python3
"""검수자가 낸 수정안을 단어장 JSON에 안전하게 반영한다(PR 브랜치에서만 실행).
사용: python3 tools/qa/apply_fixes.py fixes.json
fixes.json = [{"file":"presets/ko-beg.json","i":158,"col":1,"old":"기존 값","new":"새 값","why":"이유"}, ...]
규칙: presets/*.json 의 뜻·읽기·예문 칸(col ≥ 1)만, old가 지금 값과 정확히 같을 때만, 최대 30건. 단어(0번 칸)·항목 수는 절대 안 바꾼다.
결과: 반영 n건 / 버린 n건(이유) 출력. 원래 파일 형식(구분자)을 그대로 유지한다."""
import json, sys, re
fx = json.load(open(sys.argv[1], encoding="utf-8"))
if not isinstance(fx, list): print("버림: 형식 오류"); sys.exit(1)
done, drop, files = [], [], {}
for f in fx[:30]:
    p, i, c = f.get("file", ""), f.get("i"), f.get("col")
    if not re.fullmatch(r"presets/[\w.-]+\.json", p) or p == "presets/index.json": drop.append((f, "허용 밖 파일")); continue
    if not isinstance(i, int) or not isinstance(c, int) or c < 1: drop.append((f, "번호·칸 오류(단어 칸은 못 고침)")); continue
    new = f.get("new")
    if not isinstance(new, str) or not new.strip(): drop.append((f, "새 값이 비어 있음")); continue
    if p not in files:
        raw = open(p, encoding="utf-8").read()
        files[p] = [json.loads(raw), raw]
    items = files[p][0].get("items", [])
    if i >= len(items) or c >= len(items[i]) or not isinstance(items[i][c], str): drop.append((f, "그 칸이 없음")); continue
    if items[i][c] != f.get("old"): drop.append((f, "old가 지금 값과 다름")); continue
    items[i][c] = new; done.append(f)
for p, (d, raw) in files.items():
    compact = "\n" not in raw.strip()[:200]
    txt = json.dumps(d, ensure_ascii=False, separators=(",", ":")) if compact else json.dumps(d, ensure_ascii=False, indent=1)
    json.loads(txt); open(p, "w", encoding="utf-8").write(txt + ("\n" if raw.endswith("\n") else ""))
print(f"반영 {len(done)}건 · 버림 {len(drop)}건")
for f, why in drop: print(f"  버림 {f.get('file')}#{f.get('i')}: {why}")
