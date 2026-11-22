#!/bin/bash
# 사용: bash tools/qa/release.sh "영어 커밋 메시지" — 버전(APP_VER·sw.js 캐시) +1 → run.sh 검사 → 커밋 → main 푸시
# 푸시가 거절되면(다른 배포가 먼저 올라감) main 최신 위로 옮겨 다시 검사·푸시(최대 3번). 겹치는 줄이 있으면 멈춤(exit 1).
set -e; cd "$(git rev-parse --show-toplevel)"
for try in 1 2 3; do
  v=$(grep -o 'APP_VER = "v[0-9]*' index.html | grep -o '[0-9]*$'); nv=$((v+1))
  sed -i "s/APP_VER = \"v$v\"/APP_VER = \"v$nv\"/" index.html; sed -i "s/focus-vocab-v[0-9]*\"/focus-vocab-v$nv\"/" sw.js
  bash tools/qa/run.sh
  git add -A; git commit -qm "$1 (v$nv)"
  if git -c push.negotiate=true push origin HEAD:main; then echo "배포 v$nv"; exit 0; fi
  echo "푸시 거절 — main 최신 위로 옮겨 다시 ($try/3)"
  git reset -q --soft HEAD~1
  sed -i "s/APP_VER = \"v$nv\"/APP_VER = \"v$v\"/" index.html; sed -i "s/focus-vocab-v$nv\"/focus-vocab-v$v\"/" sw.js
  git add -A; wip=0; if ! git diff --cached --quiet; then git commit -qm "wip: release retry"; wip=1; fi
  git fetch -q origin main
  if ! git rebase -q origin/main; then git rebase --abort; [ "$wip" = 1 ] && git reset -q --soft HEAD~1; echo "충돌 — main과 같은 줄을 고침, 손으로 확인 필요"; exit 1; fi
  [ "$wip" = 1 ] && git reset -q --soft HEAD~1
done
echo "푸시 3번 거절 — 다음 회차에 다시"; exit 1
