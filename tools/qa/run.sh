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
# 옛 버전은 저장소 안 사본(tools/qa/old_v115.html.gz)을 씀 — 얕은 클론에서 e0646a8이 없어 멈추던 것(11/24)
if [ -f tools/qa/old_v115.html.gz ]; then gunzip -c tools/qa/old_v115.html.gz > /tmp/srv/old/index.html
else git cat-file -e e0646a8 2>/dev/null || git fetch -q --depth=300 origin main; git show e0646a8:index.html > /tmp/srv/old/index.html; fi
cp -r cat presets slang /tmp/srv/old/
pkill -f "^python3 -m http.server 8765" 2>/dev/null || true; (cd /tmp/srv && exec python3 -m http.server 8765) >/tmp/srv.log 2>&1 </dev/null & disown; sleep 1
# 테스트는 여러 개를 동시에 돌림(QA_JOBS, 기본 2) — 전체가 10분을 넘겨 자동 작업 시간 제한에 걸리던 것(11/24)
# 실패한 테스트는 혼자 한 번 더 돌려 보고, 그래도 실패하면 멈춤(동시 실행 부하로 흔들린 것만 통과 · 「⚠ 흔들림」으로 표시)
TESTS=$(cd tools/qa && ls t*.py | sed "s/\.py$//")   # 11/24: 목록을 손으로 안 고침 — tools/qa/t*.py 를 모두 돌림(새 테스트는 파일만 추가)
# 범위(11/24): origin/main과 비교해 바뀐 게 데이터·그림·제작 도구(pr_gate 허용 목록)와 배포 버전 줄뿐이면
# 코드는 main 그대로(이미 전체 검사 통과)라 데이터를 읽는 테스트만 돌림. QA_SCOPE=full이면 늘 전체.
SCOPE=${QA_SCOPE:-auto}
if [ "$SCOPE" = auto ]; then SCOPE=full
  if git rev-parse -q --verify origin/main >/dev/null; then
    CH=$(git diff --name-only origin/main; git ls-files --others --exclude-standard)
    OTHER=$(printf '%s\n' $CH | sort -u | grep -vE '^(presets/[A-Za-z0-9_.-]+\.json|slang/[A-Za-z0-9_.-]+\.json|cat/[A-Za-z0-9_./-]+\.svg|icon[A-Za-z0-9_.-]*\.(png|svg)|tools/[A-Za-z0-9_.-]+\.(py|json|md|txt|csv)|index\.html|sw\.js)$' || true)
    VER=$(git diff -U0 origin/main -- index.html sw.js | grep -E '^[-+][^-+]' | grep -vE 'APP_VER = "v[0-9]+"|focus-vocab-v[0-9]+"' || true)
    [ -n "$CH" ] && [ -z "$OTHER" ] && [ -z "$VER" ] && SCOPE=data
  fi
fi
[ "$SCOPE" = data ] && TESTS="treg tsafe t_curation t_steps t_meaning t_cloze t_jafix t_frame t_diag t_hint"
echo "🔎 검사 범위: $SCOPE"
L=/tmp/qa_logs; rm -rf "$L"; mkdir -p "$L"; T0=$(date +%s)
printf '%s\n' $TESTS | xargs -P "${QA_JOBS:-2}" -I{} sh -c 'S=$(date +%s); if timeout 420 python3 tools/qa/{}.py > '"$L"'/{}.log 2>&1; then echo "✅ {} ($(( $(date +%s)-S ))s)"; else echo "… {} 실패 → 혼자 다시"; touch '"$L"'/{}.fail; fi'
FLAKY=""
for F in "$L"/*.fail; do [ -e "$F" ] || continue; T=$(basename "$F" .fail)
  if timeout 420 python3 tools/qa/$T.py > "$L/$T.re.log" 2>&1; then FLAKY="$FLAKY $T"; echo "⚠ $T 흔들림(혼자 다시 돌려 통과) — 첫 실패:"; grep "❌" "$L/$T.log" | head -5
  else echo "❌ $T 실패"; tail -40 "$L/$T.re.log"; exit 1; fi
done
echo "⏱ 테스트 $(( $(date +%s)-T0 ))초${FLAKY:+ · 흔들림:$FLAKY}"
echo "✅ 전체 통과"
