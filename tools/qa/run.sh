#!/bin/bash
# MEOWCA 배포 전 검사: 문법 → 데이터 파일(JSON·SVG) → 회귀(v115 데이터 → 현재) → 데이터 안전 14개
# 사용: bash tools/qa/run.sh   (저장소 루트에서) · 하나라도 실패하면 exit 1
set -e; R=$(git rev-parse --show-toplevel); cd "$R"
python3 -c "import playwright" 2>/dev/null || pip install -q --break-system-packages playwright
timeout 60 python3 -c "
from playwright.sync_api import sync_playwright
with sync_playwright() as p: p.chromium.launch().close()" 2>/dev/null || python3 -m playwright install --with-deps chromium >/dev/null
# 1) 문법
python3 - <<'PY'
import re,subprocess,sys
h=open("index.html",encoding="utf-8").read(); bad=0
for i,s in enumerate(re.findall(r'<script(?![^>]*src)[^>]*>(.*?)</script>',h,re.S)):
    open(f"/tmp/qa_s{i}.js","w").write(s); r=subprocess.run(["node","--check",f"/tmp/qa_s{i}.js"],capture_output=True,text=True)
    if r.returncode: bad=1; print("문법 오류 script#",i,r.stderr[:500])
sys.exit(bad)
PY
echo "✅ 문법"
# 2) 데이터 파일
python3 - <<'PY'
import json,glob,sys,xml.dom.minidom as X
bad=[]
for f in glob.glob("presets/**/*.json",recursive=True)+glob.glob("slang/**/*.json",recursive=True)+["biz.json"]:
    try: json.load(open(f,encoding="utf-8"))
    except Exception as e: bad.append(f"{f}: {e}")
for f in glob.glob("cat/**/*.svg",recursive=True):
    try: X.parse(f)
    except Exception as e: bad.append(f"{f}: {e}")
print("\n".join(bad) or "✅ JSON·SVG"); sys.exit(1 if bad else 0)
PY
# 3) 로컬 서버(/tmp/srv): 현재 작업본 + 옛 버전(v115, e0646a8)
rm -rf /tmp/srv && mkdir -p /tmp/srv/old && cp -r . /tmp/srv/ 2>/dev/null; rm -rf /tmp/srv/.git
git cat-file -e e0646a8 2>/dev/null || git fetch -q --depth=60 origin main
git show e0646a8:index.html > /tmp/srv/old/index.html; cp -r cat presets slang /tmp/srv/old/
pkill -f "^python3 -m http.server 8765" 2>/dev/null || true; (cd /tmp/srv && exec python3 -m http.server 8765) >/tmp/srv.log 2>&1 </dev/null & disown; sleep 1
python3 tools/qa/treg.py && python3 tools/qa/tsafe.py && python3 tools/qa/t_curation.py && python3 tools/qa/t_steps.py && python3 tools/qa/t_course.py
echo "✅ 전체 통과"
