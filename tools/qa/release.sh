#!/bin/bash
# 사용: bash tools/qa/release.sh "영어 커밋 메시지" — 버전(APP_VER·sw.js 캐시) +1 → run.sh 검사 → 커밋 → main 푸시
set -e; cd "$(git rev-parse --show-toplevel)"
v=$(grep -o 'APP_VER = "v[0-9]*' index.html | grep -o '[0-9]*$'); nv=$((v+1))
sed -i "s/APP_VER = \"v$v\"/APP_VER = \"v$nv\"/" index.html; sed -i "s/focus-vocab-v[0-9]*\"/focus-vocab-v$nv\"/" sw.js
bash tools/qa/run.sh
git add -A; git commit -qm "$1 (v$nv)"; git -c push.negotiate=true push origin HEAD:main
echo "배포 v$nv"
